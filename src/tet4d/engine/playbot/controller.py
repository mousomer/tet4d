from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable

from ..game2d import GameState
from ..game_nd import GameStateND
from ..pieces_nd import ActivePieceND, rotate_point_nd
from .planner_2d import plan_best_2d_move
from .planner_nd import plan_best_nd_move
from .planner_nd_core import canonical_blocks as _canonical_blocks
from .planner_nd_core import rotation_planes
from ..runtime_config import playbot_default_hard_drop_after_soft_drops
from .types import (
    BOT_MODE_OPTIONS,
    BotMode,
    BotPlannerAlgorithm,
    BotPlannerProfile,
    PlanStats,
    bot_mode_label,
    bot_planner_algorithm_label,
    bot_planner_profile_label,
    clamp_planning_budget_ms,
    default_planning_budget_ms,
)


def _next_mode(mode: BotMode) -> BotMode:
    try:
        idx = BOT_MODE_OPTIONS.index(mode)
    except ValueError:
        return BotMode.OFF
    return BOT_MODE_OPTIONS[(idx + 1) % len(BOT_MODE_OPTIONS)]


RotationStep = tuple[int, int, int]
RelBlocks = tuple[tuple[int, ...], ...]


def _rotation_sequence_nd(
    start_blocks: RelBlocks,
    target_blocks: RelBlocks,
    *,
    ndim: int,
    gravity_axis: int,
) -> list[RotationStep]:
    if start_blocks == target_blocks:
        return []

    planes = rotation_planes(ndim, gravity_axis)
    max_depth = 8 if ndim == 3 else 7
    max_states = 240

    queue: deque[tuple[RelBlocks, int]] = deque([(start_blocks, 0)])
    parent: dict[RelBlocks, tuple[RelBlocks, RotationStep] | None] = {
        start_blocks: None
    }

    while queue and len(parent) < max_states:
        blocks, depth = queue.popleft()
        if depth >= max_depth:
            continue

        for rotated, step in _rotation_neighbors(blocks, planes):
            if rotated in parent:
                continue
            parent[rotated] = (blocks, step)
            if rotated == target_blocks:
                return _trace_rotation_path(parent, rotated)
            queue.append((rotated, depth + 1))
            if len(parent) >= max_states:
                break
    return []


def _rotation_neighbors(
    blocks: RelBlocks,
    planes: tuple[tuple[int, int], ...],
) -> Iterable[tuple[RelBlocks, RotationStep]]:
    for axis_a, axis_b in planes:
        for delta in (1, -1):
            rotated = _canonical_blocks(
                rotate_point_nd(block, axis_a, axis_b, delta) for block in blocks
            )
            yield rotated, (axis_a, axis_b, delta)


def _trace_rotation_path(
    parent: dict[RelBlocks, tuple[RelBlocks, RotationStep] | None],
    target: RelBlocks,
) -> list[RotationStep]:
    path: list[RotationStep] = []
    curr = target
    while True:
        prev = parent[curr]
        if prev is None:
            break
        curr, step = prev
        path.append(step)
    path.reverse()
    return path


