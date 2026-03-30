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
from tet4d.ui.pygame.ui_utils import (
    draw_fitted_text_line,
    draw_selection_highlight,
    draw_wrapped_label_value_lines,
    draw_vertical_gradient,
    wrapped_label_value_layout,
)

from .settings_hub_actions import (
    _adjust_unified_with_arrows,
    _apply_unified_numeric_text_value,
    _clear_topology_cache_action,
    _measure_topology_cache,
    _adjust_advanced_gameplay_value,
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
    _NUMERIC_TEXT_EDIT_ROWS,
    _SETTINGS_HUB_COPY,
    _UnifiedSettingsState,
    _unified_value_text,
    _validate_unified_layout_against_policy,
    build_unified_settings_state,
    selectable_index_by_row_key_for_rows,
    selectable_indexes_for_rows,
    settings_rows_for_category,
    settings_subtitle_for_category,
    settings_title_for_category,
)


def _draw_wrapped_settings_row(
    screen: pygame.Surface,
    *,
    fonts,
    panel_x: int,
    panel_w: int,
    line_y: int,
    label_lines: tuple[str, ...],
    value_lines: tuple[str, ...],
    row_height: int,
    color: tuple[int, int, int],
    selected: bool,
) -> None:
    row_rect = pygame.Rect(panel_x + 14, line_y - 5, panel_w - 28, row_height)
    if selected:
        draw_selection_highlight(screen, rect=row_rect)
    draw_wrapped_label_value_lines(
        screen,
        font=fonts.menu_font,
        label_lines=label_lines,
        value_lines=value_lines,
        label_x=panel_x + 22,
        value_right=panel_x + panel_w - 22,
        top_y=line_y,
        label_color=color,
    )


def _handle_unified_enter(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
    *,
    row_key: str,
) -> pygame.Surface:
    if row_key in _NUMERIC_TEXT_EDIT_ROWS:
        _start_unified_numeric_text_mode(state, row_key)
        return screen
    action_screen = _handle_unified_action_row_enter(
        screen,
        state,
        row_key=row_key,
    )
    if action_screen is not None:
        return action_screen
    if row_key in {
        "audio_mute",
        "display_fullscreen",
        "analytics_score_logging",
        "game_random_mode",
    }:
        state.pending_reset_confirm = False
        _adjust_unified_with_arrows(state, pygame.K_RIGHT)
        return screen
    if row_key in {
        "rotation_animation_mode",
        "kick_level_index",
        "rotation_animation_duration_ms_2d",
        "rotation_animation_duration_ms_nd",
        "translation_animation_duration_ms",
        "auto_speedup_enabled",
        "lines_per_level",
    }:
        if _adjust_advanced_gameplay_value(
            state,
            row_key,
            0,
            enter_pressed=True,
        ):
            _mark_unified_dirty(state)
            _set_unified_status(state, "Advanced gameplay updated (not saved yet)")
            play_sfx("menu_move")
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


def _handle_unified_action_row_enter(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
    *,
    row_key: str,
) -> pygame.Surface | None:
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
    if row_key == "topology_cache_measure":
        _measure_topology_cache(state)
        return screen
    if row_key == "topology_cache_clear":
        _clear_topology_cache_action(state)
        return screen
    return None


