# tetris_nd/game_nd.py
from dataclasses import dataclass, field
import random
from typing import List, Optional, Sequence

from ..core.model import GameConfigNDCoreView, GameStateNDCoreView
from ..core.model import BoardND
from ..core.rng import RNG_MODE_FIXED_SEED, normalize_rng_mode
from .pieces_nd import (
    ActivePieceND,
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_STANDARD,
    PieceShapeND,
    get_piece_shapes_nd,
    normalize_piece_set_for_dimension,
    normalize_piece_set_4d,  # backward-compatible parameter support
)
from ..runtime.score_analyzer import (
    analyze_lock_event,
    new_analysis_session_id,
    record_score_analysis_event,
)
from .scoring_bonus import score_with_clear_bonuses
from ..core.rules.scoring import score_for_clear
from ..core.rules.locking import apply_lock_and_score
from ..core.step.reducer import step_nd as core_step_nd
from .topology import (
    TOPOLOGY_BOUNDED,
    TopologyPolicy,
    map_piece_cells,
    normalize_topology_mode,
)
from ..core.model import Coord


def _score_for_clear(cleared_planes: int) -> int:
    return score_for_clear(cleared_planes)


def _coerce_rng_seed(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("rng_seed must be an integer")
    if not (0 <= value <= 999_999_999):
        raise ValueError("rng_seed must be within [0, 999999999]")
    return int(value)


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


@dataclass
class GameConfigND:
    dims: Coord = (10, 20, 6)
    gravity_axis: int = 1
    speed_level: int = 1  # 1..10, used by frontend timing
    topology_mode: str = TOPOLOGY_BOUNDED
    wrap_gravity_axis: bool = False
    topology_edge_rules: tuple[tuple[str, str], ...] | None = None
    piece_set_id: str | None = None
    piece_set_4d: str = PIECE_SET_4D_STANDARD
    random_cell_count: int = 5
    challenge_layers: int = 0
    lock_piece_points: int = 5
    exploration_mode: bool = False
    rng_mode: str = RNG_MODE_FIXED_SEED
    rng_seed: int = 1337

    def __post_init__(self) -> None:
        if len(self.dims) < 2:
            raise ValueError("dims must have at least 2 axes")
        if any(d <= 0 for d in self.dims):
            raise ValueError("all dimensions must be > 0")
        if not (0 <= self.gravity_axis < len(self.dims)):
            raise ValueError("invalid gravity_axis")
        if not (1 <= self.speed_level <= 10):
            raise ValueError("speed_level must be in [1, 10]")
        if not (3 <= self.random_cell_count <= 8):
            raise ValueError("random_cell_count must be in [3, 8]")
        if self.challenge_layers < 0:
            raise ValueError("challenge_layers must be >= 0")
        if self.lock_piece_points < 0:
            raise ValueError("lock_piece_points must be >= 0")
        self.exploration_mode = bool(self.exploration_mode)
        self.rng_mode = normalize_rng_mode(self.rng_mode)
        self.rng_seed = _coerce_rng_seed(self.rng_seed)
        self.topology_mode = normalize_topology_mode(self.topology_mode)
        self.wrap_gravity_axis = bool(self.wrap_gravity_axis)

        ndim = len(self.dims)
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
    current_piece: Optional[ActivePieceND] = None
    next_bag: List[PieceShapeND] = field(default_factory=list)
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

    def __post_init__(self) -> None:
        self.topology_policy = self.config.topology_policy()
        if self.board is None:
            self.board = BoardND(self.config.dims)
        if self.board.dims != self.config.dims:
            raise ValueError("board dims must match config dims")
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
        self.current_piece = ActivePieceND.from_shape(
            shape, self._spawn_pos_for_shape(shape)
        )
        if not self._can_exist(self.current_piece):
            self.game_over = True

    def _shape_fits_board(self, shape: PieceShapeND) -> bool:
        for axis in range(self.config.ndim):
            axis_values = [block[axis] for block in shape.blocks]
            span = max(axis_values) - min(axis_values) + 1
            if span > self.config.dims[axis]:
                return False
        return True

    def _mapped_piece_cells(self, piece: ActivePieceND) -> tuple[Coord, ...] | None:
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

    # --- Validation and locking ---

    def _can_exist(self, piece: ActivePieceND) -> bool:
        mapped_cells = self._mapped_piece_cells(piece)
        if mapped_cells is None:
            return False
        g = self.config.gravity_axis
        for coord in mapped_cells:
            if coord[g] < 0:
                continue
            if coord in self.board.cells:
                return False
        return True

    def lock_current_piece(self) -> int:
        if self.current_piece is None:
            return 0
        if self.config.exploration_mode:
            return 0

        g = self.config.gravity_axis
        piece = self.current_piece
        mapped_cells = self._mapped_piece_cells(piece)
        if mapped_cells is None:
            self.game_over = True
            return 0
        pre_cells = dict(self.board.cells)
        visible_piece_cells = tuple(coord for coord in mapped_cells if coord[g] >= 0)

        # If any block is still above the board along gravity axis, game over.
        for coord in mapped_cells:
            if coord[g] < 0:
                self.game_over = True

        lock_result = apply_lock_and_score(
            board=self.board,
            visible_piece_cells=visible_piece_cells,
            color_id=piece.shape.color_id,
            gravity_axis=g,
            lock_piece_points=self.config.lock_piece_points,
            score_multiplier=self.score_multiplier,
        )
        cleared = lock_result.cleared
        self.lines_cleared += cleared
        raw_points, awarded_points = score_with_clear_bonuses(
            raw_base_points=lock_result.raw_points,
            cleared_count=cleared,
            board_cell_count_after_clear=len(self.board.cells),
            score_multiplier=self.score_multiplier,
        )
        self.score += awarded_points

        self.analysis_seq += 1
        self.last_score_analysis = analyze_lock_event(
            board_pre=pre_cells,
            board_post=dict(self.board.cells),
            dims=self.config.dims,
            gravity_axis=g,
            locked_cells=visible_piece_cells,
            cleared=cleared,
            piece_id=piece.shape.name,
            actor_mode=self.analysis_actor_mode,
            bot_mode=self.analysis_bot_mode,
            grid_mode=self.analysis_grid_mode,
            speed_level=self.config.speed_level,
            raw_points=raw_points,
            final_points=awarded_points,
            session_id=self.analysis_session_id,
            seq=self.analysis_seq,
        )
        record_score_analysis_event(self.last_score_analysis)
        return cleared

    # --- Movement and rotation ---

    def try_move(self, delta: Sequence[int]) -> bool:
        if self.current_piece is None:
            return False
        candidate = self.current_piece.moved(delta)
        if self._can_exist(candidate):
            self.current_piece = candidate
            return True
        return False

    def try_move_axis(self, axis: int, delta: int) -> bool:
        if not (0 <= axis < self.config.ndim):
            raise ValueError("axis out of bounds")
        vector = [0] * self.config.ndim
        vector[axis] = delta
        return self.try_move(vector)

    def try_rotate(self, axis_a: int, axis_b: int, delta_steps: int = 1) -> bool:
        if self.current_piece is None:
            return False
        rotated = self.current_piece.rotated(axis_a, axis_b, delta_steps)
        if self._can_exist(rotated):
            self.current_piece = rotated
            return True
        return False

    def hard_drop(self) -> None:
        if self.current_piece is None:
            return
        if self.config.exploration_mode:
            self.spawn_new_piece()
            return

        g = self.config.gravity_axis
        while self.try_move_axis(g, 1):
            pass

        self.lock_current_piece()
        if not self.game_over:
            self.spawn_new_piece()

    # --- Time step ---

    def step_gravity(self) -> None:
        if self.config.exploration_mode or self.game_over or self.current_piece is None:
            return

        g = self.config.gravity_axis
        if not self.try_move_axis(g, 1):
            self.lock_current_piece()
            if not self.game_over:
                self.spawn_new_piece()

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
