from __future__ import annotations

from tet4d.engine.runtime.topology_playground_sandbox import (
    SandboxShape,
    ensure_piece_sandbox_state,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    cycle_sandbox_piece as cycle_sandbox_piece_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    move_sandbox_piece as move_sandbox_piece_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    reset_sandbox_piece as reset_sandbox_piece_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    rotate_sandbox_piece as rotate_sandbox_piece_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    rotate_sandbox_piece_action as rotate_sandbox_piece_action_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    sandbox_cells as sandbox_cells_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    sandbox_lines as sandbox_lines_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    sandbox_shape as sandbox_shape_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    sandbox_shapes_for_state as sandbox_shapes_for_state_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    sandbox_validity as sandbox_validity_runtime,
)
from tet4d.engine.runtime.topology_playground_sandbox import (
    spawn_sandbox_piece as spawn_sandbox_piece_runtime,
)
from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundState as RuntimeTopologyPlaygroundState,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile

from .interaction_audit import record_interaction_handler
from .scene_state import (
    TopologyLabState,
    canonical_playground_state,
    ensure_sandbox_state,
    replace_explorer_profile,
    sync_canonical_playground_state,
)


def _runtime_state_for_sandbox(
    state: TopologyLabState,
    *,
    profile: ExplorerTopologyProfile | None = None,
) -> RuntimeTopologyPlaygroundState:
    runtime_state = canonical_playground_state(state)
    if profile is not None and (
        runtime_state is None or runtime_state.explorer_profile != profile
    ):
        replace_explorer_profile(state, profile)
        runtime_state = canonical_playground_state(state)
    if runtime_state is None:
        sync_canonical_playground_state(state)
        runtime_state = canonical_playground_state(state)
    if runtime_state is None:
        raise ValueError("sandbox requires canonical playground state")
    ensure_sandbox_state(state)
    state.sandbox = runtime_state.sandbox_piece_state
    return runtime_state


def sandbox_shapes_for_state(state: TopologyLabState) -> tuple[SandboxShape, ...]:
    return sandbox_shapes_for_state_runtime(_runtime_state_for_sandbox(state))


def ensure_piece_sandbox(state: TopologyLabState) -> None:
    runtime_state = _runtime_state_for_sandbox(state)
    ensure_piece_sandbox_state(runtime_state)
    state.sandbox = runtime_state.sandbox_piece_state


def spawn_sandbox_piece(state: TopologyLabState) -> None:
    runtime_state = _runtime_state_for_sandbox(state)
    spawn_sandbox_piece_runtime(runtime_state)
    state.sandbox = runtime_state.sandbox_piece_state


def sandbox_shape(state: TopologyLabState) -> SandboxShape:
    return sandbox_shape_runtime(_runtime_state_for_sandbox(state))


def sandbox_cells(state: TopologyLabState) -> tuple[tuple[int, ...], ...]:
    return sandbox_cells_runtime(_runtime_state_for_sandbox(state))


def rotate_sandbox_piece_action(
    state: TopologyLabState,
    profile: ExplorerTopologyProfile,
    action: str,
) -> tuple[bool, str]:
    return rotate_sandbox_piece_action_runtime(
        _runtime_state_for_sandbox(state, profile=profile),
        action,
    )


def sandbox_validity(
    state: TopologyLabState,
    profile: ExplorerTopologyProfile,
) -> tuple[bool, str]:
    return sandbox_validity_runtime(_runtime_state_for_sandbox(state, profile=profile))


def move_sandbox_piece(
    state: TopologyLabState,
    profile: ExplorerTopologyProfile,
    step_label: str,
) -> tuple[bool, str]:
    with record_interaction_handler(
        state,
        "sandbox_move",
        step=step_label,
        dimension=state.dimension,
        glue_count=len(profile.gluings),
    ):
        return move_sandbox_piece_runtime(
            _runtime_state_for_sandbox(state, profile=profile),
            step_label,
        )


def rotate_sandbox_piece(
    state: TopologyLabState,
    profile: ExplorerTopologyProfile,
) -> tuple[bool, str]:
    return rotate_sandbox_piece_runtime(
        _runtime_state_for_sandbox(state, profile=profile)
    )


def cycle_sandbox_piece(state: TopologyLabState, step: int) -> None:
    runtime_state = _runtime_state_for_sandbox(state)
    cycle_sandbox_piece_runtime(runtime_state, step)
    state.sandbox = runtime_state.sandbox_piece_state


def reset_sandbox_piece(state: TopologyLabState) -> None:
    runtime_state = _runtime_state_for_sandbox(state)
    reset_sandbox_piece_runtime(runtime_state)
    state.sandbox = runtime_state.sandbox_piece_state


def sandbox_lines(
    state: TopologyLabState,
    profile: ExplorerTopologyProfile,
) -> list[str]:
    del profile
    return sandbox_lines_runtime(_runtime_state_for_sandbox(state))


__all__ = [
    "cycle_sandbox_piece",
    "ensure_piece_sandbox",
    "move_sandbox_piece",
    "reset_sandbox_piece",
    "rotate_sandbox_piece",
    "rotate_sandbox_piece_action",
    "sandbox_cells",
    "sandbox_lines",
    "sandbox_shape",
    "sandbox_shapes_for_state",
    "sandbox_validity",
    "spawn_sandbox_piece",
]