def _draw_unified_settings_menu(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
    *,
    rows: tuple[tuple[str, str, str], ...],
    selectable_rows: tuple[int, ...],
    category_id: str | None,
) -> None:
    draw_vertical_gradient(screen, BG_TOP, BG_BOTTOM)
    width, height = screen.get_size()
    title = draw_fitted_text_line(
        screen,
        font=fonts.title_font,
        text=settings_title_for_category(category_id),
        color=TEXT_COLOR,
        max_width=width - 28,
        center_x=width // 2,
        y=44,
    )
    subtitle = draw_fitted_text_line(
        screen,
        font=fonts.hint_font,
        text=settings_subtitle_for_category(category_id),
        color=MUTED_COLOR,
        max_width=width - 28,
        center_x=width // 2,
        y=44 + title.get_height() + 8,
    )
    title_y = 44
    subtitle_y = title_y + title.get_height() + 8

    panel_w = min(700, max(360, width - 40))
    line_h = fonts.hint_font.get_height() + 3
    panel_top = subtitle_y + subtitle.get_height() + 10
    bottom_lines = 2 + (1 if state.status else 0)
    panel_max_h = max(
        180,
        height
        - panel_top
        - (bottom_lines * line_h)
        - 10
    )
    header_count = sum(
        1 for kind, _label, _row_key in rows if kind == "header"
    )
    item_count = sum(
        1 for kind, _label, _row_key in rows if kind == "item"
    )
    header_step_default = fonts.hint_font.get_height() + 10
    item_heights_default = [
        wrapped_label_value_layout(
            fonts.menu_font,
            label=label,
            value=_unified_value_text(state, row_key),
            total_width=panel_w,
        )[2]
        for kind, label, row_key in rows
        if kind == "item"
    ]
    item_step_default = max(
        fonts.menu_font.get_height() + 8,
        int(sum(item_heights_default) / max(1, len(item_heights_default))),
    )
    required_default = 18 + (header_count * header_step_default) + sum(
        height + 6 for height in item_heights_default
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

    selected_row_idx = selectable_rows[state.selected]
    y = panel_y + 14
    panel_bottom = panel_y + panel_h - 8
    for idx, (row_kind, label, row_key) in enumerate(rows):
        if y > panel_bottom:
            break
        if row_kind == "header":
            draw_fitted_text_line(
                screen,
                font=fonts.hint_font,
                text=label,
                color=(182, 206, 255),
                max_width=panel_w - 44,
                x=panel_x + 22,
                y=y + 3,
            )
            y += header_step
            continue

        if y + fonts.menu_font.get_height() > panel_bottom:
            break
        selected = idx == selected_row_idx
        color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        value = _unified_value_text(state, row_key)
        label_lines, value_lines, row_height = wrapped_label_value_layout(
            fonts.menu_font,
            label=label,
            value=value,
            total_width=panel_w,
        )
        _draw_wrapped_settings_row(
            screen,
            fonts=fonts,
            panel_x=panel_x,
            panel_w=panel_w,
            line_y=y,
            label_lines=label_lines,
            value_lines=value_lines,
            row_height=row_height,
            color=color,
            selected=selected,
        )
        y += row_height + max(6, item_step - row_height)

    hints = tuple(_SETTINGS_HUB_COPY["hints"])
    hy = panel_y + panel_h + 8
    max_hint_lines = max(0, (height - hy - 6) // max(1, line_h))
    hint_budget = max(0, max_hint_lines - (1 if state.status else 0))
    for line in hints[:hint_budget]:
        surf = draw_fitted_text_line(
            screen,
            font=fonts.hint_font,
            text=line,
            color=MUTED_COLOR,
            max_width=width - 28,
            center_x=width // 2,
            y=hy,
        )
        hy += surf.get_height() + 3

    if state.status and hy + line_h <= height - 6:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        draw_fitted_text_line(
            screen,
            font=fonts.hint_font,
            text=state.status,
            color=color,
            max_width=width - 28,
            center_x=width // 2,
            y=hy + 2,
        )



def _dispatch_unified_key(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
    key: int,
    *,
    rows: tuple[tuple[str, str, str], ...],
    selectable_rows: tuple[int, ...],
) -> pygame.Surface:
    text_mode_screen = _dispatch_unified_text_mode_key(screen, state, key)
    if text_mode_screen is not None:
        return text_mode_screen
    row_key = rows[selectable_rows[state.selected]][2]
    nav_key = normalize_menu_navigation_key(key)
    if _handle_unified_exit_key(state, key=key, nav_key=nav_key):
        state.running = False
        return screen
    nav_screen = _dispatch_unified_nav_key(
        screen,
        state,
        key=key,
        nav_key=nav_key,
        selectable_rows=selectable_rows,
    )
    if nav_screen is not None:
        return nav_screen
    if _adjust_unified_with_arrows(state, key, row_key=row_key):
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return _handle_unified_enter(screen, fonts, state, row_key=row_key)
    return screen


def _dispatch_unified_nav_key(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
    *,
    key: int,
    nav_key: int,
    selectable_rows: tuple[int, ...],
) -> pygame.Surface | None:
    if nav_key == pygame.K_UP:
        state.pending_reset_confirm = False
        state.selected = (state.selected - 1) % len(selectable_rows)
        play_sfx("menu_move")
        return screen
    if nav_key == pygame.K_DOWN:
        state.pending_reset_confirm = False
        state.selected = (state.selected + 1) % len(selectable_rows)
        play_sfx("menu_move")
        return screen
    if key == pygame.K_F5:
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if key != pygame.K_F8:
        return None
    if not state.pending_reset_confirm:
        state.pending_reset_confirm = True
        _set_unified_status(state, _SETTINGS_HUB_COPY["reset_confirm_f8"])
        return screen
    return _reset_unified_settings(screen, state)


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
    *,
    rows: tuple[tuple[str, str, str], ...],
    selectable_rows: tuple[int, ...],
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
        screen = _dispatch_unified_key(
            screen,
            fonts,
            state,
            event.key,
            rows=rows,
            selectable_rows=selectable_rows,
        )
        if not state.running:
            break
    return screen, True


def run_settings_hub_menu(
    screen: pygame.Surface,
    fonts,
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
    initial_row_key: str | None = None,
    category_id: str | None = None,
) -> SettingsHubResult:
    rows = settings_rows_for_category(category_id)
    selectable_rows = selectable_indexes_for_rows(rows)
    state = build_unified_settings_state(
        audio_settings=audio_settings,
        display_settings=display_settings,
    )
    visible_row_index = selectable_index_by_row_key_for_rows(rows)
    if initial_row_key:
        selected = visible_row_index.get(str(initial_row_key).strip().lower())
        if selected is not None:
            state.selected = selected
    if state.selected >= len(selectable_rows):
        state.selected = 0
    ok_layout, msg_layout = _validate_unified_layout_against_policy()
    if category_id is None and not ok_layout:
        _set_unified_status(state, msg_layout, is_error=True)
    _sync_audio_preview(state.audio_settings)
    _sync_analytics_preview(state.score_logging_enabled)

    clock = pygame.time.Clock()
    keep_running = True
    while state.running:
        _dt = clock.tick(60)
        screen, keep_running = _process_unified_events(
            screen,
            fonts,
            state,
            rows=rows,
            selectable_rows=selectable_rows,
        )
        if not keep_running or not state.running:
            break
        _draw_unified_settings_menu(
            screen,
            fonts,
            state,
            rows=rows,
            selectable_rows=selectable_rows,
            category_id=category_id,
        )
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
