"""Exact 2D T1 rotation/classification evidence; no runtime or commit engine.

Inputs are already structurally validated fixture states/profiles. This bounded
calculation has no translation resolver, history, import, or application API.
Reviewed expected fixture values remain independent, literal data.
"""

from __future__ import annotations

IDENTITY = {"permutation": [0, 1], "signs": [1, 1]}


def apply_frame(frame: dict, vector) -> tuple[int, int]:
    result = [0, 0]
    for j, target in enumerate(frame["permutation"]):
        result[target] = frame["signs"][j] * vector[j]
    return tuple(result)


def compose(left: dict, right: dict) -> dict:
    return {
        "permutation": [left["permutation"][j] for j in right["permutation"]],
        "signs": [
            right["signs"][j] * left["signs"][right["permutation"][j]] for j in range(2)
        ],
    }


def inverse(frame: dict) -> dict:
    p, s = [0, 0], [0, 0]
    for j, target in enumerate(frame["permutation"]):
        p[target], s[target] = j, frame["signs"][j]
    return {"permutation": p, "signs": s}


def identity_wrap_axes(profile: dict) -> set[int]:
    """Per-axis classification periods in a validated canonical v1 profile."""
    return {
        "xy".index(g["source"]["axis"])
        for g in profile["gluings"]
        if g["source"]["axis"] == g["target"]["axis"]
        and g["source"]["side"] != g["target"]["side"]
        and g["transform"] == {"permutation": [0], "signs": [1]}
    }


def classify_correspondence(
    source: list[dict], target: list[dict], profile: dict
) -> str:
    """Classify validated ID correspondence, never make an invalid move valid."""
    targets = {c["id"]: c for c in target}
    if len(targets) != len(source) or set(targets) != {c["id"] for c in source}:
        raise ValueError("classification requires conserved IDs")
    if len({(c["domain"], tuple(c["coordinate"])) for c in target}) != len(target):
        raise ValueError("classification requires injective occupancy")
    wrapped = identity_wrap_axes(profile)
    witnesses = []
    for cell in source:
        dest = targets[cell["id"]]
        u = compose(dest["frame"], inverse(cell["frame"]))
        uc = apply_frame(u, cell["coordinate"])
        t = tuple(
            (dest["coordinate"][j] - uc[j]) % length
            if j in wrapped
            else dest["coordinate"][j] - uc[j]
            for j, length in enumerate(profile["board_dimensions"])
        )
        witnesses.append((u, t))
    if any(w != witnesses[0] for w in witnesses[1:]):
        return "cellwise_deformation"
    return "plain_translation" if witnesses[0][0] == IDENTITY else "rigid_transform"


def nearest_centroid_ids(developed: dict[int, tuple]) -> tuple[int, ...]:
    n = len(developed)
    sums = [sum(c[j] for c in developed.values()) for j in range(2)]
    distances = {
        i: sum((n * c[j] - sums[j]) ** 2 for j in range(2))
        for i, c in developed.items()
    }
    minimum = min(distances.values())
    return tuple(sorted(i for i, value in distances.items() if value == minimum))


def pivot_doubled(developed: dict[int, tuple]) -> tuple[int, int]:
    lo = [min(c[j] for c in developed.values()) for j in range(2)]
    hi = [max(c[j] for c in developed.values()) for j in range(2)]
    if (hi[0] - lo[0]) % 2 == (hi[1] - lo[1]) % 2:
        return tuple(lo[j] + hi[j] for j in range(2))
    selected = min(nearest_centroid_ids(developed))
    return tuple(2 * v for v in developed[selected])


def turn_lift(developed: dict[int, tuple], pivot: tuple, sign: int) -> dict:
    result = {}
    for i, (x, y) in developed.items():
        px, py = pivot
        doubled = (px + sign * (2 * y - py), py - sign * (2 * x - px))
        if any(v % 2 for v in doubled):
            raise ValueError("nonlattice rotation")
        result[i] = tuple(v // 2 for v in doubled)
    return result


def rotation_evidence(state: dict, profile: dict, action: dict) -> dict:
    """Recompute only §9's development, pivot, projection and frame witnesses.

    Blocked results expose diagnostics, never an applicable candidate. No input
    object is mutated, including revision/undo/trace. No runtime claim follows.
    """
    cells = {c["id"]: c for c in state["cells"]}
    rest = {c["id"]: c["coordinate"] for c in state["rest_cells"]}
    h = min(cells)
    frame = cells[h]["frame"]
    empty = {"reason": "rotation_undefined", "cells": [], "evidence": {}}
    if any(c["frame"] != frame for c in cells.values()):
        return empty
    wrapped = identity_wrap_axes(profile)
    # Global all-seam restriction: one twisted seam disables ALL wrap projection.
    if len(wrapped) != len(profile["gluings"]):
        wrapped = set()
    dims = profile["board_dimensions"]

    def project(coord):
        values = tuple(v % dims[j] if j in wrapped else v for j, v in enumerate(coord))
        return values if all(0 <= v < n for v, n in zip(values, dims)) else None

    developed = {}
    for i in sorted(cells):
        offset = apply_frame(frame, [rest[i][j] - rest[h][j] for j in range(2)])
        developed[i] = tuple(cells[h]["coordinate"][j] + offset[j] for j in range(2))
        if project(developed[i]) != tuple(cells[i]["coordinate"]):
            return empty
    sign = action["quarter_turn"] * (1 if action["axis_a"] == 0 else -1)
    pivot = pivot_doubled(developed)
    lifted = turn_lift(developed, pivot, sign)
    evidence = {
        "developed": [list(c) for c in developed.values()],
        "pivot_doubled": list(pivot),
        "rotated_lift": [list(c) for c in lifted.values()],
    }
    targets = {i: project(c) for i, c in lifted.items()}
    if any(c is None for c in targets.values()):
        return dict(empty, evidence=evidence)
    q = {"permutation": [1, 0], "signs": [-sign, sign]}
    rows = [
        dict(cells[i], coordinate=list(targets[i]), frame=compose(q, frame))
        for i in sorted(cells)
    ]
    if len(set(targets.values())) != len(cells):
        return {
            "reason": "destination_collision",
            "cells": [],
            "evidence": evidence,
            "tentative": rows,
            "transport": q,
        }
    return {"reason": "", "cells": rows, "evidence": evidence, "transport": q}


def check_rotation_fixture(case: dict, state: dict, profile: dict) -> None:
    actual = rotation_evidence(state, profile, case["action"])
    if actual["reason"] != case["blocked_reason"]:
        raise ValueError("rotation reason witness mismatch")
    # Development failures can omit diagnostics; resolved rotations/collisions cannot.
    if not actual["reason"] or actual["reason"] == "destination_collision":
        if actual["evidence"] != case["rotation_evidence"]:
            raise ValueError("rotation development/pivot witness mismatch")
        rows = actual.get("tentative", actual["cells"])
        for row, witness in zip(rows, case["per_cell"], strict=True):
            if (
                row["coordinate"] != witness["target"]
                or row["frame"] != witness["frame"]
                or actual["transport"] != witness["transport"]
            ):
                raise ValueError("rotation projected witness mismatch")
    elif case["rotation_evidence"] and case["rotation_evidence"] != actual["evidence"]:
        raise ValueError("blocked rotation development witness mismatch")
    if actual["cells"] != case["candidate"]["cells"]:
        raise ValueError("rotation candidate witness mismatch")
