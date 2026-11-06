"""PreToolUse adapter for Claude Code and Codex over the shared command policy.

Usage: ``no_polling.py <claude|codex> [prompt]``; the hook payload arrives as
JSON on stdin. A denial exits 2 with the reason on stderr, which both runtimes
treat as a pre-execution block. ``prompt`` mode (UserPromptSubmit) starts a new
observation epoch and never blocks. The only state is a per-session record of
remote status targets already observed in the current epoch, kept under the
temporary directory; it never touches the repository or the network.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.workspace_governance import command_policy

MAX_INPUT = 1 << 20
SHELL_TOOLS = {"Bash", "Monitor", "exec_command", "shell", "local_shell"}
MCP_STATUS_TOKENS = {"status", "statuses", "checks", "ci", "rollup"}
MCP_STATUS_PHRASES = ("check_run", "check_suite", "workflow_run", "get_run")
MAX_SCRIPT = 65536
STATE_DIR = "workspace-governance-no-polling"


class GuardError(Exception):
    pass


def _read_payload() -> dict:
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise GuardError("hook payload too large")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise GuardError("hook payload is not an object")
    return payload


def gh_aliases() -> dict[str, str]:
    """Read `aliases:` from the GitHub CLI config without a YAML dependency."""
    base = os.environ.get("GH_CONFIG_DIR") or os.path.join(
        os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "gh"
    )
    try:
        text = Path(base, "config.yml").read_text(encoding="utf-8")[:MAX_INPUT]
    except OSError:
        return {}
    aliases: dict[str, str] = {}
    inside = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            inside = line.split(":", 1)[0].strip() == "aliases"
            continue
        match = re.match(r"\s+([^:\s]+):\s*(.*)$", line) if inside else None
        if match:
            value = match.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            aliases[match.group(1)] = value
    return aliases


def normalize(payload: dict) -> dict:
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    command = tool_input.get("command", tool_input.get("cmd"))
    if isinstance(command, list) and all(isinstance(a, str) for a in command):
        command = shlex.join(command)
    if tool in {"exec_command", "shell", "local_shell"}:
        tool = "Bash"
    return {"tool": tool, "command": command, "input": tool_input}


def mcp_status_tool(name: str) -> bool:
    last = name.split("__")[-1].lower()
    tokens = set(re.split(r"[_\-]+", last))
    return bool(tokens & MCP_STATUS_TOKENS) or any(
        p in last for p in MCP_STATUS_PHRASES
    )


def script_reader(cwd: str):
    """Bounded reader for scripts a command would run, relative to its cwd."""

    def read(path: str) -> str | None:
        if "$" in path or "\0" in path:
            return None
        candidate = Path(os.path.expanduser(path))
        if not candidate.is_absolute():
            candidate = Path(cwd or ".") / candidate
        try:
            if not candidate.is_file():
                return None
            with candidate.open("rb") as stream:
                data = stream.read(MAX_SCRIPT + 1)
        except OSError:
            return None
        if b"\0" in data[:4096]:
            return None
        return data[:MAX_SCRIPT].decode("utf-8", "replace")

    return read


def classify(invocation: dict, cwd: str = "") -> command_policy.Decision:
    tool = invocation["tool"]
    if (
        tool == "Monitor"
        and invocation["command"] is None
        and "ws" in invocation["input"]
    ):
        # A WebSocket source is server push, the event-driven path the policy prefers.
        return command_policy.Decision(
            command_policy.ALLOW, limits=("websocket push source",)
        )
    if tool in SHELL_TOOLS:
        if not isinstance(invocation["command"], str):
            return command_policy.Decision(
                command_policy.UNDETERMINED,
                "UNDETERMINED_REMOTE",
                f"{tool} invocation without a readable command. "
                + command_policy.ALTERNATIVE,
            )
        return command_policy.evaluate(
            invocation, aliases=gh_aliases(), reader=script_reader(cwd)
        )
    if tool.startswith("mcp__") and mcp_status_tool(tool):
        digest = hashlib.sha256(
            json.dumps(invocation["input"], sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        return command_policy.Decision(
            command_policy.ALLOW, observations=(f"mcp:{tool}:{digest}",)
        )
    return command_policy.Decision(command_policy.ALLOW)


def _state_path(runtime: str, session: str) -> Path:
    key = hashlib.sha256(f"{runtime}\0{session}".encode()).hexdigest()
    return Path(tempfile.gettempdir(), STATE_DIR, key + ".json")


def _load_state(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"epoch": "initial", "seen": []}
    if not isinstance(data, dict) or not isinstance(data.get("seen"), list):
        raise GuardError("observation state is malformed")
    return data


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    os.replace(temporary, path)


def _session(payload: dict) -> str:
    return str(payload.get("session_id") or "cwd:" + str(payload.get("cwd") or ""))


class _Locked:
    """Serialize read-modify-write of one session's state across parallel calls."""

    def __init__(self, path: Path):
        self.path = path.with_suffix(".lock")

    def __enter__(self):
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.handle = self.path.open("a")
        fcntl.flock(self.handle, fcntl.LOCK_EX)
        return self

    def __exit__(self, *_):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        self.handle.close()


def new_epoch(runtime: str, payload: dict) -> None:
    path = _state_path(runtime, _session(payload))
    token = str(payload.get("turn_id") or os.urandom(8).hex())
    with _Locked(path):
        _save_state(path, {"epoch": token, "seen": []})


def repeated(runtime: str, payload: dict, decision) -> str | None:
    """Record observations; return a repeated target within the same epoch."""
    if not decision.observations:
        return None
    path = _state_path(runtime, _session(payload))
    with _Locked(path):
        return _record(path, payload, decision)


def _record(path: Path, payload: dict, decision) -> str | None:
    try:
        state = _load_state(path)
    except (GuardError, ValueError, OSError):
        _save_state(path, {"epoch": "reset", "seen": []})
        raise GuardError("observation state was unreadable and has been reset")
    epoch = str(payload.get("turn_id") or state.get("epoch") or "initial")
    seen = state["seen"] if state.get("epoch") == epoch else []
    for target in decision.observations:
        if target in seen:
            return target
    _save_state(path, {"epoch": epoch, "seen": seen + list(decision.observations)})
    return None


def deny(violation: str, reason: str) -> int:
    print(
        f"{command_policy.POLICY_CODE} ({violation}): {reason}",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str]) -> int:
    runtime = argv[1] if len(argv) > 1 else ""
    if runtime not in {"claude", "codex"}:
        raise GuardError("unknown runtime")
    payload = _read_payload()
    if len(argv) > 2 and argv[2] == "prompt":
        new_epoch(runtime, payload)
        return 0
    decision = classify(normalize(payload), str(payload.get("cwd") or ""))
    if decision.decision != command_policy.ALLOW:
        return deny(decision.violation or "UNDETERMINED_REMOTE", decision.reason)
    target = repeated(runtime, payload, decision)
    if target is not None:
        return deny(
            "REPEATED_STATUS_QUERY",
            f"{target} was already observed this turn without a notification or "
            f"new user instruction. {command_policy.ALTERNATIVE}",
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # noqa: BLE001 - every guard failure must block
        print(
            f"{command_policy.POLICY_CODE} (GUARD_FAILURE): {type(exc).__name__}: "
            f"{exc}. The no-polling guard could not classify this call, so it is "
            "blocked; repair the pack-managed hook (./gov check).",
            file=sys.stderr,
        )
        sys.exit(2 if "prompt" not in sys.argv[2:] else 0)
