from __future__ import annotations

from typing import Any

import pygame

from tet4d.engine.runtime.menu_config import menu_item_id, settings_menu_id
from tet4d.engine.runtime.settings_schema import (
    ENDGAME_SPEED_PERCENT_MAX,
    ENDGAME_SPEED_PERCENT_MIN,
)
from tet4d.ui.pygame.menu.keybindings_menu import run_keybindings_menu
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    apply_display_mode,
    capture_windowed_display_settings,
    normalize_display_settings,
)
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings, play_sfx
from tet4d.ui.pygame.ui_utils import (
    SliderRowLayout,
    compute_slider_row_layout,
    compute_vertical_scroll_metrics,
    default_menu_back_chip_rect,
    draw_corner_chip,
    draw_fitted_text_line,
    draw_selection_highlight,
    draw_tron_menu_background,
    draw_tron_panel,
    draw_value_slider,
    draw_vertical_scrollbar,
    draw_wrapped_label_value_lines,
    ensure_scroll_offset_visible,
    format_menu_title,
    standard_menu_panel_rect,
    wrap_text_lines,
    wrapped_label_value_layout,
    wrapped_row_height,
)

from .settings_hub_actions import (
    _adjust_unified_with_arrows,
    _apply_unified_numeric_text_value,
    _clear_topology_cache_action,
    _handle_unified_text_input,
    _is_unified_text_mode,
    _mark_unified_dirty,
    _measure_topology_cache,
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
    current_page_selectable_indexes,
    current_settings_page_id,
    current_settings_page_items,
    settings_title_for_page,
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
    slider_fraction: float | None = None,
    flash_strength: float = 0.0,
    slider_layout: SliderRowLayout | None = None,
) -> None:
    row_rect = pygame.Rect(panel_x + 10, line_y - 4, panel_w - 20, row_height)
    if selected:
        draw_selection_highlight(screen, rect=row_rect, border_radius=10)
    if flash_strength > 0.0:
        draw_selection_highlight(
            screen,
            rect=row_rect,
            color=(112, 236, 255, min(112, int(42 + (70 * flash_strength)))),
            border_radius=10,
        )
    draw_wrapped_label_value_lines(
        screen,
        font=fonts.menu_font,
        label_lines=label_lines,
        value_lines=value_lines,
        label_x=panel_x + 18,
        value_right=panel_x + panel_w - 18,
        top_y=line_y
        + (slider_layout.text_top_padding if slider_layout is not None else 0),
        label_color=color,
    )
    if slider_fraction is not None and slider_layout is not None:
        draw_value_slider(
            screen,
            rect=pygame.Rect(
                panel_x + panel_w - 18 - slider_layout.slider_width,
                line_y
                + row_height
                - slider_layout.row_bottom_padding
                - slider_layout.slider_height,
                slider_layout.slider_width,
                slider_layout.slider_height,
            ),
            fraction=slider_fraction,
            flash_strength=flash_strength,
        )


def _slider_fraction_for_row(
    state: _UnifiedSettingsState, row_key: str
) -> float | None:
    def _percent_fraction(value: int, *, minimum: int, maximum: int) -> float:
        span = max(1, maximum - minimum)
        return min(1.0, max(0.0, (int(value) - minimum) / span))

    duration_values = {
        "rotation_animation_duration_ms_2d": int(
            state.rotation_animation_duration_ms_2d
        ),
        "rotation_animation_duration_ms_nd": int(
            state.rotation_animation_duration_ms_nd
        ),
        "translation_animation_duration_ms": int(
            state.translation_animation_duration_ms
        ),
    }
    duration_value = duration_values.get(row_key)
    if duration_value is not None:
        return min(1.0, max(0.0, duration_value / 300.0))

    percent_values = {
        "endgame_relic_speed_percent": int(state.endgame_relic_speed_percent),
        "endgame_shatter_speed_percent": int(state.endgame_shatter_speed_percent),
    }
    percent_value = percent_values.get(row_key)
    if percent_value is not None:
        return _percent_fraction(
            percent_value,
            minimum=ENDGAME_SPEED_PERCENT_MIN,
            maximum=ENDGAME_SPEED_PERCENT_MAX,
        )

    if row_key == "audio_master":
        return float(state.audio_settings.master_volume)
    if row_key == "audio_sfx":
        return float(state.audio_settings.sfx_volume)
    if row_key == "display_overlay_transparency":
        return float(state.overlay_transparency) / 0.9
    if row_key == "lines_per_level":
        return min(1.0, max(0.0, (int(state.lines_per_level) - 1) / 29.0))
    return None


