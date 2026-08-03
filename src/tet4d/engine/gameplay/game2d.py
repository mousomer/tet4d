# tetris_nd/game2d.py
import random
from dataclasses import dataclass, field

from ..core.model import Action, BoardND, GameConfig2DCoreView, GameState2DCoreView
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
from ..core.step.reducer import step_2d as core_step_2d
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
    require_non_negative_integral,
    require_string,
)
from ..topology_explorer.transport_resolver import (
    ExplorerTransportResolver,
    build_explorer_transport_resolver,
)
from .explorer_movement_policy import explorer_movement_policy_from_rigid_play_enabled
from .explorer_runtime_2d import (
    move_piece_via_explorer_glue_2d,
    piece_cells_in_bounds_2d,
)
from .lock_flow import apply_current_piece_lock_flow
from .pieces2d import (
    PIECE_SET_2D_CLASSIC,
    ActivePiece2D,
    PieceShape2D,
    get_piece_bag_2d,
    normalize_piece_set_2d,
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


def _normalize_explorer_transport_2d(config) -> ExplorerTransportResolver | None:
    profile = config.explorer_topology_profile
    transport = config.explorer_transport
    if profile is not None and profile.dimension != 2:
        raise ValueError("explorer_topology_profile dimension must match 2D")
    if transport is not None and profile is None:
        raise ValueError("explorer_transport requires explorer_topology_profile")
    if profile is None:
        return transport
    expected_dims = (config.width, config.height)
    if transport is None:
        return build_explorer_transport_resolver(profile, expected_dims)
    if transport.dims != expected_dims:
        raise ValueError("explorer_transport dims must match 2D board size")
    return transport


def _resolve_explorer_rigid_play_enabled_2d(config) -> bool | None:
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
        dims=(config.width, config.height),
        resolver=config.explorer_transport,
    )


def _uses_explorer_piece_transport_2d(config) -> bool:
    return config.explorer_topology_profile is not None


def _explorer_movement_policy_2d(config) -> str:
    if bool(config.exploration_mode):
        return explorer_movement_policy_from_rigid_play_enabled(False)
    return explorer_movement_policy_from_rigid_play_enabled(
        config.explorer_rigid_play_enabled
    )


def _piece_cells_in_play_bounds_2d(
    piece: ActivePiece2D,
    *,
    width: int,
    height: int,
) -> tuple[tuple[int, int], ...] | None:
    cells = tuple(piece.cells())
    if any(x < 0 or x >= width or y >= height for x, y in cells):
        return None
    return cells


def _piece_has_cells_above_gravity_2d(piece: ActivePiece2D) -> bool:
    return any(int(y) < 0 for _x, y in piece.cells())


