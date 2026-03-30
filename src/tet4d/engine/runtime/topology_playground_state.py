from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from tet4d.engine.core.model import Coord
from tet4d.engine.gameplay.topology import TopologyPolicy
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TopologyProfileState,
    default_topology_profile_state,
)
from tet4d.engine.topology_explorer import BoundaryRef, ExplorerTopologyProfile

# Canonical tool ids now follow the settled Probe-first Editor model.
# Older serialized/input aliases are accepted only through
# `canonical_tool_name(...)`.
# - editor: safe probe/selection plus explicit edit tools
# - sandbox: piece experimentation only
# - play: gameplay launch/preview only
TOOL_PROBE = "probe"
TOOL_EDIT = "edit_transform"
TOOL_SANDBOX = "piece_sandbox"
TOOL_PLAY = "play_preview"
TOOL_NAVIGATE = TOOL_PROBE
TOOL_CREATE = TOOL_EDIT
WORKSPACE_EDITOR = "editor"
WORKSPACE_SANDBOX = "sandbox"
WORKSPACE_PLAY = "play"
TOPOLOGY_PLAYGROUND_WORKSPACES = (
    WORKSPACE_EDITOR,
    WORKSPACE_SANDBOX,
    WORKSPACE_PLAY,
)
TOPOLOGY_PLAYGROUND_TOOLS = (
    TOOL_EDIT,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TOOL_PLAY,
)
_EDITOR_TOOLS = (
    TOOL_EDIT,
    TOOL_PROBE,
)
_CANONICAL_TOOL_BY_NAME = {
    "navigate": TOOL_PROBE,
    "inspect_boundary": TOOL_PROBE,
    TOOL_PROBE: TOOL_PROBE,
    "create_gluing": TOOL_EDIT,
    "edit_transform": TOOL_EDIT,
    "piece_sandbox": TOOL_SANDBOX,
    "play_preview": TOOL_PLAY,
}
_WORKSPACE_BY_TOOL = {
    TOOL_EDIT: WORKSPACE_EDITOR,
    TOOL_PROBE: WORKSPACE_EDITOR,
    TOOL_SANDBOX: WORKSPACE_SANDBOX,
    TOOL_PLAY: WORKSPACE_PLAY,
}

TRANSPORT_OWNER_LEGACY = "legacy_topology"
TRANSPORT_OWNER_EXPLORER = "explorer_gluing"
GRAVITY_MODE_FALLING = "falling"
GRAVITY_MODE_EXPLORATION = "exploration"
PLAYABILITY_STATUS_UNKNOWN = "unknown"
PLAYABILITY_STATUS_ANALYZING = "analyzing"
PLAYABILITY_STATUS_PLAYABLE = "playable"
PLAYABILITY_STATUS_WARNING = "warning"
PLAYABILITY_STATUS_BLOCKED = "blocked"
TOPOLOGY_VALIDITY_UNKNOWN = "unknown"
TOPOLOGY_VALIDITY_VALID = "valid"
TOPOLOGY_VALIDITY_INVALID = "invalid"
EXPLORER_USABILITY_UNKNOWN = "unknown"
EXPLORER_USABILITY_CELLWISE = "cellwise_explorable"
EXPLORER_USABILITY_BLOCKED = "not_explorable"
RIGID_PLAYABILITY_UNKNOWN = "unknown"
RIGID_PLAYABILITY_PLAYABLE = "rigid_playable"
RIGID_PLAYABILITY_BLOCKED = "not_rigid_playable"
RIGID_PLAY_MODE_AUTO = "auto"
RIGID_PLAY_MODE_ON = "on"
RIGID_PLAY_MODE_OFF = "off"
PRESET_SOURCE_CUSTOM = "custom"
PRESET_SOURCE_DESIGNER = "designer"
PRESET_SOURCE_EXPLORER = "explorer"
PRESET_SOURCE_FALLBACK = "fallback"

TransportOwner = Literal[
    "legacy_topology",
    "explorer_gluing",
]
GravityModeName = Literal[
    "falling",
    "exploration",
]
PlayabilityStatus = Literal[
    "unknown",
    "analyzing",
    "playable",
    "warning",
    "blocked",
]
TopologyValidity = Literal[
    "unknown",
    "valid",
    "invalid",
]
ExplorerUsability = Literal[
    "unknown",
    "cellwise_explorable",
    "not_explorable",
]
RigidPlayability = Literal[
    "unknown",
    "rigid_playable",
    "not_rigid_playable",
]
RigidPlayMode = Literal[
    "auto",
    "on",
    "off",
]
PresetSource = Literal[
    "custom",
    "designer",
    "explorer",
    "fallback",
]
TopologyWorkspace = Literal[
    "editor",
    "sandbox",
    "play",
]