def _current_items(state: _UnifiedSettingsState) -> tuple[dict[str, Any], ...]:
    return current_settings_page_items(state)


def _current_selectable_indexes(state: _UnifiedSettingsState) -> tuple[int, ...]:
    return current_page_selectable_indexes(state)


def _current_selected_item(state: _UnifiedSettingsState) -> dict[str, Any] | None:
    items = _current_items(state)
    selectable = _current_selectable_indexes(state)
    if not selectable:
        return None
    state.selected = max(0, min(len(selectable) - 1, int(state.selected)))
    return items[selectable[state.selected]]


def _remember_page_state(state: _UnifiedSettingsState) -> None:
    page_id = current_settings_page_id(state)
    state.selected_by_page[page_id] = int(state.selected)
    state.scroll_offset_by_page[page_id] = int(state.scroll_offset)


def _restore_page_state(state: _UnifiedSettingsState) -> None:
    page_id = current_settings_page_id(state)
    state.selected = int(state.selected_by_page.get(page_id, 0))
    state.scroll_offset = int(state.scroll_offset_by_page.get(page_id, 0))
    selectable = _current_selectable_indexes(state)
    if selectable:
        state.selected = max(0, min(len(selectable) - 1, int(state.selected)))
    else:
        state.selected = 0


def _push_page(state: _UnifiedSettingsState, page_id: str) -> None:
    _remember_page_state(state)
    state.page_stack.append(str(page_id).strip().lower())
    _restore_page_state(state)
    state.pending_reset_confirm = False
    _stop_unified_text_mode(state)


def _pop_page(state: _UnifiedSettingsState) -> bool:
    if len(state.page_stack) <= 1:
        return False
    _remember_page_state(state)
    state.page_stack.pop()
    _restore_page_state(state)
    state.pending_reset_confirm = False
    _stop_unified_text_mode(state)
    return True


def _page_item_value_text(state: _UnifiedSettingsState, item: dict[str, Any]) -> str:
    item_type = str(item.get("type", "")).lower()
    item_id = menu_item_id(item)
    if item_type in {"toggle", "selector", "slider"}:
        return _unified_value_text(state, item_id)
    if item_type == "submenu":
        return "Open"
    if item_type in {"action", "legacy_dispatch"}:
        action_id = str(item.get("action_id", "")).strip().lower()
        if action_id == "display_apply":
            return "Enter"
        if action_id in {"save", "reset", "back", "topology_cache_clear"}:
            return ""
        if action_id == "topology_cache_measure":
            return _unified_value_text(state, action_id)
        return "Enter"
    return ""


def _item_row_layout(
    fonts,
    *,
    item: dict[str, Any],
    content_width: int,
    state: _UnifiedSettingsState,
) -> dict[str, Any]:
    item_type = str(item.get("type", "")).lower()
    label = str(item.get("label", ""))
    item_id = menu_item_id(item)
    if item_type == "section":
        height = fonts.hint_font.get_height() + 10
        return {"height": height, "label": label}
    if item_type == "info":
        lines = wrap_text_lines(fonts.hint_font, label, max(80, content_width - 8))
        height = wrapped_row_height(
            fonts.hint_font,
            max(1, len(lines)),
            min_padding=12,
            base_padding=10,
        )
        return {"height": height, "label_lines": lines}

    value = _page_item_value_text(state, item)
    slider_fraction = (
        _slider_fraction_for_row(state, item_id) if item_type == "slider" else None
    )
    slider_layout = (
        compute_slider_row_layout(
            fonts.menu_font,
            label=label,
            value=value,
            total_width=content_width - 10,
        )
        if slider_fraction is not None
        else None
    )
    if slider_layout is not None:
        return {
            "height": slider_layout.row_height,
            "label_lines": slider_layout.label_lines,
            "value_lines": slider_layout.value_lines,
            "slider_fraction": slider_fraction,
            "slider_layout": slider_layout,
        }
    label_lines, value_lines, row_height = wrapped_label_value_layout(
        fonts.menu_font,
        label=label,
        value=value,
        total_width=content_width - 10,
    )
    return {
        "height": row_height,
        "label_lines": label_lines,
        "value_lines": value_lines,
        "slider_fraction": None,
        "slider_layout": None,
    }


