"""Supervised completion for managed operations (``supervised-completion-v3``).

Ownership:

- The policy pack (``policies/execution.json``) defines permitted behaviour and
  the transition rules below.
- Service profiles (``policies/operation_profiles.json``) declare an ordered
  preference among supported completion mechanisms, whether adapter-owned
  polling is authorized as a fallback, and the operation budget.
- This supervisor selects the mechanism deterministically, owns cadence and
  maintains durable operation state.
- Service adapters execute the selected mechanism.
- The pack hook rejects prohibited agent actions before dispatch, using the
  state this supervisor keeps.

Selection: the first mechanism in the profile's preference order that the bound
adapter can perform for this operation. Adapter polling is eligible only when
the profile authorizes it and no preferred mechanism is available. The agent
cannot choose a mechanism or change a limit: the command line accepts neither.

Transitions (each recorded with a machine-readable reason):

- Terminal outcome: ``succeeded``, ``failed`` or ``cancelled`` with evidence
  (``unknown`` and ``abandoned`` are terminal and never verification).
- Response-window expiry: continue the same handle within the remaining budget.
- Budget exhaustion (deadline, requests or waits): ``pending`` with the handle
  preserved; never restarted or cancelled. Another wait needs a new user
  instruction, which renews the budget a bounded number of times.
- Mechanism failure: an explicit ``mechanism_error``. There is no fallback
  after a failure.
- Fallback: only to the next available preference or to authorized adapter
  polling, keeping the operation identity and consumed budget.

The budget belongs to the operation, not to a wait: it persists across waits,
mechanism changes, interfaces and sessions. No outcome other than
``succeeded`` is verification.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import fcntl
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

POLICY_ID = "supervised-completion-v3"
PROFILES_PATH = Path(__file__).resolve().parent / "policies" / "operation_profiles.json"
CODE = "OPERATION_PENDING"
STATE_ENV = "GOVERNANCE_OPERATION_STATE"

# Operation status vocabulary. Only ``succeeded`` is verification.
SUCCEEDED, FAILED, CANCELLED = "succeeded", "failed", "cancelled"
UNKNOWN, ABANDONED = "unknown", "abandoned"
PENDING = "pending"
DEADLINE_EXPIRED, BUDGET_EXHAUSTED = "deadline_expired", "budget_exhausted"
ADAPTER_FAULT, MECHANISM_ERROR = "adapter_fault", "mechanism_error"
TERMINAL = {SUCCEEDED, FAILED, CANCELLED, UNKNOWN, ABANDONED}
STALLED = {DEADLINE_EXPIRED, BUDGET_EXHAUSTED, ADAPTER_FAULT, MECHANISM_ERROR}
EXIT = {
    SUCCEEDED: 0,
    FAILED: 10,
    PENDING: 11,
    DEADLINE_EXPIRED: 11,
    BUDGET_EXHAUSTED: 11,
    UNKNOWN: 12,
    ABANDONED: 12,
    CANCELLED: 12,
    ADAPTER_FAULT: 13,
    MECHANISM_ERROR: 13,
}
REFUSED_EXIT = 3

# Transition reasons (machine readable; documented in policies/execution.md).
R_SELECTED = "selected"
R_FALLBACK = "preferred_unavailable_authorized_polling"
R_WINDOW = "response_window_expired"
R_INTERRUPTED = "waiter_interrupted"
R_DEADLINE = "deadline_expired"
R_REQUESTS = "request_budget_exhausted"
R_WAITS = "wait_budget_exhausted"
R_FAILURE = "mechanism_failure"
R_FAULT = "repeated_immediate_pending"
R_NO_MECHANISM = "no_supported_mechanism"
R_COMPLETED = "completed"
R_RESUMED = "user_instruction_resume"
R_RENEWED = "user_instruction_renewed_budget"

PREFERRED = (
    "synchronous_return",
    "notification",
    "blocking_wait",
    "controlled_continuation",
)
POLLING = "adapter_polling"
WINDOWED = {"synchronous_return", "notification", "blocking_wait"}
# A blocking call that returns ``pending`` well inside its window did not block.
IMMEDIATE_FRACTION = 0.5
MAX_IMMEDIATE_PENDING = 2
MAX_TRANSITIONS = 100
MAX_ENFORCEMENT_ERRORS = 50
PROFILE_KEYS = {
    "description",
    "identity",
    "completion",
    "budget",
    "on_response_window",
    "on_budget_exhausted",
    "on_mechanism_failure",
    "probes",
}
BUDGET_KEYS = {"deadline_seconds", "max_requests", "max_waits", "max_renewals"}
POLLING_KEYS = {
    "authorized",
    "min_interval_seconds",
    "backoff_factor",
    "max_interval_seconds",
}
FIXED_RULES = {
    "on_response_window": "continue_same_handle_within_budget",
    "on_budget_exhausted": "report_pending_preserve_handle",
}
FAILURE_ACTIONS = {"report_execution_error", "report_enforcement_error"}
ALL_PROBES = (
    "process_id",
    "artifact_path",
    "remote_run_id",
    "handle",
    "duplicate_submission",
    "synthetic_wait",
)

PROCESS_TOOLS = {"ps", "kill", "pkill", "lsof", "top", "htop", "pidstat", "procs"}
SLEEP = re.compile(r"(?:^|[;&|(`\n]|\$\()\s*(?:sleep|gsleep)\s+[0-9.]")
SUPERVISOR = re.compile(
    r"(?:\bgov\s+(?:--root\s+\S+\s+)?op|operation_supervisor)\s+(\S+)(.*)"
)
SHELL_OPERATORS = set(";&|()<>")
LOG_TAIL_LINES = 20


class Refused(Exception):
    """A request the supervisor will not perform; carries the permitted action."""

    def __init__(self, reason: str, next_action: str, operation: str | None = None):
        super().__init__(reason)
        self.reason, self.next_action, self.operation = reason, next_action, operation


class MechanismError(Exception):
    """The waiting mechanism itself failed; the operation outcome is unknown."""


# ----------------------------------------------------------------- profiles


def load_profiles(path: Path = PROFILES_PATH) -> dict[str, dict]:
    """Load and validate every profile; any defect rejects the whole file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("policy") != POLICY_ID or not isinstance(data.get("profiles"), dict):
        raise ValueError("operation profiles are missing or bound to another policy")
    coverage = data.get("coverage")
    if not (
        isinstance(coverage, dict)
        and coverage.get("enforced_interfaces")
        and coverage.get("not_covered")
    ):
        raise ValueError("operation profiles must declare enforcement coverage")
    for name, profile in data["profiles"].items():
        validate_profile(name, profile)
    return data["profiles"]


def profiles_identity(path: Path = PROFILES_PATH) -> str:
    try:
        return str(json.loads(Path(path).read_text(encoding="utf-8")).get("id"))
    except (OSError, ValueError):
        return "unknown"


