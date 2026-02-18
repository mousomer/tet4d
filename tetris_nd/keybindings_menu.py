from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import pygame

from .menu_config import keybinding_category_docs
from .keybindings import (
    REBIND_CONFLICT_REPLACE,
    active_key_profile,
    binding_action_description,
    binding_group_description,
    binding_group_label,
    clone_key_profile,
    cycle_key_profile,
    cycle_rebind_conflict_mode,
    delete_key_profile,
    keybinding_file_label,
    load_active_profile_bindings,
    load_keybindings_file,
    next_auto_profile_name,
    rebind_action_key,
    rename_key_profile,
    reset_active_profile_bindings,
    runtime_binding_groups_for_dimension,
    save_keybindings_file,
    set_active_key_profile,
)


_CATEGORY_DOCS = keybinding_category_docs()
_SCOPE_ORDER = tuple(_CATEGORY_DOCS.get("scope_order", ("all", "2d", "3d", "4d")))
_VALID_SCOPES = tuple(dict.fromkeys((*_SCOPE_ORDER, "general", "all")))
_GROUP_ORDER = ("game", "camera", "slice", "system")
_TEXT_MODE_CREATE = "create"
_TEXT_MODE_RENAME = "rename"
_TEXT_MODE_SAVE_AS = "save_as"
_PROFILE_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
_SECTION_MENU: tuple[tuple[str, str, str], ...] = (
    ("general", "General Keybindings", "System actions shared across 2D/3D/4D."),
    ("2d", "2D Keybindings", "2D gameplay and shared system controls."),
    ("3d", "3D Keybindings", "3D gameplay, camera/view, slice, and system controls."),
    ("4d", "4D Keybindings", "4D gameplay, camera/view, slice, and system controls."),
)


def _scope_label(scope: str) -> str:
    if scope == "general":
        return "GENERAL"
    return "ALL" if scope == "all" else scope.upper()


def _scope_dimensions(scope: str) -> tuple[int, ...]:
    if scope in {"all", "general"}:
        return (2, 3, 4)
    return (int(scope[0]),)


def _scope_from_dimension(dimension: int) -> str:
    if dimension <= 2:
        return "2d"
    if dimension == 3:
        return "3d"
    return "4d"


def _doc_label(group: str) -> str:
    groups = _CATEGORY_DOCS.get("groups", {})
    if isinstance(groups, dict):
        raw = groups.get(group)
        if isinstance(raw, dict):
            label = raw.get("label")
            if isinstance(label, str) and label.strip():
                return label.strip()
    return binding_group_label(group)


def _doc_description(group: str) -> str:
    groups = _CATEGORY_DOCS.get("groups", {})
    if isinstance(groups, dict):
        raw = groups.get(group)
        if isinstance(raw, dict):
            desc = raw.get("description")
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
    return binding_group_description(group)


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


def _sanitize_profile_name(raw: str) -> str:
    lowered = raw.strip().lower()
    filtered = "".join(ch for ch in lowered if ch in _PROFILE_NAME_CHARS)
    return filtered[:64]


@dataclass(frozen=True)
class _BindingRow:
    dimension: int
    group: str
    action: str


@dataclass(frozen=True)
class _RenderedRow:
    kind: str  # header|binding
    text: str
    binding: _BindingRow | None = None


@dataclass
class KeybindingsMenuState:
    scope: str = "all"
    section_mode: bool = True
    allow_scope_sections: bool = True
    selected_section: int = 0
    selected_binding: int = 0
    scroll_top: int = 0
    capture_mode: bool = False
    conflict_mode: str = REBIND_CONFLICT_REPLACE
    status: str = ""
    status_error: bool = False
    active_profile: str = ""
    pending_reset_confirm: bool = False
    text_mode: str = ""
    text_buffer: str = ""

    def __post_init__(self) -> None:
        self.active_profile = active_key_profile()


def _set_status(state: KeybindingsMenuState, ok: bool, message: str) -> None:
    state.status = message
    state.status_error = not ok


def _clear_reset_confirmation(state: KeybindingsMenuState) -> None:
    state.pending_reset_confirm = False


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


def _text_mode_label(mode: str) -> str:
    if mode == _TEXT_MODE_CREATE:
        return "Create profile name"
    if mode == _TEXT_MODE_RENAME:
        return "Rename active profile"
    return "Save profile as"


