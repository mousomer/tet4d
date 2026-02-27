from __future__ import annotations

from typing import Dict, Tuple

import pygame


KeyTuple = Tuple[int, ...]
KeyBindingMap = Dict[str, KeyTuple]

PROFILE_SMALL = "small"
PROFILE_FULL = "full"
PROFILE_MACBOOK = "macbook"


def _merge_bindings(*maps: dict[str, KeyTuple]) -> KeyBindingMap:
    merged: KeyBindingMap = {}
    for mapping in maps:
        merged.update(mapping)
    return merged


def profile_movement_maps(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
    if profile == PROFILE_FULL:
        movement_2d = {
            "move_x_neg": (pygame.K_KP4,),
            "move_x_pos": (pygame.K_KP6,),
            "move_y_neg": (pygame.K_KP1,),
            "move_y_pos": (pygame.K_KP3,),
            "soft_drop": (pygame.K_KP5,),
            "hard_drop": (pygame.K_KP0,),
        }
        movement_3d = {
            "move_x_neg": (pygame.K_KP4,),
            "move_x_pos": (pygame.K_KP6,),
            "move_z_neg": (pygame.K_KP8,),
            "move_z_pos": (pygame.K_KP2,),
            "move_y_neg": (pygame.K_KP1,),
            "move_y_pos": (pygame.K_KP3,),
            "soft_drop": (pygame.K_KP5,),
            "hard_drop": (pygame.K_KP0,),
        }
        movement_4d = {
            "move_x_neg": (pygame.K_KP4,),
            "move_x_pos": (pygame.K_KP6,),
            "move_z_neg": (pygame.K_KP8,),
            "move_z_pos": (pygame.K_KP2,),
            "move_w_neg": (pygame.K_KP_DIVIDE,),
            "move_w_pos": (pygame.K_KP_MULTIPLY,),
            "move_y_neg": (pygame.K_PAGEUP,),
            "move_y_pos": (pygame.K_PAGEDOWN,),
            "soft_drop": (pygame.K_KP5,),
            "hard_drop": (pygame.K_KP0,),
        }
        return movement_2d, movement_3d, movement_4d

    movement_2d = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "move_y_neg": (pygame.K_PAGEUP,),
        "move_y_pos": (pygame.K_PAGEDOWN,),
        "soft_drop": (pygame.K_DOWN,),
        "hard_drop": (pygame.K_SPACE,),
    }
    movement_3d = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "move_z_neg": (pygame.K_UP,),
        "move_z_pos": (pygame.K_DOWN,),
        "move_y_neg": (pygame.K_PAGEUP,),
        "move_y_pos": (pygame.K_PAGEDOWN,),
        "soft_drop": (pygame.K_LSHIFT, pygame.K_RSHIFT),
        "hard_drop": (pygame.K_SPACE,),
    }
    movement_4d = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "move_z_neg": (pygame.K_UP,),
        "move_z_pos": (pygame.K_DOWN,),
        "move_w_neg": (pygame.K_n,),
        "move_w_pos": (pygame.K_SLASH,),
        "move_y_neg": (pygame.K_PAGEUP,),
        "move_y_pos": (pygame.K_PAGEDOWN,),
        "soft_drop": (pygame.K_LSHIFT, pygame.K_RSHIFT),
        "hard_drop": (pygame.K_SPACE,),
    }
    if profile == PROFILE_MACBOOK:
        movement_4d = dict(movement_4d)
        movement_4d.update(
            {
                "move_w_neg": (pygame.K_COMMA,),
                "move_w_pos": (pygame.K_PERIOD,),
            }
        )
    return movement_2d, movement_3d, movement_4d


ROTATIONS_2D_SMALL: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_UP, pygame.K_q),
    "rotate_xy_neg": (pygame.K_w,),
}


ROTATIONS_2D_FULL: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_UP, pygame.K_x),
    "rotate_xy_neg": (pygame.K_z,),
}


ROTATIONS_3D_SMALL: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_q,),
    "rotate_xy_neg": (pygame.K_w,),
    "rotate_xz_pos": (pygame.K_a,),
    "rotate_xz_neg": (pygame.K_s,),
    "rotate_yz_pos": (pygame.K_z,),
    "rotate_yz_neg": (pygame.K_x,),
}


ROTATIONS_3D_FULL: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_q,),
    "rotate_xy_neg": (pygame.K_w,),
    "rotate_xz_pos": (pygame.K_a,),
    "rotate_xz_neg": (pygame.K_s,),
    "rotate_yz_pos": (pygame.K_z,),
    "rotate_yz_neg": (pygame.K_x,),
}


ROTATIONS_4D_SMALL: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_q,),
    "rotate_xy_neg": (pygame.K_w,),
    "rotate_xz_pos": (pygame.K_a,),
    "rotate_xz_neg": (pygame.K_s,),
    "rotate_yz_pos": (pygame.K_z,),
    "rotate_yz_neg": (pygame.K_x,),
    "rotate_xw_pos": (pygame.K_r,),
    "rotate_xw_neg": (pygame.K_t,),
    "rotate_yw_pos": (pygame.K_f,),
    "rotate_yw_neg": (pygame.K_g,),
    "rotate_zw_pos": (pygame.K_v,),
    "rotate_zw_neg": (pygame.K_b,),
}


ROTATIONS_4D_FULL: KeyBindingMap = {
    "rotate_xy_pos": (pygame.K_q,),
    "rotate_xy_neg": (pygame.K_w,),
    "rotate_xz_pos": (pygame.K_a,),
    "rotate_xz_neg": (pygame.K_s,),
    "rotate_yz_pos": (pygame.K_z,),
    "rotate_yz_neg": (pygame.K_x,),
    "rotate_xw_pos": (pygame.K_r,),
    "rotate_xw_neg": (pygame.K_t,),
    "rotate_yw_pos": (pygame.K_f,),
    "rotate_yw_neg": (pygame.K_g,),
    "rotate_zw_pos": (pygame.K_v,),
    "rotate_zw_neg": (pygame.K_b,),
}


