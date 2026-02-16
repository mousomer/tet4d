from __future__ import annotations

import math

from .projection3d import normalize_angle_deg


_MAX_SAFE_ABS_PITCH = 74.0


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
