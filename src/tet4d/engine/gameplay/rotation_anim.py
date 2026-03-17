from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.piece_transform import (
    canonicalize_blocks_2d,
    canonicalize_blocks_nd,
    rotation_pivot_2d,
    rotate_blocks_2d,
)
from ..runtime.project_config import project_constant_float

if TYPE_CHECKING:
    from .pieces2d import ActivePiece2D
    from .pieces_nd import ActivePieceND


CoordF = tuple[float, ...]
Coord2F = tuple[float, float]


@dataclass(frozen=True)
class RigidPieceOverlay2D:
    cells: tuple[Coord2F, ...]
    color_id: int
    rel_blocks: tuple[Coord2F, ...]
    pos: Coord2F
    pivot: Coord2F
    angle_deg: float
_DEFAULT_ROTATION_DURATION_MS_2D = project_constant_float(
    ("animation", "piece_rotation_duration_ms_2d"),
    300.0,
    min_value=0.0,
    max_value=600.0,
)
_DEFAULT_ROTATION_DURATION_MS_ND = project_constant_float(
    ("animation", "piece_rotation_duration_ms_nd"),
    300.0,
    min_value=0.0,
    max_value=600.0,
)
_DEFAULT_ROTATION_TWEEN_DURATION_MS = _DEFAULT_ROTATION_DURATION_MS_2D
_DEFAULT_TRANSLATION_DURATION_MS = project_constant_float(
    ("animation", "piece_translation_duration_ms"),
    120.0,
    min_value=0.0,
    max_value=600.0,
)


