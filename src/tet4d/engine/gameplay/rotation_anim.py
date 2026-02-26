from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .pieces2d import rotate_point_2d
from ..runtime.project_config import project_constant_float
from tet4d.ui.pygame.projection3d import smoothstep01

if TYPE_CHECKING:
    from .pieces2d import ActivePiece2D
    from .pieces_nd import ActivePieceND


CoordF = tuple[float, ...]
Coord2F = tuple[float, float]
_DEFAULT_ROTATION_DURATION_MS = project_constant_float(
    ("animation", "piece_rotation_duration_ms"),
    150.0,
    min_value=60.0,
    max_value=400.0,
)


def _distance_sq(a: CoordF, b: CoordF) -> float:
    return sum((a[idx] - b[idx]) ** 2 for idx in range(min(len(a), len(b))))


def _pair_endpoints(
    start_rel: tuple[CoordF, ...], end_rel: tuple[CoordF, ...]
) -> tuple[CoordF, ...]:
    if len(start_rel) != len(end_rel):
        return end_rel
    remaining = list(end_rel)
    paired: list[CoordF] = []
    for start in start_rel:
        nearest_idx = min(
            range(len(remaining)),
            key=lambda idx: _distance_sq(start, remaining[idx]),
        )
        paired.append(remaining.pop(nearest_idx))
    return tuple(paired)


def _lerp_coord(start: CoordF, end: CoordF, t: float) -> CoordF:
    return tuple(start[idx] + (end[idx] - start[idx]) * t for idx in range(len(start)))


@dataclass
class _RotationTween:
    start_rel: tuple[CoordF, ...]
    end_rel: tuple[CoordF, ...]
    duration_ms: float = _DEFAULT_ROTATION_DURATION_MS
    elapsed_ms: float = 0.0

    @property
    def done(self) -> bool:
        return self.progress >= 1.0

    @property
    def progress(self) -> float:
        if self.duration_ms <= 0:
            return 1.0
        return max(0.0, min(1.0, self.elapsed_ms / self.duration_ms))

    def step(self, dt_ms: float) -> None:
        self.elapsed_ms += max(0.0, dt_ms)

    def interpolated_rel(self) -> tuple[CoordF, ...]:
        eased = smoothstep01(self.progress)
        return tuple(
            _lerp_coord(start, end, eased)
            for start, end in zip(self.start_rel, self.end_rel)
        )


def _visible_along_gravity(cells: tuple[CoordF, ...], gravity_axis: int) -> bool:
    return all(cell[gravity_axis] >= 0 for cell in cells)


def _build_tween(
    start_rel: tuple[CoordF, ...],
    end_rel: tuple[CoordF, ...],
    *,
    duration_ms: float,
) -> _RotationTween:
    if not start_rel or len(start_rel) != len(end_rel):
        return _RotationTween(
            start_rel=end_rel, end_rel=end_rel, duration_ms=duration_ms
        )
    return _RotationTween(
        start_rel=start_rel,
        end_rel=_pair_endpoints(start_rel, end_rel),
        duration_ms=duration_ms,
    )


