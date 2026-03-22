from __future__ import annotations

from dataclasses import dataclass

import pygame

from tet4d.engine.gameplay.rotation_anim import (
    ROTATION_ANIMATION_MODE_CELLWISE_SLIDING,
    ROTATION_ANIMATION_MODE_RIGID_PIECE_ROTATION,
)
from tet4d.engine.runtime.menu_config import (
    settings_hub_layout_rows,
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
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings

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
_NUMERIC_TEXT_EDIT_ROWS = {
    "display_width",
    "display_height",
    "game_seed",
}
_NUMERIC_TEXT_MAX_LENGTH = 16


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
    rotation_animation_mode: str
    rotation_animation_duration_ms_2d: int
    rotation_animation_duration_ms_nd: int
    translation_animation_duration_ms: int
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
    original_rotation_animation_mode: str
    original_rotation_animation_duration_ms_2d: int
    original_rotation_animation_duration_ms_nd: int
    original_translation_animation_duration_ms: int
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


_UNIFIED_SETTINGS_ROWS: tuple[tuple[str, str, str], ...] = settings_hub_layout_rows()
_UNIFIED_SELECTABLE = tuple(
    idx for idx, row in enumerate(_UNIFIED_SETTINGS_ROWS) if row[0] == "item"
)
_SELECTABLE_INDEX_BY_ROW_KEY = {
    row_key: selectable_idx
    for selectable_idx, row_idx in enumerate(_UNIFIED_SELECTABLE)
    for _kind, _label, row_key in (_UNIFIED_SETTINGS_ROWS[row_idx],)
}


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


def _unified_value_text(state: _UnifiedSettingsState, row_key: str) -> str:
    def _duration_text(value: int) -> str:
        return "Off" if int(value) <= 0 else f"{int(value)} ms"

    if _is_unified_text_mode(state) and row_key == state.text_mode_row_key:
        return f"{state.text_mode_buffer}_"
    if row_key == "gameplay_advanced":
        kick_index = max(0, min(len(_KICK_LEVEL_LABELS) - 1, int(state.kick_level_index)))
        mode_text = "ON" if int(state.auto_speedup_enabled) else "OFF"
        rotation_mode_label = rotation_animation_mode_label(state.rotation_animation_mode)
        return (
            f"{rotation_mode_label} / {_KICK_LEVEL_LABELS[kick_index]} / {mode_text}"
            f" / {int(state.lines_per_level)}"
            f" / rot2d {_duration_text(int(state.rotation_animation_duration_ms_2d))}"
            f" / rotnd {_duration_text(int(state.rotation_animation_duration_ms_nd))}"
            f" / move {_duration_text(int(state.translation_animation_duration_ms))}"
        )
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
    return ""


def rotation_animation_mode_label(value: str) -> str:
    return _ROTATION_ANIMATION_MODE_LABEL_BY_VALUE.get(str(value), str(value))


def build_unified_settings_state(
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
    initial_row_key: str | None = None,
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
    state = _UnifiedSettingsState(
        audio_settings=_clone_audio_settings(audio_settings),
        display_settings=_clone_display_settings(display_settings),
        overlay_transparency=overlay_transparency,
        game_seed=game_seed,
        random_mode_index=random_mode_index,
        topology_advanced=topology_advanced,
        kick_level_index=kick_level_index,
        auto_speedup_enabled=auto_speedup_enabled,
        lines_per_level=lines_per_level,
        rotation_animation_mode=rotation_animation_mode,
        rotation_animation_duration_ms_2d=rotation_animation_duration_ms_2d,
        rotation_animation_duration_ms_nd=rotation_animation_duration_ms_nd,
        translation_animation_duration_ms=translation_animation_duration_ms,
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
        original_rotation_animation_mode=rotation_animation_mode,
        original_rotation_animation_duration_ms_2d=rotation_animation_duration_ms_2d,
        original_rotation_animation_duration_ms_nd=rotation_animation_duration_ms_nd,
        original_translation_animation_duration_ms=translation_animation_duration_ms,
        original_score_logging_enabled=score_logging_enabled,
    )
    if initial_row_key:
        selected = _SELECTABLE_INDEX_BY_ROW_KEY.get(str(initial_row_key).strip().lower())
        if selected is not None:
            state.selected = selected
    return state
