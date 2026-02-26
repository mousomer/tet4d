from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pygame

from tet4d.ui.pygame.control_helper import (
    control_groups_for_dimension,
    draw_grouped_control_helper,
)
from .runtime.help_topics import help_action_topic_registry, help_topics_for_context
from tet4d.ui.pygame.key_display import format_key_tuple
from .keybindings import (
    active_key_profile,
    binding_action_description,
    binding_group_label,
    runtime_binding_groups_for_dimension,
)
from .ui_logic.keybindings_catalog import gameplay_action_category
from .runtime.menu_config import settings_category_docs
from .ui_logic.menu_layout import LayoutRect, compute_menu_layout_zones
from .gameplay.pieces2d import PIECE_SET_2D_OPTIONS, piece_set_2d_label
from .gameplay.pieces_nd import piece_set_label, piece_set_options_for_dimension
from .runtime.project_config import project_constant_int
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text


_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_MUTED_COLOR = (192, 200, 228)
_HIGHLIGHT = (255, 224, 128)
_RUNTIME_GROUP_ORDER = ("system", "game", "camera")
_LIVE_KEY_GROUP_ORDER = (
    "system",
    "game_translation",
    "game_rotation",
    "game_other",
    "camera",
)
_CONTROL_TOPIC_ID = "movement_rotation"
_KEY_REFERENCE_TOPIC_ID = "key_reference"
_SETTINGS_DOCS = settings_category_docs()

_HELP_OUTER_PAD = project_constant_int(
    ("layout", "help", "outer_pad"), 20, min_value=4, max_value=96
)
_HELP_HEADER_EXTRA = project_constant_int(
    ("layout", "help", "header_extra"), 16, min_value=4, max_value=120
)
_HELP_GAP = project_constant_int(
    ("layout", "help", "gap"), 8, min_value=1, max_value=40
)
_HELP_FOOTER_HEIGHT = project_constant_int(
    ("layout", "help", "footer_height"), 24, min_value=12, max_value=80
)
_HELP_MIN_CONTENT_HEIGHT = project_constant_int(
    ("layout", "help", "min_content_height"),
    160,
    min_value=60,
    max_value=1000,
)
_HELP_CONTENT_PAD_X = project_constant_int(
    ("layout", "help", "content_pad_x"), 12, min_value=0, max_value=80
)
_HELP_CONTENT_PAD_Y = project_constant_int(
    ("layout", "help", "content_pad_y"), 8, min_value=0, max_value=80
)
_HELP_COMPACT_WIDTH = project_constant_int(
    ("layout", "help", "compact_width_threshold"),
    760,
    min_value=300,
    max_value=2000,
)
_HELP_COMPACT_HEIGHT = project_constant_int(
    ("layout", "help", "compact_height_threshold"),
    460,
    min_value=220,
    max_value=1600,
)


@dataclass
class _HelpState:
    page: int = 0
    subpage: int = 0
    dimension: int = 2
    running: bool = True


def paginate_help_lines(
    lines: Sequence[str], rows_per_page: int
) -> tuple[tuple[str, ...], ...]:
    if rows_per_page <= 0:
        rows_per_page = 1
    if not lines:
        return (tuple(),)
    pages: list[tuple[str, ...]] = []
    for start in range(0, len(lines), rows_per_page):
        pages.append(tuple(lines[start : start + rows_per_page]))
    return tuple(pages)


def _current_binding_text(dimension: int, action: str, *, group: str = "system") -> str:
    groups = runtime_binding_groups_for_dimension(max(2, min(4, int(dimension))))
    keys = tuple(groups.get(group, {}).get(action, ()))
    return format_key_tuple(keys)


def _draw_gradient(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, _BG_TOP, _BG_BOTTOM)


def _as_rect(spec: LayoutRect) -> pygame.Rect:
    return pygame.Rect(spec.x, spec.y, spec.width, spec.height)


def is_compact_help_view(*, width: int, height: int) -> bool:
    return int(width) <= _HELP_COMPACT_WIDTH or int(height) <= _HELP_COMPACT_HEIGHT


