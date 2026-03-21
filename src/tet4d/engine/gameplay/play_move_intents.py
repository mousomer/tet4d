from __future__ import annotations

TRANSLATION_INTENT = "translation"
ROTATION_INTENT = "rotation"
GRAVITY_INTENT = "gravity"
SOFT_DROP_INTENT = "soft_drop"
HARD_DROP_INTENT = "hard_drop"

DROP_INTENTS = frozenset(
    (
        GRAVITY_INTENT,
        SOFT_DROP_INTENT,
        HARD_DROP_INTENT,
    )
)


def is_drop_intent(intent: str) -> bool:
    return str(intent) in DROP_INTENTS


def crosses_gravity_seam(step_result: object, *, gravity_axis: int) -> bool:
    for cell_step in getattr(step_result, "cell_steps", ()):
        traversal = getattr(cell_step, "traversal", None)
        if traversal is None:
            continue
        if (
            int(traversal.source_boundary.axis) == int(gravity_axis)
            or int(traversal.target_boundary.axis) == int(gravity_axis)
        ):
            return True
    return False


__all__ = [
    "DROP_INTENTS",
    "GRAVITY_INTENT",
    "HARD_DROP_INTENT",
    "ROTATION_INTENT",
    "SOFT_DROP_INTENT",
    "TRANSLATION_INTENT",
    "crosses_gravity_seam",
    "is_drop_intent",
]
