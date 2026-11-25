"""Shared completion contract and explicit, bounded execution-trace review.

This does not intercept agent tools or enable transcript collection. Callers
provide normalized observations; absent completion remains unknown. Command
observations are classified with the shared command policy, the same engine the
pack's PreToolUse adapters apply before execution.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.workspace_governance import command_policy, operation_supervisor

POLICY_ID = "supervised-completion-v3"
POLICY_PATH = "policies/execution.json"
REQUIRED = {
    "agent_wait_polling": "forbidden",
    "polling_definition": "repeated_status_log_file_or_process_queries_to_detect_completion",
    "repository_inspection": "permitted",
    "local_completion": "await_exit",
    "ownership": "pack_rules_profiles_mechanisms_supervisor_selection_and_state_adapters_execution_hooks_predispatch_denial",
    "operation_profiles": "policies/operation_profiles.json",
    "profile_before_start": "required",
    "profile_validation": "reject_incomplete_or_contradictory_before_start",
    "completion_selection": "first_available_in_profile_preference_order",
    "completion_delivery": "synchronous_return_notification_blocking_wait_or_controlled_continuation",
    "adapter_polling": "explicit_profile_authorization_when_no_preferred_mechanism_available",
    "agent_mechanism_choice": "forbidden",
    "fallback": "profile_authorized_only_preserving_identity_and_consumed_budget",
    "unsupported_completion": "report_limitation_no_agent_polling_fallback",
    "cadence_owner": "adapter",
    "service_polling": "approved_adapter_min_interval_backoff_request_limit_deadline",
    "concurrent_waits": "forbidden",
    "continuation": "existing_handle_enforced_blocking_interval",
    "repeated_immediate_pending": "adapter_fault_no_automatic_retry",
    "terminal_outcome": "success_failure_or_cancellation_with_evidence",
    "response_window_expiry": "continue_same_handle_within_remaining_budget",
    "budget_scope": "per_operation_persisted_across_waits_fallbacks_interfaces_and_sessions",
    "deadline_expiry": "pending_preserve_handle_no_restart_no_cancel",
    "budget_renewal": "new_user_instruction_bounded_renewals",
    "mechanism_failure": "report_error_no_fallback_keep_unrelated_work",
    "outcome_distinction": "response_window_deadline_budget_and_mechanism_failure_machine_readable",
    "decision_record": "mechanism_profile_version_transition_reasons_budgets_and_enforcement_errors",
    "status_queries": "supervisor_status_once_per_user_instruction",
    "denial_scope": "offending_action_only",
    "denial_content": "operation_and_permitted_next_action",
    "denial_followup": "independent_work_designated_mechanism_or_yield",
    "guard_failure": "block_wait_and_status_probes_only",
    "hook_state": "durable_across_turns_interfaces_and_compaction",
    "tool_watch_modes": "forbidden_outside_approved_adapters",
    "synthetic_waiting": "forbidden",
    "unmanaged_remote_state": "single_observation_then_pending_external",
    "reobservation": "requires_notification_event_or_user_instruction",
    "remote_wait": "only_when_declared_gate_requires",
    "non_success_states": "never_verification",
    "yield_handling": "resume_same_handle",
    "parallel_completion": "await_all_preserve_failures",
    "unknown_outcome": "never_success",
    "recovery": "reconnect_same_identity_no_automatic_redispatch",
    "undetermined_remote_invocation": "deny",
    "enforcement": "pretooluse_operation_registry_and_shared_command_policy",
    "coverage_declaration": "required",
}
EXPECTED = {
    "schema_version": 3,
    "id": POLICY_ID,
    "supersedes": "synchronous-completion-v2",
    "scope": "all_work_types_projects_roles_and_execution_modes",
    "primary_acceptance": "no_uncontrolled_agent_polling",
    "requirements": REQUIRED,
    "codes": {
        "violation": "NO_AUTONOMOUS_POLLING",
        "operation": "OPERATION_PENDING",
        "pending": "PENDING_EXTERNAL",
        "degraded": "GUARD_DEGRADED",
    },
}
OBSERVATION_RESULTS = {
    "pass": "success",
    "fail": "failure",
    "pending": "pending_external",
    "unknown": "unknown",
    "error": "error",
}
EPOCH_EVENTS = {"user_instruction", "notification", "state_change"}
MAX_EVENTS = 10000


def load_policy(pack: Path, manifest: dict) -> dict:
    binding = manifest.get("execution_policy")
    if binding != {"id": POLICY_ID, "path": POLICY_PATH}:
        raise ValueError("missing or incompatible shared execution policy binding")
    path = pack / POLICY_PATH
    if path.is_symlink() or not path.resolve().is_relative_to(pack.resolve()):
        raise ValueError("execution policy must be owned by the selected pack")
    raw = path.read_bytes()
    policy = json.loads(raw)
    if policy != EXPECTED:
        raise ValueError("shared execution policy is incomplete or weakened")
    profiles = pack / REQUIRED["operation_profiles"]
    if profiles.is_symlink() or not profiles.resolve().is_relative_to(pack.resolve()):
        raise ValueError("operation profiles must be owned by the selected pack")
    # Incomplete or contradictory profiles are rejected before any operation starts.
    operation_supervisor.load_profiles(profiles)
    return {**policy, "sha256": hashlib.sha256(raw).hexdigest()}


class _Review:
    def __init__(self) -> None:
        self.active: dict[str, dict] = {}
        self.outcomes: dict[str, str] = {}
        self.violations: list[str] = []
        self.blocked: list[dict] = []
        self.observations: list[dict] = []
        self.epoch = 0
        self.seen: set[tuple[int, str]] = set()

    def event(self, event: object) -> str | None:
        if not isinstance(event, dict):
            return "invalid_event"
        kind = event.get("event")
        if kind == "command":
            return self.command(event)
        if kind in EPOCH_EVENTS:
            self.boundary(event, kind)
            return None
        identity = event.get("id")
        if not isinstance(identity, str) or not identity:
            return "missing_identity"
        if kind == "start":
            return self.start(event)
        if identity not in self.active:
            return "unknown_execution"
        return self.continued(event)

    def boundary(self, event: dict, kind: str) -> None:
        """A notification, relevant event or user instruction authorizes one new
        observation: of the named execution, or of every execution if unnamed."""
        self.epoch += 1
        identity = event.get("id")
        targets = [identity] if identity in self.active else []
        if identity is None:
            targets = list(self.active)
        for name in targets:
            self.active[name]["authorized"] = True
            if kind == "notification":
                self.active[name]["notified"] = True

    # -- commands classified by the shared command policy
    def command(self, event: dict) -> str | None:
        decision = command_policy.evaluate(
            {"tool": event.get("tool", "Bash"), "command": event.get("command")}
        )
        if decision.decision != command_policy.ALLOW:
            if event.get("executed") is False:
                self.blocked.append(
                    {
                        "event": "execution.blocked_attempt",
                        "violation": decision.violation,
                        "decision": decision.decision,
                    }
                )
                return None
            return "polling_executed"
        if decision.state_change:
            self.epoch += 1
        for key in decision.observations:
            if (self.epoch, key) in self.seen:
                return "repeated_status_query"
            self.seen.add((self.epoch, key))
            self.observations.append({"target": key, "epoch": self.epoch})
        return None

    # -- execution identities
    def start(self, event: dict) -> str | None:
        identity = event["id"]
        if identity in self.active or identity in self.outcomes:
            return "duplicate_execution"
        if event.get("mode") not in {"local", "remote"}:
            return "unsupported_completion_mechanism"
        if event["mode"] == "remote" and not _sha(event.get("sha")):
            return "missing_remote_sha"
        self.active[identity] = {**event, "authorized": True, "notified": False}
        return None

    def continued(self, event: dict) -> str | None:
        operation = self.active[event["id"]]
        if event.get("sha", operation.get("sha")) != operation.get("sha"):
            return "remote_identity_changed"
        kind = event.get("event")
        if kind in {"watch", "log_tail", "redispatch"}:
            return "agent_polling_or_redispatch"
        if kind in {"observation", "status_query"}:
            return self.observe(event, operation)
        if kind in {"yield", "wait", "disconnect", "reconnect"}:
            return None
        return self.terminal(event, operation, kind)

    def observe(self, event: dict, operation: dict) -> str | None:
        if operation["mode"] != "remote":
            return "status_query_on_local_execution"
        if not operation["authorized"]:
            return "repeated_status_query"
        operation["authorized"] = False
        outcome = OBSERVATION_RESULTS.get(event.get("result"), "unknown")
        self.observations.append({"target": event["id"], "result": outcome})
        self.outcomes[event["id"]] = outcome
        if outcome in {"success", "failure"}:
            del self.active[event["id"]]
        return None

    def terminal(self, event: dict, operation: dict, kind: object) -> str | None:
        identity = event["id"]
        if kind == "finish":
            if operation["mode"] == "remote" and not operation["notified"]:
                return "missing_completion_mechanism"
            code = event.get("exit_code")
            if type(code) is not int:
                return "missing_exit_status"
            self.outcomes[identity] = "success" if code == 0 else "failure"
        elif kind in {"timeout", "cancel", "unsupported"}:
            self.outcomes[identity] = kind
        else:
            return "unsupported_event"
        del self.active[identity]
        return None

    def status(self) -> str:
        values = set(self.outcomes.values())
        if self.violations:
            return "violation"
        if values & {"failure", "timeout", "cancel", "unsupported"}:
            return "failure"
        if "pending_external" in values:
            return "pending_external"
        if self.active or not self.outcomes:
            return "unknown"
        return "success" if values == {"success"} else "unknown"

    def result(self) -> dict:
        return {
            "status": self.status(),
            "classifier": command_policy.VERSION,
            "violations": self.violations,
            "pending": sorted(self.active),
            "outcomes": self.outcomes,
            "blocked": self.blocked,
            "observations": self.observations,
        }


def _sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(c in "0123456789abcdef" for c in value)
    )


def review_execution(events: list[dict]) -> dict:
    """Review at most 10,000 explicit observations; absent completion is unknown.

    Remote work completes through one authorized observation or a completion
    notification. A pending observation is terminal for that observation and
    reports ``pending_external``; another observation needs a notification,
    relevant state change or new user instruction first. Watches, log tails,
    redispatch, executed polling commands and repeated observations are
    violations. Commands denied before execution (``executed: false``) are
    reported as blocked attempts, not violations. This opt-in checker does not
    collect or intercept tool calls.
    """
    review = _Review()
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        review.violations.append("invalid_trace")
        return review.result()
    for event in events:
        violation = review.event(event)
        if violation:
            review.violations.append(violation)
    return review.result()
