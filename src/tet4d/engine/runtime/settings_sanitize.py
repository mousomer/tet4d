from __future__ import annotations

from typing import Any

from .settings_schema import (
    MODE_KEY_SET,
    PROFILE_NAME_RE,
    RuntimeSettingDefaults,
    clamp_game_seed,
    clamp_overlay_transparency,
)


def ensure_default_settings_payload(
    payload: dict[str, Any],
    *,
    defaults: RuntimeSettingDefaults,
) -> dict[str, Any]:
    payload.setdefault("display", {})
    display = payload["display"]
    if isinstance(display, dict):
        windowed_size = display.get("windowed_size")
        if (
            not isinstance(windowed_size, list)
            or len(windowed_size) != 2
            or any(isinstance(v, bool) or not isinstance(v, int) for v in windowed_size)
        ):
            display["windowed_size"] = [
                defaults.windowed_size[0],
                defaults.windowed_size[1],
            ]
        display["overlay_transparency"] = clamp_overlay_transparency(
            display.get("overlay_transparency"),
            default=defaults.overlay_transparency,
        )
    payload.setdefault("analytics", {"score_logging_enabled": False})
    analytics = payload.get("analytics")
    if not isinstance(analytics, dict):
        payload["analytics"] = {"score_logging_enabled": False}
    elif not isinstance(analytics.get("score_logging_enabled"), bool):
        analytics["score_logging_enabled"] = False
    return payload


def merge_loaded_payload(payload: dict[str, Any], loaded: dict[str, Any]) -> None:
    for key in ("version", "active_profile", "last_mode"):
        if key in loaded:
            payload[key] = loaded[key]

    for section in ("display", "audio", "analytics"):
        target = payload.get(section)
        incoming = loaded.get(section)
        if isinstance(target, dict) and isinstance(incoming, dict):
            target.update(incoming)

    loaded_settings = loaded.get("settings")
    if not isinstance(loaded_settings, dict):
        return
    merged = payload.get("settings")
    if not isinstance(merged, dict):
        return
    for mode_key, mode_settings in loaded_settings.items():
        if mode_key in merged and isinstance(mode_settings, dict):
            merged[mode_key].update(mode_settings)


def _sanitize_version_profile_mode(
    payload: dict[str, Any],
    default_payload: dict[str, Any],
) -> None:
    version = payload.get("version")
    if isinstance(version, int) and version > 0:
        payload["version"] = version
    else:
        payload["version"] = default_payload["version"]

    raw_profile = payload.get("active_profile")
    if not isinstance(raw_profile, str) or not raw_profile.strip():
        payload["active_profile"] = default_payload["active_profile"]
    else:
        normalized_profile = raw_profile.strip().lower()
        if PROFILE_NAME_RE.match(normalized_profile):
            payload["active_profile"] = normalized_profile
        else:
            payload["active_profile"] = default_payload["active_profile"]

    raw_mode = payload.get("last_mode")
    payload["last_mode"] = (
        raw_mode if raw_mode in MODE_KEY_SET else default_payload["last_mode"]
    )


def _sanitize_display_section(
    payload: dict[str, Any],
    default_payload: dict[str, Any],
    *,
    defaults: RuntimeSettingDefaults,
) -> None:
    display = payload.setdefault("display", {})
    if not isinstance(display, dict):
        payload["display"] = {}
        display = payload["display"]

    default_display = default_payload.get("display", {})
    default_fullscreen = False
    default_windowed_size = [defaults.windowed_size[0], defaults.windowed_size[1]]
    default_overlay_transparency = defaults.overlay_transparency
    if isinstance(default_display, dict):
        default_fullscreen = bool(default_display.get("fullscreen", False))
        raw_default_size = default_display.get("windowed_size")
        if (
            isinstance(raw_default_size, list)
            and len(raw_default_size) == 2
            and all(
                isinstance(v, int) and not isinstance(v, bool) for v in raw_default_size
            )
        ):
            default_windowed_size = raw_default_size
        default_overlay_transparency = clamp_overlay_transparency(
            default_display.get("overlay_transparency"),
            default=defaults.overlay_transparency,
        )

    fullscreen = bool(display.get("fullscreen", default_fullscreen))
    raw_size = display.get("windowed_size", default_windowed_size)
    if (
        not isinstance(raw_size, list)
        or len(raw_size) != 2
        or any(isinstance(v, bool) or not isinstance(v, int) for v in raw_size)
    ):
        raw_size = default_windowed_size
    width = max(640, raw_size[0])
    height = max(480, raw_size[1])
    display["fullscreen"] = fullscreen
    display["windowed_size"] = [width, height]
    display["overlay_transparency"] = clamp_overlay_transparency(
        display.get("overlay_transparency", default_overlay_transparency),
        default=default_overlay_transparency,
    )


