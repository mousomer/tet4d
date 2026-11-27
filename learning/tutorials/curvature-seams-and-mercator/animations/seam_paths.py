"""Cartesian cell centres on the two 4 by 4 tutorial squares."""

from dataclasses import dataclass

LEFT, RIGHT, UP, DOWN = (-1, 0), (1, 0), (0, 1), (0, -1)
Point = tuple[int, int]


@dataclass(frozen=True)
class Path:
    source: Point
    command: Point
    target: Point
    arrival: Point
    seam: bool

    def centres(self, t):
        """Two clipped copies straddle the identified edges during a crossing."""
        x, y = self.source
        dx, dy = self.command
        yield x + t * dx, y + t * dy
        if self.seam:
            x, y = self.target
            dx, dy = self.arrival
            yield x - (1 - t) * dx, y - (1 - t) * dy


def path(cell, command, sphere):
    x, y = cell
    dx, dy = command
    u, v = x + dx, y + dy
    if 0 <= u < 4 and 0 <= v < 4:
        return Path(cell, command, (u, v), command, False)
    if sphere:
        crossings = {
            LEFT: ((y, 0), UP),
            RIGHT: ((y, 3), DOWN),
            DOWN: ((0, x), RIGHT),
            UP: ((3, x), LEFT),
        }
    else:
        crossings = {
            LEFT: ((3, 3 - y), LEFT),
            RIGHT: ((0, 3 - y), RIGHT),
            DOWN: ((3 - x, 3), DOWN),
            UP: ((3 - x, 0), UP),
        }
    target, arrival = crossings[command]
    return Path(cell, command, target, arrival, True)


def neighbors(cell: Point, sphere: bool) -> set[Point]:
    return {
        path(cell, direction, sphere).target for direction in (LEFT, RIGHT, UP, DOWN)
    }


def bond_status(cells, sphere):
    if len(set(cells)) < len(cells):
        return "collision"
    for index in range(1, len(cells)):
        a, b = cells[index - 1], cells[index]
        if b not in neighbors(a, sphere) or a not in neighbors(b, sphere):
            return "bond broken"
    return "bonds intact" if len(cells) > 2 else "bond intact"
