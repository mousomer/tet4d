from __future__ import annotations

import random
from dataclasses import replace

import pygame

from tet4d.engine.gameplay.api import (
    piece_set_2d_options_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.gameplay.pieces2d import get_piece_bag_2d
from tet4d.engine.gameplay.pieces_nd import get_piece_shapes_nd
from tet4d.engine.runtime.endgame_presets import (
    ENDGAME_BOUNDARY_RESPONSES,
    ENDGAME_PARTICLE_COLLISION_MODES,
    ENDGAME_PRESET_IDS,
)
from tet4d.engine.runtime.menu_config import explorer_default_board_dims
from tet4d.engine.runtime.topology_cache import (
    clear_topology_cache,
    topology_cache_usage,
)
from tet4d.engine.runtime.menu_settings_state import (
    ANIMATION_DURATION_MS_STEP,
    DEFAULT_GAME_SEED,
    GAME_SEED_STEP,
    OVERLAY_TRANSPARENCY_STEP,
    clamp_animation_duration_ms,
    clamp_endgame_speed_percent,
    clamp_game_seed,
    clamp_overlay_transparency,
    default_display_settings,
    save_analytics_settings,
    save_audio_settings,
    save_display_settings,
    save_global_game_seed,
    save_shared_gameplay_settings,
)
from tet4d.engine.runtime.score_analyzer import set_score_analyzer_logging_enabled
from tet4d.engine.runtime.settings_schema import (
    ENDGAME_SPEED_PERCENT_STEP,
    clamp_lines_per_level,
    sanitize_text,
)
from tet4d.engine.topology_explorer import movement_graph as movement_graph_module
from tet4d.engine.topology_explorer.presets import explorer_preset_sections_for_dimension
from tet4d.engine.topology_explorer.transport_resolver import (
    build_explorer_transport_resolver,
)
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.menu.numeric_text_input import (
    append_numeric_text,
    parse_numeric_text,
)
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    apply_display_mode,
    normalize_display_settings,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx, set_audio_settings
from tet4d.ui.pygame.locked_cell_explosion.defaults_store import (
    coerce_explosion_defaults,
    default_explosion_defaults,
    save_mode_explosion_defaults,
    serialize_explosion_defaults,
)
from tet4d.ui.pygame.locked_cell_explosion.model import (
    EXPLOSION_BOUNDARY_RESPONSES,
    EXPLOSION_DIAGNOSTICS_MODES,
    EXPLOSION_MASS_MODES,
    EXPLOSION_PARTICLE_COLLISION_MODES,
    EXPLOSION_SPEED_PRESETS,
    clamp_collision_elasticity,
    clamp_mass_value,
    clamp_trace_retention_ms,
)

from .settings_hub_model import (
    _AUTO_SPEEDUP_DEFAULT,
    _KICK_LEVEL_DEFAULT,
    _KICK_LEVEL_LABELS,
    _LINES_PER_LEVEL_DEFAULT,
    _NUMERIC_TEXT_MAX_LENGTH,
    _RANDOM_MODE_DEFAULT,
    _RANDOM_MODE_LABELS,
    _ENDGAME_BOUNDARY_RESPONSE_DEFAULT,
    _ENDGAME_PARTICLE_COLLISIONS_DEFAULT,
    _ENDGAME_RELIC_SPEED_DEFAULT,
    _ENDGAME_PRESET_DEFAULT,
    _ENDGAME_SHATTER_SPEED_DEFAULT,
    _ROTATION_ANIMATION_MODE_DEFAULT,
    _ROTATION_ANIMATION_DURATION_2D_DEFAULT,
    _ROTATION_ANIMATION_DURATION_ND_DEFAULT,
    _ROTATION_ANIMATION_MODE_VALUES,
    _TOPOLOGY_ADVANCED_DEFAULT,
    _TRANSLATION_ANIMATION_DURATION_DEFAULT,
    _UnifiedSettingsState,
    _analytics_defaults,
    _audio_defaults,
    _clone_audio_settings,
    _clone_display_settings,
    _display_defaults,
    _is_unified_text_mode,
    _explosion_defaults_for_mode,
    _explosion_mode_and_field,
    _mark_unified_dirty,
    _set_unified_status,
    _text_mode_numeric_value,
    _unified_row_key,
)


def _sanitize_text(value: str, max_length: int) -> str:
    return sanitize_text(value, max_length=max_length)


def _flash_row(state: _UnifiedSettingsState, row_key: str) -> None:
    state.flash_row_key = str(row_key)
    state.flash_frames = 12


def _sync_audio_preview(settings) -> None:
    set_audio_settings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


def _sync_analytics_preview(score_logging_enabled: bool) -> None:
    set_score_analyzer_logging_enabled(bool(score_logging_enabled))


def _stop_unified_text_mode(
    state: _UnifiedSettingsState,
    *,
    clear_buffer: bool = True,
) -> None:
    if _is_unified_text_mode(state):
        pygame.key.stop_text_input()
    state.text_mode_row_key = ""
    state.text_mode_replace_on_type = False
    if clear_buffer:
        state.text_mode_buffer = ""


def _start_unified_numeric_text_mode(
    state: _UnifiedSettingsState,
    row_key: str,
) -> None:
    numeric_value = _text_mode_numeric_value(state, row_key)
    if numeric_value is None:
        return
    _stop_unified_text_mode(state)
    state.text_mode_row_key = row_key
    state.text_mode_buffer = str(int(numeric_value))
    state.text_mode_replace_on_type = True
    state.pending_reset_confirm = False
    pygame.key.start_text_input()
    _set_unified_status(
        state,
        "Type number, Enter apply, Esc cancel",
    )


def _apply_unified_numeric_text_value(state: _UnifiedSettingsState) -> bool:
    row_key = state.text_mode_row_key
    parsed = parse_numeric_text(
        state.text_mode_buffer,
        max_length=_NUMERIC_TEXT_MAX_LENGTH,
        sanitize_text=_sanitize_text,
    )
    if parsed is None:
        _set_unified_status(state, "Invalid numeric input", is_error=True)
        return False
    if row_key == "display_width":
        width = max(640, parsed)
        height = int(state.display_settings.windowed_size[1])
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (width, height),
        )
    elif row_key == "display_height":
        width = int(state.display_settings.windowed_size[0])
        height = max(480, parsed)
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (width, height),
        )
    elif row_key == "game_seed":
        state.game_seed = int(
            clamp_game_seed(
                parsed,
                default=int(DEFAULT_GAME_SEED),
            )
        )
    elif row_key == "rotation_animation_duration_ms_2d":
        state.rotation_animation_duration_ms_2d = int(
            clamp_animation_duration_ms(
                parsed,
                default=int(_ROTATION_ANIMATION_DURATION_2D_DEFAULT),
            )
        )
    elif row_key == "rotation_animation_duration_ms_nd":
        state.rotation_animation_duration_ms_nd = int(
            clamp_animation_duration_ms(
                parsed,
                default=int(_ROTATION_ANIMATION_DURATION_ND_DEFAULT),
            )
        )
    elif row_key == "translation_animation_duration_ms":
        state.translation_animation_duration_ms = int(
            clamp_animation_duration_ms(
                parsed,
                default=int(_TRANSLATION_ANIMATION_DURATION_DEFAULT),
            )
        )
    else:
        return False

    _mark_unified_dirty(state)
    _flash_row(state, row_key)
    _set_unified_status(state, "Updated value (not saved yet)")
    return True


