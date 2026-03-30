from __future__ import annotations

from dataclasses import dataclass

import pygame

from tet4d.engine.runtime.api import runtime_binding_groups_for_dimension_runtime
from tet4d.ui.pygame.front3d_render import Camera3D
from tet4d.ui.pygame.front4d_render import LayerView3D, handle_view_key
from tet4d.ui.pygame.input.camera_mouse import (
    MouseOrbitState,
    apply_mouse_orbit_event,
    mouse_wheel_delta,
)
from tet4d.ui.pygame.input.key_dispatch import dispatch_bound_action


SceneCamera = Camera3D | LayerView3D | None


@dataclass(frozen=True)
class CameraAvailability:
    enabled: bool


def scene_camera_availability(dimension: int) -> CameraAvailability:
    if int(dimension) == 3:
        return CameraAvailability(enabled=True)
    if int(dimension) == 4:
        return CameraAvailability(enabled=True)
    return CameraAvailability(enabled=False)


def ensure_scene_camera(dimension: int, camera: SceneCamera) -> SceneCamera:
    dim = int(dimension)
    if dim == 3:
        if isinstance(camera, Camera3D):
            return camera
        next_camera = Camera3D()
        next_camera.reset()
        return next_camera
    if dim == 4:
        if isinstance(camera, LayerView3D):
            return camera
        next_view = LayerView3D()
        next_view.yaw_deg = 32.0
        next_view.pitch_deg = -26.0
        next_view.xw_deg = 0.0
        next_view.zw_deg = 0.0
        next_view.zoom_scale = 1.0
        next_view.stop_animation()
        return next_view
    return None


def ensure_mouse_orbit_state(orbit: object | None) -> MouseOrbitState:
    if isinstance(orbit, MouseOrbitState):
        return orbit
    return MouseOrbitState()


def _camera_bindings_for_dimension(dimension: int) -> dict[str, tuple[int, ...]]:
    groups = runtime_binding_groups_for_dimension_runtime(int(dimension))
    binding_map = groups.get("camera", {})
    return {
        str(action): tuple(int(key) for key in keys)
        for action, keys in dict(binding_map).items()
    }


def _handle_camera_key_3d(key: int, camera: Camera3D) -> bool:
    action = dispatch_bound_action(
        key,
        _camera_bindings_for_dimension(3),
        {
            'yaw_fine_neg': lambda: camera.start_yaw_turn(-15.0),
            'yaw_neg': lambda: camera.start_yaw_turn(-90.0),
            'yaw_pos': lambda: camera.start_yaw_turn(90.0),
            'yaw_fine_pos': lambda: camera.start_yaw_turn(15.0),
            'pitch_pos': lambda: camera.start_pitch_turn(90.0),
            'pitch_neg': lambda: camera.start_pitch_turn(-90.0),
            'zoom_in': lambda: setattr(camera, 'zoom', min(140.0, camera.zoom + 3.0)),
            'zoom_out': lambda: setattr(camera, 'zoom', max(18.0, camera.zoom - 3.0)),
            'reset': camera.reset,
            'cycle_projection': camera.cycle_projection,
            'overlay_alpha_dec': lambda: None,
            'overlay_alpha_inc': lambda: None,
        },
    )
    return action is not None


def handle_scene_camera_key(dimension: int, key: int, camera: SceneCamera) -> bool:
    if int(dimension) == 3 and isinstance(camera, Camera3D):
        return _handle_camera_key_3d(key, camera)
    if int(dimension) == 4 and isinstance(camera, LayerView3D):
        return handle_view_key(key, camera)
    return False


def step_scene_camera(camera: SceneCamera, dt_ms: float) -> None:
    if camera is None or not hasattr(camera, 'step_animation'):
        return
    camera.step_animation(float(dt_ms))


def _normalize_orbit_event(event: pygame.event.Event) -> pygame.event.Event:
    if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', None) == 2:
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 3, 'pos': event.pos})
    if event.type == pygame.MOUSEBUTTONUP and getattr(event, 'button', None) == 2:
        return pygame.event.Event(pygame.MOUSEBUTTONUP, {'button': 3, 'pos': event.pos})
    return event


def handle_scene_camera_mouse_event(
    dimension: int,
    event: pygame.event.Event,
    camera: SceneCamera,
    orbit: MouseOrbitState,
) -> bool:
    dim = int(dimension)
    if dim not in (3, 4) or camera is None:
        return False
    wheel = mouse_wheel_delta(event)
    if wheel:
        if dim == 3 and isinstance(camera, Camera3D):
            camera.zoom = max(18.0, min(140.0, camera.zoom + wheel * 3.0))
            return True
        if dim == 4 and isinstance(camera, LayerView3D):
            factor = 1.08 if wheel > 0 else (1.0 / 1.08)
            camera.zoom_scale = max(0.45, min(2.6, camera.zoom_scale * factor))
            return True
    orbit_event = _normalize_orbit_event(event)
    if dim == 3 and isinstance(camera, Camera3D):
        yaw, pitch, changed = apply_mouse_orbit_event(
            orbit_event,
            orbit,
            yaw_deg=camera.yaw_deg,
            pitch_deg=camera.pitch_deg,
        )
        if changed:
            camera.yaw_deg = yaw
            camera.pitch_deg = pitch
        return changed or orbit_event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}
    if dim == 4 and isinstance(camera, LayerView3D):
        yaw, pitch, changed = apply_mouse_orbit_event(
            orbit_event,
            orbit,
            yaw_deg=camera.yaw_deg,
            pitch_deg=camera.pitch_deg,
        )
        if changed:
            camera.yaw_deg = yaw
            camera.pitch_deg = pitch
        return changed or orbit_event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}
    return False


__all__ = [
    'CameraAvailability',
    'SceneCamera',
    'ensure_mouse_orbit_state',
    'ensure_scene_camera',
    'handle_scene_camera_key',
    'handle_scene_camera_mouse_event',
    'scene_camera_availability',
    'step_scene_camera',
]
