from __future__ import annotations

from dataclasses import dataclass

from .keybindings import (
    binding_group_description,
    binding_group_label,
    keybinding_file_label,
    runtime_binding_groups_for_dimension,
)
from .menu_config import keybinding_category_docs


CATEGORY_DOCS = keybinding_category_docs()
SCOPE_ORDER = tuple(CATEGORY_DOCS.get("scope_order", ("all", "2d", "3d", "4d")))
VALID_SCOPES = tuple(dict.fromkeys((*SCOPE_ORDER, "general", "all")))
GROUP_ORDER = ("game", "camera", "slice", "system")
SECTION_MENU: tuple[tuple[str, str, str], ...] = (
    ("general", "General Keybindings", "System actions shared across 2D/3D/4D."),
    ("2d", "2D Keybindings", "2D gameplay and shared system controls."),
    ("3d", "3D Keybindings", "3D gameplay, camera/view, slice, and system controls."),
    ("4d", "4D Keybindings", "4D gameplay, camera/view, slice, and system controls."),
)


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


def scope_label(scope: str) -> str:
    if scope == "general":
        return "GENERAL"
    return "ALL" if scope == "all" else scope.upper()


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


def _doc_label(group: str) -> str:
    groups = CATEGORY_DOCS.get("groups", {})
    if isinstance(groups, dict):
        raw = groups.get(group)
        if isinstance(raw, dict):
            label = raw.get("label")
            if isinstance(label, str) and label.strip():
                return label.strip()
    return binding_group_label(group)


def _doc_description(group: str) -> str:
    groups = CATEGORY_DOCS.get("groups", {})
    if isinstance(groups, dict):
        raw = groups.get(group)
        if isinstance(raw, dict):
            desc = raw.get("description")
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
    return binding_group_description(group)


def sections_for_scope(scope: str) -> list[tuple[str, int, tuple[str, ...]]]:
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
    for group_name in GROUP_ORDER:
        if group_name not in groups:
            continue
        section_title = f"{dimension}D {_doc_label(group_name)}"
        section_list.append((section_title, dimension, (group_name,)))
    return section_list


def rows_for_scope(scope: str) -> tuple[list[RenderedRow], list[BindingRow]]:
    rendered: list[RenderedRow] = []
    binding_rows: list[BindingRow] = []

    for section_title, dimension, groups in sections_for_scope(scope):
        rendered.append(RenderedRow(kind="header", text=section_title))
        for group_name in groups:
            group_bindings = runtime_binding_groups_for_dimension(dimension).get(group_name, {})
            if not group_bindings:
                continue
            rendered.append(
                RenderedRow(
                    kind="header",
                    text=f"  {_doc_description(group_name)}",
                )
            )
            for action_name in sorted(group_bindings.keys()):
                row = BindingRow(dimension=dimension, group=group_name, action=action_name)
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
        return f"{row.dimension}D {group_text}: {action_text}"
    return f"{group_text}: {action_text}"


def binding_keys(row: BindingRow) -> tuple[int, ...]:
    groups = runtime_binding_groups_for_dimension(row.dimension)
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