def _handle_unified_text_input(state: _UnifiedSettingsState, text: str) -> None:
    if not _is_unified_text_mode(state):
        return
    state.text_mode_buffer, state.text_mode_replace_on_type = append_numeric_text(
        current_buffer=state.text_mode_buffer,
        incoming_text=text,
        replace_on_type=state.text_mode_replace_on_type,
        max_length=_NUMERIC_TEXT_MAX_LENGTH,
        sanitize_text=_sanitize_text,
    )


def _save_unified_settings(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    state.display_settings = normalize_display_settings(state.display_settings)
    screen = apply_display_mode(
        state.display_settings,
        preferred_windowed_size=state.display_settings.windowed_size,
    )
    ok_audio, msg_audio = save_audio_settings(
        master_volume=state.audio_settings.master_volume,
        sfx_volume=state.audio_settings.sfx_volume,
        mute=state.audio_settings.mute,
    )
    ok_display, msg_display = save_display_settings(
        fullscreen=state.display_settings.fullscreen,
        windowed_size=state.display_settings.windowed_size,
        overlay_transparency=state.overlay_transparency,
    )
    ok_analytics, msg_analytics = save_analytics_settings(
        score_logging_enabled=state.score_logging_enabled,
    )
    ok_game_seed, msg_game_seed = save_global_game_seed(int(state.game_seed))
    ok_gameplay_shared, msg_gameplay_shared = save_shared_gameplay_settings(
        random_mode_index=int(state.random_mode_index),
        topology_advanced=int(state.topology_advanced),
        kick_level_index=int(state.kick_level_index),
        endgame_preset_id=str(state.endgame_preset_id),
        endgame_boundary_response=str(state.endgame_boundary_response),
        endgame_particle_collisions=str(state.endgame_particle_collisions),
        endgame_relic_speed_percent=int(state.endgame_relic_speed_percent),
        endgame_shatter_speed_percent=int(state.endgame_shatter_speed_percent),
        auto_speedup_enabled=int(state.auto_speedup_enabled),
        lines_per_level=int(state.lines_per_level),
        rotation_animation_mode=str(state.rotation_animation_mode),
        rotation_animation_duration_ms_2d=int(state.rotation_animation_duration_ms_2d),
        rotation_animation_duration_ms_nd=int(state.rotation_animation_duration_ms_nd),
        translation_animation_duration_ms=int(state.translation_animation_duration_ms),
    )
    ok_explosion_2d = ok_explosion_3d = ok_explosion_4d = True
    msg_explosion_2d = msg_explosion_3d = msg_explosion_4d = ""
    if ok_audio and ok_display and ok_analytics and ok_game_seed and ok_gameplay_shared:
        ok_explosion_2d, msg_explosion_2d = save_mode_explosion_defaults(
            "2d", state.explosion_defaults_2d
        )
        ok_explosion_3d, msg_explosion_3d = save_mode_explosion_defaults(
            "3d", state.explosion_defaults_3d
        )
        ok_explosion_4d, msg_explosion_4d = save_mode_explosion_defaults(
            "4d", state.explosion_defaults_4d
        )
    if (
        ok_audio
        and ok_display
        and ok_analytics
        and ok_game_seed
        and ok_gameplay_shared
        and ok_explosion_2d
        and ok_explosion_3d
        and ok_explosion_4d
    ):
        state.original_audio = _clone_audio_settings(state.audio_settings)
        state.original_display = _clone_display_settings(state.display_settings)
        state.original_overlay_transparency = float(state.overlay_transparency)
        state.original_game_seed = int(state.game_seed)
        state.original_random_mode_index = int(state.random_mode_index)
        state.original_topology_advanced = int(state.topology_advanced)
        state.original_kick_level_index = int(state.kick_level_index)
        state.original_endgame_preset_id = str(state.endgame_preset_id)
        state.original_endgame_boundary_response = str(
            state.endgame_boundary_response
        )
        state.original_endgame_particle_collisions = str(
            state.endgame_particle_collisions
        )
        state.original_endgame_relic_speed_percent = int(
            state.endgame_relic_speed_percent
        )
        state.original_endgame_shatter_speed_percent = int(
            state.endgame_shatter_speed_percent
        )
        state.original_auto_speedup_enabled = int(state.auto_speedup_enabled)
        state.original_lines_per_level = int(state.lines_per_level)
        state.original_rotation_animation_mode = str(state.rotation_animation_mode)
        state.original_rotation_animation_duration_ms_2d = int(
            state.rotation_animation_duration_ms_2d
        )
        state.original_rotation_animation_duration_ms_nd = int(
            state.rotation_animation_duration_ms_nd
        )
        state.original_translation_animation_duration_ms = int(
            state.translation_animation_duration_ms
        )
        state.original_score_logging_enabled = bool(state.score_logging_enabled)
        state.original_explosion_defaults_2d = state.explosion_defaults_2d
        state.original_explosion_defaults_3d = state.explosion_defaults_3d
        state.original_explosion_defaults_4d = state.explosion_defaults_4d
        state.saved = True
        _set_unified_status(
            state, "Saved audio/display/gameplay/analytics + explosion defaults"
        )
        play_sfx("menu_confirm")
        return screen

    error = msg_audio
    if ok_audio:
        error = msg_display
    if ok_audio and ok_display:
        error = msg_analytics
    if ok_audio and ok_display and ok_analytics:
        error = msg_game_seed
    if ok_audio and ok_display and ok_analytics and ok_game_seed:
        error = msg_gameplay_shared
    if ok_audio and ok_display and ok_analytics and ok_game_seed and ok_gameplay_shared:
        error = msg_explosion_2d
    if (
        ok_audio
        and ok_display
        and ok_analytics
        and ok_game_seed
        and ok_gameplay_shared
        and ok_explosion_2d
    ):
        error = msg_explosion_3d
    if (
        ok_audio
        and ok_display
        and ok_analytics
        and ok_game_seed
        and ok_gameplay_shared
        and ok_explosion_2d
        and ok_explosion_3d
    ):
        error = msg_explosion_4d
    _set_unified_status(state, error, is_error=True)
    return screen


def _reset_unified_settings(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    state.audio_settings = _audio_defaults()
    state.display_settings = _display_defaults()
    display_defaults = default_display_settings()
    state.overlay_transparency = float(display_defaults["overlay_transparency"])
    state.game_seed = int(DEFAULT_GAME_SEED)
    state.random_mode_index = _RANDOM_MODE_DEFAULT
    state.topology_advanced = _TOPOLOGY_ADVANCED_DEFAULT
    state.kick_level_index = _KICK_LEVEL_DEFAULT
    state.endgame_preset_id = _ENDGAME_PRESET_DEFAULT
    state.endgame_boundary_response = _ENDGAME_BOUNDARY_RESPONSE_DEFAULT
    state.endgame_particle_collisions = _ENDGAME_PARTICLE_COLLISIONS_DEFAULT
    state.endgame_relic_speed_percent = _ENDGAME_RELIC_SPEED_DEFAULT
    state.endgame_shatter_speed_percent = _ENDGAME_SHATTER_SPEED_DEFAULT
    state.auto_speedup_enabled = _AUTO_SPEEDUP_DEFAULT
    state.lines_per_level = _LINES_PER_LEVEL_DEFAULT
    state.rotation_animation_mode = _ROTATION_ANIMATION_MODE_DEFAULT
    state.rotation_animation_duration_ms_2d = _ROTATION_ANIMATION_DURATION_2D_DEFAULT
    state.rotation_animation_duration_ms_nd = _ROTATION_ANIMATION_DURATION_ND_DEFAULT
    state.translation_animation_duration_ms = _TRANSLATION_ANIMATION_DURATION_DEFAULT
    state.score_logging_enabled = _analytics_defaults()
    state.explosion_defaults_2d = default_explosion_defaults()
    state.explosion_defaults_3d = default_explosion_defaults()
    state.explosion_defaults_4d = default_explosion_defaults()
    state.pending_reset_confirm = False
    _mark_unified_dirty(state)
    _flash_row(state, "reset")
    _sync_audio_preview(state.audio_settings)
    _sync_analytics_preview(state.score_logging_enabled)
    screen = apply_display_mode(
        state.display_settings,
        preferred_windowed_size=state.display_settings.windowed_size,
    )
    _set_unified_status(state, "Reset to defaults (not saved yet)")
    play_sfx("menu_move")
    return screen


def _adjust_unified_audio_row(
    state: _UnifiedSettingsState, row_key: str, delta_sign: int
) -> bool:
    if row_key == "audio_master":
        state.audio_settings.master_volume = max(
            0.0, min(1.0, state.audio_settings.master_volume + delta_sign * 0.05)
        )
        _sync_audio_preview(state.audio_settings)
        _flash_row(state, row_key)
        return True
    if row_key == "audio_sfx":
        state.audio_settings.sfx_volume = max(
            0.0, min(1.0, state.audio_settings.sfx_volume + delta_sign * 0.05)
        )
        _sync_audio_preview(state.audio_settings)
        _flash_row(state, row_key)
        return True
    if row_key == "audio_mute":
        state.audio_settings.mute = not state.audio_settings.mute
        _sync_audio_preview(state.audio_settings)
        _flash_row(state, row_key)
        return True
    return False


def _adjust_unified_display_row(
    state: _UnifiedSettingsState, row_key: str, delta_sign: int
) -> bool:
    if row_key == "display_fullscreen":
        state.display_settings = DisplaySettings(
            not state.display_settings.fullscreen,
            state.display_settings.windowed_size,
        )
        _flash_row(state, row_key)
        return True
    if row_key == "display_width":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (max(640, width + delta_sign * 40), height),
        )
        _flash_row(state, row_key)
        return True
    if row_key == "display_height":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (width, max(480, height + delta_sign * 40)),
        )
        _flash_row(state, row_key)
        return True
    if row_key == "display_overlay_transparency":
        display_defaults = default_display_settings()
        state.overlay_transparency = clamp_overlay_transparency(
            state.overlay_transparency + delta_sign * float(OVERLAY_TRANSPARENCY_STEP),
            default=float(display_defaults["overlay_transparency"]),
        )
        _flash_row(state, row_key)
        return True
    return False


