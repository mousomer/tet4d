from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from .project_config import (
    playbot_history_file_default_path,
    playbot_history_file_default_relative,
    resolve_state_relative_path,
)
from .runtime_config_validation import (
    read_json_payload,
    validate_audio_sfx_payload,
    validate_gameplay_tuning_payload,
    validate_playbot_policy_payload,
)


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
GAMEPLAY_TUNING_FILE = CONFIG_DIR / "gameplay" / "tuning.json"
PLAYBOT_POLICY_FILE = CONFIG_DIR / "playbot" / "policy.json"
AUDIO_SFX_FILE = CONFIG_DIR / "audio" / "sfx.json"
DEFAULT_PLAYBOT_HISTORY_FILE = playbot_history_file_default_relative()


def _dimension_bucket_key(ndim: int) -> str:
    if ndim <= 2:
        return "2d"
    if ndim == 3:
        return "3d"
    return "4d_plus"


def _normalized_name(value: str) -> str:
    return value.strip().lower()


def _bucket_lookup(mapping: dict[str, Any], ndim: int) -> Any:
    return mapping[_dimension_bucket_key(ndim)]


@lru_cache(maxsize=1)
def _gameplay_tuning() -> dict[str, Any]:
    payload = read_json_payload(GAMEPLAY_TUNING_FILE)
    return validate_gameplay_tuning_payload(payload)


@lru_cache(maxsize=1)
def _playbot_policy() -> dict[str, Any]:
    payload = read_json_payload(PLAYBOT_POLICY_FILE)
    return validate_playbot_policy_payload(payload)


@lru_cache(maxsize=1)
def _audio_sfx() -> dict[str, Any]:
    payload = read_json_payload(AUDIO_SFX_FILE)
    return validate_audio_sfx_payload(payload)


def gameplay_tuning_payload() -> dict[str, Any]:
    return deepcopy(_gameplay_tuning())


def speed_curve_for_dimension(dimension: int) -> tuple[int, int]:
    config = _gameplay_tuning()["speed_curve"]
    key = _dimension_bucket_key(dimension)
    return config[key]["base_ms"], config[key]["min_ms"]


def challenge_prefill_ratio(dimension: int) -> float:
    challenge = _gameplay_tuning()["challenge_prefill"]
    if dimension <= 2:
        return challenge["2d_fill_ratio"]
    return challenge["nd_fill_ratio"]


def assist_bot_factor(mode_name: str) -> float:
    factors = _gameplay_tuning()["assist_scoring"]["bot_factors"]
    normalized = _normalized_name(mode_name)
    return float(factors.get(normalized, factors["off"]))


def assist_grid_factor(mode_name: str) -> float:
    factors = _gameplay_tuning()["assist_scoring"]["grid_factors"]
    normalized = _normalized_name(mode_name)
    return float(factors.get(normalized, factors["off"]))


def assist_speed_formula() -> tuple[float, float, int, int]:
    speed = _gameplay_tuning()["assist_scoring"]["speed"]
    return (
        float(speed["base"]),
        float(speed["per_level"]),
        int(speed["min_level"]),
        int(speed["max_level"]),
    )


def assist_combined_bounds() -> tuple[float, float]:
    combined = _gameplay_tuning()["assist_scoring"]["combined"]
    return float(combined["min"]), float(combined["max"])


def grid_mode_cycle_names() -> tuple[str, ...]:
    return tuple(_gameplay_tuning()["grid_modes"]["cycle"])


def grid_mode_fallback_name() -> str:
    return str(_gameplay_tuning()["grid_modes"]["fallback"])


def playbot_budget_table_for_ndim(ndim: int) -> tuple[int, int, int, int]:
    bucket = _bucket_lookup(_playbot_policy()["budget_ms"], ndim)
    return bucket["fast"], bucket["balanced"], bucket["deep"], bucket["ultra"]


def playbot_board_size_scaling_policy_for_ndim(ndim: int) -> tuple[int, float, float, float]:
    scaling = _playbot_policy()["board_size_scaling"]
    return (
        int(_bucket_lookup(scaling["reference_cells"], ndim)),
        float(scaling["min_scale"]),
        float(scaling["max_scale"]),
        float(scaling["exponent"]),
    )