@dataclass
class PlayBotController:
    mode: BotMode = BotMode.OFF
    speed_level: int = 7
    action_interval_ms: int = 80
    planner_profile: BotPlannerProfile = BotPlannerProfile.BALANCED
    planner_algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO
    planning_budget_ms: int = 24
    hard_drop_after_soft_drops: int = field(
        default_factory=playbot_default_hard_drop_after_soft_drops
    )
    _accumulator_ms: int = 0
    _step_requested: bool = False
    _piece_token: tuple[object, ...] | None = None
    last_stats: PlanStats | None = None
    last_error: str = ""
    _assist_preview_cells: tuple[tuple[int, ...], ...] = field(default_factory=tuple)
    _target_rot_2d: int | None = None
    _target_x_2d: int | None = None
    _target_blocks_nd: RelBlocks | None = None
    _target_lateral_nd: tuple[int, ...] = field(default_factory=tuple)
    _rotation_plan_nd: list[RotationStep] = field(default_factory=list)
    _soft_drop_count_2d: int = 0
    _soft_drop_count_nd: int = 0

    @property
    def user_gameplay_enabled(self) -> bool:
        return self.mode in {BotMode.OFF, BotMode.ASSIST}

    @property
    def controls_descent(self) -> bool:
        return self.mode in {BotMode.AUTO, BotMode.STEP}

    @property
    def assist_preview_cells(self) -> tuple[tuple[int, ...], ...]:
        return self._assist_preview_cells

    def cycle_mode(self) -> BotMode:
        self.mode = _next_mode(self.mode)
        self.reset_runtime()
        return self.mode

    @staticmethod
    def action_interval_from_speed(gravity_interval_ms: int, speed_level: int) -> int:
        level = max(1, min(10, int(speed_level)))
        # 1 = slower than gravity, 10 = much faster than gravity.
        factor = 1.25 - 0.10 * level
        return max(20, int(gravity_interval_ms * max(0.25, factor)))

    def configure_speed(self, gravity_interval_ms: int, speed_level: int) -> None:
        self.speed_level = max(1, min(10, int(speed_level)))
        self.action_interval_ms = self.action_interval_from_speed(
            gravity_interval_ms, self.speed_level
        )

    def configure_planner(
        self,
        *,
        ndim: int,
        dims: tuple[int, ...] | None = None,
        profile: BotPlannerProfile,
        budget_ms: int | None,
        algorithm: BotPlannerAlgorithm | None = None,
    ) -> None:
        self.planner_profile = profile
        if algorithm is not None:
            self.planner_algorithm = algorithm
        selected = budget_ms
        if selected is None:
            selected = default_planning_budget_ms(ndim, profile, dims=dims)
        self.planning_budget_ms = clamp_planning_budget_ms(
            ndim, int(selected), dims=dims
        )

    def reset_runtime(self) -> None:
        self._accumulator_ms = 0
        self._step_requested = False
        self._piece_token = None
        self._assist_preview_cells = tuple()
        self._target_rot_2d = None
        self._target_x_2d = None
        self._target_blocks_nd = None
        self._target_lateral_nd = tuple()
        self._rotation_plan_nd = []
        self._soft_drop_count_2d = 0
        self._soft_drop_count_nd = 0

    def request_step(self) -> None:
        self._step_requested = True

    def status_lines(self) -> list[str]:
        lines = [f"Bot: {bot_mode_label(self.mode)}"]
        lines.append(f"Bot speed: {self.speed_level}/10 ({self.action_interval_ms} ms)")
        lines.append(
            (
                "Bot planner: "
                f"{bot_planner_profile_label(self.planner_profile)} / "
                f"{bot_planner_algorithm_label(self.planner_algorithm)} "
                f"({self.planning_budget_ms} ms)"
            )
        )
        if self.last_stats is not None:
            lines.append(f"Bot candidates: {self.last_stats.candidate_count}")
            lines.append(f"Bot clears: {self.last_stats.expected_clears}")
            lines.append(f"Bot plan: {self.last_stats.planning_ms:.1f} ms")
        if self.last_error:
            lines.append(f"Bot status: {self.last_error}")
        lines.append("F2 bot mode   F3 bot step")
        return lines

    def _piece_token_2d(self, state: GameState) -> tuple[object, ...]:
        piece = state.current_piece
        if piece is None:
            return ("none", state.lines_cleared, len(state.board.cells))
        return (
            piece.shape.name,
            state.lines_cleared,
            len(state.board.cells),
            len(state.next_bag),
        )

    def _piece_fully_visible_2d(self, state: GameState) -> bool:
        piece = state.current_piece
        if piece is None:
            return False
        return all(y >= 0 for _x, y in piece.cells())

    def _piece_token_nd(self, state: GameStateND) -> tuple[object, ...]:
        piece = state.current_piece
        if piece is None:
            return ("none", state.lines_cleared, len(state.board.cells))
        return (
            piece.shape.name,
            state.lines_cleared,
            len(state.board.cells),
            len(state.next_bag),
        )

    def _piece_fully_visible_nd(self, state: GameStateND) -> bool:
        piece = state.current_piece
        if piece is None:
            return False
        gravity_axis = state.config.gravity_axis
        return all(coord[gravity_axis] >= 0 for coord in piece.cells())

    def _update_assist_2d(self, state: GameState) -> None:
        token = self._piece_token_2d(state)
        if token == self._piece_token:
            return
        self._soft_drop_count_2d = 0
        self._piece_token = token
        plan = plan_best_2d_move(
            state,
            profile=self.planner_profile,
            budget_ms=self.planning_budget_ms,
            algorithm=self.planner_algorithm,
        )
        if plan is None:
            self.last_error = "no valid plan"
            self._assist_preview_cells = tuple()
            self._target_rot_2d = None
            self._target_x_2d = None
            return
        self.last_stats = plan.stats
        self.last_error = ""
        self._target_rot_2d = plan.final_piece.rotation
        self._target_x_2d = plan.final_piece.pos[0]
        self._assist_preview_cells = tuple(
            tuple(cell) for cell in plan.final_piece.cells()
        )

    def _update_assist_nd(self, state: GameStateND) -> None:
        token = self._piece_token_nd(state)
        if token == self._piece_token:
            return
        self._soft_drop_count_nd = 0
        self._piece_token = token
        plan = plan_best_nd_move(
            state,
            profile=self.planner_profile,
            budget_ms=self.planning_budget_ms,
            algorithm=self.planner_algorithm,
        )
        if plan is None:
            self.last_error = "no valid plan"
            self._assist_preview_cells = tuple()
            self._target_blocks_nd = None
            self._target_lateral_nd = tuple()
            self._rotation_plan_nd = []
            return

        gravity_axis = state.config.gravity_axis
        lateral_axes = tuple(
            axis for axis in range(state.config.ndim) if axis != gravity_axis
        )
        start_blocks = (
            _canonical_blocks(state.current_piece.rel_blocks)
            if state.current_piece
            else tuple()
        )
        target_blocks = _canonical_blocks(plan.final_piece.rel_blocks)
        self._rotation_plan_nd = _rotation_sequence_nd(
            start_blocks,
            target_blocks,
            ndim=state.config.ndim,
            gravity_axis=gravity_axis,
        )
        self._target_blocks_nd = target_blocks
        self._target_lateral_nd = tuple(
            plan.final_piece.pos[axis] for axis in lateral_axes
        )
        self.last_stats = plan.stats
        self.last_error = ""
        self._assist_preview_cells = tuple(
            tuple(cell) for cell in plan.final_piece.cells()
        )

    def _soft_drop_or_lock_2d(self, state: GameState, *, allow_hard_drop: bool) -> bool:
        piece = state.current_piece
        if piece is None:
            return False
        threshold = max(0, int(self.hard_drop_after_soft_drops))
        if allow_hard_drop and threshold > 0 and self._soft_drop_count_2d >= threshold:
            state.hard_drop()
            self._piece_token = None
            self._soft_drop_count_2d = 0
            return True
        before_pos = piece.pos
        state.try_move(0, 1)
        moved_piece = state.current_piece
        if moved_piece is not None and moved_piece.pos != before_pos:
            if allow_hard_drop:
                self._soft_drop_count_2d += 1
            else:
                self._soft_drop_count_2d = 0
            return True
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
        self._piece_token = None
        self._soft_drop_count_2d = 0
        return True

    def _step_piece_2d(self, state: GameState) -> bool:
        if state.current_piece is None or state.game_over:
            return False

        if not self._piece_fully_visible_2d(state):
            return self._soft_drop_or_lock_2d(state, allow_hard_drop=False)

        self._update_assist_2d(state)
        piece = state.current_piece
        if piece is None:
            return False

        target_rot = (
            self._target_rot_2d if self._target_rot_2d is not None else piece.rotation
        )
        if piece.rotation != target_rot:
            diff = (target_rot - piece.rotation) % 4
            primary = 1 if diff in (1, 2) else -1
            before = piece.rotation
            state.try_rotate(primary)
            if (
                state.current_piece is not None
                and state.current_piece.rotation != before
            ):
                return True
            if diff == 2:
                piece_after = state.current_piece
                before_retry = (
                    piece_after.rotation if piece_after is not None else before
                )
                state.try_rotate(-primary)
                if (
                    state.current_piece is not None
                    and state.current_piece.rotation != before_retry
                ):
                    return True
            return self._soft_drop_or_lock_2d(state, allow_hard_drop=False)

        target_x = self._target_x_2d if self._target_x_2d is not None else piece.pos[0]
        if piece.pos[0] != target_x:
            delta = 1 if target_x > piece.pos[0] else -1
            before_pos = piece.pos
            state.try_move(delta, 0)
            if (
                state.current_piece is not None
                and state.current_piece.pos != before_pos
            ):
                return True
            return self._soft_drop_or_lock_2d(state, allow_hard_drop=False)

        return self._soft_drop_or_lock_2d(state, allow_hard_drop=True)

    def _soft_drop_or_lock_nd(
        self, state: GameStateND, *, allow_hard_drop: bool
    ) -> bool:
        gravity_axis = state.config.gravity_axis
        threshold = max(0, int(self.hard_drop_after_soft_drops))
        if allow_hard_drop and threshold > 0 and self._soft_drop_count_nd >= threshold:
            state.hard_drop()
            self._piece_token = None
            self._soft_drop_count_nd = 0
            return True
        if state.try_move_axis(gravity_axis, 1):
            if allow_hard_drop:
                self._soft_drop_count_nd += 1
            else:
                self._soft_drop_count_nd = 0
            return True
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
        self._piece_token = None
        self._soft_drop_count_nd = 0
        return True

    def _step_piece_nd(self, state: GameStateND) -> bool:
        if state.current_piece is None or state.game_over:
            return False

        if not self._piece_fully_visible_nd(state):
            return self._soft_drop_or_lock_nd(state, allow_hard_drop=False)

        self._update_assist_nd(state)
        piece = state.current_piece
        if piece is None:
            return False

        current_blocks = _canonical_blocks(piece.rel_blocks)
        target_blocks = (
            self._target_blocks_nd
            if self._target_blocks_nd is not None
            else current_blocks
        )
        if current_blocks != target_blocks:
            if self._apply_planned_rotation_step_nd(
                state, current_blocks, target_blocks
            ):
                return True
            return self._soft_drop_or_lock_nd(state, allow_hard_drop=False)

        if self._apply_lateral_step_nd(state, piece):
            return True

        return self._soft_drop_or_lock_nd(state, allow_hard_drop=True)

    def _apply_planned_rotation_step_nd(
        self,
        state: GameStateND,
        current_blocks: RelBlocks,
        target_blocks: RelBlocks,
    ) -> bool:
        if not self._rotation_plan_nd:
            self._rotation_plan_nd = _rotation_sequence_nd(
                current_blocks,
                target_blocks,
                ndim=state.config.ndim,
                gravity_axis=state.config.gravity_axis,
            )
        if not self._rotation_plan_nd:
            return False
        axis_a, axis_b, delta = self._rotation_plan_nd[0]
        if not state.try_rotate(axis_a, axis_b, delta):
            return False
        self._rotation_plan_nd.pop(0)
        return True

    def _apply_lateral_step_nd(
        self,
        state: GameStateND,
        piece: ActivePieceND,
    ) -> bool:
        gravity_axis = state.config.gravity_axis
        lateral_axes = tuple(
            axis for axis in range(state.config.ndim) if axis != gravity_axis
        )
        target_lateral = self._target_lateral_nd
        if len(target_lateral) != len(lateral_axes):
            target_lateral = tuple(piece.pos[axis] for axis in lateral_axes)

        for idx, axis in enumerate(lateral_axes):
            current_val = piece.pos[axis]
            target_val = target_lateral[idx]
            if current_val == target_val:
                continue
            step = 1 if target_val > current_val else -1
            return state.try_move_axis(axis, step)
        return False

    def play_one_piece_2d(self, state: GameState) -> bool:
        if state.game_over or state.current_piece is None:
            return False
        start_token = self._piece_token_2d(state)
        for _ in range(260):
            self._step_piece_2d(state)
            if state.game_over:
                break
            if self._piece_token_2d(state) != start_token:
                return True
        return self._piece_token_2d(state) != start_token

    def play_one_piece_nd(self, state: GameStateND) -> bool:
        if state.game_over or state.current_piece is None:
            return False
        start_token = self._piece_token_nd(state)
        for _ in range(580):
            self._step_piece_nd(state)
            if state.game_over:
                break
            if self._piece_token_nd(state) != start_token:
                return True
        return self._piece_token_nd(state) != start_token

    def _should_auto_step(self, dt_ms: int) -> bool:
        interval = max(0, int(self.action_interval_ms))
        if interval == 0:
            return True
        self._accumulator_ms += max(0, int(dt_ms))
        if self._accumulator_ms < interval:
            return False
        self._accumulator_ms -= interval
        return True

    def tick_2d(self, state: GameState, dt_ms: int) -> None:
        if self.mode == BotMode.OFF:
            return
        if self.mode == BotMode.ASSIST:
            self._update_assist_2d(state)
            return
        if self.mode == BotMode.STEP:
            if not self._step_requested:
                return
            self._step_requested = False
            self._step_piece_2d(state)
            return
        if self._should_auto_step(dt_ms):
            self._step_piece_2d(state)

    def tick_nd(self, state: GameStateND, dt_ms: int) -> None:
        if self.mode == BotMode.OFF:
            return
        if self.mode == BotMode.ASSIST:
            self._update_assist_nd(state)
            return
        if self.mode == BotMode.STEP:
            if not self._step_requested:
                return
            self._step_requested = False
            self._step_piece_nd(state)
            return
        if self._should_auto_step(dt_ms):
            self._step_piece_nd(state)
