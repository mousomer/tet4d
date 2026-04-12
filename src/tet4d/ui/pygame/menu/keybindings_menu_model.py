from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.runtime.menu_config import keybindings_menu_id
from tet4d.engine.runtime.menu_config import menu_items as configured_menu_items
from tet4d.engine.ui_logic.keybindings_catalog import (
    binding_group_description,
    binding_group_label,
    gameplay_bucket_label,
    partition_gameplay_actions,
)
from tet4d.engine.runtime.api import runtime_binding_groups_for_dimension_runtime
from tet4d.ui.pygame.keybindings import keybinding_file_label


SCOPE_ORDER = ("general", "2d", "3d", "4d", "all")
VALID_SCOPES = tuple(dict.fromkeys((*SCOPE_ORDER, "general", "all")))


@dataclass(frozen=True)
class BindingRow:
    dimension: int
    group: str
    action: str


@dataclass(frozen=True)
class RenderedRow:
    kind: str  # header|binding
    text: str
    binding: BindingRow | None = None


def _scope_from_menu_id(menu_id: str) -> str:
    clean_menu_id = str(menu_id).strip().lower()
    prefix = "keybindings_scope_"
    if clean_menu_id.startswith(prefix):
        return clean_menu_id[len(prefix) :]
    return clean_menu_id


def _root_scope_items() -> tuple[dict[str, str], ...]:
    return tuple(
        item
        for item in configured_menu_items(keybindings_menu_id())
        if str(item.get("type", "")).lower() == "submenu"
    )


SECTION_MENU: tuple[tuple[str, str, str], ...] = tuple(
    (
        _scope_from_menu_id(str(item.get("menu_id", ""))),
        str(item.get("label", "")),
        str(item.get("description", "")),
    )
    for item in _root_scope_items()
)


def scope_label(scope: str) -> str:
    clean_scope = str(scope).strip().lower()
    for section_scope, label, _description in SECTION_MENU:
        if section_scope == clean_scope:
            return label.upper()
    return clean_scope.upper()


def scope_dimensions(scope: str) -> tuple[int, ...]:
    if scope in {"all", "general"}:
        return (2, 3, 4)
    return (int(scope[0]),)


def scope_from_dimension(dimension: int) -> str:
    if dimension <= 2:
        return "2d"
    if dimension == 3:
        return "3d"
    return "4d"


def _bucket_actions(action_names: tuple[str, ...], *, bucket: str) -> tuple[str, ...]:
    if bucket == "all":
        return tuple(sorted(action_names))
    translation, rotation, other = partition_gameplay_actions(action_names)
    if bucket == "translation":
        return translation
    if bucket == "rotation":
        return rotation
    if bucket == "other":
        return other
    return tuple(sorted(action_names))


def _menu_id_for_scope(scope: str) -> str:
    clean_scope = str(scope).strip().lower()
    for section_scope, _label, _description in SECTION_MENU:
        if section_scope == clean_scope:
            return f"keybindings_scope_{clean_scope}"
    raise KeyError(f"Unknown keybindings scope: {scope}")


def rows_for_scope(scope: str) -> tuple[list[RenderedRow], list[BindingRow]]:
    menu_id = _menu_id_for_scope(scope)
    rendered: list[RenderedRow] = []
    binding_rows: list[BindingRow] = []
    for item in configured_menu_items(menu_id):
        if str(item.get("type", "")).lower() != "keybinding_group":
            continue
        title = str(item.get("label", ""))
        description = str(item.get("description", "")).strip()
        rendered.append(RenderedRow(kind="header", text=title))
        rendered.append(RenderedRow(kind="header", text=f"  {description}" if description else ""))

        dimension = int(str(item.get("binding_dimension", "2"))[0])
        group = str(item.get("binding_group", "")).strip().lower()
        bucket = str(item.get("binding_bucket", "all")).strip().lower()
        group_bindings = runtime_binding_groups_for_dimension_runtime(dimension).get(
            group,
            {},
        )
        action_names = _bucket_actions(tuple(group_bindings.keys()), bucket=bucket)
        for action_name in action_names:
            row = BindingRow(dimension=dimension, group=group, action=action_name)
            binding_rows.append(row)
            rendered.append(RenderedRow(kind="binding", text=action_name, binding=row))
        rendered.append(RenderedRow(kind="header", text=""))

    if rendered and rendered[-1].text == "":
        rendered.pop()
    return rendered, binding_rows


def binding_title(row: BindingRow, scope: str) -> str:
    action_text = row.action.replace("_", " ")
    group_text = binding_group_label(row.group)
    if scope == "all":
        if row.group == "game":
            action_bucket = ""
            translation, rotation, other = partition_gameplay_actions((row.action,))
            if translation:
                action_bucket = gameplay_bucket_label("translation")
            elif rotation:
                action_bucket = gameplay_bucket_label("rotation")
            elif other:
                action_bucket = gameplay_bucket_label("other")
            if action_bucket:
                return f"{row.dimension}D {action_bucket}: {action_text}"
        return f"{row.dimension}D {group_text}: {action_text}"
    return f"{group_text}: {action_text}"


def binding_keys(row: BindingRow) -> tuple[int, ...]:
    groups = runtime_binding_groups_for_dimension_runtime(row.dimension)
    return tuple(groups.get(row.group, {}).get(row.action, ()))


def scope_file_hint(scope: str) -> str:
    if scope in {"all", "general"}:
        return "Files: 2d.json + 3d.json + 4d.json"
    dimension = int(scope[0])
    return f"File: {keybinding_file_label(dimension)}"


def resolve_initial_scope(dimension: int, scope: str | None) -> str:
    initial_scope = scope.strip().lower() if isinstance(scope, str) else ""
    if initial_scope not in VALID_SCOPES:
        initial_scope = scope_from_dimension(dimension)
    return initial_scope


def scope_description(scope: str) -> str:
    clean_scope = str(scope).strip().lower()
    for section_scope, _label, description in SECTION_MENU:
        if section_scope == clean_scope:
            return description
    return binding_group_description("system")
