from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from tet4d.engine.ui_logic.keybindings_catalog import binding_action_contracts

from .project_config import (
    keybindings_defaults_path,
    keybindings_dir_path,
    keybindings_profiles_dir_path,
)
from .settings_schema import atomic_write_json, copy_text_file, read_json_value_or_raise

KEY_PROFILE_ENV = "TETRIS_KEY_PROFILE"
PROFILE_SMALL = "small"
PROFILE_FULL = "full"
PROFILE_MACBOOK = "macbook"
PROFILE_TINY = "tiny"
BUILTIN_PROFILES = (
    PROFILE_SMALL,
    PROFILE_FULL,
    PROFILE_MACBOOK,
    PROFILE_TINY,
)
SUPPORTED_DIMENSIONS = (2, 3, 4)
_PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
KEYBINDING_PAYLOAD_SCHEMA_VERSION = 2

KEYBINDINGS_DIR = keybindings_dir_path()
KEYBINDINGS_PROFILES_DIR = keybindings_profiles_dir_path()
KEYBINDING_FILES = {
    2: KEYBINDINGS_DIR / "2d.json",
    3: KEYBINDINGS_DIR / "3d.json",
    4: KEYBINDINGS_DIR / "4d.json",
}

_DEFAULT_GROUPS_BY_DIMENSION = {
    2: ("game", "explorer", "system"),
    3: ("game", "explorer", "camera", "system"),
    4: ("game", "explorer", "camera", "system"),
}
_NAMED_KEYCODES = {
    "space": 32,
    "escape": 27,
    "return": 13,
    "tab": 9,
    "backspace": 8,
    "delete": 127,
    "insert": 1073741897,
    "home": 1073741898,
    "end": 1073741901,
    "page up": 1073741899,
    "page down": 1073741902,
    "left": 1073741904,
    "right": 1073741903,
    "up": 1073741906,
    "down": 1073741905,
    "left shift": 1073742049,
    "right shift": 1073742053,
    "left ctrl": 1073742048,
    "right ctrl": 1073742052,
    "left alt": 1073742050,
    "right alt": 1073742054,
    "f1": 1073741882,
    "f2": 1073741883,
    "f3": 1073741884,
    "f4": 1073741885,
    "f5": 1073741886,
    "f6": 1073741887,
    "f7": 1073741888,
    "f8": 1073741889,
    "f9": 1073741890,
    "f10": 1073741891,
    "f11": 1073741892,
    "f12": 1073741893,
    "[0]": 1073741922,
    "[1]": 1073741913,
    "[2]": 1073741914,
    "[3]": 1073741915,
    "[4]": 1073741916,
    "[5]": 1073741917,
    "[6]": 1073741918,
    "[7]": 1073741919,
    "[8]": 1073741920,
    "[9]": 1073741921,
    "[/]": 1073741908,
    "[*]": 1073741909,
    "[-]": 1073741910,
    "[+]": 1073741911,
}
_KEY_NAME_ALIASES = {
    "esc": "escape",
    "enter": "return",
    "pageup": "page up",
    "pagedown": "page down",
    "lshift": "left shift",
    "rshift": "right shift",
    "lctrl": "left ctrl",
    "rctrl": "right ctrl",
    "lalt": "left alt",
    "ralt": "right alt",
}


def _is_int_list(value: object) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    )


def _is_key_token_list(value: object) -> bool:
    return isinstance(value, list) and all(
        (
            isinstance(item, int)
            and not isinstance(item, bool)
        )
        or (isinstance(item, str) and bool(item.strip()))
        for item in value
    )


def _parse_key_token(raw_key: object) -> int | None:
    if isinstance(raw_key, int) and not isinstance(raw_key, bool):
        return raw_key
    if not isinstance(raw_key, str):
        return None
    token = raw_key.strip()
    if not token:
        return None
    lowered = token.lower()
    alias = _KEY_NAME_ALIASES.get(lowered, lowered)
    if len(alias) == 1:
        return ord(alias)
    return _NAMED_KEYCODES.get(alias)


def _normalize_key_token_list(raw_keys: object, *, path: str) -> list[int]:
    if not _is_key_token_list(raw_keys):
        raise ValueError(
            f"{path} must be a list of non-empty key-name strings or integers"
        )
    normalized: list[int] = []
    for idx, raw_key in enumerate(raw_keys):
        parsed = _parse_key_token(raw_key)
        if parsed is None:
            raise ValueError(f"{path}[{idx}] contains unknown key token {raw_key!r}")
        normalized.append(parsed)
    return normalized


