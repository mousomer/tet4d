from __future__ import annotations

from dataclasses import dataclass

import pygame

from tet4d.engine.runtime.menu_config import (
    settings_hub_layout_rows,
    settings_option_labels,
    settings_top_level_categories,
    ui_copy_section,
)
from tet4d.engine.runtime.menu_settings_state import (
    DEFAULT_GAME_SEED,
    GAME_SEED_STEP,
    OVERLAY_TRANSPARENCY_STEP,
    clamp_game_seed,
    clamp_overlay_transparency,
    default_analytics_settings,
    default_audio_settings,
    default_display_settings,
    default_mode_shared_gameplay_settings,
    get_global_game_seed,
    get_overlay_transparency,
    mode_shared_gameplay_settings,
    save_analytics_settings,
    save_audio_settings,
    save_display_settings,
    save_global_game_seed,
    save_shared_gameplay_settings,
)
from tet4d.engine.runtime.score_analyzer import set_score_analyzer_logging_enabled
from tet4d.engine.runtime.settings_schema import clamp_lines_per_level, sanitize_text
from tet4d.ui.pygame.menu.numeric_text_input import (
    append_numeric_text,
    parse_numeric_text,
)
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings, play_sfx, set_audio_settings
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    apply_display_mode,
    normalize_display_settings,
)
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)
_SETTINGS_OPTION_LABELS = settings_option_labels()
_RANDOM_MODE_LABELS = tuple(_SETTINGS_OPTION_LABELS["game_random_mode"])
_KICK_LEVEL_LABELS = tuple(_SETTINGS_OPTION_LABELS["game_kick_level"])
_SETTINGS_HUB_COPY = ui_copy_section("settings_hub")
_DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS = (
    default_mode_shared_gameplay_settings("2d")
)
_RANDOM_MODE_DEFAULT = int(_DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["random_mode_index"])
_TOPOLOGY_ADVANCED_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["topology_advanced"]
)
_KICK_LEVEL_DEFAULT = int(_DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["kick_level_index"])
_AUTO_SPEEDUP_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["auto_speedup_enabled"]
)
_LINES_PER_LEVEL_DEFAULT = int(
    _DEFAULT_MODE_SHARED_GAMEPLAY_SETTINGS["lines_per_level"]
)
_NUMERIC_TEXT_EDIT_ROWS = {
    "display_width",
    "display_height",
    "game_seed",
}
_NUMERIC_TEXT_MAX_LENGTH = 16


def _sanitize_text(value: str, max_length: int) -> str:
    return sanitize_text(value, max_length=max_length)


@dataclass
class SettingsHubResult:
    screen: pygame.Surface
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    keep_running: bool


@dataclass
class _UnifiedSettingsState:
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    overlay_transparency: float
    game_seed: int
    random_mode_index: int
    topology_advanced: int
    kick_level_index: int
    auto_speedup_enabled: int
    lines_per_level: int
    score_logging_enabled: bool
    original_audio: AudioSettings
    original_display: DisplaySettings
    original_overlay_transparency: float
    original_game_seed: int
    original_random_mode_index: int
    original_topology_advanced: int
    original_kick_level_index: int
    original_auto_speedup_enabled: int
    original_lines_per_level: int
    original_score_logging_enabled: bool
    selected: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    text_mode_row_key: str = ""
    text_mode_buffer: str = ""
    text_mode_replace_on_type: bool = False
    saved: bool = False
    running: bool = True


_UNIFIED_SETTINGS_ROWS: tuple[tuple[str, str, str], ...] = (
    settings_hub_layout_rows()
)
_UNIFIED_SELECTABLE = tuple(
    idx for idx, row in enumerate(_UNIFIED_SETTINGS_ROWS) if row[0] == "item"
)


def _configured_top_level_labels() -> tuple[str, ...]:
    entries = settings_top_level_categories()
    return tuple(entry["label"] for entry in entries)


def _layout_top_level_labels() -> tuple[str, ...]:
    return tuple(
        label
        for row_kind, label, _row_key in _UNIFIED_SETTINGS_ROWS
        if row_kind == "header"
    )


def _validate_unified_layout_against_policy() -> tuple[bool, str]:
    expected = _configured_top_level_labels()
    actual = _layout_top_level_labels()
    if expected == actual:
        return True, "Settings layout policy verified"
    return False, (
        "Settings layout mismatch: expected top-level categories "
        f"{', '.join(expected)} but UI renders {', '.join(actual)}"
    )


def _draw_gradient(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, BG_TOP, BG_BOTTOM)


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
        fullscreen=settings.fullscreen, windowed_size=settings.windowed_size
    )


def _sync_audio_preview(settings: AudioSettings) -> None:
    set_audio_settings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


def _sync_analytics_preview(score_logging_enabled: bool) -> None:
    set_score_analyzer_logging_enabled(bool(score_logging_enabled))


