# tetris_nd/game2d.py
from dataclasses import dataclass, field
from typing import List, Optional
import random

from ..core.model import Action, BoardND, GameConfig2DCoreView, GameState2DCoreView
from ..core.rng import RNG_MODE_FIXED_SEED, normalize_rng_mode
from .pieces2d import (
    ActivePiece2D,
    PieceShape2D,
    PIECE_SET_2D_CLASSIC,
    get_piece_bag_2d,
    normalize_piece_set_2d,
)
from ..runtime.score_analyzer import (
    analyze_lock_event,
    new_analysis_session_id,
    record_score_analysis_event,
)
from .scoring_bonus import score_with_clear_bonuses
from ..core.rules.scoring import score_for_clear
from ..core.rules.locking import apply_lock_and_score
from ..core.rules.state_queries import can_piece_exist_2d
from ..core.step.reducer import apply_action_2d as core_apply_action_2d
from ..core.step.reducer import step_2d as core_step_2d
from .topology import (
    TOPOLOGY_BOUNDED,
    TopologyPolicy,
    map_piece_cells,
    normalize_topology_mode,
)


def _score_for_clear(cleared_lines: int) -> int:
    return score_for_clear(cleared_lines)


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
    random_cell_count: int = 4
    challenge_layers: int = 0
    lock_piece_points: int = 5
    exploration_mode: bool = False
    rng_mode: str = RNG_MODE_FIXED_SEED
    rng_seed: int = 1337

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be > 0")
        # 2D mode is defined as gravity along y (axis 1), clearing full x-rows.
        if self.gravity_axis != 1:
            raise ValueError("2D mode requires gravity_axis=1 (y-axis)")
        if not (1 <= self.speed_level <= 10):
            raise ValueError("speed_level must be in [1, 10]")
        self.piece_set = normalize_piece_set_2d(self.piece_set)
        if not (3 <= self.random_cell_count <= 8):
            raise ValueError("random_cell_count must be in [3, 8]")
        if self.challenge_layers < 0:
            raise ValueError("challenge_layers must be >= 0")
        if self.lock_piece_points < 0:
            raise ValueError("lock_piece_points must be >= 0")
        self.exploration_mode = bool(self.exploration_mode)
        self.rng_mode = normalize_rng_mode(self.rng_mode)
        if isinstance(self.rng_seed, bool) or not isinstance(self.rng_seed, int):
            raise ValueError("rng_seed must be an integer")
        if not (0 <= self.rng_seed <= 999_999_999):
            raise ValueError("rng_seed must be within [0, 999999999]")
        self.topology_mode = normalize_topology_mode(self.topology_mode)
        self.wrap_gravity_axis = bool(self.wrap_gravity_axis)

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
    current_piece: Optional[ActivePiece2D] = None
    next_bag: List[PieceShape2D] = field(default_factory=list)
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
        self.current_piece = ActivePiece2D(shape, (spawn_x, spawn_y), rotation=0)
        if not self._can_exist(self.current_piece):
            self.game_over = True

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

    def _mapped_piece_cells(
        self, piece: ActivePiece2D
    ) -> tuple[tuple[int, int], ...] | None:
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

    def _can_exist(self, piece: ActivePiece2D) -> bool:
        """Compatibility wrapper over the core 2D existence/collision helper."""
        return can_piece_exist_2d(self, piece)

    def lock_current_piece(self) -> int:
        """
        Lock current piece into the board and clear any full lines.
        Returns number of cleared lines.
        """
        if self.current_piece is None:
            return 0
        if self.config.exploration_mode:
            return 0

        piece = self.current_piece
        mapped_cells = self._mapped_piece_cells(piece)
        if mapped_cells is None:
            self.game_over = True
            return 0
        pre_cells = dict(self.board.cells)
        visible_piece_cells = tuple(coord for coord in mapped_cells if coord[1] >= 0)

        # If any block is above the top row, the game is over.
        for x, y in mapped_cells:
            if y < 0:
                self.game_over = True

        lock_result = apply_lock_and_score(
            board=self.board,
            visible_piece_cells=visible_piece_cells,
            color_id=piece.shape.color_id,
            gravity_axis=self.config.gravity_axis,
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
            dims=(self.config.width, self.config.height),
            gravity_axis=self.config.gravity_axis,
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

    # --- Movement / rotation helpers ---

    def try_move(self, dx: int, dy: int):
        if self.current_piece is None:
            return
        moved = self.current_piece.moved(dx, dy)
        if self._can_exist(moved):
            self.current_piece = moved

    def try_rotate(self, delta_steps: int):
        if self.current_piece is None:
            return
        rotated = self.current_piece.rotated(delta_steps)
        if self._can_exist(rotated):
            self.current_piece = rotated

    def hard_drop(self):
        if self.current_piece is None:
            return
        if self.config.exploration_mode:
            self.spawn_new_piece()
            return
        # Move down until just before collision
        while True:
            moved = self.current_piece.moved(0, 1)
            if self._can_exist(moved):
                self.current_piece = moved
            else:
                break
        # Lock piece and spawn new one
        self.lock_current_piece()
        if not self.game_over:
            self.spawn_new_piece()

    def _apply_action(self, action: Action) -> bool:
        return core_apply_action_2d(self, action)

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
