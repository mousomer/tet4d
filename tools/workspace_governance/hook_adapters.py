"""Pack-managed PreToolUse adapters binding the shared no-polling guard.

The adapters are JSON hook entries merged into a consumer's
``.claude/settings.json`` and ``.codex/hooks.json``. Merging preserves every
unrelated key and hook; only entries whose command runs the pack guard are
owned here. ``check`` is the integrity test applied by ``gov check``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

GUARD = "tools/workspace_governance/hooks/no_polling.sh"
CLAUDE_PATH = ".claude/settings.json"
CODEX_PATH = ".codex/hooks.json"
CLAUDE_GUARD = f'"$CLAUDE_PROJECT_DIR"/{GUARD}'
CODEX_ROOT = (
    (
        'r=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NO_AUTONOMOUS_POLLING '
        '(GUARD_FAILURE): checkout root unavailable" >&2; exit %s; }; '
        # Codex 0.153 reads a linked worktree's .codex/ from the main checkout, so a
        # worktree on an older commit may lack the guard: fall back to the main one.
        f'g="$r/{GUARD}"; [ -x "$g" ] || {{ '
        "c=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) "
        f'&& g="${{c%/.git}}/{GUARD}"; }}; '
    )
    .replace("%", "%%")
    .replace("exit %%s", "exit %s")
)


def _entry(
    matcher: str | None, command: str, *, block_on_failure: bool = False
) -> dict[str, Any]:
    handler: dict[str, Any] = {"type": "command", "command": command, "timeout": 30}
    if block_on_failure:
        # Claude Code >= 2.1.295 blocks the call on hook timeout/crash/bad output.
        handler["onFailure"] = "block"
    group: dict[str, Any] = {"hooks": [handler]}
    if matcher is not None:
        group = {"matcher": matcher, **group}
    return group


def claude_entries() -> dict[str, dict[str, Any]]:
    return {
        "PreToolUse": _entry(
            "Bash|Monitor|mcp__.*",
            f"{CLAUDE_GUARD} claude || exit 2",
            block_on_failure=True,
        ),
        "UserPromptSubmit": _entry(None, f"{CLAUDE_GUARD} claude prompt || exit 0"),
    }


def codex_entries() -> dict[str, dict[str, Any]]:
    tool = CODEX_ROOT % 2 + '"$g" codex || exit 2'
    prompt = CODEX_ROOT % 0 + '"$g" codex prompt || exit 0'
    return {
        "PreToolUse": _entry("Bash|mcp__.*", f"sh -c '{_squote(tool)}'"),
        "UserPromptSubmit": _entry(None, f"sh -c '{_squote(prompt)}'"),
    }


def _squote(text: str) -> str:
    return text.replace("'", "'\\''")


def _owned(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    hooks = group.get("hooks")
    return isinstance(hooks, list) and any(
        isinstance(h, dict) and GUARD in str(h.get("command", "")) for h in hooks
    )


def merge(existing: dict[str, Any], entries: dict[str, dict[str, Any]]) -> dict:
    """Return ``existing`` with exactly one managed entry per event."""
    if not isinstance(existing, dict):
        raise TypeError("hook configuration must be a JSON object")
    result = dict(existing)
    hooks = result.get("hooks", {})
    if not isinstance(hooks, dict):
        raise TypeError("hooks must be a JSON object")
    hooks = dict(hooks)
    for event, entry in entries.items():
        groups = hooks.get(event, [])
        if not isinstance(groups, list):
            raise TypeError(f"hooks.{event} must be a list")
        hooks[event] = [g for g in groups if not _owned(g)] + [entry]
    result["hooks"] = hooks
    return result


def render(root: Path) -> dict[str, bytes]:
    """Rendered bytes for both adapter files of a consumer checkout."""
    output: dict[str, bytes] = {}
    for name, entries in (
        (CLAUDE_PATH, claude_entries()),
        (CODEX_PATH, codex_entries()),
    ):
        path = root / name
        existing = json.loads(path.read_text()) if path.exists() else {}
        output[name] = (json.dumps(merge(existing, entries), indent=2) + "\n").encode()
    return output


def check(root: Path) -> list[str]:
    """Problems with the consumer's adapter bindings; empty when intact."""
    problems: list[str] = []
    guard = root / GUARD
    if not guard.is_file() or not guard.stat().st_mode & 0o111:
        problems.append(f"{GUARD} is missing or not executable")
    for name, entries in (
        (CLAUDE_PATH, claude_entries()),
        (CODEX_PATH, codex_entries()),
    ):
        problems += _check_file(root / name, name, entries)
        if _git_ignored(root, name):
            problems.append(f"{name} is ignored by git and will not reach clones")
    return problems


def _git_ignored(root: Path, name: str) -> bool:
    if not (root / ".git").exists():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", "--no-index", name],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _check_file(path: Path, name: str, entries: dict) -> list[str]:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return [f"{name} is missing or not valid JSON"]
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return [f"{name} has no hooks object"]
    problems = []
    for event, entry in entries.items():
        groups = hooks.get(event)
        owned = [g for g in groups if _owned(g)] if isinstance(groups, list) else []
        if owned != [entry]:
            problems.append(f"{name} {event} does not bind the pack no-polling guard")
    if isinstance(data, dict) and data.get("disableAllHooks") is True:
        problems.append(f"{name} disables all hooks")
    return problems
