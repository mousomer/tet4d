from __future__ import annotations

from tet4d.engine import api as engine_api


class _GridModeProxy:
    @property
    def FULL(self):
        return engine_api.profile_4d_grid_mode_full()


GridMode = _GridModeProxy()


def LayerView3D(*, xw_deg: float = 0.0, zw_deg: float = 0.0):
    return engine_api.profile_4d_new_layer_view_3d(xw_deg=xw_deg, zw_deg=zw_deg)


def create_initial_state(cfg):
    return engine_api.profile_4d_create_initial_state(cfg)


def draw_game_frame(*args, **kwargs):
    return engine_api.profile_4d_draw_game_frame(*args, **kwargs)


def init_fonts():
    return engine_api.profile_4d_init_fonts()


__all__ = [
    "GridMode",
    "LayerView3D",
    "create_initial_state",
    "draw_game_frame",
    "init_fonts",
]
