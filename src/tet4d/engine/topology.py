from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Sequence

from .core.model import Coord


TOPOLOGY_BOUNDED = "bounded"
TOPOLOGY_WRAP_ALL = "wrap_all"
TOPOLOGY_INVERT_ALL = "invert_all"
EDGE_BOUNDED = "bounded"
EDGE_WRAP = "wrap"
EDGE_INVERT = "invert"
TOPOLOGY_MODE_OPTIONS = (
    TOPOLOGY_BOUNDED,
    TOPOLOGY_WRAP_ALL,
    TOPOLOGY_INVERT_ALL,
)
_TOPOLOGY_MODE_SET = frozenset(TOPOLOGY_MODE_OPTIONS)
EDGE_BEHAVIOR_OPTIONS = (
    EDGE_BOUNDED,
    EDGE_WRAP,
    EDGE_INVERT,
)
_EDGE_BEHAVIOR_SET = frozenset(EDGE_BEHAVIOR_OPTIONS)
_TOPOLOGY_LABELS = {
    TOPOLOGY_BOUNDED: "Bounded",
    TOPOLOGY_WRAP_ALL: "Wrap all",
    TOPOLOGY_INVERT_ALL: "Invert all",
}
AxisEdgeRule = tuple[str, str]
EdgeRules = tuple[AxisEdgeRule, ...]


def normalize_topology_mode(mode: str | None) -> str:
    if mode is None:
        return TOPOLOGY_BOUNDED
    normalized = mode.strip().lower()
    if normalized not in _TOPOLOGY_MODE_SET:
        raise ValueError(f"unknown topology mode: {mode!r}")
    return normalized


def topology_mode_from_index(index: int) -> str:
    safe_index = max(0, min(len(TOPOLOGY_MODE_OPTIONS) - 1, int(index)))
    return TOPOLOGY_MODE_OPTIONS[safe_index]


def topology_mode_label(mode: str | None) -> str:
    normalized = normalize_topology_mode(mode)
    return _TOPOLOGY_LABELS.get(normalized, normalized)


def normalize_edge_behavior(value: str | None) -> str:
    if value is None:
        return EDGE_BOUNDED
    normalized = value.strip().lower()
    if normalized not in _EDGE_BEHAVIOR_SET:
        raise ValueError(f"unknown edge behavior: {value!r}")
    return normalized


def default_edge_rules_for_mode(
    axis_count: int,
    gravity_axis: int,
    *,
    mode: str,
    wrap_gravity_axis: bool = False,
) -> EdgeRules:
    normalized_mode = normalize_topology_mode(mode)
    rules: list[AxisEdgeRule] = []
    for axis in range(axis_count):
        if axis == gravity_axis and not wrap_gravity_axis:
            rules.append((EDGE_BOUNDED, EDGE_BOUNDED))
            continue
        if normalized_mode == TOPOLOGY_BOUNDED:
            rules.append((EDGE_BOUNDED, EDGE_BOUNDED))
        elif normalized_mode == TOPOLOGY_WRAP_ALL:
            rules.append((EDGE_WRAP, EDGE_WRAP))
        else:
            rules.append((EDGE_INVERT, EDGE_INVERT))
    return tuple(rules)


def _normalize_edge_rules(
    rules: Sequence[Sequence[str]],
    *,
    axis_count: int,
    gravity_axis: int,
    wrap_gravity_axis: bool,
) -> EdgeRules:
    if len(rules) != axis_count:
        raise ValueError("edge_rules axis count must match dims")
    normalized: list[AxisEdgeRule] = []
    for axis, axis_rule in enumerate(rules):
        if len(axis_rule) != 2:
            raise ValueError("each axis edge rule must contain two behaviors (neg/pos)")
        neg = normalize_edge_behavior(axis_rule[0])
        pos = normalize_edge_behavior(axis_rule[1])
        if axis == gravity_axis and not wrap_gravity_axis:
            neg = EDGE_BOUNDED
            pos = EDGE_BOUNDED
        normalized.append((neg, pos))
    return tuple(normalized)


