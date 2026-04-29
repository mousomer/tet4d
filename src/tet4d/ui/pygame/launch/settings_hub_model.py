from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import pygame

from tet4d.engine.gameplay.api import (
    piece_set_2d_label_gameplay,
    piece_set_label_gameplay,
)
from tet4d.engine.gameplay.rotation_anim import (
    ROTATION_ANIMATION_MODE_CELLWISE_SLIDING,
    ROTATION_ANIMATION_MODE_RIGID_PIECE_ROTATION,
)
from tet4d.engine.runtime.endgame_presets import (
    ENDGAME_BOUNDARY_RESPONSES,
    ENDGAME_PARTICLE_COLLISION_MODES,
    ENDGAME_PRESET_IDS,
)
from tet4d.engine.runtime.menu_config import (
    menu_definition,
    menu_item_id,
    menu_items,
    resolve_runtime_menu_id,
    settings_menu_id,
    settings_option_labels,
    settings_top_level_categories,
    ui_copy_section,
)
from tet4d.engine.runtime.menu_settings_state import (
    DEFAULT_GAME_SEED,
    clamp_game_seed,
    default_analytics_settings,
    default_audio_settings,
    default_display_settings,
    default_mode_shared_gameplay_settings,
    get_analytics_settings,
    get_global_game_seed,
    get_overlay_transparency,
    mode_shared_gameplay_settings,
)
from tet4d.engine.topology_explorer.presets import (
    explorer_preset_sections_for_dimension,
    preset_display_label,
)
from tet4d.engine.ui_logic.view_modes import GridMode, ShadowMode
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.locked_cell_explosion.defaults_store import (
    ExplosionDefaults,
    mode_explosion_defaults,
)
from tet4d.ui.pygame.locked_cell_explosion.model import (
    EXPLOSION_BOUNDARY_RESPONSES,
    EXPLOSION_DIAGNOSTICS_MODES,
    EXPLOSION_MASS_MODES,
    EXPLOSION_PARTICLE_COLLISION_MODES,
    EXPLOSION_SPEED_PRESETS,
)

TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)
BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
_SETTINGS_OPTION_LABELS = settings_option_labels()
_RANDOM_MODE_LABELS = tuple(_SETTINGS_OPTION_LABELS["game_random_mode"])
_KICK_LEVEL_LABELS = tuple(_SETTINGS_OPTION_LABELS["game_kick_level"])
_ROTATION_ANIMATION_MODE_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["game_rotation_animation_mode"]
)
_ENDGAME_PRESET_LABELS = tuple(_SETTINGS_OPTION_LABELS["game_endgame_preset"])
_ENDGAME_BOUNDARY_RESPONSE_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["game_endgame_boundary_response"]
)
_ENDGAME_PARTICLE_COLLISION_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["game_endgame_particle_collisions"]
)
_EXPLOSION_TOPOLOGY_PRESET_2D_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_topology_preset_2d"]
)
_EXPLOSION_TOPOLOGY_PRESET_3D_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_topology_preset_3d"]
)
_EXPLOSION_TOPOLOGY_PRESET_4D_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_topology_preset_4d"]
)
_EXPLOSION_SNAPSHOT_SOURCE_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_snapshot_source"]
)
_EXPLOSION_PIECE_SET_2D_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_piece_set_2d"])
_EXPLOSION_PIECE_SET_3D_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_piece_set_3d"])
_EXPLOSION_PIECE_SET_4D_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_piece_set_4d"])
_EXPLOSION_PIECE_SHAPE_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_piece_shape"])
_EXPLOSION_VIEW_MODE_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_view_mode"])
_EXPLOSION_BOUNDARY_RESPONSE_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_boundary_response"]
)
_EXPLOSION_PARTICLE_COLLISIONS_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_particle_collisions"]
)
_EXPLOSION_MASS_MODE_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_mass_mode"])
_EXPLOSION_DIAGNOSTICS_MODE_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_diagnostics_mode"]
)
_EXPLOSION_GRID_MODE_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_grid_mode"])
_EXPLOSION_SHADOW_MODE_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_shadow_mode"])
_EXPLOSION_SPEED_PRESET_LABELS = tuple(_SETTINGS_OPTION_LABELS["explosion_speed_preset"])
_EXPLOSION_W_MOVEMENT_STYLE_LABELS = tuple(
    _SETTINGS_OPTION_LABELS["explosion_w_movement_animation_style"]
)
_ROTATION_ANIMATION_MODE_VALUES = (
    ROTATION_ANIMATION_MODE_CELLWISE_SLIDING,
    ROTATION_ANIMATION_MODE_RIGID_PIECE_ROTATION,
)
_ROTATION_ANIMATION_MODE_LABEL_BY_VALUE = dict(
    zip(_ROTATION_ANIMATION_MODE_VALUES, _ROTATION_ANIMATION_MODE_LABELS)
)
_SETTINGS_HUB_COPY = ui_copy_section("settings_hub")
_DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS = default_mode_shared_gameplay_settings("2d")
_RANDOM_MODE_DEFAULT = int(_DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["random_mode_index"])
_TOPOLOGY_ADVANCED_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["topology_advanced"]
)
_KICK_LEVEL_DEFAULT = int(_DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["kick_level_index"])
_ENDGAME_PRESET_DEFAULT = str(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["endgame_preset_id"]
)
_ENDGAME_BOUNDARY_RESPONSE_DEFAULT = str(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["endgame_boundary_response"]
)
_ENDGAME_PARTICLE_COLLISIONS_DEFAULT = str(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["endgame_particle_collisions"]
)
_ENDGAME_RELIC_SPEED_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["endgame_relic_speed_percent"]
)
_ENDGAME_SHATTER_SPEED_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["endgame_shatter_speed_percent"]
)
_AUTO_SPEEDUP_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["auto_speedup_enabled"]
)
_LINES_PER_LEVEL_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["lines_per_level"]
)
_ROTATION_ANIMATION_MODE_DEFAULT = str(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["rotation_animation_mode"]
)
_ROTATION_ANIMATION_DURATION_2D_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["rotation_animation_duration_ms_2d"]
)
_ROTATION_ANIMATION_DURATION_ND_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["rotation_animation_duration_ms_nd"]
)
_TRANSLATION_ANIMATION_DURATION_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["translation_animation_duration_ms"]
)
_EXPLOSION_SNAPSHOT_SOURCE_VALUES = (
    "single_piece",
    "single_cell",
    "piece_change",
    "inherited_current_state",
)
_EXPLOSION_VIEW_MODE_VALUES = (
    "board_native",
    "projection_reference",
)
_EXPLOSION_W_MOVEMENT_STYLE_VALUES = (
    "fade",
    "box_size",
)
_EXPLOSION_GRID_MODE_VALUES = (
    str(GridMode.OFF.value),
    str(GridMode.BOTTOM_BOUNDARY.value),
    str(GridMode.EDGE.value),
    str(GridMode.FULL.value),
    str(GridMode.HELPER.value),
    str(GridMode.ALL_BOUNDARIES.value),
)
_EXPLOSION_SHADOW_MODE_VALUES = (
    str(ShadowMode.OFF.value),
    str(ShadowMode.BOTTOM_BOUNDARY.value),
    str(ShadowMode.ALL_BOUNDARIES.value),
)
_EXPLOSION_SNAPSHOT_SOURCE_LABEL_BY_VALUE = dict(
    zip(_EXPLOSION_SNAPSHOT_SOURCE_VALUES, _EXPLOSION_SNAPSHOT_SOURCE_LABELS)
)
_EXPLOSION_VIEW_MODE_LABEL_BY_VALUE = dict(
    zip(_EXPLOSION_VIEW_MODE_VALUES, _EXPLOSION_VIEW_MODE_LABELS)
)
_EXPLOSION_BOUNDARY_RESPONSE_LABEL_BY_VALUE = dict(
    zip(EXPLOSION_BOUNDARY_RESPONSES, _EXPLOSION_BOUNDARY_RESPONSE_LABELS)
)
_EXPLOSION_PARTICLE_COLLISIONS_LABEL_BY_VALUE = dict(
    zip(EXPLOSION_PARTICLE_COLLISION_MODES, _EXPLOSION_PARTICLE_COLLISIONS_LABELS)
)
_EXPLOSION_MASS_MODE_LABEL_BY_VALUE = dict(
    zip(EXPLOSION_MASS_MODES, _EXPLOSION_MASS_MODE_LABELS)
)
_EXPLOSION_DIAGNOSTICS_LABEL_BY_VALUE = dict(
    zip(EXPLOSION_DIAGNOSTICS_MODES, _EXPLOSION_DIAGNOSTICS_MODE_LABELS)
)
_EXPLOSION_GRID_MODE_LABEL_BY_VALUE = dict(
    zip(_EXPLOSION_GRID_MODE_VALUES, _EXPLOSION_GRID_MODE_LABELS)
)
_EXPLOSION_SHADOW_MODE_LABEL_BY_VALUE = dict(
    zip(_EXPLOSION_SHADOW_MODE_VALUES, _EXPLOSION_SHADOW_MODE_LABELS)
)
_EXPLOSION_SPEED_PRESET_LABEL_BY_VALUE = dict(
    zip(EXPLOSION_SPEED_PRESETS, _EXPLOSION_SPEED_PRESET_LABELS)
)
_EXPLOSION_W_MOVEMENT_STYLE_LABEL_BY_VALUE = dict(
    zip(_EXPLOSION_W_MOVEMENT_STYLE_VALUES, _EXPLOSION_W_MOVEMENT_STYLE_LABELS)
)
_NUMERIC_TEXT_EDIT_ROWS = {
    "display_width",
    "display_height",
    "game_seed",
    "rotation_animation_duration_ms_2d",
    "rotation_animation_duration_ms_nd",
    "translation_animation_duration_ms",
}
_NUMERIC_TEXT_MAX_LENGTH = 16