def _smoothstep01(t: float) -> float:
    clamped = max(0.0, min(1.0, float(t)))
    return clamped * clamped * (3.0 - (2.0 * clamped))


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
    start_pos: CoordF
    end_pos: CoordF
    duration_ms: float = _DEFAULT_ROTATION_TWEEN_DURATION_MS
    elapsed_ms: float = 0.0
    rotation_plane: tuple[int, int] | None = None
    rotation_steps: int = 0
    rigid_rotation: bool = False
    rotation_pivot: Coord2F | None = None

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
        """Interpolate using rotation-based or linear interpolation."""
        if self.rotation_plane is not None and self.rotation_steps != 0:
            if self.rigid_rotation:
                return self._interpolated_rel_rigid_rotation()
            return self._interpolated_rel_rotational()
        else:
            return self._interpolated_rel_linear()

    def _interpolated_rel_linear(self) -> tuple[CoordF, ...]:
        """Original linear interpolation (fallback)."""
        eased = _smoothstep01(self.progress)
        return tuple(
            _lerp_coord(start, end, eased)
            for start, end in zip(self.start_rel, self.end_rel)
        )

    def _interpolated_rel_rotational(self) -> tuple[CoordF, ...]:
        """
        Rotation-based interpolation using circular arc between start and end positions.

        Matches the discrete rotation algorithm's 3-case pivot selection:
        - Odd×Odd or Even×Even: rotate around geometric center
        - Even×Odd or Odd×Even: rotate around block closest to center of mass
        """
        import math

        eased = _smoothstep01(self.progress)
        axis_a, axis_b = self.rotation_plane  # type: ignore

        # Calculate bounding box in rotation plane
        a_values = [b[axis_a] for b in self.start_rel]
        b_values = [b[axis_b] for b in self.start_rel]
        min_a, max_a = min(a_values), max(a_values)
        min_b, max_b = min(b_values), max(b_values)
        span_a = max_a - min_a
        span_b = max_b - min_b

        # Determine pivot using same logic as discrete rotation
        a_even = (span_a % 2) == 0
        b_even = (span_b % 2) == 0

        if a_even == b_even:
            # Both odd or both even - use geometric center
            pivot_a = (min_a + max_a) / 2.0
            pivot_b = (min_b + max_b) / 2.0
        else:
            # Mixed parity - find block closest to center of mass
            center_mass_a = sum(a_values) / len(self.start_rel)
            center_mass_b = sum(b_values) / len(self.start_rel)

            min_dist_sq = float('inf')
            pivot_a = self.start_rel[0][axis_a]
            pivot_b = self.start_rel[0][axis_b]

            for block in self.start_rel:
                dist_sq = (block[axis_a] - center_mass_a) ** 2 + (block[axis_b] - center_mass_b) ** 2
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    pivot_a = float(block[axis_a])
                    pivot_b = float(block[axis_b])

        # Interpolate each block along a circular arc
        result: list[CoordF] = []
        for start_block, end_block in zip(self.start_rel, self.end_rel):
            # Get coordinates in the rotation plane
            start_a = start_block[axis_a] - pivot_a
            start_b = start_block[axis_b] - pivot_b
            end_a = end_block[axis_a] - pivot_a
            end_b = end_block[axis_b] - pivot_b

            # Calculate angle for this block
            start_angle = math.atan2(start_b, start_a)
            end_angle = math.atan2(end_b, end_a)

            # Handle angle wrapping to take shortest path
            angle_diff = end_angle - start_angle
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            elif angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            # Interpolate angle
            current_angle = start_angle + angle_diff * eased

            # Interpolate radius (for blocks that may change distance during discrete rotation)
            start_radius = math.sqrt(start_a**2 + start_b**2)
            end_radius = math.sqrt(end_a**2 + end_b**2)
            current_radius = start_radius + (end_radius - start_radius) * eased

            # Convert back to coordinates
            new_a = current_radius * math.cos(current_angle) + pivot_a
            new_b = current_radius * math.sin(current_angle) + pivot_b

            # Build result block with interpolated values
            new_block = list(start_block)
            new_block[axis_a] = new_a
            new_block[axis_b] = new_b
            result.append(tuple(new_block))

        return tuple(result)

    def _interpolated_rel_rigid_rotation(self) -> tuple[CoordF, ...]:
        import math

        if self.rotation_plane is None:
            return self._interpolated_rel_linear()
        axis_a, axis_b = self.rotation_plane
        pivot = self.rotation_pivot
        if pivot is None:
            return self._interpolated_rel_rotational()
        pivot_a, pivot_b = pivot
        reference_idx = self._reference_rotation_index(axis_a, axis_b, pivot_a, pivot_b)
        if reference_idx is None:
            return self._interpolated_rel_linear()
        start_block = self.start_rel[reference_idx]
        end_block = self.end_rel[reference_idx]
        start_angle = math.atan2(start_block[axis_b] - pivot_b, start_block[axis_a] - pivot_a)
        end_angle = math.atan2(end_block[axis_b] - pivot_b, end_block[axis_a] - pivot_a)
        angle_diff = end_angle - start_angle
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        current_angle = angle_diff * _smoothstep01(self.progress)
        cos_theta = math.cos(current_angle)
        sin_theta = math.sin(current_angle)
        result: list[CoordF] = []
        for start in self.start_rel:
            rel_a = start[axis_a] - pivot_a
            rel_b = start[axis_b] - pivot_b
            rotated_a = rel_a * cos_theta - rel_b * sin_theta
            rotated_b = rel_a * sin_theta + rel_b * cos_theta
            block = list(start)
            block[axis_a] = rotated_a + pivot_a
            block[axis_b] = rotated_b + pivot_b
            result.append(tuple(block))
        return tuple(result)

    def _reference_rotation_index(
        self,
        axis_a: int,
        axis_b: int,
        pivot_a: float,
        pivot_b: float,
    ) -> int | None:
        best_idx: int | None = None
        best_radius_sq = 0.0
        for idx, start in enumerate(self.start_rel):
            rel_a = start[axis_a] - pivot_a
            rel_b = start[axis_b] - pivot_b
            radius_sq = (rel_a * rel_a) + (rel_b * rel_b)
            if radius_sq > best_radius_sq + 1e-9:
                best_radius_sq = radius_sq
                best_idx = idx
        return best_idx

    def interpolated_pos(self) -> CoordF:
        eased = _smoothstep01(self.progress)
        return _lerp_coord(self.start_pos, self.end_pos, eased)

    def interpolated_rotation_deg(self) -> float:
        if not self.rigid_rotation:
            return 0.0
        return 90.0 * float(self.rotation_steps) * _smoothstep01(self.progress)


def _visible_along_gravity(cells: tuple[CoordF, ...], gravity_axis: int) -> bool:
    return all(cell[gravity_axis] >= 0 for cell in cells)


