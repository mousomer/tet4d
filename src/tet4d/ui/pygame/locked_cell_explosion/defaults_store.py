from __future__ import annotations

from dataclasses import asdict, dataclass

from tet4d.engine.runtime.menu_settings_state import (
    load_app_settings_payload,
    save_app_settings_payload,
)
from tet4d.engine.ui_logic.view_modes import GridMode, ShadowMode

from .model import (
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_DIAGNOSTICS_MODE_OFF,
    EXPLOSION_MASS_MODE_UNIFORM,
    EXPLOSION_PARTICLE_COLLISIONS_OFF,
    EXPLOSION_SPEED_NORMAL,
    EXPLOSION_TRAIL_MAX_LIFETIME_MS,
    clamp_collision_elasticity,
    clamp_mass_value,
    clamp_trace_retention_ms,
    normalize_boundary_response,
    normalize_diagnostics_mode,
    normalize_mass_mode,
    normalize_mass_range,
    normalize_particle_collisions,
    normalize_speed_preset,
)

_MODE_KEYS = ("2d", "3d", "4d")
_VIEW_MODES = ("board_native", "projection_reference")
_SNAPSHOT_SOURCES = (
    "single_piece",
    "single_cell",
    "piece_change",
    "inherited_current_state",
)
_W_MOVEMENT_ANIMATION_STYLES = ("fade", "box_size")


@dataclass(frozen=True)
class ExplosionDefaults:
    topology_preset_id: str = ""
    snapshot_source_id: str = "single_piece"
    piece_set_id: str = ""
    piece_shape_name: str = ""
    cell_origin: tuple[int, int, int, int] = (-1, -1, -1, -1)
    view_mode: str = "board_native"
    boundary_response: str = EXPLOSION_BOUNDARY_RESPONSE_ESCAPE
    particle_collisions: str = EXPLOSION_PARTICLE_COLLISIONS_OFF
    mass_mode: str = EXPLOSION_MASS_MODE_UNIFORM
    base_mass: float = 1.0
    random_mass_min: float = 0.75
    random_mass_max: float = 1.25
    collision_elasticity: float = 1.0
    diagnostics_mode: str = EXPLOSION_DIAGNOSTICS_MODE_OFF
    grid_mode: str = str(GridMode.FULL.value)
    shadow_mode: str = str(ShadowMode.OFF.value)
    trace_enabled: bool = False
    trace_retention_ms: float = EXPLOSION_TRAIL_MAX_LIFETIME_MS
    speed_preset: str = EXPLOSION_SPEED_NORMAL
    w_movement_animation_style: str = "fade"
    sound_enabled: bool = True
    seed: int = 1337


def default_explosion_defaults() -> ExplosionDefaults:
    return ExplosionDefaults()


def _normalize_mode_key(mode_key: str) -> str:
    normalized = str(mode_key).strip().lower()
    if normalized not in _MODE_KEYS:
        raise ValueError("mode_key must be one of: 2d, 3d, 4d")
    return normalized


