from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pygame

from tet4d.ui.pygame.launch import leaderboard_menu
from tet4d.engine.runtime.leaderboard import (
    leaderboard_entry_would_enter,
    leaderboard_payload,
    leaderboard_top_entries,
    record_leaderboard_entry,
)


def _record(path: Path, *, score: int, lines: int, dimension: int = 2) -> None:
    record_leaderboard_entry(
        path=path,
        dimension=dimension,
        player_name="Tester",
        score=score,
        lines_cleared=lines,
        start_speed_level=1,
        end_speed_level=2,
        duration_seconds=42.0,
        outcome="game_over",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="off",
        exploration_mode=False,
    )


def _leaderboard_path(name: str) -> Path:
    path = Path.cwd() / 'state' / 'analytics' / 'test_outputs' / f'{name}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    return path


def test_leaderboard_records_and_sorts_scores() -> None:
    path = _leaderboard_path('leaderboard_sort')
    _record(path, score=100, lines=5)
    _record(path, score=220, lines=2)
    _record(path, score=160, lines=8)

    entries = leaderboard_top_entries(path=path, limit=10)
    scores = [int(entry["score"]) for entry in entries]
    assert scores[:3] == [220, 160, 100]
    assert str(entries[0]["player_name"]) == "Tester"


def test_leaderboard_keeps_top_ten_per_dimension() -> None:
    path = _leaderboard_path('leaderboard_per_dimension_limit')
    for offset in range(12):
        _record(path, score=300 - offset, lines=offset, dimension=2)
        _record(path, score=500 - offset, lines=offset, dimension=3)

    entries = leaderboard_top_entries(path=path, limit=40)
    dim2_scores = [int(entry["score"]) for entry in entries if int(entry["dimension"]) == 2]
    dim3_scores = [int(entry["score"]) for entry in entries if int(entry["dimension"]) == 3]

    assert len(dim2_scores) == 10
    assert len(dim3_scores) == 10
    assert dim2_scores == [300, 299, 298, 297, 296, 295, 294, 293, 292, 291]
    assert dim3_scores == [500, 499, 498, 497, 496, 495, 494, 493, 492, 491]


def test_leaderboard_clamps_invalid_values() -> None:
    path = _leaderboard_path('leaderboard_clamps')
    record_leaderboard_entry(
        path=path,
        dimension=9,
        player_name="",
        score=-50,
        lines_cleared=-2,
        start_speed_level=0,
        end_speed_level=99,
        duration_seconds=-5.0,
        outcome="weird",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="light",
        exploration_mode=True,
    )
    entry = leaderboard_top_entries(path=path, limit=1)[0]
    assert int(entry["dimension"]) == 4
    assert int(entry["score"]) == 0
    assert int(entry["lines_cleared"]) == 0
    assert int(entry["start_speed_level"]) == 1
    assert int(entry["end_speed_level"]) == 10
    assert float(entry["duration_seconds"]) == 0.0
    assert str(entry["outcome"]) == "session_end"
    assert str(entry["kick_level"]) == "light"
    assert bool(entry["exploration_mode"]) is True
    assert str(entry["player_name"]) == "Player"


def test_leaderboard_keeps_restart_outcome() -> None:
    path = _leaderboard_path('leaderboard_restart')
    record_leaderboard_entry(
        path=path,
        dimension=3,
        player_name="Alpha",
        score=25,
        lines_cleared=2,
        start_speed_level=2,
        end_speed_level=3,
        duration_seconds=12.5,
        outcome="restart",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="standard",
        exploration_mode=False,
    )
    entry = leaderboard_top_entries(path=path, limit=1)[0]
    assert str(entry["outcome"]) == "restart"
    assert str(entry["kick_level"]) == "standard"
    assert str(entry["player_name"]) == "Alpha"


def test_leaderboard_entry_would_enter_reports_rank() -> None:
    path = _leaderboard_path('leaderboard_rank')
    _record(path, score=200, lines=3)
    _record(path, score=120, lines=4)

    qualifies, rank = leaderboard_entry_would_enter(
        path=path,
        dimension=2,
        score=150,
        lines_cleared=2,
        start_speed_level=1,
        end_speed_level=2,
        duration_seconds=9.0,
        outcome="menu",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="off",
        exploration_mode=False,
    )

    assert qualifies is True
    assert rank == 2


def test_leaderboard_rank_ignores_other_dimensions() -> None:
    path = _leaderboard_path('leaderboard_rank_per_dimension')
    for offset in range(10):
        _record(path, score=600 - offset, lines=offset, dimension=3)
    _record(path, score=190, lines=3, dimension=2)
    _record(path, score=120, lines=4, dimension=2)

    qualifies, rank = leaderboard_entry_would_enter(
        path=path,
        dimension=2,
        score=150,
        lines_cleared=2,
        start_speed_level=1,
        end_speed_level=2,
        duration_seconds=9.0,
        outcome="game_over",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="off",
        exploration_mode=False,
    )

    assert qualifies is True
    assert rank == 2


def test_leaderboard_payload_falls_back_on_invalid_json() -> None:
    path = _leaderboard_path('leaderboard_invalid_json')
    path.write_text('{invalid', encoding='utf-8')
    payload = leaderboard_payload(path=path)
    assert int(payload["schema_version"]) >= 1
    assert isinstance(payload["updated_at_utc"], str)
    assert payload["entries"] == []


