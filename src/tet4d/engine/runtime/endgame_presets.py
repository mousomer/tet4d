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

ENDGAME_BOUNDARY_RESPONSE_ESCAPE: Final[str] = "escape"
ENDGAME_BOUNDARY_RESPONSE_BOUNCE: Final[str] = "bounce"
ENDGAME_BOUNDARY_RESPONSES: Final[tuple[str, ...]] = (
    ENDGAME_BOUNDARY_RESPONSE_ESCAPE,
    ENDGAME_BOUNDARY_RESPONSE_BOUNCE,
)

ENDGAME_PARTICLE_COLLISIONS_OFF: Final[str] = "off"
ENDGAME_PARTICLE_COLLISIONS_ON: Final[str] = "on"
ENDGAME_PARTICLE_COLLISION_MODES: Final[tuple[str, ...]] = (
    ENDGAME_PARTICLE_COLLISIONS_OFF,
    ENDGAME_PARTICLE_COLLISIONS_ON,
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


def normalize_endgame_boundary_response(
    value: object,
    *,
    default: str = ENDGAME_BOUNDARY_RESPONSE_ESCAPE,
) -> str:
    normalized = str(value).strip().lower()
    if normalized not in ENDGAME_BOUNDARY_RESPONSES:
        return str(default)
    return normalized


def normalize_endgame_particle_collisions(
    value: object,
    *,
    default: str = ENDGAME_PARTICLE_COLLISIONS_OFF,
) -> str:
    normalized = str(value).strip().lower()
    if normalized not in ENDGAME_PARTICLE_COLLISION_MODES:
        return str(default)
    return normalized


def resolve_endgame_interaction_axes(
    *,
    boundary_response: object = None,
    particle_collisions: object = None,
    legacy_mode: object = None,
    default_boundary_response: str = ENDGAME_BOUNDARY_RESPONSE_ESCAPE,
    default_particle_collisions: str = ENDGAME_PARTICLE_COLLISIONS_OFF,
) -> tuple[str, str]:
    legacy_boundary = str(default_boundary_response)
    legacy_collisions = str(default_particle_collisions)
    normalized_legacy = str(legacy_mode).strip().lower()
    if normalized_legacy == "none":
        legacy_boundary = ENDGAME_BOUNDARY_RESPONSE_ESCAPE
        legacy_collisions = ENDGAME_PARTICLE_COLLISIONS_OFF
    elif normalized_legacy == "boundary":
        legacy_boundary = ENDGAME_BOUNDARY_RESPONSE_BOUNCE
        legacy_collisions = ENDGAME_PARTICLE_COLLISIONS_OFF
    elif normalized_legacy in {"full", "collide"}:
        legacy_boundary = ENDGAME_BOUNDARY_RESPONSE_BOUNCE
        legacy_collisions = ENDGAME_PARTICLE_COLLISIONS_ON
    return (
        normalize_endgame_boundary_response(
            legacy_boundary if boundary_response is None else boundary_response,
            default=str(default_boundary_response),
        ),
        normalize_endgame_particle_collisions(
            legacy_collisions if particle_collisions is None else particle_collisions,
            default=str(default_particle_collisions),
        ),
    )


__all__ = [
    "ENDGAME_BOUNDARY_RESPONSES",
    "ENDGAME_BOUNDARY_RESPONSE_BOUNCE",
    "ENDGAME_BOUNDARY_RESPONSE_ESCAPE",
    "ENDGAME_PARTICLE_COLLISION_MODES",
    "ENDGAME_PARTICLE_COLLISIONS_OFF",
    "ENDGAME_PARTICLE_COLLISIONS_ON",
    "ENDGAME_PRESET_DEFAULT_ORBIT",
    "ENDGAME_PRESET_IDS",
    "ENDGAME_PRESET_INVERT_ALL",
    "ENDGAME_PRESET_REQUIRED_IDS",
    "ENDGAME_PRESET_SPHERE",
    "ENDGAME_PRESET_WRAP_ALL",
    "normalize_endgame_boundary_response",
    "normalize_endgame_particle_collisions",
    "normalize_endgame_preset_id",
    "resolve_endgame_interaction_axes",
]