def _build_tween(
    start_rel: tuple[CoordF, ...],
    end_rel: tuple[CoordF, ...],
    *,
    start_pos: CoordF,
    end_pos: CoordF,
    duration_ms: float,
    rotation_plane: tuple[int, int] | None = None,
    rotation_steps: int = 0,
    rigid_rotation: bool = False,
    rotation_pivot: Coord2F | None = None,
) -> _RotationTween:
    if not start_rel or len(start_rel) != len(end_rel):
        return _RotationTween(
            start_rel=end_rel,
            end_rel=end_rel,
            start_pos=end_pos,
            end_pos=end_pos,
            duration_ms=duration_ms,
            rotation_plane=rotation_plane,
            rotation_steps=rotation_steps,
            rigid_rotation=rigid_rotation,
            rotation_pivot=rotation_pivot,
        )
    # For rotation-based animation, we don't pair endpoints
    # because rotation handles block matching automatically
    if rotation_plane is not None:
        return _RotationTween(
            start_rel=start_rel,
            end_rel=end_rel,
            start_pos=start_pos,
            end_pos=end_pos,
            duration_ms=duration_ms,
            rotation_plane=rotation_plane,
            rotation_steps=rotation_steps,
            rigid_rotation=rigid_rotation,
            rotation_pivot=rotation_pivot,
        )
    else:
        # Use endpoint pairing for linear interpolation
        return _RotationTween(
            start_rel=start_rel,
            end_rel=_pair_endpoints(start_rel, end_rel),
            start_pos=start_pos,
            end_pos=end_pos,
            duration_ms=duration_ms,
            rotation_plane=None,
            rotation_steps=0,
            rigid_rotation=False,
            rotation_pivot=None,
        )


