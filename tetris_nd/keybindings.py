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
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence, Tuple

import pygame


KeyTuple = Tuple[int, ...]
KeyBindingMap = Dict[str, KeyTuple]

PROFILE_SMALL = "small"
PROFILE_FULL = "full"
KEY_PROFILE_ENV = "TETRIS_KEY_PROFILE"

KEYBINDINGS_DIR = Path(__file__).resolve().parent.parent / "keybindings"
KEYBINDING_FILES = {
    2: KEYBINDINGS_DIR / "2d.json",
    3: KEYBINDINGS_DIR / "3d.json",
    4: KEYBINDINGS_DIR / "4d.json",
}


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


_DEFAULT_MOVEMENT_2D, _DEFAULT_MOVEMENT_3D, _DEFAULT_MOVEMENT_4D = _profile_movement_maps(
    ACTIVE_KEY_PROFILE
)
_DEFAULT_KEYS_2D = _merge_bindings(_DEFAULT_MOVEMENT_2D, ROTATIONS_2D)
_DEFAULT_KEYS_3D = _merge_bindings(_DEFAULT_MOVEMENT_3D, ROTATIONS_3D)
_DEFAULT_KEYS_4D = _merge_bindings(_DEFAULT_MOVEMENT_4D, ROTATIONS_4D)
_DEFAULT_CAMERA_KEYS_3D: KeyBindingMap = {
    "yaw_neg": (pygame.K_j,),
    "yaw_pos": (pygame.K_l,),
    "pitch_pos": (pygame.K_i,),
    "pitch_neg": (pygame.K_k,),
    "zoom_in": (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS),
    "zoom_out": (pygame.K_MINUS, pygame.K_KP_MINUS),
    "reset": (pygame.K_0,),
    "cycle_projection": (pygame.K_p,),
}
_DEFAULT_CAMERA_KEYS_4D: KeyBindingMap = {
    "yaw_neg": (pygame.K_j,),
    "yaw_pos": (pygame.K_l,),
    "pitch_pos": (pygame.K_i,),
    "pitch_neg": (pygame.K_k,),
    "zoom_in": (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS),
    "zoom_out": (pygame.K_MINUS, pygame.K_KP_MINUS),
    "reset": (pygame.K_0,),
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
            ("action", SYSTEM_KEYS, "toggle_grid", "toggle grid"),
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
        (*common_3d_specs, ("action", SYSTEM_KEYS, "toggle_grid", "toggle grid")),
    )
    CONTROL_LINES_ND_3D[:] = _build_control_section(
        "Controls:",
        (
            *common_3d_specs,
            ("pair", SLICE_KEYS_3D, "slice_z_neg", "slice_z_pos", "slice z"),
            ("action", SYSTEM_KEYS, "toggle_grid", "toggle grid"),
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
            ("action", SYSTEM_KEYS, "toggle_grid", "toggle grid"),
            ("action", SYSTEM_KEYS, "restart", "restart"),
            ("action", SYSTEM_KEYS, "menu", "menu"),
            ("action", SYSTEM_KEYS, "quit", "quit"),
        ),
    )

    CONTROL_LINES_3D_CAMERA[:] = _build_control_section(
        "Camera:",
        (
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
        return {"game": KEYS_2D}
    if dimension == 3:
        return {
            "game": KEYS_3D,
            "camera": CAMERA_KEYS_3D,
            "slice": SLICE_KEYS_3D,
        }
    if dimension == 4:
        return {
            "game": KEYS_4D,
            "slice": SLICE_KEYS_4D,
            "camera": CAMERA_KEYS_4D,
        }
    raise ValueError("dimension must be one of: 2, 3, 4")


def keybinding_file_path(dimension: int) -> Path:
    path = KEYBINDING_FILES.get(dimension)
    if path is None:
        raise ValueError("dimension must be one of: 2, 3, 4")
    return path


def keybinding_file_label(dimension: int) -> str:
    path = keybinding_file_path(dimension)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def save_keybindings_file(dimension: int, file_path: str | None = None) -> Tuple[bool, str]:
    try:
        groups = _binding_groups_for_dimension(dimension)
        path = Path(file_path) if file_path else keybinding_file_path(dimension)
    except ValueError as exc:
        return False, str(exc)

    payload = {
        "dimension": dimension,
        "profile": ACTIVE_KEY_PROFILE,
        "bindings": {
            group_name: _serialize_binding_group(binding_map)
            for group_name, binding_map in groups.items()
        },
    }

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    except OSError as exc:
        return False, f"Failed saving keybindings: {exc}"

    return True, f"Saved keybindings to {path}"


def load_keybindings_file(dimension: int, file_path: str | None = None) -> Tuple[bool, str]:
    try:
        groups = _binding_groups_for_dimension(dimension)
        path = Path(file_path) if file_path else keybinding_file_path(dimension)
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
        _apply_group_payload(target, raw_group)

    _rebuild_control_lines()
    return True, f"Loaded keybindings from {path}"


_KEYBINDINGS_INITIALIZED = False


def initialize_keybinding_files() -> None:
    global _KEYBINDINGS_INITIALIZED
    if _KEYBINDINGS_INITIALIZED:
        return
    for dimension in (2, 3, 4):
        path = keybinding_file_path(dimension)
        if path.exists():
            ok, _ = load_keybindings_file(dimension)
            if ok:
                continue
        save_keybindings_file(dimension)
    _KEYBINDINGS_INITIALIZED = True


_rebuild_control_lines()
