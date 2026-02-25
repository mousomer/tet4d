from __future__ import annotations

from dataclasses import dataclass

import pygame

from .app_runtime import capture_windowed_display_settings
from .audio import AudioSettings, play_sfx, set_audio_settings
from .display import DisplaySettings, apply_display_mode, normalize_display_settings
from .menu_config import (
    default_settings_payload,
    settings_hub_layout_rows,
    settings_top_level_categories,
)
from .menu_persistence import (
    load_analytics_payload,
    persist_analytics_payload,
    persist_audio_payload,
    persist_display_payload,
)
from .menu_settings_state import DEFAULT_WINDOWED_SIZE
from .score_analyzer import set_score_analyzer_logging_enabled
from .ui_utils import draw_vertical_gradient, fit_text


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)


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
    score_logging_enabled: bool
    original_audio: AudioSettings
    original_display: DisplaySettings
    original_score_logging_enabled: bool
    selected: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    saved: bool = False
    running: bool = True


_UNIFIED_SETTINGS_ROWS: tuple[tuple[str, str, str], ...] = settings_hub_layout_rows()
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
    defaults = default_settings_payload().get("audio", {})
    master = 0.8
    sfx = 0.7
    mute = False
    if isinstance(defaults, dict):
        raw_master = defaults.get("master_volume")
        raw_sfx = defaults.get("sfx_volume")
        if isinstance(raw_master, (int, float)) and not isinstance(raw_master, bool):
            master = float(raw_master)
        if isinstance(raw_sfx, (int, float)) and not isinstance(raw_sfx, bool):
            sfx = float(raw_sfx)
        mute = bool(defaults.get("mute", False))
    return AudioSettings(master_volume=master, sfx_volume=sfx, mute=mute)


def _display_defaults() -> DisplaySettings:
    defaults = default_settings_payload().get("display", {})
    fullscreen = False
    windowed_size = DEFAULT_WINDOWED_SIZE
    if isinstance(defaults, dict):
        fullscreen = bool(defaults.get("fullscreen", False))
        raw_size = defaults.get("windowed_size")
        if (
            isinstance(raw_size, list)
            and len(raw_size) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in raw_size)
        ):
            windowed_size = (raw_size[0], raw_size[1])
    return DisplaySettings(fullscreen=fullscreen, windowed_size=windowed_size)


def _analytics_defaults() -> bool:
    defaults = default_settings_payload().get("analytics", {})
    if isinstance(defaults, dict):
        return bool(defaults.get("score_logging_enabled", False))
    return False


def _load_score_logging_setting() -> bool:
    payload = load_analytics_payload()
    if isinstance(payload, dict):
        return bool(payload.get("score_logging_enabled", _analytics_defaults()))
    return _analytics_defaults()


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


def _save_unified_settings(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    state.display_settings = normalize_display_settings(state.display_settings)
    screen = apply_display_mode(
        state.display_settings,
        preferred_windowed_size=state.display_settings.windowed_size,
    )
    ok_audio, msg_audio = persist_audio_payload(
        master_volume=state.audio_settings.master_volume,
        sfx_volume=state.audio_settings.sfx_volume,
        mute=state.audio_settings.mute,
    )
    ok_display, msg_display = persist_display_payload(
        fullscreen=state.display_settings.fullscreen,
        windowed_size=state.display_settings.windowed_size,
    )
    ok_analytics, msg_analytics = persist_analytics_payload(
        score_logging_enabled=state.score_logging_enabled,
    )
    if ok_audio and ok_display and ok_analytics:
        state.original_audio = _clone_audio_settings(state.audio_settings)
        state.original_display = _clone_display_settings(state.display_settings)
        state.original_score_logging_enabled = bool(state.score_logging_enabled)
        state.saved = True
        _set_unified_status(state, "Saved audio/display/analytics settings")
        play_sfx("menu_confirm")
        return screen

    error = (
        msg_audio if not ok_audio else msg_display if not ok_display else msg_analytics
    )
    _set_unified_status(state, error, is_error=True)
    return screen


def _reset_unified_settings(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    state.audio_settings = _audio_defaults()
    state.display_settings = _display_defaults()
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


def _adjust_unified_with_arrows(state: _UnifiedSettingsState, key: int) -> bool:
    if key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    delta_sign = -1 if key == pygame.K_LEFT else 1
    row_key = _unified_row_key(state)
    if row_key == "audio_master":
        state.audio_settings.master_volume = max(
            0.0, min(1.0, state.audio_settings.master_volume + delta_sign * 0.05)
        )
        _sync_audio_preview(state.audio_settings)
    elif row_key == "audio_sfx":
        state.audio_settings.sfx_volume = max(
            0.0, min(1.0, state.audio_settings.sfx_volume + delta_sign * 0.05)
        )
        _sync_audio_preview(state.audio_settings)
    elif row_key == "audio_mute":
        state.audio_settings.mute = not state.audio_settings.mute
        _sync_audio_preview(state.audio_settings)
    elif row_key == "display_fullscreen":
        state.display_settings = DisplaySettings(
            not state.display_settings.fullscreen, state.display_settings.windowed_size
        )
    elif row_key == "display_width":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (max(640, width + delta_sign * 40), height),
        )
    elif row_key == "display_height":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (width, max(480, height + delta_sign * 40)),
        )
    elif row_key == "analytics_score_logging":
        state.score_logging_enabled = not state.score_logging_enabled
        _sync_analytics_preview(state.score_logging_enabled)
    else:
        return False
    _mark_unified_dirty(state)
    state.pending_reset_confirm = False
    play_sfx("menu_move")
    return True


