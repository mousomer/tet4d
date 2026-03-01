from __future__ import annotations

from dataclasses import dataclass

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.runtime_ui.audio import (
    AudioSettings,
    initialize_audio,
    set_audio_settings,
)
from tet4d.engine.api import (
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    normalize_windowed_size,
)

_WINDOW_RESIZE_EVENTS = tuple(
    event_type
    for event_type in (
        getattr(pygame, "VIDEORESIZE", None),
        getattr(pygame, "WINDOWRESIZED", None),
        getattr(pygame, "WINDOWSIZECHANGED", None),
    )
    if isinstance(event_type, int)
)


@dataclass(frozen=True)
class RuntimeSettings:
    audio_settings: AudioSettings
    display_settings: DisplaySettings


@dataclass(frozen=True)
class DisplaySettings:
    fullscreen: bool = False
    windowed_size: tuple[int, int] = (1200, 760)


def normalize_display_settings(settings: DisplaySettings) -> DisplaySettings:
    width, height = normalize_windowed_size(
        settings.windowed_size,
        min_width=MIN_WINDOW_WIDTH,
        min_height=MIN_WINDOW_HEIGHT,
    )
    return DisplaySettings(
        fullscreen=bool(settings.fullscreen),
        windowed_size=(width, height),
    )


def apply_display_mode(
    settings: DisplaySettings,
    *,
    preferred_windowed_size: tuple[int, int] | None = None,
) -> pygame.Surface:
    normalized = normalize_display_settings(settings)
    if normalized.fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    size = (
        preferred_windowed_size
        if preferred_windowed_size is not None
        else normalized.windowed_size
    )
    width, height = normalize_windowed_size(
        size,
        min_width=MIN_WINDOW_WIDTH,
        min_height=MIN_WINDOW_HEIGHT,
    )
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


def load_audio_settings_from_store() -> AudioSettings:
    payload = engine_api.get_audio_settings_runtime()
    return AudioSettings(
        master_volume=float(payload["master_volume"]),
        sfx_volume=float(payload["sfx_volume"]),
        mute=bool(payload["mute"]),
    )


def load_display_settings_from_store() -> DisplaySettings:
    payload = engine_api.get_display_settings_runtime()
    return normalize_display_settings(
        DisplaySettings(
            fullscreen=bool(payload["fullscreen"]),
            windowed_size=tuple(payload["windowed_size"]),
        )
    )


def initialize_runtime(*, sync_audio_state: bool = True) -> RuntimeSettings:
    pygame.init()
    engine_api.initialize_keybinding_files_runtime()
    audio_settings = load_audio_settings_from_store()
    initialize_audio(audio_settings)
    if sync_audio_state:
        set_audio_settings(
            master_volume=audio_settings.master_volume,
            sfx_volume=audio_settings.sfx_volume,
            mute=audio_settings.mute,
        )
    display_settings = load_display_settings_from_store()
    analytics = engine_api.get_analytics_settings_runtime()
    engine_api.set_score_analyzer_logging_enabled_runtime(
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
    engine_api.save_display_settings_runtime(windowed_size=updated.windowed_size)
    return updated


def capture_windowed_display_settings_from_event(
    display_settings: DisplaySettings,
    *,
    event: pygame.event.Event,
    min_width: int = 640,
    min_height: int = 480,
) -> DisplaySettings:
    if display_settings.fullscreen or event.type not in _WINDOW_RESIZE_EVENTS:
        return display_settings

    raw_width = getattr(event, "w", None)
    raw_height = getattr(event, "h", None)
    if isinstance(raw_width, int) and isinstance(raw_height, int):
        width, height = raw_width, raw_height
    else:
        surface = pygame.display.get_surface()
        if surface is None:
            return display_settings
        width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return display_settings

    normalized = normalize_display_settings(
        DisplaySettings(
            fullscreen=False,
            windowed_size=(max(min_width, width), max(min_height, height)),
        )
    )
    if normalized.windowed_size == display_settings.windowed_size:
        return display_settings

    engine_api.save_display_settings_runtime(windowed_size=normalized.windowed_size)
    return normalized