def _page_layouts(
    fonts,
    *,
    items: tuple[dict[str, Any], ...],
    content_width: int,
    state: _UnifiedSettingsState,
) -> tuple[list[dict[str, Any]], int]:
    layouts: list[dict[str, Any]] = []
    y = 0
    for item in items:
        item_layout = _item_row_layout(
            fonts,
            item=item,
            content_width=content_width,
            state=state,
        )
        row_height = int(item_layout["height"])
        layouts.append(
            {
                "item": item,
                "top": y,
                "bottom": y + row_height,
                "layout": item_layout,
            }
        )
        gap = 8 if str(item.get("type", "")).lower() == "section" else 6
        y += row_height + gap
    return layouts, max(0, y - 6)


def _draw_page_item(
    screen: pygame.Surface,
    *,
    fonts,
    draw_rect: pygame.Rect,
    item: dict[str, Any],
    layout: dict[str, Any],
    selected: bool,
    flash_strength: float,
    state: _UnifiedSettingsState,
) -> None:
    item_type = str(item.get("type", "")).lower()
    label = str(item.get("label", ""))
    item_id = menu_item_id(item)
    if item_type == "section":
        draw_fitted_text_line(
            screen,
            font=fonts.hint_font,
            text=label,
            color=(182, 206, 255),
            max_width=draw_rect.width,
            x=draw_rect.x,
            y=draw_rect.y + 2,
        )
        return
    if item_type == "info":
        y = draw_rect.y + 4
        for line in layout["label_lines"]:
            surf = fonts.hint_font.render(line, True, MUTED_COLOR)
            screen.blit(surf, (draw_rect.x, y))
            y += fonts.hint_font.get_height() + 2
        return

    color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
    _draw_wrapped_settings_row(
        screen,
        fonts=fonts,
        panel_x=draw_rect.x - 8,
        panel_w=draw_rect.width + 16,
        line_y=draw_rect.y,
        label_lines=layout["label_lines"],
        value_lines=layout["value_lines"],
        row_height=int(layout["height"]),
        color=color,
        selected=selected,
        slider_fraction=layout["slider_fraction"],
        flash_strength=flash_strength if state.flash_row_key == item_id else 0.0,
        slider_layout=layout["slider_layout"],
    )


