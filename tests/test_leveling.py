from __future__ import annotations

from tet4d.engine.gameplay.leveling import compute_speed_level


def test_compute_speed_level_disabled_returns_start_level() -> None:
    assert (
        compute_speed_level(
            start_level=4,
            lines_cleared=120,
            enabled=False,
            lines_per_level=10,
        )
        == 4
    )


def test_compute_speed_level_enabled_advances_by_threshold() -> None:
    assert (
        compute_speed_level(
            start_level=1,
            lines_cleared=19,
            enabled=True,
            lines_per_level=10,
        )
        == 2
    )
    assert (
        compute_speed_level(
            start_level=1,
            lines_cleared=20,
            enabled=True,
            lines_per_level=10,
        )
        == 3
    )


def test_compute_speed_level_lines_per_level_is_clamped_to_one() -> None:
    assert (
        compute_speed_level(
            start_level=1,
            lines_cleared=3,
            enabled=True,
            lines_per_level=0,
        )
        == 4
    )


def test_compute_speed_level_caps_at_max_level() -> None:
    assert (
        compute_speed_level(
            start_level=9,
            lines_cleared=50,
            enabled=True,
            lines_per_level=5,
        )
        == 10
    )


def test_compute_speed_level_negative_lines_are_treated_as_zero() -> None:
    assert (
        compute_speed_level(
            start_level=3,
            lines_cleared=-100,
            enabled=True,
            lines_per_level=10,
        )
        == 3
    )
