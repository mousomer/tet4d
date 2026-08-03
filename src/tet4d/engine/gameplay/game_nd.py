# tetris_nd/game_nd.py
import random
from collections.abc import Sequence
from dataclasses import dataclass, field

from ..core.model import BoardND, Coord, GameConfigNDCoreView, GameStateNDCoreView
from ..core.rng import RNG_MODE_FIXED_SEED, normalize_rng_mode
from ..core.rotation_kicks import resolve_and_commit_rotated_piece
from ..core.rules.lifecycle import (
    advance_or_lock_and_respawn,
    install_spawn_candidate,
    run_hard_drop,
)
from ..core.rules.piece_placement import (
    commit_piece_if_legal,
    piece_placement_is_legal,
)
from ..core.step.reducer import step_nd as core_step_nd
from ..runtime.runtime_config import (
    kick_level_names,
    normalize_kick_level_name,
    rotation_kick_candidate_offsets,
)
from ..runtime.score_analyzer import new_analysis_session_id
from ..runtime.topology_playability_signal import resolve_rigid_play_enabled
from ..topology_explorer import ExplorerTopologyProfile, MoveStep
from ..topology_explorer.domain_validation import (
    require_bounded_integral,
    require_exact_bool,
    require_instance,
    require_integral_sequence,
    require_non_negative_integral,
    require_string,
)
from ..topology_explorer.transport_resolver import (
    ExplorerTransportFrameTransform,
    ExplorerTransportResolver,
    build_explorer_transport_resolver,
)
from .explorer_movement_policy import explorer_movement_policy_from_rigid_play_enabled
from .explorer_runtime_nd import (
    move_piece_via_explorer_glue_with_frame,
    piece_cells_in_bounds,
)
from .lock_flow import apply_current_piece_lock_flow
from .pieces_nd import (
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_STANDARD,
    ActivePieceND,
    PieceShapeND,
    get_piece_shapes_nd,
    normalize_piece_set_4d,  # backward-compatible parameter support
    normalize_piece_set_for_dimension,
)
from .play_move_intents import (
    GRAVITY_INTENT,
    HARD_DROP_INTENT,
    SOFT_DROP_INTENT,
    TRANSLATION_INTENT,
    crosses_gravity_seam,
    is_drop_intent,
)
from .topology import (
    TOPOLOGY_BOUNDED,
    TopologyPolicy,
    map_piece_cells,
    normalize_edge_rules,
    normalize_topology_mode,
)


def _coerce_rng_seed(value: object) -> int:
    return require_bounded_integral(
        value,
        "rng_seed",
        minimum=0,
        maximum=999_999_999,
    )


def _resolve_piece_set_id(
    *,
    ndim: int,
    piece_set_id: str | None,
    piece_set_4d: str,
) -> str:
    selected_piece_set = piece_set_id
    if selected_piece_set is None and ndim >= 4:
        selected_piece_set = normalize_piece_set_4d(piece_set_4d)
    if selected_piece_set is None and ndim == 3:
        selected_piece_set = PIECE_SET_3D_STANDARD
    return normalize_piece_set_for_dimension(ndim, selected_piece_set)


def _normalize_explorer_transport_nd(
    config,
    *,
    ndim: int,
) -> ExplorerTransportResolver | None:
    profile = config.explorer_topology_profile
    transport = config.explorer_transport
    if profile is not None and profile.dimension != ndim:
        raise ValueError("explorer_topology_profile dimension must match dims")
    if transport is not None and profile is None:
        raise ValueError("explorer_transport requires explorer_topology_profile")
    if profile is None:
        return transport
    expected_dims = tuple(int(value) for value in config.dims)
    if transport is None:
        return build_explorer_transport_resolver(profile, expected_dims)
    if transport.dims != expected_dims:
        raise ValueError("explorer_transport dims must match board dims")
    return transport


def _resolve_explorer_rigid_play_enabled_nd(config) -> bool | None:
    enabled = config.explorer_rigid_play_enabled
    if enabled is not None:
        return enabled
    profile = config.explorer_topology_profile
    if profile is None:
        return None
    resolver = config.explorer_transport
    if resolver is not None and not hasattr(resolver, "resolve_piece_step"):
        return True
    return resolve_rigid_play_enabled(
        profile,
        dims=tuple(int(value) for value in config.dims),
        resolver=config.explorer_transport,
    )