def _handle_unified_enter(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    row_key = _unified_row_key(state)
    if row_key in {"audio_mute", "display_fullscreen", "analytics_score_logging"}:
        state.pending_reset_confirm = False
        _adjust_unified_with_arrows(state, pygame.K_RIGHT)
        return screen
    if row_key == "display_apply":
        state.display_settings = normalize_display_settings(state.display_settings)
        screen = apply_display_mode(
            state.display_settings,
            preferred_windowed_size=state.display_settings.windowed_size,
        )
        _mark_unified_dirty(state)
        state.pending_reset_confirm = False
        _set_unified_status(state, "Applied display mode")
        play_sfx("menu_confirm")
        return screen
    if row_key == "save":
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if row_key == "reset":
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_unified_status(state, "Press Enter on Reset defaults again to confirm")
            return screen
        return _reset_unified_settings(screen, state)
    if row_key == "back":
        state.pending_reset_confirm = False
        state.running = False
    return screen


def _unified_value_text(state: _UnifiedSettingsState, row_key: str) -> str:
    if row_key == "audio_master":
        return f"{int(state.audio_settings.master_volume * 100)}%"
    if row_key == "audio_sfx":
        return f"{int(state.audio_settings.sfx_volume * 100)}%"
    if row_key == "audio_mute":
        return "ON" if state.audio_settings.mute else "OFF"
    if row_key == "display_fullscreen":
        return "ON" if state.display_settings.fullscreen else "OFF"
    if row_key == "display_width":
        return str(state.display_settings.windowed_size[0])
    if row_key == "display_height":
        return str(state.display_settings.windowed_size[1])
    if row_key == "analytics_score_logging":
        return "ON" if state.score_logging_enabled else "OFF"
    return ""


def _draw_unified_settings_menu(
    screen: pygame.Surface, fonts, state: _UnifiedSettingsState
) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Settings", True, TEXT_COLOR)
    categories = ", ".join(_configured_top_level_labels())
    subtitle_text = fit_text(
        fonts.hint_font,
        f"Top-level categories: {categories}",
        width - 28,
    )
    subtitle = fonts.hint_font.render(
        subtitle_text,
        True,
        MUTED_COLOR,
    )
    title_y = 44
    subtitle_y = title_y + title.get_height() + 8
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, subtitle_y))

    panel_w = min(700, max(360, width - 40))
    line_h = fonts.hint_font.get_height() + 3
    panel_top = subtitle_y + subtitle.get_height() + 10
    bottom_lines = 2 + (1 if state.status else 0)
    panel_max_h = max(180, height - panel_top - (bottom_lines * line_h) - 10)
    header_count = sum(
        1 for kind, _label, _row_key in _UNIFIED_SETTINGS_ROWS if kind == "header"
    )
    item_count = sum(
        1 for kind, _label, _row_key in _UNIFIED_SETTINGS_ROWS if kind == "item"
    )
    header_step_default = fonts.hint_font.get_height() + 10
    item_step_default = 46
    required_default = (
        18 + (header_count * header_step_default) + (item_count * item_step_default)
    )
    scale = min(1.0, panel_max_h / max(1, required_default))
    header_step = max(
        fonts.hint_font.get_height() + 4, int(header_step_default * scale)
    )
    item_step = max(fonts.menu_font.get_height() + 8, int(item_step_default * scale))
    panel_h = min(
        panel_max_h, 18 + (header_count * header_step) + (item_count * item_step) + 8
    )
    panel_x = (width - panel_w) // 2
    panel_y = max(
        panel_top,
        min((height - panel_h) // 2, height - panel_h - (bottom_lines * line_h) - 8),
    )
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    selected_row_idx = _UNIFIED_SELECTABLE[state.selected]
    y = panel_y + 14
    panel_bottom = panel_y + panel_h - 8
    label_left = panel_x + 22
    label_right = panel_x + panel_w - 22
    for idx, (row_kind, label, row_key) in enumerate(_UNIFIED_SETTINGS_ROWS):
        if y > panel_bottom:
            break
        if row_kind == "header":
            header_text = fit_text(fonts.hint_font, label, panel_w - 44)
            header = fonts.hint_font.render(header_text, True, (182, 206, 255))
            screen.blit(header, (panel_x + 22, y + 3))
            y += header_step
            continue

        if y + fonts.menu_font.get_height() > panel_bottom:
            break
        selected = idx == selected_row_idx
        color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        if selected:
            hi = pygame.Surface(
                (panel_w - 28, fonts.menu_font.get_height() + 10), pygame.SRCALPHA
            )
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 4))
        value = _unified_value_text(state, row_key)
        value_width = int(panel_w * 0.34) if value else 0
        value_draw = fit_text(fonts.menu_font, value, value_width)
        value_surf = (
            fonts.menu_font.render(value_draw, True, color) if value_draw else None
        )
        value_x = label_right - (
            value_surf.get_width() if value_surf is not None else 0
        )
        label_width = max(
            80, value_x - label_left - 10 if value_surf is not None else panel_w - 44
        )
        label_draw = fit_text(fonts.menu_font, label, label_width)
        label_surf = fonts.menu_font.render(label_draw, True, color)
        screen.blit(label_surf, (label_left, y))
        if value_surf is not None:
            screen.blit(value_surf, (value_x, y))
        y += item_step

    hints = (
        "Up/Down select   Left/Right adjust   Enter activate",
        "F5 save   F8 reset defaults   Esc back",
    )
    hy = panel_y + panel_h + 8
    max_hint_lines = max(0, (height - hy - 6) // max(1, line_h))
    hint_budget = max(0, max_hint_lines - (1 if state.status else 0))
    for line in hints[:hint_budget]:
        line_text = fit_text(fonts.hint_font, line, width - 28)
        surf = fonts.hint_font.render(line_text, True, MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3

    if state.status and hy + line_h <= height - 6:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 28)
        surf = fonts.hint_font.render(status_text, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


def _dispatch_unified_key(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
    key: int,
) -> pygame.Surface:
    if key == pygame.K_ESCAPE:
        state.running = False
        return screen
    if key == pygame.K_UP:
        state.pending_reset_confirm = False
        state.selected = (state.selected - 1) % len(_UNIFIED_SELECTABLE)
        play_sfx("menu_move")
        return screen
    if key == pygame.K_DOWN:
        state.pending_reset_confirm = False
        state.selected = (state.selected + 1) % len(_UNIFIED_SELECTABLE)
        play_sfx("menu_move")
        return screen
    if key == pygame.K_F5:
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if key == pygame.K_F8:
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_unified_status(state, "Press F8 again to confirm reset defaults")
            return screen
        return _reset_unified_settings(screen, state)
    if _adjust_unified_with_arrows(state, key):
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return _handle_unified_enter(screen, state)
    return screen


def _process_unified_events(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
) -> tuple[pygame.Surface, bool]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.running = False
            return screen, False
        if event.type != pygame.KEYDOWN:
            continue
        screen = _dispatch_unified_key(screen, state, event.key)
        if not state.running:
            break
    return screen, True


def run_settings_hub_menu(
    screen: pygame.Surface,
    fonts,
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
) -> SettingsHubResult:
    score_logging_enabled = _load_score_logging_setting()
    state = _UnifiedSettingsState(
        audio_settings=_clone_audio_settings(audio_settings),
        display_settings=_clone_display_settings(display_settings),
        score_logging_enabled=score_logging_enabled,
        original_audio=_clone_audio_settings(audio_settings),
        original_display=_clone_display_settings(display_settings),
        original_score_logging_enabled=score_logging_enabled,
    )
    ok_layout, msg_layout = _validate_unified_layout_against_policy()
    if not ok_layout:
        _set_unified_status(state, msg_layout, is_error=True)
    _sync_audio_preview(state.audio_settings)
    _sync_analytics_preview(state.score_logging_enabled)

    clock = pygame.time.Clock()
    keep_running = True
    while state.running:
        _dt = clock.tick(60)
        screen, keep_running = _process_unified_events(screen, state)
        if not keep_running or not state.running:
            break
        _draw_unified_settings_menu(screen, fonts, state)
        pygame.display.flip()

    if not state.saved:
        _sync_audio_preview(state.original_audio)
        _sync_analytics_preview(state.original_score_logging_enabled)
        restored_display = normalize_display_settings(state.original_display)
        screen = apply_display_mode(
            restored_display, preferred_windowed_size=restored_display.windowed_size
        )
        return SettingsHubResult(
            screen=screen,
            audio_settings=state.original_audio,
            display_settings=restored_display,
            keep_running=keep_running,
        )

    final_display = capture_windowed_display_settings(
        normalize_display_settings(state.display_settings)
    )
    return SettingsHubResult(
        screen=screen,
        audio_settings=state.audio_settings,
        display_settings=final_display,
        keep_running=keep_running,
    )
