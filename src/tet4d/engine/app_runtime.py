from __future__ import annotations

from dataclasses import dataclass

import pygame

from .audio import AudioSettings, initialize_audio, set_audio_settings
from .display import DisplaySettings, apply_display_mode, normalize_display_settings
from .keybindings import initialize_keybinding_files
from .menu_settings_state import (
    get_analytics_settings,
    get_audio_settings,
    get_display_settings,
    save_display_settings,
)
from .runtime.score_analyzer import set_score_analyzer_logging_enabled


@dataclass(frozen=True)
class RuntimeSettings:
    audio_settings: AudioSettings
    display_settings: DisplaySettings


def load_audio_settings_from_store() -> AudioSettings:
    payload = get_audio_settings()
    return AudioSettings(
        master_volume=float(payload["master_volume"]),
        sfx_volume=float(payload["sfx_volume"]),
        mute=bool(payload["mute"]),
    )


def load_display_settings_from_store() -> DisplaySettings:
    payload = get_display_settings()
    return normalize_display_settings(
        DisplaySettings(
            fullscreen=bool(payload["fullscreen"]),
            windowed_size=tuple(payload["windowed_size"]),
        )
    )


def initialize_runtime(*, sync_audio_state: bool = True) -> RuntimeSettings:
    pygame.init()
    initialize_keybinding_files()
    audio_settings = load_audio_settings_from_store()
    initialize_audio(audio_settings)
    if sync_audio_state:
        set_audio_settings(
            master_volume=audio_settings.master_volume,
            sfx_volume=audio_settings.sfx_volume,
            mute=audio_settings.mute,
        )
    display_settings = load_display_settings_from_store()
    analytics = get_analytics_settings()
    set_score_analyzer_logging_enabled(
        bool(analytics.get("score_logging_enabled", False))
    )
    return RuntimeSettings(
        audio_settings=audio_settings, display_settings=display_settings
    )


def open_display(
    display_settings: DisplaySettings,
    *,
    caption: str | None = None,
    preferred_windowed_size: tuple[int, int] | None = None,
) -> pygame.Surface:
    if caption:
        pygame.display.set_caption(caption)
    target_size = (
        display_settings.windowed_size
        if preferred_windowed_size is None
        else preferred_windowed_size
    )
    return apply_display_mode(display_settings, preferred_windowed_size=target_size)


def capture_windowed_display_settings(
    display_settings: DisplaySettings,
    *,
    min_width: int = 640,
    min_height: int = 480,
) -> DisplaySettings:
    if display_settings.fullscreen:
        return display_settings
    surface = pygame.display.get_surface()
    if surface is None:
        return display_settings
    width, height = surface.get_size()
    if width < min_width or height < min_height:
        return display_settings
    updated = DisplaySettings(fullscreen=False, windowed_size=(width, height))
    save_display_settings(windowed_size=updated.windowed_size)
    return updated