@dataclass
class SettingsHubResult:
    screen: pygame.Surface
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    keep_running: bool
    dispatched_action_id: str = ""


@dataclass
class _UnifiedSettingsState:
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    overlay_transparency: float
    game_seed: int
    random_mode_index: int
    topology_advanced: int
    kick_level_index: int
    endgame_preset_id: str
    endgame_boundary_response: str
    endgame_particle_collisions: str
    endgame_relic_speed_percent: int
    endgame_shatter_speed_percent: int
    auto_speedup_enabled: int
    lines_per_level: int
    rotation_animation_mode: str
    rotation_animation_duration_ms_2d: int
    rotation_animation_duration_ms_nd: int
    translation_animation_duration_ms: int
    score_logging_enabled: bool
    explosion_defaults_2d: ExplosionDefaults
    explosion_defaults_3d: ExplosionDefaults
    explosion_defaults_4d: ExplosionDefaults
    original_audio: AudioSettings
    original_display: DisplaySettings
    original_overlay_transparency: float
    original_game_seed: int
    original_random_mode_index: int
    original_topology_advanced: int
    original_kick_level_index: int
    original_endgame_preset_id: str
    original_endgame_boundary_response: str
    original_endgame_particle_collisions: str
    original_endgame_relic_speed_percent: int
    original_endgame_shatter_speed_percent: int
    original_auto_speedup_enabled: int
    original_lines_per_level: int
    original_rotation_animation_mode: str
    original_rotation_animation_duration_ms_2d: int
    original_rotation_animation_duration_ms_nd: int
    original_translation_animation_duration_ms: int
    original_score_logging_enabled: bool
    original_explosion_defaults_2d: ExplosionDefaults
    original_explosion_defaults_3d: ExplosionDefaults
    original_explosion_defaults_4d: ExplosionDefaults
    page_stack: list[str]
    selected_by_page: dict[str, int]
    scroll_offset_by_page: dict[str, int]
    selected: int = 0
    scroll_offset: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    text_mode_row_key: str = ""
    text_mode_buffer: str = ""
    text_mode_replace_on_type: bool = False
    flash_row_key: str = ""
    flash_frames: int = 0
    saved: bool = False
    running: bool = True
    dispatched_action_id: str = ""
    topology_cache_file_count: int = 0
    topology_cache_size_bytes: int | None = None