@dataclass
class GameConfig:
    width: int = 10
    height: int = 20
    gravity_axis: int = 1  # for 2D, dims=(width, height), so y-axis
    speed_level: int = 1  # 1..10, used by frontend to pick gravity speed
    topology_mode: str = TOPOLOGY_BOUNDED
    wrap_gravity_axis: bool = False
    topology_edge_rules: tuple[tuple[str, str], ...] | None = None
    piece_set: str = PIECE_SET_2D_CLASSIC
    kick_level: str = "off"
    random_cell_count: int = 4
    challenge_layers: int = 0
    lock_piece_points: int = 5
    exploration_mode: bool = False
    explorer_topology_profile: ExplorerTopologyProfile | None = None
    explorer_transport: ExplorerTransportResolver | None = None
    explorer_rigid_play_enabled: bool | None = None
    rng_mode: str = RNG_MODE_FIXED_SEED
    rng_seed: int = 1337

    def __post_init__(self):
        self.width = require_non_negative_integral(self.width, "width")
        self.height = require_non_negative_integral(self.height, "height")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be > 0")
        self.gravity_axis = require_bounded_integral(
            self.gravity_axis,
            "gravity_axis",
            minimum=0,
            maximum=1,
        )
        # 2D mode is defined as gravity along y (axis 1), clearing full x-rows.
        if self.gravity_axis != 1:
            raise ValueError("2D mode requires gravity_axis=1 (y-axis)")
        self.speed_level = require_bounded_integral(
            self.speed_level,
            "speed_level",
            minimum=1,
            maximum=10,
        )
        if not (1 <= self.speed_level <= 10):
            raise ValueError("speed_level must be in [1, 10]")
        self.piece_set = normalize_piece_set_2d(
            require_string(self.piece_set, "piece_set")
        )
        kick_level = require_string(self.kick_level, "kick_level").strip().lower()
        if kick_level not in kick_level_names():
            raise ValueError(f"unsupported kick level: {self.kick_level!r}")
        self.kick_level = normalize_kick_level_name(kick_level)
        self.random_cell_count = require_bounded_integral(
            self.random_cell_count,
            "random_cell_count",
            minimum=3,
            maximum=8,
        )
        if not (3 <= self.random_cell_count <= 8):
            raise ValueError("random_cell_count must be in [3, 8]")
        self.challenge_layers = require_non_negative_integral(
            self.challenge_layers, "challenge_layers"
        )
        self.lock_piece_points = require_non_negative_integral(
            self.lock_piece_points, "lock_piece_points"
        )
        self.exploration_mode = require_exact_bool(
            self.exploration_mode, "exploration_mode"
        )
        self.wrap_gravity_axis = require_exact_bool(
            self.wrap_gravity_axis, "wrap_gravity_axis"
        )
        if self.explorer_rigid_play_enabled is not None:
            self.explorer_rigid_play_enabled = require_exact_bool(
                self.explorer_rigid_play_enabled,
                "explorer_rigid_play_enabled",
            )
        if self.explorer_topology_profile is not None:
            self.explorer_topology_profile = require_instance(
                self.explorer_topology_profile,
                "explorer_topology_profile",
                ExplorerTopologyProfile,
            )
        if self.explorer_transport is not None:
            self.explorer_transport = require_instance(
                self.explorer_transport,
                "explorer_transport",
                ExplorerTransportResolver,
            )
        self.topology_mode = normalize_topology_mode(
            require_string(self.topology_mode, "topology_mode")
        )
        if self.topology_edge_rules is not None:
            self.topology_edge_rules = normalize_edge_rules(
                self.topology_edge_rules,
                axis_count=2,
                gravity_axis=self.gravity_axis,
                wrap_gravity_axis=self.wrap_gravity_axis,
            )
        self.explorer_transport = _normalize_explorer_transport_2d(self)
        self.explorer_rigid_play_enabled = _resolve_explorer_rigid_play_enabled_2d(self)
        self.rng_mode = normalize_rng_mode(require_string(self.rng_mode, "rng_mode"))
        self.rng_seed = require_bounded_integral(
            self.rng_seed,
            "rng_seed",
            minimum=0,
            maximum=999_999_999,
        )

    def topology_policy(self) -> TopologyPolicy:
        return TopologyPolicy(
            dims=(self.width, self.height),
            gravity_axis=self.gravity_axis,
            mode=self.topology_mode,
            wrap_gravity_axis=self.wrap_gravity_axis,
            edge_rules=self.topology_edge_rules,
        )

    def to_core_view(self) -> GameConfig2DCoreView:
        return GameConfig2DCoreView(
            width=self.width,
            height=self.height,
            gravity_axis=self.gravity_axis,
            speed_level=self.speed_level,
            topology_mode=self.topology_mode,
            wrap_gravity_axis=self.wrap_gravity_axis,
            piece_set=self.piece_set,
            kick_level=self.kick_level,
            random_cell_count=self.random_cell_count,
            challenge_layers=self.challenge_layers,
            lock_piece_points=self.lock_piece_points,
            exploration_mode=self.exploration_mode,
        )


