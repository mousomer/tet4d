"""Shared keyboard bindings for 2D/3D/4D frontends."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Tuple

import pygame
from tet4d.engine.runtime.keybinding_runtime_state import (
    KEYBINDING_STATE,
    KEY_PROFILE_ENV,  # noqa: F401 - re-exported for callers
    PROFILE_FULL,  # noqa: F401 - re-exported for callers
    PROFILE_MACBOOK,  # noqa: F401 - re-exported for callers
    PROFILE_TINY,  # noqa: F401 - re-exported for callers
    REBIND_CONFLICT_CANCEL,  # noqa: F401 - re-exported for callers
    REBIND_CONFLICT_OPTIONS,  # noqa: F401 - re-exported for callers
    REBIND_CONFLICT_REPLACE,
    REBIND_CONFLICT_SWAP,  # noqa: F401 - re-exported for callers
    KeyBindingMap,
    KeyTuple,
    cycle_rebind_conflict_mode,  # noqa: F401 - re-exported for callers
    normalize_rebind_conflict_mode,
)
from tet4d.engine.runtime.keybinding_store import (
    BUILTIN_PROFILES,
    KEYBINDING_PAYLOAD_SCHEMA_VERSION,
    PROFILE_SMALL,
    SUPPORTED_DIMENSIONS,
    clone_keybinding_dimension,
    delete_key_profile as delete_key_profile_files,
    keybinding_file_path_for_profile as runtime_keybinding_file_path_for_profile,
    list_key_profiles as list_key_profiles_from_store,
    load_keybindings_payload,
    next_auto_profile_name as next_auto_profile_name_from_store,
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

def default_game_bindings_for_profile(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
    return KEYBINDING_STATE.default_game_bindings_for_profile(profile)


def default_camera_bindings_for_profile(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap]:
    return KEYBINDING_STATE.default_camera_bindings_for_profile(profile)


def default_explorer_bindings_for_profile(
    profile: str,
) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
    return KEYBINDING_STATE.default_explorer_bindings_for_profile(profile)


def default_system_bindings_for_profile(profile: str) -> KeyBindingMap:
    return KEYBINDING_STATE.default_system_bindings_for_profile(profile)


_DEFAULTS_VERSION = KEYBINDING_STATE.defaults_version
DISABLED_KEYS_2D = KEYBINDING_STATE.disabled_keys_2d


def get_active_key_profile() -> str:
    return KEYBINDING_STATE.active_profile


KEYBINDING_STATE.reset_keybindings_to_profile_defaults(
    reset_camera_key_fallback=pygame.K_BACKSPACE
)
ACTIVE_KEY_PROFILE = KEYBINDING_STATE.active_profile


def active_key_profile() -> str:
    return KEYBINDING_STATE.active_profile


def _selected_profile(profile: str | None = None) -> str:
    return KEYBINDING_STATE.selected_profile(profile)


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


SYSTEM_KEYS = KEYBINDING_STATE.system_keys
KEYS_2D = KEYBINDING_STATE.keys_2d
KEYS_3D = KEYBINDING_STATE.keys_3d
KEYS_4D = KEYBINDING_STATE.keys_4d
EXPLORER_KEYS_2D = KEYBINDING_STATE.explorer_keys_2d
EXPLORER_KEYS_3D = KEYBINDING_STATE.explorer_keys_3d
EXPLORER_KEYS_4D = KEYBINDING_STATE.explorer_keys_4d
CAMERA_KEYS_3D = KEYBINDING_STATE.camera_keys_3d
CAMERA_KEYS_4D = KEYBINDING_STATE.camera_keys_4d


def reset_keybindings_to_profile_defaults(profile: str | None = None) -> None:
    KEYBINDING_STATE.reset_keybindings_to_profile_defaults(
        profile,
        reset_camera_key_fallback=pygame.K_BACKSPACE,
    )


def _sanitize_runtime_bindings(
    *,
    camera_defaults_4d: Mapping[str, KeyTuple] | None = None,
) -> None:
    KEYBINDING_STATE.sanitize_runtime_bindings(
        camera_defaults_4d=camera_defaults_4d,
        reset_camera_key_fallback=pygame.K_BACKSPACE,
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
    target.clear()
    target.update(updated)


def _resolve_keybindings_io_context(
    dimension: int,
    *,
    file_path: str | None,
    profile: str | None,
) -> tuple[Dict[str, MutableMapping[str, KeyTuple]], Path, str]:
    groups = KEYBINDING_STATE.binding_groups_for_dimension(dimension)
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
    return KEYBINDING_STATE.runtime_binding_groups_for_dimension(dimension)


def binding_actions_for_dimension(dimension: int) -> Dict[str, list[str]]:
    return KEYBINDING_STATE.binding_actions_for_dimension(dimension)


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
    selected_mode = normalize_rebind_conflict_mode(conflict_mode)
    ok, msg, conflicts = KEYBINDING_STATE.apply_rebind_action_key(
        dimension,
        group,
        action,
        key,
        conflict_mode=selected_mode,
        reset_camera_key_fallback=pygame.K_BACKSPACE,
    )
    if not ok:
        return False, msg
    key_name = display_key_name(key)
    return True, _rebind_success_message(
        group=group,
        action=action,
        key_name=key_name,
        conflict_mode=selected_mode,
        conflicts=list(conflicts),
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
    ok, msg = KEYBINDING_STATE.set_active_profile(profile)
    if not ok:
        return False, msg
    global ACTIVE_KEY_PROFILE
    ACTIVE_KEY_PROFILE = KEYBINDING_STATE.active_profile
    return True, msg


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
    target = normalize_profile_name(target_profile)
    source = (
        normalize_profile_name(source_profile)
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
    normalized = normalize_profile_name(profile)
    ok, msg = delete_key_profile_files(normalized)
    if not ok:
        return ok, msg
    global ACTIVE_KEY_PROFILE
    if ACTIVE_KEY_PROFILE == normalized:
        KEYBINDING_STATE.set_active_profile(PROFILE_SMALL)
        ACTIVE_KEY_PROFILE = PROFILE_SMALL
        load_active_profile_bindings()
    return ok, msg


def rename_key_profile(profile: str, new_profile: str) -> tuple[bool, str]:
    source = normalize_profile_name(profile)
    target = normalize_profile_name(new_profile)
    ok, msg = rename_key_profile_files(source, target)
    if not ok:
        return ok, msg

    global ACTIVE_KEY_PROFILE
    if ACTIVE_KEY_PROFILE == source:
        KEYBINDING_STATE.set_active_profile(target)
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
    explorer_2d, explorer_3d, explorer_4d = default_explorer_bindings_for_profile(profile)
    camera_3d, camera_4d = default_camera_bindings_for_profile(profile)
    system = default_system_bindings_for_profile(profile)
    group_map = {
        2: {"game": game_2d, "explorer": explorer_2d, "system": system},
        3: {"game": game_3d, "explorer": explorer_3d, "camera": camera_3d, "system": system},
        4: {"game": game_4d, "explorer": explorer_4d, "camera": camera_4d, "system": system},
    }
    bindings = group_map.get(dimension)
    if bindings is None:
        raise ValueError("dimension must be one of: 2, 3, 4")
    return {
        "schema_version": KEYBINDING_PAYLOAD_SCHEMA_VERSION,
        "defaults_version": _DEFAULTS_VERSION,
        "dimension": dimension,
        "profile": normalize_profile_name(profile),
        "bindings": {
            group_name: _serialize_binding_group(binding_map)
            for group_name, binding_map in bindings.items()
        },
    }


def _builtin_profile_payload_is_stale(
    dimension: int,
    *,
    profile: str,
) -> bool:
    expected = _binding_payload_for_dimension(dimension, profile)
    ok, _msg, payload = load_keybindings_payload(
        dimension,
        profile=profile,
        active_profile=ACTIVE_KEY_PROFILE,
    )
    if not ok or payload is None:
        return True
    return payload != expected


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
        "schema_version": KEYBINDING_PAYLOAD_SCHEMA_VERSION,
        "dimension": dimension,
        "profile": selected_profile,
        "bindings": {
            group_name: _serialize_binding_group(binding_map)
            for group_name, binding_map in groups.items()
        },
    }
    if selected_profile in BUILTIN_PROFILES:
        payload["defaults_version"] = _DEFAULTS_VERSION
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


def _remove_obsolete_small_profile_dir() -> None:
    obsolete_dir = profile_keybinding_file_path(2, PROFILE_FULL).parent.parent / PROFILE_SMALL
    if not obsolete_dir.exists():
        return
    shutil.rmtree(obsolete_dir, ignore_errors=True)


def _ensure_profile_files(profile: str) -> None:
    selected = normalize_profile_name(profile)
    reset_keybindings_to_profile_defaults(selected)
    for dimension in SUPPORTED_DIMENSIONS:
        preferred = keybinding_file_path_for_profile(dimension, selected)
        if preferred.exists():
            if selected in BUILTIN_PROFILES and _builtin_profile_payload_is_stale(
                dimension,
                profile=selected,
            ):
                save_keybindings_payload(
                    dimension,
                    _binding_payload_for_dimension(dimension, selected),
                    profile=selected,
                    active_profile=ACTIVE_KEY_PROFILE,
                )
            continue
        save_keybindings_file(dimension, profile=selected)


def load_active_profile_bindings() -> tuple[bool, str]:
    selected = ACTIVE_KEY_PROFILE
    reset_keybindings_to_profile_defaults(selected)
    messages: list[str] = []
    for dimension in SUPPORTED_DIMENSIONS:
        ok, msg = load_keybindings_file(dimension, profile=selected)
        if not ok:
            if selected not in BUILTIN_PROFILES:
                return False, msg
            ok_save, save_msg = save_keybindings_file(dimension, profile=selected)
            if not ok_save:
                return False, save_msg
            messages.append(f"{msg}; regenerated built-in defaults")
            continue
        messages.append(msg)
    return True, "; ".join(messages)


def initialize_keybinding_files() -> None:
    global _KEYBINDINGS_INITIALIZED
    if _KEYBINDINGS_INITIALIZED:
        return
    _remove_obsolete_small_profile_dir()
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