def _configured_top_level_labels() -> tuple[str, ...]:
    return tuple(entry["label"] for entry in settings_top_level_categories())


def _top_level_settings_labels() -> tuple[str, ...]:
    return tuple(
        str(item.get("label", ""))
        for item in menu_items(settings_menu_id())
        if str(item.get("type", "")).lower() == "submenu"
    )


def _validate_unified_layout_against_policy() -> tuple[bool, str]:
    expected = _configured_top_level_labels()
    actual = _top_level_settings_labels()
    if expected == actual:
        return True, "Settings layout policy verified"
    return False, (
        "Settings layout mismatch: expected top-level categories "
        f"{', '.join(expected)} but UI renders {', '.join(actual)}"
    )


def settings_page_items(page_id: str) -> tuple[dict[str, Any], ...]:
    return tuple(menu_definition(page_id)["items"])


def selectable_indexes_for_items(
    items: tuple[dict[str, Any], ...],
) -> tuple[int, ...]:
    return tuple(
        idx
        for idx, item in enumerate(items)
        if str(item.get("type", "")).lower() not in {"section", "info"}
    )


def selectable_index_by_item_id_for_items(
    items: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    selectable = selectable_indexes_for_items(items)
    return {
        menu_item_id(items[row_idx]): selectable_idx
        for selectable_idx, row_idx in enumerate(selectable)
    }


def settings_title_for_page(page_id: str) -> str:
    return str(menu_definition(page_id)["title"])


def _audio_defaults() -> AudioSettings:
    defaults = default_audio_settings()
    return AudioSettings(
        master_volume=float(defaults["master_volume"]),
        sfx_volume=float(defaults["sfx_volume"]),
        mute=bool(defaults["mute"]),
    )


def _display_defaults() -> DisplaySettings:
    defaults = default_display_settings()
    return DisplaySettings(
        fullscreen=bool(defaults["fullscreen"]),
        windowed_size=tuple(defaults["windowed_size"]),
    )


def _analytics_defaults() -> bool:
    defaults = default_analytics_settings()
    return bool(defaults["score_logging_enabled"])


def _clone_audio_settings(settings: AudioSettings) -> AudioSettings:
    return AudioSettings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


def _clone_display_settings(settings: DisplaySettings) -> DisplaySettings:
    return DisplaySettings(
        fullscreen=settings.fullscreen,
        windowed_size=settings.windowed_size,
    )


def current_settings_page_id(state: _UnifiedSettingsState) -> str:
    return state.page_stack[-1]


def current_settings_page_items(state: _UnifiedSettingsState) -> tuple[dict[str, Any], ...]:
    return settings_page_items(current_settings_page_id(state))


def current_page_selectable_indexes(state: _UnifiedSettingsState) -> tuple[int, ...]:
    return selectable_indexes_for_items(current_settings_page_items(state))


def _unified_row_key(state: _UnifiedSettingsState) -> str:
    items = current_settings_page_items(state)
    selectable = current_page_selectable_indexes(state)
    if not selectable:
        return ""
    safe_selected = max(0, min(len(selectable) - 1, int(state.selected)))
    return menu_item_id(items[selectable[safe_selected]])


def _set_unified_status(
    state: _UnifiedSettingsState, message: str, *, is_error: bool = False
) -> None:
    state.status = message
    state.status_error = is_error


def _mark_unified_dirty(state: _UnifiedSettingsState) -> None:
    state.saved = False


def _is_unified_text_mode(state: _UnifiedSettingsState) -> bool:
    return bool(state.text_mode_row_key)


def _text_mode_numeric_value(state: _UnifiedSettingsState, row_key: str) -> int | None:
    if row_key == "display_width":
        return int(state.display_settings.windowed_size[0])
    if row_key == "display_height":
        return int(state.display_settings.windowed_size[1])
    if row_key == "game_seed":
        return int(state.game_seed)
    if row_key == "rotation_animation_duration_ms_2d":
        return int(state.rotation_animation_duration_ms_2d)
    if row_key == "rotation_animation_duration_ms_nd":
        return int(state.rotation_animation_duration_ms_nd)
    if row_key == "translation_animation_duration_ms":
        return int(state.translation_animation_duration_ms)
    return None


def _format_cache_bytes(total_bytes: int) -> str:
    size = max(0, int(total_bytes))
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024.0:.1f} KB"
    return f"{size / (1024.0 * 1024.0):.2f} MB"