def _sections_for_scope(scope: str) -> list[tuple[str, int, tuple[str, ...]]]:
    if scope == "general":
        return [
            (_doc_label("system"), 2, ("system",)),
        ]
    if scope == "all":
        return [
            (_doc_label("system"), 2, ("system",)),
            ("2D Gameplay", 2, ("game",)),
            ("3D Gameplay", 3, ("game",)),
            ("3D Camera / View", 3, ("camera",)),
            ("3D Slice", 3, ("slice",)),
            ("4D Gameplay", 4, ("game",)),
            ("4D Camera / View", 4, ("camera",)),
            ("4D Slice", 4, ("slice",)),
        ]

    dimension = int(scope[0])
    groups = runtime_binding_groups_for_dimension(dimension)
    section_list: list[tuple[str, int, tuple[str, ...]]] = []
    for group_name in _GROUP_ORDER:
        if group_name not in groups:
            continue
        section_title = f"{dimension}D {_doc_label(group_name)}"
        section_list.append((section_title, dimension, (group_name,)))
    return section_list


def _rows_for_scope(scope: str) -> tuple[list[_RenderedRow], list[_BindingRow]]:
    rendered: list[_RenderedRow] = []
    binding_rows: list[_BindingRow] = []

    for section_title, dimension, groups in _sections_for_scope(scope):
        rendered.append(_RenderedRow(kind="header", text=section_title))
        for group_name in groups:
            group_bindings = runtime_binding_groups_for_dimension(dimension).get(group_name, {})
            if not group_bindings:
                continue
            rendered.append(
                _RenderedRow(
                    kind="header",
                    text=f"  {_doc_description(group_name)}",
                )
            )
            for action_name in sorted(group_bindings.keys()):
                row = _BindingRow(dimension=dimension, group=group_name, action=action_name)
                binding_rows.append(row)
                rendered.append(_RenderedRow(kind="binding", text=action_name, binding=row))
        rendered.append(_RenderedRow(kind="header", text=""))

    if rendered and rendered[-1].text == "":
        rendered.pop()

    return rendered, binding_rows


def _cycle_binding(state: KeybindingsMenuState, binding_rows: list[_BindingRow], step: int) -> None:
    if not binding_rows:
        return
    state.selected_binding = (state.selected_binding + step) % len(binding_rows)


def _cycle_scope(state: KeybindingsMenuState, step: int) -> None:
    idx = _SCOPE_ORDER.index(state.scope)
    state.scope = _SCOPE_ORDER[(idx + step) % len(_SCOPE_ORDER)]
    state.selected_binding = 0
    state.scroll_top = 0
    state.capture_mode = False


def _cycle_profile(state: KeybindingsMenuState, step: int) -> None:
    ok, msg, profile = cycle_key_profile(step)
    state.active_profile = profile
    _set_status(state, ok, msg)


def _activate_profile(state: KeybindingsMenuState, profile: str) -> tuple[bool, str]:
    ok, msg = set_active_key_profile(profile)
    if not ok:
        return False, msg
    ok, msg = load_active_profile_bindings()
    if not ok:
        return False, msg
    state.active_profile = active_key_profile()
    return True, f"Active key profile: {state.active_profile}"


def _delete_profile(state: KeybindingsMenuState) -> None:
    ok, msg = delete_key_profile(state.active_profile)
    state.active_profile = active_key_profile()
    _set_status(state, ok, msg)


def _start_text_mode(state: KeybindingsMenuState, mode: str) -> None:
    state.text_mode = mode
    if mode == _TEXT_MODE_RENAME:
        state.text_buffer = state.active_profile
    else:
        state.text_buffer = next_auto_profile_name("custom")
    pygame.key.start_text_input()
    _set_status(state, True, f"{_text_mode_label(mode)}: type name and press Enter")


def _stop_text_mode(state: KeybindingsMenuState) -> None:
    state.text_mode = ""
    state.text_buffer = ""
    pygame.key.stop_text_input()


