from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable

from ..pieces_nd import rotate_point_nd
from ..game2d import GameState
from ..game_nd import GameStateND
from .planner_2d import plan_best_2d_move
from .planner_nd import plan_best_nd_move
from .types import BOT_MODE_OPTIONS, BotMode, PlanStats, bot_mode_label


def _next_mode(mode: BotMode) -> BotMode:
    try:
        idx = BOT_MODE_OPTIONS.index(mode)
    except ValueError:
        return BotMode.OFF
    return BOT_MODE_OPTIONS[(idx + 1) % len(BOT_MODE_OPTIONS)]


RotationStep = tuple[int, int, int]
RelBlocks = tuple[tuple[int, ...], ...]


def _canonical_blocks(blocks: Iterable[tuple[int, ...]]) -> RelBlocks:
    return tuple(sorted(tuple(block) for block in blocks))


def _rotation_planes(ndim: int, gravity_axis: int) -> tuple[tuple[int, int], ...]:
    if ndim == 3:
        z_axis = next((axis for axis in range(ndim) if axis not in (0, gravity_axis)), 2)
        return (
            (0, gravity_axis),
            (0, z_axis),
            (gravity_axis, z_axis),
        )
    pairs: list[tuple[int, int]] = []
    for axis_a in range(ndim):
        for axis_b in range(axis_a + 1, ndim):
            pairs.append((axis_a, axis_b))
    return tuple(pairs)


def _rotation_sequence_nd(
    start_blocks: RelBlocks,
    target_blocks: RelBlocks,
    *,
    ndim: int,
    gravity_axis: int,
) -> list[RotationStep]:
    if start_blocks == target_blocks:
        return []

    planes = _rotation_planes(ndim, gravity_axis)
    max_depth = 8 if ndim == 3 else 7
    max_states = 240

    queue: deque[tuple[RelBlocks, int]] = deque([(start_blocks, 0)])
    parent: dict[RelBlocks, tuple[RelBlocks, RotationStep] | None] = {start_blocks: None}

    while queue and len(parent) < max_states:
        blocks, depth = queue.popleft()
        if depth >= max_depth:
            continue

        for axis_a, axis_b in planes:
            for delta in (1, -1):
                rotated = _canonical_blocks(
                    rotate_point_nd(block, axis_a, axis_b, delta)
                    for block in blocks
                )
                if rotated in parent:
                    continue
                parent[rotated] = (blocks, (axis_a, axis_b, delta))
                if rotated == target_blocks:
                    path: list[RotationStep] = []
                    curr = rotated
                    while True:
                        prev = parent[curr]
                        if prev is None:
                            break
                        curr, step = prev
                        path.append(step)
                    path.reverse()
                    return path
                queue.append((rotated, depth + 1))
                if len(parent) >= max_states:
                    break
            if len(parent) >= max_states:
                break
    return []