def _keybinding_action_contracts() -> dict[str, dict[str, object]]:
    return binding_action_contracts()


def _expected_actions_for_group(
    *,
    group_name: str,
    dimension: int | None = None,
) -> tuple[str, ...]:
    expected: list[str] = []
    for action_name, contract in _keybinding_action_contracts().items():
        if contract["group"] != group_name:
            continue
        if dimension is not None:
            dimensions = tuple(int(value) for value in contract["dimensions"])
            if dimension not in dimensions:
                continue
        expected.append(action_name)
    return tuple(sorted(expected))


def _validate_action_binding_map(
    raw_group: object,
    *,
    path: str,
    expected_group: str,
    dimension: int,
    allow_key_tokens: bool,
) -> None:
    if not isinstance(raw_group, dict):
        raise ValueError(f"{path} must be an object")
    action_contracts = _keybinding_action_contracts()
    for action_name, raw_keys in raw_group.items():
        if not isinstance(action_name, str) or not action_name.strip():
            raise ValueError(f"{path} contains non-string action id")
        contract = action_contracts.get(action_name)
        if contract is None:
            raise ValueError(f"{path}.{action_name} references unknown action id")
        if contract["group"] != expected_group:
            raise ValueError(
                f"{path}.{action_name} must belong to group {expected_group}"
            )
        dimensions = tuple(int(value) for value in contract["dimensions"])
        if dimension not in dimensions:
            raise ValueError(
                f"{path}.{action_name} is not valid for dimension {dimension}"
            )
        if allow_key_tokens:
            raw_group[action_name] = _normalize_key_token_list(
                raw_keys,
                path=f"{path}.{action_name}",
            )
            continue
        if not _is_int_list(raw_keys):
            raise ValueError(f"{path}.{action_name} must be a list of integers")


def _validate_dimension_group_map(
    raw_group: object,
    *,
    path: str,
    group_name: str,
) -> None:
    if not isinstance(raw_group, dict):
        raise ValueError(f"{path} must be an object")
    expected_dim_keys = {
        f"d{dimension}"
        for dimension in SUPPORTED_DIMENSIONS
        if _expected_actions_for_group(group_name=group_name, dimension=dimension)
    }
    actual_dim_keys = set(raw_group.keys())
    missing_dim_keys = sorted(expected_dim_keys - actual_dim_keys)
    if missing_dim_keys:
        raise ValueError(
            f"{path} is missing required dimension sections: {', '.join(missing_dim_keys)}"
        )
    unexpected_dim_keys = sorted(actual_dim_keys - expected_dim_keys)
    if unexpected_dim_keys:
        raise ValueError(
            f"{path} contains unexpected dimension sections: {', '.join(unexpected_dim_keys)}"
        )
    for dim_key, raw_dim_group in raw_group.items():
        if not isinstance(dim_key, str) or not dim_key.startswith("d"):
            raise ValueError(f"{path} must use d2/d3/d4 dimension keys")
        try:
            dimension = int(dim_key[1:])
        except ValueError as exc:
            raise ValueError(f"{path} must use d2/d3/d4 dimension keys") from exc
        if dimension not in SUPPORTED_DIMENSIONS:
            raise ValueError(f"{path}.{dim_key} uses unsupported dimension")
        _validate_action_binding_map(
            raw_dim_group,
            path=f"{path}.{dim_key}",
            expected_group=group_name,
            dimension=dimension,
            allow_key_tokens=True,
        )
        expected_actions = set(
            _expected_actions_for_group(group_name=group_name, dimension=dimension)
        )
        actual_actions = set(raw_dim_group.keys()) if isinstance(raw_dim_group, dict) else set()
        missing_actions = sorted(expected_actions - actual_actions)
        if missing_actions:
            raise ValueError(
                f"{path}.{dim_key} is missing required actions: {', '.join(missing_actions)}"
            )