_VALID_DIMENSIONS = frozenset((2, 3, 4))
_VALID_TRANSPORT_OWNERS = frozenset((TRANSPORT_OWNER_LEGACY, TRANSPORT_OWNER_EXPLORER))
_VALID_GRAVITY_MODES = frozenset((GRAVITY_MODE_FALLING, GRAVITY_MODE_EXPLORATION))
_VALID_PLAYABILITY_STATUSES = frozenset(
    (
        PLAYABILITY_STATUS_UNKNOWN,
        PLAYABILITY_STATUS_ANALYZING,
        PLAYABILITY_STATUS_PLAYABLE,
        PLAYABILITY_STATUS_WARNING,
        PLAYABILITY_STATUS_BLOCKED,
    )
)
_VALID_TOPOLOGY_VALIDITY = frozenset(
    (
        TOPOLOGY_VALIDITY_UNKNOWN,
        TOPOLOGY_VALIDITY_VALID,
        TOPOLOGY_VALIDITY_INVALID,
    )
)
_VALID_EXPLORER_USABILITY = frozenset(
    (
        EXPLORER_USABILITY_UNKNOWN,
        EXPLORER_USABILITY_CELLWISE,
        EXPLORER_USABILITY_BLOCKED,
    )
)
_VALID_RIGID_PLAYABILITY = frozenset(
    (
        RIGID_PLAYABILITY_UNKNOWN,
        RIGID_PLAYABILITY_PLAYABLE,
        RIGID_PLAYABILITY_BLOCKED,
    )
)
_VALID_RIGID_PLAY_MODES = frozenset(
    (
        RIGID_PLAY_MODE_AUTO,
        RIGID_PLAY_MODE_ON,
        RIGID_PLAY_MODE_OFF,
    )
)
_VALID_PRESET_SOURCES = frozenset(
    (
        PRESET_SOURCE_CUSTOM,
        PRESET_SOURCE_DESIGNER,
        PRESET_SOURCE_EXPLORER,
        PRESET_SOURCE_FALLBACK,
    )
)


def _normalize_dimension(dimension: int) -> int:
    value = int(dimension)
    if value not in _VALID_DIMENSIONS:
        raise ValueError("dimension must be one of: 2, 3, 4")
    return value


def _normalize_axis_sizes(dimension: int, axis_sizes: Coord) -> Coord:
    normalized = tuple(int(value) for value in axis_sizes)
    if len(normalized) != dimension:
        raise ValueError("axis_sizes length must match dimension")
    if any(value <= 0 for value in normalized):
        raise ValueError("axis_sizes must contain only positive integers")
    return normalized


def _normalize_coord(name: str, coord: Coord, *, dimension: int) -> Coord:
    normalized = tuple(int(value) for value in coord)
    if len(normalized) != dimension:
        raise ValueError(f"{name} must match the active dimension")
    return normalized


def _coord_in_bounds(coord: Coord, axis_sizes: Coord) -> bool:
    return all(
        0 <= int(value) < int(axis_sizes[index]) for index, value in enumerate(coord)
    )


