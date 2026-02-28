from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

Coord = tuple[int, ...]


@dataclass
class BoardND:
    """
    ND board. For 2D, dims = (width, height) and coords are (x, y).
    We only store *occupied* cells in a dict: coord -> cell_id (e.g. color).
    """

    dims: Coord
    cells: Dict[Coord, int] = field(default_factory=dict)
    last_cleared_levels: List[int] = field(default_factory=list)
    last_cleared_cells: List[tuple[Coord, int]] = field(default_factory=list)

    def inside_bounds(self, coord: Coord) -> bool:
        if len(coord) != len(self.dims):
            return False
        return all(0 <= c < d for c, d in zip(coord, self.dims))

    def is_occupied(self, coord: Coord) -> bool:
        return coord in self.cells

    def can_place(self, coords: Iterable[Coord]) -> bool:
        for c in coords:
            if not self.inside_bounds(c):
                return False
            if self.is_occupied(c):
                return False
        return True

    def place(self, coords: Iterable[Coord], cell_id: int) -> None:
        for c in coords:
            if not self.inside_bounds(c):
                raise ValueError(f"Trying to place outside board: {c}")
            self.cells[c] = cell_id

    def full_levels(self, gravity_axis: int) -> List[int]:
        from ..rules.board_rules import full_levels as full_levels_rule

        return full_levels_rule(self.dims, self.cells, gravity_axis)

    def clear_planes(self, gravity_axis: int) -> int:
        from ..rules.board_rules import clear_planes as clear_planes_rule

        cleared, new_cells, cleared_levels, cleared_cells = clear_planes_rule(
            self.dims,
            self.cells,
            gravity_axis,
        )
        self.cells = new_cells
        self.last_cleared_levels = cleared_levels
        self.last_cleared_cells = cleared_cells
        return cleared


__all__ = ["BoardND"]