def profile_digest(profile: dict) -> str:
    return hashlib.sha256(
        json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_profile(name: str, profile: dict) -> None:
    """Reject incomplete or contradictory profiles before any operation starts."""
    if not isinstance(profile, dict):
        raise ValueError(f"operation profile {name}: not an object")  # noqa: TRY004
    problems = _shape_problems(profile)
    budget = profile.get("budget")
    if not isinstance(budget, dict):
        problems.append("no budget")
        budget = {}
    problems += _budget_problems(budget)
    deadline = (
        budget.get("deadline_seconds")
        if _positive(budget.get("deadline_seconds"))
        else None
    )
    completion = profile.get("completion")
    if not isinstance(completion, dict):
        problems.append("no completion declaration")
        completion = {}
    problems += _completion_problems(completion, deadline)
    if problems:
        raise ValueError(f"operation profile {name}: " + "; ".join(problems))


def _shape_problems(profile: dict) -> list[str]:
    """Keys, identity, fixed transition rules and probe classes."""
    problems: list[str] = []
    unknown = sorted(set(profile) - PROFILE_KEYS)
    if unknown:
        problems.append(f"unknown keys {unknown}")
    identity = profile.get("identity")
    if not (isinstance(identity, list) and identity):
        problems.append("no identity")
    problems += [
        f"{key} must be {value}"
        for key, value in FIXED_RULES.items()
        if profile.get(key) != value
    ]
    if profile.get("on_mechanism_failure") not in FAILURE_ACTIONS:
        problems.append("on_mechanism_failure must report an error")
    probes = profile.get("probes", [])
    if not isinstance(probes, list) or set(probes) - set(ALL_PROBES):
        problems.append("unknown probe classes")
    return problems


def _budget_problems(budget: dict) -> list[str]:
    problems = (
        [f"unknown budget keys {sorted(set(budget) - BUDGET_KEYS)}"]
        if (set(budget) - BUDGET_KEYS)
        else []
    )
    if not _positive(budget.get("deadline_seconds")):
        problems.append("no waiting deadline")
    for key in ("max_requests", "max_waits"):
        if not _count(budget.get(key), 1):
            problems.append(f"budget.{key} must be a whole number of at least 1")
    if not _count(budget.get("max_renewals"), 0):
        problems.append("budget.max_renewals must be a whole number")
    return problems


def _completion_problems(completion: dict, deadline: float | None) -> list[str]:
    problems: list[str] = []
    preference = completion.get("preference")
    if not isinstance(preference, list):
        problems.append("completion.preference must be an ordered list")
        preference = []
    if len({str(m) for m in preference}) != len(preference):
        problems.append("completion.preference repeats a mechanism")
    extra = sorted(set(completion) - {"preference", POLLING, *PREFERRED})
    if extra:
        problems.append(
            f"unknown completion keys {extra}: fallback is only by preference order "
            "or authorized adapter polling"
        )
    problems += _preference_problems(completion, preference, deadline)
    polling = completion.get(POLLING)
    authorized = False
    if polling is not None:
        if not isinstance(polling, dict) or not isinstance(
            polling.get("authorized"), bool
        ):
            problems.append("adapter_polling.authorized must be true or false")
        else:
            authorized = polling["authorized"]
            problems += _polling_problems(polling, deadline) if authorized else []
    if not preference and not authorized:
        problems.append("no supported completion mechanism and no authorized polling")
    return problems


def _preference_problems(
    completion: dict, preference: list, deadline: float | None
) -> list[str]:
    problems: list[str] = []
    for mechanism in preference:
        if mechanism == POLLING:
            problems.append(
                "adapter_polling cannot be preferred; it is only an authorized fallback"
            )
        elif mechanism not in PREFERRED:
            problems.append(f"unsupported mechanism {mechanism!r}")
        elif not isinstance(completion.get(mechanism), dict):
            problems.append(f"{mechanism} lacks parameters")
        else:
            problems += _mechanism_problems(mechanism, completion[mechanism], deadline)
    problems += [
        f"{mechanism} parameters declared outside the preference"
        for mechanism in PREFERRED
        if mechanism in completion and mechanism not in preference
    ]
    return problems


def _mechanism_problems(
    mechanism: str, params: dict, deadline: float | None
) -> list[str]:
    if mechanism == "controlled_continuation":
        allowed = {"block_seconds", "immediate_fraction", "max_immediate_pending"}
        window = params.get("block_seconds")
        problems = []
        fraction = params.get("immediate_fraction")
        if not (_positive(fraction) and fraction <= 1):
            problems.append("immediate_fraction must be in (0, 1]")
        if not _count(params.get("max_immediate_pending"), 1):
            problems.append("max_immediate_pending must be at least 1")
        name = "block_seconds"
    else:
        allowed, problems = {"response_window_seconds"}, []
        window = params.get("response_window_seconds")
        name = "response_window_seconds"
    extra = sorted(set(params) - allowed)
    if extra:
        problems.append(f"{mechanism} has unknown keys {extra}")
    if not _positive(window):
        problems.append(f"{mechanism} lacks {name}")
    elif deadline is not None and window > deadline:
        problems.append(f"{mechanism}.{name} exceeds the deadline")
    return problems


def _polling_problems(polling: dict, deadline: float | None) -> list[str]:
    problems = []
    extra = sorted(set(polling) - POLLING_KEYS)
    if extra:
        problems.append(f"adapter_polling has unknown keys {extra}")
    low, high = polling.get("min_interval_seconds"), polling.get("max_interval_seconds")
    backoff = polling.get("backoff_factor")
    if not (_positive(low) and low >= 1):
        problems.append("min_interval_seconds below one second")
    if not (_positive(backoff) and backoff >= 1):
        problems.append("backoff_factor must be at least 1")
    if not _positive(high):
        problems.append("adapter_polling lacks max_interval_seconds")
    elif _positive(low) and high < low:
        problems.append("max_interval_seconds is below min_interval_seconds")
    if deadline is not None and _positive(low) and low > deadline:
        problems.append("min_interval_seconds exceeds the deadline")
    return problems


def _positive(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _count(value: object, minimum: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


# -------------------------------------------------------------------- clocks


class Clock(Protocol):
    def now(self) -> float: ...
    def sleep(self, seconds: float) -> None: ...


class RealClock:
    """Wall-clock seconds: cadence and budgets are shared across processes."""

    def now(self) -> float:
        return time.time()

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)


# ------------------------------------------------------------------ services


@dataclass
class Observation:
    """One service observation: pending, succeeded, failed, cancelled or unknown."""

    state: str
    detail: str = ""
    exit_status: int | None = None


class Service(Protocol):
    """Adapter-side access to an operation. Agents never call these directly."""

    def supports(self, mechanism: str, record: dict) -> bool: ...


_MECHANISM_METHODS = {
    "synchronous_return": "block",
    "blocking_wait": "block",
    "notification": "wait_notification",
    "controlled_continuation": "continue_",
    POLLING: "status",
}


def adapter_supports(service: Any, mechanism: str, record: dict) -> bool:
    probe = getattr(service, "supports", None)
    if callable(probe):
        return bool(probe(mechanism, record))
    return callable(getattr(service, _MECHANISM_METHODS[mechanism], None))


class LocalProcessService:
    """Detached local process with an exit-status file written by its wrapper.

    It can block (``synchronous_return``/``blocking_wait``) only in the process
    that launched the child; any other waiter needs authorized adapter polling.
    """

    def __init__(self) -> None:
        self.children: dict[str, subprocess.Popen] = {}

    def supports(self, mechanism: str, record: dict) -> bool:
        if mechanism in {"synchronous_return", "blocking_wait"}:
            return record["id"] in self.children
        return mechanism == POLLING

    def start(self, record: dict) -> dict:
        directory = Path(record["artifacts"]["directory"])
        directory.mkdir(parents=True, exist_ok=True)
        log = Path(record["artifacts"]["log"])
        exit_file = Path(record["artifacts"]["exit_file"])
        script = (
            '"$@"; s=$?; printf "%s\\n" "$s" > "$GOV_OP_EXIT.tmp" '
            '&& mv "$GOV_OP_EXIT.tmp" "$GOV_OP_EXIT"'
        )
        with log.open("ab") as output:
            child = subprocess.Popen(
                ["/bin/sh", "-c", script, "gov-op", *record["identity"]["argv"]],
                cwd=record["identity"]["cwd"],
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env={**os.environ, "GOV_OP_EXIT": str(exit_file)},
            )
        self.children[record["id"]] = child
        return {"pid": child.pid}

    def block(self, record: dict, timeout: float) -> Observation:
        child = self.children.get(record["id"])
        if child is None:
            raise MechanismError("no child handle to block on")
        try:
            child.wait(timeout=max(timeout, 0))
        except subprocess.TimeoutExpired:
            return Observation(PENDING, "running")
        return self.status(record)

    def status(self, record: dict) -> Observation:
        exit_file = Path(record["artifacts"]["exit_file"])
        try:
            text = exit_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            text = None
        if text is not None:
            try:
                code = int(text)
            except ValueError:
                return Observation(UNKNOWN, "unreadable exit status")
            return Observation(SUCCEEDED if code == 0 else FAILED, f"exit {code}", code)
        pid = record["identity"].get("pid")
        if isinstance(pid, int) and _alive(pid):
            return Observation(PENDING, "running")
        # Exited without recording a status (killed, crashed wrapper): unknown.
        time.sleep(0.05)
        if exit_file.exists():
            return self.status(record)
        return Observation(UNKNOWN, "process ended without an exit record")


class GitHubRunService:
    """One ``gh run view`` request per observation; cadence stays in the supervisor."""

    def __init__(self, runner=subprocess.run):
        self.runner = runner

    def supports(self, mechanism: str, record: dict) -> bool:
        return mechanism == POLLING

    def status(self, record: dict) -> Observation:
        identity = record["identity"]
        command = [
            "gh",
            "run",
            "view",
            str(identity["run_id"]),
            "--repo",
            identity["repository"],
            "--json",
            "status,conclusion,headSha",
        ]
        try:
            result = self.runner(
                command, capture_output=True, text=True, timeout=60, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise MechanismError(f"gh request failed: {type(exc).__name__}") from exc
        if result.returncode != 0:
            raise MechanismError(f"gh exited {result.returncode}")
        try:
            data = json.loads(result.stdout)
        except ValueError as exc:
            raise MechanismError("gh returned unreadable JSON") from exc
        expected = str(identity.get("head_sha") or "").lower()
        if expected and str(data.get("headSha") or "").lower() != expected:
            raise MechanismError("run head commit does not match the operation")
        if data.get("status") != "completed":
            return Observation(PENDING, str(data.get("status")))
        conclusion = str(data.get("conclusion"))
        if conclusion == "success":
            if not expected:
                # Success is verification only for the source commit it binds.
                return Observation(UNKNOWN, "success without a source-commit binding")
            return Observation(SUCCEEDED, conclusion)
        if conclusion == "cancelled":
            return Observation(CANCELLED, conclusion)
        return Observation(FAILED, conclusion)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# ------------------------------------------------------------------ registry


def state_root() -> Path:
    override = os.environ.get(STATE_ENV)
    if override:
        return Path(override)
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    return Path(base, "workspace-governance", "operations")


def checkout_key(root: Path) -> str:
    return hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()[:16]


class Registry:
    """Durable operation records for one checkout, independent of agent sessions."""

    def __init__(self, root: Path, base: Path | None = None):
        self.root = Path(root).resolve()
        self.dir = (base or state_root()) / checkout_key(self.root)

    # -- storage
    def _ops(self) -> Path:
        return self.dir / "ops"

    def path(self, op_id: str) -> Path:
        if not re.fullmatch(r"op-[0-9a-f]{12}", op_id):
            raise Refused(
                f"{op_id!r} is not an operation id", "use an id from `op list`"
            )
        return self._ops() / f"{op_id}.json"

    @contextlib.contextmanager
    def locked(self):
        self.dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (self.dir / "registry.lock").open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def load(self, op_id: str) -> dict:
        try:
            return json.loads(self.path(op_id).read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise Refused(f"no operation {op_id}", "use an id from `op list`") from None

    def save(self, record: dict) -> None:
        _atomic_write(self.path(record["id"]), record)

    def records(self) -> list[dict]:
        found = []
        directory = self._ops()
        if not directory.is_dir():
            return found
        for path in sorted(directory.glob("op-*.json")):
            try:
                found.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                # An unreadable record must not hide a pending operation.
                found.append(
                    {"id": path.stem, "status": MECHANISM_ERROR, "corrupt": True}
                )
        return found

    def open_records(self) -> list[dict]:
        return [r for r in self.records() if r.get("status") not in TERMINAL]

    # -- checkout-wide metadata (user epochs, status queries, enforcement errors)
    def meta(self) -> dict:
        try:
            data = json.loads((self.dir / "meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _update_meta(self, change) -> dict:
        with self.locked():
            meta = self.meta()
            change(meta)
            _atomic_write(self.dir / "meta.json", meta)
            return meta

    def user_epoch(self) -> int:
        try:
            return int(self.meta().get("user_epoch", 0))
        except (TypeError, ValueError):
            return 0

    def advance_user_epoch(self) -> int:
        def change(meta: dict) -> None:
            try:
                meta["user_epoch"] = int(meta.get("user_epoch", 0)) + 1
            except (TypeError, ValueError):
                meta["user_epoch"] = 1

        return int(self._update_meta(change)["user_epoch"])

    def status_queried(self, op_id: str) -> bool:
        queries = self.meta().get("status_queries") or {}
        return queries.get(op_id) == self.user_epoch()

    def mark_status_queries(self, op_ids: list[str]) -> list[str]:
        """Record one supervisor status report per operation and user instruction.

        Returns the operations already reported under the current instruction.
        """
        repeated: list[str] = []

        def change(meta: dict) -> None:
            epoch = int(meta.get("user_epoch", 0) or 0)
            queries = meta.setdefault("status_queries", {})
            for op_id in op_ids:
                if queries.get(op_id) == epoch:
                    repeated.append(op_id)
                queries[op_id] = epoch

        self._update_meta(change)
        return repeated

    def record_enforcement_error(self, detail: str) -> None:
        def change(meta: dict) -> None:
            errors = meta.get("enforcement_errors")
            errors = errors if isinstance(errors, list) else []
            errors.append({"at": round(time.time(), 3), "detail": detail[:300]})
            meta["enforcement_errors"] = errors[-MAX_ENFORCEMENT_ERRORS:]

        self._update_meta(change)

    def enforcement_errors(self, since: float) -> list[dict]:
        errors = self.meta().get("enforcement_errors")
        if not isinstance(errors, list):
            return []
        return [e for e in errors if isinstance(e, dict) and e.get("at", 0) >= since]

    # -- waiter exclusion
    def wait_lock_path(self, op_id: str) -> Path:
        return self._ops() / f"{op_id}.wait.lock"

    def waiter_active(self, op_id: str) -> bool:
        path = self.wait_lock_path(op_id)
        if not path.exists():
            return False
        with path.open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            fcntl.flock(handle, fcntl.LOCK_UN)
        return False


def _atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True))
    os.replace(temporary, path)


# ---------------------------------------------------------------- supervisor


@dataclass
class WaitResult:
    operation: str
    profile: str
    status: str
    last_state: str
    requests_used: int
    elapsed: float
    next_action: str
    detail: str = ""
    reason: str = ""
    mechanism: str | None = None
    budget: dict = field(default_factory=dict)
    consumed: dict = field(default_factory=dict)
    allotment: int = 1
    transitions: list[dict] = field(default_factory=list)
    profile_version: dict = field(default_factory=dict)
    enforcement_errors: list[dict] = field(default_factory=list)
    log_tail: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return EXIT.get(self.status, 13)

    def as_dict(self) -> dict:
        budget = self.budget
        remaining = {
            "wait_seconds": round(
                max(
                    budget.get("deadline_seconds", 0)
                    - self.consumed.get("wait_seconds", 0),
                    0,
                ),
                3,
            ),
            "requests": max(
                budget.get("max_requests", 0) - self.consumed.get("requests", 0), 0
            ),
            "waits": max(budget.get("max_waits", 0) - self.consumed.get("waits", 0), 0),
        }
        return {
            "policy": POLICY_ID,
            "operation": self.operation,
            "profile": self.profile,
            "profile_version": self.profile_version,
            "status": self.status,
            "reason": self.reason,
            "verification": self.status == SUCCEEDED,
            "mechanism": self.mechanism,
            "last_state": self.last_state,
            "requests_used": self.requests_used,
            "elapsed_seconds": round(self.elapsed, 3),
            "budget": budget,
            "consumed": self.consumed,
            "remaining": remaining,
            "allotment": self.allotment,
            "transitions": self.transitions,
            "enforcement_errors": self.enforcement_errors,
            "detail": self.detail,
            "next_action": self.next_action,
            "log_tail": self.log_tail,
        }


def _zero_budget() -> dict:
    return {"wait_seconds": 0.0, "requests": 0, "waits": 0}


class Supervisor:
    def __init__(
        self,
        root: Path,
        *,
        clock: Clock | None = None,
        services: dict[str, Any] | None = None,
        profiles: dict[str, dict] | None = None,
        state_base: Path | None = None,
        gov: str = "./gov",
    ):
        self.registry = Registry(root, state_base)
        self.clock = clock or RealClock()
        if profiles is None:
            profiles = load_profiles()
        else:
            for name, profile in profiles.items():
                validate_profile(name, profile)
        self.profiles = profiles
        self.services = services if services is not None else default_services()
        self.gov = gov

    # -- submission
    def submit(self, profile: str, identity: dict, outputs: list[str] = ()) -> dict:
        if profile not in self.profiles:
            raise Refused(
                f"no operation profile {profile!r}",
                "report that this operation has no supported completion mechanism; "
                "do not wait for it with an agent-written loop",
            )
        spec = copy.deepcopy(self.profiles[profile])
        key = _identity_key(profile, identity)
        with self.registry.locked():
            for record in self.registry.open_records():
                if record.get("corrupt"):
                    continue
                if _record_key(record) == key:
                    raise Refused(
                        f"{record['id']} already tracks this operation "
                        f"({record['status']}); a second submission would duplicate it",
                        next_action(record, self),
                        record["id"],
                    )
                self._refuse_child_probe(record, identity)
            op_id = "op-" + uuid.uuid4().hex[:12]
            directory = self.registry.dir / "artifacts" / op_id
            record = {
                "id": op_id,
                "policy": POLICY_ID,
                "profile": profile,
                "profiles_id": profiles_identity(),
                "profile_sha256": profile_digest(spec),
                "spec": spec,
                "key": key,
                "identity": dict(identity),
                "status": PENDING,
                "reason": "submitted",
                "detail": "",
                "last_state": "submitted",
                "mechanism": None,
                "allotment": 1,
                "consumed": _zero_budget(),
                "total_consumed": _zero_budget(),
                "cadence": {
                    "interval": None,
                    "next_request_at": None,
                    "immediate_pending": 0,
                },
                "active_wait": None,
                "last_wait_epoch": None,
                "submitted_epoch": self.registry.user_epoch(),
                "submitted_wall": round(time.time(), 3),
                "artifacts": {
                    "directory": str(directory),
                    "log": str(directory / "output.log"),
                    "exit_file": str(directory / "exit_status"),
                    "outputs": [
                        str(Path(identity.get("cwd", ".")) / o) for o in outputs
                    ],
                },
                "history": [],
                "transitions": [],
            }
            service = self.services.get(profile)
            if hasattr(service, "start"):
                try:
                    record["identity"].update(service.start(record))
                except OSError as exc:
                    raise MechanismError(f"could not start operation: {exc}") from exc
            self.registry.save(record)
        return record

    def _refuse_child_probe(self, record: dict, identity: dict) -> None:
        """A submitted command is checked against pending operations before it runs.

        Wrapping a probe in a new operation must not escape the restrictions of
        the operation it probes, or acquire a fresh budget for probing it.
        """
        argv = identity.get("argv")
        if not isinstance(argv, list) or not argv or _completed_locally(record):
            return
        child = {"tool": "Bash", "command": shlex.join(map(str, argv)), "input": {}}
        denial = _probe(
            record, child, str(identity.get("cwd") or ""), _HookView(self.registry)
        )
        if denial is not None:
            raise Refused(
                f"the submitted command would probe or duplicate pending operation "
                f"{denial.operation} ({denial.violation}): {denial.reason}",
                denial.next_action,
                denial.operation,
            )

    # -- waiting
    def wait(self, op_id: str) -> WaitResult:
        lock_path = self.registry.wait_lock_path(op_id)
        record = self.registry.load(op_id)
        if record["status"] in TERMINAL:
            return self._result(record, 0.0)
        lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with lock_path.open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refused(
                    f"a supervised wait is already attached to {op_id}",
                    next_action(record, self, waiter=True),
                    op_id,
                ) from None
            try:
                return self._wait_locked(op_id)
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _wait_locked(self, op_id: str) -> WaitResult:
        with self.registry.locked():
            record = self.registry.load(op_id)
            if record["status"] in TERMINAL:
                return self._result(record, 0.0, waiter=False)
            try:
                spec = record_spec(record)
            except MechanismError as exc:
                self._transition(record, R_FAILURE, status=MECHANISM_ERROR)
                record.update(
                    {"status": MECHANISM_ERROR, "reason": R_FAILURE, "detail": str(exc)}
                )
                self.registry.save(record)
                return self._result(record, 0.0, waiter=False)
            if record.get("active_wait"):
                # The previous waiter ended without finishing: its own response
                # window expired or it was stopped. Same handle, same budget.
                self._transition(record, R_INTERRUPTED)
            self._authorize_wait(record, spec)
            for bucket in (record["consumed"], record["total_consumed"]):
                bucket["waits"] += 1
            record["last_wait_epoch"] = self.registry.user_epoch()
            record["active_wait"] = {"pid": os.getpid(), "started_at": self.clock.now()}
            self.registry.save(record)
        run = _Wait(self, record, spec)
        try:
            status, reason, detail = run.execute(self.services.get(record["profile"]))
        except MechanismError as exc:
            run.checkpoint()
            status, reason, detail = MECHANISM_ERROR, R_FAILURE, str(exc)
        return self._finish(record, status, reason, detail, run.elapsed())

    def _authorize_wait(self, record: dict, spec: dict) -> None:
        budget = spec["budget"]
        last, epoch = record.get("last_wait_epoch"), self.registry.user_epoch()
        fresh_instruction = last is None or epoch > last
        exhausted = budget_exhausted(record, budget)
        stalled = record["status"] in STALLED
        if (stalled or exhausted) and not fresh_instruction:
            raise Refused(
                f"{record['id']} is {record['status']} "
                f"({exhausted or record.get('reason')}); another wait needs a new "
                "user instruction",
                next_action(record, self),
                record["id"],
            )
        if exhausted:
            if record["allotment"] > budget["max_renewals"]:
                raise Refused(
                    f"{record['id']} has used its budget and all "
                    f"{budget['max_renewals']} renewals",
                    f"report {record['status']} for {record['id']} with last state "
                    f"'{record['last_state']}' and yield; the handle is preserved",
                    record["id"],
                )
            record["allotment"] += 1
            record["consumed"] = _zero_budget()
            record["cadence"]["immediate_pending"] = 0
            self._transition(record, R_RENEWED, allotment=record["allotment"])
        elif stalled:
            record["cadence"]["immediate_pending"] = 0
            self._transition(record, R_RESUMED)

    def _transition(
        self, record: dict, reason: str, to: str | None = None, **extra
    ) -> None:
        entry = {
            "at": round(self.clock.now(), 3),
            "reason": reason,
            "from": record.get("mechanism"),
            "to": to if to is not None else record.get("mechanism"),
            **extra,
        }
        record["transitions"] = (record.get("transitions", []) + [entry])[
            -MAX_TRANSITIONS:
        ]

    def _finish(self, record, status, reason, detail, elapsed) -> WaitResult:
        self._transition(record, reason, status=status)
        record.update(
            {"status": status, "reason": reason, "detail": detail, "active_wait": None}
        )
        with self.registry.locked():
            self.registry.save(record)
        # This waiter is finishing: its own lock must not read as another waiter.
        return self._result(record, elapsed, waiter=False)

    def _result(self, record, elapsed, waiter=None) -> WaitResult:
        spec = record.get("spec") or {}
        return WaitResult(
            operation=record["id"],
            profile=record["profile"],
            status=record["status"],
            last_state=record.get("last_state", ""),
            requests_used=int(record.get("total_consumed", {}).get("requests", 0)),
            elapsed=elapsed,
            detail=record.get("detail", ""),
            reason=record.get("reason", ""),
            mechanism=record.get("mechanism"),
            budget=dict(spec.get("budget") or {}),
            consumed=dict(record.get("consumed") or {}),
            allotment=int(record.get("allotment", 1)),
            transitions=list(record.get("transitions", []))[-10:],
            profile_version={
                "profiles_id": record.get("profiles_id"),
                "profile_sha256": record.get("profile_sha256"),
            },
            enforcement_errors=self.registry.enforcement_errors(
                float(record.get("submitted_wall", 0))
            ),
            next_action=next_action(record, self, waiter=waiter),
            log_tail=_tail(record),
        )

    def abandon(self, op_id: str) -> dict:
        """Stop restricting an operation without cancelling it (user authorized)."""
        with self.registry.locked():
            record = self.registry.load(op_id)
            if record["status"] in TERMINAL:
                return record
            if self.registry.waiter_active(op_id):
                raise Refused(
                    f"a supervised wait is attached to {op_id}",
                    next_action(record, self, waiter=True),
                    op_id,
                )
            if record["submitted_epoch"] >= self.registry.user_epoch():
                raise Refused(
                    f"abandoning {op_id} needs a new user instruction",
                    next_action(record, self),
                    op_id,
                )
            record.update(
                {
                    "status": ABANDONED,
                    "reason": "user_instruction_abandon",
                    "detail": "released by user instruction; the operation was not cancelled",
                }
            )
            self.registry.save(record)
            return record


def record_spec(record: dict) -> dict:
    """The profile frozen at submission, revalidated so it cannot be weakened."""
    spec = record.get("spec")
    try:
        validate_profile(record.get("profile", "?"), spec)
    except ValueError as exc:
        raise MechanismError(f"operation profile snapshot invalid: {exc}") from exc
    if profile_digest(spec) != record.get("profile_sha256"):
        raise MechanismError("operation profile snapshot was modified after submission")
    return spec


def budget_exhausted(record: dict, budget: dict) -> str | None:
    consumed = record["consumed"]
    if consumed["wait_seconds"] >= budget["deadline_seconds"] - 1e-6:
        return R_DEADLINE
    if consumed["requests"] >= budget["max_requests"]:
        return R_REQUESTS
    if consumed["waits"] >= budget["max_waits"]:
        return R_WAITS
    return None


class _Wait:
    """One supervised wait: selection, mechanism execution and budget accounting."""

    def __init__(self, supervisor: Supervisor, record: dict, spec: dict):
        self.supervisor, self.record, self.spec = supervisor, record, spec
        self.clock = supervisor.clock
        self.budget = spec["budget"]
        self.started = self.mark = self.clock.now()

    # -- accounting
    def elapsed(self) -> float:
        return self.clock.now() - self.started

    def checkpoint(self) -> None:
        now = self.clock.now()
        spent = max(now - self.mark, 0.0)
        self.mark = now
        for bucket in (self.record["consumed"], self.record["total_consumed"]):
            bucket["wait_seconds"] = round(bucket["wait_seconds"] + spent, 6)
        self.save()

    def save(self) -> None:
        with self.supervisor.registry.locked():
            self.supervisor.registry.save(self.record)

    def remaining(self) -> float:
        return self.budget["deadline_seconds"] - self.record["consumed"]["wait_seconds"]

    def stop(self) -> tuple[str, str, str] | None:
        if self.record["consumed"]["requests"] >= self.budget["max_requests"]:
            return BUDGET_EXHAUSTED, R_REQUESTS, "request budget spent"
        if self.remaining() <= 1e-6:
            return DEADLINE_EXPIRED, R_DEADLINE, "waiting deadline reached"
        return None

    def observe(self, call, *args) -> Observation:
        for bucket in (self.record["consumed"], self.record["total_consumed"]):
            bucket["requests"] += 1
        self.save()  # counted before the call, so an interrupted call still counts
        observation = call(self.record, *args)
        self.record["last_state"] = observation.state + (
            f" ({observation.detail})" if observation.detail else ""
        )
        self.record["history"] = (self.record.get("history", []) + [observation.state])[
            -50:
        ]
        self.checkpoint()
        return observation

    def sleep(self, seconds: float) -> None:
        self.clock.sleep(max(seconds, 0.0))
        self.checkpoint()

    # -- selection
    def select(self, service) -> tuple[str | None, list[str]]:
        completion = self.spec["completion"]
        unavailable = []
        for mechanism in completion["preference"]:
            if adapter_supports(service, mechanism, self.record):
                return mechanism, unavailable
            unavailable.append(mechanism)
        polling = completion.get(POLLING) or {}
        if polling.get("authorized") and adapter_supports(
            service, POLLING, self.record
        ):
            return POLLING, unavailable
        return None, unavailable

    def execute(self, service) -> tuple[str, str, str]:
        if service is None:
            return (
                MECHANISM_ERROR,
                R_FAILURE,
                "no service adapter is bound for this profile",
            )
        mechanism, unavailable = self.select(service)
        if mechanism is None:
            self.supervisor._transition(
                self.record, R_NO_MECHANISM, to=None, unavailable=unavailable
            )
            return (
                MECHANISM_ERROR,
                R_NO_MECHANISM,
                (
                    "no supported completion mechanism is available and the profile "
                    "does not authorize adapter polling"
                ),
            )
        if mechanism != self.record.get("mechanism"):
            reason = R_FALLBACK if mechanism == POLLING else R_SELECTED
            self.supervisor._transition(
                self.record, reason, to=mechanism, unavailable=unavailable
            )
            self.record["mechanism"] = mechanism
            self.save()
        stop = self.stop()
        if stop is not None:
            return stop
        if mechanism == POLLING:
            return self.poll(service)
        if mechanism == "controlled_continuation":
            params = self.spec["completion"][mechanism]
            return self.blocking(
                service.continue_,
                params["block_seconds"],
                params["immediate_fraction"],
                params["max_immediate_pending"],
            )
        call = (
            service.wait_notification if mechanism == "notification" else service.block
        )
        window = self.spec["completion"][mechanism]["response_window_seconds"]
        return self.blocking(call, window, IMMEDIATE_FRACTION, MAX_IMMEDIATE_PENDING)

    # -- mechanisms
    def blocking(self, call, window, fraction, immediate_limit) -> tuple[str, str, str]:
        """Blocking windows on one handle; window expiry continues within budget."""
        cadence = self.record["cadence"]
        while True:
            stop = self.stop()
            if stop is not None:
                return stop
            span = min(window, self.remaining())
            began = self.clock.now()
            observation = self.observe(call, span)
            if observation.state != PENDING:
                # An immediate return caused by completion is valid.
                cadence["immediate_pending"] = 0
                return observation.state, R_COMPLETED, observation.detail
            took = self.clock.now() - began
            if took < span * fraction:
                cadence["immediate_pending"] += 1
                if cadence["immediate_pending"] >= immediate_limit:
                    return (
                        ADAPTER_FAULT,
                        R_FAULT,
                        (
                            f"{cadence['immediate_pending']} consecutive immediate pending "
                            "responses; the mechanism does not block as required"
                        ),
                    )
                # Never a tight loop: enforce the window the tool failed to honour.
                self.sleep(min(span - took, self.remaining()))
            else:
                cadence["immediate_pending"] = 0
            self.supervisor._transition(self.record, R_WINDOW, window=round(span, 3))
            self.save()

    def poll(self, service) -> tuple[str, str, str]:
        """Authorized adapter polling; cadence persists across waits and processes."""
        params = self.spec["completion"][POLLING]
        cadence = self.record["cadence"]
        interval = float(cadence.get("interval") or params["min_interval_seconds"])
        while True:
            stop = self.stop()
            if stop is not None:
                return stop
            due = cadence.get("next_request_at")
            delay = (due - self.clock.now()) if due is not None else 0.0
            if delay > 0:
                if delay >= self.remaining():
                    self.sleep(self.remaining())
                    return DEADLINE_EXPIRED, R_DEADLINE, "waiting deadline reached"
                self.sleep(delay)
            # Reserve the next slot before requesting, so a waiter stopped during
            # the request cannot let its successor request sooner.
            cadence["next_request_at"] = self.clock.now() + interval
            interval = min(
                interval * float(params["backoff_factor"]),
                float(params["max_interval_seconds"]),
            )
            cadence["interval"] = interval
            observation = self.observe(service.status)
            if observation.state != PENDING:
                return observation.state, R_COMPLETED, observation.detail


def default_services() -> dict[str, Any]:
    local = LocalProcessService()
    return {
        "local-command": local,
        "local-process": local,
        "github-actions-run": GitHubRunService(),
    }


def _identity_key(profile: str, identity: dict) -> str:
    """Operation identity shared by every profile that drives the same service.

    Profiles differ in how completion is awaited, not in what runs: the same
    command in the same directory is one local operation, and the same run of
    one repository is one remote operation, whichever profile submits it.
    """
    argv = identity.get("argv")
    if isinstance(argv, list):
        cwd = os.path.realpath(str(identity.get("cwd") or "."))
        stable: list = ["local-process", [str(a) for a in argv], cwd]
    elif identity.get("run_id") is not None:
        repository = str(identity.get("repository") or "").lower()
        stable = ["github-run", repository, str(identity["run_id"])]
    else:
        stable = [profile, {k: v for k, v in identity.items() if k != "pid"}]
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, default=str).encode()
    ).hexdigest()


def _record_key(record: dict) -> str:
    # Recomputed, so records stored under an earlier key form still match.
    identity = record.get("identity")
    if not isinstance(identity, dict):
        return str(record.get("key"))
    return _identity_key(str(record.get("profile")), identity)


def _tail(record: dict) -> list[str]:
    log = record.get("artifacts", {}).get("log")
    if not log:
        return []
    try:
        with open(log, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(size - 8192, 0))
            lines = handle.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []
    return lines[-LOG_TAIL_LINES:]


def next_action(record: dict, supervisor=None, *, waiter: bool | None = None) -> str:
    gov = getattr(supervisor, "gov", "./gov")
    op_id = record.get("id", "?")
    status = record.get("status")
    if status in TERMINAL:
        return f"read the final result with `{gov} op result {op_id}`"
    if waiter is None and supervisor is not None:
        waiter = supervisor.registry.waiter_active(op_id)
    if waiter:
        return (
            f"a supervised wait is already attached to {op_id} and will deliver its "
            "completion; continue independent work or yield"
        )
    if status == PENDING:
        return (
            f"run `{gov} op wait {op_id}` once (in Claude Code with "
            "run_in_background so completion arrives as a notification); the adapter "
            "enforces cadence"
        )
    return (
        f"report {status} for {op_id} (last state '{record.get('last_state', '')}') "
        f"and yield; after a new user instruction `{gov} op wait {op_id}` resumes the "
        "same handle within its remaining or renewed budget. Do not resubmit, restart "
        "or cancel it"
    )


# --------------------------------------------------------- hook integration


@dataclass(frozen=True)
class Denial:
    operation: str
    profile: str
    violation: str
    reason: str
    next_action: str

    def message(self) -> str:
        return (
            f"{CODE} ({self.violation}) operation={self.operation} "
            f"profile={self.profile}: {self.reason}. Permitted next action: "
            f"{self.next_action}. Only this call is blocked; unrelated work remains "
            "available."
        )


def hook_check(invocation: dict, cwd: str, roots: list[Path]) -> Denial | None:
    """Refuse an invocation that probes or duplicates a pending managed operation."""
    seen: set[str] = set()
    for root in roots:
        registry = Registry(root)
        if str(registry.dir) in seen or not registry.dir.is_dir():
            continue
        seen.add(str(registry.dir))
        supervisor = _HookView(registry)
        for record in registry.open_records():
            if _completed_locally(record):
                continue
            denial = _probe(record, invocation, cwd, supervisor)
            if denial is not None:
                return denial
    return None


def advance_user_epoch(roots: list[Path]) -> None:
    for root in roots:
        registry = Registry(root)
        if registry.dir.is_dir():
            registry.advance_user_epoch()


def record_enforcement_error(roots: list[Path], detail: str) -> None:
    """Best effort: keep a hook enforcement error with the checkout's operations."""
    for root in roots:
        registry = Registry(root)
        if registry.dir.is_dir():
            registry.record_enforcement_error(detail)


class _HookView:
    def __init__(self, registry: Registry):
        self.registry, self.gov = registry, "./gov"


def _completed_locally(record: dict) -> bool:
    # A finished local process is not "pending": its result is one `op result` away.
    exit_file = record.get("artifacts", {}).get("exit_file")
    local = isinstance(record.get("identity", {}).get("argv"), list)
    return local and bool(exit_file and os.path.exists(exit_file))


@dataclass(frozen=True)
class _Call:
    """One tool invocation as seen by the probe checks."""

    command: str | None
    texts: tuple[str, ...]
    joined: str
    tokens: frozenset[str]
    cwd: str
    tool: str = ""
    tool_input: Any = None
    globs: tuple[str, ...] = ()


def _invocation_texts(invocation: dict) -> list[str]:
    command = invocation.get("command")
    tool_input = invocation.get("input") or {}
    texts = [command] if isinstance(command, str) else []
    texts += [
        tool_input[key]
        for key in ("file_path", "path", "notebook_path")
        if isinstance(tool_input.get(key), str)
    ]
    texts += list(_glob_patterns(invocation, ""))
    if str(invocation.get("tool") or "").startswith("mcp__"):
        texts.append(json.dumps(tool_input, sort_keys=True, default=str))
    return texts


def _glob_patterns(invocation: dict, cwd: str) -> tuple[str, ...]:
    """A Glob call's ``pattern``, anchored at its ``path`` (or the cwd if given)."""
    if invocation.get("tool") != "Glob":
        return ()
    tool_input = invocation.get("input") or {}
    pattern = tool_input.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        return ()
    base = tool_input.get("path")
    base = base if isinstance(base, str) and base else cwd
    if base and not os.path.isabs(os.path.expanduser(pattern)):
        return (os.path.join(base, pattern),)
    return (os.path.expanduser(pattern),)


SUPERVISOR_VALUE_OPTIONS = {"--profile", "--output", "--run-id", "--repo", "--head-sha"}


def _supervisor_args(command: str) -> list[str] | None:
    """Arguments of one plain ``gov op`` invocation with no shell composition."""
    if "`" in command or "$(" in command or "\n" in command:
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        words = list(lexer)
    except ValueError:
        return None
    if any(word and set(word) <= SHELL_OPERATORS for word in words):
        return None
    rest = _supervisor_entry(words)
    if rest is None:
        return None
    while rest[:1] == ["--root"] or (rest and rest[0].startswith("--root=")):
        rest = rest[2:] if rest[0] == "--root" else rest[1:]
    return rest


def _supervisor_entry(words: list[str]) -> list[str] | None:
    """Words after the supervisor entry point (``gov op`` or the module)."""
    if not words:
        return None
    head = words[0].rsplit("/", 1)[-1]
    rest = words[1:]
    if head in {"python", "python3"} or head.startswith("python3."):
        if rest[:1] and rest[0].endswith("operation_supervisor.py"):
            return rest[1:]
        if rest[:2] == ["-m", "tools.workspace_governance.operation_supervisor"]:
            return rest[2:]
        return None
    if head != "gov":
        return None
    if rest[:1] == ["--root"]:
        rest = rest[2:]
    return rest[1:] if rest[:1] == ["op"] else None


def single_supervisor_call(command: str) -> bool:
    """True only for one plain ``gov op`` invocation with no shell composition."""
    return _supervisor_args(command) is not None


def _submitted_child(args: list[str]) -> list[str]:
    """The command a ``run`` or ``submit`` call would start (argparse REMAINDER)."""
    if args[:1] not in (["run"], ["submit"]):
        return []
    index = 1
    while index < len(args):
        word = args[index]
        if word == "--":
            return args[index + 1 :]
        if word in SUPERVISOR_VALUE_OPTIONS:
            index += 2
        elif word.startswith("-"):
            index += 1
        else:
            return args[index:]
    return []


_CONTINUE = object()


def _supervisor_probe(record, supervisor_call, command, cwd, view, deny):
    """Checks for a call of the supervisor itself; ``_CONTINUE`` if composed."""
    action, rest = supervisor_call.group(1), supervisor_call.group(2)
    targets_this = record.get("id", "?") in rest
    if (
        targets_this
        and action in {"wait", "result"}
        and view.registry.waiter_active(record["id"])
    ):
        reason = (
            f"`op {action}` would duplicate the supervised wait already attached "
            "to this operation"
        )
        return deny(("REDUNDANT_WAIT", reason), waiter=True)
    status_query = action == "list" or (action == "result" and targets_this)
    if status_query and view.registry.status_queried(record["id"]):
        reason = (
            "the supervisor already reported this operation's status for the "
            "current user instruction; repeating the query to detect completion "
            "is polling"
        )
        return deny(("STATUS_QUERY", reason))
    args = _supervisor_args(command or "")
    if args is None:
        return _CONTINUE
    # The supervisor enforces its own budgets and status-query limit, but the
    # command it would start is an agent command like any other: a probe
    # wrapped in a new operation is still a probe of this one.
    child = _submitted_child(args)
    if not child:
        return None
    wrapped = {"tool": "Bash", "command": shlex.join(child), "input": {}}
    return _probe(record, wrapped, cwd, view)


def _probe(record: dict, invocation: dict, cwd: str, view) -> Denial | None:
    texts = _invocation_texts(invocation)
    if not texts:
        return None
    command = invocation.get("command")
    command = command if isinstance(command, str) else None

    def deny(found: tuple[str, str], waiter: bool | None = None) -> Denial:
        return Denial(
            record.get("id", "?"),
            record.get("profile", "?"),
            found[0],
            found[1],
            next_action(record, view, waiter=waiter),
        )

    supervisor_call = SUPERVISOR.search(command or "")
    if supervisor_call:
        outcome = _supervisor_probe(record, supervisor_call, command, cwd, view, deny)
        if outcome is not _CONTINUE:
            return outcome
        # Composed with other commands: every probe check still applies.
    if record.get("corrupt"):
        return None
    joined = "\n".join(texts)
    call = _Call(
        command,
        tuple(texts),
        joined,
        frozenset(_tokens(joined)),
        cwd,
        str(invocation.get("tool") or ""),
        invocation.get("input") or {},
        _glob_patterns(invocation, cwd),
    )
    for name in view_profile_probes(record):
        found = PROBE_CHECKS[name](record, call) if name in PROBE_CHECKS else None
        if found is not None:
            return deny(found)
    return None


def _process_probe(record: dict, call: _Call) -> tuple[str, str] | None:
    pid = record.get("identity", {}).get("pid")
    if not isinstance(pid, int):
        return None
    proc = f"/proc/{pid}" in call.joined
    if proc or (str(pid) in call.tokens and call.tokens & PROCESS_TOOLS):
        return "PROCESS_PROBE", f"the command inspects process {pid}"
    return None


def _artifact_probe(record: dict, call: _Call) -> tuple[str, str] | None:
    artifacts = record.get("artifacts", {})
    paths = [artifacts.get(key) for key in ("directory", "log", "exit_file")]
    paths += list(artifacts.get("outputs") or [])
    paths = [p for p in paths if p]
    if _mentions_path(call.texts, call.tokens, paths, call.cwd) or _glob_matches(
        call.globs, paths
    ):
        reason = (
            "reading or testing this operation's log, exit file or declared outputs "
            "before completion is a completion probe"
        )
        return "ARTIFACT_PROBE", reason
    return None


def _run_probe(record: dict, call: _Call) -> tuple[str, str] | None:
    """A query of the run itself, judged by tool, command and argument role.

    A bare number elsewhere (``git log -n 123``, ``--maxfail=123``) is not a
    reference to run 123.
    """
    run_id = record.get("identity", {}).get("run_id")
    if run_id is None:
        return None
    run_id = str(run_id)
    found = "STATUS_PROBE", f"the call queries run {run_id}"
    if re.search(rf"/runs/{re.escape(run_id)}(?![\w-])", call.joined):
        return found  # REST paths and URLs, through gh api, curl or a tool
    if call.tool.startswith("mcp__"):
        return found if _mcp_names_run(call.tool, call.tool_input, run_id) else None
    if call.command is None:
        return None
    segments = _command_segments(call.command)
    listed = any(_gh_run_call(words) == "list" for words in segments)
    for words in segments:
        sub = _gh_run_call(words)
        if sub and sub != "list" and run_id in words[words.index("run") + 1 :]:
            return found  # gh run view/watch/download/cancel <id>
    if listed and run_id in call.tokens:
        return found  # gh run list filtered for this run
    return None


def _gh_run_call(words: list[str]) -> str | None:
    """The ``gh run`` subcommand a simple command invokes, if any."""
    for index, word in enumerate(words):
        if word.rsplit("/", 1)[-1] != "gh":
            continue
        rest = words[index + 1 :]
        while rest and rest[0].startswith("-"):
            rest = rest[2:] if rest[0] in {"-R", "--repo"} else rest[1:]
        if rest[:1] == ["run"]:
            return rest[1] if len(rest) > 1 else "run"
    return None


def _mcp_names_run(tool: str, tool_input: Any, run_id: str) -> bool:
    run_tool = "run" in tool.lower()

    def walk(value: Any, key: str) -> bool:
        if isinstance(value, dict):
            return any(walk(v, str(k)) for k, v in value.items())
        if isinstance(value, list):
            return any(walk(v, key) for v in value)
        named = "run" in key.lower() or (run_tool and key.lower() in {"id", ""})
        return named and str(value) == run_id

    return walk(tool_input, "")


def _command_segments(command: str, depth: int = 0) -> list[list[str]]:
    """Simple commands of a shell command line, including ``sh -c`` scripts."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        words = list(lexer)
    except ValueError:
        words = command.split()
    segments: list[list[str]] = [[]]
    for word in words:
        if word and set(word) <= SHELL_OPERATORS:
            segments.append([])
            continue
        segments[-1].append(word)
        if depth < 3 and any(c.isspace() for c in word):
            segments += _command_segments(word, depth + 1)
    return [s for s in segments if s]


def _handle_probe(record: dict, call: _Call) -> tuple[str, str] | None:
    handle = record.get("identity", {}).get("handle")
    if handle and str(handle) in call.joined:
        return "STATUS_PROBE", "the call continues or queries the handle directly"
    return None


def _duplicate_probe(record: dict, call: _Call) -> tuple[str, str] | None:
    if call.command is None:
        return None
    identity = record.get("identity", {})
    argv = identity.get("argv")
    same = (
        isinstance(argv, list)
        and argv
        and (_normalized(call.command) == _normalized(shlex.join(argv)))
    )
    if same:
        return "DUPLICATE_SUBMISSION", "the command resubmits the pending operation"
    run_id = identity.get("run_id")
    rerun = rf"\bgh\s+run\s+rerun\s+{re.escape(str(run_id))}\b"
    if run_id is not None and re.search(rerun, call.command):
        return "DUPLICATE_SUBMISSION", "the command reruns the pending run"
    return None


def _sleep_probe(record: dict, call: _Call) -> tuple[str, str] | None:
    if call.command is not None and SLEEP.search(call.command):
        reason = (
            "sleeping while a managed operation is pending substitutes for its "
            "supervised completion"
        )
        return "SYNTHETIC_WAIT", reason
    return None


PROBE_CHECKS = {
    "process_id": _process_probe,
    "artifact_path": _artifact_probe,
    "remote_run_id": _run_probe,
    "handle": _handle_probe,
    "duplicate_submission": _duplicate_probe,
    "synthetic_wait": _sleep_probe,
}


def view_profile_probes(record: dict) -> list[str]:
    """Probe classes from the profile frozen at submission; all of them if unreadable."""
    spec = record.get("spec")
    probes = spec.get("probes") if isinstance(spec, dict) else None
    if isinstance(probes, list) and probes and not set(probes) - set(ALL_PROBES):
        return probes
    return list(ALL_PROBES)


def _tokens(text: str) -> set[str]:
    try:
        parts = shlex.split(text, comments=False, posix=True)
    except ValueError:
        parts = text.split()
    tokens: set[str] = set()
    for part in parts:
        tokens.add(part)
        tokens.update(t for t in re.split(r"[\s;&|()<>=,:'\"{}\[\]]+", part) if t)
        if part.startswith("-p") and part[2:].isdigit():
            tokens.add(part[2:])
    return tokens


def _mentions_path(texts, tokens, paths, cwd) -> bool:
    resolved = {os.path.realpath(p) for p in paths}
    for token in tokens:
        if "/" not in token and "." not in token:
            continue
        candidate = os.path.expanduser(token)
        if not os.path.isabs(candidate):
            candidate = os.path.join(cwd or ".", candidate)
        real = os.path.realpath(candidate)
        for path in resolved:
            if real == path or real.startswith(path.rstrip("/") + "/"):
                return True
    joined = "\n".join(texts)
    return any(p in joined for p in paths)


def _glob_matches(globs, paths) -> bool:
    """True when a glob pattern would match an artifact (``*`` may cross ``/``)."""
    if not globs:
        return False
    candidates = {p for p in paths} | {os.path.realpath(p) for p in paths}
    for pattern in globs:
        variants = {pattern, _real_glob(pattern)}
        for variant in variants:
            if any(fnmatch.fnmatchcase(c, variant) for c in candidates):
                return True
    return False


def _real_glob(pattern: str) -> str:
    # Resolve the literal leading directories, so /tmp and /private/tmp agree.
    match = re.search(r"[*?\[]", pattern)
    head = pattern[: match.start()] if match else pattern
    directory = head.rsplit("/", 1)[0] if "/" in head else ""
    if not directory:
        return pattern
    return os.path.realpath(directory) + pattern[len(directory) :]


def _normalized(command: str) -> str:
    return " ".join(command.split())


# ----------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gov op",
        description="Submit managed operations and await them under adapter-owned cadence.",
    )
    parser.add_argument("--root", type=Path, default=root or Path.cwd())
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run", help="submit and wait once (one call for a long job)")
    submit = sub.add_parser("submit", help="register or start without waiting")
    for item in (run, submit):
        item.add_argument("--profile", required=True)
        item.add_argument("--output", action="append", default=[])
        item.add_argument("--run-id")
        item.add_argument("--repo")
        item.add_argument("--head-sha")
        item.add_argument("argv", nargs=argparse.REMAINDER)
    sub.add_parser("wait").add_argument("operation")
    sub.add_parser("result").add_argument("operation")
    sub.add_parser("abandon").add_argument("operation")
    sub.add_parser("list")
    sub.add_parser("profiles")
    args = parser.parse_args(argv)
    try:
        supervisor = Supervisor(args.root)
    except (OSError, ValueError) as exc:
        _emit({"policy": POLICY_ID, "status": MECHANISM_ERROR, "detail": str(exc)})
        return EXIT[MECHANISM_ERROR]
    try:
        return _dispatch(supervisor, args)
    except Refused as refusal:
        _emit(
            {
                "policy": POLICY_ID,
                "refused": refusal.reason,
                "operation": refusal.operation,
                "next_action": refusal.next_action,
            }
        )
        return REFUSED_EXIT
    except MechanismError as exc:
        _emit({"policy": POLICY_ID, "status": MECHANISM_ERROR, "detail": str(exc)})
        return EXIT[MECHANISM_ERROR]


def _dispatch(supervisor: Supervisor, args) -> int:
    registry = supervisor.registry
    if args.action == "profiles":
        _emit(supervisor.profiles)
        return 0
    if args.action == "list":
        records = registry.records()
        pending = [r["id"] for r in records if r.get("status") not in TERMINAL]
        repeated = registry.mark_status_queries(pending) if pending else []
        if repeated:
            raise Refused(
                "the status of pending operations was already reported for the current "
                "user instruction; repeating it to detect completion is polling",
                "continue independent work or yield; the supervised wait delivers "
                "completion",
                repeated[0],
            )
        _emit(
            [
                {k: r.get(k) for k in ("id", "profile", "status", "reason")}
                for r in records
            ]
        )
        return 0
    if args.action in {"run", "submit"}:
        identity = _identity(args, supervisor)
        record = supervisor.submit(args.profile, identity, args.output)
        if args.action == "submit":
            _emit(
                {
                    "policy": POLICY_ID,
                    "operation": record["id"],
                    "status": record["status"],
                    "next_action": next_action(record, supervisor),
                }
            )
            return 0
        result = supervisor.wait(record["id"])
        _emit(result.as_dict())
        return result.exit_code
    if args.action == "wait":
        result = supervisor.wait(args.operation)
        _emit(result.as_dict())
        return result.exit_code
    if args.action == "result":
        record = registry.load(args.operation)
        if record["status"] not in TERMINAL:
            repeated = registry.mark_status_queries([args.operation])
            again = " again" if repeated else ""
            raise Refused(
                f"{args.operation} has not completed; its status was reported{again} "
                "for the current user instruction",
                next_action(record, supervisor),
                args.operation,
            )
        _emit(supervisor._result(record, 0.0).as_dict())
        return EXIT.get(record["status"], 13)
    if args.action == "abandon":
        record = supervisor.abandon(args.operation)
        _emit(
            {"policy": POLICY_ID, "operation": record["id"], "status": record["status"]}
        )
        return 0
    raise AssertionError(args.action)


def _identity(args, supervisor) -> dict:
    profile = supervisor.profiles.get(args.profile)
    if profile is None:
        raise Refused(
            f"no operation profile {args.profile!r}",
            "report that this operation has no supported completion mechanism; do not "
            "wait for it with an agent-written loop",
        )
    command = list(args.argv)
    if command[:1] == ["--"]:
        command = command[1:]
    if args.profile == "github-actions-run":
        if not (args.run_id and args.repo and args.head_sha):
            raise Refused(
                "github-actions-run needs --run-id, --repo and --head-sha: a run's "
                "success is verification only for the source commit it binds",
                "supply all three, with the full commit SHA the run must test",
            )
        if not re.fullmatch(r"[0-9a-fA-F]{40}", args.head_sha):
            raise Refused(
                "--head-sha must be a full 40-character commit SHA",
                "supply the full commit SHA the run must test",
            )
        return {
            "run_id": args.run_id,
            "repository": args.repo,
            "head_sha": args.head_sha.lower(),
        }
    if not command:
        raise Refused(f"{args.profile} needs a command after --", "supply the command")
    return {"argv": command, "cwd": str(Path.cwd())}


def _emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    sys.exit(main())