DEFAULT_CAMERA_KEYS_3D: KeyBindingMap = {
    "yaw_fine_neg": (pygame.K_1,),
    "yaw_neg": (pygame.K_2,),
    "yaw_pos": (pygame.K_3,),
    "yaw_fine_pos": (pygame.K_4,),
    "pitch_neg": (pygame.K_5,),
    "pitch_pos": (pygame.K_6,),
    "zoom_out": (pygame.K_7,),
    "zoom_in": (pygame.K_8,),
    "cycle_projection": (pygame.K_9,),
    "reset": (pygame.K_0,),
    "overlay_alpha_dec": (pygame.K_LEFTBRACKET,),
    "overlay_alpha_inc": (pygame.K_RIGHTBRACKET,),
}


DEFAULT_CAMERA_KEYS_4D: KeyBindingMap = {
    "view_xw_neg": (pygame.K_1,),
    "view_xw_pos": (pygame.K_2,),
    "view_zw_neg": (pygame.K_3,),
    "view_zw_pos": (pygame.K_4,),
    "yaw_neg": (pygame.K_5,),
    "yaw_pos": (pygame.K_6,),
    "pitch_neg": (pygame.K_7,),
    "pitch_pos": (pygame.K_8,),
    "zoom_out": (pygame.K_9,),
    "zoom_in": (pygame.K_0,),
    "yaw_fine_neg": (pygame.K_KP7,),
    "yaw_fine_pos": (pygame.K_KP9,),
    "cycle_projection": (pygame.K_KP1,),
    "reset": (pygame.K_KP3,),
    "overlay_alpha_dec": (pygame.K_LEFTBRACKET,),
    "overlay_alpha_inc": (pygame.K_RIGHTBRACKET,),
}


DEFAULT_CAMERA_KEYS_4D_MACBOOK: KeyBindingMap = {
    "view_xw_neg": (pygame.K_1,),
    "view_xw_pos": (pygame.K_2,),
    "view_zw_neg": (pygame.K_3,),
    "view_zw_pos": (pygame.K_4,),
    "yaw_neg": (pygame.K_5,),
    "yaw_pos": (pygame.K_6,),
    "pitch_neg": (pygame.K_7,),
    "pitch_pos": (pygame.K_8,),
    "zoom_out": (pygame.K_9,),
    "zoom_in": (pygame.K_0,),
    "yaw_fine_neg": (pygame.K_MINUS,),
    "yaw_fine_pos": (pygame.K_EQUALS,),
    "cycle_projection": (pygame.K_p,),
    "reset": (pygame.K_BACKSPACE,),
    "overlay_alpha_dec": (pygame.K_LEFTBRACKET,),
    "overlay_alpha_inc": (pygame.K_RIGHTBRACKET,),
}


DEFAULT_SYSTEM_KEYS: KeyBindingMap = {
    "quit": (pygame.K_ESCAPE,),
    "menu": (pygame.K_m,),
    "restart": (pygame.K_y,),
    "toggle_grid": (pygame.K_c,),
    "help": (pygame.K_F1,),
}


DEFAULT_SYSTEM_KEYS_MACBOOK: KeyBindingMap = {
    "quit": (pygame.K_ESCAPE,),
    "menu": (pygame.K_m,),
    "restart": (pygame.K_y,),
    "toggle_grid": (pygame.K_c,),
    "help": (pygame.K_TAB,),
}


def default_game_bindings_for_profile(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
    movement_2d, movement_3d, movement_4d = profile_movement_maps(profile)
    if profile == PROFILE_FULL:
        rotations_2d = ROTATIONS_2D_FULL
        rotations_3d = ROTATIONS_3D_FULL
        rotations_4d = ROTATIONS_4D_FULL
    else:
        rotations_2d = ROTATIONS_2D_SMALL
        rotations_3d = ROTATIONS_3D_SMALL
        rotations_4d = ROTATIONS_4D_SMALL
    return (
        _merge_bindings(movement_2d, rotations_2d),
        _merge_bindings(movement_3d, rotations_3d),
        _merge_bindings(movement_4d, rotations_4d),
    )


def default_camera_bindings_for_profile(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap]:
    if profile == PROFILE_MACBOOK:
        return dict(DEFAULT_CAMERA_KEYS_3D), dict(DEFAULT_CAMERA_KEYS_4D_MACBOOK)
    return dict(DEFAULT_CAMERA_KEYS_3D), dict(DEFAULT_CAMERA_KEYS_4D)


def default_system_bindings_for_profile(profile: str) -> KeyBindingMap:
    if profile == PROFILE_MACBOOK:
        return dict(DEFAULT_SYSTEM_KEYS_MACBOOK)
    return dict(DEFAULT_SYSTEM_KEYS)


DISABLED_KEYS_2D: KeyTuple = (
    pygame.K_e,
    pygame.K_a,
    pygame.K_s,
    pygame.K_d,
    pygame.K_r,
    pygame.K_t,
    pygame.K_f,
    pygame.K_g,
    pygame.K_v,
    pygame.K_b,
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
    pygame.K_n,
    pygame.K_SLASH,
    pygame.K_COMMA,
    pygame.K_PERIOD,
    pygame.K_LEFTBRACKET,
    pygame.K_RIGHTBRACKET,
    pygame.K_SEMICOLON,
    pygame.K_QUOTE,
)