@dataclass(frozen=True)
class TopologyPolicy:
    dims: Coord
    gravity_axis: int
    mode: str = TOPOLOGY_BOUNDED
    wrap_gravity_axis: bool = False
    edge_rules: EdgeRules | None = None

    def __post_init__(self) -> None:
        if len(self.dims) < 2:
            raise ValueError("dims must include at least two axes")
        if any(size <= 0 for size in self.dims):
            raise ValueError("all dimension sizes must be positive")
        if not (0 <= self.gravity_axis < len(self.dims)):
            raise ValueError("invalid gravity axis")
        normalized_mode = normalize_topology_mode(self.mode)
        object.__setattr__(self, "mode", normalized_mode)
        if self.edge_rules is None:
            normalized_rules = default_edge_rules_for_mode(
                len(self.dims),
                self.gravity_axis,
                mode=normalized_mode,
                wrap_gravity_axis=self.wrap_gravity_axis,
            )
        else:
            normalized_rules = _normalize_edge_rules(
                self.edge_rules,
                axis_count=len(self.dims),
                gravity_axis=self.gravity_axis,
                wrap_gravity_axis=self.wrap_gravity_axis,
            )
        object.__setattr__(self, "edge_rules", normalized_rules)

    def _wrap_axes(self) -> tuple[int, ...]:
        assert self.edge_rules is not None
        return tuple(
            axis
            for axis, (neg, pos) in enumerate(self.edge_rules)
            if neg != EDGE_BOUNDED or pos != EDGE_BOUNDED
        )

    def _map_axis_value(
        self,
        axis: int,
        value: int,
        size: int,
        *,
        allow_above_gravity: bool,
    ) -> tuple[int | None, int]:
        assert self.edge_rules is not None
        neg_behavior, pos_behavior = self.edge_rules[axis]
        invert_count = 0

        while value < 0 or value >= size:
            if value < 0:
                behavior = neg_behavior
                if behavior == EDGE_BOUNDED:
                    if axis == self.gravity_axis and allow_above_gravity:
                        return value, invert_count
                    return None, 0
                value += size
            else:
                behavior = pos_behavior
                if behavior == EDGE_BOUNDED:
                    return None, 0
                value -= size
            if behavior == EDGE_INVERT:
                invert_count += 1
        return value, invert_count

    def map_coord(
        self,
        coord: Coord,
        *,
        allow_above_gravity: bool,
    ) -> Coord | None:
        detail = _map_coord_detail(self, coord, allow_above_gravity=allow_above_gravity)
        if detail is None:
            return None
        base_values, crossed_axes, wrap_axes = detail
        mapped = _apply_invert_crossings(
            dims=self.dims,
            values=base_values,
            wrap_axes=wrap_axes,
            crossed_axes=crossed_axes,
        )
        return tuple(int(value) for value in mapped)


def _map_coord_detail(
    policy: TopologyPolicy,
    coord: Sequence[float],
    *,
    allow_above_gravity: bool,
) -> tuple[tuple[float, ...], frozenset[int], tuple[int, ...]] | None:
    if len(coord) != len(policy.dims):
        return None
    values = [float(value) for value in coord]
    wrap_axes = policy._wrap_axes()
    crossed_axes: set[int] = set()

    for axis, size in enumerate(policy.dims):
        mapped, invert_count = policy._map_axis_value(
            axis,
            values[axis],
            size,
            allow_above_gravity=allow_above_gravity,
        )
        if mapped is None:
            return None
        values[axis] = float(mapped)
        if invert_count % 2 != 0 and axis in wrap_axes:
            crossed_axes.add(axis)

    return tuple(values), frozenset(crossed_axes), wrap_axes


def _apply_invert_crossings(
    *,
    dims: Sequence[int],
    values: Sequence[float],
    wrap_axes: Sequence[int],
    crossed_axes: frozenset[int] | set[int],
) -> tuple[float, ...]:
    output = list(values)
    for axis in wrap_axes:
        inversion_count = sum(1 for crossed in crossed_axes if crossed != axis)
        if inversion_count % 2 != 0:
            output[axis] = float(dims[axis] - 1) - output[axis]
    return tuple(output)


