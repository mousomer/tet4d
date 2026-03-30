from __future__ import annotations

from collections.abc import Mapping, MutableMapping

from . import keybinding_store as runtime_keybinding_store
from .keybinding_store import (
    active_key_profile_from_env,
    load_keybinding_defaults_payload,
    normalize_builtin_profile,
    normalize_profile_name,
)

KeyTuple = tuple[int, ...]
KeyBindingMap = dict[str, KeyTuple]

REBIND_CONFLICT_REPLACE = "replace"
REBIND_CONFLICT_SWAP = "swap"
REBIND_CONFLICT_CANCEL = "cancel"
REBIND_CONFLICT_OPTIONS = (
    REBIND_CONFLICT_REPLACE,
    REBIND_CONFLICT_SWAP,
    REBIND_CONFLICT_CANCEL,
)


def _replace_map(
    target: MutableMapping[str, KeyTuple], source: Mapping[str, KeyTuple]
) -> None:
    target.clear()
    target.update(source)


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
    groups: Mapping[str, MutableMapping[str, KeyTuple]],
    binding_map: MutableMapping[str, KeyTuple],
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
    groups: Mapping[str, MutableMapping[str, KeyTuple]],
    key: int,
    conflicts: list[tuple[str, str]],
) -> None:
    for conflict_group, conflict_action in conflicts:
        conflict_map = groups[conflict_group]
        conflict_map[conflict_action] = _remove_key_from_tuple(
            conflict_map[conflict_action], key
        )


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