def _explosion_mode_and_field(row_key: str) -> tuple[str, str] | None:
    parts = str(row_key).strip().lower().split("_")
    if len(parts) < 3 or parts[0] != "explosion":
        return None
    mode_key = str(parts[1])
    if mode_key not in {"2d", "3d", "4d"}:
        return None
    field = "_".join(parts[2:])
    return mode_key, field


def _explosion_defaults_for_mode(
    state: _UnifiedSettingsState, mode_key: str
) -> ExplosionDefaults:
    if mode_key == "2d":
        return state.explosion_defaults_2d
    if mode_key == "3d":
        return state.explosion_defaults_3d
    return state.explosion_defaults_4d


@lru_cache(maxsize=8)
def _topology_preset_label_by_id(dimension: int) -> dict[str, str]:
    dim = int(dimension)
    by_id: dict[str, str] = {}
    for section in explorer_preset_sections_for_dimension(dim):
        for preset in section.presets:
            by_id[str(preset.preset_id)] = preset_display_label(
                preset,
                include_group=False,
                include_unsafe=True,
            )
    return by_id


def _explosion_cell_origin_value_text(defaults: ExplosionDefaults, field: str) -> str:
    axis = field.split("_")[-1]
    axis_index = {"x": 0, "y": 1, "z": 2, "w": 3}.get(axis)
    if axis_index is None:
        return ""
    value = int(defaults.cell_origin[axis_index])
    return "Auto" if value < 0 else str(value)


def _explosion_topology_preset_value_text(
    defaults: ExplosionDefaults, *, dimension: int
) -> str:
    preset_id = str(defaults.topology_preset_id)
    if not preset_id:
        return "Default"
    return _topology_preset_label_by_id(int(dimension)).get(preset_id, preset_id)


def _explosion_piece_set_value_text(defaults: ExplosionDefaults, *, dimension: int) -> str:
    piece_set_id = str(defaults.piece_set_id)
    if not piece_set_id:
        return "Default"
    if int(dimension) == 2:
        return piece_set_2d_label_gameplay(piece_set_id)
    return piece_set_label_gameplay(piece_set_id)


