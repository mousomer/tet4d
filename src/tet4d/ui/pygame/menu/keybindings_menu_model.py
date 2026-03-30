from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.ui_logic.keybindings_catalog import (
    binding_group_description,
    binding_group_label,
    binding_scope_menu_sections,
    binding_scope_order,
    gameplay_bucket_label,
    partition_gameplay_actions,
)
from tet4d.engine.runtime.api import runtime_binding_groups_for_dimension_runtime
from tet4d.ui.pygame.keybindings import (
    keybinding_file_label,
)

SCOPE_ORDER = binding_scope_order()
VALID_SCOPES = tuple(dict.fromkeys((*SCOPE_ORDER, "general", "all")))
_SECTION_COPY = binding_scope_menu_sections()
SECTION_MENU: tuple[tuple[str, str, str], ...] = tuple(
    (scope, _SECTION_COPY[scope]["title"], _SECTION_COPY[scope]["description"])
    for scope in SCOPE_ORDER
    if scope in _SECTION_COPY
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


@dataclass(frozen=True)
class _SectionSpec:
    title: str
    dimension: int
    group: str
    action_bucket: str = "all"


_BUCKET_TRANSLATION = "translation"
_BUCKET_ROTATION = "rotation"
_BUCKET_OTHER = "other"
_BUCKET_ALL = "all"


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
    return binding_group_label(group)


def _doc_description(group: str) -> str:
    return binding_group_description(group)


def _bucket_actions(
    action_names: tuple[str, ...],
    *,
    bucket: str,
) -> tuple[str, ...]:
    if bucket == _BUCKET_ALL:
        return tuple(sorted(action_names))
    translation, rotation, other = (
        partition_gameplay_actions(action_names)
    )
    if bucket == _BUCKET_TRANSLATION:
        return translation
    if bucket == _BUCKET_ROTATION:
        return rotation
    if bucket == _BUCKET_OTHER:
        return other
    return tuple(sorted(action_names))


def _gameplay_sections_for_dimension(dimension: int) -> list[_SectionSpec]:
    groups = runtime_binding_groups_for_dimension_runtime(dimension)
    game_actions = tuple(groups.get("game", {}).keys())
    sections: list[_SectionSpec] = []
    for bucket in (_BUCKET_TRANSLATION, _BUCKET_ROTATION, _BUCKET_OTHER):
        if not _bucket_actions(game_actions, bucket=bucket):
            continue
        sections.append(
            _SectionSpec(
                title=f"{dimension}D {gameplay_bucket_label(bucket)}",
                dimension=dimension,
                group="game",
                action_bucket=bucket,
            )
        )
    return sections


def _sections_for_dimension(*, dimension: int) -> list[_SectionSpec]:
    groups = runtime_binding_groups_for_dimension_runtime(dimension)
    prefix = f"{dimension}D "
    sections: list[_SectionSpec] = []
    if groups.get("game"):
        sections.extend(_gameplay_sections_for_dimension(dimension))
    if groups.get("explorer"):
        sections.append(
            _SectionSpec(
                title=f"{prefix}{_doc_label('explorer')}",
                dimension=dimension,
                group="explorer",
            )
        )
    if groups.get("camera"):
        sections.append(
            _SectionSpec(
                title=f"{prefix}{_doc_label('camera')}",
                dimension=dimension,
                group="camera",
            )
        )
    return sections


def sections_for_scope(scope: str) -> list[_SectionSpec]:
    if scope == "general":
        return [
            _SectionSpec(
                title=_doc_label("system"),
                dimension=2,
                group="system",
            ),
        ]
    if scope == "all":
        sections: list[_SectionSpec] = [
            _SectionSpec(
                title=f"{_doc_label('system')} (shared)",
                dimension=2,
                group="system",
            )
        ]
        for dimension in (2, 3, 4):
            sections.extend(_sections_for_dimension(dimension=dimension))
        return sections
    dimension = int(scope[0])
    return _sections_for_dimension(dimension=dimension)


def rows_for_scope(scope: str) -> tuple[list[RenderedRow], list[BindingRow]]:
    rendered: list[RenderedRow] = []
    binding_rows: list[BindingRow] = []

    for section in sections_for_scope(scope):
        rendered.append(RenderedRow(kind="header", text=section.title))
        group_bindings = runtime_binding_groups_for_dimension_runtime(section.dimension).get(
            section.group, {}
        )
        if not group_bindings:
            rendered.append(RenderedRow(kind="header", text=""))
            continue
        if section.group == "game":
            rendered.append(
                RenderedRow(
                    kind="header",
                    text=f"  {_doc_description('game')}",
                )
            )
        else:
            rendered.append(
                RenderedRow(
                    kind="header",
                    text=f"  {_doc_description(section.group)}",
                )
            )
        action_names = _bucket_actions(
            tuple(group_bindings.keys()), bucket=section.action_bucket
        )
        for action_name in action_names:
            row = BindingRow(
                dimension=section.dimension, group=section.group, action=action_name
            )
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