def _adjust_unified_gameplay_row(
    state: _UnifiedSettingsState, row_key: str, delta_sign: int
) -> bool:
    if row_key == "game_seed":
        state.game_seed = int(
            clamp_game_seed(
                int(state.game_seed) + delta_sign * int(GAME_SEED_STEP),
                default=int(DEFAULT_GAME_SEED),
            )
        )
        _flash_row(state, row_key)
        return True
    if row_key == "game_random_mode":
        state.random_mode_index = (int(state.random_mode_index) + delta_sign) % len(
            _RANDOM_MODE_LABELS
        )
        _flash_row(state, row_key)
        return True
    if row_key == "game_topology_advanced":
        state.topology_advanced = 0 if int(state.topology_advanced) else 1
        _flash_row(state, row_key)
        return True
    if row_key == "endgame_preset_id":
        state.endgame_preset_id = _cycle_text_option(
            current=str(state.endgame_preset_id),
            values=ENDGAME_PRESET_IDS,
            delta_sign=delta_sign,
        )
        _flash_row(state, row_key)
        return True
    if row_key == "endgame_boundary_response":
        state.endgame_boundary_response = _cycle_text_option(
            current=str(state.endgame_boundary_response),
            values=ENDGAME_BOUNDARY_RESPONSES,
            delta_sign=delta_sign,
        )
        _flash_row(state, row_key)
        return True
    if row_key == "endgame_particle_collisions":
        state.endgame_particle_collisions = _cycle_text_option(
            current=str(state.endgame_particle_collisions),
            values=ENDGAME_PARTICLE_COLLISION_MODES,
            delta_sign=delta_sign,
        )
        _flash_row(state, row_key)
        return True
    if row_key == "endgame_relic_speed_percent":
        state.endgame_relic_speed_percent = int(
            clamp_endgame_speed_percent(
                int(state.endgame_relic_speed_percent)
                + (delta_sign * int(ENDGAME_SPEED_PERCENT_STEP)),
                default=_ENDGAME_RELIC_SPEED_DEFAULT,
            )
        )
        _flash_row(state, row_key)
        return True
    if row_key == "endgame_shatter_speed_percent":
        state.endgame_shatter_speed_percent = int(
            clamp_endgame_speed_percent(
                int(state.endgame_shatter_speed_percent)
                + (delta_sign * int(ENDGAME_SPEED_PERCENT_STEP)),
                default=_ENDGAME_SHATTER_SPEED_DEFAULT,
            )
        )
        _flash_row(state, row_key)
        return True
    return _adjust_advanced_gameplay_value(state, row_key, delta_sign)


