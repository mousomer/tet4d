from __future__ import annotations

import math
from dataclasses import dataclass

from .projection3d import interpolate_angle_deg, normalize_angle_deg, smoothstep01


_MAX_SAFE_ABS_PITCH = 74.0


@dataclass
class YawPitchTurnAnimator:
    yaw_deg: float = 32.0
    pitch_deg: float = -26.0
    animating: bool = False
    anim_start_yaw: float = 0.0
    anim_target_yaw: float = 0.0
    anim_start_pitch: float = 0.0
    anim_target_pitch: float = 0.0
    anim_elapsed_ms: float = 0.0
    anim_duration_ms: float = 240.0

    def _start_turn(self, target_yaw: float, target_pitch: float) -> None:
        self.animating = True
        self.anim_elapsed_ms = 0.0
        self.anim_start_yaw = normalize_angle_deg(self.yaw_deg)
        self.anim_target_yaw = normalize_angle_deg(target_yaw)
        self.anim_start_pitch = self.pitch_deg
        self.anim_target_pitch = target_pitch

    def start_yaw_turn(self, delta_deg: float) -> None:
        self._start_turn(self.yaw_deg + delta_deg, self.pitch_deg)

    def start_pitch_turn(self, delta_deg: float) -> None:
        target_yaw, target_pitch = wrapped_pitch_target(self.yaw_deg, self.pitch_deg, delta_deg)
        self._start_turn(target_yaw, target_pitch)

    def is_animating(self) -> bool:
        return self.animating

    def stop_animation(self) -> None:
        self.animating = False
        self.anim_elapsed_ms = 0.0

    def step_animation(self, dt_ms: float) -> None:
        if not self.animating:
            return
        self.anim_elapsed_ms += max(0.0, dt_ms)
        if self.anim_duration_ms <= 0:
            progress = 1.0
        else:
            progress = min(1.0, self.anim_elapsed_ms / self.anim_duration_ms)
        self.yaw_deg = interpolate_angle_deg(self.anim_start_yaw, self.anim_target_yaw, progress)
        eased = smoothstep01(progress)
        self.pitch_deg = self.anim_start_pitch + (self.anim_target_pitch - self.anim_start_pitch) * eased
        if progress >= 1.0:
            self.yaw_deg = normalize_angle_deg(self.anim_target_yaw)
            self.pitch_deg = self.anim_target_pitch
            self.animating = False


def _dominant_xz_axis_step(vec_x: float, vec_z: float) -> tuple[int, int]:
    if abs(vec_x) >= abs(vec_z):
        if vec_x > 0:
            return 0, 1
        if vec_x < 0:
            return 0, -1
        return 2, 1 if vec_z >= 0 else -1
    if vec_z > 0:
        return 2, 1
    if vec_z < 0:
        return 2, -1
    return 0, 1


def viewer_relative_move_axis_delta(
    yaw_deg: float,
    intent: str,
) -> tuple[int, int]:
    """
    Map viewer-intent movement to board-axis movement on the x-z plane.
    Supported intents: left, right, away, closer.
    """
    yaw = math.radians(yaw_deg)
    right_x, right_z = math.cos(yaw), math.sin(yaw)
    away_x, away_z = -math.sin(yaw), math.cos(yaw)

    if intent == "left":
        return _dominant_xz_axis_step(-right_x, -right_z)
    if intent == "right":
        return _dominant_xz_axis_step(right_x, right_z)
    if intent == "away":
        return _dominant_xz_axis_step(away_x, away_z)
    if intent == "closer":
        return _dominant_xz_axis_step(-away_x, -away_z)
    raise ValueError(f"unsupported movement intent: {intent}")


def wrapped_pitch_target(
    yaw_deg: float,
    pitch_deg: float,
    delta_deg: float,
    *,
    max_abs_pitch: float = _MAX_SAFE_ABS_PITCH,
) -> tuple[float, float]:
    """
    Compute a 90-degree pitch turn target while avoiding near-flat top/down views.
    If the target would exceed +/-max_abs_pitch, wrap by 180 yaw and reflect pitch.
    """
    target_yaw = normalize_angle_deg(yaw_deg)
    target_pitch = pitch_deg + delta_deg

    while target_pitch > max_abs_pitch:
        target_pitch -= 180.0
        target_yaw = normalize_angle_deg(target_yaw + 180.0)
    while target_pitch < -max_abs_pitch:
        target_pitch += 180.0
        target_yaw = normalize_angle_deg(target_yaw + 180.0)

    return target_yaw, target_pitch