def _validate_default_profile(profile_name: object, raw_profile: object) -> None:
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise ValueError("keybindings defaults config profiles must use non-empty string keys")
    path = f"keybindings.defaults.profiles.{profile_name}"
    if not isinstance(raw_profile, dict):
        raise ValueError(f"{path} must be an object")
    unexpected_groups = sorted(
        set(raw_profile.keys()) - {"system", "game", "explorer", "camera"}
    )
    if unexpected_groups:
        raise ValueError(
            f"{path} contains unknown binding groups: {', '.join(unexpected_groups)}"
        )
    raw_system = raw_profile.get("system")
    if raw_system is None:
        raise ValueError(f"{path}.system must be present")
    _validate_action_binding_map(
        raw_system,
        path=f"{path}.system",
        expected_group="system",
        dimension=2,
        allow_key_tokens=True,
    )
    expected_system_actions = set(_expected_actions_for_group(group_name="system"))
    actual_system_actions = (
        set(raw_system.keys()) if isinstance(raw_system, dict) else set()
    )
    missing_system_actions = sorted(expected_system_actions - actual_system_actions)
    if missing_system_actions:
        raise ValueError(
            f"{path}.system is missing required actions: {', '.join(missing_system_actions)}"
        )
    for group_name in ("game", "explorer", "camera"):
        raw_group = raw_profile.get(group_name)
        if raw_group is None:
            raise ValueError(f"{path}.{group_name} must be present")
        _validate_dimension_group_map(
            raw_group,
            path=f"{path}.{group_name}",
            group_name=group_name,
        )


def validate_keybinding_defaults_payload(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("keybindings defaults config must be a JSON object")
    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("keybindings defaults config must define integer version >= 1")
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("keybindings defaults config must define non-empty profiles")
    disabled_keys_2d = payload.get("disabled_keys_2d", [])
    try:
        payload["disabled_keys_2d"] = _normalize_key_token_list(
            disabled_keys_2d,
            path="keybindings defaults config disabled_keys_2d",
        )
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    for profile_name, raw_profile in profiles.items():
        _validate_default_profile(profile_name, raw_profile)
    return payload


def _validate_keybinding_payload_header(
    payload: dict[str, Any],
    *,
    expected_dimension: int | None,
) -> tuple[int, dict[str, object]]:
    schema_version = payload.get("schema_version")
    if schema_version is not None:
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version < 1
        ):
            raise ValueError("keybinding payload schema_version must be an integer >= 1")
        if schema_version > KEYBINDING_PAYLOAD_SCHEMA_VERSION:
            raise ValueError(
                "keybinding payload schema_version is newer than this runtime supports"
            )
    dimension = payload.get("dimension")
    if (
        not isinstance(dimension, int)
        or isinstance(dimension, bool)
        or dimension not in SUPPORTED_DIMENSIONS
    ):
        raise ValueError("keybinding payload must define dimension 2, 3, or 4")
    if expected_dimension is not None and dimension != expected_dimension:
        raise ValueError(
            f"keybinding payload dimension {dimension} does not match requested dimension {expected_dimension}"
        )
    profile = payload.get("profile")
    if not isinstance(profile, str) or not profile.strip():
        raise ValueError("keybinding payload must define non-empty profile")
    normalize_profile_name(profile)
    bindings = payload.get("bindings")
    if not isinstance(bindings, dict):
        raise ValueError("keybinding payload must define a bindings object")
    return dimension, bindings


def _validate_legacy_2d_binding_payload(
    bindings: dict[str, object],
    *,
    allow_partial_bindings: bool,
) -> None:
    _validate_action_binding_map(
        bindings,
        path="keybinding.payload.bindings",
        expected_group="game",
        dimension=2,
        allow_key_tokens=True,
    )
    if allow_partial_bindings:
        return
    expected_actions = set(_expected_actions_for_group(group_name="game", dimension=2))
    actual_actions = set(bindings.keys())
    missing_actions = sorted(expected_actions - actual_actions)
    if missing_actions:
        raise ValueError(
            "keybinding payload.bindings is missing required actions: "
            + ", ".join(missing_actions)
        )


def _validate_grouped_binding_payload(
    bindings: dict[str, object],
    *,
    dimension: int,
) -> None:
    allowed_groups = set(_DEFAULT_GROUPS_BY_DIMENSION[dimension])
    for group_name, raw_group in bindings.items():
        if group_name not in allowed_groups:
            raise ValueError(
                f"keybinding payload group {group_name!r} is not valid for dimension {dimension}"
            )
        _validate_action_binding_map(
            raw_group,
            path=f"keybinding.payload.bindings.{group_name}",
            expected_group=group_name,
            dimension=dimension,
            allow_key_tokens=True,
        )


