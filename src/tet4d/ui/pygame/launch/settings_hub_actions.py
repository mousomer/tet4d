from __future__ import annotations

import pygame

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
from tet4d.engine.runtime.settings_schema import clamp_lines_per_level, sanitize_text
from tet4d.engine.topology_explorer import movement_graph as movement_graph_module
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

from .settings_hub_model import (
    _AUTO_SPEEDUP_DEFAULT,
    _KICK_LEVEL_DEFAULT,
    _KICK_LEVEL_LABELS,
    _LINES_PER_LEVEL_DEFAULT,
    _NUMERIC_TEXT_MAX_LENGTH,
    _RANDOM_MODE_DEFAULT,
    _RANDOM_MODE_LABELS,
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
    _mark_unified_dirty,
    _set_unified_status,
    _text_mode_numeric_value,
    _unified_row_key,
)


def _sanitize_text(value: str, max_length: int) -> str:
    return sanitize_text(value, max_length=max_length)


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
    else:
        return False

    _mark_unified_dirty(state)
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
        auto_speedup_enabled=int(state.auto_speedup_enabled),
        lines_per_level=int(state.lines_per_level),
        rotation_animation_mode=str(state.rotation_animation_mode),
        rotation_animation_duration_ms_2d=int(state.rotation_animation_duration_ms_2d),
        rotation_animation_duration_ms_nd=int(state.rotation_animation_duration_ms_nd),
        translation_animation_duration_ms=int(state.translation_animation_duration_ms),
    )
    if ok_audio and ok_display and ok_analytics and ok_game_seed and ok_gameplay_shared:
        state.original_audio = _clone_audio_settings(state.audio_settings)
        state.original_display = _clone_display_settings(state.display_settings)
        state.original_overlay_transparency = float(state.overlay_transparency)
        state.original_game_seed = int(state.game_seed)
        state.original_random_mode_index = int(state.random_mode_index)
        state.original_topology_advanced = int(state.topology_advanced)
        state.original_kick_level_index = int(state.kick_level_index)
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
        state.saved = True
        _set_unified_status(state, "Saved audio/display/gameplay/analytics settings")
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
    state.auto_speedup_enabled = _AUTO_SPEEDUP_DEFAULT
    state.lines_per_level = _LINES_PER_LEVEL_DEFAULT
    state.rotation_animation_mode = _ROTATION_ANIMATION_MODE_DEFAULT
    state.rotation_animation_duration_ms_2d = _ROTATION_ANIMATION_DURATION_2D_DEFAULT
    state.rotation_animation_duration_ms_nd = _ROTATION_ANIMATION_DURATION_ND_DEFAULT
    state.translation_animation_duration_ms = _TRANSLATION_ANIMATION_DURATION_DEFAULT
    state.score_logging_enabled = _analytics_defaults()
    state.pending_reset_confirm = False
    _mark_unified_dirty(state)
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
        return True
    if row_key == "audio_sfx":
        state.audio_settings.sfx_volume = max(
            0.0, min(1.0, state.audio_settings.sfx_volume + delta_sign * 0.05)
        )
        _sync_audio_preview(state.audio_settings)
        return True
    if row_key == "audio_mute":
        state.audio_settings.mute = not state.audio_settings.mute
        _sync_audio_preview(state.audio_settings)
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
        return True
    if row_key == "display_width":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (max(640, width + delta_sign * 40), height),
        )
        return True
    if row_key == "display_height":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (width, max(480, height + delta_sign * 40)),
        )
        return True
    if row_key == "display_overlay_transparency":
        display_defaults = default_display_settings()
        state.overlay_transparency = clamp_overlay_transparency(
            state.overlay_transparency
            + delta_sign * float(OVERLAY_TRANSPARENCY_STEP),
            default=float(display_defaults["overlay_transparency"]),
        )
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
        return True
    if row_key == "game_random_mode":
        state.random_mode_index = (int(state.random_mode_index) + delta_sign) % len(
            _RANDOM_MODE_LABELS
        )
        return True
    if row_key == "game_topology_advanced":
        state.topology_advanced = 0 if int(state.topology_advanced) else 1
        return True
    return _adjust_advanced_gameplay_value(state, row_key, delta_sign)


def _adjust_unified_analytics_row(state: _UnifiedSettingsState, row_key: str) -> bool:
    if row_key != "analytics_score_logging":
        return False
    state.score_logging_enabled = not state.score_logging_enabled
    _sync_analytics_preview(state.score_logging_enabled)
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

