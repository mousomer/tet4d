from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pygame

from tet4d.engine.runtime.leaderboard import (
    leaderboard_entry_would_enter,
    leaderboard_top_entries,
    record_leaderboard_entry,
)
from tet4d.engine.runtime.project_config import project_constant_int
from tet4d.engine.runtime.settings_schema import sanitize_text
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.ui_utils import (
    draw_corner_chip,
    draw_tron_menu_background,
    draw_tron_panel,
    fit_text,
    format_menu_title,
    standard_menu_panel_rect,
)

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)

_ROWS_PER_PAGE = int(project_constant_int(("analytics", "leaderboard_page_rows"), 12, min_value=5, max_value=40))
_NAME_MAX_LENGTH = int(project_constant_int(("analytics", "leaderboard_name_max_length"), 24, min_value=3, max_value=64))


@dataclass
class _LeaderboardState:
    page_index: int = 0
    running: bool = True


@dataclass
class _NamePromptState:
    name: str
    running: bool = True
    accepted: bool = False


@dataclass(frozen=True)
class _NamePromptSummary:
    dimension: int
    score: int
    lines_cleared: int
    duration_seconds: float
    rank: int


def _safe_int(value: object, *, default: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return int(default)
    return int(value)


def _format_duration(seconds: float) -> str:
    total = max(0, int(round(float(seconds))))
    mins, secs = divmod(total, 60)
    return f"{mins:02d}:{secs:02d}"


def _format_date(timestamp_utc: str) -> str:
    text = (
        sanitize_text(timestamp_utc, max_length=64).strip()
        if timestamp_utc is not None
        else ""
    )
    if len(text) >= 10:
        return text[:10]
    return "n/a"


def _session_is_recordable(*, outcome: str, exploration_mode: bool) -> bool:
    if exploration_mode:
        return False
    return sanitize_text(outcome, max_length=24).strip().lower() == "game_over"


def _entry_cells(rank: int, entry: dict[str, object]) -> tuple[str, ...]:
    name = (
        sanitize_text(entry.get("player_name"), max_length=64).strip()
        or "Player"
    )
    score = _safe_int(entry.get("score"))
    lines = _safe_int(entry.get("lines_cleared"))
    dimension = _safe_int(entry.get("dimension"), default=2)
    speed_start = _safe_int(entry.get("start_speed_level"), default=1)
    speed_end = _safe_int(entry.get("end_speed_level"), default=speed_start)
    duration = _format_duration(float(entry.get("duration_seconds", 0.0)))
    date_text = _format_date(entry.get("timestamp_utc"))
    return (
        str(rank),
        name,
        str(score),
        str(lines),
        f"{dimension}D",
        f"{speed_start}->{speed_end}",
        duration,
        date_text,
    )


def _table_columns() -> tuple[tuple[str, int, str], ...]:
    return (
        ("Rank", 72, "center"),
        ("Player", 190, "left"),
        ("Score", 120, "right"),
        ("Lines", 100, "right"),
        ("Dim", 72, "center"),
        ("Level", 120, "center"),
        ("Time", 100, "center"),
        ("Date", 130, "center"),
    )


def _scaled_column_widths(total_width: int) -> tuple[int, ...]:
    columns = _table_columns()
    base_total = sum(int(column[1]) for column in columns)
    usable = max(160, int(total_width))
    if usable >= base_total:
        widths = [
            int(round((column[1] / base_total) * usable)) for column in columns
        ]
    else:
        # On narrow windows, keep all columns visible by allowing tighter cells.
        widths = [
            max(14, int(round((column[1] / base_total) * usable)))
            for column in columns
        ]
    diff = usable - sum(widths)
    widths[-1] += diff
    return tuple(widths)


def _draw_table_cell(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    *,
    align: str,
) -> None:
    draw_text = fit_text(font, text, max(4, rect.width - 10))
    surf = font.render(draw_text, True, color)
    if align == "right":
        x = rect.right - surf.get_width() - 6
    elif align == "center":
        x = rect.x + max(0, (rect.width - surf.get_width()) // 2)
    else:
        x = rect.x + 6
    y = rect.y + max(0, (rect.height - surf.get_height()) // 2)
    screen.blit(surf, (x, y))


def _entries_page(
    entries: tuple[dict[str, object], ...],
    page_index: int,
) -> tuple[tuple[dict[str, object], ...], int, int]:
    if not entries:
        return (), 1, 1
    rows_per_page = max(1, int(_ROWS_PER_PAGE))
    total_pages = max(1, ((len(entries) - 1) // rows_per_page) + 1)
    page = max(0, min(total_pages - 1, page_index))
    start = page * rows_per_page
    stop = min(len(entries), start + rows_per_page)
    return tuple(entries[start:stop]), total_pages, start + 1


def _draw_leaderboard(
    screen: pygame.Surface,
    fonts: Any,
    state: _LeaderboardState,
    entries: tuple[dict[str, object], ...],
) -> None:
    draw_tron_menu_background(screen, top_color=_BG_TOP, bottom_color=_BG_BOTTOM)
    width, height = screen.get_size()

    title = fonts.title_font.render(
        format_menu_title("Leaderboard"),
        True,
        _TEXT_COLOR,
    )
    title_y = 40
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    draw_corner_chip(screen, font=fonts.hint_font, text="Back", x=18, y=18)

    page_entries, total_pages, start_rank = _entries_page(entries, state.page_index)
    has_rows = bool(page_entries)
    row_h = fonts.menu_font.get_height() + 12
    table_rows = max(1, len(page_entries))
    hint_lines = (
        "Left/Right (or [ / ]) change page",
        "Esc returns, Q exits, Enter returns",
    )
    line_h = fonts.hint_font.get_height() + 3
    panel_rect = standard_menu_panel_rect(
        screen,
        panel_w=min(1220, max(520, width - 36)),
        panel_h=min(
            height - 170,
            max(220, 88 + (table_rows * row_h) + (36 if not has_rows else 0)),
        ),
        panel_top=title_y + title.get_height() + 18,
        bottom_reserved=len(hint_lines) * line_h,
    )
    draw_tron_panel(screen, rect=panel_rect)

    table_rect = pygame.Rect(
        panel_rect.x + 12,
        panel_rect.y + 14,
        panel_rect.width - 24,
        panel_rect.height - 48,
    )
    header_h = fonts.hint_font.get_height() + 10
    widths = _scaled_column_widths(table_rect.width)
    columns = _table_columns()

    pygame.draw.rect(screen, (18, 24, 42), table_rect, border_radius=8)
    pygame.draw.rect(screen, (98, 116, 160), table_rect, 1, border_radius=8)

    header_rect = pygame.Rect(table_rect.x, table_rect.y, table_rect.width, header_h)
    pygame.draw.rect(screen, (28, 37, 61), header_rect, border_radius=8)

    x = table_rect.x
    for idx, column in enumerate(columns):
        col_w = widths[idx]
        cell_rect = pygame.Rect(x, table_rect.y, col_w, header_h)
        _draw_table_cell(
            screen,
            fonts.hint_font,
            str(column[0]),
            _HIGHLIGHT_COLOR,
            cell_rect,
            align=str(column[2]),
        )
        if idx < len(columns) - 1:
            pygame.draw.line(
                screen,
                (74, 92, 138),
                (x + col_w, table_rect.y),
                (x + col_w, table_rect.bottom),
                1,
            )
        x += col_w
    pygame.draw.line(
        screen,
        (74, 92, 138),
        (table_rect.x, table_rect.y + header_h),
        (table_rect.right, table_rect.y + header_h),
        1,
    )

    y = table_rect.y + header_h
    if not has_rows:
        empty_line = "No leaderboard runs yet. Reach game over in standard play to record a session."
        empty_rect = pygame.Rect(table_rect.x, y, table_rect.width, row_h)
        _draw_table_cell(
            screen,
            fonts.menu_font,
            empty_line,
            _TEXT_COLOR,
            empty_rect,
            align="left",
        )
    else:
        for offset, entry in enumerate(page_entries):
            row_rect = pygame.Rect(table_rect.x, y, table_rect.width, row_h)
            if offset % 2 == 1:
                pygame.draw.rect(screen, (14, 20, 38), row_rect)
            cells = _entry_cells(start_rank + offset, entry)
            x = table_rect.x
            for idx, cell in enumerate(cells):
                col_w = widths[idx]
                cell_rect = pygame.Rect(x, y, col_w, row_h)
                _draw_table_cell(
                    screen,
                    fonts.menu_font,
                    str(cell),
                    _TEXT_COLOR,
                    cell_rect,
                    align=str(columns[idx][2]),
                )
                x += col_w
            pygame.draw.line(
                screen,
                (52, 64, 100),
                (table_rect.x, y + row_h),
                (table_rect.right, y + row_h),
                1,
            )
            y += row_h

    page_text = f"Page {state.page_index + 1}/{total_pages}"
    page_surf = fonts.hint_font.render(page_text, True, _HIGHLIGHT_COLOR)
    screen.blit(
        page_surf,
        (
            panel_rect.right - page_surf.get_width() - 16,
            panel_rect.bottom - 30,
        ),
    )

    hint_y = panel_rect.bottom + 10
    for hint in hint_lines:
        hint_draw = fit_text(fonts.hint_font, hint, width - 24)
        hint_surf = fonts.hint_font.render(hint_draw, True, _MUTED_COLOR)
        screen.blit(hint_surf, ((width - hint_surf.get_width()) // 2, hint_y))
        hint_y += hint_surf.get_height() + 3


def _handle_keydown(
    state: _LeaderboardState,
    *,
    key: int,
    total_pages: int,
) -> None:
    nav_key = normalize_menu_navigation_key(key)
    if key == pygame.K_q:
        state.running = False
        return
    if nav_key == pygame.K_ESCAPE or key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        state.running = False
        return
    if total_pages <= 1:
        return
    if nav_key == pygame.K_RIGHT or key in (pygame.K_PAGEDOWN, pygame.K_RIGHTBRACKET):
        state.page_index = (state.page_index + 1) % total_pages
    elif nav_key == pygame.K_LEFT or key in (pygame.K_PAGEUP, pygame.K_LEFTBRACKET):
        state.page_index = (state.page_index - 1) % total_pages


def run_leaderboard_menu(
    screen: pygame.Surface,
    fonts: Any,
) -> pygame.Surface:
    state = _LeaderboardState()
    entries = leaderboard_top_entries(limit=200)
    clock = pygame.time.Clock()

    while state.running:
        _dt = clock.tick(60)
        rows_per_page = max(1, int(_ROWS_PER_PAGE))
        total_pages = max(1, ((max(0, len(entries) - 1)) // rows_per_page) + 1)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.running = False
                break
            if event.type != pygame.KEYDOWN:
                continue
            _handle_keydown(state, key=event.key, total_pages=total_pages)
            if not state.running:
                break
        _draw_leaderboard(screen, fonts, state, entries)
        pygame.display.flip()
    return screen


def _draw_name_prompt(
    screen: pygame.Surface,
    fonts: Any,
    *,
    state: _NamePromptState,
    rank: int,
    summary: _NamePromptSummary | None = None,
) -> None:
    width, height = screen.get_size()
    backdrop = pygame.Surface((width, height), pygame.SRCALPHA)
    backdrop.fill((4, 8, 18, 150))
    screen.blit(backdrop, (0, 0))

    panel_w = min(560, max(360, width - 48))
    summary_rows = 0 if summary is None else 2
    panel_h = 220 + (summary_rows * (fonts.hint_font.get_height() + 6))
    panel_x = (width - panel_w) // 2
    panel_y = max(72, (height - panel_h) // 2)
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (8, 12, 26, 228), panel.get_rect(), border_radius=18)
    pygame.draw.rect(panel, (116, 136, 188, 255), panel.get_rect(), 2, border_radius=18)
    screen.blit(panel, panel_rect.topleft)

    title = fonts.title_font.render("Leaderboard Entry", True, _TEXT_COLOR)
    subtitle_text = f"Rank #{rank} qualifies. Enter player name to save this run."
    subtitle = fonts.hint_font.render(
        fit_text(fonts.hint_font, subtitle_text, panel_w - 40),
        True,
        _MUTED_COLOR,
    )
    title_y = panel_y + 18
    subtitle_y = title_y + title.get_height() + 6
    screen.blit(title, (panel_x + 20, title_y))
    screen.blit(subtitle, (panel_x + 20, subtitle_y))

    label_y = subtitle_y + subtitle.get_height() + 14
    if summary is not None:
        summary_lines = (
            f"Score {int(summary.score)}   Lines {int(summary.lines_cleared)}   Rank #{int(summary.rank)}",
            f"{int(summary.dimension)}D run   Time {_format_duration(float(summary.duration_seconds))}",
        )
        for index, line in enumerate(summary_lines):
            line_surf = fonts.hint_font.render(
                fit_text(fonts.hint_font, line, panel_w - 40),
                True,
                (214, 220, 244),
            )
            screen.blit(line_surf, (panel_x + 20, label_y + (index * (line_surf.get_height() + 6))))
        label_y += len(summary_lines) * (fonts.hint_font.get_height() + 6) + 10

    label = fonts.hint_font.render("Name", True, _MUTED_COLOR)
    screen.blit(label, (panel_x + 20, label_y))
    input_rect = pygame.Rect(panel_x + 20, label_y + 26, panel_w - 40, 48)
    pygame.draw.rect(screen, (34, 44, 72), input_rect, border_radius=10)
    pygame.draw.rect(screen, (98, 116, 160), input_rect, 2, border_radius=10)
    input_text = state.name
    caret = "_" if (pygame.time.get_ticks() // 450) % 2 else ""
    content = fit_text(fonts.menu_font, input_text + caret, input_rect.width - 16)
    value = fonts.menu_font.render(content, True, _HIGHLIGHT_COLOR)
    screen.blit(value, (input_rect.x + 8, input_rect.y + 11))

    button_y = input_rect.bottom + 18
    submit_rect = pygame.Rect(panel_x + 20, button_y, 138, 34)
    cancel_rect = pygame.Rect(submit_rect.right + 12, button_y, 138, 34)
    pygame.draw.rect(screen, (50, 110, 88), submit_rect, border_radius=17)
    pygame.draw.rect(screen, (100, 196, 158), submit_rect, 2, border_radius=17)
    pygame.draw.rect(screen, (60, 50, 74), cancel_rect, border_radius=17)
    pygame.draw.rect(screen, (132, 122, 156), cancel_rect, 2, border_radius=17)
    submit_text = fonts.hint_font.render("Enter Submit", True, _TEXT_COLOR)
    cancel_text = fonts.hint_font.render("Esc Skip", True, _TEXT_COLOR)
    screen.blit(
        submit_text,
        (
            submit_rect.centerx - (submit_text.get_width() // 2),
            submit_rect.centery - (submit_text.get_height() // 2),
        ),
    )
    screen.blit(
        cancel_text,
        (
            cancel_rect.centerx - (cancel_text.get_width() // 2),
            cancel_rect.centery - (cancel_text.get_height() // 2),
        ),
    )

    hint = fonts.hint_font.render(
        fit_text(
            fonts.hint_font,
            "Leaderboard registration is modal here; gameplay input stays locked behind the popup.",
            panel_w - 40,
        ),
        True,
        _MUTED_COLOR,
    )
    screen.blit(hint, (panel_x + 20, panel_rect.bottom - hint.get_height() - 16))


def _handle_name_prompt_event(event: pygame.event.Event, state: _NamePromptState) -> bool:
    if event.type == pygame.QUIT:
        state.running = False
        return False
    if event.type == pygame.TEXTINPUT:
        combined = state.name + event.text
        state.name = sanitize_text(
            combined,
            max_length=_NAME_MAX_LENGTH,
        )
        return True
    if event.type != pygame.KEYDOWN:
        return True
    if event.key == pygame.K_ESCAPE:
        state.running = False
        return False
    if event.key == pygame.K_BACKSPACE:
        state.name = state.name[:-1]
        return True
    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        state.accepted = True
        state.running = False
        return False
    return True


def prompt_leaderboard_player_name(
    screen: pygame.Surface,
    fonts: Any,
    *,
    rank: int,
    draw_background: Callable[[], None] | None = None,
    summary: _NamePromptSummary | None = None,
) -> str | None:
    state = _NamePromptState(name="Player")
    clock = pygame.time.Clock()
    pygame.key.start_text_input()
    try:
        while state.running:
            _dt = clock.tick(60)
            for event in pygame.event.get():
                if not _handle_name_prompt_event(event, state):
                    break

            if draw_background is not None:
                draw_background()
            else:
                draw_tron_menu_background(
                    screen,
                    top_color=_BG_TOP,
                    bottom_color=_BG_BOTTOM,
                )
            _draw_name_prompt(
                screen,
                fonts,
                state=state,
                rank=rank,
                summary=summary,
            )
            pygame.display.flip()
    finally:
        pygame.key.stop_text_input()

    if not state.accepted:
        return None
    sanitized = sanitize_text(state.name, max_length=_NAME_MAX_LENGTH)
    final_name = sanitized.strip()
    if not final_name:
        return "Player"
    return final_name


def maybe_record_leaderboard_session(
    screen: pygame.Surface,
    fonts: Any,
    *,
    dimension: int,
    score: int,
    lines_cleared: int,
    start_speed_level: int,
    end_speed_level: int,
    duration_seconds: float,
    outcome: str,
    bot_mode: str,
    grid_mode: str,
    random_mode: str,
    topology_mode: str,
    kick_level: str,
    exploration_mode: bool,
    draw_background: Callable[[], None] | None = None,
) -> bool:
    if not _session_is_recordable(
        outcome=outcome,
        exploration_mode=exploration_mode,
    ):
        return False
    qualifies, rank = leaderboard_entry_would_enter(
        dimension=dimension,
        score=score,
        lines_cleared=lines_cleared,
        start_speed_level=start_speed_level,
        end_speed_level=end_speed_level,
        duration_seconds=duration_seconds,
        outcome=outcome,
        bot_mode=bot_mode,
        grid_mode=grid_mode,
        random_mode=random_mode,
        topology_mode=topology_mode,
        kick_level=kick_level,
        exploration_mode=exploration_mode,
    )
    if not qualifies:
        return False
    summary = _NamePromptSummary(
        dimension=int(dimension),
        score=int(score),
        lines_cleared=int(lines_cleared),
        duration_seconds=float(duration_seconds),
        rank=int(rank),
    )
    player_name = prompt_leaderboard_player_name(
        screen,
        fonts,
        rank=rank,
        draw_background=draw_background,
        summary=summary,
    )
    if player_name is None:
        return False
    record_leaderboard_entry(
        dimension=dimension,
        score=score,
        lines_cleared=lines_cleared,
        start_speed_level=start_speed_level,
        end_speed_level=end_speed_level,
        duration_seconds=duration_seconds,
        outcome=outcome,
        bot_mode=bot_mode,
        grid_mode=grid_mode,
        random_mode=random_mode,
        topology_mode=topology_mode,
        kick_level=kick_level,
        exploration_mode=exploration_mode,
        player_name=player_name,
    )
    return True


__all__ = [
    "maybe_record_leaderboard_session",
    "prompt_leaderboard_player_name",
    "run_leaderboard_menu",
]