@dataclass
class PieceRotationAnimator2D:
    duration_ms: float = _DEFAULT_ROTATION_DURATION_MS
    gravity_axis: int = 1
    _tween: _RotationTween | None = None
    _prev_rel_sig: tuple[tuple[int, int], ...] | None = None
    _prev_rel: tuple[CoordF, ...] = tuple()
    _prev_shape_name: str | None = None
    _prev_visible: bool = False

    def reset(self) -> None:
        self._tween = None
        self._prev_rel_sig = None
        self._prev_rel = tuple()
        self._prev_shape_name = None
        self._prev_visible = False

    def _rel_blocks(self, piece: ActivePiece2D) -> tuple[CoordF, ...]:
        return tuple(
            (float(rx), float(ry))
            for bx, by in piece.shape.blocks
            for rx, ry in (rotate_point_2d(bx, by, piece.rotation),)
        )

    def _rel_signature(self, piece: ActivePiece2D) -> tuple[tuple[int, int], ...]:
        return tuple(
            sorted(
                rotate_point_2d(bx, by, piece.rotation) for bx, by in piece.shape.blocks
            )
        )

    def observe(self, piece: ActivePiece2D | None, dt_ms: float) -> None:
        if self._tween is not None:
            self._tween.step(dt_ms)
            if self._tween.done:
                self._tween = None

        if piece is None:
            self.reset()
            return

        curr_rel = self._rel_blocks(piece)
        curr_sig = self._rel_signature(piece)
        curr_shape = piece.shape.name
        curr_cells = tuple((float(x), float(y)) for x, y in piece.cells())
        curr_visible = _visible_along_gravity(curr_cells, self.gravity_axis)

        shape_changed = (
            self._prev_shape_name is not None and curr_shape != self._prev_shape_name
        )
        rel_changed = self._prev_rel_sig is not None and curr_sig != self._prev_rel_sig

        if shape_changed:
            self._tween = None
        elif rel_changed:
            if curr_visible and self._prev_visible:
                start_rel = (
                    self._tween.interpolated_rel()
                    if self._tween is not None
                    else self._prev_rel
                )
                self._tween = _build_tween(
                    start_rel,
                    curr_rel,
                    duration_ms=self.duration_ms,
                )
            else:
                self._tween = None

        self._prev_rel_sig = curr_sig
        self._prev_rel = curr_rel
        self._prev_shape_name = curr_shape
        self._prev_visible = curr_visible

    def overlay_cells(
        self,
        piece: ActivePiece2D | None,
    ) -> tuple[tuple[Coord2F, ...], int] | None:
        if piece is None or self._tween is None:
            return None
        rel = self._tween.interpolated_rel()
        px, py = piece.pos
        cells = tuple((px + block[0], py + block[1]) for block in rel)
        return cells, int(piece.shape.color_id)


@dataclass
class PieceRotationAnimatorND:
    ndim: int
    gravity_axis: int
    duration_ms: float = _DEFAULT_ROTATION_DURATION_MS
    _tween: _RotationTween | None = None
    _prev_rel_sig: tuple[tuple[int, ...], ...] | None = None
    _prev_rel: tuple[CoordF, ...] = tuple()
    _prev_shape_name: str | None = None
    _prev_visible: bool = False

    def reset(self) -> None:
        self._tween = None
        self._prev_rel_sig = None
        self._prev_rel = tuple()
        self._prev_shape_name = None
        self._prev_visible = False

    def _rel_blocks(self, piece: ActivePieceND) -> tuple[CoordF, ...]:
        return tuple(
            tuple(float(value) for value in block) for block in piece.rel_blocks
        )

    def _rel_signature(self, piece: ActivePieceND) -> tuple[tuple[int, ...], ...]:
        return tuple(
            sorted(tuple(int(value) for value in block) for block in piece.rel_blocks)
        )

    def observe(self, piece: ActivePieceND | None, dt_ms: float) -> None:
        if self._tween is not None:
            self._tween.step(dt_ms)
            if self._tween.done:
                self._tween = None

        if piece is None:
            self.reset()
            return

        curr_rel = self._rel_blocks(piece)
        curr_sig = self._rel_signature(piece)
        curr_shape = piece.shape.name
        curr_cells = tuple(
            tuple(float(value) for value in coord) for coord in piece.cells()
        )
        curr_visible = _visible_along_gravity(curr_cells, self.gravity_axis)

        shape_changed = (
            self._prev_shape_name is not None and curr_shape != self._prev_shape_name
        )
        rel_changed = self._prev_rel_sig is not None and curr_sig != self._prev_rel_sig

        if shape_changed:
            self._tween = None
        elif rel_changed:
            if curr_visible and self._prev_visible:
                start_rel = (
                    self._tween.interpolated_rel()
                    if self._tween is not None
                    else self._prev_rel
                )
                self._tween = _build_tween(
                    start_rel,
                    curr_rel,
                    duration_ms=self.duration_ms,
                )
            else:
                self._tween = None

        self._prev_rel_sig = curr_sig
        self._prev_rel = curr_rel
        self._prev_shape_name = curr_shape
        self._prev_visible = curr_visible

    def overlay_cells(
        self,
        piece: ActivePieceND | None,
    ) -> tuple[tuple[CoordF, ...], int] | None:
        if piece is None or self._tween is None:
            return None
        rel = self._tween.interpolated_rel()
        pos = piece.pos
        cells: list[CoordF] = []
        for block in rel:
            cells.append(
                tuple(float(pos[idx]) + block[idx] for idx in range(self.ndim))
            )
        return tuple(cells), int(piece.shape.color_id)
