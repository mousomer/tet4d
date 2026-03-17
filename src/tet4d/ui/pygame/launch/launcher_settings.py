from __future__ import annotations

import pygame

from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    apply_display_mode,
    capture_windowed_display_settings,
    normalize_display_settings,
)
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings, play_sfx
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text

from .settings_hub_actions import (
    _adjust_unified_with_arrows,
    _apply_unified_numeric_text_value,
    _handle_advanced_gameplay_event,
    _handle_unified_text_input,
    _is_unified_text_mode,
    _mark_unified_dirty,
    _reset_unified_settings,
    _save_unified_settings,
    _set_unified_status,
    _start_unified_numeric_text_mode,
    _stop_unified_text_mode,
    _sync_analytics_preview,
    _sync_audio_preview,
)
from .settings_hub_model import (
    BG_BOTTOM,
    BG_TOP,
    HIGHLIGHT_COLOR,
    MUTED_COLOR,
    TEXT_COLOR,
    SettingsHubResult,
    _KICK_LEVEL_LABELS,
    _NUMERIC_TEXT_EDIT_ROWS,
    _SETTINGS_HUB_COPY,
    _UNIFIED_SELECTABLE,
    _UNIFIED_SETTINGS_ROWS,
    _UnifiedSettingsState,
    _configured_top_level_labels,
    _unified_row_key,
    _unified_value_text,
    _validate_unified_layout_against_policy,
    build_unified_settings_state,
)


def _draw_gradient(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, BG_TOP, BG_BOTTOM)


def _format_animation_duration(value: int) -> str:
    return "Off" if int(value) <= 0 else f"{int(value)} ms"


def _handle_unified_enter(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
) -> pygame.Surface:
    row_key = _unified_row_key(state)
    if row_key in _NUMERIC_TEXT_EDIT_ROWS:
        _start_unified_numeric_text_mode(state, row_key)
        return screen
    if row_key in {
        "audio_mute",
        "display_fullscreen",
        "analytics_score_logging",
        "game_random_mode",
    }:
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
    if row_key == "gameplay_advanced":
        state.pending_reset_confirm = False
        return run_advanced_gameplay_menu(screen, fonts, state)
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



