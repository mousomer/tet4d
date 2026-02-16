from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pygame

from .keybindings import (
    REBIND_CONFLICT_REPLACE,
    active_key_profile,
    create_auto_profile,
    cycle_key_profile,
    cycle_rebind_conflict_mode,
    delete_key_profile,
    keybinding_file_label,
    load_active_profile_bindings,
    load_keybindings_file,
    rebind_action_key,
    reset_active_profile_bindings,
    runtime_binding_groups_for_dimension,
    save_keybindings_file,
    set_active_key_profile,
)


_DRAW_GROUP_ORDER = ("game", "camera", "slice", "system")


def _key_name(key: int) -> str:
    name = pygame.key.name(key)
    if not name:
        return str(key)
    if len(name) == 1:
        return name.upper()
    words = []
    for token in name.split():
        if token == "kp":
            words.append("Numpad")
            continue
        words.append(token.capitalize())
    return " ".join(words)


def _format_key_tuple(keys: Sequence[int]) -> str:
    if not keys:
        return "-"
    return "/".join(_key_name(key) for key in keys)


def _action_rows_for_dimension(dimension: int) -> list[tuple[str, str]]:
    groups = runtime_binding_groups_for_dimension(dimension)
    rows: list[tuple[str, str]] = []
    for group_name in _DRAW_GROUP_ORDER:
        actions = groups.get(group_name)
        if not actions:
            continue
        for action_name in sorted(actions.keys()):
            rows.append((group_name, action_name))
    return rows


@dataclass
class KeybindingsMenuState:
    dimension: int
    selected_row: int = 0
    capture_mode: bool = False
    conflict_mode: str = REBIND_CONFLICT_REPLACE
    status: str = ""
    status_error: bool = False
    active_profile: str = ""

    def __post_init__(self) -> None:
        self.active_profile = active_key_profile()


def _draw_background(surface: pygame.Surface) -> None:
    width, height = surface.get_size()
    top = (14, 18, 42)
    bottom = (4, 7, 20)
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(top[0] * (1 - t) + bottom[0] * t),
            int(top[1] * (1 - t) + bottom[1] * t),
            int(top[2] * (1 - t) + bottom[2] * t),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))