def _sanitize_audio_section(
    payload: dict[str, Any],
    default_payload: dict[str, Any],
) -> None:
    audio = payload.setdefault("audio", {})
    if not isinstance(audio, dict):
        payload["audio"] = {}
        audio = payload["audio"]

    default_audio = default_payload.get("audio", {})
    default_master = 0.8
    default_sfx = 0.7
    default_mute = False
    if isinstance(default_audio, dict):
        raw_master = default_audio.get("master_volume")
        raw_sfx = default_audio.get("sfx_volume")
        if isinstance(raw_master, (int, float)) and not isinstance(raw_master, bool):
            default_master = float(raw_master)
        if isinstance(raw_sfx, (int, float)) and not isinstance(raw_sfx, bool):
            default_sfx = float(raw_sfx)
        default_mute = bool(default_audio.get("mute", False))

    master = audio.get("master_volume", default_master)
    sfx = audio.get("sfx_volume", default_sfx)
    mute = bool(audio.get("mute", default_mute))
    if not isinstance(master, (int, float)):
        master = default_master
    if not isinstance(sfx, (int, float)):
        sfx = default_sfx
    audio["master_volume"] = max(0.0, min(1.0, float(master)))
    audio["sfx_volume"] = max(0.0, min(1.0, float(sfx)))
    audio["mute"] = mute


def _sanitize_analytics_section(
    payload: dict[str, Any],
    default_payload: dict[str, Any],
) -> None:
    analytics = payload.setdefault("analytics", {})
    if not isinstance(analytics, dict):
        payload["analytics"] = {}
        analytics = payload["analytics"]
    default_analytics = default_payload.get("analytics", {})
    default_logging = (
        bool(default_analytics.get("score_logging_enabled", False))
        if isinstance(default_analytics, dict)
        else False
    )
    analytics["score_logging_enabled"] = bool(
        analytics.get("score_logging_enabled", default_logging)
    )


def _sanitize_mode_settings(
    payload: dict[str, Any],
    default_payload: dict[str, Any],
    *,
    defaults: RuntimeSettingDefaults,
) -> None:
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        settings = {}
    sanitized_settings: dict[str, dict[str, Any]] = {}
    default_settings = default_payload["settings"]
    for mode_key, mode_defaults in default_settings.items():
        mode_payload = settings.get(mode_key, {})
        if not isinstance(mode_payload, dict):
            mode_payload = {}
        merged_mode: dict[str, Any] = {}
        for attr_name, default_value in mode_defaults.items():
            value = mode_payload.get(attr_name, default_value)
            if isinstance(default_value, int):
                if isinstance(value, bool) or not isinstance(value, int):
                    value = default_value
                elif attr_name == "game_seed":
                    value = clamp_game_seed(value, default=defaults.game_seed)
            elif not isinstance(value, type(default_value)):
                value = default_value
            merged_mode[attr_name] = value
        sanitized_settings[mode_key] = merged_mode
    payload["settings"] = sanitized_settings


def sanitize_payload(
    payload: dict[str, Any],
    *,
    default_payload: dict[str, Any],
    defaults: RuntimeSettingDefaults,
) -> None:
    _sanitize_version_profile_mode(payload, default_payload)
    _sanitize_display_section(payload, default_payload, defaults=defaults)
    _sanitize_audio_section(payload, default_payload)
    _sanitize_analytics_section(payload, default_payload)
    _sanitize_mode_settings(payload, default_payload, defaults=defaults)


def display_settings_from_payload(
    payload: dict[str, Any],
    *,
    default_payload: dict[str, Any],
    defaults: RuntimeSettingDefaults,
) -> dict[str, Any]:
    display = payload.get("display", {})
    if not isinstance(display, dict):
        display = {}
    baseline = default_payload.get("display", {})
    if not isinstance(baseline, dict):
        baseline = {}

    default_fullscreen = bool(baseline.get("fullscreen", False))
    default_windowed_size = baseline.get(
        "windowed_size",
        [defaults.windowed_size[0], defaults.windowed_size[1]],
    )
    if (
        not isinstance(default_windowed_size, list)
        or len(default_windowed_size) != 2
        or any(
            isinstance(v, bool) or not isinstance(v, int) for v in default_windowed_size
        )
    ):
        default_windowed_size = [defaults.windowed_size[0], defaults.windowed_size[1]]

    return {
        "fullscreen": bool(display.get("fullscreen", default_fullscreen)),
        "windowed_size": list(display.get("windowed_size", default_windowed_size)),
        "overlay_transparency": clamp_overlay_transparency(
            display.get("overlay_transparency"),
            default=clamp_overlay_transparency(
                baseline.get("overlay_transparency"),
                default=defaults.overlay_transparency,
            ),
        ),
    }


def audio_settings_from_payload(
    payload: dict[str, Any],
    *,
    default_payload: dict[str, Any],
) -> dict[str, Any]:
    audio = payload.get("audio", {})
    if not isinstance(audio, dict):
        audio = {}
    defaults = default_payload.get("audio", {})
    if not isinstance(defaults, dict):
        defaults = {}
    default_master = float(defaults.get("master_volume", 0.8))
    default_sfx = float(defaults.get("sfx_volume", 0.7))
    default_mute = bool(defaults.get("mute", False))
    return {
        "master_volume": float(audio.get("master_volume", default_master)),
        "sfx_volume": float(audio.get("sfx_volume", default_sfx)),
        "mute": bool(audio.get("mute", default_mute)),
    }


def analytics_settings_from_payload(
    payload: dict[str, Any],
    *,
    default_payload: dict[str, Any],
) -> dict[str, Any]:
    analytics = payload.get("analytics", {})
    if not isinstance(analytics, dict):
        analytics = {}
    defaults = default_payload.get("analytics", {})
    if not isinstance(defaults, dict):
        defaults = {}
    default_logging = bool(defaults.get("score_logging_enabled", False))
    return {
        "score_logging_enabled": bool(
            analytics.get("score_logging_enabled", default_logging)
        )
    }
