from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.gameplay.topology import (
    EDGE_BEHAVIOR_OPTIONS,
    default_edge_rules_for_mode,
    topology_mode_from_index,
    topology_mode_label,
)
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TopologyProfileState,
    designer_profiles_for_dimension,
    export_topology_profile_state,
    profile_state_from_preset,
    validate_topology_profile_state,
)

from .scene_state import TopologyLabState

_AXIS_LABELS = {"x": "X", "y": "Y", "z": "Z", "w": "W"}
_EDGE_LABELS = {
    "bounded": "Bounded",
    "wrap": "Wrap",
    "invert": "Invert",
}


@dataclass(frozen=True)
class LegacyRowSpecData:
    key: str
    label: str
    axis: int | None = None
    side: int | None = None
    disabled: bool = False


@dataclass(frozen=True)
class LegacyRowAdjustment:
    handled: bool
    profile: TopologyProfileState | None = None
    error: str | None = None


@dataclass(frozen=True)
class LegacyExportResult:
    ok: bool
    status_lines: tuple[str, ...] = ()
    error: str | None = None


def _preset_profiles(state: TopologyLabState):
    return designer_profiles_for_dimension(state.dimension, state.gameplay_mode)


def _preset_index(state: TopologyLabState) -> int:
    profiles = _preset_profiles(state)
    preset_id = state.profile.preset_id
    if not preset_id:
        return 0
    for idx, profile in enumerate(profiles):
        if profile.profile_id == preset_id:
            return idx
    return 0


def legacy_row_specs(state: TopologyLabState) -> tuple[LegacyRowSpecData, ...]:
    rows = [
        LegacyRowSpecData("preset", "Legacy Preset"),
        LegacyRowSpecData("topology_mode", "Legacy Topology"),
    ]
    axis_names = tuple("xyzw"[: state.dimension])
    for axis_name in axis_names:
        axis = "xyzw".index(axis_name)
        disabled = axis_name == "y" and state.gameplay_mode == GAMEPLAY_MODE_NORMAL
        rows.append(
            LegacyRowSpecData(
                f"{axis_name}_neg",
                f"{_AXIS_LABELS[axis_name]}-",
                axis=axis,
                side=0,
                disabled=disabled,
            )
        )
        rows.append(
            LegacyRowSpecData(
                f"{axis_name}_pos",
                f"{_AXIS_LABELS[axis_name]}+",
                axis=axis,
                side=1,
                disabled=disabled,
            )
        )
    return tuple(rows)


def legacy_row_value_text(
    state: TopologyLabState,
    *,
    key: str,
    axis: int | None = None,
    side: int | None = None,
) -> str | None:
    if key == "preset":
        profiles = _preset_profiles(state)
        return profiles[_preset_index(state)].label
    if key == "topology_mode":
        return topology_mode_label(state.profile.topology_mode)
    if axis is not None and side is not None:
        value = state.profile.edge_rules[axis][side]
        return _EDGE_LABELS.get(value, str(value).title())
    return None


def _profile_from_preset(state: TopologyLabState, step: int) -> TopologyProfileState:
    profiles = _preset_profiles(state)
    idx = (_preset_index(state) + step) % len(profiles)
    return profile_state_from_preset(
        dimension=state.dimension,
        gravity_axis=1,
        gameplay_mode=state.gameplay_mode,
        preset_index=idx,
        topology_mode=state.profile.topology_mode,
    )


def _profile_from_topology_mode(
    state: TopologyLabState,
    step: int,
) -> TopologyProfileState:
    options = tuple(topology_mode_from_index(idx) for idx in range(3))
    current = state.profile.topology_mode
    idx = options.index(current)
    next_mode = options[(idx + step) % len(options)]
    rules = default_edge_rules_for_mode(
        state.dimension,
        1,
        mode=next_mode,
        wrap_gravity_axis=(state.gameplay_mode == GAMEPLAY_MODE_EXPLORER),
    )
    return validate_topology_profile_state(
        gameplay_mode=state.gameplay_mode,
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=next_mode,
        edge_rules=rules,
        preset_id=None,
    )


def _profile_from_edge_rule(
    state: TopologyLabState,
    *,
    axis: int,
    side: int,
    step: int,
) -> TopologyProfileState:
    current = state.profile.edge_rules[axis][side]
    idx = EDGE_BEHAVIOR_OPTIONS.index(current)
    next_value = EDGE_BEHAVIOR_OPTIONS[(idx + step) % len(EDGE_BEHAVIOR_OPTIONS)]
    rules = [tuple(axis_rule) for axis_rule in state.profile.edge_rules]
    axis_rule = list(rules[axis])
    axis_rule[side] = next_value
    rules[axis] = tuple(axis_rule)
    return validate_topology_profile_state(
        gameplay_mode=state.gameplay_mode,
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=state.profile.topology_mode,
        edge_rules=tuple(rules),
        preset_id=None,
    )


def adjust_legacy_row(
    state: TopologyLabState,
    *,
    key: str,
    axis: int | None,
    side: int | None,
    disabled: bool,
    step: int,
    locked_message: str,
) -> LegacyRowAdjustment:
    try:
        if key == "preset":
            return LegacyRowAdjustment(
                handled=True,
                profile=_profile_from_preset(state, step),
            )
        if key == "topology_mode":
            return LegacyRowAdjustment(
                handled=True,
                profile=_profile_from_topology_mode(state, step),
            )
        if axis is not None and side is not None:
            if disabled:
                return LegacyRowAdjustment(handled=True, error=locked_message)
            return LegacyRowAdjustment(
                handled=True,
                profile=_profile_from_edge_rule(
                    state,
                    axis=axis,
                    side=side,
                    step=step,
                ),
            )
    except ValueError as exc:
        return LegacyRowAdjustment(handled=True, error=str(exc))
    return LegacyRowAdjustment(handled=False)


def export_legacy_profile(profile: TopologyProfileState) -> LegacyExportResult:
    ok, message, _path = export_topology_profile_state(
        profile=profile,
        gravity_axis=1,
    )
    if not ok:
        return LegacyExportResult(ok=False, error=message)
    return LegacyExportResult(ok=True, status_lines=(message,))


__all__ = [
    "LegacyExportResult",
    "LegacyRowAdjustment",
    "LegacyRowSpecData",
    "adjust_legacy_row",
    "export_legacy_profile",
    "export_topology_profile_state",
    "legacy_row_specs",
    "legacy_row_value_text",
]
