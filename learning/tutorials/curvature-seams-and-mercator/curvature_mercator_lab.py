"""Chapter 2: exact square-quotient curvature and spherical Mercator calculations.

Standard library only; educational calculations, NOT Tet4D movement logic.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from math import cos, isfinite, log, pi, radians, tan

# Natural tangent coordinate directions from Chapter 1.
EDGES = {
    "L": ("A", "D"),  # (0,t)
    "R": ("B", "C"),  # (1,t)
    "B": ("A", "B"),  # (t,0)
    "T": ("D", "C"),  # (t,1)
}

# Each tuple is (edge_1, edge_2, tangent_sign). Sign +1 means t -> t.
SURFACES = {
    "sphere": (("L", "B", +1), ("R", "T", +1)),
    "torus": (("L", "R", +1), ("B", "T", +1)),
    "klein": (("L", "R", +1), ("B", "T", -1)),
    "projective": (("L", "R", -1), ("B", "T", -1)),
}


def vertex_classes(gluings: Iterable[tuple[str, str, int]]) -> tuple[tuple[str, ...], ...]:
    """Identify corner endpoints, independently of any cell-centre resolver."""
    parent = {vertex: vertex for vertex in "ABCD"}
    pairs = tuple(gluings)
    used = [name for a, b, _ in pairs for name in (a, b)]
    if len(pairs) != 2 or sorted(used) != sorted(EDGES):
        raise ValueError("expected two disjoint pairs covering all square edges")

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, sign in pairs:
        if sign not in (+1, -1):
            raise ValueError("tangent sign must be +1 or -1")
        aa, ab = EDGES[a]
        ba, bb = EDGES[b]
        for u, v in ((aa, ba), (ab, bb)) if sign == +1 else ((aa, bb), (ab, ba)):
            parent[find(u)] = find(v)

    groups: dict[str, list[str]] = defaultdict(list)
    for vertex in "ABCD":
        groups[find(vertex)].append(vertex)
    return tuple(sorted(tuple(sorted(g)) for g in groups.values()))


def cone_defects(gluings: Iterable[tuple[str, str, int]]) -> dict[tuple[str, ...], float]:
    """Angular deficits for the unit-square's inherited piecewise-Euclidean metric.

    Assumes that the edge pairing defines a closed 2-manifold. Vertex links
    must be checked separately for general quotient constructions.
    """
    return {cls: 2 * pi - len(cls) * pi / 2 for cls in vertex_classes(gluings)}


def quotient_summary(gluings: Iterable[tuple[str, str, int]]) -> tuple[int, float]:
    """(Euler characteristic, total angle deficit). For one face, two edges."""
    defects = cone_defects(gluings)
    chi = len(defects) - 2 + 1
    return chi, sum(defects.values())


def sphere_seam_map(edge: str, x: float, y: float) -> tuple[float, float]:
    """Local Euclidean unfolding across the two canonical S2 edge gluings.

    L -> B: (x,y) -> (y,-x); R -> T: (x,y) -> (y,2-x).
    Defined locally on the extended plane, not a complete movement resolver.
    """
    if edge == "L":
        return (y, -x)
    if edge == "R":
        return (y, 2 - x)
    raise ValueError("expected L or R source seam")


def sphere_seam_vector(vx: float, vy: float) -> tuple[float, float]:
    """Jacobian of either orientation-preserving S2 local seam unfolding."""
    return (vy, -vx)


def mercator_y(latitude_radians: float, radius: float = 1.0) -> float:
    """Spherical Mercator northing; undefined at or beyond either pole."""
    if not isfinite(radius) or radius <= 0 or not isfinite(latitude_radians):
        raise ValueError("radius must be finite positive, latitude finite")
    if not -pi / 2 < latitude_radians < pi / 2:
        raise ValueError("Mercator excludes both poles")
    return radius * log(tan(pi / 4 + latitude_radians / 2))


def mercator_scale(latitude_radians: float) -> float:
    """Ratio of map length to spherical ground length, for local displacements."""
    if not isfinite(latitude_radians) or not -pi / 2 < latitude_radians < pi / 2:
        raise ValueError("latitude is outside Mercator's domain")
    return 1 / cos(latitude_radians)


def mercator_distortion_samples(degrees: Iterable[float] = (0, 30, 60, 80, 85)) -> list[tuple[float, float, float]]:
    """Rows: latitude degrees, local linear scale, local area scale."""
    result = []
    for deg in degrees:
        scale = mercator_scale(radians(deg))
        result.append((deg, scale, scale**2))
    return result


if __name__ == "__main__":
    for name, pairs in SURFACES.items():
        chi, defect = quotient_summary(pairs)
        print(f"{name:11} chi={chi:+d} total_defect/pi={defect/pi:.1f}")
        for cls, angle in cone_defects(pairs).items():
            print(f"  {''.join(cls):4} delta/pi={angle/pi:.2f}")
    print("Mercator local scale:")
    for lat, linear, area in mercator_distortion_samples():
        print(f"  {lat:4g} deg: length={linear:8.4f} area={area:9.4f}")