def _adjust_unified_analytics_row(state: _UnifiedSettingsState, row_key: str) -> bool:
    if row_key != "analytics_score_logging":
        return False
    state.score_logging_enabled = not state.score_logging_enabled
    _sync_analytics_preview(state.score_logging_enabled)
    _flash_row(state, row_key)
    return True


def _set_explosion_defaults_for_mode(
    state: _UnifiedSettingsState,
    mode_key: str,
    defaults,
) -> None:
    if mode_key == "2d":
        state.explosion_defaults_2d = defaults
        return
    if mode_key == "3d":
        state.explosion_defaults_3d = defaults
        return
    state.explosion_defaults_4d = defaults


def _explode_piece_shape_options(
    *,
    dimension: int,
    piece_set_id: str,
    seed: int,
) -> tuple[str, ...]:
    dims = explorer_default_board_dims(int(dimension))
    rng = random.Random(int(seed))
    if int(dimension) == 2:
        shapes = get_piece_bag_2d(
            piece_set_id,
            rng=rng,
            board_dims=(int(dims[0]), int(dims[1])),
        )
        return tuple(str(shape.name) for shape in shapes)
    shapes = get_piece_shapes_nd(
        int(dimension),
        piece_set_id=piece_set_id,
        rng=rng,
        board_dims=dims,
    )
    return tuple(str(shape.name) for shape in shapes)