def playbot_clamp_policy() -> tuple[int, int, int, int]:
    clamp = _playbot_policy()["clamp"]
    return (
        clamp["floor_divisor"],
        clamp["floor_min"],
        clamp["ceil_multiplier"],
        clamp["ceil_min"],
    )


def playbot_lookahead_depth(ndim: int, profile_name: str) -> int:
    depth = _playbot_policy()["lookahead"]["depth"]
    normalized = _normalized_name(profile_name)
    if normalized == "fast":
        return depth["fast"]
    if ndim >= 4:
        return depth["all_4d_plus"]
    if normalized == "ultra":
        return depth["ultra_2d_3d"]
    if normalized == "deep":
        return depth["deep_2d_3d"]
    return depth["balanced_2d_3d"]


def playbot_lookahead_top_k(ndim: int, profile_name: str, depth_value: int) -> int:
    top_k = _playbot_policy()["lookahead"]["top_k"]
    if depth_value <= 1:
        return top_k["depth_lte_one"]
    normalized = _normalized_name(profile_name)
    if ndim <= 2:
        if normalized == "ultra":
            return top_k["ultra_2d"]
        if normalized == "deep":
            return top_k["deep_2d"]
        return top_k["balanced_2d"]
    if normalized == "ultra":
        return top_k["ultra_3d_plus"]
    if normalized == "deep":
        return top_k["deep_3d_plus"]
    return top_k["balanced_3d_plus"]


def playbot_adaptive_fallback_enabled() -> bool:
    return bool(_playbot_policy()["adaptive_fallback"]["enabled"])


def playbot_adaptive_lookahead_min_budget_ms(ndim: int) -> int:
    lookup = _playbot_policy()["adaptive_fallback"]["lookahead_min_budget_ms"]
    return int(_bucket_lookup(lookup, ndim))


def playbot_adaptive_candidate_cap_for_ndim(ndim: int) -> tuple[float, int, int]:
    cap_obj = _bucket_lookup(_playbot_policy()["adaptive_fallback"]["candidate_cap"], ndim)
    return float(cap_obj["per_ms"]), int(cap_obj["min"]), int(cap_obj["max"])


def playbot_deadline_safety_ms() -> float:
    return float(_playbot_policy()["adaptive_fallback"]["deadline_safety_ms"])


def playbot_auto_algorithm_policy_for_ndim(ndim: int) -> tuple[float, float, float, float]:
    auto_obj = _playbot_policy()["auto_algorithm"]
    key = _dimension_bucket_key(ndim)
    return (
        float(auto_obj["greedy_bias"][key]),
        float(auto_obj["density_weight"]),
        float(auto_obj["lines_cleared_weight"]),
        float(auto_obj["threshold"]),
    )


def playbot_benchmark_p95_thresholds() -> dict[str, float]:
    thresholds = _playbot_policy()["benchmark"]["p95_threshold_ms"]
    return {
        "2d": float(thresholds["2d"]),
        "3d": float(thresholds["3d"]),
        "4d": float(thresholds["4d"]),
    }


def playbot_benchmark_history_file() -> Path:
    raw = _playbot_policy()["benchmark"]["history_file"]
    default_path = playbot_history_file_default_path()
    text = str(raw).strip()
    if not text:
        return default_path
    return resolve_state_relative_path(
        text,
        default_relative=DEFAULT_PLAYBOT_HISTORY_FILE,
    )


def playbot_default_hard_drop_after_soft_drops() -> int:
    return int(_playbot_policy()["controller"]["hard_drop_after_soft_drops"])


def playbot_dry_run_defaults() -> tuple[int, int]:
    dry_run = _playbot_policy()["dry_run"]
    return int(dry_run["default_pieces"]), int(dry_run["default_seed"])


def audio_event_specs() -> dict[str, tuple[float, int, float]]:
    events = _audio_sfx()["events"]
    specs: dict[str, tuple[float, int, float]] = {}
    for event_name, spec in events.items():
        specs[event_name] = (
            float(spec["frequency_hz"]),
            int(spec["duration_ms"]),
            float(spec["amplitude"]),
        )
    return specs
