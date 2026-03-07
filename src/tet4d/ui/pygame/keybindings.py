"""Shared keyboard bindings for 2D/3D/4D frontends."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Tuple

import pygame
from tet4d.engine.runtime import keybinding_store as runtime_keybinding_store
from tet4d.engine.runtime.keybinding_store import (
    BUILTIN_PROFILES,
    PROFILE_SMALL,
    SUPPORTED_DIMENSIONS,
    active_key_profile_from_env,
    clone_keybinding_dimension,
    delete_key_profile as delete_key_profile_files,
    load_keybinding_defaults_payload,
    keybinding_file_path_for_profile as runtime_keybinding_file_path_for_profile,
    list_key_profiles as list_key_profiles_from_store,
    load_keybindings_payload,
    next_auto_profile_name as next_auto_profile_name_from_store,
    normalize_builtin_profile,
    normalize_profile_name,
    profile_keybinding_file_path as runtime_profile_keybinding_file_path,
    rename_key_profile as rename_key_profile_files,
    resolve_keybinding_io_path as resolve_keybindings_io_path_from_store,
    save_keybindings_payload,
)
from tet4d.engine.ui_logic.keybindings_catalog import (
    binding_action_description,  # noqa: F401 - re-exported for UI callers
    binding_group_description,  # noqa: F401 - re-exported for UI callers
    binding_group_label,  # noqa: F401 - re-exported for UI callers
)
from tet4d.ui.pygame.input.key_display import display_key_name

KeyTuple = Tuple[int, ...]
KeyBindingMap = Dict[str, KeyTuple]

KEY_PROFILE_ENV = runtime_keybinding_store.KEY_PROFILE_ENV
PROFILE_FULL = runtime_keybinding_store.PROFILE_FULL
PROFILE_MACBOOK = runtime_keybinding_store.PROFILE_MACBOOK
PROFILE_TINY = runtime_keybinding_store.PROFILE_TINY

REBIND_CONFLICT_REPLACE = "replace"
REBIND_CONFLICT_SWAP = "swap"
REBIND_CONFLICT_CANCEL = "cancel"
REBIND_CONFLICT_OPTIONS = (
    REBIND_CONFLICT_REPLACE,
    REBIND_CONFLICT_SWAP,
    REBIND_CONFLICT_CANCEL,
)


def _load_defaults_payload() -> dict:
    return load_keybinding_defaults_payload()


_DEFAULTS = _load_defaults_payload()
_PROFILE_MAP = _DEFAULTS.get("profiles", {})


def _bindings_for(
    profile: str, section: str, dim_key: str | None = None
) -> KeyBindingMap:
    profile_payload = _PROFILE_MAP.get(profile, {})
    section_payload = profile_payload.get(section, {})
    if dim_key is not None:
        section_payload = section_payload.get(dim_key, {})
    if not isinstance(section_payload, dict):
        return {}
    return {
        action: tuple(int(k) for k in keys) for action, keys in section_payload.items()
    }


def default_game_bindings_for_profile(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
    return (
        _bindings_for(profile, "game", "d2"),
        _bindings_for(profile, "game", "d3"),
        _bindings_for(profile, "game", "d4"),
    )


def default_camera_bindings_for_profile(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap]:
    return (
        _bindings_for(profile, "camera", "d3"),
        _bindings_for(profile, "camera", "d4"),
    )


def default_system_bindings_for_profile(profile: str) -> KeyBindingMap:
    return _bindings_for(profile, "system")


DISABLED_KEYS_2D = tuple(int(k) for k in _DEFAULTS.get("disabled_keys_2d", ()))


def _normalize_profile(raw: str | None) -> str:
    return normalize_builtin_profile(raw)


def _normalize_profile_name(raw: str) -> str:
    return normalize_profile_name(raw)


def get_active_key_profile() -> str:
    return active_key_profile_from_env()


ACTIVE_KEY_PROFILE = get_active_key_profile()


def active_key_profile() -> str:
    return ACTIVE_KEY_PROFILE


def _selected_profile(profile: str | None = None) -> str:
    if not profile:
        return ACTIVE_KEY_PROFILE
    return _normalize_profile_name(profile)


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


def profile_keybinding_file_path(dimension: int, profile: str) -> Path:
    return runtime_profile_keybinding_file_path(dimension, profile)


def keybinding_file_path_for_profile(
    dimension: int, profile: str | None = None
) -> Path:
    return runtime_keybinding_file_path_for_profile(
        dimension,
        profile=profile,
        active_profile=ACTIVE_KEY_PROFILE,
    )


def key_matches(bindings: Mapping[str, KeyTuple], action: str, key: int) -> bool:
    return key in bindings.get(action, ())


def _replace_map(
    target: MutableMapping[str, KeyTuple], source: Mapping[str, KeyTuple]
) -> None:
    target.clear()
    target.update(source)


_DEFAULT_KEYS_2D, _DEFAULT_KEYS_3D, _DEFAULT_KEYS_4D = (
    default_game_bindings_for_profile(ACTIVE_KEY_PROFILE)
)
_DEFAULT_CAMERA_KEYS_3D, _DEFAULT_CAMERA_KEYS_4D = default_camera_bindings_for_profile(
    ACTIVE_KEY_PROFILE
)
_DEFAULT_SYSTEM_KEYS = default_system_bindings_for_profile(ACTIVE_KEY_PROFILE)


SYSTEM_KEYS: KeyBindingMap = dict(_DEFAULT_SYSTEM_KEYS)
KEYS_2D: KeyBindingMap = dict(_DEFAULT_KEYS_2D)
KEYS_3D: KeyBindingMap = dict(_DEFAULT_KEYS_3D)
KEYS_4D: KeyBindingMap = dict(_DEFAULT_KEYS_4D)
CAMERA_KEYS_3D: KeyBindingMap = dict(_DEFAULT_CAMERA_KEYS_3D)
CAMERA_KEYS_4D: KeyBindingMap = dict(_DEFAULT_CAMERA_KEYS_4D)


def reset_keybindings_to_profile_defaults(profile: str | None = None) -> None:
    selected = _selected_profile(profile)
    keys_2d, keys_3d, keys_4d = default_game_bindings_for_profile(selected)
    camera_3d, camera_4d = default_camera_bindings_for_profile(selected)
    system_keys = default_system_bindings_for_profile(selected)
    _replace_map(SYSTEM_KEYS, system_keys)
    _replace_map(KEYS_2D, keys_2d)
    _replace_map(KEYS_3D, keys_3d)
    _replace_map(KEYS_4D, keys_4d)
    _replace_map(CAMERA_KEYS_3D, camera_3d)
    _replace_map(CAMERA_KEYS_4D, camera_4d)
    _sanitize_runtime_bindings(camera_defaults_4d=camera_4d)


def _sanitize_runtime_bindings(
    *,
    camera_defaults_4d: Mapping[str, KeyTuple] | None = None,
) -> None:
    fallback_camera_4d = (
        dict(camera_defaults_4d)
        if camera_defaults_4d is not None
        else default_camera_bindings_for_profile(ACTIVE_KEY_PROFILE)[1]
    )
    # 4D gameplay keys must not be shadowed by 4D camera/view keys.
    occupied = set()
    for mapping in (KEYS_4D, SYSTEM_KEYS):
        for keys in mapping.values():
            occupied.update(keys)

    sanitized_camera_4d: KeyBindingMap = {}
    for action, keys in CAMERA_KEYS_4D.items():
        filtered = tuple(key for key in keys if key not in occupied)
        if not filtered:
            filtered = fallback_camera_4d.get(action, ())
            filtered = tuple(key for key in filtered if key not in occupied)
        if action == "reset" and not filtered:
            filtered = (pygame.K_BACKSPACE,)
        sanitized_camera_4d[action] = filtered
    _replace_map(CAMERA_KEYS_4D, sanitized_camera_4d)


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
    parsed = tuple(
        key for raw_key in raw_keys if (key := _parse_key(raw_key)) is not None
    )
    return parsed or None


def _apply_group_payload(
    target: MutableMapping[str, KeyTuple], raw_group: object
) -> None:
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


def _binding_groups_for_dimension(
    dimension: int,
) -> Dict[str, MutableMapping[str, KeyTuple]]:
    group_map: dict[int, Dict[str, MutableMapping[str, KeyTuple]]] = {
        2: {
            "game": KEYS_2D,
            "system": SYSTEM_KEYS,
        },
        3: {
            "game": KEYS_3D,
            "camera": CAMERA_KEYS_3D,
            "system": SYSTEM_KEYS,
        },
        4: {
            "game": KEYS_4D,
            "camera": CAMERA_KEYS_4D,
            "system": SYSTEM_KEYS,
        },
    }
    groups = group_map.get(dimension)
    if groups is None:
        raise ValueError("dimension must be one of: 2, 3, 4")
    return groups


def _resolve_keybindings_io_context(
    dimension: int,
    *,
    file_path: str | None,
    profile: str | None,
) -> tuple[Dict[str, MutableMapping[str, KeyTuple]], Path, str]:
    groups = _binding_groups_for_dimension(dimension)
    path, selected_profile = resolve_keybindings_io_path_from_store(
        dimension,
        file_path=file_path,
        profile=profile,
        active_profile=ACTIVE_KEY_PROFILE,
    )
    return groups, path, selected_profile


def runtime_binding_groups_for_dimension(
    dimension: int,
) -> Dict[str, Mapping[str, KeyTuple]]:
    groups = _binding_groups_for_dimension(dimension)
    return {group: dict(bindings) for group, bindings in groups.items()}



def binding_actions_for_dimension(dimension: int) -> Dict[str, list[str]]:
    groups = _binding_groups_for_dimension(dimension)
    return {group: sorted(bindings.keys()) for group, bindings in groups.items()}


def _remove_key_from_tuple(keys: KeyTuple, key: int) -> KeyTuple:
    return tuple(candidate for candidate in keys if candidate != key)


def _find_conflicts(
    groups: Mapping[str, Mapping[str, KeyTuple]],
    key: int,
    skip_group: str,
    skip_action: str,
) -> list[tuple[str, str]]:
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
    return (
        [
            (conflict_group, conflict_action)
            for conflict_group, conflict_action in conflicts
            if conflict_group in {"game", "system"}
        ]
        if group == "camera"
        else []
    )


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
        conflict_map[conflict_action] = _remove_key_from_tuple(
            conflict_map[conflict_action], key
        )


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
    else:
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
    key_name = display_key_name(key)
    return True, _rebind_success_message(
        group=group,
        action=action,
        key_name=key_name,
        conflict_mode=selected_mode,
        conflicts=conflicts,
    )


def keybinding_file_path(dimension: int) -> Path:
    return keybinding_file_path_for_profile(dimension, ACTIVE_KEY_PROFILE)


def keybinding_file_label(dimension: int) -> str:
    path = keybinding_file_path(dimension)
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def list_key_profiles() -> list[str]:
    return list_key_profiles_from_store()


def next_auto_profile_name(prefix: str = "custom") -> str:
    return next_auto_profile_name_from_store(prefix)


def set_active_key_profile(profile: str) -> tuple[bool, str]:
    try:
        normalized = _normalize_profile_name(profile)
    except ValueError as exc:
        return False, str(exc)
    global ACTIVE_KEY_PROFILE
    ACTIVE_KEY_PROFILE = normalized
    return True, f"Active key profile: {normalized}"


def create_auto_profile(
    base_profile: str | None = None,
) -> tuple[bool, str, str | None]:
    candidate = next_auto_profile_name("custom")
    ok, msg = clone_key_profile(candidate, base_profile)
    if not ok:
        return False, msg, None
    return True, msg, candidate


def clone_key_profile(
    target_profile: str, source_profile: str | None = None
) -> tuple[bool, str]:
    target = _normalize_profile_name(target_profile)
    source = (
        _normalize_profile_name(source_profile)
        if source_profile
        else ACTIVE_KEY_PROFILE
    )
    if target in BUILTIN_PROFILES:
        return False, "cannot overwrite built-in profile"
    if target in list_key_profiles():
        return False, f"profile already exists: {target}"
    try:
        for dimension in SUPPORTED_DIMENSIONS:
            _clone_keybinding_dimension(source, target, dimension)
    except (OSError, ValueError) as exc:
        return False, f"failed creating profile {target}: {exc}"
    return True, f"Created profile: {target}"


def delete_key_profile(profile: str) -> tuple[bool, str]:
    normalized = _normalize_profile_name(profile)
    ok, msg = delete_key_profile_files(normalized)
    if not ok:
        return ok, msg
    global ACTIVE_KEY_PROFILE
    if ACTIVE_KEY_PROFILE == normalized:
        ACTIVE_KEY_PROFILE = PROFILE_SMALL
        load_active_profile_bindings()
    return ok, msg


def rename_key_profile(profile: str, new_profile: str) -> tuple[bool, str]:
    source = _normalize_profile_name(profile)
    target = _normalize_profile_name(new_profile)
    ok, msg = rename_key_profile_files(source, target)
    if not ok:
        return ok, msg

    global ACTIVE_KEY_PROFILE
    if ACTIVE_KEY_PROFILE == source:
        ACTIVE_KEY_PROFILE = target
        ok, msg = load_active_profile_bindings()
        if not ok:
            return False, msg
    return True, msg


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


def _binding_payload_for_dimension(dimension: int, profile: str) -> dict[str, object]:
    game_2d, game_3d, game_4d = default_game_bindings_for_profile(profile)
    camera_3d, camera_4d = default_camera_bindings_for_profile(profile)
    system = default_system_bindings_for_profile(profile)
    group_map = {
        2: {"game": game_2d, "system": system},
        3: {"game": game_3d, "camera": camera_3d, "system": system},
        4: {"game": game_4d, "camera": camera_4d, "system": system},
    }
    bindings = group_map.get(dimension)
    if bindings is None:
        raise ValueError("dimension must be one of: 2, 3, 4")
    return {
        "dimension": dimension,
        "profile": _normalize_profile_name(profile),
        "bindings": {
            group_name: _serialize_binding_group(binding_map)
            for group_name, binding_map in bindings.items()
        },
    }


def _clone_keybinding_dimension(
    source_profile: str, target_profile: str, dimension: int
) -> None:
    clone_keybinding_dimension(
        source_profile,
        target_profile,
        dimension,
        materialize_source=lambda: save_keybindings_payload(
            dimension,
            _binding_payload_for_dimension(dimension, source_profile),
            profile=source_profile,
            active_profile=ACTIVE_KEY_PROFILE,
        ),
    )


def save_keybindings_file(
    dimension: int,
    file_path: str | None = None,
    profile: str | None = None,
) -> Tuple[bool, str]:
    try:
        groups, _path, selected_profile = _resolve_keybindings_io_context(
            dimension,
            file_path=file_path,
            profile=profile,
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
    return save_keybindings_payload(
        dimension,
        payload,
        file_path=file_path,
        profile=profile,
        active_profile=ACTIVE_KEY_PROFILE,
    )


def load_keybindings_file(
    dimension: int,
    file_path: str | None = None,
    profile: str | None = None,
) -> Tuple[bool, str]:
    try:
        groups, _path, _selected_profile = _resolve_keybindings_io_context(
            dimension,
            file_path=file_path,
            profile=profile,
        )
    except ValueError as exc:
        return False, str(exc)

    ok, msg, payload = load_keybindings_payload(
        dimension,
        file_path=file_path,
        profile=profile,
        active_profile=ACTIVE_KEY_PROFILE,
    )
    if not ok or payload is None:
        return ok, msg

    bindings_payload = payload.get("bindings")
    if not isinstance(bindings_payload, dict):
        return False, "Invalid keybindings JSON: missing 'bindings' object"

    for group_name, target in groups.items():
        raw_group = bindings_payload.get(group_name)
        if raw_group is None and dimension == 2 and group_name == "game":
            # Compatibility for legacy 2D schema now that 2D also includes system bindings.
            raw_group = bindings_payload
        _apply_group_payload(target, raw_group)

    _sanitize_runtime_bindings()
    return True, msg


_KEYBINDINGS_INITIALIZED = False


def _ensure_profile_files(profile: str) -> None:
    selected = _normalize_profile_name(profile)
    reset_keybindings_to_profile_defaults(selected)
    for dimension in SUPPORTED_DIMENSIONS:
        preferred = keybinding_file_path_for_profile(dimension, selected)
        if preferred.exists():
            continue
        save_keybindings_file(dimension, profile=selected)


def load_active_profile_bindings() -> tuple[bool, str]:
    selected = ACTIVE_KEY_PROFILE
    reset_keybindings_to_profile_defaults(selected)
    messages: list[str] = []
    for dimension in SUPPORTED_DIMENSIONS:
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
    dimensions = (dimension,) if dimension is not None else SUPPORTED_DIMENSIONS
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