def _explosion_cycle_options_for_field(
    state: _UnifiedSettingsState,
    mode_key: str,
    *,
    field: str,
) -> tuple[str, ...]:
    dim = int(mode_key[0])

    def _topology_preset_ids() -> tuple[str, ...]:
        preset_ids = tuple(
            str(preset.preset_id)
            for section in explorer_preset_sections_for_dimension(dim)
            for preset in section.presets
        )
        return ("",) + preset_ids

    def _snapshot_sources() -> tuple[str, ...]:
        return (
            "single_piece",
            "single_cell",
            "piece_change",
            "inherited_current_state",
        )

    def _piece_set_ids() -> tuple[str, ...]:
        if dim == 2:
            return ("",) + tuple(piece_set_2d_options_gameplay())
        return ("",) + tuple(piece_set_options_for_dimension_gameplay(dim))

    def _piece_shape_names() -> tuple[str, ...]:
        defaults = _explosion_defaults_for_mode(state, mode_key)
        piece_sets = _piece_set_ids()[1:]
        default_piece_set = str(piece_sets[0]) if piece_sets else ""
        active_piece_set = str(defaults.piece_set_id) or default_piece_set
        shape_names = _explode_piece_shape_options(
            dimension=dim,
            piece_set_id=active_piece_set,
            seed=int(defaults.seed),
        )
        return ("",) + shape_names

    handlers = {
        "topology_preset_id": _topology_preset_ids,
        "snapshot_source_id": _snapshot_sources,
        "piece_set_id": _piece_set_ids,
        "piece_shape_name": _piece_shape_names,
        "view_mode": lambda: ("board_native", "projection_reference"),
        "boundary_response": lambda: tuple(EXPLOSION_BOUNDARY_RESPONSES),
        "particle_collisions": lambda: tuple(EXPLOSION_PARTICLE_COLLISION_MODES),
        "mass_mode": lambda: tuple(EXPLOSION_MASS_MODES),
        "diagnostics_mode": lambda: tuple(EXPLOSION_DIAGNOSTICS_MODES),
        "grid_mode": lambda: (
            "off",
            "bottom_boundary",
            "edge",
            "full",
            "helper",
            "all_boundaries",
        ),
        "shadow_mode": lambda: (
            "off",
            "bottom_boundary",
            "all_boundaries",
        ),
        "speed_preset": lambda: tuple(EXPLOSION_SPEED_PRESETS),
        "w_movement_animation_style": lambda: ("fade", "box_size"),
    }
    handler = handlers.get(field)
    if handler is None:
        return tuple()
    return tuple(handler())