def test_explorer_sessions_do_not_prompt_or_record(monkeypatch) -> None:
    called: list[str] = []

    def _boom(*_args, **_kwargs):
        called.append("unexpected")
        raise AssertionError("explorer leaderboard path should short-circuit")

    monkeypatch.setattr(leaderboard_menu, "leaderboard_entry_would_enter", _boom)
    monkeypatch.setattr(leaderboard_menu, "prompt_leaderboard_player_name", _boom)
    monkeypatch.setattr(leaderboard_menu, "record_leaderboard_entry", _boom)

    recorded = leaderboard_menu.maybe_record_leaderboard_session(
        None,
        None,
        dimension=2,
        score=999,
        lines_cleared=0,
        start_speed_level=1,
        end_speed_level=1,
        duration_seconds=1.0,
        outcome="menu",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="off",
        exploration_mode=True,
    )

    assert recorded is False
    assert called == []


def test_non_endgame_sessions_do_not_prompt_or_record(monkeypatch) -> None:
    calls: list[str] = []

    def _boom(*_args, **_kwargs):
        calls.append("unexpected")
        raise AssertionError("non-endgame leaderboard path should short-circuit")

    monkeypatch.setattr(leaderboard_menu, "leaderboard_entry_would_enter", _boom)
    monkeypatch.setattr(leaderboard_menu, "prompt_leaderboard_player_name", _boom)
    monkeypatch.setattr(leaderboard_menu, "record_leaderboard_entry", _boom)

    recorded = leaderboard_menu.maybe_record_leaderboard_session(
        None,
        None,
        dimension=2,
        score=999,
        lines_cleared=0,
        start_speed_level=1,
        end_speed_level=1,
        duration_seconds=1.0,
        outcome="quit",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="off",
        exploration_mode=False,
    )

    assert recorded is False
    assert calls == []


def test_endgame_sessions_still_record_when_qualifying(monkeypatch) -> None:
    calls: list[str] = []

    def _qualifies(*_args, **_kwargs):
        calls.append("rank")
        return True, 1

    def _prompt(*_args, **_kwargs):
        calls.append("prompt")
        return "Tester"

    def _record(*_args, **_kwargs):
        calls.append("record")

    monkeypatch.setattr(leaderboard_menu, "leaderboard_entry_would_enter", _qualifies)
    monkeypatch.setattr(leaderboard_menu, "prompt_leaderboard_player_name", _prompt)
    monkeypatch.setattr(leaderboard_menu, "record_leaderboard_entry", _record)

    recorded = leaderboard_menu.maybe_record_leaderboard_session(
        None,
        None,
        dimension=2,
        score=999,
        lines_cleared=0,
        start_speed_level=1,
        end_speed_level=1,
        duration_seconds=1.0,
        outcome="game_over",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="off",
        exploration_mode=False,
    )

    assert recorded is True
    assert calls == ["rank", "prompt", "record"]


def test_maybe_record_passes_modal_background_and_summary(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _qualifies(*_args, **_kwargs):
        return True, 2

    def _prompt(*_args, **kwargs):
        captured["draw_background"] = kwargs.get("draw_background")
        captured["summary"] = kwargs.get("summary")
        return "Tester"

    monkeypatch.setattr(leaderboard_menu, "leaderboard_entry_would_enter", _qualifies)
    monkeypatch.setattr(leaderboard_menu, "prompt_leaderboard_player_name", _prompt)
    monkeypatch.setattr(leaderboard_menu, "record_leaderboard_entry", lambda **_kwargs: None)

    background_calls: list[str] = []
    recorded = leaderboard_menu.maybe_record_leaderboard_session(
        None,
        None,
        dimension=3,
        score=999,
        lines_cleared=4,
        start_speed_level=1,
        end_speed_level=3,
        duration_seconds=12.0,
        outcome="game_over",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        kick_level="off",
        exploration_mode=False,
        draw_background=lambda: background_calls.append("drawn"),
    )

    assert recorded is True
    assert callable(captured["draw_background"])
    assert captured["summary"] == leaderboard_menu._NamePromptSummary(
        dimension=3,
        score=999,
        lines_cleared=4,
        duration_seconds=12.0,
        rank=2,
    )
    cast_draw = captured["draw_background"]
    assert callable(cast_draw)
    cast_draw()
    assert background_calls == ["drawn"]


def test_name_prompt_renders_modal_over_existing_background() -> None:
    pygame.init()
    try:
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 42),
            hint_font=pygame.font.Font(None, 24),
            menu_font=pygame.font.Font(None, 30),
        )
        screen = pygame.Surface((640, 480))
        screen.fill((180, 40, 40))
        leaderboard_menu._draw_name_prompt(
            screen,
            fonts,
            state=leaderboard_menu._NamePromptState(name="Player"),
            rank=1,
            summary=leaderboard_menu._NamePromptSummary(
                dimension=2,
                score=3210,
                lines_cleared=12,
                duration_seconds=48.0,
                rank=1,
            ),
        )
        corner = screen.get_at((8, 8))[:3]
        assert corner != leaderboard_menu._BG_TOP
        assert corner != (180, 40, 40)
    finally:
        pygame.quit()