def _unified_row_key(state: _UnifiedSettingsState) -> str:
    row_idx = _UNIFIED_SELECTABLE[state.selected]
    return _UNIFIED_SETTINGS_ROWS[row_idx][2]


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
    return None


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
        _height = int(state.display_settings.windowed_size[1])
        state.display_settings = DisplaySettings(state.display_settings.fullscreen, (width, _height))
    elif row_key == "display_height":
        _width = int(state.display_settings.windowed_size[0])
        height = max(480, parsed)
        state.display_settings = DisplaySettings(state.display_settings.fullscreen, (_width, height))
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
    ok_game_seed, msg_game_seed = save_global_game_seed(
        int(state.game_seed)
    )
    ok_gameplay_shared, msg_gameplay_shared = save_shared_gameplay_settings(
        int(state.random_mode_index),
        int(state.topology_advanced),
        int(state.kick_level_index),
        int(state.auto_speedup_enabled),
        int(state.lines_per_level),
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
            not state.display_settings.fullscreen, state.display_settings.windowed_size
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
                int(state.game_seed)
                + delta_sign * int(GAME_SEED_STEP),
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
    return False


def _adjust_unified_analytics_row(state: _UnifiedSettingsState, row_key: str) -> bool:
    if row_key != "analytics_score_logging":
        return False
    state.score_logging_enabled = not state.score_logging_enabled
    _sync_analytics_preview(state.score_logging_enabled)
    return True


def _adjust_unified_with_arrows(state: _UnifiedSettingsState, key: int) -> bool:
    nav_key = normalize_menu_navigation_key(key)
    if nav_key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    delta_sign = -1 if nav_key == pygame.K_LEFT else 1
    row_key = _unified_row_key(state)
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
    if row_key == "auto_speedup_enabled":
        if delta_sign == 0 and not enter_pressed:
            return False
        state.auto_speedup_enabled = 0 if int(state.auto_speedup_enabled) else 1
        return True
    if row_key == "lines_per_level":
        if delta_sign == 0:
            return False
        state.lines_per_level = clamp_lines_per_level(
            int(state.lines_per_level) + int(delta_sign),
            default=_LINES_PER_LEVEL_DEFAULT,
        )
        return True
    return False


def _mark_advanced_gameplay_updated(state: _UnifiedSettingsState) -> None:
    _mark_unified_dirty(state)
    _set_unified_status(state, "Advanced gameplay updated (not saved yet)")
    play_sfx("menu_move")


def _apply_advanced_gameplay_adjustment(
    state: _UnifiedSettingsState,
    *,
    row_key: str,
    delta_sign: int,
    enter_pressed: bool = False,
) -> None:
    if not _adjust_advanced_gameplay_value(
        state,
        row_key,
        delta_sign,
        enter_pressed=enter_pressed,
    ):
        return
    _mark_advanced_gameplay_updated(state)


def _handle_advanced_gameplay_event(
    *,
    event: pygame.event.Event,
    state: _UnifiedSettingsState,
    selected: int,
    row_keys: tuple[str, ...],
) -> tuple[int, bool]:
    if event.type == pygame.QUIT:
        state.running = False
        return selected, False
    if event.type != pygame.KEYDOWN:
        return selected, True
    if event.key == pygame.K_q:
        state.running = False
        return selected, False
    nav_key = normalize_menu_navigation_key(int(event.key))
    if nav_key == pygame.K_ESCAPE:
        return selected, False
    if nav_key == pygame.K_UP:
        play_sfx("menu_move")
        return (selected - 1) % len(row_keys), True
    if nav_key == pygame.K_DOWN:
        play_sfx("menu_move")
        return (selected + 1) % len(row_keys), True
    if nav_key in (pygame.K_LEFT, pygame.K_RIGHT):
        delta_sign = -1 if nav_key == pygame.K_LEFT else 1
        _apply_advanced_gameplay_adjustment(
            state,
            row_key=row_keys[selected],
            delta_sign=delta_sign,
        )
        return selected, True
    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _apply_advanced_gameplay_adjustment(
            state,
            row_key=row_keys[selected],
            delta_sign=0,
            enter_pressed=True,
        )
    return selected, True


def _unified_value_text(state: _UnifiedSettingsState, row_key: str) -> str:
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
    if row_key == "game_topology_advanced":
        return "ON" if int(state.topology_advanced) else "OFF"
    if row_key == "gameplay_advanced":
        kick_index = max(0, min(len(_KICK_LEVEL_LABELS) - 1, int(state.kick_level_index)))
        mode_text = "ON" if int(state.auto_speedup_enabled) else "OFF"
        return f"{_KICK_LEVEL_LABELS[kick_index]} / {mode_text} / {int(state.lines_per_level)}"
    return ""




def build_unified_settings_state(
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
) -> _UnifiedSettingsState:
    score_logging_enabled = bool(default_analytics_settings()["score_logging_enabled"])
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
    auto_speedup_enabled = int(mode_gameplay["auto_speedup_enabled"])
    lines_per_level = int(mode_gameplay["lines_per_level"])
    return _UnifiedSettingsState(
        audio_settings=_clone_audio_settings(audio_settings),
        display_settings=_clone_display_settings(display_settings),
        overlay_transparency=overlay_transparency,
        game_seed=game_seed,
        random_mode_index=random_mode_index,
        topology_advanced=topology_advanced,
        kick_level_index=kick_level_index,
        auto_speedup_enabled=auto_speedup_enabled,
        lines_per_level=lines_per_level,
        score_logging_enabled=score_logging_enabled,
        original_audio=_clone_audio_settings(audio_settings),
        original_display=_clone_display_settings(display_settings),
        original_overlay_transparency=overlay_transparency,
        original_game_seed=game_seed,
        original_random_mode_index=random_mode_index,
        original_topology_advanced=topology_advanced,
        original_kick_level_index=kick_level_index,
        original_auto_speedup_enabled=auto_speedup_enabled,
        original_lines_per_level=lines_per_level,
        original_score_logging_enabled=score_logging_enabled,
    )
