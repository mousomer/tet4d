"""Shared keyboard bindings for 2D/3D/4D frontends.

Key profile selection:
- small (default): compact/laptop-friendly
- full: full keyboard with numpad-centric movement

Set via environment variable:
    TETRIS_KEY_PROFILE=small|full
"""

from __future__ import annotations

import os
from typing import Dict, Mapping, Tuple

import pygame


KeyTuple = Tuple[int, ...]
KeyBindingMap = Dict[str, KeyTuple]

PROFILE_SMALL = "small"
PROFILE_FULL = "full"
KEY_PROFILE_ENV = "TETRIS_KEY_PROFILE"


def _normalize_profile(raw: str | None) -> str:
    if raw is None:
        return PROFILE_SMALL
    value = raw.strip().lower()
    if value == PROFILE_FULL:
        return PROFILE_FULL
    return PROFILE_SMALL


def get_active_key_profile() -> str:
    return _normalize_profile(os.environ.get(KEY_PROFILE_ENV))


ACTIVE_KEY_PROFILE = get_active_key_profile()


def key_matches(bindings: Mapping[str, KeyTuple], action: str, key: int) -> bool:
    return key in bindings.get(action, ())


def _merge_bindings(*maps: Mapping[str, KeyTuple]) -> KeyBindingMap:
    merged: KeyBindingMap = {}
    for m in maps:
        merged.update(m)
    return merged


SYSTEM_KEYS: KeyBindingMap = {
    "quit": (pygame.K_ESCAPE,),
    "menu": (pygame.K_m,),
    "restart": (pygame.K_r,),
}


ROTATIONS_2D: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_UP, pygame.K_x),
    "rotate_xy_neg": (pygame.K_z,),
}


ROTATIONS_3D: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_q,),
    "rotate_xy_neg": (pygame.K_w,),
    "rotate_xz_pos": (pygame.K_a,),
    "rotate_xz_neg": (pygame.K_s,),
    "rotate_yz_pos": (pygame.K_z,),
    "rotate_yz_neg": (pygame.K_x,),
}


ROTATIONS_4D: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_UP, pygame.K_x),
    "rotate_xy_neg": (pygame.K_z,),
    "rotate_xz_pos": (pygame.K_1,),
    "rotate_xz_neg": (pygame.K_2,),
    "rotate_yz_pos": (pygame.K_3,),
    "rotate_yz_neg": (pygame.K_4,),
    "rotate_xw_pos": (pygame.K_5,),
    "rotate_xw_neg": (pygame.K_6,),
    "rotate_yw_pos": (pygame.K_7,),
    "rotate_yw_neg": (pygame.K_8,),
    "rotate_zw_pos": (pygame.K_9,),
    "rotate_zw_neg": (pygame.K_0,),
}


if ACTIVE_KEY_PROFILE == PROFILE_FULL:
    MOVEMENT_2D: KeyBindingMap = {
        "move_x_neg": (pygame.K_KP4,),
        "move_x_pos": (pygame.K_KP6,),
        "soft_drop": (pygame.K_KP5,),
        "hard_drop": (pygame.K_KP0,),
    }
    MOVEMENT_3D: KeyBindingMap = {
        "move_x_neg": (pygame.K_KP4,),
        "move_x_pos": (pygame.K_KP6,),
        "move_z_neg": (pygame.K_KP8,),
        "move_z_pos": (pygame.K_KP2,),
        "soft_drop": (pygame.K_KP5,),
        "hard_drop": (pygame.K_KP0,),
    }
    MOVEMENT_4D: KeyBindingMap = {
        "move_x_neg": (pygame.K_KP4,),
        "move_x_pos": (pygame.K_KP6,),
        "move_z_neg": (pygame.K_KP8,),
        "move_z_pos": (pygame.K_KP2,),
        "move_w_neg": (pygame.K_KP7,),
        "move_w_pos": (pygame.K_KP9,),
        "soft_drop": (pygame.K_KP5,),
        "hard_drop": (pygame.K_KP0,),
    }
else:
    MOVEMENT_2D = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "soft_drop": (pygame.K_DOWN,),
        "hard_drop": (pygame.K_SPACE,),
    }
    MOVEMENT_3D = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "move_z_neg": (pygame.K_UP,),
        "move_z_pos": (pygame.K_DOWN,),
        "soft_drop": (pygame.K_LSHIFT, pygame.K_RSHIFT),
        "hard_drop": (pygame.K_SPACE,),
    }
    MOVEMENT_4D = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "move_z_neg": (pygame.K_UP,),
        "move_z_pos": (pygame.K_DOWN,),
        "move_w_neg": (pygame.K_COMMA,),
        "move_w_pos": (pygame.K_PERIOD,),
        "soft_drop": (pygame.K_LSHIFT, pygame.K_RSHIFT),
        "hard_drop": (pygame.K_SPACE,),
    }


KEYS_2D: KeyBindingMap = _merge_bindings(MOVEMENT_2D, ROTATIONS_2D)
KEYS_3D: KeyBindingMap = _merge_bindings(MOVEMENT_3D, ROTATIONS_3D)
KEYS_4D: KeyBindingMap = _merge_bindings(MOVEMENT_4D, ROTATIONS_4D)