class KeybindingRuntimeState:
    def __init__(
        self,
        *,
        defaults_payload: dict[str, object] | None = None,
        active_profile: str | None = None,
    ) -> None:
        payload = defaults_payload or load_keybinding_defaults_payload()
        self._profile_map = payload.get("profiles", {})
        self.defaults_version = int(payload.get("version", 1))
        self.disabled_keys_2d = tuple(int(key) for key in payload.get("disabled_keys_2d", ()))
        self._active_profile = normalize_builtin_profile(active_profile)
        self.system_keys: KeyBindingMap = {}
        self.keys_2d: KeyBindingMap = {}
        self.keys_3d: KeyBindingMap = {}
        self.keys_4d: KeyBindingMap = {}
        self.explorer_keys_2d: KeyBindingMap = {}
        self.explorer_keys_3d: KeyBindingMap = {}
        self.explorer_keys_4d: KeyBindingMap = {}
        self.camera_keys_3d: KeyBindingMap = {}
        self.camera_keys_4d: KeyBindingMap = {}
        self.reset_keybindings_to_profile_defaults()

    @property
    def active_profile(self) -> str:
        return self._active_profile

    def bindings_for(
        self,
        profile: str,
        section: str,
        dim_key: str | None = None,
    ) -> KeyBindingMap:
        profile_payload = self._profile_map.get(profile, {})
        section_payload = profile_payload.get(section, {})
        if dim_key is not None:
            section_payload = section_payload.get(dim_key, {})
        if not isinstance(section_payload, dict):
            return {}
        return {
            action: tuple(int(key) for key in keys)
            for action, keys in section_payload.items()
        }

    def default_game_bindings_for_profile(
        self,
        profile: str,
    ) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
        return (
            self.bindings_for(profile, "game", "d2"),
            self.bindings_for(profile, "game", "d3"),
            self.bindings_for(profile, "game", "d4"),
        )

    def default_camera_bindings_for_profile(
        self,
        profile: str,
    ) -> tuple[KeyBindingMap, KeyBindingMap]:
        return (
            self.bindings_for(profile, "camera", "d3"),
            self.bindings_for(profile, "camera", "d4"),
        )

    def default_explorer_bindings_for_profile(
        self,
        profile: str,
    ) -> tuple[KeyBindingMap, KeyBindingMap, KeyBindingMap]:
        return (
            self.bindings_for(profile, "explorer", "d2"),
            self.bindings_for(profile, "explorer", "d3"),
            self.bindings_for(profile, "explorer", "d4"),
        )

    def default_system_bindings_for_profile(self, profile: str) -> KeyBindingMap:
        return self.bindings_for(profile, "system")

    def selected_profile(self, profile: str | None = None) -> str:
        if not profile:
            return self._active_profile
        return normalize_profile_name(profile)

    def set_active_profile(self, profile: str) -> tuple[bool, str]:
        try:
            normalized = normalize_profile_name(profile)
        except ValueError as exc:
            return False, str(exc)
        self._active_profile = normalized
        return True, f"Active key profile: {normalized}"

    def reset_keybindings_to_profile_defaults(
        self,
        profile: str | None = None,
        *,
        reset_camera_key_fallback: int | None = None,
    ) -> None:
        selected = self.selected_profile(profile)
        keys_2d, keys_3d, keys_4d = self.default_game_bindings_for_profile(selected)
        explorer_2d, explorer_3d, explorer_4d = self.default_explorer_bindings_for_profile(selected)
        camera_3d, camera_4d = self.default_camera_bindings_for_profile(selected)
        system_keys = self.default_system_bindings_for_profile(selected)
        _replace_map(self.system_keys, system_keys)
        _replace_map(self.keys_2d, keys_2d)
        _replace_map(self.keys_3d, keys_3d)
        _replace_map(self.keys_4d, keys_4d)
        _replace_map(self.explorer_keys_2d, explorer_2d)
        _replace_map(self.explorer_keys_3d, explorer_3d)
        _replace_map(self.explorer_keys_4d, explorer_4d)
        _replace_map(self.camera_keys_3d, camera_3d)
        _replace_map(self.camera_keys_4d, camera_4d)
        self.sanitize_runtime_bindings(
            camera_defaults_4d=camera_4d,
            reset_camera_key_fallback=reset_camera_key_fallback,
        )

    def sanitize_runtime_bindings(
        self,
        *,
        camera_defaults_4d: Mapping[str, KeyTuple] | None = None,
        reset_camera_key_fallback: int | None = None,
    ) -> None:
        fallback_camera_4d = (
            dict(camera_defaults_4d)
            if camera_defaults_4d is not None
            else self.default_camera_bindings_for_profile(self._active_profile)[1]
        )
        occupied: set[int] = set()
        for mapping in (self.keys_4d, self.system_keys):
            for keys in mapping.values():
                occupied.update(keys)

        sanitized_camera_4d: KeyBindingMap = {}
        for action, keys in self.camera_keys_4d.items():
            filtered = tuple(key for key in keys if key not in occupied)
            if not filtered:
                filtered = fallback_camera_4d.get(action, ())
                filtered = tuple(key for key in filtered if key not in occupied)
            if action == "reset" and not filtered and reset_camera_key_fallback is not None:
                filtered = (reset_camera_key_fallback,)
            sanitized_camera_4d[action] = filtered
        _replace_map(self.camera_keys_4d, sanitized_camera_4d)

    def binding_groups_for_dimension(
        self,
        dimension: int,
    ) -> dict[str, MutableMapping[str, KeyTuple]]:
        group_map: dict[int, dict[str, MutableMapping[str, KeyTuple]]] = {
            2: {
                "game": self.keys_2d,
                "explorer": self.explorer_keys_2d,
                "system": self.system_keys,
            },
            3: {
                "game": self.keys_3d,
                "explorer": self.explorer_keys_3d,
                "camera": self.camera_keys_3d,
                "system": self.system_keys,
            },
            4: {
                "game": self.keys_4d,
                "explorer": self.explorer_keys_4d,
                "camera": self.camera_keys_4d,
                "system": self.system_keys,
            },
        }
        groups = group_map.get(dimension)
        if groups is None:
            raise ValueError("dimension must be one of: 2, 3, 4")
        return groups

    def runtime_binding_groups_for_dimension(
        self,
        dimension: int,
    ) -> dict[str, Mapping[str, KeyTuple]]:
        groups = self.binding_groups_for_dimension(dimension)
        return {group: dict(bindings) for group, bindings in groups.items()}

    def binding_actions_for_dimension(self, dimension: int) -> dict[str, list[str]]:
        groups = self.binding_groups_for_dimension(dimension)
        return {group: sorted(bindings.keys()) for group, bindings in groups.items()}

    def apply_rebind_action_key(
        self,
        dimension: int,
        group: str,
        action: str,
        key: int,
        *,
        conflict_mode: str = REBIND_CONFLICT_REPLACE,
        reset_camera_key_fallback: int | None = None,
    ) -> tuple[bool, str, tuple[tuple[str, str], ...]]:
        try:
            groups = self.binding_groups_for_dimension(dimension)
        except ValueError as exc:
            return False, str(exc), ()
        binding_map = groups.get(group)
        if binding_map is None:
            return False, f"unknown binding group: {group}", ()
        if action not in binding_map:
            return False, f"unknown action: {group}.{action}", ()

        selected_mode = normalize_rebind_conflict_mode(conflict_mode)
        conflicts = _find_conflicts(groups, key, group, action)
        blocked_conflicts = _camera_blocked_conflicts(group, conflicts)
        if blocked_conflicts:
            conflict_refs = ", ".join(f"{g}.{a}" for g, a in blocked_conflicts)
            return False, f"Camera key cannot override {conflict_refs}", ()
        if conflicts and selected_mode == REBIND_CONFLICT_CANCEL:
            conflict_refs = ", ".join(f"{g}.{a}" for g, a in conflicts)
            return (
                False,
                f"Key already used by {conflict_refs}; conflict mode=cancel",
                (),
            )

        if conflicts and selected_mode == REBIND_CONFLICT_SWAP:
            _swap_conflicts(groups, binding_map, action, key, conflicts)
        else:
            _replace_conflicts(groups, key, conflicts)
        binding_map[action] = (key,)
        self.sanitize_runtime_bindings(
            reset_camera_key_fallback=reset_camera_key_fallback
        )
        return True, "", tuple(conflicts)


KEY_PROFILE_ENV = runtime_keybinding_store.KEY_PROFILE_ENV
PROFILE_FULL = runtime_keybinding_store.PROFILE_FULL
PROFILE_MACBOOK = runtime_keybinding_store.PROFILE_MACBOOK
PROFILE_TINY = runtime_keybinding_store.PROFILE_TINY
KEYBINDING_STATE = KeybindingRuntimeState(
    active_profile=active_key_profile_from_env()
)