@dataclass
class PieceRotationAnimator2D:
    duration_ms: float = _DEFAULT_ROTATION_DURATION_MS_2D
    translation_duration_ms: float = _DEFAULT_TRANSLATION_DURATION_MS
    gravity_axis: int = 1
    _tween: _RotationTween | None = None
    _prev_rel_sig: tuple[tuple[int, int], ...] | None = None
    _prev_rel: tuple[CoordF, ...] = tuple()
    _prev_shape_name: str | None = None
    _prev_pos: Coord2F = tuple()
    _prev_visible: bool = False
    _prev_rotation: int | None = None

    def reset(self) -> None:
        self._tween = None
        self._prev_rel_sig = None
        self._prev_rel = tuple()
        self._prev_shape_name = None
        self._prev_pos = tuple()
        self._prev_visible = False
        self._prev_rotation = None

    def _rel_blocks(self, piece: ActivePiece2D) -> tuple[CoordF, ...]:
        return tuple(
            (float(rx), float(ry))
            for rx, ry in rotate_blocks_2d(piece.shape.blocks, piece.rotation)
        )

    def _rel_signature(self, piece: ActivePiece2D) -> tuple[tuple[int, int], ...]:
        return canonicalize_blocks_2d(
            rotate_blocks_2d(piece.shape.blocks, piece.rotation)
        )

    def _start_rotation_tween(
        self,
        *,
        curr_rel: tuple[CoordF, ...],
        curr_pos: Coord2F,
        curr_rotation: int,
    ) -> None:
        start_rel = (
            self._tween.interpolated_rel()
            if self._tween is not None
            else self._prev_rel
        )
        start_pos = (
            self._tween.interpolated_pos()
            if self._tween is not None
            else self._prev_pos
        )
        rotation_steps = 0
        if self._prev_rotation is not None:
            rotation_steps = (curr_rotation - self._prev_rotation) % 4
            if rotation_steps > 2:
                rotation_steps -= 4
        rotation_pivot = (
            self._tween.rotation_pivot
            if self._tween is not None and self._tween.rigid_rotation
            else rotation_pivot_2d(
                tuple((int(round(block[0])), int(round(block[1]))) for block in self._prev_rel)
            )
        )
        self._tween = _build_tween(
            start_rel,
            curr_rel,
            start_pos=start_pos,
            end_pos=curr_pos,
            duration_ms=self.duration_ms,
            rotation_plane=(0, self.gravity_axis),
            rotation_steps=rotation_steps,
            rigid_rotation=True,
            rotation_pivot=rotation_pivot,
        )

    def _start_translation_tween(
        self,
        *,
        curr_rel: tuple[CoordF, ...],
        curr_pos: Coord2F,
    ) -> None:
        self._tween = _build_tween(
            self._prev_rel,
            curr_rel,
            start_pos=self._prev_pos,
            end_pos=curr_pos,
            duration_ms=self.translation_duration_ms,
        )

    def _shift_active_tween(self, curr_pos: Coord2F) -> None:
        if self._tween is None:
            return
        delta_x = curr_pos[0] - self._prev_pos[0]
        delta_y = curr_pos[1] - self._prev_pos[1]
        self._tween.start_pos = (
            self._tween.start_pos[0] + delta_x,
            self._tween.start_pos[1] + delta_y,
        )
        self._tween.end_pos = (
            self._tween.end_pos[0] + delta_x,
            self._tween.end_pos[1] + delta_y,
        )

    def observe(
        self,
        piece: ActivePiece2D | None,
        dt_ms: float,
        *,
        animate_translation: bool = False,
    ) -> None:
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
        curr_pos = (float(piece.pos[0]), float(piece.pos[1]))
        curr_cells = tuple((float(x), float(y)) for x, y in piece.cells())
        curr_visible = _visible_along_gravity(curr_cells, self.gravity_axis)
        curr_rotation = piece.rotation

        shape_changed = (
            self._prev_shape_name is not None and curr_shape != self._prev_shape_name
        )
        rel_changed = self._prev_rel_sig is not None and curr_sig != self._prev_rel_sig
        pos_changed = self._prev_pos != tuple() and curr_pos != self._prev_pos

        should_animate_rotation = (
            curr_visible and self._prev_visible and float(self.duration_ms) > 0.0
        )
        should_animate_translation = (
            animate_translation
            and curr_visible
            and self._prev_visible
            and float(self.translation_duration_ms) > 0.0
        )

        if shape_changed:
            self._tween = None
        elif rel_changed:
            if should_animate_rotation:
                self._start_rotation_tween(
                    curr_rel=curr_rel,
                    curr_pos=curr_pos,
                    curr_rotation=curr_rotation,
                )
            else:
                self._tween = None
        elif pos_changed:
            if self._tween is not None:
                self._shift_active_tween(curr_pos)
            elif should_animate_translation:
                self._start_translation_tween(curr_rel=curr_rel, curr_pos=curr_pos)

        self._prev_rel_sig = curr_sig
        self._prev_rel = curr_rel
        self._prev_shape_name = curr_shape
        self._prev_pos = curr_pos
        self._prev_visible = curr_visible
        self._prev_rotation = curr_rotation

    def overlay_cells(
        self,
        piece: ActivePiece2D | None,
    ) -> tuple[tuple[Coord2F, ...], int] | None:
        if piece is None or self._tween is None:
            return None
        rel = self._tween.interpolated_rel()
        px, py = self._tween.interpolated_pos()
        cells = tuple((px + block[0], py + block[1]) for block in rel)
        return cells, int(piece.shape.color_id)

    def overlay_state(
        self,
        piece: ActivePiece2D | None,
    ) -> tuple[tuple[Coord2F, ...], int] | RigidPieceOverlay2D | None:
        overlay = self.overlay_cells(piece)
        if (
            piece is None
            or overlay is None
            or self._tween is None
            or not self._tween.rigid_rotation
            or self._tween.rotation_pivot is None
        ):
            return overlay
        rel_blocks = tuple(
            (float(block[0]), float(block[1])) for block in self._tween.start_rel
        )
        pos = tuple(float(value) for value in self._tween.interpolated_pos())
        if len(pos) != 2:
            return overlay
        return RigidPieceOverlay2D(
            cells=overlay[0],
            color_id=int(piece.shape.color_id),
            rel_blocks=rel_blocks,
            pos=(pos[0], pos[1]),
            pivot=self._tween.rotation_pivot,
            angle_deg=self._tween.interpolated_rotation_deg(),
        )


