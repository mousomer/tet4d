from __future__ import annotations

from typing import Literal

CELLWISE_FREE = "cellwise_free"
RIGID = "rigid"

ExplorerMovementPolicy = Literal["cellwise_free", "rigid"]


def normalize_explorer_movement_policy(value: str) -> ExplorerMovementPolicy:
    normalized = str(value).strip().lower()
    if normalized not in {CELLWISE_FREE, RIGID}:
        raise ValueError(f"unsupported explorer movement policy: {value!r}")
    return normalized


def explorer_movement_policy_from_rigid_play_enabled(
    rigid_play_enabled: bool | None,
) -> ExplorerMovementPolicy:
    return RIGID if bool(rigid_play_enabled) else CELLWISE_FREE


__all__ = [
    "CELLWISE_FREE",
    "RIGID",
    "ExplorerMovementPolicy",
    "explorer_movement_policy_from_rigid_play_enabled",
    "normalize_explorer_movement_policy",
]