CAMERA_KEYS_3D: KeyBindingMap = {
    "yaw_neg": (pygame.K_j,),
    "yaw_pos": (pygame.K_l,),
    "pitch_pos": (pygame.K_i,),
    "pitch_neg": (pygame.K_k,),
    "zoom_in": (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS),
    "zoom_out": (pygame.K_MINUS, pygame.K_KP_MINUS),
    "reset": (pygame.K_0,),
    "cycle_projection": (pygame.K_p,),
}


SLICE_KEYS_3D: KeyBindingMap = {
    "slice_z_neg": (pygame.K_LEFTBRACKET,),
    "slice_z_pos": (pygame.K_RIGHTBRACKET,),
}


SLICE_KEYS_4D: KeyBindingMap = {
    "slice_z_neg": (pygame.K_LEFTBRACKET,),
    "slice_z_pos": (pygame.K_RIGHTBRACKET,),
    "slice_w_neg": (pygame.K_SEMICOLON,),
    "slice_w_pos": (pygame.K_QUOTE,),
}


DISABLED_KEYS_2D: KeyTuple = (
    pygame.K_q,
    pygame.K_w,
    pygame.K_e,
    pygame.K_a,
    pygame.K_s,
    pygame.K_d,
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_4,
    pygame.K_5,
    pygame.K_6,
    pygame.K_7,
    pygame.K_8,
    pygame.K_9,
    pygame.K_0,
    pygame.K_COMMA,
    pygame.K_PERIOD,
    pygame.K_LEFTBRACKET,
    pygame.K_RIGHTBRACKET,
    pygame.K_SEMICOLON,
    pygame.K_QUOTE,
)


CONTROL_LINES_3D_CAMERA = [
    "Camera:",
    " J/L        : yaw",
    " I/K        : pitch",
    " +/-        : zoom",
    " P          : projection",
    " 0          : reset camera",
]


if ACTIVE_KEY_PROFILE == PROFILE_FULL:
    CONTROL_LINES_2D = [
        "Controls:",
        " Numpad 4/6 : move x",
        " Up/X       : rotate x-y +",
        " Z          : rotate x-y -",
        " Numpad 5   : soft drop",
        " Numpad 0   : hard drop",
        "",
        " M          : menu",
        " Esc        : quit",
        " R          : restart",
    ]
    CONTROL_LINES_3D_GAME = [
        "Game:",
        " Numpad 4/6 : move x",
        " Numpad 8/2 : move z",
        " Numpad 5   : soft drop",
        " Numpad 0   : hard drop",
        " Q/W        : rotate x-y",
        " A/S        : rotate x-z",
        " Z/X        : rotate y-z",
    ]
    CONTROL_LINES_ND_3D = [
        "Controls:",
        " Numpad 4/6 : move x",
        " Numpad 8/2 : move z",
        " Numpad 5   : soft drop",
        " Numpad 0   : hard drop",
        " Q/W        : rotate x-y",
        " A/S        : rotate x-z",
        " Z/X        : rotate y-z",
        " [ / ]      : slice z",
        " R          : restart",
        " M          : menu",
        " Esc        : quit",
    ]
    CONTROL_LINES_ND_4D = [
        "Controls:",
        " Numpad 4/6 : move x",
        " Numpad 8/2 : move z",
        " Numpad 7/9 : move w",
        " Numpad 5   : soft drop",
        " Numpad 0   : hard drop",
        " Up/X       : rotate x-y +",
        " Z          : rotate x-y -",
        " 1/2        : rotate x-z",
        " 3/4        : rotate y-z",
        " 5/6        : rotate x-w",
        " 7/8        : rotate y-w",
        " 9/0        : rotate z-w",
        " [ / ]      : slice z",
        " ; / '      : slice w",
        " R          : restart",
        " M          : menu",
        " Esc        : quit",
    ]
else:
    CONTROL_LINES_2D = [
        "Controls:",
        " Left/Right : move x",
        " Up/X       : rotate x-y +",
        " Z          : rotate x-y -",
        " Down       : soft drop",
        " Space      : hard drop",
        "",
        " M          : menu",
        " Esc        : quit",
        " R          : restart",
    ]
    CONTROL_LINES_3D_GAME = [
        "Game:",
        " Arrows     : move x/z",
        " Shift      : soft drop",
        " Space      : hard drop",
        " Q/W        : rotate x-y",
        " A/S        : rotate x-z",
        " Z/X        : rotate y-z",
    ]
    CONTROL_LINES_ND_3D = [
        "Controls:",
        " Left/Right : move x",
        " Up/Down    : move z",
        " Shift      : soft drop",
        " Space      : hard drop",
        " Q/W        : rotate x-y",
        " A/S        : rotate x-z",
        " Z/X        : rotate y-z",
        " [ / ]      : slice z",
        " R          : restart",
        " M          : menu",
        " Esc        : quit",
    ]
    CONTROL_LINES_ND_4D = [
        "Controls:",
        " Left/Right : move x",
        " Up/Down    : move z",
        " , / .      : move w",
        " Shift      : soft drop",
        " Space      : hard drop",
        " Up/X       : rotate x-y +",
        " Z          : rotate x-y -",
        " 1/2        : rotate x-z",
        " 3/4        : rotate y-z",
        " 5/6        : rotate x-w",
        " 7/8        : rotate y-w",
        " 9/0        : rotate z-w",
        " [ / ]      : slice z",
        " ; / '      : slice w",
        " R          : restart",
        " M          : menu",
        " Esc        : quit",
    ]
