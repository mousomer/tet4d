from __future__ import annotations

from tet4d.ui.pygame.locked_cell_explosion.model import (
    ExplosionSeedCell,
    select_endgame_live_cells,
    split_endgame_cells,
)


def _cells() -> tuple[ExplosionSeedCell, ...]:
    return tuple(
        ExplosionSeedCell((x, y, z, w), (x + y + z + w) % 7, f"G{x}")
        for x in range(3)
        for y in range(2)
        for z in range(2)
        for w in range(2)
    )


def test_same_seed_selects_same_subset_independent_of_input_order() -> None:
    cells = _cells()

    selected_a = select_endgame_live_cells(
        locked_cells=cells,
        dimension=4,
        seed=12345,
        live_fraction=0.25,
    )
    selected_b = select_endgame_live_cells(
        locked_cells=tuple(reversed(cells)),
        dimension=4,
        seed=12345,
        live_fraction=0.25,
    )

    assert selected_a == selected_b
    assert len(selected_a) == 6


def test_selected_subset_is_separate_from_full_locked_context() -> None:
    cells = _cells()

    split = split_endgame_cells(
        locked_cells=cells,
        dimension=4,
        seed=12345,
        live_fraction=0.25,
    )

    assert len(split.persistent_live_cells) == 6
    assert len(split.escaping_cells) == len(cells) - 6
    assert set(split.persistent_live_cells).isdisjoint(split.escaping_cells)