def _explosion_value_text(state: _UnifiedSettingsState, row_key: str) -> str:
    mode_and_field = _explosion_mode_and_field(row_key)
    if mode_and_field is None:
        return ""
    mode_key, field = mode_and_field
    defaults = _explosion_defaults_for_mode(state, mode_key)
    dimension = int(mode_key[0])
    if field.startswith("cell_origin_"):
        return _explosion_cell_origin_value_text(defaults, field)

    handlers = {
        "topology_preset_id": lambda: _explosion_topology_preset_value_text(
            defaults, dimension=dimension
        ),
        "snapshot_source_id": lambda: _EXPLOSION_SNAPSHOT_SOURCE_LABEL_BY_VALUE.get(
            str(defaults.snapshot_source_id), str(defaults.snapshot_source_id)
        ),
        "piece_set_id": lambda: _explosion_piece_set_value_text(
            defaults, dimension=dimension
        ),
        "piece_shape_name": lambda: (
            "Default" if not str(defaults.piece_shape_name) else str(defaults.piece_shape_name)
        ),
        "view_mode": lambda: _EXPLOSION_VIEW_MODE_LABEL_BY_VALUE.get(
            str(defaults.view_mode), str(defaults.view_mode)
        ),
        "boundary_response": lambda: _EXPLOSION_BOUNDARY_RESPONSE_LABEL_BY_VALUE.get(
            str(defaults.boundary_response), str(defaults.boundary_response)
        ),
        "particle_collisions": lambda: _EXPLOSION_PARTICLE_COLLISIONS_LABEL_BY_VALUE.get(
            str(defaults.particle_collisions), str(defaults.particle_collisions)
        ),
        "mass_mode": lambda: _EXPLOSION_MASS_MODE_LABEL_BY_VALUE.get(
            str(defaults.mass_mode), str(defaults.mass_mode)
        ),
        "base_mass": lambda: f"{float(defaults.base_mass):.2f}",
        "random_mass_min": lambda: f"{float(defaults.random_mass_min):.2f}",
        "random_mass_max": lambda: f"{float(defaults.random_mass_max):.2f}",
        "collision_elasticity": lambda: f"{float(defaults.collision_elasticity):.2f}",
        "diagnostics_mode": lambda: _EXPLOSION_DIAGNOSTICS_LABEL_BY_VALUE.get(
            str(defaults.diagnostics_mode), str(defaults.diagnostics_mode)
        ),
        "grid_mode": lambda: _EXPLOSION_GRID_MODE_LABEL_BY_VALUE.get(
            str(defaults.grid_mode), str(defaults.grid_mode)
        ),
        "shadow_mode": lambda: _EXPLOSION_SHADOW_MODE_LABEL_BY_VALUE.get(
            str(defaults.shadow_mode), str(defaults.shadow_mode)
        ),
        "trace_enabled": lambda: "ON" if bool(defaults.trace_enabled) else "OFF",
        "trace_retention_ms": lambda: f"{int(round(float(defaults.trace_retention_ms)))} ms",
        "speed_preset": lambda: _EXPLOSION_SPEED_PRESET_LABEL_BY_VALUE.get(
            str(defaults.speed_preset), str(defaults.speed_preset)
        ),
        "w_movement_animation_style": lambda: _EXPLOSION_W_MOVEMENT_STYLE_LABEL_BY_VALUE.get(
            str(defaults.w_movement_animation_style), str(defaults.w_movement_animation_style)
        ),
        "endgame_live_cell_fraction": lambda: f"{int(round(float(defaults.endgame_live_cell_fraction) * 100.0))}%",
        "sound_enabled": lambda: "ON" if bool(defaults.sound_enabled) else "OFF",
        "seed": lambda: str(int(defaults.seed)),
    }
    handler = handlers.get(field)
    if handler is None:
        return ""
    return str(handler())


