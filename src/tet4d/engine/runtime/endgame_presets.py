from __future__ import annotations

from typing import Final

ENDGAME_PRESET_DEFAULT_ORBIT: Final[str] = "default_orbit"
ENDGAME_PRESET_WRAP_ALL: Final[str] = "wrap_all"
ENDGAME_PRESET_INVERT_ALL: Final[str] = "invert_all"
ENDGAME_PRESET_SPHERE: Final[str] = "sphere"

ENDGAME_PRESET_IDS: Final[tuple[str, ...]] = (
    ENDGAME_PRESET_DEFAULT_ORBIT,
    ENDGAME_PRESET_WRAP_ALL,
    ENDGAME_PRESET_INVERT_ALL,
    ENDGAME_PRESET_SPHERE,
)
ENDGAME_PRESET_REQUIRED_IDS: Final[tuple[str, ...]] = (
    ENDGAME_PRESET_WRAP_ALL,
    ENDGAME_PRESET_INVERT_ALL,
    ENDGAME_PRESET_SPHERE,
)

ENDGAME_INTERACTION_NONE: Final[str] = "none"
ENDGAME_INTERACTION_COLLIDE: Final[str] = "collide"
ENDGAME_INTERACTION_MODES: Final[tuple[str, ...]] = (
    ENDGAME_INTERACTION_NONE,
    ENDGAME_INTERACTION_COLLIDE,
)


def normalize_endgame_preset_id(
    value: object,
    *,
    default: str = ENDGAME_PRESET_DEFAULT_ORBIT,
) -> str:
    normalized = str(value).strip().lower()
    if normalized not in ENDGAME_PRESET_IDS:
        return str(default)
    return normalized


def normalize_endgame_interaction_mode(
    value: object,
    *,
    default: str = ENDGAME_INTERACTION_NONE,
) -> str:
    normalized = str(value).strip().lower()
    if normalized not in ENDGAME_INTERACTION_MODES:
        return str(default)
    return normalized


__all__ = [
    "ENDGAME_INTERACTION_COLLIDE",
    "ENDGAME_INTERACTION_MODES",
    "ENDGAME_INTERACTION_NONE",
    "ENDGAME_PRESET_DEFAULT_ORBIT",
    "ENDGAME_PRESET_IDS",
    "ENDGAME_PRESET_INVERT_ALL",
    "ENDGAME_PRESET_REQUIRED_IDS",
    "ENDGAME_PRESET_SPHERE",
    "ENDGAME_PRESET_WRAP_ALL",
    "normalize_endgame_interaction_mode",
    "normalize_endgame_preset_id",
]
