"""Shared keyboard bindings for 2D/3D/4D frontends.

Bindings are persisted in external JSON files:
    keybindings/2d.json
    keybindings/3d.json
    keybindings/4d.json

Default bindings still derive from the active profile:
    TETRIS_KEY_PROFILE=small|full
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence, Tuple

import pygame


KeyTuple = Tuple[int, ...]
KeyBindingMap = Dict[str, KeyTuple]

PROFILE_SMALL = "small"
PROFILE_FULL = "full"
KEY_PROFILE_ENV = "TETRIS_KEY_PROFILE"
BUILTIN_PROFILES = (PROFILE_SMALL, PROFILE_FULL)

REBIND_CONFLICT_REPLACE = "replace"
REBIND_CONFLICT_SWAP = "swap"
REBIND_CONFLICT_CANCEL = "cancel"
REBIND_CONFLICT_OPTIONS = (
    REBIND_CONFLICT_REPLACE,
    REBIND_CONFLICT_SWAP,
    REBIND_CONFLICT_CANCEL,
)

KEYBINDINGS_DIR = Path(__file__).resolve().parent.parent / "keybindings"
KEYBINDINGS_PROFILES_DIR = KEYBINDINGS_DIR / "profiles"
KEYBINDING_FILES = {
    2: KEYBINDINGS_DIR / "2d.json",
    3: KEYBINDINGS_DIR / "3d.json",
    4: KEYBINDINGS_DIR / "4d.json",
}
_PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _normalize_profile(raw: str | None) -> str:
    if raw is None:
        return PROFILE_SMALL
    value = raw.strip().lower()
    if value == PROFILE_FULL:
        return PROFILE_FULL
    return PROFILE_SMALL


def _normalize_profile_name(raw: str) -> str:
    value = raw.strip().lower()
    if not _PROFILE_NAME_RE.match(value):
        raise ValueError("invalid profile name; use letters, numbers, '_' or '-'")
    return value


def get_active_key_profile() -> str:
    return _normalize_profile(os.environ.get(KEY_PROFILE_ENV))


ACTIVE_KEY_PROFILE = get_active_key_profile()


def active_key_profile() -> str:
    return ACTIVE_KEY_PROFILE


def normalize_rebind_conflict_mode(mode: str | None) -> str:
    if mode is None:
        return REBIND_CONFLICT_REPLACE
    value = mode.strip().lower()
    if value in REBIND_CONFLICT_OPTIONS:
        return value
    return REBIND_CONFLICT_REPLACE


def cycle_rebind_conflict_mode(mode: str, step: int = 1) -> str:
    current = normalize_rebind_conflict_mode(mode)
    idx = REBIND_CONFLICT_OPTIONS.index(current)
    return REBIND_CONFLICT_OPTIONS[(idx + step) % len(REBIND_CONFLICT_OPTIONS)]


def _safe_resolve_path(path: Path) -> Path:
    root = KEYBINDINGS_DIR.resolve()
    resolved = path.expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path must be within keybindings directory: {root}")
    return resolved


def _default_profile_file_path(dimension: int) -> Path:
    path = KEYBINDING_FILES.get(dimension)
    if path is None:
        raise ValueError("dimension must be one of: 2, 3, 4")
    return path


def profile_keybinding_file_path(dimension: int, profile: str) -> Path:
    normalized = _normalize_profile_name(profile)
    filename = _default_profile_file_path(dimension).name
    return _safe_resolve_path(KEYBINDINGS_PROFILES_DIR / normalized / filename)


def keybinding_file_path_for_profile(dimension: int, profile: str | None = None) -> Path:
    selected = _normalize_profile_name(profile) if profile else ACTIVE_KEY_PROFILE
    return profile_keybinding_file_path(dimension, selected)


def key_matches(bindings: Mapping[str, KeyTuple], action: str, key: int) -> bool:
    return key in bindings.get(action, ())


def _merge_bindings(*maps: Mapping[str, KeyTuple]) -> KeyBindingMap:
    merged: KeyBindingMap = {}
    for m in maps:
        merged.update(m)
    return merged


def _replace_map(target: MutableMapping[str, KeyTuple], source: Mapping[str, KeyTuple]) -> None:
    target.clear()
    target.update(source)


def _profile_movement_maps(profile: str) -> Tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
    if profile == PROFILE_FULL:
        movement_2d = {
            "move_x_neg": (pygame.K_KP4,),
            "move_x_pos": (pygame.K_KP6,),
            "soft_drop": (pygame.K_KP5,),
            "hard_drop": (pygame.K_KP0,),
        }
        movement_3d = {
            "move_x_neg": (pygame.K_KP4,),
            "move_x_pos": (pygame.K_KP6,),
            "move_z_neg": (pygame.K_KP8,),
            "move_z_pos": (pygame.K_KP2,),
            "soft_drop": (pygame.K_KP5,),
            "hard_drop": (pygame.K_KP0,),
        }
        movement_4d = {
            "move_x_neg": (pygame.K_KP4,),
            "move_x_pos": (pygame.K_KP6,),
            "move_z_neg": (pygame.K_KP8,),
            "move_z_pos": (pygame.K_KP2,),
            "move_w_neg": (pygame.K_KP7,),
            "move_w_pos": (pygame.K_KP9,),
            "soft_drop": (pygame.K_KP5,),
            "hard_drop": (pygame.K_KP0,),
        }
        return movement_2d, movement_3d, movement_4d

    movement_2d = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "soft_drop": (pygame.K_DOWN,),
        "hard_drop": (pygame.K_SPACE,),
    }
    movement_3d = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "move_z_neg": (pygame.K_UP,),
        "move_z_pos": (pygame.K_DOWN,),
        "soft_drop": (pygame.K_LSHIFT, pygame.K_RSHIFT),
        "hard_drop": (pygame.K_SPACE,),
    }
    movement_4d = {
        "move_x_neg": (pygame.K_LEFT,),
        "move_x_pos": (pygame.K_RIGHT,),
        "move_z_neg": (pygame.K_UP,),
        "move_z_pos": (pygame.K_DOWN,),
        "move_w_neg": (pygame.K_COMMA,),
        "move_w_pos": (pygame.K_PERIOD,),
        "soft_drop": (pygame.K_LSHIFT, pygame.K_RSHIFT),
        "hard_drop": (pygame.K_SPACE,),
    }
    return movement_2d, movement_3d, movement_4d


SYSTEM_KEYS: KeyBindingMap = {
    "quit": (pygame.K_ESCAPE,),
    "menu": (pygame.K_m,),
    "restart": (pygame.K_r,),
    "toggle_grid": (pygame.K_g,),
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
    "rotate_xy_pos": (pygame.K_x,),
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


_DEFAULT_CAMERA_KEYS_3D: KeyBindingMap = {
    "yaw_fine_neg": (pygame.K_h,),
    "yaw_neg": (pygame.K_j,),
    "yaw_pos": (pygame.K_k,),
    "yaw_fine_pos": (pygame.K_l,),
    "pitch_pos": (pygame.K_u,),
    "pitch_neg": (pygame.K_o,),
    "zoom_in": (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS),
    "zoom_out": (pygame.K_MINUS, pygame.K_KP_MINUS),
    "reset": (pygame.K_0,),
    "cycle_projection": (pygame.K_p,),
}
_DEFAULT_CAMERA_KEYS_4D: KeyBindingMap = {
    "yaw_fine_neg": (pygame.K_h,),
    "yaw_neg": (pygame.K_j,),
    "yaw_pos": (pygame.K_k,),
    "yaw_fine_pos": (pygame.K_l,),
    "pitch_pos": (pygame.K_u,),
    "pitch_neg": (pygame.K_o,),
    "zoom_in": (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS),
    "zoom_out": (pygame.K_MINUS, pygame.K_KP_MINUS),
    "reset": (pygame.K_BACKSPACE,),
    "cycle_projection": (pygame.K_p,),
}
_DEFAULT_SLICE_KEYS_3D: KeyBindingMap = {
    "slice_z_neg": (pygame.K_LEFTBRACKET,),
    "slice_z_pos": (pygame.K_RIGHTBRACKET,),
}
_DEFAULT_SLICE_KEYS_4D: KeyBindingMap = {
    "slice_z_neg": (pygame.K_LEFTBRACKET,),
    "slice_z_pos": (pygame.K_RIGHTBRACKET,),
    "slice_w_neg": (pygame.K_SEMICOLON,),
    "slice_w_pos": (pygame.K_QUOTE,),
}


def _default_game_bindings_for_profile(profile: str) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
    movement_2d, movement_3d, movement_4d = _profile_movement_maps(profile)
    return (
        _merge_bindings(movement_2d, ROTATIONS_2D),
        _merge_bindings(movement_3d, ROTATIONS_3D),
        _merge_bindings(movement_4d, ROTATIONS_4D),
    )


_DEFAULT_KEYS_2D, _DEFAULT_KEYS_3D, _DEFAULT_KEYS_4D = _default_game_bindings_for_profile(
    ACTIVE_KEY_PROFILE
)


KEYS_2D: KeyBindingMap = dict(_DEFAULT_KEYS_2D)
KEYS_3D: KeyBindingMap = dict(_DEFAULT_KEYS_3D)
KEYS_4D: KeyBindingMap = dict(_DEFAULT_KEYS_4D)
CAMERA_KEYS_3D: KeyBindingMap = dict(_DEFAULT_CAMERA_KEYS_3D)
CAMERA_KEYS_4D: KeyBindingMap = dict(_DEFAULT_CAMERA_KEYS_4D)
SLICE_KEYS_3D: KeyBindingMap = dict(_DEFAULT_SLICE_KEYS_3D)
SLICE_KEYS_4D: KeyBindingMap = dict(_DEFAULT_SLICE_KEYS_4D)


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


CONTROL_LINES_2D: List[str] = []
CONTROL_LINES_3D_GAME: List[str] = []
CONTROL_LINES_ND_3D: List[str] = []
CONTROL_LINES_ND_4D: List[str] = []
CONTROL_LINES_3D_CAMERA: List[str] = []
CONTROL_LINES_4D_VIEW: List[str] = []


def reset_keybindings_to_profile_defaults(profile: str | None = None) -> None:
    selected = _normalize_profile_name(profile) if profile else ACTIVE_KEY_PROFILE
    keys_2d, keys_3d, keys_4d = _default_game_bindings_for_profile(selected)
    _replace_map(KEYS_2D, keys_2d)
    _replace_map(KEYS_3D, keys_3d)
    _replace_map(KEYS_4D, keys_4d)
    _replace_map(CAMERA_KEYS_3D, _DEFAULT_CAMERA_KEYS_3D)
    _replace_map(CAMERA_KEYS_4D, _DEFAULT_CAMERA_KEYS_4D)
    _replace_map(SLICE_KEYS_3D, _DEFAULT_SLICE_KEYS_3D)
    _replace_map(SLICE_KEYS_4D, _DEFAULT_SLICE_KEYS_4D)
    _sanitize_runtime_bindings()
    _rebuild_control_lines()


def _sanitize_runtime_bindings() -> None:
    # 4D gameplay keys must not be shadowed by 4D camera/view keys.
    occupied = set()
    for mapping in (KEYS_4D, SLICE_KEYS_4D, SYSTEM_KEYS):
        for keys in mapping.values():
            occupied.update(keys)

    sanitized_camera_4d: KeyBindingMap = {}
    for action, keys in CAMERA_KEYS_4D.items():
        filtered = tuple(key for key in keys if key not in occupied)
        if not filtered:
            filtered = _DEFAULT_CAMERA_KEYS_4D.get(action, ())
            filtered = tuple(key for key in filtered if key not in occupied)
        if action == "reset" and not filtered:
            filtered = (pygame.K_BACKSPACE,)
        sanitized_camera_4d[action] = filtered
    _replace_map(CAMERA_KEYS_4D, sanitized_camera_4d)


_KEY_NAME_OVERRIDES = {
    "escape": "Esc",
    "return": "Enter",
    "space": "Space",
    "left shift": "LShift",
    "right shift": "RShift",
    "left": "Left",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "left bracket": "[",
    "right bracket": "]",
    "semicolon": ";",
    "quote": "'",
    "comma": ",",
    "period": ".",
}


def _display_key_name(key: int) -> str:
    raw = pygame.key.name(key)
    if not raw:
        return str(key)
    lowered = raw.lower()
    if lowered in _KEY_NAME_OVERRIDES:
        return _KEY_NAME_OVERRIDES[lowered]
    if len(raw) == 1:
        return raw.upper()
    words = []
    for word in raw.split():
        if word == "kp":
            words.append("Numpad")
        else:
            words.append(word.capitalize())
    return " ".join(words)


def _format_keys(keys: Sequence[int]) -> str:
    if not keys:
        return "-"
    return "/".join(_display_key_name(key) for key in keys)


def _format_action(bindings: Mapping[str, KeyTuple], action: str) -> str:
    return _format_keys(bindings.get(action, ()))


def _format_pair(bindings: Mapping[str, KeyTuple], neg_action: str, pos_action: str) -> str:
    return f"{_format_action(bindings, neg_action)}/{_format_action(bindings, pos_action)}"


def _line(label: str, description: str) -> str:
    return f" {label:<11}: {description}"


def _build_control_section(
    title: str,
    specs: Sequence[tuple[object, ...]],
) -> list[str]:
    lines = [title]
    for spec in specs:
        kind = spec[0]
        if kind == "sep":
            lines.append("")
            continue

        bindings = spec[1]
        if kind == "action":
            lines.append(_line(_format_action(bindings, spec[2]), spec[3]))
            continue

        # pair
        lines.append(_line(_format_pair(bindings, spec[2], spec[3]), spec[4]))
    return lines


def _rebuild_control_lines() -> None:
    CONTROL_LINES_2D[:] = _build_control_section(
        "Controls:",
        (
            ("pair", KEYS_2D, "move_x_neg", "move_x_pos", "move x"),
            ("action", KEYS_2D, "rotate_xy_pos", "rotate x-y +"),
            ("action", KEYS_2D, "rotate_xy_neg", "rotate x-y -"),
            ("action", KEYS_2D, "soft_drop", "soft drop"),
            ("action", KEYS_2D, "hard_drop", "hard drop"),
            ("sep",),
            ("action", SYSTEM_KEYS, "toggle_grid", "cycle grid mode"),
            ("action", SYSTEM_KEYS, "menu", "menu"),
            ("action", SYSTEM_KEYS, "quit", "quit"),
            ("action", SYSTEM_KEYS, "restart", "restart"),
        ),
    )

    common_3d_specs = (
        ("pair", KEYS_3D, "move_x_neg", "move_x_pos", "move x"),
        ("pair", KEYS_3D, "move_z_neg", "move_z_pos", "move z"),
        ("action", KEYS_3D, "soft_drop", "soft drop"),
        ("action", KEYS_3D, "hard_drop", "hard drop"),
        ("pair", KEYS_3D, "rotate_xy_pos", "rotate_xy_neg", "rotate x-y"),
        ("pair", KEYS_3D, "rotate_xz_pos", "rotate_xz_neg", "rotate x-z"),
        ("pair", KEYS_3D, "rotate_yz_pos", "rotate_yz_neg", "rotate y-z"),
    )
    CONTROL_LINES_3D_GAME[:] = _build_control_section(
        "Game:",
        (*common_3d_specs, ("action", SYSTEM_KEYS, "toggle_grid", "cycle grid mode")),
    )
    CONTROL_LINES_ND_3D[:] = _build_control_section(
        "Controls:",
        (
            *common_3d_specs,
            ("pair", SLICE_KEYS_3D, "slice_z_neg", "slice_z_pos", "slice z"),
            ("action", SYSTEM_KEYS, "toggle_grid", "cycle grid mode"),
            ("action", SYSTEM_KEYS, "restart", "restart"),
            ("action", SYSTEM_KEYS, "menu", "menu"),
            ("action", SYSTEM_KEYS, "quit", "quit"),
        ),
    )

    CONTROL_LINES_ND_4D[:] = _build_control_section(
        "Controls:",
        (
            ("pair", KEYS_4D, "move_x_neg", "move_x_pos", "move x"),
            ("pair", KEYS_4D, "move_z_neg", "move_z_pos", "move z"),
            ("pair", KEYS_4D, "move_w_neg", "move_w_pos", "move w"),
            ("action", KEYS_4D, "soft_drop", "soft drop"),
            ("action", KEYS_4D, "hard_drop", "hard drop"),
            ("pair", KEYS_4D, "rotate_xy_pos", "rotate_xy_neg", "rotate x-y"),
            ("pair", KEYS_4D, "rotate_xz_pos", "rotate_xz_neg", "rotate x-z"),
            ("pair", KEYS_4D, "rotate_yz_pos", "rotate_yz_neg", "rotate y-z"),
            ("pair", KEYS_4D, "rotate_xw_pos", "rotate_xw_neg", "rotate x-w"),
            ("pair", KEYS_4D, "rotate_yw_pos", "rotate_yw_neg", "rotate y-w"),
            ("pair", KEYS_4D, "rotate_zw_pos", "rotate_zw_neg", "rotate z-w"),
            ("pair", SLICE_KEYS_4D, "slice_z_neg", "slice_z_pos", "slice z"),
            ("pair", SLICE_KEYS_4D, "slice_w_neg", "slice_w_pos", "slice w"),
            ("action", SYSTEM_KEYS, "toggle_grid", "cycle grid mode"),
            ("action", SYSTEM_KEYS, "restart", "restart"),
            ("action", SYSTEM_KEYS, "menu", "menu"),
            ("action", SYSTEM_KEYS, "quit", "quit"),
        ),
    )

    CONTROL_LINES_3D_CAMERA[:] = _build_control_section(
        "Camera:",
        (
            ("pair", CAMERA_KEYS_3D, "yaw_fine_neg", "yaw_fine_pos", "yaw +/-15"),
            ("pair", CAMERA_KEYS_3D, "yaw_neg", "yaw_pos", "yaw +/-90"),
            ("pair", CAMERA_KEYS_3D, "pitch_neg", "pitch_pos", "pitch +/-90"),
            ("pair", CAMERA_KEYS_3D, "zoom_out", "zoom_in", "zoom"),
            ("action", CAMERA_KEYS_3D, "cycle_projection", "projection"),
            ("action", CAMERA_KEYS_3D, "reset", "reset camera"),
        ),
    )

    CONTROL_LINES_4D_VIEW[:] = _build_control_section(
        "View:",
        (
            ("pair", CAMERA_KEYS_4D, "yaw_fine_neg", "yaw_fine_pos", "yaw +/-15"),
            ("pair", CAMERA_KEYS_4D, "yaw_neg", "yaw_pos", "yaw +/-90"),
            ("pair", CAMERA_KEYS_4D, "pitch_neg", "pitch_pos", "pitch +/-90"),
            ("pair", CAMERA_KEYS_4D, "zoom_out", "zoom_in", "zoom"),
            ("action", CAMERA_KEYS_4D, "reset", "reset view"),
        ),
    )


def _serialize_binding_group(bindings: Mapping[str, KeyTuple]) -> Dict[str, List[str]]:
    return {
        action: [pygame.key.name(key) for key in keys]
        for action, keys in bindings.items()
    }


def _parse_key(raw_key: object) -> int | None:
    if isinstance(raw_key, int):
        return raw_key
    if not isinstance(raw_key, str):
        return None
    token = raw_key.strip()
    if not token:
        return None
    for candidate in (token, token.lower()):
        try:
            return pygame.key.key_code(candidate)
        except ValueError:
            continue
    aliases = {
        "esc": "escape",
        "enter": "return",
        "lshift": "left shift",
        "rshift": "right shift",
    }
    alias = aliases.get(token.lower())
    if alias is None:
        return None
    try:
        return pygame.key.key_code(alias)
    except ValueError:
        return None


def _parse_key_list(raw_keys: object) -> KeyTuple | None:
    if not isinstance(raw_keys, list):
        return None
    parsed: List[int] = []
    for raw_key in raw_keys:
        key = _parse_key(raw_key)
        if key is not None:
            parsed.append(key)
    if not parsed:
        return None
    return tuple(parsed)


def _apply_group_payload(target: MutableMapping[str, KeyTuple], raw_group: object) -> None:
    if not isinstance(raw_group, dict):
        return
    updated: Dict[str, KeyTuple] = dict(target)
    for action in updated:
        if action not in raw_group:
            continue
        parsed = _parse_key_list(raw_group[action])
        if parsed is not None:
            updated[action] = parsed
    _replace_map(target, updated)


def _binding_groups_for_dimension(dimension: int) -> Dict[str, MutableMapping[str, KeyTuple]]:
    if dimension == 2:
        return {
            "game": KEYS_2D,
            "system": SYSTEM_KEYS,
        }
    if dimension == 3:
        return {
            "game": KEYS_3D,
            "camera": CAMERA_KEYS_3D,
            "slice": SLICE_KEYS_3D,
            "system": SYSTEM_KEYS,
        }
    if dimension == 4:
        return {
            "game": KEYS_4D,
            "slice": SLICE_KEYS_4D,
            "camera": CAMERA_KEYS_4D,
            "system": SYSTEM_KEYS,
        }
    raise ValueError("dimension must be one of: 2, 3, 4")


def runtime_binding_groups_for_dimension(dimension: int) -> Dict[str, Mapping[str, KeyTuple]]:
    groups = _binding_groups_for_dimension(dimension)
    return {group: dict(bindings) for group, bindings in groups.items()}


def binding_actions_for_dimension(dimension: int) -> Dict[str, list[str]]:
    groups = _binding_groups_for_dimension(dimension)
    return {group: sorted(bindings.keys()) for group, bindings in groups.items()}


_BINDING_GROUP_LABELS = {
    "system": "General / System",
    "game": "Gameplay",
    "camera": "Camera / View",
    "slice": "Slice",
}

_BINDING_GROUP_DESCRIPTIONS = {
    "system": "Global actions available in all modes.",
    "game": "Piece translation, drop, and rotation actions.",
    "camera": "Board/view camera orbit, projection, and zoom controls.",
    "slice": "Layer selection controls for dense 3D/4D inspection.",
}

_COMMON_ACTION_DESCRIPTIONS = {
    "toggle_grid": "Cycle grid display mode.",
    "menu": "Open the in-game pause menu.",
    "restart": "Restart the current run.",
    "quit": "Quit the current game or application flow.",
    "move_x_neg": "Move active piece left on the x axis.",
    "move_x_pos": "Move active piece right on the x axis.",
    "move_z_neg": "Move active piece away from viewer (default view).",
    "move_z_pos": "Move active piece closer to viewer (default view).",
    "move_w_neg": "Move active piece toward lower w layer.",
    "move_w_pos": "Move active piece toward higher w layer.",
    "soft_drop": "Move piece one gravity step down.",
    "hard_drop": "Drop piece immediately to lock position.",
    "rotate_xy_pos": "Rotate piece in x-y plane (+90).",
    "rotate_xy_neg": "Rotate piece in x-y plane (-90).",
    "rotate_xz_pos": "Rotate piece in x-z plane (+90).",
    "rotate_xz_neg": "Rotate piece in x-z plane (-90).",
    "rotate_yz_pos": "Rotate piece in y-z plane (+90).",
    "rotate_yz_neg": "Rotate piece in y-z plane (-90).",
    "rotate_xw_pos": "Rotate piece in x-w plane (+90).",
    "rotate_xw_neg": "Rotate piece in x-w plane (-90).",
    "rotate_yw_pos": "Rotate piece in y-w plane (+90).",
    "rotate_yw_neg": "Rotate piece in y-w plane (-90).",
    "rotate_zw_pos": "Rotate piece in z-w plane (+90).",
    "rotate_zw_neg": "Rotate piece in z-w plane (-90).",
    "yaw_fine_neg": "Yaw camera by -15 degrees.",
    "yaw_fine_pos": "Yaw camera by +15 degrees.",
    "yaw_neg": "Yaw camera by -90 degrees.",
    "yaw_pos": "Yaw camera by +90 degrees.",
    "pitch_neg": "Pitch camera by -90 degrees.",
    "pitch_pos": "Pitch camera by +90 degrees.",
    "zoom_in": "Zoom camera in.",
    "zoom_out": "Zoom camera out.",
    "cycle_projection": "Cycle projection mode.",
    "reset": "Reset camera/view transform.",
    "slice_z_neg": "Move active z slice toward lower z.",
    "slice_z_pos": "Move active z slice toward higher z.",
    "slice_w_neg": "Move active w slice toward lower w.",
    "slice_w_pos": "Move active w slice toward higher w.",
}


def binding_group_label(group: str) -> str:
    return _BINDING_GROUP_LABELS.get(group, group.replace("_", " ").title())


def binding_group_description(group: str) -> str:
    return _BINDING_GROUP_DESCRIPTIONS.get(group, "Control category.")


def binding_action_description(action: str) -> str:
    return _COMMON_ACTION_DESCRIPTIONS.get(action, action.replace("_", " "))


def _remove_key_from_tuple(keys: KeyTuple, key: int) -> KeyTuple:
    filtered = tuple(candidate for candidate in keys if candidate != key)
    return filtered


def _find_conflicts(groups: Mapping[str, Mapping[str, KeyTuple]],
                    key: int,
                    skip_group: str,
                    skip_action: str) -> list[tuple[str, str]]:
    conflicts: list[tuple[str, str]] = []
    for group_name, binding_map in groups.items():
        for action_name, keys in binding_map.items():
            if group_name == skip_group and action_name == skip_action:
                continue
            if key in keys:
                conflicts.append((group_name, action_name))
    return conflicts


def _camera_blocked_conflicts(
    group: str,
    conflicts: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    if group != "camera":
        return []
    return [
        (conflict_group, conflict_action)
        for conflict_group, conflict_action in conflicts
        if conflict_group in {"game", "slice", "system"}
    ]


def _swap_conflicts(
    groups: Mapping[str, Mapping[str, KeyTuple]],
    binding_map: Mapping[str, KeyTuple],
    action: str,
    key: int,
    conflicts: list[tuple[str, str]],
) -> None:
    first_group, first_action = conflicts[0]
    first_map = groups[first_group]
    old_keys = binding_map[action]
    first_map[first_action] = old_keys
    for extra_group, extra_action in conflicts[1:]:
        extra_map = groups[extra_group]
        extra_map[extra_action] = _remove_key_from_tuple(extra_map[extra_action], key)


def _replace_conflicts(
    groups: Mapping[str, Mapping[str, KeyTuple]],
    key: int,
    conflicts: list[tuple[str, str]],
) -> None:
    for conflict_group, conflict_action in conflicts:
        conflict_map = groups[conflict_group]
        conflict_map[conflict_action] = _remove_key_from_tuple(conflict_map[conflict_action], key)


def _apply_rebind_conflicts(
    groups: Mapping[str, Mapping[str, KeyTuple]],
    binding_map: Mapping[str, KeyTuple],
    action: str,
    key: int,
    conflicts: list[tuple[str, str]],
    conflict_mode: str,
) -> None:
    if conflicts and conflict_mode == REBIND_CONFLICT_SWAP:
        _swap_conflicts(groups, binding_map, action, key, conflicts)
        return
    _replace_conflicts(groups, key, conflicts)


def _rebind_success_message(
    *,
    group: str,
    action: str,
    key_name: str,
    conflict_mode: str,
    conflicts: list[tuple[str, str]],
) -> str:
    if not conflicts:
        return f"Rebound {group}.{action} -> {key_name}"
    conflict_refs = ", ".join(f"{g}.{a}" for g, a in conflicts)
    return f"Rebound {group}.{action} -> {key_name} ({conflict_mode}: {conflict_refs})"


def rebind_action_key(
    dimension: int,
    group: str,
    action: str,
    key: int,
    *,
    conflict_mode: str = REBIND_CONFLICT_REPLACE,
) -> tuple[bool, str]:
    try:
        groups = _binding_groups_for_dimension(dimension)
    except ValueError as exc:
        return False, str(exc)
    binding_map = groups.get(group)
    if binding_map is None:
        return False, f"unknown binding group: {group}"
    if action not in binding_map:
        return False, f"unknown action: {group}.{action}"

    selected_mode = normalize_rebind_conflict_mode(conflict_mode)
    conflicts = _find_conflicts(groups, key, group, action)
    blocked_conflicts = _camera_blocked_conflicts(group, conflicts)
    if blocked_conflicts:
        conflict_refs = ", ".join(f"{g}.{a}" for g, a in blocked_conflicts)
        return False, f"Camera key cannot override {conflict_refs}"
    if conflicts and selected_mode == REBIND_CONFLICT_CANCEL:
        conflict_refs = ", ".join(f"{g}.{a}" for g, a in conflicts)
        return False, f"Key already used by {conflict_refs}; conflict mode=cancel"

    _apply_rebind_conflicts(
        groups,
        binding_map,
        action,
        key,
        conflicts,
        selected_mode,
    )
    binding_map[action] = (key,)

    _sanitize_runtime_bindings()
    _rebuild_control_lines()
    key_name = _display_key_name(key)
    return True, _rebind_success_message(
        group=group,
        action=action,
        key_name=key_name,
        conflict_mode=selected_mode,
        conflicts=conflicts,
    )


def keybinding_file_path(dimension: int) -> Path:
    return keybinding_file_path_for_profile(dimension, ACTIVE_KEY_PROFILE)


def _legacy_keybinding_file_path(dimension: int) -> Path:
    return _safe_resolve_path(_default_profile_file_path(dimension))


def keybinding_file_label(dimension: int) -> str:
    path = keybinding_file_path(dimension)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _validate_optional_external_path(file_path: str | None) -> Path | None:
    if file_path is None:
        return None
    return _safe_resolve_path(Path(file_path))


def list_key_profiles() -> list[str]:
    profiles = set(BUILTIN_PROFILES)
    if KEYBINDINGS_PROFILES_DIR.exists():
        for child in KEYBINDINGS_PROFILES_DIR.iterdir():
            if not child.is_dir():
                continue
            try:
                profiles.add(_normalize_profile_name(child.name))
            except ValueError:
                continue
    return sorted(profiles)


def next_auto_profile_name(prefix: str = "custom") -> str:
    safe_prefix = _normalize_profile_name(prefix)
    existing = set(list_key_profiles())
    idx = 1
    while True:
        candidate = f"{safe_prefix}_{idx}"
        if candidate not in existing:
            return candidate
        idx += 1


def set_active_key_profile(profile: str) -> tuple[bool, str]:
    try:
        normalized = _normalize_profile_name(profile)
    except ValueError as exc:
        return False, str(exc)
    global ACTIVE_KEY_PROFILE
    ACTIVE_KEY_PROFILE = normalized
    return True, f"Active key profile: {normalized}"


def create_auto_profile(base_profile: str | None = None) -> tuple[bool, str, str | None]:
    source = _normalize_profile_name(base_profile) if base_profile else ACTIVE_KEY_PROFILE
    candidate = next_auto_profile_name("custom")
    ok, msg = clone_key_profile(candidate, source)
    if not ok:
        return False, msg, None
    return True, msg, candidate


def clone_key_profile(target_profile: str, source_profile: str | None = None) -> tuple[bool, str]:
    target = _normalize_profile_name(target_profile)
    source = _normalize_profile_name(source_profile) if source_profile else ACTIVE_KEY_PROFILE
    if target in BUILTIN_PROFILES:
        return False, "cannot overwrite built-in profile"
    if target in list_key_profiles():
        return False, f"profile already exists: {target}"
    try:
        for dimension in (2, 3, 4):
            src_path = keybinding_file_path_for_profile(dimension, source)
            if not src_path.exists() and source == PROFILE_SMALL:
                src_path = _legacy_keybinding_file_path(dimension)
            dst_path = keybinding_file_path_for_profile(dimension, target)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.exists():
                dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
                continue
            # Fallback: generate defaults for source profile.
            reset_keybindings_to_profile_defaults(source)
            save_keybindings_file(dimension, profile=source)
            src_path = keybinding_file_path_for_profile(dimension, source)
            dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
    except (OSError, ValueError) as exc:
        return False, f"failed creating profile {target}: {exc}"
    return True, f"Created profile: {target}"


def delete_key_profile(profile: str) -> tuple[bool, str]:
    normalized = _normalize_profile_name(profile)
    if normalized in BUILTIN_PROFILES:
        return False, "cannot delete built-in profile"
    dir_path = _safe_resolve_path(KEYBINDINGS_PROFILES_DIR / normalized)
    if not dir_path.exists():
        return False, f"profile not found: {normalized}"
    try:
        for child in dir_path.glob("*.json"):
            child.unlink()
        dir_path.rmdir()
    except OSError as exc:
        return False, f"failed deleting profile: {exc}"
    global ACTIVE_KEY_PROFILE
    if ACTIVE_KEY_PROFILE == normalized:
        ACTIVE_KEY_PROFILE = PROFILE_SMALL
        load_active_profile_bindings()
    return True, f"Deleted profile: {normalized}"


def rename_key_profile(profile: str, new_profile: str) -> tuple[bool, str]:
    source = _normalize_profile_name(profile)
    target = _normalize_profile_name(new_profile)
    if source in BUILTIN_PROFILES:
        return False, "cannot rename built-in profile"
    if target in BUILTIN_PROFILES:
        return False, "cannot rename to built-in profile name"
    if source == target:
        return True, f"Profile already named: {source}"
    profiles = set(list_key_profiles())
    if source not in profiles:
        return False, f"profile not found: {source}"
    if target in profiles:
        return False, f"profile already exists: {target}"

    src_dir = _safe_resolve_path(KEYBINDINGS_PROFILES_DIR / source)
    dst_dir = _safe_resolve_path(KEYBINDINGS_PROFILES_DIR / target)
    try:
        src_dir.rename(dst_dir)
    except OSError as exc:
        return False, f"failed renaming profile: {exc}"

    global ACTIVE_KEY_PROFILE
    if ACTIVE_KEY_PROFILE == source:
        ACTIVE_KEY_PROFILE = target
        ok, msg = load_active_profile_bindings()
        if not ok:
            return False, msg
    return True, f"Renamed profile {source} -> {target}"


def cycle_key_profile(step: int = 1) -> tuple[bool, str, str]:
    profiles = list_key_profiles()
    if not profiles:
        return False, "no profiles available", ACTIVE_KEY_PROFILE
    try:
        idx = profiles.index(ACTIVE_KEY_PROFILE)
    except ValueError:
        idx = 0
    next_idx = (idx + step) % len(profiles)
    next_profile = profiles[next_idx]
    ok, msg = set_active_key_profile(next_profile)
    if not ok:
        return False, msg, ACTIVE_KEY_PROFILE
    load_active_profile_bindings()
    return True, msg, next_profile


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(path)


def save_keybindings_file(
    dimension: int,
    file_path: str | None = None,
    profile: str | None = None,
) -> Tuple[bool, str]:
    try:
        groups = _binding_groups_for_dimension(dimension)
        external_path = _validate_optional_external_path(file_path)
        selected_profile = _normalize_profile_name(profile) if profile else ACTIVE_KEY_PROFILE
        path = external_path if external_path is not None else keybinding_file_path_for_profile(
            dimension, selected_profile
        )
    except ValueError as exc:
        return False, str(exc)

    payload = {
        "dimension": dimension,
        "profile": selected_profile,
        "bindings": {
            group_name: _serialize_binding_group(binding_map)
            for group_name, binding_map in groups.items()
        },
    }

    encoded_payload = json.dumps(payload, indent=2, sort_keys=True)
    try:
        _atomic_write(path, encoded_payload)
        if external_path is None and selected_profile == PROFILE_SMALL:
            legacy_path = _legacy_keybinding_file_path(dimension)
            _atomic_write(legacy_path, encoded_payload)
    except OSError as exc:
        return False, f"Failed saving keybindings: {exc}"

    return True, f"Saved keybindings to {path}"


def load_keybindings_file(
    dimension: int,
    file_path: str | None = None,
    profile: str | None = None,
) -> Tuple[bool, str]:
    try:
        groups = _binding_groups_for_dimension(dimension)
        external_path = _validate_optional_external_path(file_path)
        selected_profile = _normalize_profile_name(profile) if profile else ACTIVE_KEY_PROFILE
        path = external_path if external_path is not None else keybinding_file_path_for_profile(
            dimension, selected_profile
        )
        if external_path is None and not path.exists() and selected_profile == PROFILE_SMALL:
            path = _legacy_keybinding_file_path(dimension)
    except ValueError as exc:
        return False, str(exc)

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"Failed loading keybindings: {exc}"

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return False, f"Invalid keybindings JSON: {exc}"

    bindings_payload = payload.get("bindings")
    if not isinstance(bindings_payload, dict):
        return False, "Invalid keybindings JSON: missing 'bindings' object"

    for group_name, target in groups.items():
        raw_group = bindings_payload.get(group_name)
        if raw_group is None and len(groups) == 1:
            # Compatibility: allow {"bindings": {"move_x_neg": [...]}} in 2D-only files.
            raw_group = bindings_payload
        if raw_group is None and dimension == 2 and group_name == "game":
            # Compatibility for legacy 2D schema now that 2D also includes system bindings.
            raw_group = bindings_payload
        _apply_group_payload(target, raw_group)

    _sanitize_runtime_bindings()
    _rebuild_control_lines()
    return True, f"Loaded keybindings from {path}"


_KEYBINDINGS_INITIALIZED = False


def _ensure_profile_files(profile: str) -> None:
    selected = _normalize_profile_name(profile)
    reset_keybindings_to_profile_defaults(selected)
    for dimension in (2, 3, 4):
        preferred = keybinding_file_path_for_profile(dimension, selected)
        if preferred.exists():
            continue
        if selected == PROFILE_SMALL:
            legacy = _legacy_keybinding_file_path(dimension)
            if legacy.exists():
                preferred.parent.mkdir(parents=True, exist_ok=True)
                preferred.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
                continue
        save_keybindings_file(dimension, profile=selected)


def load_active_profile_bindings() -> tuple[bool, str]:
    selected = ACTIVE_KEY_PROFILE
    reset_keybindings_to_profile_defaults(selected)
    messages: list[str] = []
    for dimension in (2, 3, 4):
        ok, msg = load_keybindings_file(dimension, profile=selected)
        if not ok:
            ok_save, save_msg = save_keybindings_file(dimension, profile=selected)
            if not ok_save:
                return False, save_msg
            messages.append(msg)
            continue
        messages.append(msg)
    return True, "; ".join(messages)


def initialize_keybinding_files() -> None:
    global _KEYBINDINGS_INITIALIZED
    if _KEYBINDINGS_INITIALIZED:
        return
    for builtin in BUILTIN_PROFILES:
        _ensure_profile_files(builtin)
    load_active_profile_bindings()
    _KEYBINDINGS_INITIALIZED = True


def reset_active_profile_bindings(dimension: int | None = None) -> tuple[bool, str]:
    selected = ACTIVE_KEY_PROFILE
    reset_keybindings_to_profile_defaults(selected)
    dimensions = (dimension,) if dimension is not None else (2, 3, 4)
    messages: list[str] = []
    for dim in dimensions:
        ok, msg = save_keybindings_file(dim, profile=selected)
        if not ok:
            return False, msg
        messages.append(msg)
    ok_load, msg_load = load_active_profile_bindings()
    if not ok_load:
        return False, msg_load
    return True, f"Reset keybindings for profile {selected}; {'; '.join(messages)}"


_rebuild_control_lines()