def _unified_value_text(state: _UnifiedSettingsState, row_key: str) -> str:
    def _duration_text(value: int) -> str:
        return "Off" if int(value) <= 0 else f"{int(value)} ms"

    if _is_unified_text_mode(state) and row_key == state.text_mode_row_key:
        return f"{state.text_mode_buffer}_"
    static_values = {
        "audio_master": f"{int(state.audio_settings.master_volume * 100)}%",
        "audio_sfx": f"{int(state.audio_settings.sfx_volume * 100)}%",
        "audio_mute": "ON" if state.audio_settings.mute else "OFF",
        "display_fullscreen": "ON" if state.display_settings.fullscreen else "OFF",
        "display_width": str(state.display_settings.windowed_size[0]),
        "display_height": str(state.display_settings.windowed_size[1]),
        "display_overlay_transparency": (
            f"{int(round(state.overlay_transparency * 100.0))}%"
        ),
        "game_seed": str(int(state.game_seed)),
        "analytics_score_logging": "ON" if state.score_logging_enabled else "OFF",
        "rotation_animation_mode": rotation_animation_mode_label(
            state.rotation_animation_mode
        ),
        "kick_level_index": _KICK_LEVEL_LABELS[
            max(0, min(len(_KICK_LEVEL_LABELS) - 1, int(state.kick_level_index)))
        ],
        "rotation_animation_duration_ms_2d": _duration_text(
            int(state.rotation_animation_duration_ms_2d)
        ),
        "rotation_animation_duration_ms_nd": _duration_text(
            int(state.rotation_animation_duration_ms_nd)
        ),
        "translation_animation_duration_ms": _duration_text(
            int(state.translation_animation_duration_ms)
        ),
        "endgame_relic_speed_percent": f"{int(state.endgame_relic_speed_percent)}%",
        "endgame_shatter_speed_percent": (
            f"{int(state.endgame_shatter_speed_percent)}%"
        ),
        "auto_speedup_enabled": "ON" if int(state.auto_speedup_enabled) else "OFF",
        "lines_per_level": str(int(state.lines_per_level)),
        "topology_cache_measure": (
            "Enter"
            if state.topology_cache_size_bytes is None
            else f"{int(state.topology_cache_file_count)} files / "
            f"{_format_cache_bytes(int(state.topology_cache_size_bytes))}"
        ),
        "topology_cache_clear": "Enter",
    }
    value = static_values.get(row_key)
    if value is not None:
        return value
    if row_key == "game_random_mode":
        safe_index = max(
            0,
            min(len(_RANDOM_MODE_LABELS) - 1, int(state.random_mode_index)),
        )
        return _RANDOM_MODE_LABELS[safe_index]
    if row_key == "endgame_preset_id":
        label_by_value = dict(zip(ENDGAME_PRESET_IDS, _ENDGAME_PRESET_LABELS))
        return label_by_value.get(
            str(state.endgame_preset_id), str(state.endgame_preset_id)
        )
    if row_key == "endgame_boundary_response":
        label_by_value = dict(
            zip(ENDGAME_BOUNDARY_RESPONSES, _ENDGAME_BOUNDARY_RESPONSE_LABELS)
        )
        return label_by_value.get(
            str(state.endgame_boundary_response),
            str(state.endgame_boundary_response),
        )
    if row_key == "endgame_particle_collisions":
        label_by_value = dict(
            zip(
                ENDGAME_PARTICLE_COLLISION_MODES,
                _ENDGAME_PARTICLE_COLLISION_LABELS,
            )
        )
        return label_by_value.get(
            str(state.endgame_particle_collisions),
            str(state.endgame_particle_collisions),
        )
    if row_key == "game_topology_advanced":
        return "ON" if int(state.topology_advanced) else "OFF"
    if row_key.startswith("explosion_"):
        return _explosion_value_text(state, row_key)
    return ""


def rotation_animation_mode_label(value: str) -> str:
    return _ROTATION_ANIMATION_MODE_LABEL_BY_VALUE.get(str(value), str(value))