def _normalize_string_choice(value: object, *, allowed: tuple[str, ...], default: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in allowed:
        return str(default)
    return normalized


def _normalize_cell_origin(value: object) -> tuple[int, int, int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return (-1, -1, -1, -1)
    normalized: list[int] = []
    for component in value:
        if isinstance(component, bool) or not isinstance(component, int):
            normalized.append(-1)
            continue
        normalized.append(int(component))
    return tuple(normalized)


def _coerce_seed(value: object, *, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return int(default)
    return max(0, int(value))


def coerce_explosion_defaults(
    raw: object,
    *,
    defaults: ExplosionDefaults | None = None,
) -> ExplosionDefaults:
    fallback = default_explosion_defaults() if defaults is None else defaults
    payload = raw if isinstance(raw, dict) else {}
    random_min, random_max = normalize_mass_range(
        payload.get("random_mass_min", fallback.random_mass_min),
        payload.get("random_mass_max", fallback.random_mass_max),
    )
    return ExplosionDefaults(
        topology_preset_id=str(payload.get("topology_preset_id", fallback.topology_preset_id)),
        snapshot_source_id=_normalize_string_choice(
            payload.get("snapshot_source_id", fallback.snapshot_source_id),
            allowed=_SNAPSHOT_SOURCES,
            default=fallback.snapshot_source_id,
        ),
        piece_set_id=str(payload.get("piece_set_id", fallback.piece_set_id)),
        piece_shape_name=str(payload.get("piece_shape_name", fallback.piece_shape_name)),
        cell_origin=_normalize_cell_origin(payload.get("cell_origin", fallback.cell_origin)),
        view_mode=_normalize_string_choice(
            payload.get("view_mode", fallback.view_mode),
            allowed=_VIEW_MODES,
            default=fallback.view_mode,
        ),
        boundary_response=normalize_boundary_response(
            payload.get("boundary_response", fallback.boundary_response),
            default=fallback.boundary_response,
        ),
        particle_collisions=normalize_particle_collisions(
            payload.get("particle_collisions", fallback.particle_collisions),
            default=fallback.particle_collisions,
        ),
        mass_mode=normalize_mass_mode(
            payload.get("mass_mode", fallback.mass_mode),
            default=fallback.mass_mode,
        ),
        base_mass=clamp_mass_value(payload.get("base_mass", fallback.base_mass)),
        random_mass_min=random_min,
        random_mass_max=random_max,
        collision_elasticity=clamp_collision_elasticity(
            payload.get("collision_elasticity", fallback.collision_elasticity)
        ),
        diagnostics_mode=normalize_diagnostics_mode(
            payload.get("diagnostics_mode", fallback.diagnostics_mode),
            default=fallback.diagnostics_mode,
        ),
        grid_mode=_normalize_string_choice(
            payload.get("grid_mode", fallback.grid_mode),
            allowed=tuple(str(value.value) for value in GridMode),
            default=fallback.grid_mode,
        ),
        shadow_mode=_normalize_string_choice(
            payload.get("shadow_mode", fallback.shadow_mode),
            allowed=tuple(str(value.value) for value in ShadowMode),
            default=fallback.shadow_mode,
        ),
        trace_enabled=bool(payload.get("trace_enabled", fallback.trace_enabled)),
        trace_retention_ms=clamp_trace_retention_ms(
            payload.get("trace_retention_ms", fallback.trace_retention_ms)
        ),
        speed_preset=normalize_speed_preset(
            payload.get("speed_preset", fallback.speed_preset),
            default=fallback.speed_preset,
        ),
        w_movement_animation_style=_normalize_string_choice(
            payload.get(
                "w_movement_animation_style",
                fallback.w_movement_animation_style,
            ),
            allowed=_W_MOVEMENT_ANIMATION_STYLES,
            default=fallback.w_movement_animation_style,
        ),
        sound_enabled=bool(payload.get("sound_enabled", fallback.sound_enabled)),
        seed=_coerce_seed(payload.get("seed", fallback.seed), default=fallback.seed),
    )


def serialize_explosion_defaults(defaults: ExplosionDefaults) -> dict[str, object]:
    payload = asdict(defaults)
    payload["cell_origin"] = list(defaults.cell_origin)
    return payload


def mode_explosion_defaults(mode_key: str) -> ExplosionDefaults:
    normalized_mode = _normalize_mode_key(mode_key)
    payload = load_app_settings_payload()
    defaults_section = payload.get("explosion_defaults", {})
    mode_payload = (
        defaults_section.get(normalized_mode, {})
        if isinstance(defaults_section, dict)
        else {}
    )
    return coerce_explosion_defaults(mode_payload)


def save_mode_explosion_defaults(
    mode_key: str,
    defaults: ExplosionDefaults,
) -> tuple[bool, str]:
    normalized_mode = _normalize_mode_key(mode_key)
    payload = load_app_settings_payload()
    explosion_defaults = payload.setdefault("explosion_defaults", {})
    if not isinstance(explosion_defaults, dict):
        explosion_defaults = {}
        payload["explosion_defaults"] = explosion_defaults
    explosion_defaults[normalized_mode] = serialize_explosion_defaults(
        coerce_explosion_defaults(serialize_explosion_defaults(defaults))
    )
    ok, message = save_app_settings_payload(payload)
    if not ok:
        return ok, message
    return True, f"Saved explosion defaults for {normalized_mode}"


__all__ = [
    "ExplosionDefaults",
    "coerce_explosion_defaults",
    "default_explosion_defaults",
    "mode_explosion_defaults",
    "save_mode_explosion_defaults",
    "serialize_explosion_defaults",
]