def _validate_complete_binding_payload(
    bindings: dict[str, object],
    *,
    dimension: int,
) -> None:
    expected_groups = set(_DEFAULT_GROUPS_BY_DIMENSION[dimension])
    actual_groups = set(bindings.keys())
    missing_groups = sorted(expected_groups - actual_groups)
    if missing_groups:
        raise ValueError(
            "keybinding payload.bindings is missing required groups: "
            + ", ".join(missing_groups)
        )
    for group_name in expected_groups:
        raw_group = bindings.get(group_name, {})
        expected_actions = set(
            _expected_actions_for_group(group_name=group_name, dimension=dimension)
        )
        if group_name == "system":
            expected_actions = set(_expected_actions_for_group(group_name="system"))
        actual_actions = set(raw_group.keys()) if isinstance(raw_group, dict) else set()
        missing_actions = sorted(expected_actions - actual_actions)
        if missing_actions:
            raise ValueError(
                f"keybinding payload.bindings.{group_name} is missing required actions: "
                + ", ".join(missing_actions)
            )


def validate_keybinding_file_payload(
    payload: object,
    *,
    expected_dimension: int | None = None,
    allow_partial_bindings: bool = True,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("keybinding payload must be a JSON object")
    dimension, bindings = _validate_keybinding_payload_header(
        payload,
        expected_dimension=expected_dimension,
    )
    legacy_2d_flat = dimension == 2 and all(
        isinstance(action_name, str)
        and action_name in _keybinding_action_contracts()
        for action_name in bindings.keys()
    )
    if legacy_2d_flat:
        _validate_legacy_2d_binding_payload(
            bindings,
            allow_partial_bindings=allow_partial_bindings,
        )
        return payload
    _validate_grouped_binding_payload(bindings, dimension=dimension)
    if not allow_partial_bindings:
        _validate_complete_binding_payload(bindings, dimension=dimension)
    return payload


def load_keybinding_defaults_payload() -> dict[str, Any]:
    payload = read_json_value_or_raise(keybindings_defaults_path())
    return validate_keybinding_defaults_payload(payload)


def normalize_builtin_profile(raw: str | None) -> str:
    if raw is None:
        return PROFILE_SMALL
    value = raw.strip().lower()
    if value in BUILTIN_PROFILES:
        return value
    return PROFILE_SMALL


def normalize_profile_name(raw: str) -> str:
    value = raw.strip().lower()
    if not _PROFILE_NAME_RE.match(value):
        raise ValueError("invalid profile name; use letters, numbers, '_' or '-'")
    return value


def active_key_profile_from_env() -> str:
    return normalize_builtin_profile(os.environ.get(KEY_PROFILE_ENV))


def selected_profile_name(profile: str | None, active_profile: str) -> str:
    if not profile:
        return active_profile
    return normalize_profile_name(profile)


def safe_resolve_keybinding_path(path: Path) -> Path:
    root = KEYBINDINGS_DIR.resolve()
    resolved = path.expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path must be within keybindings directory: {root}")
    return resolved


def default_keybinding_file_path(dimension: int) -> Path:
    path = KEYBINDING_FILES.get(dimension)
    if path is None:
        raise ValueError("dimension must be one of: 2, 3, 4")
    return path


def profile_keybinding_file_path(dimension: int, profile: str) -> Path:
    normalized = normalize_profile_name(profile)
    if normalized == PROFILE_SMALL:
        return safe_resolve_keybinding_path(default_keybinding_file_path(dimension))
    filename = default_keybinding_file_path(dimension).name
    return safe_resolve_keybinding_path(KEYBINDINGS_PROFILES_DIR / normalized / filename)


def keybinding_file_path_for_profile(
    dimension: int,
    *,
    profile: str | None = None,
    active_profile: str = PROFILE_SMALL,
) -> Path:
    return profile_keybinding_file_path(
        dimension,
        selected_profile_name(profile, active_profile),
    )


def resolve_keybinding_io_path(
    dimension: int,
    *,
    file_path: str | None,
    profile: str | None,
    active_profile: str,
) -> tuple[Path, str]:
    selected_profile = selected_profile_name(profile, active_profile)
    if file_path is not None:
        return safe_resolve_keybinding_path(Path(file_path)), selected_profile
    return keybinding_file_path_for_profile(
        dimension,
        profile=selected_profile,
        active_profile=active_profile,
    ), selected_profile


def list_key_profiles() -> list[str]:
    profiles = set(BUILTIN_PROFILES)
    if KEYBINDINGS_PROFILES_DIR.exists():
        for child in KEYBINDINGS_PROFILES_DIR.iterdir():
            if not child.is_dir():
                continue
            try:
                profiles.add(normalize_profile_name(child.name))
            except ValueError:
                continue
    return sorted(profiles)


def next_auto_profile_name(prefix: str = "custom") -> str:
    safe_prefix = normalize_profile_name(prefix)
    existing = set(list_key_profiles())
    idx = 1
    while True:
        candidate = f"{safe_prefix}_{idx}"
        if candidate not in existing:
            return candidate
        idx += 1


def delete_key_profile(profile: str) -> tuple[bool, str]:
    normalized = normalize_profile_name(profile)
    if normalized in BUILTIN_PROFILES:
        return False, "cannot delete built-in profile"
    dir_path = safe_resolve_keybinding_path(KEYBINDINGS_PROFILES_DIR / normalized)
    if not dir_path.exists():
        return False, f"profile not found: {normalized}"
    try:
        for child in dir_path.glob("*.json"):
            child.unlink()
        dir_path.rmdir()
    except OSError as exc:
        return False, f"failed deleting profile: {exc}"
    return True, f"Deleted profile: {normalized}"


def rename_key_profile(profile: str, new_profile: str) -> tuple[bool, str]:
    source = normalize_profile_name(profile)
    target = normalize_profile_name(new_profile)
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

    src_dir = safe_resolve_keybinding_path(KEYBINDINGS_PROFILES_DIR / source)
    dst_dir = safe_resolve_keybinding_path(KEYBINDINGS_PROFILES_DIR / target)
    try:
        src_dir.rename(dst_dir)
    except OSError as exc:
        return False, f"failed renaming profile: {exc}"
    return True, f"Renamed profile {source} -> {target}"


def clone_keybinding_dimension(
    source_profile: str,
    target_profile: str,
    dimension: int,
    *,
    materialize_source: Callable[[], None] | None = None,
) -> None:
    src_path = profile_keybinding_file_path(dimension, source_profile)
    if not src_path.exists() and materialize_source is not None:
        materialize_source()
        src_path = profile_keybinding_file_path(dimension, source_profile)
    dst_path = profile_keybinding_file_path(dimension, target_profile)
    copy_text_file(src_path, dst_path)


def save_keybindings_payload(
    dimension: int,
    payload: dict[str, Any],
    *,
    file_path: str | None = None,
    profile: str | None = None,
    active_profile: str,
) -> tuple[bool, str]:
    try:
        path, _selected_profile = resolve_keybinding_io_path(
            dimension,
            file_path=file_path,
            profile=profile,
            active_profile=active_profile,
        )
    except ValueError as exc:
        return False, str(exc)

    try:
        atomic_write_json(path, payload)
    except OSError as exc:
        return False, f"Failed saving keybindings: {exc}"
    return True, f"Saved keybindings to {path}"


def load_keybindings_payload(
    dimension: int,
    *,
    file_path: str | None = None,
    profile: str | None = None,
    active_profile: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    try:
        path, _selected_profile = resolve_keybinding_io_path(
            dimension,
            file_path=file_path,
            profile=profile,
            active_profile=active_profile,
        )
    except ValueError as exc:
        return False, str(exc), None

    try:
        payload = read_json_value_or_raise(path)
    except OSError as exc:
        return False, f"Failed loading keybindings: {exc}", None
    except json.JSONDecodeError as exc:
        return False, f"Invalid keybindings JSON: {exc}", None
    try:
        validated = validate_keybinding_file_payload(
            payload, expected_dimension=dimension
        )
    except ValueError as exc:
        return False, f"Invalid keybindings JSON: {exc}", None
    if not isinstance(validated, dict):
        return False, "Invalid keybindings JSON: root must be an object", None
    return True, f"Loaded keybindings from {path}", validated