def _commit_text_mode(state: KeybindingsMenuState) -> None:
    profile_name = _sanitize_profile_name(state.text_buffer)
    mode = state.text_mode
    _stop_text_mode(state)

    if not profile_name:
        _set_status(state, False, "Profile name cannot be empty")
        return

    if mode == _TEXT_MODE_RENAME:
        ok, msg = rename_key_profile(state.active_profile, profile_name)
        state.active_profile = active_key_profile()
        _set_status(state, ok, msg)
        return

    ok, msg = clone_key_profile(profile_name, source_profile=state.active_profile)
    if not ok:
        _set_status(state, ok, msg)
        return
    ok, activate_msg = _activate_profile(state, profile_name)
    if ok:
        _set_status(state, True, f"{msg}; {activate_msg}")
    else:
        _set_status(state, False, activate_msg)


def _cancel_text_mode(state: KeybindingsMenuState) -> None:
    _stop_text_mode(state)
    _set_status(state, True, "Profile input cancelled")


def _handle_text_input_event(state: KeybindingsMenuState, text: str) -> None:
    if not state.text_mode:
        return
    appended = "".join(ch for ch in text.lower() if ch in _PROFILE_NAME_CHARS)
    if not appended:
        return
    state.text_buffer = (state.text_buffer + appended)[:64]


def _run_scope_operation(
    state: KeybindingsMenuState,
    operation: Callable[[int], tuple[bool, str]],
) -> tuple[bool, str]:
    results: list[str] = []
    ok_all = True
    for dimension in _scope_dimensions(state.scope):
        ok, msg = operation(dimension)
        ok_all = ok_all and ok
        results.append(f"{dimension}D: {msg}")
    return ok_all, " | ".join(results)


def _active_binding(binding_rows: list[_BindingRow], state: KeybindingsMenuState) -> _BindingRow | None:
    if not binding_rows:
        return None
    safe_index = max(0, min(len(binding_rows) - 1, state.selected_binding))
    return binding_rows[safe_index]


def _handle_capture_input(
    state: KeybindingsMenuState,
    key: int,
    binding_rows: list[_BindingRow],
) -> bool:
    if key == pygame.K_ESCAPE:
        state.capture_mode = False
        _set_status(state, True, "Capture cancelled")
        return False

    selected = _active_binding(binding_rows, state)
    if selected is None:
        state.capture_mode = False
        return False

    if state.scope == "general" and selected.group == "system":
        results: list[str] = []
        ok = True
        for dimension in _scope_dimensions(state.scope):
            dim_ok, dim_msg = rebind_action_key(
                dimension,
                selected.group,
                selected.action,
                key,
                conflict_mode=state.conflict_mode,
            )
            ok = ok and dim_ok
            results.append(f"{dimension}D: {dim_msg}")
        msg = " | ".join(results)
    else:
        ok, msg = rebind_action_key(
            selected.dimension,
            selected.group,
            selected.action,
            key,
            conflict_mode=state.conflict_mode,
        )
    _set_status(state, ok, msg)
    state.capture_mode = False
    return False