def _uses_explorer_piece_transport_nd(config) -> bool:
    return config.explorer_topology_profile is not None


def _piece_cells_in_play_bounds_nd(
    piece: ActivePieceND,
    *,
    dims: Coord,
    gravity_axis: int,
) -> tuple[Coord, ...] | None:
    cells = tuple(piece.cells())
    for coord in cells:
        for axis in range(len(dims)):
            value = int(coord[axis])
            if axis == int(gravity_axis):
                if value >= int(dims[axis]):
                    return None
                continue
            if value < 0 or value >= int(dims[axis]):
                return None
    return cells


def _piece_has_cells_above_gravity_nd(
    piece: ActivePieceND,
    *,
    gravity_axis: int,
) -> bool:
    return any(int(coord[int(gravity_axis)]) < 0 for coord in piece.cells())


def _explorer_movement_policy_nd(config) -> str:
    if bool(config.exploration_mode):
        return explorer_movement_policy_from_rigid_play_enabled(False)
    return explorer_movement_policy_from_rigid_play_enabled(
        config.explorer_rigid_play_enabled
    )


def _identity_piece_frame(ndim: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(range(ndim)), tuple(1 for _ in range(ndim))


def _compose_piece_frame(
    *,
    ndim: int,
    permutation: tuple[int, ...],
    signs: tuple[int, ...],
    frame_transform: ExplorerTransportFrameTransform | None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if frame_transform is None or frame_transform.is_identity_linear():
        return permutation, signs
    composed_permutation = [0] * ndim
    composed_signs = [1] * ndim
    for source_axis, intermediate_axis in enumerate(permutation):
        target_axis = int(frame_transform.permutation[intermediate_axis])
        composed_permutation[source_axis] = target_axis
        composed_signs[source_axis] = int(signs[source_axis]) * int(
            frame_transform.signs[intermediate_axis]
        )
    return tuple(composed_permutation), tuple(composed_signs)


def _normalize_game_config_nd_scalars(config) -> None:
    config.dims = require_integral_sequence(config.dims, "dims")
    if len(config.dims) < 2:
        raise ValueError("dims must have at least 2 axes")
    if any(dimension <= 0 for dimension in config.dims):
        raise ValueError("all dimensions must be > 0")
    config.gravity_axis = require_bounded_integral(
        config.gravity_axis,
        "gravity_axis",
        minimum=0,
        maximum=len(config.dims) - 1,
    )
    config.speed_level = require_bounded_integral(
        config.speed_level,
        "speed_level",
        minimum=1,
        maximum=10,
    )
    config.random_cell_count = require_bounded_integral(
        config.random_cell_count,
        "random_cell_count",
        minimum=3,
        maximum=8,
    )
    config.challenge_layers = require_non_negative_integral(
        config.challenge_layers, "challenge_layers"
    )
    config.lock_piece_points = require_non_negative_integral(
        config.lock_piece_points, "lock_piece_points"
    )
    config.rng_seed = _coerce_rng_seed(config.rng_seed)


def _normalize_game_config_nd_flags_and_explorer(config) -> None:
    config.exploration_mode = require_exact_bool(
        config.exploration_mode, "exploration_mode"
    )
    config.wrap_gravity_axis = require_exact_bool(
        config.wrap_gravity_axis, "wrap_gravity_axis"
    )
    if config.explorer_rigid_play_enabled is not None:
        config.explorer_rigid_play_enabled = require_exact_bool(
            config.explorer_rigid_play_enabled,
            "explorer_rigid_play_enabled",
        )
    if config.explorer_topology_profile is not None:
        config.explorer_topology_profile = require_instance(
            config.explorer_topology_profile,
            "explorer_topology_profile",
            ExplorerTopologyProfile,
        )
    if config.explorer_transport is not None:
        config.explorer_transport = require_instance(
            config.explorer_transport,
            "explorer_transport",
            ExplorerTransportResolver,
        )


def _normalize_game_config_nd_named_fields(config) -> None:
    config.rng_mode = normalize_rng_mode(require_string(config.rng_mode, "rng_mode"))
    config.topology_mode = normalize_topology_mode(
        require_string(config.topology_mode, "topology_mode")
    )
    if config.topology_edge_rules is not None:
        config.topology_edge_rules = normalize_edge_rules(
            config.topology_edge_rules,
            axis_count=len(config.dims),
            gravity_axis=config.gravity_axis,
            wrap_gravity_axis=config.wrap_gravity_axis,
        )
    kick_level = require_string(config.kick_level, "kick_level").strip().lower()
    if kick_level not in kick_level_names():
        raise ValueError(f"unsupported kick level: {config.kick_level!r}")
    config.kick_level = normalize_kick_level_name(kick_level)
    if config.piece_set_id is not None:
        config.piece_set_id = require_string(config.piece_set_id, "piece_set_id")
    config.piece_set_4d = require_string(config.piece_set_4d, "piece_set_4d")


@dataclass
class GameConfigND:
    dims: Coord = (10, 20, 6)
    gravity_axis: int = 1
    speed_level: int = 1  # 1..10, used by frontend timing
    topology_mode: str = TOPOLOGY_BOUNDED
    wrap_gravity_axis: bool = False
    topology_edge_rules: tuple[tuple[str, str], ...] | None = None
    explorer_topology_profile: ExplorerTopologyProfile | None = None
    explorer_transport: ExplorerTransportResolver | None = None
    explorer_rigid_play_enabled: bool | None = None
    piece_set_id: str | None = None
    piece_set_4d: str = PIECE_SET_4D_STANDARD
    kick_level: str = "off"
    random_cell_count: int = 5
    challenge_layers: int = 0
    lock_piece_points: int = 5
    exploration_mode: bool = False
    rng_mode: str = RNG_MODE_FIXED_SEED
    rng_seed: int = 1337

    def __post_init__(self) -> None:
        _normalize_game_config_nd_scalars(self)
        _normalize_game_config_nd_flags_and_explorer(self)
        _normalize_game_config_nd_named_fields(self)
        ndim = len(self.dims)
        self.explorer_transport = _normalize_explorer_transport_nd(self, ndim=ndim)
        self.explorer_rigid_play_enabled = _resolve_explorer_rigid_play_enabled_nd(self)
        self.piece_set_id = _resolve_piece_set_id(
            ndim=ndim,
            piece_set_id=self.piece_set_id,
            piece_set_4d=self.piece_set_4d,
        )
        # Keep legacy field populated for existing callers/UI labels.
        self.piece_set_4d = self.piece_set_id

    @property
    def ndim(self) -> int:
        return len(self.dims)

    def topology_policy(self) -> TopologyPolicy:
        return TopologyPolicy(
            dims=self.dims,
            gravity_axis=self.gravity_axis,
            mode=self.topology_mode,
            wrap_gravity_axis=self.wrap_gravity_axis,
            edge_rules=self.topology_edge_rules,
        )

    def to_core_view(self) -> GameConfigNDCoreView:
        return GameConfigNDCoreView(
            dims=tuple(self.dims),
            gravity_axis=self.gravity_axis,
            speed_level=self.speed_level,
            topology_mode=self.topology_mode,
            wrap_gravity_axis=self.wrap_gravity_axis,
            piece_set_id=self.piece_set_id,
            kick_level=self.kick_level,
            random_cell_count=self.random_cell_count,
            challenge_layers=self.challenge_layers,
            lock_piece_points=self.lock_piece_points,
            exploration_mode=self.exploration_mode,
        )


@dataclass
class GameStateND:
    config: GameConfigND
    board: BoardND
    topology_policy: TopologyPolicy = field(init=False, repr=False)
    current_piece: ActivePieceND | None = None
    next_bag: list[PieceShapeND] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)
    score: int = 0
    lines_cleared: int = 0
    game_over: bool = False
    score_multiplier: float = 1.0
    analysis_actor_mode: str = "human"
    analysis_bot_mode: str = "off"
    analysis_grid_mode: str = "full"
    analysis_session_id: str = field(default_factory=new_analysis_session_id)
    analysis_seq: int = 0
    last_score_analysis: dict[str, object] | None = None
    _pending_translation_animation: bool = field(default=False, init=False, repr=False)
    _piece_frame_permutation: tuple[int, ...] = field(
        default=(), init=False, repr=False
    )
    _piece_frame_signs: tuple[int, ...] = field(default=(), init=False, repr=False)

    def __post_init__(self) -> None:
        self.topology_policy = self.config.topology_policy()
        if self.board is None:
            self.board = BoardND(self.config.dims)
        if self.board.dims != self.config.dims:
            raise ValueError("board dims must match config dims")
        self._reset_piece_frame()
        if not self.next_bag:
            self._refill_bag()
        if self.current_piece is None:
            self.spawn_new_piece()

    # --- Bag and spawning ---

    def _refill_bag(self) -> None:
        attempts = 0
        while True:
            generated = get_piece_shapes_nd(
                self.config.ndim,
                piece_set_id=self.config.piece_set_id,
                random_cell_count=self.config.random_cell_count,
                rng=self.rng,
                board_dims=self.config.dims,
            )
            self.next_bag = [
                shape for shape in generated if self._shape_fits_board(shape)
            ]
            if self.next_bag:
                break
            attempts += 1
            if attempts >= 4:
                # Stable fallback for tiny boards.
                fallback_id = (
                    PIECE_SET_3D_STANDARD
                    if self.config.ndim == 3
                    else PIECE_SET_4D_STANDARD
                )
                fallback = get_piece_shapes_nd(
                    self.config.ndim,
                    piece_set_id=fallback_id,
                    rng=self.rng,
                    board_dims=self.config.dims,
                )
                self.next_bag = [
                    shape for shape in fallback if self._shape_fits_board(shape)
                ]
                if self.next_bag:
                    break
                raise RuntimeError("no spawnable pieces for current board dimensions")
        self.rng.shuffle(self.next_bag)

    def draw_next_piece_shape(self) -> PieceShapeND:
        if not self.next_bag:
            self._refill_bag()
        return self.next_bag.pop()

    def _spawn_pos_for_shape(self, shape: PieceShapeND) -> Coord:
        g = self.config.gravity_axis
        coords = [0] * self.config.ndim
        for axis in range(self.config.ndim):
            axis_values = [block[axis] for block in shape.blocks]
            min_axis = min(axis_values)
            max_axis = max(axis_values)
            if self.config.exploration_mode:
                span = max_axis - min_axis + 1
                start = (self.config.dims[axis] - span) // 2
                coords[axis] = start - min_axis
            elif axis == g:
                coords[axis] = -2 - min_axis
            else:
                span = max_axis - min_axis + 1
                start = (self.config.dims[axis] - span) // 2
                coords[axis] = start - min_axis
        return tuple(coords)

    def spawn_new_piece(self) -> None:
        shape = self.draw_next_piece_shape()
        candidate = ActivePieceND.from_shape(shape, self._spawn_pos_for_shape(shape))
        install_spawn_candidate(
            self,
            candidate,
            can_exist=self._can_exist,
            before_install=self._reset_piece_frame,
        )

    def _shape_fits_board(self, shape: PieceShapeND) -> bool:
        for axis in range(self.config.ndim):
            axis_values = [block[axis] for block in shape.blocks]
            span = max(axis_values) - min(axis_values) + 1
            if span > self.config.dims[axis]:
                return False
        return True

    def _reset_piece_frame(self) -> None:
        permutation, signs = _identity_piece_frame(self.config.ndim)
        self._piece_frame_permutation = permutation
        self._piece_frame_signs = signs

    def _compose_current_piece_frame(
        self,
        frame_transform: ExplorerTransportFrameTransform | None,
    ) -> None:
        permutation, signs = _compose_piece_frame(
            ndim=self.config.ndim,
            permutation=self._piece_frame_permutation,
            signs=self._piece_frame_signs,
            frame_transform=frame_transform,
        )
        self._piece_frame_permutation = permutation
        self._piece_frame_signs = signs

    def _mapped_piece_cells(self, piece: ActivePieceND) -> tuple[Coord, ...] | None:
        if self.config.exploration_mode and _uses_explorer_piece_transport_nd(
            self.config
        ):
            return piece_cells_in_bounds(piece, dims=self.config.dims)
        if _uses_explorer_piece_transport_nd(self.config):
            return _piece_cells_in_play_bounds_nd(
                piece,
                dims=self.config.dims,
                gravity_axis=self.config.gravity_axis,
            )
        return map_piece_cells(
            self.topology_policy,
            piece.cells(),
            allow_above_gravity=True,
        )

    def current_piece_cells_mapped(
        self, *, include_above: bool = False
    ) -> tuple[Coord, ...]:
        if self.current_piece is None:
            return ()
        mapped = self._mapped_piece_cells(self.current_piece)
        if mapped is None:
            return ()
        if include_above:
            return mapped
        gravity_axis = self.config.gravity_axis
        return tuple(coord for coord in mapped if coord[gravity_axis] >= 0)

    def consume_translation_animation_hint(self) -> bool:
        pending = bool(self._pending_translation_animation)
        self._pending_translation_animation = False
        return pending

    # --- Validation and locking ---

    def _placement_ignore_cells(
        self,
        *,
        allow_self_overlap: bool = False,
    ) -> tuple[Coord, ...]:
        if not allow_self_overlap or self.current_piece is None:
            return ()
        return self.current_piece_cells_mapped(include_above=True)

    def piece_pose_legal(
        self,
        piece: ActivePieceND,
        *,
        allow_self_overlap: bool = False,
    ) -> bool:
        return piece_placement_is_legal(
            piece,
            self._mapped_piece_cells(piece),
            self.board.cells,
            ignore_cells=self._placement_ignore_cells(
                allow_self_overlap=allow_self_overlap
            ),
        )

    def _can_exist_after_motion(self, piece: ActivePieceND) -> bool:
        return self.piece_pose_legal(piece, allow_self_overlap=True)

    def _try_commit_candidate_piece(self, piece: ActivePieceND) -> bool:
        return commit_piece_if_legal(
            self,
            piece,
            self._mapped_piece_cells(piece),
            self.board.cells,
            ignore_cells=self._placement_ignore_cells(allow_self_overlap=True),
        )

    def _can_exist(self, piece: ActivePieceND) -> bool:
        return self.piece_pose_legal(piece)

    def lock_current_piece(self) -> int:
        if self.current_piece is None:
            return 0
        if self.config.exploration_mode:
            return 0

        g = self.config.gravity_axis
        mapped_cells = self._mapped_piece_cells(self.current_piece)
        return apply_current_piece_lock_flow(
            self,
            mapped_cells=mapped_cells,
            dims=self.config.dims,
            gravity_axis=g,
        )

    # --- Movement and rotation ---

    def try_move(
        self, delta: Sequence[int], *, animate_translation: bool = False
    ) -> bool:
        if self.current_piece is None:
            return False
        if _uses_explorer_piece_transport_nd(
            self.config
        ) and not _piece_has_cells_above_gravity_nd(
            self.current_piece,
            gravity_axis=self.config.gravity_axis,
        ):
            non_zero = [
                (axis, int(value))
                for axis, value in enumerate(delta)
                if int(value) != 0
            ]
            if len(non_zero) == 1 and abs(non_zero[0][1]) == 1:
                axis, step = non_zero[0]
                return self._move_axis_with_intent(
                    axis,
                    step,
                    intent=TRANSLATION_INTENT,
                    animate_translation=animate_translation,
                )
        moved = self._try_commit_candidate_piece(self.current_piece.moved(delta))
        if moved and animate_translation:
            self._pending_translation_animation = True
        return moved

    def _explorer_move_result_for_intent(
        self,
        *,
        axis: int,
        delta: int,
        intent: str,
    ):
        if self.current_piece is None:
            return None
        if self.config.explorer_transport is None:
            raise ValueError(
                "explorer transport must exist when explorer topology is active"
            )
        if is_drop_intent(intent):
            if axis != self.config.gravity_axis or delta != 1:
                raise ValueError("drop intents must use the configured gravity step")
            step_result = self.config.explorer_transport.resolve_piece_step(
                self.current_piece.cells(),
                MoveStep(axis=axis, delta=delta),
            )
            if crosses_gravity_seam(
                step_result,
                gravity_axis=self.config.gravity_axis,
            ):
                return None
        return move_piece_via_explorer_glue_with_frame(
            self.current_piece,
            transport=self.config.explorer_transport,
            axis=axis,
            delta=delta,
            movement_policy=_explorer_movement_policy_nd(self.config),
        )

    def _move_axis_with_intent(
        self,
        axis: int,
        delta: int,
        *,
        intent: str,
        animate_translation: bool = False,
    ) -> bool:
        if not (0 <= axis < self.config.ndim):
            raise ValueError("axis out of bounds")
        if self.current_piece is None:
            return False
        if _uses_explorer_piece_transport_nd(
            self.config
        ) and not _piece_has_cells_above_gravity_nd(
            self.current_piece,
            gravity_axis=self.config.gravity_axis,
        ):
            move_result = self._explorer_move_result_for_intent(
                axis=axis,
                delta=delta,
                intent=intent,
            )
            if move_result is None:
                return False
            moved = self._try_commit_candidate_piece(move_result.piece)
            if moved and intent == TRANSLATION_INTENT:
                self._compose_current_piece_frame(move_result.frame_transform)
            if moved and animate_translation:
                self._pending_translation_animation = True
            return moved
        vector = [0] * self.config.ndim
        vector[axis] = delta
        moved = self._try_commit_candidate_piece(self.current_piece.moved(vector))
        if moved and animate_translation:
            self._pending_translation_animation = True
        return moved

    def try_move_axis(
        self, axis: int, delta: int, *, animate_translation: bool = False
    ) -> bool:
        return self._move_axis_with_intent(
            axis,
            delta,
            intent=TRANSLATION_INTENT,
            animate_translation=animate_translation,
        )

    def try_soft_drop(self) -> bool:
        return self._move_axis_with_intent(
            self.config.gravity_axis,
            1,
            intent=SOFT_DROP_INTENT,
        )

    def try_gravity_step(self) -> bool:
        return self._move_axis_with_intent(
            self.config.gravity_axis,
            1,
            intent=GRAVITY_INTENT,
        )

    def try_rotate(self, axis_a: int, axis_b: int, delta_steps: int = 1) -> bool:
        if self.current_piece is None:
            return False
        rotated = self.current_piece.rotated(axis_a, axis_b, delta_steps)
        return resolve_and_commit_rotated_piece(
            rotated,
            ndim=self.config.ndim,
            axis_a=axis_a,
            axis_b=axis_b,
            gravity_axis=self.config.gravity_axis,
            kick_level=self.config.kick_level,
            plane_offsets_for_level=rotation_kick_candidate_offsets,
            move_piece=lambda piece, delta: piece.moved(delta),
            can_place=self._can_exist_after_motion,
            commit_piece=self._try_commit_candidate_piece,
        )

    def hard_drop(self) -> None:
        run_hard_drop(
            self,
            try_advance=lambda: self._move_axis_with_intent(
                self.config.gravity_axis,
                1,
                intent=HARD_DROP_INTENT,
            ),
        )

    # --- Time step ---

    def step_gravity(self) -> None:
        if self.config.exploration_mode or self.game_over or self.current_piece is None:
            return

        advance_or_lock_and_respawn(
            self,
            try_advance=self.try_gravity_step,
        )

    def step(self) -> None:
        core_step_nd(self)

    def to_core_view(self) -> GameStateNDCoreView:
        return GameStateNDCoreView(
            config=self.config.to_core_view(),
            score=int(self.score),
            lines_cleared=int(self.lines_cleared),
            game_over=bool(self.game_over),
            board_cells=tuple(
                sorted(
                    (tuple(coord), int(color))
                    for coord, color in self.board.cells.items()
                )
            ),
            current_piece_cells=tuple(
                tuple(cell)
                for cell in self.current_piece_cells_mapped(include_above=True)
            ),
            has_current_piece=self.current_piece is not None,
        )