def _adjust_unified_explosion_row(
    state: _UnifiedSettingsState,
    *,
    row_key: str,
    delta_sign: int,
) -> bool:
    parsed = _explosion_mode_and_field(row_key)
    if parsed is None:
        return False
    mode_key, field = parsed
    defaults = _explosion_defaults_for_mode(state, mode_key)
    if _adjust_explosion_selector_field(
        state,
        mode_key=mode_key,
        defaults=defaults,
        field=field,
        delta_sign=delta_sign,
        row_key=row_key,
    ):
        return True
    if _adjust_explosion_toggle_field(
        state,
        mode_key=mode_key,
        defaults=defaults,
        field=field,
        row_key=row_key,
    ):
        return True
    if _adjust_explosion_numeric_field(
        state,
        mode_key=mode_key,
        defaults=defaults,
        field=field,
        delta_sign=delta_sign,
        row_key=row_key,
    ):
        return True
    return _adjust_explosion_cell_origin_field(
        state,
        mode_key=mode_key,
        defaults=defaults,
        field=field,
        delta_sign=delta_sign,
        row_key=row_key,
    )


def _adjust_explosion_selector_field(
    state: _UnifiedSettingsState,
    *,
    mode_key: str,
    defaults,
    field: str,
    delta_sign: int,
    row_key: str,
) -> bool:
    selector_fields = {
        "topology_preset_id",
        "snapshot_source_id",
        "piece_set_id",
        "piece_shape_name",
        "view_mode",
        "boundary_response",
        "particle_collisions",
        "mass_mode",
        "diagnostics_mode",
        "grid_mode",
        "shadow_mode",
        "speed_preset",
        "w_movement_animation_style",
    }
    if field not in selector_fields:
        return False
    options = _explosion_cycle_options_for_field(state, mode_key, field=field)
    current = str(getattr(defaults, field))
    next_value = _cycle_text_option(
        current=current,
        values=options,
        delta_sign=delta_sign,
    )
    updated = replace(defaults, **{field: next_value})
    if field == "piece_set_id":
        updated = replace(updated, piece_shape_name="")
    updated = coerce_explosion_defaults(serialize_explosion_defaults(updated))
    _set_explosion_defaults_for_mode(state, mode_key, updated)
    _flash_row(state, row_key)
    return True


def _adjust_explosion_toggle_field(
    state: _UnifiedSettingsState,
    *,
    mode_key: str,
    defaults,
    field: str,
    row_key: str,
) -> bool:
    if field not in {"trace_enabled", "sound_enabled"}:
        return False
    updated = replace(defaults, **{field: not bool(getattr(defaults, field))})
    updated = coerce_explosion_defaults(serialize_explosion_defaults(updated))
    _set_explosion_defaults_for_mode(state, mode_key, updated)
    _flash_row(state, row_key)
    return True


