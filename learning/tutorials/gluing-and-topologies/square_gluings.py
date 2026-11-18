"""Enumerate square edge gluings and classify their compact quotient surfaces.

Python >= 3.10; no third-party dependencies.

Each edge is parameterized naturally as follows:
  L: (0,0) -> (0,1)
  R: (1,0) -> (1,1)
  B: (0,0) -> (1,0)
  T: (0,1) -> (1,1)
A sign of +1 matches first endpoints and last endpoints.
A sign of -1 swaps them.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product

Point = tuple[int, int]
EDGE_ENDS: dict[str, tuple[Point, Point]] = {
    "L": ((0, 0), (0, 1)),
    "R": ((1, 0), (1, 1)),
    "B": ((0, 0), (1, 0)),
    "T": ((0, 1), (1, 1)),
}
EDGE_ORDER = "LRBT"
EDGE_INDEX = {name: index for index, name in enumerate(EDGE_ORDER)}

@dataclass(frozen=True, order=True)
class Pair:
    """A paired edge pair (first < second by EDGE_ORDER) and tangent sign."""
    first: str
    second: str
    sign: int

    def __post_init__(self) -> None:
        if EDGE_INDEX[self.first] >= EDGE_INDEX[self.second]:
            raise ValueError("Pair edges must be in canonical order")
        if self.sign not in (-1, 1):
            raise ValueError("Gluing sign must be +1 or -1")

# A gluing is a tuple of disjoint edge pairs; any unmentioned edge is left free.
Gluing = tuple[Pair, ...]


def normalize(pairs: list[tuple[str, str, int]]) -> Gluing:
    """Canonical order, irrespective of how a pair was described."""
    normalized: list[Pair] = []
    used: set[str] = set()
    for a, b, sign in pairs:
        if a == b or a not in EDGE_ENDS or b not in EDGE_ENDS:
            raise ValueError("Each pair must consist of distinct known edges")
        if a in used or b in used:
            raise ValueError("An edge cannot occur in two gluing pairs")
        used.update((a, b))
        if EDGE_INDEX[a] > EDGE_INDEX[b]:
            a, b = b, a
        normalized.append(Pair(a, b, sign))
    return tuple(sorted(normalized, key=lambda p: (EDGE_INDEX[p.first], EDGE_INDEX[p.second])))


def all_gluings(complete: bool = True) -> list[Gluing]:
    """Generate 12 complete pairings, or all 25 including free edges."""
    def matchings(edges: tuple[str, ...]):
        if not edges:
            yield ()
            return
        first, rest = edges[0], edges[1:]
        if not complete:
            for tail in matchings(rest):
                yield tail
        for other in rest:
            remaining = tuple(e for e in rest if e != other)
            for tail in matchings(remaining):
                yield ((first, other),) + tail

    result: set[Gluing] = set()
    for matching in matchings(tuple(EDGE_ORDER)):
        for signs in product((-1, 1), repeat=len(matching)):
            result.add(normalize([(a, b, s) for (a, b), s in zip(matching, signs)]))
    return sorted(result)


@dataclass(frozen=True)
class SquareSymmetry:
    """(x,y) -> signed permutation of coordinates on [0,1]^2."""
    perm: tuple[int, int]
    flips: tuple[bool, bool]

    def apply(self, p: Point) -> Point:
        return tuple(1-p[self.perm[i]] if self.flips[i] else p[self.perm[i]]
                     for i in (0, 1))  # type: ignore[return-value]


D4 = tuple(SquareSymmetry(p, f) for p in permutations((0, 1))
           for f in product((False, True), repeat=2))


def mapped_edge(sym: SquareSymmetry, edge: str) -> tuple[str, int]:
    """Return the image edge and whether its natural parameter is reversed."""
    mapped = tuple(sym.apply(vertex) for vertex in EDGE_ENDS[edge])
    for target, ends in EDGE_ENDS.items():
        if mapped == ends:
            return (target, 1)
        if mapped == tuple(reversed(ends)):
            return (target, -1)
    raise AssertionError(f"Not a square symmetry: {sym}")


def transform(gluing: Gluing, sym: SquareSymmetry) -> Gluing:
    """Act on both paired edges and their coordinate correspondence."""
    new_pairs = []
    for pair in gluing:
        a, epsilon_a = mapped_edge(sym, pair.first)
        b, epsilon_b = mapped_edge(sym, pair.second)
        new_pairs.append((a, b, pair.sign * epsilon_a * epsilon_b))
    return normalize(new_pairs)


def orbit(gluing: Gluing) -> tuple[Gluing, ...]:
    return tuple(sorted({transform(gluing, symmetry) for symmetry in D4}))


def orbits(gluings: list[Gluing]) -> list[tuple[Gluing, ...]]:
    unseen = set(gluings)
    groups = []
    while unseen:
        representative = min(unseen)
        members = orbit(representative)
        if not set(members) <= set(gluings):
            raise AssertionError("Symmetry action left the input collection")
        unseen.difference_update(members)
        groups.append(members)
    return sorted(groups, key=lambda g: g[0])


def symmetry_name(sym: SquareSymmetry) -> str:
    """Human-readable D4 element based on its action on vertices."""
    vertices = ((0, 0), (1, 0), (1, 1), (0, 1))
    signatures = {
        ((0,0),(1,0),(1,1),(0,1)): "identity",
        ((1,0),(1,1),(0,1),(0,0)): "rotate 90°",
        ((1,1),(0,1),(0,0),(1,0)): "rotate 180°",
        ((0,1),(0,0),(1,0),(1,1)): "rotate 270°",
        ((1,0),(0,0),(0,1),(1,1)): "reflect vertical",
        ((0,1),(1,1),(1,0),(0,0)): "reflect horizontal",
        ((0,0),(0,1),(1,1),(1,0)): "reflect main diagonal",
        ((1,1),(1,0),(0,0),(0,1)): "reflect other diagonal",
    }
    return signatures[tuple(sym.apply(v) for v in vertices)]


class DSU:
    def __init__(self, elements):
        self.parent = {x: x for x in elements}

    def root(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.root(self.parent[x])
        return self.parent[x]

    def union(self, x, y) -> None:
        self.parent[self.root(x)] = self.root(y)

    def classes(self):
        groups = {}
        for x in self.parent:
            groups.setdefault(self.root(x), []).append(x)
        return tuple(sorted(tuple(sorted(x)) for x in groups.values()))


def vertex_classes(gluing: Gluing) -> tuple[tuple[Point, ...], ...]:
    dsu = DSU({v for ends in EDGE_ENDS.values() for v in ends})
    for p in gluing:
        a0, a1 = EDGE_ENDS[p.first]
        b0, b1 = EDGE_ENDS[p.second]
        dsu.union(a0, b0 if p.sign == 1 else b1)
        dsu.union(a1, b1 if p.sign == 1 else b0)
    return dsu.classes()


def validate_vertex_links(gluing: Gluing) -> None:
    """Reject non-manifold quotient vertices (branched/disconnected links).

    Each original corner contributes one arc of its local link. An edge gluing
    identifies corresponding endpoint germs of these arcs. At a valid surface
    vertex the assembled graph is a single circle or a single interval.
    """
    corners = {v for endpoints in EDGE_ENDS.values() for v in endpoints}
    incident = {v: [e for e, ends in EDGE_ENDS.items() if v in ends]
                for v in corners}
    germs = [(v, e) for v in corners for e in incident[v]]
    dsu = DSU(germs)
    for pair in gluing:
        a0, a1 = EDGE_ENDS[pair.first]
        b0, b1 = EDGE_ENDS[pair.second]
        targets = (b0, b1) if pair.sign == 1 else (b1, b0)
        for a, b in zip((a0, a1), targets):
            dsu.union((a, pair.first), (b, pair.second))

    for vertex_group in vertex_classes(gluing):
        arcs = []
        for v in vertex_group:
            a, b = incident[v]
            arcs.append((dsu.root((v, a)), dsu.root((v, b))))
        adjacency: dict[tuple, set] = {}
        degree: dict[tuple, int] = {}
        for a, b in arcs:
            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1  # loops contribute twice
        remaining = set(degree)
        explored = set()
        stack = [next(iter(remaining))]
        while stack:
            node = stack.pop()
            if node in explored:
                continue
            explored.add(node)
            stack.extend(adjacency[node] - explored)
        loose_ends = sum(d == 1 for d in degree.values())
        if explored != remaining or any(d not in (1, 2) for d in degree.values()) \
                or loose_ends not in (0, 2):
            raise ValueError(f"Non-manifold quotient vertex link: {vertex_group}")


def orientable(gluing: Gluing) -> bool:
    """One-face orientation consistency using counterclockwise edge directions.

    CCW boundary traversal: B forward, R forward, T backward, L backward.
    A paired edge must induce opposite boundary orientations to be orientable.
    """
    boundary_sign = {"B": 1, "R": 1, "T": -1, "L": -1}
    return all(boundary_sign[p.first] * p.sign * boundary_sign[p.second] == -1
               for p in gluing)


def boundary_components(gluing: Gluing) -> int:
    """Count cycles of unpaired edges after vertex identifications.

    This is valid for the square-gluing family, whose corner links are manifolds;
    the general case also needs an explicit link validation.
    """
    classes = vertex_classes(gluing)
    belonging = {v: i for i, group in enumerate(classes) for v in group}
    paired_edges = {e for p in gluing for e in (p.first, p.second)}
    free_edges = [e for e in EDGE_ORDER if e not in paired_edges]
    if not free_edges:
        return 0
    dsu = DSU(range(len(classes)))
    incident = set()
    for edge in free_edges:
        a, b = EDGE_ENDS[edge]
        ca, cb = belonging[a], belonging[b]
        incident.update((ca, cb))
        dsu.union(ca, cb)
    return len({dsu.root(v) for v in incident})


def classify(gluing: Gluing) -> dict:
    """Calculate invariants and use compact surface classification.

    Vertex links are validated for the supported single-square cellulation.
    Arbitrary polyhedral complexes need a more general incidence checker.
    """
    validate_vertex_links(gluing)
    V = len(vertex_classes(gluing))
    E = 4 - len(gluing)
    F = 1
    chi = V - E + F
    b = boundary_components(gluing)
    oriented = orientable(gluing)
    if oriented:
        remainder = 2 - b - chi
        if remainder < 0 or remainder % 2:
            raise ValueError("Invariants do not specify an orientable surface")
        g = remainder // 2
        name = {(0,1): "disk", (0,2): "annulus / cylinder", (0,0): "sphere", (1,0): "torus"}.get((g,b), f"orientable genus {g}, {b} boundaries")
    else:
        k = 2 - b - chi
        if k < 1:
            raise ValueError("Invariants do not specify a nonorientable surface")
        name = {(1,1): "Möbius strip", (1,0): "projective plane (RP²)", (2,0): "Klein bottle"}.get((k,b), f"nonorientable crosscaps {k}, {b} boundaries")
    return {"name": name, "V": V, "E": E, "F": F,
            "chi": chi, "boundary": b, "orientable": oriented}


def label(gluing: Gluing) -> str:
    if not gluing:
        return "no pairs"
    return ", ".join(f"{p.first}{p.second}{'+' if p.sign == 1 else '-'}" for p in gluing)
