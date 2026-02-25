from __future__ import annotations

from dataclasses import dataclass

import pygame

from .projection3d import normalize_angle_deg

MAX_ABS_MOUSE_PITCH = 74.0


@dataclass
class MouseOrbitState:
    dragging: bool = False
    last_pos: tuple[int, int] | None = None
    yaw_sensitivity: float = 0.35
    pitch_sensitivity: float = 0.30
    invert_y: bool = False

    def reset(self) -> None:
        self.dragging = False
        self.last_pos = None


def clamp_pitch_deg(
    pitch_deg: float, *, max_abs_pitch: float = MAX_ABS_MOUSE_PITCH
) -> float:
    return max(-max_abs_pitch, min(max_abs_pitch, pitch_deg))


def mouse_wheel_delta(event: pygame.event.Event) -> int:
    if event.type == pygame.MOUSEWHEEL:
        delta = getattr(event, "y", 0)
        return int(delta) if isinstance(delta, (int, float)) else 0
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 4:
            return 1
        if event.button == 5:
            return -1
    return 0


def apply_mouse_orbit_event(
    event: pygame.event.Event,
    state: MouseOrbitState,
    *,
    yaw_deg: float,
    pitch_deg: float,
) -> tuple[float, float, bool]:
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        state.dragging = True
        state.last_pos = event.pos
        return yaw_deg, pitch_deg, False

    if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
        state.dragging = False
        state.last_pos = None
        return yaw_deg, pitch_deg, False

    if event.type != pygame.MOUSEMOTION or not state.dragging:
        return yaw_deg, pitch_deg, False

    if state.last_pos is None:
        state.last_pos = event.pos
        return yaw_deg, pitch_deg, False

    dx = event.pos[0] - state.last_pos[0]
    dy = event.pos[1] - state.last_pos[1]
    state.last_pos = event.pos
    if dx == 0 and dy == 0:
        return yaw_deg, pitch_deg, False

    next_yaw = normalize_angle_deg(yaw_deg + dx * state.yaw_sensitivity)
    direction = 1.0 if state.invert_y else -1.0
    next_pitch = clamp_pitch_deg(pitch_deg + direction * dy * state.pitch_sensitivity)
    return next_yaw, next_pitch, True