def _adjust_explosion_numeric_field(
    state: _UnifiedSettingsState,
    *,
    mode_key: str,
    defaults,
    field: str,
    delta_sign: int,
    row_key: str,
) -> bool:
    numeric_step_by_field = {
        "base_mass": 0.05,
        "random_mass_min": 0.05,
        "random_mass_max": 0.05,
        "collision_elasticity": 0.05,
        "trace_retention_ms": 120.0,
        "endgame_live_cell_fraction": 0.01,
        "seed": 1,
    }
    if field not in numeric_step_by_field:
        return False
    step = float(numeric_step_by_field[field])
    current_value = float(getattr(defaults, field))
    next_value = current_value + (float(delta_sign) * step)
    next_value = _clamped_explosion_numeric_value(field, next_value)
    payload_value = next_value if field != "seed" else int(round(next_value))
    updated = replace(defaults, **{field: payload_value})
    updated = coerce_explosion_defaults(serialize_explosion_defaults(updated))
    _set_explosion_defaults_for_mode(state, mode_key, updated)
    _flash_row(state, row_key)
    return True


def _clamped_explosion_numeric_value(field: str, value: float) -> float:
    if field in {"base_mass", "random_mass_min", "random_mass_max"}:
        return float(clamp_mass_value(value))
    if field == "collision_elasticity":
        return float(clamp_collision_elasticity(value))
    if field == "trace_retention_ms":
        return float(clamp_trace_retention_ms(value))
    if field == "endgame_live_cell_fraction":
        return max(0.0, min(1.0, float(value)))
    if field == "seed":
        return float(max(0, min(9999, int(round(value)))))
    return float(value)


def _adjust_explosion_cell_origin_field(
    state: _UnifiedSettingsState,
    *,
    mode_key: str,
    defaults,
    field: str,
    delta_sign: int,
    row_key: str,
) -> bool:
    if not field.startswith("cell_origin_"):
        return False
    axis = field.split("_")[-1]
    axis_index = {"x": 0, "y": 1, "z": 2, "w": 3}.get(axis)
    if axis_index is None:
        return False
    origin = list(defaults.cell_origin)
    origin_value = int(origin[axis_index])
    next_value = origin_value + int(delta_sign)
    next_value = max(-1, min(9999, int(next_value)))
    origin[axis_index] = next_value
    updated = replace(defaults, cell_origin=tuple(int(value) for value in origin))
    updated = coerce_explosion_defaults(serialize_explosion_defaults(updated))
    _set_explosion_defaults_for_mode(state, mode_key, updated)
    _flash_row(state, row_key)
    return True


def _adjust_unified_with_arrows(
    state: _UnifiedSettingsState,
    key: int,
    *,
    row_key: str | None = None,
) -> bool:
    nav_key = normalize_menu_navigation_key(key)
    if nav_key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    delta_sign = -1 if nav_key == pygame.K_LEFT else 1
    row_key = str(row_key or _unified_row_key(state))
    handled = (
        _adjust_unified_audio_row(state, row_key, delta_sign)
        or _adjust_unified_display_row(state, row_key, delta_sign)
        or _adjust_unified_gameplay_row(state, row_key, delta_sign)
        or _adjust_unified_explosion_row(state, row_key=row_key, delta_sign=delta_sign)
        or _adjust_unified_analytics_row(state, row_key)
    )
    if not handled:
        return False
    _mark_unified_dirty(state)
    state.pending_reset_confirm = False
    play_sfx("menu_move")
    return True


def _adjust_advanced_gameplay_value(
    state: _UnifiedSettingsState,
    row_key: str,
    delta_sign: int,
    *,
    enter_pressed: bool = False,
) -> bool:
    if row_key == "kick_level_index":
        return _adjust_kick_level_index(
            state,
            delta_sign,
            enter_pressed=enter_pressed,
        )
    duration_defaults = {
        "rotation_animation_duration_ms_2d": _ROTATION_ANIMATION_DURATION_2D_DEFAULT,
        "rotation_animation_duration_ms_nd": _ROTATION_ANIMATION_DURATION_ND_DEFAULT,
        "translation_animation_duration_ms": _TRANSLATION_ANIMATION_DURATION_DEFAULT,
    }
    if row_key in duration_defaults:
        return _adjust_animation_duration_value(
            state,
            row_key,
            delta_sign,
            default_value=int(duration_defaults[row_key]),
        )
    handlers = {
        "auto_speedup_enabled": lambda: _toggle_advanced_auto_speedup(
            state,
            delta_sign=delta_sign,
            enter_pressed=enter_pressed,
        ),
        "lines_per_level": lambda: _adjust_advanced_lines_per_level(
            state,
            delta_sign=delta_sign,
        ),
        "rotation_animation_mode": lambda: _adjust_rotation_animation_mode_value(
            state,
            delta_sign=delta_sign,
            enter_pressed=enter_pressed,
        ),
    }
    handler = handlers.get(row_key)
    if handler is None:
        return False
    return bool(handler())