def _draw_unified_settings_menu(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
) -> None:
    draw_tron_menu_background(screen, top_color=BG_TOP, bottom_color=BG_BOTTOM)
    width, height = screen.get_size()
    title = draw_fitted_text_line(
        screen,
        font=fonts.title_font,
        text=format_menu_title(settings_title_for_page(current_settings_page_id(state))),
        color=TEXT_COLOR,
        max_width=width - 28,
        center_x=width // 2,
        y=44,
    )
    draw_corner_chip(screen, font=fonts.hint_font, text="Back", x=18, y=18)

    line_h = fonts.hint_font.get_height() + 3
    bottom_lines = 2 + (1 if state.status else 0)
    panel_rect = standard_menu_panel_rect(
        screen,
        panel_w=min(width - 40, 820),
        panel_h=max(220, height - (title.get_height() + 44) - (bottom_lines * line_h) - 46),
        panel_top=44 + title.get_height() + 18,
        bottom_reserved=(bottom_lines * line_h) + 10,
    )
    draw_tron_panel(screen, rect=panel_rect)

    viewport_rect = pygame.Rect(
        panel_rect.x + 18,
        panel_rect.y + 14,
        panel_rect.width - 36,
        panel_rect.height - 24,
    )
    items = _current_items(state)
    selectable = _current_selectable_indexes(state)

    layouts, content_height = _page_layouts(
        fonts,
        items=items,
        content_width=viewport_rect.width,
        state=state,
    )
    metrics = compute_vertical_scroll_metrics(
        viewport_rect=viewport_rect,
        content_height=content_height,
        scroll_offset=state.scroll_offset,
    )
    if metrics.shows_scrollbar:
        layouts, content_height = _page_layouts(
            fonts,
            items=items,
            content_width=viewport_rect.width - metrics.reserved_width,
            state=state,
        )
        metrics = compute_vertical_scroll_metrics(
            viewport_rect=viewport_rect,
            content_height=content_height,
            scroll_offset=state.scroll_offset,
        )

    if selectable:
        state.selected = max(0, min(len(selectable) - 1, int(state.selected)))
        selected_layout = layouts[selectable[state.selected]]
        state.scroll_offset = ensure_scroll_offset_visible(
            metrics.scroll_offset,
            item_top=int(selected_layout["top"]),
            item_bottom=int(selected_layout["bottom"]),
            viewport_height=metrics.viewport_height,
            content_height=content_height,
        )
        metrics = compute_vertical_scroll_metrics(
            viewport_rect=viewport_rect,
            content_height=content_height,
            scroll_offset=state.scroll_offset,
        )
    else:
        state.scroll_offset = 0

    content_rect = viewport_rect.copy()
    content_rect.width -= metrics.reserved_width
    previous_clip = screen.get_clip()
    screen.set_clip(viewport_rect)
    for idx, row in enumerate(layouts):
        item = row["item"]
        top = int(row["top"]) - metrics.scroll_offset + content_rect.y
        bottom = int(row["bottom"]) - metrics.scroll_offset + content_rect.y
        if bottom < viewport_rect.y or top > viewport_rect.bottom:
            continue
        draw_rect = pygame.Rect(
            content_rect.x,
            top,
            content_rect.width,
            int(row["bottom"]) - int(row["top"]),
        )
        _draw_page_item(
            screen,
            fonts=fonts,
            draw_rect=draw_rect,
            item=item,
            layout=row["layout"],
            selected=(idx in selectable and selectable[state.selected] == idx),
            flash_strength=max(0.0, min(1.0, state.flash_frames / 12.0)),
            state=state,
        )
    screen.set_clip(previous_clip)
    draw_vertical_scrollbar(screen, metrics=metrics)

    hy = panel_rect.y + panel_rect.height + 8
    hint_budget = max(0, (height - hy - 6) // max(1, line_h))
    for line in tuple(_SETTINGS_HUB_COPY["hints"])[: hint_budget - (1 if state.status else 0)]:
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


def _handle_special_action(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
    *,
    action_id: str,
) -> pygame.Surface | None:
    if action_id == "display_apply":
        state.display_settings = normalize_display_settings(state.display_settings)
        screen = apply_display_mode(
            state.display_settings,
            preferred_windowed_size=state.display_settings.windowed_size,
        )
        _mark_unified_dirty(state)
        state.pending_reset_confirm = False
        state.flash_row_key = action_id
        state.flash_frames = 12
        _set_unified_status(state, "Applied display mode")
        play_sfx("menu_confirm")
        return screen
    if action_id == "topology_cache_measure":
        _measure_topology_cache(state)
        return screen
    if action_id == "topology_cache_clear":
        _clear_topology_cache_action(state)
        return screen
    if action_id == "keybindings":
        run_keybindings_menu(screen, fonts, dimension=2, scope="general")
        _set_unified_status(state, "Returned from Keyboard Bindings")
        return screen
    return None


def _handle_unified_enter(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
) -> pygame.Surface:
    item = _current_selected_item(state)
    if item is None:
        return screen
    item_type = str(item.get("type", "")).lower()
    item_id = menu_item_id(item)
    if item_type == "submenu":
        target = str(item.get("menu_id", "")).strip().lower()
        if target:
            _push_page(state, target)
            play_sfx("menu_confirm")
        return screen
    if item_type == "legacy_dispatch":
        state.dispatched_action_id = str(item.get("action_id", "")).strip().lower()
        state.running = False
        return screen
    if item_type == "action":
        return _handle_unified_action_enter(screen, fonts, state, item=item)
    if item_id in _NUMERIC_TEXT_EDIT_ROWS:
        _start_unified_numeric_text_mode(state, item_id)
        return screen
    if item_type in {"toggle", "selector", "slider"}:
        state.pending_reset_confirm = False
        _adjust_unified_with_arrows(state, pygame.K_RIGHT, row_key=item_id)
        return screen
    return screen


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


def _handle_unified_action_enter(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
    *,
    item: dict[str, Any],
) -> pygame.Surface:
    action_id = str(item.get("action_id", "")).strip().lower()
    if action_id == "back":
        if not _pop_page(state):
            state.running = False
        return screen
    if action_id == "save":
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if action_id == "reset":
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_unified_status(state, "Press Enter on Reset defaults again to confirm")
            return screen
        return _reset_unified_settings(screen, state)
    special_screen = _handle_special_action(
        screen,
        fonts,
        state,
        action_id=action_id,
    )
    return special_screen if special_screen is not None else screen


def _handle_unified_navigation_key(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
    *,
    key: int,
    selectable_count: int,
) -> pygame.Surface | None:
    nav_key = normalize_menu_navigation_key(key)
    if key == pygame.K_q:
        state.running = False
        return screen
    if nav_key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
        if not _pop_page(state):
            state.running = False
        return screen
    if nav_key == pygame.K_UP:
        state.pending_reset_confirm = False
        state.selected = (state.selected - 1) % selectable_count
        play_sfx("menu_move")
        return screen
    if nav_key == pygame.K_DOWN:
        state.pending_reset_confirm = False
        state.selected = (state.selected + 1) % selectable_count
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
    return None


def _dispatch_unified_key(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
    key: int,
) -> pygame.Surface:
    text_mode_screen = _dispatch_unified_text_mode_key(screen, state, key)
    if text_mode_screen is not None:
        return text_mode_screen

    selectable = _current_selectable_indexes(state)
    if not selectable:
        if normalize_menu_navigation_key(key) == pygame.K_ESCAPE:
            state.running = False
        return screen

    navigation_screen = _handle_unified_navigation_key(
        screen,
        state,
        key=key,
        selectable_count=len(selectable),
    )
    if navigation_screen is not None:
        return navigation_screen

    item = _current_selected_item(state)
    if item is None:
        return screen
    item_type = str(item.get("type", "")).lower()
    item_id = menu_item_id(item)
    if item_type in {"toggle", "selector", "slider"} and _adjust_unified_with_arrows(
        state,
        key,
        row_key=item_id,
    ):
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return _handle_unified_enter(screen, fonts, state)
    return screen


def _handle_unified_non_key_event(
    state: _UnifiedSettingsState,
    event: pygame.event.Event,
) -> bool:
    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and int(getattr(event, "button", 0)) == 1
        and default_menu_back_chip_rect().collidepoint(getattr(event, "pos", (-1, -1)))
    ):
        if not _pop_page(state):
            state.running = False
        return True
    if event.type != pygame.TEXTINPUT:
        return False
    if _is_unified_text_mode(state):
        _handle_unified_text_input(state, event.text)
        return True
    item = _current_selected_item(state)
    if item is None:
        return False
    item_id = menu_item_id(item)
    if item_id in _NUMERIC_TEXT_EDIT_ROWS:
        _start_unified_numeric_text_mode(state, item_id)
        _handle_unified_text_input(state, event.text)
        return True
    return False