@dataclass
class PieceRotationAnimatorND:
    ndim: int
    gravity_axis: int
    duration_ms: float = _DEFAULT_ROTATION_DURATION_MS_ND
    translation_duration_ms: float = _DEFAULT_TRANSLATION_DURATION_MS
    _tween: _RotationTween | None = None
    _prev_rel_sig: tuple[tuple[int, ...], ...] | None = None
    _prev_rel: tuple[CoordF, ...] = tuple()
    _prev_shape_name: str | None = None
    _prev_pos: CoordF = tuple()
    _prev_visible: bool = False

    def reset(self) -> None:
        self._tween = None
        self._prev_rel_sig = None
        self._prev_rel = tuple()
        self._prev_shape_name = None
        self._prev_pos = tuple()
        self._prev_visible = False

    def _rel_blocks(self, piece: ActivePieceND) -> tuple[CoordF, ...]:
        return tuple(
            tuple(float(value) for value in block) for block in piece.rel_blocks
        )

    def _rel_signature(self, piece: ActivePieceND) -> tuple[tuple[int, ...], ...]:
        return canonicalize_blocks_nd(piece.rel_blocks)

    def observe(
        self,
        piece: ActivePieceND | None,
        dt_ms: float,
        *,
        animate_translation: bool = False,
    ) -> None:
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
        curr_pos = tuple(float(value) for value in piece.pos)
        curr_cells = tuple(
            tuple(float(value) for value in coord) for coord in piece.cells()
        )
        curr_visible = _visible_along_gravity(curr_cells, self.gravity_axis)

        shape_changed = (
            self._prev_shape_name is not None and curr_shape != self._prev_shape_name
        )
        rel_changed = self._prev_rel_sig is not None and curr_sig != self._prev_rel_sig
        pos_changed = self._prev_pos != tuple() and curr_pos != self._prev_pos

        if shape_changed:
            self._tween = None
        elif rel_changed:
            if (
                curr_visible
                and self._prev_visible
                and float(self.duration_ms) > 0.0
            ):
                start_rel = (
                    self._tween.interpolated_rel()
                    if self._tween is not None
                    else self._prev_rel
                )
                start_pos = (
                    self._tween.interpolated_pos()
                    if self._tween is not None
                    else self._prev_pos
                )
                # Extract rotation plane from piece if available
                rotation_plane = piece.last_rotation_plane if piece else None
                rotation_steps = piece.last_rotation_steps if piece else 0
                self._tween = _build_tween(
                    start_rel,
                    curr_rel,
                    start_pos=start_pos,
                    end_pos=curr_pos,
                    duration_ms=self.duration_ms,
                    rotation_plane=rotation_plane,
                    rotation_steps=rotation_steps,
                )
            else:
                self._tween = None
        elif pos_changed and self._tween is None:
            if (
                animate_translation
                and curr_visible
                and self._prev_visible
                and float(self.translation_duration_ms) > 0.0
            ):
                self._tween = _build_tween(
                    self._prev_rel,
                    curr_rel,
                    start_pos=self._prev_pos,
                    end_pos=curr_pos,
                    duration_ms=self.translation_duration_ms,
                )
        elif pos_changed and self._tween is not None:
            delta = tuple(curr_pos[idx] - self._prev_pos[idx] for idx in range(self.ndim))
            self._tween.start_pos = tuple(
                self._tween.start_pos[idx] + delta[idx] for idx in range(self.ndim)
            )
            self._tween.end_pos = tuple(
                self._tween.end_pos[idx] + delta[idx] for idx in range(self.ndim)
            )

        self._prev_rel_sig = curr_sig
        self._prev_rel = curr_rel
        self._prev_shape_name = curr_shape
        self._prev_pos = curr_pos
        self._prev_visible = curr_visible

    def overlay_cells(
        self,
        piece: ActivePieceND | None,
    ) -> tuple[tuple[CoordF, ...], int] | None:
        if piece is None or self._tween is None:
            return None
        rel = self._tween.interpolated_rel()
        pos = self._tween.interpolated_pos()
        cells: list[CoordF] = []
        for block in rel:
            cells.append(tuple(pos[idx] + block[idx] for idx in range(self.ndim)))
        return tuple(cells), int(piece.shape.color_id)