def _cycle_text_option(
    *,
    current: str,
    values: tuple[str, ...],
    delta_sign: int,
) -> str:
    if not values:
        return current
    try:
        index = values.index(str(current))
    except ValueError:
        index = 0
    return str(values[(index + delta_sign) % len(values)])


def _adjust_kick_level_index(
    state: _UnifiedSettingsState,
    delta_sign: int,
    *,
    enter_pressed: bool,
) -> bool:
    max_index = max(0, len(_KICK_LEVEL_LABELS) - 1)
    if max_index == 0:
        return False
    if delta_sign == 0:
        if not enter_pressed:
            return False
        next_index = int(state.kick_level_index) + 1
    else:
        next_index = int(state.kick_level_index) + int(delta_sign)
    state.kick_level_index = max(0, min(max_index, next_index))
    return True


def _toggle_advanced_auto_speedup(
    state: _UnifiedSettingsState,
    *,
    delta_sign: int,
    enter_pressed: bool,
) -> bool:
    if delta_sign == 0 and not enter_pressed:
        return False
    state.auto_speedup_enabled = 0 if int(state.auto_speedup_enabled) else 1
    return True


def _adjust_advanced_lines_per_level(
    state: _UnifiedSettingsState,
    *,
    delta_sign: int,
) -> bool:
    if delta_sign == 0:
        return False
    state.lines_per_level = clamp_lines_per_level(
        int(state.lines_per_level) + int(delta_sign),
        default=_LINES_PER_LEVEL_DEFAULT,
    )
    return True


def _adjust_rotation_animation_mode_value(
    state: _UnifiedSettingsState,
    *,
    delta_sign: int,
    enter_pressed: bool,
) -> bool:
    if delta_sign == 0 and not enter_pressed:
        return False
    current_mode = str(state.rotation_animation_mode)
    try:
        current_index = _ROTATION_ANIMATION_MODE_VALUES.index(current_mode)
    except ValueError:
        current_index = 0
    step = 1 if delta_sign == 0 else int(delta_sign)
    state.rotation_animation_mode = _ROTATION_ANIMATION_MODE_VALUES[
        (current_index + step) % len(_ROTATION_ANIMATION_MODE_VALUES)
    ]
    return True


def _adjust_animation_duration_value(
    state: _UnifiedSettingsState,
    attribute_name: str,
    delta_sign: int,
    *,
    default_value: int,
) -> bool:
    if delta_sign == 0:
        return False
    setattr(
        state,
        attribute_name,
        clamp_animation_duration_ms(
            int(getattr(state, attribute_name))
            + int(delta_sign) * int(ANIMATION_DURATION_MS_STEP),
            default=default_value,
        ),
    )
    return True


def _format_cache_bytes(total_bytes: int) -> str:
    size = max(0, int(total_bytes))
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024.0:.1f} KB"
    return f"{size / (1024.0 * 1024.0):.2f} MB"


def _measure_topology_cache(state: _UnifiedSettingsState) -> bool:
    file_count, total_bytes = topology_cache_usage()
    state.topology_cache_file_count = int(file_count)
    state.topology_cache_size_bytes = int(total_bytes)
    _set_unified_status(
        state,
        "Topology cache: "
        f"{int(file_count)} files, {_format_cache_bytes(int(total_bytes))}",
    )
    play_sfx("menu_confirm")
    return True


def _clear_topology_cache_action(state: _UnifiedSettingsState) -> bool:
    file_count, total_bytes = clear_topology_cache()
    movement_graph_module._build_movement_graph_rows.cache_clear()
    build_explorer_transport_resolver.cache_clear()
    state.topology_cache_file_count = 0
    state.topology_cache_size_bytes = 0
    _set_unified_status(
        state,
        "Cleared topology cache: "
        f"{int(file_count)} files, {_format_cache_bytes(int(total_bytes))}",
    )
    play_sfx("menu_confirm")
    return True
