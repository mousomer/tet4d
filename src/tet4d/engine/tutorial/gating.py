from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.runtime.settings_schema import sanitize_text

from .schema import TutorialStep

_MAX_ACTION_ID_LENGTH = 96


def sanitize_action_id(action_id: object) -> str:
    if not isinstance(action_id, str):
        return ""
    return sanitize_text(action_id, max_length=_MAX_ACTION_ID_LENGTH).strip().lower()


@dataclass(frozen=True)
class TutorialInputGate:
    allow: tuple[str, ...]
    deny: tuple[str, ...]

    def is_action_allowed(self, action_id: object) -> bool:
        action = sanitize_action_id(action_id)
        if not action:
            return False
        if action in self.deny:
            return False
        if not self.allow:
            return True
        return action in self.allow


def gate_for_step(step: TutorialStep) -> TutorialInputGate:
    return TutorialInputGate(allow=step.gating.allow, deny=step.gating.deny)