def build_unified_settings_state(
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
    initial_page_id: str | None = None,
    initial_item_id: str | None = None,
) -> _UnifiedSettingsState:
    score_logging_enabled = bool(get_analytics_settings()["score_logging_enabled"])
    overlay_transparency = get_overlay_transparency()
    game_seed = int(
        clamp_game_seed(
            get_global_game_seed(),
            default=int(DEFAULT_GAME_SEED),
        )
    )
    mode_gameplay = mode_shared_gameplay_settings("2d")
    random_mode_index = int(mode_gameplay["random_mode_index"])
    topology_advanced = int(mode_gameplay["topology_advanced"])
    kick_level_index = int(mode_gameplay["kick_level_index"])
    endgame_preset_id = str(mode_gameplay["endgame_preset_id"])
    endgame_boundary_response = str(mode_gameplay["endgame_boundary_response"])
    endgame_particle_collisions = str(mode_gameplay["endgame_particle_collisions"])
    endgame_relic_speed_percent = int(mode_gameplay["endgame_relic_speed_percent"])
    endgame_shatter_speed_percent = int(
        mode_gameplay["endgame_shatter_speed_percent"]
    )
    auto_speedup_enabled = int(mode_gameplay["auto_speedup_enabled"])
    lines_per_level = int(mode_gameplay["lines_per_level"])
    rotation_animation_mode = str(mode_gameplay["rotation_animation_mode"])
    rotation_animation_duration_ms_2d = int(
        mode_gameplay["rotation_animation_duration_ms_2d"]
    )
    rotation_animation_duration_ms_nd = int(
        mode_gameplay["rotation_animation_duration_ms_nd"]
    )
    translation_animation_duration_ms = int(
        mode_gameplay["translation_animation_duration_ms"]
    )
    explosion_defaults_2d = mode_explosion_defaults("2d")
    explosion_defaults_3d = mode_explosion_defaults("3d")
    explosion_defaults_4d = mode_explosion_defaults("4d")
    requested_page = str(initial_page_id or settings_menu_id()).strip().lower()
    requested_item = str(initial_item_id or "").strip().lower()
    start_page = resolve_runtime_menu_id(
        requested_page or settings_menu_id(),
        item_id=requested_item or None,
        fallback_menu_id=settings_menu_id(),
    )
    state = _UnifiedSettingsState(
        audio_settings=_clone_audio_settings(audio_settings),
        display_settings=_clone_display_settings(display_settings),
        overlay_transparency=overlay_transparency,
        game_seed=game_seed,
        random_mode_index=random_mode_index,
        topology_advanced=topology_advanced,
        kick_level_index=kick_level_index,
        endgame_preset_id=endgame_preset_id,
        endgame_boundary_response=endgame_boundary_response,
        endgame_particle_collisions=endgame_particle_collisions,
        endgame_relic_speed_percent=endgame_relic_speed_percent,
        endgame_shatter_speed_percent=endgame_shatter_speed_percent,
        auto_speedup_enabled=auto_speedup_enabled,
        lines_per_level=lines_per_level,
        rotation_animation_mode=rotation_animation_mode,
        rotation_animation_duration_ms_2d=rotation_animation_duration_ms_2d,
        rotation_animation_duration_ms_nd=rotation_animation_duration_ms_nd,
        translation_animation_duration_ms=translation_animation_duration_ms,
        score_logging_enabled=score_logging_enabled,
        explosion_defaults_2d=explosion_defaults_2d,
        explosion_defaults_3d=explosion_defaults_3d,
        explosion_defaults_4d=explosion_defaults_4d,
        original_audio=_clone_audio_settings(audio_settings),
        original_display=_clone_display_settings(display_settings),
        original_overlay_transparency=overlay_transparency,
        original_game_seed=game_seed,
        original_random_mode_index=random_mode_index,
        original_topology_advanced=topology_advanced,
        original_kick_level_index=kick_level_index,
        original_endgame_preset_id=endgame_preset_id,
        original_endgame_boundary_response=endgame_boundary_response,
        original_endgame_particle_collisions=endgame_particle_collisions,
        original_endgame_relic_speed_percent=endgame_relic_speed_percent,
        original_endgame_shatter_speed_percent=endgame_shatter_speed_percent,
        original_auto_speedup_enabled=auto_speedup_enabled,
        original_lines_per_level=lines_per_level,
        original_rotation_animation_mode=rotation_animation_mode,
        original_rotation_animation_duration_ms_2d=rotation_animation_duration_ms_2d,
        original_rotation_animation_duration_ms_nd=rotation_animation_duration_ms_nd,
        original_translation_animation_duration_ms=translation_animation_duration_ms,
        original_score_logging_enabled=score_logging_enabled,
        original_explosion_defaults_2d=explosion_defaults_2d,
        original_explosion_defaults_3d=explosion_defaults_3d,
        original_explosion_defaults_4d=explosion_defaults_4d,
        page_stack=[start_page],
        selected_by_page={},
        scroll_offset_by_page={},
    )
    items = settings_page_items(start_page)
    selectable = selectable_index_by_item_id_for_items(items)
    if initial_item_id:
        selected = selectable.get(str(initial_item_id).strip().lower())
        if selected is not None:
            state.selected = selected
    state.selected_by_page[start_page] = int(state.selected)
    state.scroll_offset_by_page[start_page] = 0
    return state
