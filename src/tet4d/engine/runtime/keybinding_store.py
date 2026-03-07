from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

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

KEYBINDINGS_DIR = keybindings_dir_path()
KEYBINDINGS_PROFILES_DIR = keybindings_profiles_dir_path()
KEYBINDING_FILES = {
    2: KEYBINDINGS_DIR / "2d.json",
    3: KEYBINDINGS_DIR / "3d.json",
    4: KEYBINDINGS_DIR / "4d.json",
}


def load_keybinding_defaults_payload() -> dict[str, Any]:
    payload = read_json_value_or_raise(keybindings_defaults_path())
    if not isinstance(payload, dict):
        raise ValueError("keybindings defaults config must be a JSON object")
    return payload


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
    if not isinstance(payload, dict):
        return False, "Invalid keybindings JSON: root must be an object", None
    return True, f"Loaded keybindings from {path}", payload
