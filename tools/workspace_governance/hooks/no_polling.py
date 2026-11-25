"""PreToolUse adapter for Claude Code and Codex (``supervised-completion-v3``).

Usage: ``no_polling.py <claude|codex> [prompt]``; the hook payload arrives as
JSON on stdin. A denial exits 2 with the reason on stderr, which both runtimes
treat as a pre-execution block. ``prompt`` mode (UserPromptSubmit) starts a new
observation epoch, records a new user instruction for the operation supervisor
and never blocks.

Two checks run in order. The operation check consults the durable registry of
pending managed operations (``operation_supervisor``) and refuses only calls that
probe or duplicate one of them, naming the operation and the permitted next
action. The shared command policy then refuses tool watch modes and agent
polling loops. A guard failure is scoped: it blocks only a call that looks like
a wait or status probe and lets every other call proceed with a visible
``GUARD_DEGRADED`` warning, so no waiting-policy failure becomes a blanket
prohibition of unrelated work.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shlex
import signal
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

PROMPT_MODE = "prompt" in sys.argv[2:]
ALARM_SECONDS = 18
POLICY_CODE = "NO_AUTONOMOUS_POLLING"
RAW = {"text": ""}
# Fallback used only when the guard itself fails: block what plainly waits for or
# probes an operation, allow everything else. Mirrors the launcher's case list.
FALLBACK_PROBE = re.compile(
    r"\bgh\b[^;\n]*\brun\s+(?:list|watch|view)|gh\s+pr\s+checks"
    r"|(?:api\.github\.com/|\bgh\s+api\b)[^;\n]*(?:/runs|status|check)"
    r"|mcp__[^\s\"]*(?:actions_(?:get|list)|workflow_runs?|commit[^\s\"]*status)"
    r"|(?:^|[\s;&|(\"])watch\s|--watch|--interval|(?:^|[\s;&|(\"])sleep\s+[0-9]"
    r"|tail\s+-[A-Za-z]*[fF]|while\s.*sleep\s|until\s.*;\s*do|ps\s+-p|kill\s+-0"
    r"|(?:^|[\s;&|(\"])pgrep\s"
)


def _keep_enforcement_error(detail: str) -> None:
    """Best effort: record the error with the checkout's managed operations."""
    try:
        payload = json.loads(RAW["text"] or "{}")
        cwd = str(payload.get("cwd") or os.getcwd())
        from tools.workspace_governance import operation_supervisor

        operation_supervisor.record_enforcement_error(checkout_roots(cwd), detail)
    except Exception:  # noqa: BLE001 - recording must never change the decision
        return


def scoped_failure(
    runtime: str, detail: str, text: str | None = None, *, keep: bool = True
) -> int:
    """Turn a guard failure into a block of probe-like calls only."""
    text = RAW["text"] if text is None else text
    if PROMPT_MODE:
        return 0
    if keep:
        _keep_enforcement_error(f"GUARD_DEGRADED: {detail}")
    if FALLBACK_PROBE.search(text or ""):
        sys.stderr.write(
            f"{POLICY_CODE} (GUARD_FAILURE): {detail}. This call looks like a wait or "
            "status probe, so it is blocked while the guard is degraded. Unrelated "
            "commands remain available; repair the pack-managed hook (./gov check).\n"
        )
        return 2
    warning = (
        f"{POLICY_CODE} (GUARD_DEGRADED): {detail}. Waiting-policy enforcement is "
        "degraded for this call, which is allowed because it is not a wait or status "
        "probe. Report this enforcement error; repair with ./gov check."
    )
    sys.stderr.write(warning + "\n")
    if runtime == "claude":
        sys.stdout.write(json.dumps({"systemMessage": warning}) + "\n")
    return 0


def _deadline(*_):
    # Independent of the launcher's watchdog: a hang is scoped, never a blanket block.
    runtime = sys.argv[1] if len(sys.argv) > 1 else ""
    os._exit(scoped_failure(runtime, "classifier deadline exceeded", keep=False))


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_INPUT = 1 << 20
SHELL_TOOLS = {"Bash", "Monitor", "exec_command", "shell", "local_shell"}
MCP_STATUS_TOKENS = {"status", "statuses", "checks", "ci", "rollup"}
MCP_STATUS_PHRASES = ("check_run", "check_suite", "workflow_run", "get_run")
STATE_DIR = "workspace-governance-no-polling"
MAX_STATE_CHANGE_RESETS = 2


class GuardError(Exception):
    pass


def _read_payload() -> dict:
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    RAW["text"] = raw[:MAX_INPUT].decode("utf-8", "replace")
    if len(raw) > MAX_INPUT:
        raise GuardError("hook payload too large")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise GuardError("hook payload is not an object")
    return payload


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