def _draw_menu(
    surface: pygame.Surface,
    fonts,
    state: KeybindingsMenuState,
    rows: list[tuple[str, str]],
) -> None:
    _draw_background(surface)
    width, height = surface.get_size()
    title = fonts.title_font.render("Keybindings Setup", True, (232, 232, 240))
    subtitle = fonts.hint_font.render(
        "Up/Down select, Enter rebind, Left/Right mode (2D/3D/4D), Esc back",
        True,
        (192, 200, 228),
    )
    surface.blit(title, ((width - title.get_width()) // 2, 28))
    surface.blit(subtitle, ((width - subtitle.get_width()) // 2, 74))

    header = (
        f"Dimension: {state.dimension}D   "
        f"Profile: {state.active_profile}   "
        f"Conflict: {state.conflict_mode}"
    )
    header_surf = fonts.hint_font.render(header, True, (210, 220, 245))
    surface.blit(header_surf, ((width - header_surf.get_width()) // 2, 106))

    panel_w = min(width - 40, 1060)
    panel_h = min(height - 230, 560)
    panel_x = (width - panel_w) // 2
    panel_y = 138

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 152), panel.get_rect(), border_radius=14)
    surface.blit(panel, (panel_x, panel_y))

    groups = runtime_binding_groups_for_dimension(state.dimension)
    row_y = panel_y + 16
    line_h = fonts.panel_font.get_height() + 5

    for idx, (group, action_name) in enumerate(rows):
        keys = groups.get(group, {}).get(action_name, ())
        key_text = _format_key_tuple(keys)
        label = f"{group}.{action_name}"
        selected = idx == state.selected_row
        color = (255, 224, 130) if selected else (228, 230, 242)
        if selected:
            hi = pygame.Surface((panel_w - 24, line_h + 4), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            surface.blit(hi, (panel_x + 12, row_y - 2))

        label_surf = fonts.panel_font.render(label, True, color)
        key_surf = fonts.panel_font.render(key_text, True, color)
        surface.blit(label_surf, (panel_x + 18, row_y))
        surface.blit(key_surf, (panel_x + panel_w - key_surf.get_width() - 18, row_y))
        row_y += line_h
        if row_y > panel_y + panel_h - line_h:
            break

    hints = [
        "L load   S save   F6 reset profile bindings",
        "[ / ] profile prev/next   N new profile   Backspace delete custom profile",
        "C conflict mode cycle   Enter capture   Esc cancel/back",
        f"File: {keybinding_file_label(state.dimension)}",
    ]
    hint_y = panel_y + panel_h + 12
    for line in hints:
        surf = fonts.hint_font.render(line, True, (188, 197, 228))
        surface.blit(surf, ((width - surf.get_width()) // 2, hint_y))
        hint_y += surf.get_height() + 3

    if state.capture_mode and rows:
        group, action = rows[state.selected_row]
        cap = fonts.hint_font.render(
            f"Press a key for {group}.{action} (Esc to cancel capture)",
            True,
            (255, 226, 144),
        )
        surface.blit(cap, ((width - cap.get_width()) // 2, hint_y + 2))
        hint_y += cap.get_height() + 4

    if state.status:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status = fonts.hint_font.render(state.status, True, color)
        surface.blit(status, ((width - status.get_width()) // 2, hint_y + 2))


def _run_menu_action(state: KeybindingsMenuState, key: int, rows: list[tuple[str, str]]) -> bool:
    if state.capture_mode:
        if key == pygame.K_ESCAPE:
            state.capture_mode = False
            state.status = "Capture cancelled"
            state.status_error = False
            return False
        if rows:
            group, action_name = rows[state.selected_row]
            ok, msg = rebind_action_key(
                state.dimension,
                group,
                action_name,
                key,
                conflict_mode=state.conflict_mode,
            )
            state.status = msg
            state.status_error = not ok
        state.capture_mode = False
        return False

    if key == pygame.K_ESCAPE:
        return True
    if key == pygame.K_UP:
        if rows:
            state.selected_row = (state.selected_row - 1) % len(rows)
        return False
    if key == pygame.K_DOWN:
        if rows:
            state.selected_row = (state.selected_row + 1) % len(rows)
        return False
    if key == pygame.K_LEFT:
        state.dimension = 4 if state.dimension == 2 else state.dimension - 1
        state.selected_row = 0
        return False
    if key == pygame.K_RIGHT:
        state.dimension = 2 if state.dimension == 4 else state.dimension + 1
        state.selected_row = 0
        return False
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        if rows:
            state.capture_mode = True
        return False
    if key == pygame.K_c:
        state.conflict_mode = cycle_rebind_conflict_mode(state.conflict_mode, 1)
        state.status = f"Conflict mode: {state.conflict_mode}"
        state.status_error = False
        return False
    if key == pygame.K_l:
        ok, msg = load_keybindings_file(state.dimension)
        state.status = msg
        state.status_error = not ok
        return False
    if key == pygame.K_s:
        ok, msg = save_keybindings_file(state.dimension)
        state.status = msg
        state.status_error = not ok
        return False
    if key == pygame.K_F6:
        ok, msg = reset_active_profile_bindings(state.dimension)
        state.status = msg
        state.status_error = not ok
        return False
    if key == pygame.K_LEFTBRACKET:
        ok, msg, profile = cycle_key_profile(-1)
        state.active_profile = profile
        state.status = msg
        state.status_error = not ok
        return False
    if key == pygame.K_RIGHTBRACKET:
        ok, msg, profile = cycle_key_profile(1)
        state.active_profile = profile
        state.status = msg
        state.status_error = not ok
        return False
    if key == pygame.K_n:
        ok, msg, profile = create_auto_profile()
        if ok and profile is not None:
            set_ok, set_msg = set_active_key_profile(profile)
            if not set_ok:
                ok = False
                msg = set_msg
            else:
                load_ok, load_msg = load_active_profile_bindings()
                if not load_ok:
                    ok = False
                    msg = load_msg
                else:
                    state.active_profile = profile
        state.status = msg
        state.status_error = not ok
        return False
    if key == pygame.K_BACKSPACE:
        ok, msg = delete_key_profile(state.active_profile)
        state.active_profile = active_key_profile()
        state.status = msg
        state.status_error = not ok
        return False

    return False


def run_keybindings_menu(screen: pygame.Surface, fonts, dimension: int = 2) -> None:
    state = KeybindingsMenuState(dimension=max(2, min(4, int(dimension))))
    clock = pygame.time.Clock()

    running = True
    while running:
        _dt = clock.tick(60)
        rows = _action_rows_for_dimension(state.dimension)
        if rows:
            state.selected_row = max(0, min(len(rows) - 1, state.selected_row))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type != pygame.KEYDOWN:
                continue
            should_exit = _run_menu_action(state, event.key, rows)
            if should_exit:
                running = False
                break

        _draw_menu(screen, fonts, state, rows)
        pygame.display.flip()