@dataclass
class GameState:
    config: GameConfig
    board: BoardND
    topology_policy: TopologyPolicy = field(init=False, repr=False)
    current_piece: ActivePiece2D | None = None
    next_bag: list[PieceShape2D] = field(default_factory=list)
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

    def __post_init__(self):
        self.topology_policy = self.config.topology_policy()
        if self.board is None:
            self.board = BoardND((self.config.width, self.config.height))
        if not self.next_bag:
            self._refill_bag()
        if self.current_piece is None:
            self.spawn_new_piece()

    # --- Piece bag handling ---

    def _refill_bag(self):
        """Refill the 7-bag for random piece selection."""
        generated = get_piece_bag_2d(
            self.config.piece_set,
            rng=self.rng,
            random_cell_count=self.config.random_cell_count,
            board_dims=(self.config.width, self.config.height),
        )
        self.next_bag = [shape for shape in generated if self._shape_fits_spawn(shape)]
        if not self.next_bag:
            # Fallback to a stable baseline bag if selected set cannot spawn on this board.
            self.next_bag = [
                shape
                for shape in get_piece_bag_2d(
                    PIECE_SET_2D_CLASSIC,
                    rng=self.rng,
                    board_dims=(self.config.width, self.config.height),
                )
                if self._shape_fits_spawn(shape)
            ]
        self.rng.shuffle(self.next_bag)

    def draw_next_piece_shape(self) -> PieceShape2D:
        if not self.next_bag:
            self._refill_bag()
        return self.next_bag.pop()

    # --- Piece spawning & validation ---

    def spawn_new_piece(self):
        """
        Spawn a new piece at the top center.
        We allow negative y so pieces can start above the visible board.
        """
        shape = self.draw_next_piece_shape()
        min_x = min(block[0] for block in shape.blocks)
        max_x = max(block[0] for block in shape.blocks)
        span_x = max_x - min_x + 1
        spawn_x = ((self.config.width - span_x) // 2) - min_x
        if self.config.exploration_mode:
            min_y = min(block[1] for block in shape.blocks)
            max_y = max(block[1] for block in shape.blocks)
            span_y = max_y - min_y + 1
            spawn_y = ((self.config.height - span_y) // 2) - min_y
        else:
            spawn_y = -2  # above the visible area
        candidate = ActivePiece2D(shape, (spawn_x, spawn_y), rotation=0)
        install_spawn_candidate(self, candidate, can_exist=self._can_exist)

    def _shape_fits_spawn(self, shape: PieceShape2D) -> bool:
        if not shape.blocks:
            return False
        min_x = min(block[0] for block in shape.blocks)
        max_x = max(block[0] for block in shape.blocks)
        span_x = max_x - min_x + 1
        min_y = min(block[1] for block in shape.blocks)
        max_y = max(block[1] for block in shape.blocks)
        span_y = max_y - min_y + 1
        return span_x <= self.config.width and span_y <= self.config.height

    def consume_translation_animation_hint(self) -> bool:
        pending = bool(self._pending_translation_animation)
        self._pending_translation_animation = False
        return pending

    def _mapped_piece_cells(
        self, piece: ActivePiece2D
    ) -> tuple[tuple[int, int], ...] | None:
        if self.config.exploration_mode and _uses_explorer_piece_transport_2d(
            self.config
        ):
            return piece_cells_in_bounds_2d(
                piece,
                dims=(self.config.width, self.config.height),
            )
        if _uses_explorer_piece_transport_2d(self.config):
            return _piece_cells_in_play_bounds_2d(
                piece,
                width=self.config.width,
                height=self.config.height,
            )
        mapped = map_piece_cells(
            self.topology_policy,
            piece.cells(),
            allow_above_gravity=True,
        )
        if mapped is None:
            return None
        return tuple((coord[0], coord[1]) for coord in mapped)

    def mapped_piece_cells_for_piece(
        self,
        piece: ActivePiece2D,
        *,
        include_above: bool = True,
    ) -> tuple[tuple[int, int], ...] | None:
        mapped = self._mapped_piece_cells(piece)
        if mapped is None or include_above:
            return mapped
        return tuple(coord for coord in mapped if coord[1] >= 0)

    def current_piece_cells_mapped(
        self, *, include_above: bool = False
    ) -> tuple[tuple[int, int], ...]:
        if self.current_piece is None:
            return ()
        mapped = self.mapped_piece_cells_for_piece(
            self.current_piece, include_above=include_above
        )
        if mapped is None:
            return ()
        return mapped

    def _placement_ignore_cells(
        self,
        *,
        allow_self_overlap: bool = False,
    ) -> tuple[tuple[int, int], ...]:
        if not allow_self_overlap or self.current_piece is None:
            return ()
        return self.current_piece_cells_mapped(include_above=True)

    def piece_pose_legal(
        self,
        piece: ActivePiece2D,
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

    def _can_exist_after_motion(self, piece: ActivePiece2D) -> bool:
        return self.piece_pose_legal(piece, allow_self_overlap=True)

    def _try_commit_candidate_piece(self, piece: ActivePiece2D) -> bool:
        return commit_piece_if_legal(
            self,
            piece,
            self._mapped_piece_cells(piece),
            self.board.cells,
            ignore_cells=self._placement_ignore_cells(allow_self_overlap=True),
        )

    def _can_exist(self, piece: ActivePiece2D) -> bool:
        """Compatibility wrapper over the shared placement validator."""
        return self.piece_pose_legal(piece)

    def lock_current_piece(self) -> int:
        """
        Lock current piece into the board and clear any full lines.
        Returns number of cleared lines.
        """
        if self.current_piece is None:
            return 0
        if self.config.exploration_mode:
            return 0

        mapped_cells = self._mapped_piece_cells(self.current_piece)
        return apply_current_piece_lock_flow(
            self,
            mapped_cells=mapped_cells,
            dims=(self.config.width, self.config.height),
            gravity_axis=self.config.gravity_axis,
        )

    # --- Movement / rotation helpers ---

    def _explorer_move_for_intent(
        self,
        *,
        dx: int,
        dy: int,
        intent: str,
    ) -> ActivePiece2D | None:
        if self.current_piece is None:
            return None
        if self.config.explorer_transport is None:
            raise ValueError(
                "explorer transport must exist when explorer topology is active"
            )
        if is_drop_intent(intent):
            if (dx, dy) != (0, 1):
                raise ValueError("drop intents must use the configured gravity step")
            step_result = self.config.explorer_transport.resolve_piece_step(
                self.current_piece.cells(),
                MoveStep(axis=self.config.gravity_axis, delta=1),
            )
            if crosses_gravity_seam(
                step_result,
                gravity_axis=self.config.gravity_axis,
            ):
                return None
        return move_piece_via_explorer_glue_2d(
            self.current_piece,
            transport=self.config.explorer_transport,
            dx=dx,
            dy=dy,
            movement_policy=_explorer_movement_policy_2d(self.config),
        )

    def _try_move_with_intent(
        self,
        dx: int,
        dy: int,
        *,
        intent: str,
        animate_translation: bool = False,
    ) -> bool:
        if self.current_piece is None:
            return False
        if _uses_explorer_piece_transport_2d(
            self.config
        ) and not _piece_has_cells_above_gravity_2d(self.current_piece):
            moved = self._explorer_move_for_intent(
                dx=dx,
                dy=dy,
                intent=intent,
            )
            if moved is None:
                return False
            committed = self._try_commit_candidate_piece(moved)
            if committed and animate_translation:
                self._pending_translation_animation = True
            return committed
        moved = self._try_commit_candidate_piece(self.current_piece.moved(dx, dy))
        if moved and animate_translation:
            self._pending_translation_animation = True
        return moved

    def try_move(self, dx: int, dy: int, *, animate_translation: bool = False) -> bool:
        return self._try_move_with_intent(
            dx,
            dy,
            intent=TRANSLATION_INTENT,
            animate_translation=animate_translation,
        )

    def try_soft_drop(self) -> bool:
        return self._try_move_with_intent(0, 1, intent=SOFT_DROP_INTENT)

    def try_gravity_step(self) -> bool:
        return self._try_move_with_intent(0, 1, intent=GRAVITY_INTENT)

    def try_rotate(self, delta_steps: int):
        if self.current_piece is None:
            return
        rotated = self.current_piece.rotated(delta_steps)
        resolve_and_commit_rotated_piece(
            rotated,
            ndim=2,
            axis_a=0,
            axis_b=self.config.gravity_axis,
            gravity_axis=self.config.gravity_axis,
            kick_level=self.config.kick_level,
            plane_offsets_for_level=rotation_kick_candidate_offsets,
            move_piece=lambda piece, vector: piece.moved(
                int(vector[0]), int(vector[1])
            ),
            can_place=self._can_exist_after_motion,
            commit_piece=self._try_commit_candidate_piece,
        )

    def hard_drop(self):
        run_hard_drop(
            self,
            try_advance=lambda: self._try_move_with_intent(
                0,
                1,
                intent=HARD_DROP_INTENT,
            ),
        )

    def step_gravity(self) -> None:
        if self.config.exploration_mode or self.current_piece is None:
            return
        advance_or_lock_and_respawn(
            self,
            try_advance=self.try_gravity_step,
        )

    # --- Main step function ---

    def step(self, action: Action = Action.NONE):
        """Advance the game by one tick with the given player action."""
        core_step_2d(self, action)

    def to_core_view(self) -> GameState2DCoreView:
        return GameState2DCoreView(
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
