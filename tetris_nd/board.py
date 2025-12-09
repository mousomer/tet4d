# tetris_nd/board.py
from dataclasses import dataclass, field
from typing import Dict, Iterable, List
from functools import reduce
import operator

from .types import Coord


@dataclass
class BoardND:
    """
    ND board. For 2D, dims = (width, height) and coords are (x, y).
    We only store *occupied* cells in a dict: coord -> cell_id (e.g. color).
    """
    dims: Coord  # e.g. (width, height)
    cells: Dict[Coord, int] = field(default_factory=dict)

    def inside_bounds(self, coord: Coord) -> bool:
        if len(coord) != len(self.dims):
            return False
        return all(0 <= c < d for c, d in zip(coord, self.dims))

    def is_occupied(self, coord: Coord) -> bool:
        return coord in self.cells

    def can_place(self, coords: Iterable[Coord]) -> bool:
        """
        Check that all coords are inside the board AND empty.
        Use this only for already-validated coords (no negative y, etc.).
        """
        for c in coords:
            if not self.inside_bounds(c):
                return False
            if self.is_occupied(c):
                return False
        return True

    def place(self, coords: Iterable[Coord], cell_id: int) -> None:
        """
        Place cells on the board permanently (used when a piece locks).
        Assumes coords are inside bounds.
        """
        for c in coords:
            if not self.inside_bounds(c):
                raise ValueError(f"Trying to place outside board: {c}")
            self.cells[c] = cell_id

    def clear_planes(self, gravity_axis: int) -> int:
        """
        Clear all full hyperplanes orthogonal to gravity_axis.
        For 2D, this means clearing full rows.
        Returns the number of planes cleared.
        """
        n_dims = len(self.dims)
        if not (0 <= gravity_axis < n_dims):
            raise ValueError("Invalid gravity_axis")

        if not self.cells:
            return 0

        axis_size = self.dims[gravity_axis]
        # Size of one "plane": product of other dimensions
        other_dims = [self.dims[i] for i in range(n_dims) if i != gravity_axis]
        max_per_level = reduce(operator.mul, other_dims, 1) if other_dims else 1

        # Count how many cells we have on each level
        level_counts = [0] * axis_size
        for coord in self.cells.keys():
            level_counts[coord[gravity_axis]] += 1

        # Which levels are full?
        full_levels: List[int] = [
            level for level, count in enumerate(level_counts)
            if count == max_per_level and max_per_level > 0
        ]
        if not full_levels:
            return 0

        full_levels = sorted(set(full_levels))
        full_set = set(full_levels)

        # Precompute shift for each coordinate along gravity axis.
        # Convention: index 0 = top, increasing index = downwards.
        # When we clear a level k, all cells with index < k drop down by 1.
        # So a cell at g_val moves to g_val + (#cleared_levels_below_it)
        shift = [0] * axis_size
        for g_val in range(axis_size):
            shift[g_val] = sum(1 for lvl in full_levels if lvl > g_val)

        new_cells: Dict[Coord, int] = {}
        for coord, cell_id in self.cells.items():
            g_val = coord[gravity_axis]
            if g_val in full_set:
                # This cell was on a cleared plane; remove it.
                continue
            new_g = g_val + shift[g_val]
            if new_g >= axis_size:
                # Should not happen with correct logic, but guard anyway.
                continue
            new_coord = list(coord)
            new_coord[gravity_axis] = new_g
            new_cells[tuple(new_coord)] = cell_id

        self.cells = new_cells
        return len(full_levels)
