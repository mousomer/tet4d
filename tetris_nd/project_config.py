from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_CONFIG_DIR = PROJECT_ROOT / "config" / "project"
IO_PATHS_FILE = PROJECT_CONFIG_DIR / "io_paths.json"
CONSTANTS_FILE = PROJECT_CONFIG_DIR / "constants.json"

_DEFAULT_IO_PATHS = {
    "version": 1,
    "paths": {
        "state_dir": "state",
        "menu_settings_file": "state/menu_settings.json",
        "keybindings_dir": "keybindings",
        "keybindings_profiles_dir": "keybindings/profiles",
        "playbot_history_file_default": "state/bench/playbot_latency_history.jsonl",
        "score_events_file_default": "state/analytics/score_events.jsonl",
        "score_summary_file_default": "state/analytics/score_summary.json",
        "topology_profile_export_file_default": "state/topology/selected_profile.json",
    },
}

_DEFAULT_CONSTANTS = {
    "version": 1,
    "cache_limits": {
        "gradient_surface_max": 16,
        "text_surface_max": 3072,
        "projection_lattice_max": 96,
    },
    "animation": {
        "piece_rotation_duration_ms": 150.0,
        "clear_effect_duration_ms_2d": 320.0,
        "clear_effect_duration_ms_3d": 360.0,
        "clear_effect_duration_ms_4d": 380.0,
    },
    "rendering": {
        "2d": {
            "cell_size": 30,
            "margin": 20,
            "side_panel": 200,
        },
        "3d": {
            "margin": 20,
            "side_panel": 360,
        },
        "4d": {
            "margin": 16,
            "side_panel": 360,
            "layer_gap": 12,
        },
    },
}


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _merge_objects(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in incoming.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _merge_objects(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


@lru_cache(maxsize=1)
def io_paths_payload() -> dict[str, Any]:
    loaded = _read_json_object(IO_PATHS_FILE)
    return _merge_objects(_DEFAULT_IO_PATHS, loaded)


@lru_cache(maxsize=1)
def constants_payload() -> dict[str, Any]:
    loaded = _read_json_object(CONSTANTS_FILE)
    return _merge_objects(_DEFAULT_CONSTANTS, loaded)


def reset_project_config_cache() -> None:
    io_paths_payload.cache_clear()
    constants_payload.cache_clear()


def _normalize_relative_path(
    raw: object,
    *,
    default_relative: str,
    required_prefix: str | None = None,
) -> str:
    if not isinstance(raw, str):
        return default_relative
    text = raw.strip().replace("\\", "/")
    if not text:
        return default_relative

    candidate = Path(text)
    if candidate.is_absolute():
        return default_relative

    parts = [part for part in candidate.parts if part not in ("", ".")]
    if not parts:
        return default_relative
    if any(part == ".." for part in parts):
        return default_relative
    if any(":" in part for part in parts):
        return default_relative

    clean = "/".join(parts)
    if required_prefix is not None:
        prefix = required_prefix.rstrip("/")
        if clean != prefix and not clean.startswith(prefix + "/"):
            return default_relative
    return clean


def _resolve_repo_relative(relative_path: str, default_relative: str) -> Path:
    default_path = (PROJECT_ROOT / default_relative).resolve()
    resolved = (PROJECT_ROOT / relative_path).resolve()
    root = PROJECT_ROOT.resolve()
    if resolved == root or root in resolved.parents:
        return resolved
    return default_path


def state_dir_relative() -> str:
    paths = io_paths_payload().get("paths", {})
    if not isinstance(paths, dict):
        return "state"
    return _normalize_relative_path(
        paths.get("state_dir"),
        default_relative="state",
    )


def state_dir_path() -> Path:
    rel = state_dir_relative()
    return _resolve_repo_relative(rel, "state")


def sanitize_state_relative_path(raw: object, *, default_relative: str) -> str:
    return _normalize_relative_path(
        raw,
        default_relative=default_relative,
        required_prefix=state_dir_relative(),
    )


def resolve_state_relative_path(raw: object, *, default_relative: str) -> Path:
    rel = sanitize_state_relative_path(raw, default_relative=default_relative)
    return _resolve_repo_relative(rel, default_relative)


def _path_value(name: str, *, default_relative: str, required_prefix: str | None = None) -> str:
    paths = io_paths_payload().get("paths", {})
    raw = paths.get(name) if isinstance(paths, dict) else None
    return _normalize_relative_path(
        raw,
        default_relative=default_relative,
        required_prefix=required_prefix,
    )


def menu_settings_file_relative() -> str:
    default = "state/menu_settings.json"
    return _path_value(
        "menu_settings_file",
        default_relative=default,
        required_prefix=state_dir_relative(),
    )


def menu_settings_file_path() -> Path:
    rel = menu_settings_file_relative()
    return _resolve_repo_relative(rel, "state/menu_settings.json")


def keybindings_dir_relative() -> str:
    return _path_value(
        "keybindings_dir",
        default_relative="keybindings",
        required_prefix="keybindings",
    )


def keybindings_dir_path() -> Path:
    rel = keybindings_dir_relative()
    return _resolve_repo_relative(rel, "keybindings")


def keybindings_profiles_dir_relative() -> str:
    keybindings_root = keybindings_dir_relative()
    default_rel = f"{keybindings_root}/profiles"
    return _path_value(
        "keybindings_profiles_dir",
        default_relative=default_rel,
        required_prefix=keybindings_root,
    )


def keybindings_profiles_dir_path() -> Path:
    rel = keybindings_profiles_dir_relative()
    default_rel = f"{keybindings_dir_relative()}/profiles"
    return _resolve_repo_relative(rel, default_rel)


def playbot_history_file_default_relative() -> str:
    return _path_value(
        "playbot_history_file_default",
        default_relative="state/bench/playbot_latency_history.jsonl",
        required_prefix=state_dir_relative(),
    )


def playbot_history_file_default_path() -> Path:
    rel = playbot_history_file_default_relative()
    return _resolve_repo_relative(rel, "state/bench/playbot_latency_history.jsonl")


def score_events_file_default_relative() -> str:
    return _path_value(
        "score_events_file_default",
        default_relative="state/analytics/score_events.jsonl",
        required_prefix=state_dir_relative(),
    )


def score_events_file_default_path() -> Path:
    rel = score_events_file_default_relative()
    return _resolve_repo_relative(rel, "state/analytics/score_events.jsonl")


def score_summary_file_default_relative() -> str:
    return _path_value(
        "score_summary_file_default",
        default_relative="state/analytics/score_summary.json",
        required_prefix=state_dir_relative(),
    )


def score_summary_file_default_path() -> Path:
    rel = score_summary_file_default_relative()
    return _resolve_repo_relative(rel, "state/analytics/score_summary.json")


def topology_profile_export_file_default_relative() -> str:
    return _path_value(
        "topology_profile_export_file_default",
        default_relative="state/topology/selected_profile.json",
        required_prefix=state_dir_relative(),
    )


def topology_profile_export_file_default_path() -> Path:
    rel = topology_profile_export_file_default_relative()
    return _resolve_repo_relative(rel, "state/topology/selected_profile.json")


def project_constant_int(
    path: tuple[str, ...],
    default: int,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    value: object = constants_payload()
    for key in path:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    if min_value is not None and value < min_value:
        return default
    if max_value is not None and value > max_value:
        return default
    return value


def project_constant_float(
    path: tuple[str, ...],
    default: float,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    value: object = constants_payload()
    for key in path:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    fval = float(value)
    if min_value is not None and fval < min_value:
        return default
    if max_value is not None and fval > max_value:
        return default
    return fval
