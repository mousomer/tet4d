from __future__ import annotations

from pathlib import Path

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
        outcome="menu",
        bot_mode="off",
        grid_mode="full",
        random_mode="fixed_seed",
        topology_mode="bounded",
        exploration_mode=False,
    )


def test_leaderboard_records_and_sorts_scores(tmp_path) -> None:
    path = tmp_path / "leaderboard.json"
    _record(path, score=100, lines=5)
    _record(path, score=220, lines=2)
    _record(path, score=160, lines=8)

    entries = leaderboard_top_entries(path=path, limit=10)
    scores = [int(entry["score"]) for entry in entries]
    assert scores[:3] == [220, 160, 100]
    assert str(entries[0]["player_name"]) == "Tester"


def test_leaderboard_clamps_invalid_values(tmp_path) -> None:
    path = tmp_path / "leaderboard.json"
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
    assert bool(entry["exploration_mode"]) is True
    assert str(entry["player_name"]) == "Player"


def test_leaderboard_keeps_restart_outcome(tmp_path) -> None:
    path = tmp_path / "leaderboard.json"
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
        exploration_mode=False,
    )
    entry = leaderboard_top_entries(path=path, limit=1)[0]
    assert str(entry["outcome"]) == "restart"
    assert str(entry["player_name"]) == "Alpha"


def test_leaderboard_entry_would_enter_reports_rank(tmp_path) -> None:
    path = tmp_path / "leaderboard.json"
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
        exploration_mode=False,
    )

    assert qualifies is True
    assert rank == 2


def test_leaderboard_payload_falls_back_on_invalid_json(tmp_path) -> None:
    path = tmp_path / "leaderboard.json"
    path.write_text("{invalid", encoding="utf-8")

    payload = leaderboard_payload(path=path)

    assert int(payload["schema_version"]) >= 1
    assert isinstance(payload["updated_at_utc"], str)
    assert payload["entries"] == []
