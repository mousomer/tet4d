from __future__ import annotations

from typing import Any

from .menu_settings_state import (
    get_audio_settings,
    get_analytics_settings,
    get_display_settings,
    load_app_settings_payload,
    save_app_settings_payload,
    save_analytics_settings,
    save_audio_settings,
    save_display_settings,
)


def load_menu_payload() -> dict[str, Any]:
    return load_app_settings_payload()


def save_menu_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    return save_app_settings_payload(payload)


def load_audio_payload() -> dict[str, Any]:
    return get_audio_settings()


def load_display_payload() -> dict[str, Any]:
    return get_display_settings()


def load_analytics_payload() -> dict[str, Any]:
    return get_analytics_settings()


def persist_audio_payload(
    *,
    master_volume: float | None = None,
    sfx_volume: float | None = None,
    mute: bool | None = None,
) -> tuple[bool, str]:
    return save_audio_settings(
        master_volume=master_volume,
        sfx_volume=sfx_volume,
        mute=mute,
    )


def persist_display_payload(
    *,
    fullscreen: bool | None = None,
    windowed_size: tuple[int, int] | None = None,
    overlay_transparency: float | None = None,
) -> tuple[bool, str]:
    return save_display_settings(
        fullscreen=fullscreen,
        windowed_size=windowed_size,
        overlay_transparency=overlay_transparency,
    )


def persist_analytics_payload(
    *,
    score_logging_enabled: bool | None = None,
) -> tuple[bool, str]:
    return save_analytics_settings(score_logging_enabled=score_logging_enabled)