def classify(invocation: dict, cwd: str = ""):
    from tools.workspace_governance import command_policy

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
        return command_policy.evaluate_shell(invocation, cwd)
    key = ""
    if tool.startswith("mcp__") and mcp_status_tool(tool):
        digest = hashlib.sha256(
            json.dumps(invocation["input"], sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        key = f"mcp:{tool}:{digest}"
    target = command_policy.mcp_remote_target(tool, invocation["input"])
    if target:
        if target.kind == "broad":
            target = replace(target, ordinary_listing_key=key)
        else:
            key = target.observation() if target.observe else ""
        return command_policy.Decision(
            command_policy.ALLOW,
            observations=(key,) if key else (),
            remote_targets=(target,),
        )
    return command_policy.Decision(
        command_policy.ALLOW, observations=(key,) if key else ()
    )


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


def _turn(payload: dict) -> str | None:
    """Turn identity: Codex ``turn_id``; Claude Code >= 2.1.3xx ``prompt_id``.

    Subagents share the parent's session and turn, so a read delegated to a
    subagent counts as the same observer repeating it."""
    value = payload.get("turn_id") or payload.get("prompt_id")
    return str(value) if value else None


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
    token = str(_turn(payload) or os.urandom(8).hex())
    with _Locked(path):
        _save_state(path, {"epoch": token, "seen": []})


def repeated(runtime: str, payload: dict, decision) -> str | None:
    """Record observations; return a repeated target within the same epoch."""
    if not decision.observations and not decision.state_change:
        return None
    path = _state_path(runtime, _session(payload))
    with _Locked(path):
        return _record(path, payload, decision)


def _record(path: Path, payload: dict, decision) -> str | None:
    try:
        state = _load_state(path)
    except (GuardError, ValueError, OSError):
        # Reset and continue: corrupt bookkeeping must not block the current call.
        sys.stderr.write(
            f"{POLICY_CODE} (GUARD_DEGRADED): observation state was unreadable and "
            "has been reset.\n"
        )
        _keep_enforcement_error("GUARD_DEGRADED: observation state reset")
        state = {"epoch": "reset", "seen": []}
    epoch = str(_turn(payload) or state.get("epoch") or "initial")
    same = state.get("epoch") == epoch
    seen = state["seen"] if same else []
    resets = int(state.get("resets", 0)) if same else 0
    if decision.state_change and resets < MAX_STATE_CHANGE_RESETS:
        # The agent's own push/merge/rerun changes remote state: one new read.
        seen, resets = [], resets + 1
    for target in decision.observations:
        if target in seen:
            return target
    _save_state(
        path,
        {"epoch": epoch, "seen": seen + list(decision.observations), "resets": resets},
    )
    return None


def deny(violation: str, reason: str) -> int:
    print(f"{POLICY_CODE} ({violation}): {reason}", file=sys.stderr)
    return 2


def checkout_roots(cwd: str) -> list[Path]:
    """The guard's own consumer root plus the governed checkout containing cwd."""
    roots = [ROOT]
    current = Path(cwd or ".").expanduser()
    for candidate in (current, *current.parents):
        if (candidate / "tools/workspace_governance/MANIFEST.json").is_file():
            if candidate.resolve() != ROOT:
                roots.append(candidate.resolve())
            break
    return roots


def _command_text(invocation: dict) -> str:
    command = invocation.get("command")
    if isinstance(command, str):
        return command
    return json.dumps(invocation.get("input") or {}, default=str)


def _session_key(runtime: str, payload: dict) -> str:
    return hashlib.sha256(f"{runtime}\0{_session(payload)}".encode()).hexdigest()


def _event_key(session: str, payload: dict) -> str | None:
    turn = _turn(payload)
    return hashlib.sha256(f"{session}\0{turn}".encode()).hexdigest() if turn else None


def _prompt(runtime: str, payload: dict, cwd: str) -> int:
    from tools.workspace_governance import operation_supervisor

    session = _session_key(runtime, payload)
    event = _event_key(session, payload)
    journal = operation_supervisor.PromptJournal(operation_supervisor.state_root())
    try:
        if event and journal.register(session, event):
            new_epoch(runtime, payload)
    except (OSError, ValueError, TypeError, KeyError):
        detail = "GUARD_DEGRADED: could not record user instruction"
        _keep_enforcement_error(detail)
        print(detail, file=sys.stderr)
    return 0


def _check_tool(runtime: str, payload: dict, cwd: str) -> int:
    invocation = normalize(payload)
    workdir = invocation["input"].get("workdir")
    if isinstance(workdir, str) and workdir:
        cwd = str((Path(cwd) / Path(workdir).expanduser()).resolve())
    text = invocation["tool"] + " " + _command_text(invocation)
    from tools.workspace_governance import operation_supervisor

    try:
        roots = checkout_roots(cwd)
        journal = operation_supervisor.PromptJournal(operation_supervisor.state_root())
        session = _session_key(runtime, payload)
        try:
            instruction = journal.instruction(session, _event_key(session, payload))
        except (OSError, ValueError, TypeError, KeyError):
            instruction = operation_supervisor.Instruction()
            print("GUARD_DEGRADED: prompt journal unavailable", file=sys.stderr)
        denial = operation_supervisor.hook_check(invocation, cwd, roots, instruction)
        if denial is not None:
            print(denial.message(), file=sys.stderr)
            _report_alias_fault(invocation)
            return 2
        try:
            decision, wrapper = _classify_dispatch(invocation, cwd)
        except Exception as exc:  # noqa: BLE001 - preserve independent probe checks
            return _classifier_failure(runtime, text, exc)
        result = _check_dispatch(
            runtime, payload, cwd, decision, invocation, text, instruction, wrapper
        )
        if result == 0 and wrapper:
            journal.handoff(wrapper, cwd, instruction)
        return result
    except operation_supervisor.MechanismError as exc:
        _keep_enforcement_error(str(exc))
        return deny("GUARD_DEGRADED", str(exc))
    except Exception as exc:  # noqa: BLE001 - scoped, never blanket
        return scoped_failure(
            runtime, f"operation registry unavailable ({type(exc).__name__})", text
        )


def _report_alias_fault(invocation: dict) -> None:
    """Report the optional configuration fault without opening a denied script."""
    from tools.workspace_governance import command_policy

    if invocation["tool"] not in SHELL_TOOLS:
        return
    try:
        command_policy.gh_aliases()
    except (OSError, ValueError) as exc:
        detail = f"GUARD_DEGRADED: command classifier failed ({type(exc).__name__})"
        _keep_enforcement_error(detail)
        print(detail, file=sys.stderr)


def _classify_dispatch(invocation: dict, cwd: str):
    from tools.workspace_governance import operation_supervisor

    decision = classify(invocation, cwd)
    wrapper = operation_supervisor.supervisor_args(invocation)
    if wrapper and not decision.supervised_remote:
        decision = operation_supervisor.wrapped_decision(invocation, cwd) or decision
    return decision, wrapper


def _classifier_failure(runtime: str, text: str, exc: Exception) -> int:
    detail = f"command classifier failed ({type(exc).__name__})"
    if re.search(r"\bgh\b", text):
        _keep_enforcement_error(f"GUARD_DEGRADED: {detail}")
        return deny("GUARD_DEGRADED", detail)
    return scoped_failure(runtime, detail, text)


def _check_dispatch(
    runtime: str,
    payload: dict,
    cwd: str,
    decision,
    invocation,
    text: str,
    instruction,
    wrapper,
) -> int:
    from tools.workspace_governance import command_policy, operation_supervisor

    admission = operation_supervisor.hook_remote_admission(
        decision.remote_targets, cwd, invocation.get("command") or ""
    )
    denial = operation_supervisor.hook_reserve_observations(
        admission, instruction, reserve=False
    )
    if denial is not None:
        print(denial.message(), file=sys.stderr)
        return 2
    if decision.decision != command_policy.ALLOW:
        return deny(decision.violation or "UNDETERMINED_REMOTE", decision.reason)
    if decision.supervised_remote and not wrapper:
        return deny(
            "UNDETERMINED_REMOTE",
            "a remote observation needs one standalone supervisor submission",
        )
    decision = _ordinary_observations(decision, admission)
    try:
        target = repeated(runtime, payload, decision)
    except Exception as exc:  # noqa: BLE001 - bookkeeping must not block the call
        return scoped_failure(
            runtime, f"observation state unavailable ({type(exc).__name__})", text
        )
    if target is not None:
        return deny(
            "REPEATED_STATUS_QUERY",
            f"{target} was already observed this turn without a notification or "
            f"new user instruction. {command_policy.ALTERNATIVE}",
        )
    if decision.remote_targets and not wrapper:
        denial = operation_supervisor.hook_reserve_observations(
            admission, instruction, reserve=True
        )
        if denial:
            print(denial.message(), file=sys.stderr)
            return 2
    return 0


def _ordinary_observations(decision, admission):
    observations = tuple(
        key
        for key in decision.observations
        if key not in admission.replaced_observations
    )
    return replace(decision, observations=observations)


def main(argv: list[str]) -> int:
    runtime = argv[1] if len(argv) > 1 else ""
    payload = _read_payload()
    if runtime not in {"claude", "codex"}:
        raise GuardError("unknown runtime")
    cwd = str(payload.get("cwd") or os.getcwd())
    if len(argv) > 2 and argv[2] == "prompt":
        return _prompt(runtime, payload, cwd)
    return _check_tool(runtime, payload, cwd)


if __name__ == "__main__":
    # Armed only when run as the hook, never on import (tests import helpers).
    signal.signal(signal.SIGALRM, _deadline)
    signal.alarm(ALARM_SECONDS)
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # noqa: BLE001 - guard failure is scoped, never blanket
        runtime = sys.argv[1] if len(sys.argv) > 1 else ""
        sys.exit(scoped_failure(runtime, f"{type(exc).__name__}: {exc}"))