def _center_coord(axis_sizes: Coord) -> Coord:
    return tuple(max(0, size // 2) for size in axis_sizes)


def _identity_probe_frame(dimension: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(range(dimension)), tuple(1 for _ in range(dimension))


def _normalize_probe_frame(
    *,
    dimension: int,
    permutation: tuple[int, ...] | None,
    signs: tuple[int, ...] | None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    default_permutation, default_signs = _identity_probe_frame(dimension)
    normalized_permutation = (
        default_permutation
        if permutation is None
        else tuple(int(value) for value in permutation)
    )
    normalized_signs = (
        default_signs if signs is None else tuple(int(value) for value in signs)
    )
    if len(normalized_permutation) != dimension:
        normalized_permutation = default_permutation
    if len(normalized_signs) != dimension:
        normalized_signs = default_signs
    if tuple(sorted(normalized_permutation)) != tuple(range(dimension)):
        normalized_permutation = default_permutation
    if any(value not in (-1, 1) for value in normalized_signs):
        normalized_signs = default_signs
    return normalized_permutation, normalized_signs


@dataclass
class TopologyPlaygroundLaunchSettings:
    piece_set_index: int = 0
    speed_level: int = 1
    random_mode_index: int = 0
    game_seed: int = 0
    rigid_play_mode: RigidPlayMode = RIGID_PLAY_MODE_AUTO

    def __post_init__(self) -> None:
        self.piece_set_index = max(0, int(self.piece_set_index))
        self.speed_level = max(1, int(self.speed_level))
        self.random_mode_index = max(0, int(self.random_mode_index))
        self.game_seed = max(0, int(self.game_seed))
        rigid_play_mode = str(self.rigid_play_mode)
        if rigid_play_mode not in _VALID_RIGID_PLAY_MODES:
            raise ValueError(f"unsupported rigid play mode: {self.rigid_play_mode!r}")
        self.rigid_play_mode = rigid_play_mode


@dataclass
class TopologyPlaygroundGluingDraft:
    slot_index: int = 0
    source_boundary: BoundaryRef | None = None
    target_boundary: BoundaryRef | None = None
    permutation: tuple[int, ...] = ()
    signs: tuple[int, ...] = ()
    enabled: bool = True

    def normalize(self, *, dimension: int) -> None:
        self.slot_index = max(0, int(self.slot_index))
        if (
            self.source_boundary is not None
            and self.source_boundary.dimension != dimension
        ):
            raise ValueError("source_boundary dimension must match playground state")
        if (
            self.target_boundary is not None
            and self.target_boundary.dimension != dimension
        ):
            raise ValueError("target_boundary dimension must match playground state")
        tangent_dimension = dimension - 1
        permutation = (
            tuple(range(tangent_dimension))
            if not self.permutation
            else tuple(int(value) for value in self.permutation)
        )
        signs = (
            tuple(1 for _ in range(tangent_dimension))
            if not self.signs
            else tuple(int(value) for value in self.signs)
        )
        if len(permutation) != tangent_dimension:
            raise ValueError("gluing draft permutation must match tangent rank")
        if len(signs) != tangent_dimension:
            raise ValueError("gluing draft signs must match tangent rank")
        if tuple(sorted(permutation)) != tuple(range(tangent_dimension)):
            raise ValueError("gluing draft permutation must be a complete permutation")
        if any(value not in (-1, 1) for value in signs):
            raise ValueError("gluing draft signs must contain only -1 or +1")
        self.permutation = permutation
        self.signs = signs
        self.enabled = bool(self.enabled)


@dataclass
class TopologyPlaygroundTopologyConfig:
    legacy_profile: TopologyProfileState
    explorer_profile: ExplorerTopologyProfile | None = None
    gluing_draft: TopologyPlaygroundGluingDraft = field(
        default_factory=TopologyPlaygroundGluingDraft
    )

    @property
    def gameplay_mode(self) -> str:
        return self.legacy_profile.gameplay_mode

    def normalize(self, *, dimension: int) -> None:
        if self.legacy_profile.dimension != dimension:
            raise ValueError("legacy_profile dimension must match playground state")
        if self.explorer_profile is None:
            self.explorer_profile = ExplorerTopologyProfile(
                dimension=dimension,
                gluings=(),
            )
        elif self.explorer_profile.dimension != dimension:
            raise ValueError("explorer_profile dimension must match playground state")
        self.gluing_draft.normalize(dimension=dimension)


@dataclass
class TopologyPlaygroundProbeState:
    coord: Coord | None = None
    path: tuple[Coord, ...] = ()
    trace: tuple[str, ...] = ()
    show_trace: bool = True
    show_neighbors: bool = False
    highlighted_gluing: str | None = None
    frame_permutation: tuple[int, ...] | None = None
    frame_signs: tuple[int, ...] | None = None
    last_step: str | None = None

    def normalize(self, *, dimension: int, axis_sizes: Coord) -> None:
        coord = (
            None
            if self.coord is None
            else _normalize_coord("probe coord", self.coord, dimension=dimension)
        )
        if coord is not None and not _coord_in_bounds(coord, axis_sizes):
            coord = _center_coord(axis_sizes)
        normalized_path = [
            item
            for item in (
                _normalize_coord("probe path entry", entry, dimension=dimension)
                for entry in self.path
            )
            if _coord_in_bounds(item, axis_sizes)
        ]
        if coord is None:
            normalized_path = []
        elif not normalized_path:
            normalized_path = [coord]
        elif normalized_path[-1] != coord:
            normalized_path.append(coord)
        frame_permutation, frame_signs = _normalize_probe_frame(
            dimension=dimension,
            permutation=self.frame_permutation,
            signs=self.frame_signs,
        )
        self.coord = coord
        self.path = tuple(normalized_path)
        self.trace = tuple(str(entry) for entry in self.trace)
        self.show_trace = bool(self.show_trace)
        self.show_neighbors = bool(self.show_neighbors)
        self.highlighted_gluing = (
            None if self.highlighted_gluing is None else str(self.highlighted_gluing)
        )
        self.frame_permutation = frame_permutation
        self.frame_signs = frame_signs
        self.last_step = None if self.last_step is None else str(self.last_step)


@dataclass
class TopologyPlaygroundSandboxPieceState:
    enabled: bool = False
    piece_index: int = 0
    origin: Coord | None = None
    local_blocks: tuple[Coord, ...] | None = None
    neighbor_search_enabled: bool = True
    trace: tuple[str, ...] = ()
    seam_crossings: tuple[str, ...] = ()
    invalid_message: str = ""
    show_trace: bool = True

    def normalize(self, *, dimension: int, axis_sizes: Coord) -> None:
        self.enabled = bool(self.enabled)
        self.piece_index = max(0, int(self.piece_index))
        origin = (
            None
            if self.origin is None
            else _normalize_coord("sandbox origin", self.origin, dimension=dimension)
        )
        if origin is not None and not _coord_in_bounds(origin, axis_sizes):
            origin = _center_coord(axis_sizes)
        self.origin = origin
        if self.local_blocks is not None:
            self.local_blocks = tuple(
                _normalize_coord(
                    "sandbox local block",
                    block,
                    dimension=dimension,
                )
                for block in self.local_blocks
            )
        self.neighbor_search_enabled = bool(self.neighbor_search_enabled)
        self.trace = tuple(str(entry) for entry in self.trace)
        self.seam_crossings = tuple(str(entry) for entry in self.seam_crossings)
        self.invalid_message = str(self.invalid_message)
        self.show_trace = bool(self.show_trace)


@dataclass
class TopologyPlaygroundGravityMode:
    name: GravityModeName = GRAVITY_MODE_EXPLORATION
    gravity_axis: int = 1
    tick_enabled: bool = False
    locking_enabled: bool = False
    wrap_gravity_axis: bool = True

    def normalize(self, *, dimension: int) -> None:
        name = str(self.name)
        if name not in _VALID_GRAVITY_MODES:
            raise ValueError(f"unsupported gravity mode: {self.name!r}")
        gravity_axis = int(self.gravity_axis)
        if not (0 <= gravity_axis < dimension):
            raise ValueError("gravity_axis must exist in the active dimension")
        self.name = name
        self.gravity_axis = gravity_axis
        self.tick_enabled = bool(self.tick_enabled)
        self.locking_enabled = bool(self.locking_enabled)
        self.wrap_gravity_axis = bool(self.wrap_gravity_axis)


@dataclass
class TopologyPlaygroundTransportPolicy:
    owner: TransportOwner
    base_policy: TopologyPolicy
    explorer_profile: ExplorerTopologyProfile | None = None
    allow_above_gravity: bool = True

    def normalize(
        self,
        *,
        dimension: int,
        axis_sizes: Coord,
        gravity_axis: int,
    ) -> None:
        owner = str(self.owner)
        if owner not in _VALID_TRANSPORT_OWNERS:
            raise ValueError(f"unsupported transport owner: {self.owner!r}")
        if tuple(int(value) for value in self.base_policy.dims) != axis_sizes:
            raise ValueError("base_policy dims must match axis_sizes")
        if int(self.base_policy.gravity_axis) != gravity_axis:
            raise ValueError("base_policy gravity_axis must match gravity_mode")
        if (
            self.explorer_profile is not None
            and self.explorer_profile.dimension != dimension
        ):
            raise ValueError("explorer_profile dimension must match playground state")
        if owner == TRANSPORT_OWNER_EXPLORER and self.explorer_profile is None:
            raise ValueError("explorer transport requires an explorer_profile")
        self.owner = owner
        self.allow_above_gravity = bool(self.allow_above_gravity)


@dataclass
class TopologyPlaygroundMovementSummary:
    cell_count: int | None = None
    directed_edge_count: int | None = None
    boundary_traversal_count: int | None = None
    component_count: int | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "cell_count",
            "directed_edge_count",
            "boundary_traversal_count",
            "component_count",
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            normalized = int(value)
            if normalized < 0:
                raise ValueError(f"{field_name} must be non-negative")
            setattr(self, field_name, normalized)


@dataclass
class TopologyPlaygroundPlayabilityAnalysis:
    status: PlayabilityStatus = PLAYABILITY_STATUS_UNKNOWN
    validity: TopologyValidity = TOPOLOGY_VALIDITY_UNKNOWN
    explorer_usability: ExplorerUsability = EXPLORER_USABILITY_UNKNOWN
    rigid_playability: RigidPlayability = RIGID_PLAYABILITY_UNKNOWN
    summary: str = ""
    validity_reason: str = ""
    explorer_reason: str = ""
    rigid_reason: str = ""
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    movement_summary: TopologyPlaygroundMovementSummary = field(
        default_factory=TopologyPlaygroundMovementSummary
    )
    recommended_next_preset: str | None = None

    def __post_init__(self) -> None:
        status = str(self.status)
        if status not in _VALID_PLAYABILITY_STATUSES:
            raise ValueError(f"unsupported playability status: {self.status!r}")
        validity = str(self.validity)
        if validity not in _VALID_TOPOLOGY_VALIDITY:
            raise ValueError(f"unsupported topology validity: {self.validity!r}")
        explorer_usability = str(self.explorer_usability)
        if explorer_usability not in _VALID_EXPLORER_USABILITY:
            raise ValueError(
                f"unsupported explorer usability: {self.explorer_usability!r}"
            )
        rigid_playability = str(self.rigid_playability)
        if rigid_playability not in _VALID_RIGID_PLAYABILITY:
            raise ValueError(
                f"unsupported rigid playability: {self.rigid_playability!r}"
            )
        self.status = status
        self.validity = validity
        self.explorer_usability = explorer_usability
        self.rigid_playability = rigid_playability
        self.summary = str(self.summary)
        self.validity_reason = str(self.validity_reason)
        self.explorer_reason = str(self.explorer_reason)
        self.rigid_reason = str(self.rigid_reason)
        self.warnings = tuple(str(entry) for entry in self.warnings)
        self.errors = tuple(str(entry) for entry in self.errors)
        self.recommended_next_preset = (
            None
            if self.recommended_next_preset is None
            else str(self.recommended_next_preset)
        )


@dataclass
class TopologyPlaygroundPresetSelection:
    preset_id: str | None = None
    label: str | None = None
    description: str = ""
    source: PresetSource = PRESET_SOURCE_CUSTOM
    unsafe: bool = False

    def __post_init__(self) -> None:
        source = str(self.source)
        if source not in _VALID_PRESET_SOURCES:
            raise ValueError(f"unsupported preset source: {self.source!r}")
        self.preset_id = None if self.preset_id is None else str(self.preset_id)
        self.label = None if self.label is None else str(self.label)
        self.description = str(self.description)
        self.source = source
        self.unsafe = bool(self.unsafe)


@dataclass
class TopologyPlaygroundPresetMetadata:
    topology_preset: TopologyPlaygroundPresetSelection = field(
        default_factory=TopologyPlaygroundPresetSelection
    )
    explorer_preset: TopologyPlaygroundPresetSelection = field(
        default_factory=TopologyPlaygroundPresetSelection
    )


@dataclass(frozen=True)
class TopologyPlaygroundCanonicalOwnershipState:
    dimension: int
    axis_sizes: Coord
    topology_config: TopologyPlaygroundTopologyConfig
    launch_settings: TopologyPlaygroundLaunchSettings
    playability_analysis: TopologyPlaygroundPlayabilityAnalysis
    preset_metadata: TopologyPlaygroundPresetMetadata
    dirty: bool


@dataclass(frozen=True)
class TopologyPlaygroundEditorOwnershipState:
    workspace: TopologyWorkspace
    probe_state: TopologyPlaygroundProbeState
    selected_boundary: BoundaryRef | None
    selected_gluing: str | None
    active_tool: str


@dataclass(frozen=True)
class TopologyPlaygroundInspectorOwnershipState:
    probe_state: TopologyPlaygroundProbeState


@dataclass(frozen=True)
class TopologyPlaygroundSandboxOwnershipState:
    workspace: TopologyWorkspace
    sandbox_piece_state: TopologyPlaygroundSandboxPieceState


@dataclass(frozen=True)
class TopologyPlaygroundDerivedOwnershipState:
    transport_policy: TopologyPlaygroundTransportPolicy
    gravity_mode: TopologyPlaygroundGravityMode


@dataclass
class TopologyPlaygroundState:
    dimension: int
    axis_sizes: Coord
    topology_config: TopologyPlaygroundTopologyConfig
    selected_boundary: BoundaryRef | None = None
    selected_gluing: str | None = None
    active_tool: str = TOOL_EDIT
    editor_tool: str = TOOL_EDIT
    probe_state: TopologyPlaygroundProbeState = field(
        default_factory=TopologyPlaygroundProbeState
    )
    sandbox_piece_state: TopologyPlaygroundSandboxPieceState = field(
        default_factory=TopologyPlaygroundSandboxPieceState
    )
    launch_settings: TopologyPlaygroundLaunchSettings = field(
        default_factory=TopologyPlaygroundLaunchSettings
    )
    transport_policy: TopologyPlaygroundTransportPolicy | None = None
    gravity_mode: TopologyPlaygroundGravityMode | None = None
    playability_analysis: TopologyPlaygroundPlayabilityAnalysis = field(
        default_factory=TopologyPlaygroundPlayabilityAnalysis
    )
    preset_metadata: TopologyPlaygroundPresetMetadata = field(
        default_factory=TopologyPlaygroundPresetMetadata
    )
    dirty: bool = False

    def __post_init__(self) -> None:
        dimension = _normalize_dimension(self.dimension)
        axis_sizes = _normalize_axis_sizes(dimension, self.axis_sizes)
        self.dimension = dimension
        self.axis_sizes = axis_sizes
        self.topology_config.normalize(dimension=dimension)
        if (
            self.selected_boundary is not None
            and self.selected_boundary.dimension != dimension
        ):
            raise ValueError("selected_boundary dimension must match playground state")
        self.selected_gluing = (
            None if self.selected_gluing is None else str(self.selected_gluing)
        )
        self.active_tool = _normalize_active_tool(self.active_tool)
        self.editor_tool = _normalize_editor_tool(self.editor_tool)
        if self.active_tool not in TOPOLOGY_PLAYGROUND_TOOLS:
            raise ValueError(
                f"unsupported topology playground tool: {self.active_tool}"
            )
        if workspace_for_tool(self.active_tool) == WORKSPACE_EDITOR:
            self.editor_tool = self.active_tool
        if self.gravity_mode is None:
            self.gravity_mode = default_gravity_mode_for_gameplay(
                self.topology_config.gameplay_mode
            )
        self.gravity_mode.normalize(dimension=dimension)
        if self.transport_policy is None:
            self.transport_policy = build_transport_policy(
                dimension=dimension,
                axis_sizes=axis_sizes,
                topology_config=self.topology_config,
                gravity_mode=self.gravity_mode,
            )
        self.transport_policy.normalize(
            dimension=dimension,
            axis_sizes=axis_sizes,
            gravity_axis=self.gravity_mode.gravity_axis,
        )
        self.probe_state.normalize(dimension=dimension, axis_sizes=axis_sizes)
        self.sandbox_piece_state.normalize(
            dimension=dimension,
            axis_sizes=axis_sizes,
        )
        self.dirty = bool(self.dirty)

    @property
    def gameplay_mode(self) -> str:
        return self.topology_config.gameplay_mode

    @property
    def explorer_profile(self) -> ExplorerTopologyProfile:
        assert self.topology_config.explorer_profile is not None
        return self.topology_config.explorer_profile

    @property
    def active_workspace(self) -> TopologyWorkspace:
        return workspace_for_tool(self.active_tool)

    @property
    def canonical_state(self) -> TopologyPlaygroundCanonicalOwnershipState:
        return TopologyPlaygroundCanonicalOwnershipState(
            dimension=self.dimension,
            axis_sizes=self.axis_sizes,
            topology_config=self.topology_config,
            launch_settings=self.launch_settings,
            playability_analysis=self.playability_analysis,
            preset_metadata=self.preset_metadata,
            dirty=self.dirty,
        )

    @property
    def editor_state(self) -> TopologyPlaygroundEditorOwnershipState:
        return TopologyPlaygroundEditorOwnershipState(
            workspace=WORKSPACE_EDITOR,
            probe_state=self.probe_state,
            selected_boundary=self.selected_boundary,
            selected_gluing=self.selected_gluing,
            active_tool=self.editor_tool,
        )

    @property
    def inspector_state(self) -> TopologyPlaygroundInspectorOwnershipState:
        return TopologyPlaygroundInspectorOwnershipState(
            probe_state=self.probe_state,
        )

    @property
    def sandbox_state(self) -> TopologyPlaygroundSandboxOwnershipState:
        return TopologyPlaygroundSandboxOwnershipState(
            workspace=WORKSPACE_SANDBOX,
            sandbox_piece_state=self.sandbox_piece_state,
        )

    @property
    def derived_state(self) -> TopologyPlaygroundDerivedOwnershipState:
        assert self.transport_policy is not None
        assert self.gravity_mode is not None
        return TopologyPlaygroundDerivedOwnershipState(
            transport_policy=self.transport_policy,
            gravity_mode=self.gravity_mode,
        )


def default_gravity_mode_for_gameplay(
    gameplay_mode: str,
    *,
    gravity_axis: int = 1,
) -> TopologyPlaygroundGravityMode:
    mode = str(gameplay_mode)
    if mode == GAMEPLAY_MODE_NORMAL:
        return TopologyPlaygroundGravityMode(
            name=GRAVITY_MODE_FALLING,
            gravity_axis=gravity_axis,
            tick_enabled=True,
            locking_enabled=True,
            wrap_gravity_axis=False,
        )
    return TopologyPlaygroundGravityMode(
        name=GRAVITY_MODE_EXPLORATION,
        gravity_axis=gravity_axis,
        tick_enabled=False,
        locking_enabled=False,
        wrap_gravity_axis=True,
    )


def build_transport_policy(
    *,
    dimension: int,
    axis_sizes: Coord,
    topology_config: TopologyPlaygroundTopologyConfig,
    gravity_mode: TopologyPlaygroundGravityMode,
) -> TopologyPlaygroundTransportPolicy:
    base_policy = TopologyPolicy(
        dims=axis_sizes,
        gravity_axis=gravity_mode.gravity_axis,
        mode=topology_config.legacy_profile.topology_mode,
        wrap_gravity_axis=gravity_mode.wrap_gravity_axis,
        edge_rules=topology_config.legacy_profile.edge_rules,
    )
    owner: TransportOwner
    explorer_profile: ExplorerTopologyProfile | None = None
    if topology_config.gameplay_mode == GAMEPLAY_MODE_EXPLORER:
        owner = TRANSPORT_OWNER_EXPLORER
        explorer_profile = topology_config.explorer_profile
    else:
        owner = TRANSPORT_OWNER_LEGACY
    return TopologyPlaygroundTransportPolicy(
        owner=owner,
        base_policy=base_policy,
        explorer_profile=explorer_profile,
        allow_above_gravity=not gravity_mode.tick_enabled,
    )


def default_topology_playground_state(
    *,
    dimension: int,
    axis_sizes: Coord | None = None,
    gameplay_mode: str = GAMEPLAY_MODE_EXPLORER,
    gravity_axis: int = 1,
    active_tool: str = TOOL_EDIT,
    editor_tool: str = TOOL_EDIT,
) -> TopologyPlaygroundState:
    normalized_dimension = _normalize_dimension(dimension)
    if not (0 <= int(gravity_axis) < normalized_dimension):
        raise ValueError("gravity_axis must exist in the active dimension")
    resolved_axis_sizes = (
        tuple(4 for _ in range(normalized_dimension))
        if axis_sizes is None
        else _normalize_axis_sizes(normalized_dimension, axis_sizes)
    )
    legacy_profile = default_topology_profile_state(
        dimension=normalized_dimension,
        gravity_axis=int(gravity_axis),
        gameplay_mode=gameplay_mode,
    )
    topology_config = TopologyPlaygroundTopologyConfig(
        legacy_profile=legacy_profile,
        explorer_profile=ExplorerTopologyProfile(
            dimension=normalized_dimension,
            gluings=(),
        ),
    )
    preset_metadata = TopologyPlaygroundPresetMetadata(
        topology_preset=TopologyPlaygroundPresetSelection(
            preset_id=legacy_profile.preset_id,
            source=PRESET_SOURCE_DESIGNER,
        ),
        explorer_preset=TopologyPlaygroundPresetSelection(
            source=PRESET_SOURCE_CUSTOM,
        ),
    )
    return TopologyPlaygroundState(
        dimension=normalized_dimension,
        axis_sizes=resolved_axis_sizes,
        topology_config=topology_config,
        active_tool=_normalize_active_tool(active_tool),
        editor_tool=(
            _normalize_active_tool(active_tool)
            if workspace_for_tool(active_tool) == WORKSPACE_EDITOR
            else _normalize_editor_tool(editor_tool)
        ),
        preset_metadata=preset_metadata,
    )


def canonical_tool_name(tool: str) -> str:
    try:
        return _CANONICAL_TOOL_BY_NAME[str(tool)]
    except KeyError as exc:
        raise ValueError(f"unsupported topology playground tool: {tool}") from exc


def _normalize_active_tool(tool: str) -> str:
    return canonical_tool_name(tool)


def _normalize_editor_tool(tool: str) -> str:
    normalized_tool = _normalize_active_tool(tool)
    if normalized_tool not in _EDITOR_TOOLS:
        raise ValueError(f"unsupported editor tool: {tool}")
    return normalized_tool


def workspace_for_tool(tool: str) -> TopologyWorkspace:
    normalized_tool = _normalize_active_tool(tool)
    return _WORKSPACE_BY_TOOL[normalized_tool]


__all__ = [
    "EXPLORER_USABILITY_BLOCKED",
    "EXPLORER_USABILITY_CELLWISE",
    "EXPLORER_USABILITY_UNKNOWN",
    "GRAVITY_MODE_EXPLORATION",
    "GRAVITY_MODE_FALLING",
    "PLAYABILITY_STATUS_ANALYZING",
    "PLAYABILITY_STATUS_BLOCKED",
    "PLAYABILITY_STATUS_PLAYABLE",
    "PLAYABILITY_STATUS_UNKNOWN",
    "PLAYABILITY_STATUS_WARNING",
    "PRESET_SOURCE_CUSTOM",
    "PRESET_SOURCE_DESIGNER",
    "PRESET_SOURCE_EXPLORER",
    "PRESET_SOURCE_FALLBACK",
    "RIGID_PLAYABILITY_BLOCKED",
    "RIGID_PLAY_MODE_AUTO",
    "RIGID_PLAY_MODE_OFF",
    "RIGID_PLAY_MODE_ON",
    "RIGID_PLAYABILITY_PLAYABLE",
    "RIGID_PLAYABILITY_UNKNOWN",
    "TOOL_CREATE",
    "TOOL_EDIT",
    "TOOL_NAVIGATE",
    "TOOL_PLAY",
    "TOOL_PROBE",
    "TOOL_SANDBOX",
    "TOPOLOGY_PLAYGROUND_WORKSPACES",
    "TOPOLOGY_VALIDITY_INVALID",
    "TOPOLOGY_VALIDITY_UNKNOWN",
    "TOPOLOGY_VALIDITY_VALID",
    "TOPOLOGY_PLAYGROUND_TOOLS",
    "TRANSPORT_OWNER_EXPLORER",
    "TRANSPORT_OWNER_LEGACY",
    "TopologyPlaygroundGluingDraft",
    "TopologyPlaygroundGravityMode",
    "TopologyPlaygroundLaunchSettings",
    "TopologyPlaygroundCanonicalOwnershipState",
    "TopologyPlaygroundDerivedOwnershipState",
    "TopologyPlaygroundEditorOwnershipState",
    "TopologyPlaygroundInspectorOwnershipState",
    "TopologyPlaygroundSandboxOwnershipState",
    "TopologyPlaygroundMovementSummary",
    "TopologyPlaygroundPlayabilityAnalysis",
    "TopologyPlaygroundPresetMetadata",
    "TopologyPlaygroundPresetSelection",
    "TopologyPlaygroundProbeState",
    "TopologyPlaygroundSandboxPieceState",
    "TopologyPlaygroundState",
    "TopologyPlaygroundTopologyConfig",
    "TopologyPlaygroundTransportPolicy",
    "TopologyWorkspace",
    "WORKSPACE_EDITOR",
    "WORKSPACE_PLAY",
    "WORKSPACE_SANDBOX",
    "build_transport_policy",
    "canonical_tool_name",
    "default_gravity_mode_for_gameplay",
    "default_topology_playground_state",
    "workspace_for_tool",
]