def _process_unified_events(
    screen: pygame.Surface,
    fonts,
    state: _UnifiedSettingsState,
) -> tuple[pygame.Surface, bool]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.running = False
            return screen, False
        if event.type != pygame.KEYDOWN:
            if _handle_unified_non_key_event(state, event):
                if not state.running:
                    return screen, True
                continue
            continue
        screen = _dispatch_unified_key(screen, fonts, state, event.key)
        if not state.running:
            break
    if state.flash_frames > 0:
        state.flash_frames -= 1
        if state.flash_frames <= 0:
            state.flash_frames = 0
            state.flash_row_key = ""
    return screen, True


def run_settings_hub_menu(
    screen: pygame.Surface,
    fonts,
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
    initial_page_id: str | None = None,
    initial_item_id: str | None = None,
) -> SettingsHubResult:
    state = build_unified_settings_state(
        audio_settings=audio_settings,
        display_settings=display_settings,
        initial_page_id=initial_page_id or settings_menu_id(),
        initial_item_id=initial_item_id,
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

    _remember_page_state(state)
    _stop_unified_text_mode(state)
    if not state.saved:
        _sync_audio_preview(state.original_audio)
        _sync_analytics_preview(state.original_score_logging_enabled)
        restored_display = normalize_display_settings(state.original_display)
        screen = apply_display_mode(
            restored_display,
            preferred_windowed_size=restored_display.windowed_size,
        )
        return SettingsHubResult(
            screen=screen,
            audio_settings=state.original_audio,
            display_settings=restored_display,
            keep_running=keep_running,
            dispatched_action_id=state.dispatched_action_id,
        )

    final_display = capture_windowed_display_settings(
        normalize_display_settings(state.display_settings)
    )
    return SettingsHubResult(
        screen=screen,
        audio_settings=state.audio_settings,
        display_settings=final_display,
        keep_running=keep_running,
        dispatched_action_id=state.dispatched_action_id,
    )