def _help_layout_zones(
    surface: pygame.Surface, fonts
) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect]:
    width, height = surface.get_size()
    compact = is_compact_help_view(width=width, height=height)
    header_extra = max(8, _HELP_HEADER_EXTRA // 2) if compact else _HELP_HEADER_EXTRA
    footer_height = max(16, _HELP_FOOTER_HEIGHT - 6) if compact else _HELP_FOOTER_HEIGHT
    gap = max(4, _HELP_GAP - 3) if compact else _HELP_GAP
    min_content_height = (
        max(90, _HELP_MIN_CONTENT_HEIGHT // 2) if compact else _HELP_MIN_CONTENT_HEIGHT
    )
    header_height = (
        fonts.title_font.get_height() + fonts.hint_font.get_height() + header_extra
    )
    zones = compute_menu_layout_zones(
        width=width,
        height=height,
        outer_pad=_HELP_OUTER_PAD,
        header_height=header_height,
        footer_height=footer_height,
        gap=gap,
        min_content_height=min_content_height,
    )
    return (
        _as_rect(zones.frame),
        _as_rect(zones.header),
        _as_rect(zones.content),
        _as_rect(zones.footer),
    )


def _draw_content_title(
    surface: pygame.Surface,
    *,
    font: pygame.font.Font,
    text: str,
    rect: pygame.Rect,
) -> int:
    draw_text = fit_text(font, text, max(40, rect.width - (_HELP_CONTENT_PAD_X * 2)))
    title = font.render(draw_text, True, _HIGHLIGHT)
    x = rect.x + max(0, (rect.width - title.get_width()) // 2)
    y = rect.y + _HELP_CONTENT_PAD_Y
    surface.blit(title, (x, y))
    return y + title.get_height() + 8


def _line_capacity(
    font: pygame.font.Font, *, content_rect: pygame.Rect, y_start: int
) -> int:
    available_h = max(1, content_rect.bottom - _HELP_CONTENT_PAD_Y - y_start)
    row_h = max(1, font.get_height() + 4)
    return max(1, available_h // row_h)


def _draw_lines(
    surface: pygame.Surface,
    font: pygame.font.Font,
    lines: Sequence[str],
    *,
    rect: pygame.Rect,
    y_start: int,
    line_gap: int = 4,
) -> None:
    x = rect.x + _HELP_CONTENT_PAD_X
    y = max(rect.y, y_start)
    max_width = max(40, rect.width - (_HELP_CONTENT_PAD_X * 2))
    for line in lines:
        color = _TEXT_COLOR
        text = line
        if not line:
            y += max(4, font.get_height() // 3)
            continue
        if line.startswith("## "):
            color = _HIGHLIGHT
            text = line[3:]
        elif line.startswith("-- "):
            color = _MUTED_COLOR
            text = line[3:]
        draw_text = fit_text(font, text, max_width)
        surf = font.render(draw_text, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + line_gap


def _fallback_topic() -> dict[str, Any]:
    return {
        "id": "overview",
        "title": "Help Overview",
        "summary": "No context-specific help topics were found.",
        "sections": (
            {
                "id": "fallback",
                "title": "What",
                "lines": (
                    "Use Left/Right to switch topics.",
                    "Use Up/Down to switch dimensions.",
                ),
            },
        ),
    }


def _topics_for_state(
    state: _HelpState, context_label: str
) -> tuple[dict[str, Any], ...]:
    topics = help_topics_for_context(
        dimension=state.dimension, context_label=context_label
    )
    if topics:
        return topics
    return (_fallback_topic(),)


def _current_topic(
    state: _HelpState, context_label: str
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    topics = _topics_for_state(state, context_label)
    state.page = max(0, min(len(topics) - 1, state.page))
    return topics[state.page], topics


def _cycle_page(state: _HelpState, context_label: str, step: int) -> None:
    topics = _topics_for_state(state, context_label)
    state.page = (state.page + step) % len(topics)
    state.subpage = 0


def _cycle_dimension(state: _HelpState, context_label: str, step: int) -> None:
    current_topic, _ = _current_topic(state, context_label)
    current_topic_id = str(current_topic.get("id", ""))
    if step < 0:
        state.dimension = 4 if state.dimension == 2 else state.dimension - 1
    else:
        state.dimension = 2 if state.dimension == 4 else state.dimension + 1

    next_topics = _topics_for_state(state, context_label)
    next_ids = [str(topic.get("id", "")) for topic in next_topics]
    state.page = next_ids.index(current_topic_id) if current_topic_id in next_ids else 0
    state.subpage = 0


def _topic_section_lines(topic: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    summary = str(topic.get("summary", "")).strip()
    if summary:
        lines.append(f"-- {summary}")

    for section in topic.get("sections", ()):  # type: ignore[assignment]
        if not isinstance(section, dict):
            continue
        section_title = str(section.get("title", "")).strip()
        if section_title:
            lines.append("")
            lines.append(f"## {section_title}")
        for raw_line in section.get("lines", ()):  # type: ignore[assignment]
            line = str(raw_line).strip()
            if not line:
                continue
            lines.append(f"- {line}")
    return lines


def help_topic_action_rows(
    *,
    topic_id: str,
    dimension: int,
    include_all: bool,
) -> tuple[tuple[str, str, str], ...]:
    groups = runtime_binding_groups_for_dimension(dimension)
    action_registry = help_action_topic_registry()
    default_topic = str(action_registry["default_topic"])
    action_topics = action_registry["action_topics"]
    rows: list[tuple[str, str, str]] = []

    for group in _RUNTIME_GROUP_ORDER:
        actions = groups.get(group, {})
        if not actions:
            continue
        for action_name in sorted(actions.keys()):
            mapped_topic = action_topics.get(action_name, default_topic)
            if include_all or mapped_topic == topic_id:
                keys = format_key_tuple(tuple(actions[action_name]))
                key_text = keys if keys else "(unbound)"
                rows.append((group, action_name, key_text))
    return tuple(rows)


def _topic_action_lines(
    *,
    topic_id: str,
    dimension: int,
    include_all: bool,
) -> list[str]:
    rows = help_topic_action_rows(
        topic_id=topic_id,
        dimension=dimension,
        include_all=include_all,
    )
    lines: list[str] = []
    grouped: dict[str, list[tuple[str, str]]] = {
        group: [] for group in _LIVE_KEY_GROUP_ORDER
    }
    for group, action_name, key_text in rows:
        target_group = group
        if group == "game":
            target_group = f"game_{gameplay_action_category(action_name)}"
        grouped.setdefault(target_group, []).append((action_name, key_text))

    for group in _LIVE_KEY_GROUP_ORDER:
        action_rows = grouped.get(group, [])
        if not action_rows:
            continue
        if group == "game_translation":
            heading = "Gameplay / Translation"
        elif group == "game_rotation":
            heading = "Gameplay / Rotation"
        elif group == "game_other":
            heading = "Gameplay / Other"
        else:
            heading = binding_group_label(group)
        lines.append(f"-- {heading}")
        for action_name, key_text in action_rows:
            desc = binding_action_description(action_name)
            lines.append(f"{key_text}: {desc}")
    return lines


def help_topic_action_lines(
    *,
    topic_id: str,
    dimension: int,
    include_all: bool = False,
) -> tuple[str, ...]:
    return tuple(
        _topic_action_lines(
            topic_id=topic_id,
            dimension=max(2, min(4, int(dimension))),
            include_all=include_all,
        )
    )


def _extend_overview_lines(
    lines: list[str],
    *,
    state: _HelpState,
    context_label: str,
    topics: Sequence[dict[str, Any]],
    compact: bool,
) -> None:
    lines.extend(
        [
            "",
            f"## Context: {context_label}",
            f"- Active profile: {active_key_profile()}",
            f"- Help key: {_current_binding_text(state.dimension, 'help')}",
            "- Left/Right switches topic. Up/Down switches dimension.",
            "- [ or ] (also PgUp/PgDn) switches subpage when needed.",
            "",
            "## Topics in this context",
        ]
    )
    max_topics = 5 if compact else len(topics)
    for idx, topic in enumerate(topics[:max_topics], start=1):
        title = str(topic.get("title", "Topic"))
        lines.append(f"- {idx}. {title}")
    if compact and len(topics) > max_topics:
        lines.append(f"- ... and {len(topics) - max_topics} more topics")


def _extend_game_types_lines(lines: list[str], *, compact: bool) -> None:
    if compact:
        lines.extend(
            [
                "",
                "## Piece sets",
                "- Use Full Key Map topic for complete live key coverage.",
            ]
        )
        return
    piece_sets_2d = ", ".join(
        piece_set_2d_label(piece_set_id) for piece_set_id in PIECE_SET_2D_OPTIONS
    )
    piece_sets_3d = ", ".join(
        piece_set_label(piece_set_id)
        for piece_set_id in piece_set_options_for_dimension(3)
    )
    piece_sets_4d = ", ".join(
        piece_set_label(piece_set_id)
        for piece_set_id in piece_set_options_for_dimension(4)
    )
    lines.extend(
        [
            "",
            "## Piece sets",
            f"- 2D: {piece_sets_2d}",
            f"- 3D: {piece_sets_3d}",
            f"- 4D: {piece_sets_4d}",
        ]
    )


def _extend_features_lines(lines: list[str], *, compact: bool) -> None:
    if compact:
        lines.extend(
            [
                "",
                "## Practical notes",
                "- Challenge mode pre-fills lower layers.",
                "- Exploration mode disables gravity/lock/clear.",
            ]
        )
        return
    lines.extend(
        [
            "",
            "## Practical notes",
            "- Challenge mode prefills lower layers to raise early-game pressure.",
            "- Exploration mode disables gravity/locking/clears for practice.",
            "- Dry-run checks whether a selected setup can clear layers.",
        ]
    )


def _extend_settings_lines(lines: list[str], *, compact: bool) -> None:
    lines.extend(
        [
            "",
            "## Settings categories",
        ]
    )
    docs = _SETTINGS_DOCS[:3] if compact else _SETTINGS_DOCS
    for entry in docs:
        lines.append(f"- {entry['label']}: {entry['description']}")
    if compact and len(_SETTINGS_DOCS) > len(docs):
        lines.append("- Open full-size window to view all category descriptions.")


def _extend_camera_view_lines(lines: list[str], *, compact: bool) -> None:
    lines.extend(
        [
            "",
            "## Grid modes",
            "- OFF: board shadow only.",
            "- EDGE: only outer board edges.",
            "- FULL: full lattice grid.",
            "- HELPER: only lines intersecting active piece cells.",
        ]
    )
    if compact:
        return
    lines.extend(
        [
            "",
            "## 4D view note",
            "- 4D is shown as multiple 3D boards (one per W layer).",
        ]
    )


def _extend_workflow_lines(lines: list[str], *, compact: bool) -> None:
    lines.extend(
        [
            "",
            "## Launcher sections",
            "- Play 2D / Play 3D / Play 4D / Help / Settings / Keybindings / Bot Options / Quit",
        ]
    )
    if compact:
        lines.append("- Pause menu keeps Help/Settings/Keybindings/Bot options parity.")
        return
    lines.extend(
        [
            "",
            "## Keybindings menu",
            "- Sections: General, 2D, 3D, 4D.",
            "- Rows show action, key(s), and action description.",
            "",
            "## Pause parity",
            "- Pause includes Help, Settings, Keybindings, Bot Options, Restart, and Quit.",
        ]
    )


def _extend_troubleshooting_lines(
    lines: list[str], state: _HelpState, *, compact: bool
) -> None:
    lines.extend(
        [
            "",
            "## Quick recovery",
            "- Re-open Keybindings Setup if controls feel inconsistent.",
            "- Use explicit Save when you want a durable checkpoint.",
            "- Use Edge/OFF grid if visuals feel crowded.",
        ]
    )
    if compact:
        return
    lines.extend(
        [
            "",
            "## Gameplay shortcuts",
            f"- Help: {_current_binding_text(state.dimension, 'help')}",
            f"- Grid mode: {_current_binding_text(state.dimension, 'toggle_grid')}",
            f"- Pause menu: {_current_binding_text(state.dimension, 'menu')}",
        ]
    )


def _topic_text_lines(
    *,
    topic: dict[str, Any],
    state: _HelpState,
    context_label: str,
    topics: Sequence[dict[str, Any]],
    compact: bool,
) -> list[str]:
    topic_id = str(topic.get("id", ""))
    lines = _topic_section_lines(topic)

    if topic_id == "overview":
        _extend_overview_lines(
            lines,
            state=state,
            context_label=context_label,
            topics=topics,
            compact=compact,
        )
    elif topic_id == "game_types":
        _extend_game_types_lines(lines, compact=compact)
    elif topic_id == "gameplay_features":
        _extend_features_lines(lines, compact=compact)
    elif topic_id == "settings_profiles":
        _extend_settings_lines(lines, compact=compact)
    elif topic_id == "camera_and_view":
        _extend_camera_view_lines(lines, compact=compact)
    elif topic_id == "menu_workflows":
        _extend_workflow_lines(lines, compact=compact)
    elif topic_id == "troubleshooting":
        _extend_troubleshooting_lines(lines, state, compact=compact)

    include_all = topic_id == _KEY_REFERENCE_TOPIC_ID
    action_lines = help_topic_action_lines(
        topic_id=topic_id,
        dimension=state.dimension,
        include_all=include_all,
    )
    if action_lines:
        lines.extend(["", "## Live keys (active profile)", *action_lines])
    return lines


def _group_box_height(
    *, rows: int, panel_font: pygame.font.Font, hint_font: pygame.font.Font
) -> int:
    base = 10 + hint_font.get_height() + 6 + (rows * (panel_font.get_height() + 2)) + 8
    return base + 6


def _paginate_control_groups(
    groups: Sequence[tuple[str, tuple[str, ...]]],
    *,
    panel_font: pygame.font.Font,
    hint_font: pygame.font.Font,
    available_height: int,
) -> tuple[tuple[tuple[str, tuple[str, ...]], ...], ...]:
    pages: list[tuple[tuple[str, tuple[str, ...]], ...]] = []
    current: list[tuple[str, tuple[str, ...]]] = []
    used_height = 0

    for group_name, rows in groups:
        block_h = _group_box_height(
            rows=len(rows), panel_font=panel_font, hint_font=hint_font
        )
        if current and used_height + block_h > available_height:
            pages.append(tuple(current))
            current = [(group_name, rows)]
            used_height = block_h
            continue
        current.append((group_name, rows))
        used_height += block_h

    if current:
        pages.append(tuple(current))
    if not pages:
        pages.append(tuple())
    return tuple(pages)


def _draw_controls_topic(
    surface: pygame.Surface,
    fonts,
    *,
    topic: dict[str, Any],
    state: _HelpState,
    content_rect: pygame.Rect,
) -> int:
    title = str(topic.get("title", "Controls"))
    y = _draw_content_title(
        surface,
        font=fonts.hint_font,
        text=f"{title} ({state.dimension}D)",
        rect=content_rect,
    )
    groups = tuple(control_groups_for_dimension(state.dimension))
    helper_rect = pygame.Rect(
        content_rect.x + _HELP_CONTENT_PAD_X,
        y,
        max(1, content_rect.width - (_HELP_CONTENT_PAD_X * 2)),
        max(1, content_rect.bottom - y - _HELP_CONTENT_PAD_Y),
    )
    pages = _paginate_control_groups(
        groups,
        panel_font=fonts.panel_font,
        hint_font=fonts.hint_font,
        available_height=helper_rect.height,
    )
    state.subpage = max(0, min(len(pages) - 1, state.subpage))
    page_groups = pages[state.subpage]
    draw_grouped_control_helper(
        surface,
        groups=page_groups,
        rect=helper_rect,
        panel_font=fonts.panel_font,
        hint_font=fonts.hint_font,
    )
    return len(pages)


def _draw_topic_text(
    surface: pygame.Surface,
    fonts,
    *,
    topic: dict[str, Any],
    state: _HelpState,
    context_label: str,
    topics: Sequence[dict[str, Any]],
    content_rect: pygame.Rect,
    compact: bool,
) -> int:
    title = str(topic.get("title", "Help"))
    y = _draw_content_title(
        surface,
        font=fonts.hint_font,
        text=f"{title} ({state.dimension}D)",
        rect=content_rect,
    )
    lines = _topic_text_lines(
        topic=topic,
        state=state,
        context_label=context_label,
        topics=topics,
        compact=compact,
    )
    rows_per_page = _line_capacity(
        fonts.hint_font, content_rect=content_rect, y_start=y
    )
    line_pages = paginate_help_lines(lines, rows_per_page)
    state.subpage = max(0, min(len(line_pages) - 1, state.subpage))
    _draw_lines(
        surface,
        fonts.hint_font,
        line_pages[state.subpage],
        rect=content_rect,
        y_start=y,
    )
    return len(line_pages)


def _draw_help(
    surface: pygame.Surface, fonts, state: _HelpState, context_label: str
) -> None:
    _draw_gradient(surface)
    width, height = surface.get_size()
    compact = is_compact_help_view(width=width, height=height)
    frame_rect, header_rect, content_rect, footer_rect = _help_layout_zones(
        surface, fonts
    )

    topic, topics = _current_topic(state, context_label)
    total_pages = len(topics)

    help_binding = _current_binding_text(state.dimension, "help")
    title_text = fit_text(
        fonts.title_font,
        "Help & Explanations",
        max(40, header_rect.width - (_HELP_CONTENT_PAD_X * 2)),
    )
    subtitle_text = (
        f"{context_label} | {state.dimension}D | Help: {help_binding}"
        if compact
        else f"Context: {context_label}   Dim: {state.dimension}D   Help: {help_binding} (live profile)"
    )
    subtitle_draw = fit_text(
        fonts.hint_font,
        subtitle_text,
        max(40, header_rect.width - (_HELP_CONTENT_PAD_X * 2)),
    )
    title = fonts.title_font.render(title_text, True, _TEXT_COLOR)
    subtitle = fonts.hint_font.render(subtitle_draw, True, _MUTED_COLOR)
    title_y = header_rect.y + _HELP_CONTENT_PAD_Y
    subtitle_y = title_y + title.get_height() + 6
    surface.blit(
        title,
        (header_rect.x + max(0, (header_rect.width - title.get_width()) // 2), title_y),
    )
    surface.blit(
        subtitle,
        (
            header_rect.x + max(0, (header_rect.width - subtitle.get_width()) // 2),
            subtitle_y,
        ),
    )

    topic_id = str(topic.get("id", ""))
    if topic_id == _CONTROL_TOPIC_ID:
        subpage_count = _draw_controls_topic(
            surface,
            fonts,
            topic=topic,
            state=state,
            content_rect=content_rect,
        )
    else:
        subpage_count = _draw_topic_text(
            surface,
            fonts,
            topic=topic,
            state=state,
            context_label=context_label,
            topics=topics,
            content_rect=content_rect,
            compact=compact,
        )

    state.subpage = max(0, min(subpage_count - 1, state.subpage))
    page_label = fonts.hint_font.render(
        f"Topic {state.page + 1}/{total_pages}", True, _MUTED_COLOR
    )
    part_label = fonts.hint_font.render(
        f"Part {state.subpage + 1}/{subpage_count}", True, _MUTED_COLOR
    )
    page_x = frame_rect.right - page_label.get_width() - _HELP_CONTENT_PAD_X
    part_x = page_x
    page_y = header_rect.y + _HELP_CONTENT_PAD_Y
    part_y = page_y + page_label.get_height() + 3
    surface.blit(page_label, (page_x, page_y))
    surface.blit(part_label, (part_x, part_y))

    footer_msg = fonts.hint_font.render(
        fit_text(
            fonts.hint_font,
            (
                "Esc | <- -> topic | [ ] part"
                if compact
                else "Esc back | Left/Right topic | Up/Down dimension | [ ] subpage"
            ),
            max(40, footer_rect.width - (_HELP_CONTENT_PAD_X * 2)),
        ),
        True,
        _MUTED_COLOR,
    )
    footer_x = footer_rect.x + max(0, (footer_rect.width - footer_msg.get_width()) // 2)
    footer_y = footer_rect.y + max(
        0, (footer_rect.height - footer_msg.get_height()) // 2
    )
    surface.blit(footer_msg, (footer_x, footer_y))


def _handle_help_keydown(state: _HelpState, *, context_label: str, key: int) -> bool:
    if key == pygame.K_ESCAPE:
        state.running = False
        return True
    if key == pygame.K_LEFT:
        _cycle_page(state, context_label, -1)
        return True
    if key == pygame.K_RIGHT:
        _cycle_page(state, context_label, 1)
        return True
    if key == pygame.K_UP:
        _cycle_dimension(state, context_label, -1)
        return True
    if key == pygame.K_DOWN:
        _cycle_dimension(state, context_label, 1)
        return True
    if key in (pygame.K_LEFTBRACKET, pygame.K_PAGEUP, pygame.K_COMMA):
        state.subpage = max(0, state.subpage - 1)
        return True
    if key in (pygame.K_RIGHTBRACKET, pygame.K_PAGEDOWN, pygame.K_PERIOD):
        state.subpage += 1
        return True
    return False


def run_help_menu(
    screen: pygame.Surface,
    fonts,
    *,
    dimension: int = 2,
    context_label: str = "Launcher",
) -> pygame.Surface:
    state = _HelpState(dimension=max(2, min(4, int(dimension))))
    clock = pygame.time.Clock()

    while state.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return screen
            if event.type != pygame.KEYDOWN:
                continue
            _handle_help_keydown(state, context_label=context_label, key=event.key)

        _draw_help(screen, fonts, state, context_label)
        pygame.display.flip()

    return screen