def _action_exit(_state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    return True


def _action_row_up(state: KeybindingsMenuState, rows: list[_BindingRow]) -> bool:
    _cycle_binding(state, rows, -1)
    return False


def _action_row_down(state: KeybindingsMenuState, rows: list[_BindingRow]) -> bool:
    _cycle_binding(state, rows, 1)
    return False


def _action_scope_prev(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _cycle_scope(state, -1)
    return False


def _action_scope_next(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _cycle_scope(state, 1)
    return False


def _action_capture_start(state: KeybindingsMenuState, rows: list[_BindingRow]) -> bool:
    if rows:
        state.capture_mode = True
    return False


def _action_conflict_cycle(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    state.conflict_mode = cycle_rebind_conflict_mode(state.conflict_mode, 1)
    _set_status(state, True, f"Conflict mode: {state.conflict_mode}")
    return False


def _action_load_file(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    ok, msg = _run_scope_operation(state, load_keybindings_file)
    _set_status(state, ok, msg)
    return False


def _action_save_file(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    ok, msg = _run_scope_operation(state, save_keybindings_file)
    _set_status(state, ok, msg)
    return False


def _action_reset_bindings(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    if not state.pending_reset_confirm:
        state.pending_reset_confirm = True
        _set_status(state, True, "Press F6 again to confirm profile reset")
        return False
    state.pending_reset_confirm = False
    ok, msg = _run_scope_operation(state, reset_active_profile_bindings)
    _set_status(state, ok, msg)
    return False


def _action_profile_prev(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _cycle_profile(state, -1)
    return False


def _action_profile_next(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _cycle_profile(state, 1)
    return False


def _action_profile_new(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _start_text_mode(state, _TEXT_MODE_CREATE)
    return False


def _action_profile_rename(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _start_text_mode(state, _TEXT_MODE_RENAME)
    return False


def _action_profile_save_as(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _start_text_mode(state, _TEXT_MODE_SAVE_AS)
    return False


def _action_profile_delete(state: KeybindingsMenuState, _rows: list[_BindingRow]) -> bool:
    _delete_profile(state)
    return False


_MENU_KEY_HANDLERS = {
    pygame.K_ESCAPE: _action_exit,
    pygame.K_UP: _action_row_up,
    pygame.K_DOWN: _action_row_down,
    pygame.K_RETURN: _action_capture_start,
    pygame.K_KP_ENTER: _action_capture_start,
    pygame.K_c: _action_conflict_cycle,
    pygame.K_l: _action_load_file,
    pygame.K_s: _action_save_file,
    pygame.K_F6: _action_reset_bindings,
    pygame.K_F2: _action_profile_rename,
    pygame.K_F3: _action_profile_save_as,
    pygame.K_LEFTBRACKET: _action_profile_prev,
    pygame.K_RIGHTBRACKET: _action_profile_next,
    pygame.K_n: _action_profile_new,
    pygame.K_BACKSPACE: _action_profile_delete,
}


def _run_menu_action(state: KeybindingsMenuState, key: int, rows: list[_BindingRow]) -> bool:
    if state.section_mode:
        if state.text_mode:
            if key == pygame.K_ESCAPE:
                _cancel_text_mode(state)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                _commit_text_mode(state)
            elif key == pygame.K_BACKSPACE:
                state.text_buffer = state.text_buffer[:-1]
            return False
        return _handle_section_key(state, key)

    if state.capture_mode:
        _clear_reset_confirmation(state)
        return _handle_capture_input(state, key, rows)

    if state.text_mode:
        if key == pygame.K_ESCAPE:
            _cancel_text_mode(state)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            _commit_text_mode(state)
        elif key == pygame.K_BACKSPACE:
            state.text_buffer = state.text_buffer[:-1]
        return False

    if key == pygame.K_ESCAPE and state.allow_scope_sections:
        state.section_mode = True
        state.capture_mode = False
        _set_status(state, True, "Returned to keybinding sections")
        return False

    if key != pygame.K_F6:
        _clear_reset_confirmation(state)

    handler = _MENU_KEY_HANDLERS.get(key)
    if handler is None:
        return False
    return handler(state, rows)


def _binding_title(row: _BindingRow, scope: str) -> str:
    action_text = row.action.replace("_", " ")
    group_text = binding_group_label(row.group)
    if scope == "all":
        return f"{row.dimension}D {group_text}: {action_text}"
    return f"{group_text}: {action_text}"


def _binding_keys(row: _BindingRow) -> tuple[int, ...]:
    groups = runtime_binding_groups_for_dimension(row.dimension)
    return tuple(groups.get(row.group, {}).get(row.action, ()))


def _scope_file_hint(state: KeybindingsMenuState) -> str:
    if state.scope in {"all", "general"}:
        return "Files: 2d.json + 3d.json + 4d.json"
    dimension = int(state.scope[0])
    return f"File: {keybinding_file_label(dimension)}"


def _draw_menu_header(surface: pygame.Surface, fonts, state: KeybindingsMenuState) -> None:
    width, _ = surface.get_size()
    title = fonts.title_font.render("Keybindings Setup", True, (232, 232, 240))
    subtitle_text = (
        "Up/Down select section, Enter open, Esc back"
        if state.section_mode
        else "Up/Down select, Enter rebind, Esc back"
    )
    subtitle = fonts.hint_font.render(subtitle_text, True, (192, 200, 228))
    surface.blit(title, ((width - title.get_width()) // 2, 28))
    surface.blit(subtitle, ((width - subtitle.get_width()) // 2, 74))

    header = (
        f"Scope: {_scope_label(state.scope)}   "
        f"Profile: {state.active_profile}   "
        f"Conflict: {state.conflict_mode}"
    )
    header_surf = fonts.hint_font.render(header, True, (210, 220, 245))
    surface.blit(header_surf, ((width - header_surf.get_width()) // 2, 106))


def _panel_geometry(surface: pygame.Surface) -> tuple[int, int, int, int]:
    width, height = surface.get_size()
    panel_w = min(width - 40, 1120)
    panel_h = min(height - 260, 580)
    panel_x = (width - panel_w) // 2
    panel_y = 138
    return panel_x, panel_y, panel_w, panel_h


def _draw_panel(surface: pygame.Surface, *, panel_x: int, panel_y: int, panel_w: int, panel_h: int) -> None:
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 152), panel.get_rect(), border_radius=14)
    surface.blit(panel, (panel_x, panel_y))


def _selected_render_index(
    state: KeybindingsMenuState,
    rendered_rows: list[_RenderedRow],
    binding_rows: list[_BindingRow],
) -> int:
    if not binding_rows:
        return 0
    state.selected_binding = max(0, min(len(binding_rows) - 1, state.selected_binding))
    selected_row = binding_rows[state.selected_binding]
    for idx, rendered in enumerate(rendered_rows):
        if rendered.binding == selected_row:
            return idx
    return 0


def _sync_scroll_window(
    state: KeybindingsMenuState,
    *,
    selected_render_index: int,
    total_rows: int,
    visible_rows: int,
) -> None:
    if selected_render_index < state.scroll_top:
        state.scroll_top = selected_render_index
    if selected_render_index >= state.scroll_top + visible_rows:
        state.scroll_top = selected_render_index - visible_rows + 1
    max_top = max(0, total_rows - visible_rows)
    state.scroll_top = max(0, min(max_top, state.scroll_top))


def _draw_row_selection(
    surface: pygame.Surface,
    *,
    panel_x: int,
    panel_w: int,
    y: int,
    line_h: int,
) -> None:
    hi = pygame.Surface((panel_w - 24, line_h + 4), pygame.SRCALPHA)
    pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
    surface.blit(hi, (panel_x + 12, y - 2))


def _draw_binding_row(
    surface: pygame.Surface,
    fonts,
    row: _BindingRow,
    *,
    selected: bool,
    scope: str,
    panel_x: int,
    panel_w: int,
    y: int,
    row_h: int,
) -> None:
    color = (255, 224, 130) if selected else (228, 230, 242)
    if selected:
        _draw_row_selection(surface, panel_x=panel_x, panel_w=panel_w, y=y, line_h=row_h - 4)

    label = _binding_title(row, scope)
    desc = binding_action_description(row.action)
    key_text = _format_key_tuple(_binding_keys(row))

    label_surf = fonts.panel_font.render(label, True, color)
    key_surf = fonts.panel_font.render(key_text, True, color)
    desc_surf = fonts.hint_font.render(desc, True, (168, 182, 215))

    surface.blit(label_surf, (panel_x + 18, y))
    surface.blit(key_surf, (panel_x + panel_w - key_surf.get_width() - 18, y))
    surface.blit(desc_surf, (panel_x + 18, y + fonts.panel_font.get_height() + 1))


def _draw_rows(
    surface: pygame.Surface,
    fonts,
    *,
    state: KeybindingsMenuState,
    rendered_rows: list[_RenderedRow],
    binding_rows: list[_BindingRow],
    panel_x: int,
    panel_y: int,
    panel_w: int,
    panel_h: int,
) -> int:
    row_h = fonts.panel_font.get_height() + fonts.hint_font.get_height() + 12
    visible_rows = max(4, (panel_h - 20) // row_h)
    selected_render_index = _selected_render_index(state, rendered_rows, binding_rows)
    _sync_scroll_window(
        state,
        selected_render_index=selected_render_index,
        total_rows=len(rendered_rows),
        visible_rows=visible_rows,
    )

    draw_rows = rendered_rows[state.scroll_top: state.scroll_top + visible_rows]
    y = panel_y + 12
    selected_binding = _active_binding(binding_rows, state)
    for row in draw_rows:
        if row.kind == "header":
            header_color = (170, 186, 224) if row.text else (132, 142, 172)
            surf = fonts.hint_font.render(row.text, True, header_color)
            header_y = y + (row_h - surf.get_height()) // 2
            surface.blit(surf, (panel_x + 16, header_y))
            y += row_h
            continue
        if row.binding is None:
            y += row_h
            continue
        _draw_binding_row(
            surface,
            fonts,
            row.binding,
            selected=(row.binding == selected_binding),
            scope=state.scope,
            panel_x=panel_x,
            panel_w=panel_w,
            y=y,
            row_h=row_h,
        )
        y += row_h
    return y


def _draw_hints(surface: pygame.Surface, fonts, state: KeybindingsMenuState, panel_y: int, panel_h: int) -> int:
    width, _ = surface.get_size()
    hints = [
        "L load   S save   F3 save as   F2 rename   F6 reset (confirm)",
        "[ / ] profile prev/next   N new profile   Backspace delete custom profile",
        "C conflict mode cycle   Enter capture   Esc cancel/back",
        _scope_file_hint(state),
    ]
    hint_y = panel_y + panel_h + 12
    for line in hints:
        surf = fonts.hint_font.render(line, True, (188, 197, 228))
        surface.blit(surf, ((width - surf.get_width()) // 2, hint_y))
        hint_y += surf.get_height() + 3
    return hint_y


def _draw_capture_hint(
    surface: pygame.Surface,
    fonts,
    state: KeybindingsMenuState,
    binding_rows: list[_BindingRow],
    hint_y: int,
) -> int:
    if not state.capture_mode or not binding_rows:
        return hint_y
    width, _ = surface.get_size()
    selected = binding_rows[state.selected_binding]
    cap = fonts.hint_font.render(
        f"Press a key for {_binding_title(selected, state.scope)} (Esc cancels)",
        True,
        (255, 226, 144),
    )
    surface.blit(cap, ((width - cap.get_width()) // 2, hint_y + 2))
    return hint_y + cap.get_height() + 4


def _draw_text_mode_hint(surface: pygame.Surface, fonts, state: KeybindingsMenuState, hint_y: int) -> int:
    if not state.text_mode:
        return hint_y
    width, _ = surface.get_size()
    prompt = f"{_text_mode_label(state.text_mode)}: {state.text_buffer}_"
    cap = fonts.hint_font.render(prompt, True, (255, 226, 144))
    surface.blit(cap, ((width - cap.get_width()) // 2, hint_y + 2))
    hint_y += cap.get_height() + 4
    tip = fonts.hint_font.render("Enter confirm   Esc cancel", True, (188, 197, 228))
    surface.blit(tip, ((width - tip.get_width()) // 2, hint_y + 2))
    return hint_y + tip.get_height() + 4


def _draw_status(surface: pygame.Surface, fonts, state: KeybindingsMenuState, hint_y: int) -> None:
    if not state.status:
        return
    width, _ = surface.get_size()
    color = (255, 150, 150) if state.status_error else (170, 240, 170)
    status = fonts.hint_font.render(state.status, True, color)
    surface.blit(status, ((width - status.get_width()) // 2, hint_y + 2))


def _draw_section_menu(surface: pygame.Surface, fonts, state: KeybindingsMenuState) -> None:
    _draw_background(surface)
    _draw_menu_header(surface, fonts, state)
    panel_x, panel_y, panel_w, panel_h = _panel_geometry(surface)
    _draw_panel(surface, panel_x=panel_x, panel_y=panel_y, panel_w=panel_w, panel_h=panel_h)

    y = panel_y + 20
    for idx, (_scope, title, description) in enumerate(_SECTION_MENU):
        selected = idx == state.selected_section
        color = (255, 224, 130) if selected else (228, 230, 242)
        if selected:
            hi = pygame.Surface((panel_w - 24, fonts.panel_font.get_height() + fonts.hint_font.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            surface.blit(hi, (panel_x + 12, y - 3))

        title_surf = fonts.panel_font.render(title, True, color)
        desc_surf = fonts.hint_font.render(description, True, (168, 182, 215))
        surface.blit(title_surf, (panel_x + 18, y))
        surface.blit(desc_surf, (panel_x + 18, y + fonts.panel_font.get_height() + 1))
        y += fonts.panel_font.get_height() + fonts.hint_font.get_height() + 14

    width, _ = surface.get_size()
    hints = (
        "Enter open section   Up/Down select section   Esc back",
        "[ / ] profile prev/next   N new profile   F2 rename   F3 save as",
    )
    hy = panel_y + panel_h + 12
    for line in hints:
        surf = fonts.hint_font.render(line, True, (188, 197, 228))
        surface.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3
    hy = _draw_text_mode_hint(surface, fonts, state, hy)
    if state.status:
        _draw_status(surface, fonts, state, hy)


def _handle_section_key(state: KeybindingsMenuState, key: int) -> bool:
    if key == pygame.K_ESCAPE:
        return True
    if key == pygame.K_UP:
        state.selected_section = (state.selected_section - 1) % len(_SECTION_MENU)
        return False
    if key == pygame.K_DOWN:
        state.selected_section = (state.selected_section + 1) % len(_SECTION_MENU)
        return False
    if key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
        step = -1 if key == pygame.K_LEFTBRACKET else 1
        _cycle_profile(state, step)
        return False
    if key == pygame.K_n:
        _start_text_mode(state, _TEXT_MODE_CREATE)
        return False
    if key == pygame.K_F2:
        _start_text_mode(state, _TEXT_MODE_RENAME)
        return False
    if key == pygame.K_F3:
        _start_text_mode(state, _TEXT_MODE_SAVE_AS)
        return False
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        scope = _SECTION_MENU[state.selected_section][0]
        state.scope = scope
        state.section_mode = False
        state.selected_binding = 0
        state.scroll_top = 0
        state.capture_mode = False
        _set_status(state, True, f"Opened {_scope_label(scope)} bindings")
    return False


def _draw_menu(
    surface: pygame.Surface,
    fonts,
    state: KeybindingsMenuState,
    rendered_rows: list[_RenderedRow],
    binding_rows: list[_BindingRow],
) -> None:
    _draw_background(surface)
    _draw_menu_header(surface, fonts, state)
    panel_x, panel_y, panel_w, panel_h = _panel_geometry(surface)
    _draw_panel(surface, panel_x=panel_x, panel_y=panel_y, panel_w=panel_w, panel_h=panel_h)
    _draw_rows(
        surface,
        fonts,
        state=state,
        rendered_rows=rendered_rows,
        binding_rows=binding_rows,
        panel_x=panel_x,
        panel_y=panel_y,
        panel_w=panel_w,
        panel_h=panel_h,
    )
    hint_y = _draw_hints(surface, fonts, state, panel_y, panel_h)
    hint_y = _draw_capture_hint(surface, fonts, state, binding_rows, hint_y)
    hint_y = _draw_text_mode_hint(surface, fonts, state, hint_y)
    _draw_status(surface, fonts, state, hint_y)


def run_keybindings_menu(
    screen: pygame.Surface,
    fonts,
    dimension: int = 2,
    *,
    scope: str | None = None,
) -> None:
    initial_scope = scope.strip().lower() if isinstance(scope, str) else ""
    if initial_scope not in _VALID_SCOPES:
        initial_scope = _scope_from_dimension(dimension)
    allow_scope_sections = initial_scope in {"all", "general"}
    selected_section = 0
    for idx, (section_scope, _title, _description) in enumerate(_SECTION_MENU):
        if section_scope == initial_scope:
            selected_section = idx
            break
    state = KeybindingsMenuState(
        scope=initial_scope,
        section_mode=allow_scope_sections,
        allow_scope_sections=allow_scope_sections,
        selected_section=selected_section,
    )

    clock = pygame.time.Clock()
    running = True
    while running:
        _dt = clock.tick(60)
        rendered_rows, binding_rows = _rows_for_scope(state.scope)
        if binding_rows:
            state.selected_binding = max(0, min(len(binding_rows) - 1, state.selected_binding))
        else:
            state.selected_binding = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.key.stop_text_input()
                return
            if event.type == pygame.TEXTINPUT and state.text_mode:
                _handle_text_input_event(state, event.text)
                continue
            if event.type != pygame.KEYDOWN:
                continue
            should_exit = _run_menu_action(state, event.key, binding_rows)
            if should_exit:
                running = False
                break

        if state.section_mode:
            _draw_section_menu(screen, fonts, state)
        else:
            _draw_menu(screen, fonts, state, rendered_rows, binding_rows)
        pygame.display.flip()

    pygame.key.stop_text_input()
