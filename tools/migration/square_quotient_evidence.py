"""Finite continuous unit-square proof evidence; never a cell transport resolver."""

from __future__ import annotations

from collections import Counter

# Mathematical incidence of one oriented square, not runtime board constants.
EDGES = {"x-": ("A", "D"), "x+": ("B", "C"), "y-": ("A", "B"), "y+": ("D", "C")}
ORIENTATION = {"x-": -1, "x+": 1, "y-": 1, "y+": -1}


def components(nodes: list[str], pairs: list[tuple[str, str]]) -> list[list[str]]:
    adjacency = {node: set() for node in nodes}
    for left, right in pairs:
        adjacency[left].add(right)
        adjacency[right].add(left)
    remaining = set(nodes)
    groups = []
    while remaining:
        reached, pending = set(), [min(remaining)]
        while pending:
            node = pending.pop()
            if node not in reached:
                reached.add(node)
                pending.extend(adjacency[node] - reached)
        remaining -= reached
        groups.append(sorted(reached))
    return sorted(groups)


def link_kind(arcs: list[tuple[str, str]]) -> tuple[str, list[int]]:
    """Keep loops and parallel arcs; degree two without connectivity is insufficient."""
    degrees = Counter(node for arc in arcs for node in arc)
    values = sorted(degrees.values())
    if not arcs or len(components(list(degrees), arcs)) != 1:
        return "singular", values
    if all(degree == 2 for degree in values):
        return "circle", values
    if values.count(1) == 2 and all(degree in (1, 2) for degree in values):
        return "interval", values
    return "singular", values


def _pairings(recipe: dict) -> list[tuple[str, str, int]]:
    if (
        recipe["schema"],
        recipe["schema_version"],
        recipe["domain"],
        recipe["dimension"],
        recipe["operator_version"],
        recipe["parameters"],
    ) != ("tet4d.square_quotient", 1, "unit_square", 2, 1, {}):
        raise ValueError("unsupported square proof recipe")
    result, used = [], set()
    for row in recipe["gluings"]:
        left = row["source"]["axis"] + row["source"]["side"]
        right = row["target"]["axis"] + row["target"]["side"]
        transform = row["transform"]
        if left not in EDGES or right not in EDGES or left == right:
            raise ValueError("invalid square edge")
        if left in used or right in used:
            raise ValueError("duplicate square edge ownership")
        if transform["permutation"] != [0] or transform["signs"] not in ([1], [-1]):
            raise ValueError("invalid edge parameter map")
        used.update((left, right))
        result.append((left, right, transform["signs"][0]))
    return result


def _boundary_cycles(
    unpaired: list[str], vertex_rep: dict[str, str]
) -> list[list[str]]:
    endpoints = {edge: tuple(vertex_rep[v] for v in EDGES[edge]) for edge in unpaired}
    degrees = Counter(v for pair in endpoints.values() for v in pair)
    if any(value != 2 for value in degrees.values()):
        raise ValueError("boundary incidence is not a union of cycles")
    remaining, cycles = set(unpaired), []
    while remaining:
        edge = min(remaining)
        start, current = endpoints[edge]
        remaining.remove(edge)
        cycle = [edge]
        while current != start:
            choices = sorted(e for e in remaining if current in endpoints[e])
            if len(choices) != 1:
                raise ValueError("ambiguous boundary cycle")
            edge = choices[0]
            a, b = endpoints[edge]
            current = b if current == a else a
            remaining.remove(edge)
            cycle.append(edge)
        cycles.append(cycle)
    return cycles


def analyze_square(recipe: dict) -> dict:
    """Compute endpoint and germ quotients, without inspecting lattice extents."""
    pairs = _pairings(recipe)
    vertex_pairs, germ_pairs = [], []
    for left, right, sign in pairs:
        target = EDGES[right] if sign == 1 else tuple(reversed(EDGES[right]))
        for a, b in zip(EDGES[left], target, strict=True):
            vertex_pairs.append((a, b))
            germ_pairs.append((f"{left}:{a}", f"{right}:{b}"))
    vertices = components(list("ABCD"), vertex_pairs)
    edge_classes = components(list(EDGES), [(a, b) for a, b, _ in pairs])
    germs = [f"{edge}:{v}" for edge, ends in EDGES.items() for v in ends]
    germ_classes = components(germs, germ_pairs)
    germ_rep = {node: group[0] for group in germ_classes for node in group}
    links = []
    for group in vertices:
        arcs = []
        for corner in group:
            ends = [
                germ_rep[f"{edge}:{corner}"]
                for edge, vs in EDGES.items()
                if corner in vs
            ]
            arcs.append(tuple(ends))
        kind, degrees = link_kind(arcs)
        links.append({"corners": group, "kind": kind, "degrees": degrees})
    if any(link["kind"] == "singular" for link in links):
        raise ValueError("nonmanifold vertex link")
    used = {edge for a, b, _ in pairs for edge in (a, b)}
    unpaired = sorted(set(EDGES) - used)
    vertex_rep = {node: group[0] for group in vertices for node in group}
    cycles = _boundary_cycles(unpaired, vertex_rep)
    for link in links:
        has_boundary = any(v in EDGES[e] for v in link["corners"] for e in unpaired)
        if has_boundary != (link["kind"] == "interval"):
            raise ValueError("link endpoints disagree with boundary incidence")
    orientable = all(
        ORIENTATION[a] * sign * ORIENTATION[b] == -1 for a, b, sign in pairs
    )
    return {
        "face_count": 1,
        "edge_classes": edge_classes,
        "vertex_classes": vertices,
        "vertex_links": links,
        "boundary_cycles": cycles,
        "orientable": orientable,
        "euler_characteristic": len(vertices) - len(edge_classes) + 1,
        "compact": True,
        "connected": True,
    }