def _mapped_cells_unique(cells: Sequence[Sequence[float]]) -> bool:
    return len({tuple(cell) for cell in cells}) == len(cells)


def _resolve_invert_piece_mapping(
    policy: TopologyPolicy,
    details: Sequence[tuple[tuple[float, ...], frozenset[int], tuple[int, ...]]],
) -> tuple[tuple[float, ...], ...] | None:
    if not details:
        return tuple()
    wrap_axes = details[0][2]
    if not wrap_axes:
        return tuple(base for base, _crossed, _wrap_axes in details)

    observed_cross_sets = [crossed for _base, crossed, _wrap_axes in details]
    candidate_sets: list[frozenset[int]] = []
    first_crossed = observed_cross_sets[0]
    candidate_sets.append(first_crossed)
    for mask in product((0, 1), repeat=len(wrap_axes)):
        candidate = frozenset(axis for idx, axis in enumerate(wrap_axes) if mask[idx])
        if candidate not in candidate_sets:
            candidate_sets.append(candidate)

    best_cells: tuple[tuple[float, ...], ...] | None = None
    best_score: tuple[int, tuple[int, ...]] | None = None
    for candidate in candidate_sets:
        mapped = tuple(
            _apply_invert_crossings(
                dims=policy.dims,
                values=base,
                wrap_axes=wrap_axes,
                crossed_axes=candidate,
            )
            for base, _crossed, _wrap_axes in details
        )
        if not _mapped_cells_unique(mapped):
            continue
        drift = sum(
            len(candidate.symmetric_difference(observed))
            for observed in observed_cross_sets
        )
        score = (drift, tuple(sorted(candidate)))
        if best_score is None or score < best_score:
            best_cells = mapped
            best_score = score
    return best_cells


def _map_piece_cells_common(
    policy: TopologyPolicy,
    coords: Iterable[Sequence[float]],
    *,
    allow_above_gravity: bool,
    require_unique: bool,
) -> tuple[tuple[float, ...], ...] | None:
    details: list[tuple[tuple[float, ...], frozenset[int], tuple[int, ...]]] = []
    for coord in coords:
        detail = _map_coord_detail(
            policy,
            coord,
            allow_above_gravity=allow_above_gravity,
        )
        if detail is None:
            if require_unique:
                return None
            continue
        details.append(detail)
    if not details:
        return tuple()

    mapped_cells = tuple(
        _apply_invert_crossings(
            dims=policy.dims,
            values=base_values,
            wrap_axes=wrap_axes,
            crossed_axes=crossed_axes,
        )
        for base_values, crossed_axes, wrap_axes in details
    )
    if _mapped_cells_unique(mapped_cells):
        return mapped_cells
    if policy.mode == TOPOLOGY_INVERT_ALL:
        resolved = _resolve_invert_piece_mapping(policy, details)
        if resolved is not None:
            return resolved
    if require_unique:
        return None
    return mapped_cells


def map_piece_cells(
    policy: TopologyPolicy,
    coords: Iterable[Coord],
    *,
    allow_above_gravity: bool,
) -> tuple[Coord, ...] | None:
    mapped = _map_piece_cells_common(
        policy,
        coords,
        allow_above_gravity=allow_above_gravity,
        require_unique=True,
    )
    if mapped is None:
        return None
    return tuple(tuple(int(value) for value in coord) for coord in mapped)


def map_overlay_cells(
    policy: TopologyPolicy,
    coords: Iterable[Sequence[float]],
    *,
    allow_above_gravity: bool,
) -> tuple[tuple[float, ...], ...]:
    mapped = _map_piece_cells_common(
        policy,
        coords,
        allow_above_gravity=allow_above_gravity,
        require_unique=False,
    )
    if mapped is None:
        return tuple()
    return mapped
