from __future__ import annotations

from typing import Callable, Optional, Protocol, TypeVar

from ..gameplay.game_nd import GameStateND

Color = tuple[int, int, int]
CoordN = tuple[int, ...]


class _StepDoneAnimation(Protocol):
    def step(self, dt_ms: float) -> None: ...

    @property
    def done(self) -> bool: ...


TAnimation = TypeVar("TAnimation", bound=_StepDoneAnimation)


def advance_gravity(
    state: GameStateND, gravity_accumulator: int, gravity_interval_ms: int
) -> int:
    while not state.game_over and gravity_accumulator >= gravity_interval_ms:
        state.step_gravity()
        gravity_accumulator -= gravity_interval_ms
    return gravity_accumulator


def tick_animation(animation: Optional[TAnimation], dt_ms: int) -> Optional[TAnimation]:
    if animation is None:
        return None
    animation.step(dt_ms)
    if animation.done:
        return None
    return animation


def collect_cleared_ghost_cells(
    state: GameStateND,
    expected_coord_len: int,
    color_for_cell: Callable[[int], Color],
) -> tuple[tuple[CoordN, Color], ...]:
    ghost_cells: list[tuple[CoordN, Color]] = []
    for coord, cell_id in state.board.last_cleared_cells:
        if len(coord) != expected_coord_len:
            continue
        ghost_cells.append((tuple(coord), color_for_cell(cell_id)))
    return tuple(ghost_cells)