def _draw_advanced_gameplay_menu(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
    *,
    selected: int,
) -> None:
    _draw_gradient(screen)
    width, _height = screen.get_size()
    title_text = "Advanced gameplay"
    subtitle_text = (
        "Up/Down select   Left/Right adjust   Enter toggle/cycle   Esc back   Q quit"
    )
    title = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle = fonts.hint_font.render(subtitle_text, True, MUTED_COLOR)
    screen.blit(title, ((width - title.get_width()) // 2, 60))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 108))

    rows = (
        ("kick_level_index", "Kick permissiveness"),
        ("rotation_animation_duration_ms_2d", "2D rotation animation"),
        ("rotation_animation_duration_ms_nd", "ND rotation animation"),
        ("translation_animation_duration_ms", "Translation animation"),
        ("auto_speedup_enabled", "Auto speed-up by clears"),
        ("lines_per_level", "Lines per level"),
    )
    panel_w = min(760, max(420, width - 40))
    panel_h = 436
    panel_x = (width - panel_w) // 2
    panel_y = 170
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 152), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    line_y = panel_y + 28
    for idx, (row_key, label) in enumerate(rows):
        is_selected = idx == selected
        color = HIGHLIGHT_COLOR if is_selected else TEXT_COLOR
        if is_selected:
            hi = pygame.Surface((panel_w - 28, 44), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, line_y - 5))
        if row_key == "kick_level_index":
            safe_index = max(0, min(len(_KICK_LEVEL_LABELS) - 1, int(state.kick_level_index)))
            value = _KICK_LEVEL_LABELS[safe_index]
        elif row_key == "rotation_animation_duration_ms_2d":
            value = _format_animation_duration(
                int(state.rotation_animation_duration_ms_2d)
            )
        elif row_key == "rotation_animation_duration_ms_nd":
            value = _format_animation_duration(
                int(state.rotation_animation_duration_ms_nd)
            )
        elif row_key == "translation_animation_duration_ms":
            value = _format_animation_duration(
                int(state.translation_animation_duration_ms)
            )
        elif row_key == "auto_speedup_enabled":
            value = "ON" if int(state.auto_speedup_enabled) else "OFF"
        else:
            value = str(int(state.lines_per_level))
        label_surf = fonts.menu_font.render(label, True, color)
        value_surf = fonts.menu_font.render(value, True, color)
        screen.blit(label_surf, (panel_x + 22, line_y))
        screen.blit(value_surf, (panel_x + panel_w - value_surf.get_width() - 22, line_y))
        line_y += 58

    if state.status:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 28)
        status = fonts.hint_font.render(status_text, True, color)
        screen.blit(status, ((width - status.get_width()) // 2, panel_y + panel_h + 18))


def run_advanced_gameplay_menu(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
) -> pygame.Surface:
    selected = 0
    row_keys = (
        "kick_level_index",
        "rotation_animation_duration_ms_2d",
        "rotation_animation_duration_ms_nd",
        "translation_animation_duration_ms",
        "auto_speedup_enabled",
        "lines_per_level",
    )
    running = True
    clock = pygame.time.Clock()
    while running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            selected, running = _handle_advanced_gameplay_event(
                event=event,
                state=state,
                selected=selected,
                row_keys=row_keys,
            )
            if not running:
                break
        if not running or not state.running:
            break
        _draw_advanced_gameplay_menu(screen, fonts, state, selected=selected)
        pygame.display.flip()
    return screen



def _draw_unified_settings_menu(
    screen: pygame.Surface, fonts, state: _UnifiedSettingsState
) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render(_SETTINGS_HUB_COPY["title"], True, TEXT_COLOR)
    categories = ", ".join(_configured_top_level_labels())
    subtitle_text = fit_text(
        fonts.hint_font,
        _SETTINGS_HUB_COPY["subtitle_categories_template"].format(
            categories=categories
        ),
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

    hints = tuple(_SETTINGS_HUB_COPY["hints"])
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
    fonts,
    state: _UnifiedSettingsState,
    key: int,
) -> pygame.Surface:
    text_mode_screen = _dispatch_unified_text_mode_key(screen, state, key)
    if text_mode_screen is not None:
        return text_mode_screen
    nav_key = normalize_menu_navigation_key(key)
    if _handle_unified_exit_key(state, key=key, nav_key=nav_key):
        state.running = False
        return screen
    if nav_key == pygame.K_UP:
        state.pending_reset_confirm = False
        state.selected = (state.selected - 1) % len(_UNIFIED_SELECTABLE)
        play_sfx("menu_move")
        return screen
    if nav_key == pygame.K_DOWN:
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
            _set_unified_status(state, _SETTINGS_HUB_COPY["reset_confirm_f8"])
            return screen
        return _reset_unified_settings(screen, state)
    if _adjust_unified_with_arrows(state, key):
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return _handle_unified_enter(screen, fonts, state)
    return screen


def _handle_unified_exit_key(
    state: _UnifiedSettingsState,
    *,
    key: int,
    nav_key: int,
) -> bool:
    if key == pygame.K_q:
        state.running = False
        return True
    if nav_key == pygame.K_ESCAPE:
        state.running = False
        return True
    return False


def _dispatch_unified_text_mode_key(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
    key: int,
) -> pygame.Surface | None:
    if not _is_unified_text_mode(state):
        return None
    if key == pygame.K_ESCAPE:
        _stop_unified_text_mode(state)
        _set_unified_status(state, "Value edit cancelled")
        return screen
    if key == pygame.K_BACKSPACE:
        state.text_mode_replace_on_type = False
        state.text_mode_buffer = state.text_mode_buffer[:-1]
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        updated = _apply_unified_numeric_text_value(state)
        _stop_unified_text_mode(state)
        if updated:
            play_sfx("menu_move")
        return screen
    return screen


def _process_unified_events(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
) -> tuple[pygame.Surface, bool]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.running = False
            return screen, False
        if event.type == pygame.TEXTINPUT and _is_unified_text_mode(state):
            _handle_unified_text_input(state, event.text)
            continue
        if event.type != pygame.KEYDOWN:
            continue
        screen = _dispatch_unified_key(screen, fonts, state, event.key)
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
    state = build_unified_settings_state(
        audio_settings=audio_settings,
        display_settings=display_settings,
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
        screen, keep_running = _process_unified_events(screen, fonts, state)
        if not keep_running or not state.running:
            break
        _draw_unified_settings_menu(screen, fonts, state)
        pygame.display.flip()

    _stop_unified_text_mode(state)
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