@dataclass
class PlayBotController:
    mode: BotMode = BotMode.OFF
    speed_level: int = 7
    action_interval_ms: int = 80
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
        self.action_interval_ms = self.action_interval_from_speed(gravity_interval_ms, self.speed_level)

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

    def request_step(self) -> None:
        self._step_requested = True

    def status_lines(self) -> list[str]:
        lines = [f"Bot: {bot_mode_label(self.mode)}"]
        lines.append(f"Bot speed: {self.speed_level}/10 ({self.action_interval_ms} ms)")
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
        self._piece_token = token
        plan = plan_best_2d_move(state)
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
        self._assist_preview_cells = tuple(tuple(cell) for cell in plan.final_piece.cells())

    def _update_assist_nd(self, state: GameStateND) -> None:
        token = self._piece_token_nd(state)
        if token == self._piece_token:
            return
        self._piece_token = token
        plan = plan_best_nd_move(state)
        if plan is None:
            self.last_error = "no valid plan"
            self._assist_preview_cells = tuple()
            self._target_blocks_nd = None
            self._target_lateral_nd = tuple()
            self._rotation_plan_nd = []
            return

        gravity_axis = state.config.gravity_axis
        lateral_axes = tuple(axis for axis in range(state.config.ndim) if axis != gravity_axis)
        start_blocks = _canonical_blocks(state.current_piece.rel_blocks) if state.current_piece else tuple()
        target_blocks = _canonical_blocks(plan.final_piece.rel_blocks)
        self._rotation_plan_nd = _rotation_sequence_nd(
            start_blocks,
            target_blocks,
            ndim=state.config.ndim,
            gravity_axis=gravity_axis,
        )
        self._target_blocks_nd = target_blocks
        self._target_lateral_nd = tuple(plan.final_piece.pos[axis] for axis in lateral_axes)
        self.last_stats = plan.stats
        self.last_error = ""
        self._assist_preview_cells = tuple(tuple(cell) for cell in plan.final_piece.cells())

    def _soft_drop_or_lock_2d(self, state: GameState) -> bool:
        piece = state.current_piece
        if piece is None:
            return False
        before_pos = piece.pos
        state.try_move(0, 1)
        moved_piece = state.current_piece
        if moved_piece is not None and moved_piece.pos != before_pos:
            return True
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
        self._piece_token = None
        return True

    def _step_piece_2d(self, state: GameState) -> bool:
        if state.current_piece is None or state.game_over:
            return False

        if not self._piece_fully_visible_2d(state):
            return self._soft_drop_or_lock_2d(state)

        self._update_assist_2d(state)
        piece = state.current_piece
        if piece is None:
            return False

        target_rot = self._target_rot_2d if self._target_rot_2d is not None else piece.rotation
        if piece.rotation != target_rot:
            diff = (target_rot - piece.rotation) % 4
            primary = 1 if diff in (1, 2) else -1
            before = piece.rotation
            state.try_rotate(primary)
            if state.current_piece is not None and state.current_piece.rotation != before:
                return True
            if diff == 2:
                piece_after = state.current_piece
                before_retry = piece_after.rotation if piece_after is not None else before
                state.try_rotate(-primary)
                if state.current_piece is not None and state.current_piece.rotation != before_retry:
                    return True
            return self._soft_drop_or_lock_2d(state)

        target_x = self._target_x_2d if self._target_x_2d is not None else piece.pos[0]
        if piece.pos[0] != target_x:
            delta = 1 if target_x > piece.pos[0] else -1
            before_pos = piece.pos
            state.try_move(delta, 0)
            if state.current_piece is not None and state.current_piece.pos != before_pos:
                return True
            return self._soft_drop_or_lock_2d(state)

        return self._soft_drop_or_lock_2d(state)

    def _soft_drop_or_lock_nd(self, state: GameStateND) -> bool:
        gravity_axis = state.config.gravity_axis
        if state.try_move_axis(gravity_axis, 1):
            return True
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
        self._piece_token = None
        return True

    def _step_piece_nd(self, state: GameStateND) -> bool:
        if state.current_piece is None or state.game_over:
            return False

        if not self._piece_fully_visible_nd(state):
            return self._soft_drop_or_lock_nd(state)

        self._update_assist_nd(state)
        piece = state.current_piece
        if piece is None:
            return False

        current_blocks = _canonical_blocks(piece.rel_blocks)
        target_blocks = self._target_blocks_nd if self._target_blocks_nd is not None else current_blocks
        if current_blocks != target_blocks:
            if not self._rotation_plan_nd:
                self._rotation_plan_nd = _rotation_sequence_nd(
                    current_blocks,
                    target_blocks,
                    ndim=state.config.ndim,
                    gravity_axis=state.config.gravity_axis,
                )
            if self._rotation_plan_nd:
                axis_a, axis_b, delta = self._rotation_plan_nd[0]
                if state.try_rotate(axis_a, axis_b, delta):
                    self._rotation_plan_nd.pop(0)
                    return True
            return self._soft_drop_or_lock_nd(state)

        gravity_axis = state.config.gravity_axis
        lateral_axes = tuple(axis for axis in range(state.config.ndim) if axis != gravity_axis)
        target_lateral = self._target_lateral_nd
        if len(target_lateral) != len(lateral_axes):
            target_lateral = tuple(piece.pos[axis] for axis in lateral_axes)

        for idx, axis in enumerate(lateral_axes):
            current_val = piece.pos[axis]
            target_val = target_lateral[idx]
            if current_val == target_val:
                continue
            step = 1 if target_val > current_val else -1
            if state.try_move_axis(axis, step):
                return True
            return self._soft_drop_or_lock_nd(state)

        return self._soft_drop_or_lock_nd(state)

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
