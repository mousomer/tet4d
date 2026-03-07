from __future__ import annotations

from dataclasses import dataclass

import pygame

from tet4d.engine.runtime.menu_settings_state import (
    get_analytics_settings,
    get_audio_settings,
    get_display_settings,
    load_app_settings_payload,
    save_display_settings,
)
from tet4d.engine.runtime.settings_schema import (
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    normalize_windowed_size,
)
from tet4d.engine.runtime.score_analyzer import set_score_analyzer_logging_enabled
from tet4d.ui.pygame.keybindings import (
    initialize_keybinding_files,
    load_active_profile_bindings,
    set_active_key_profile,
)
from tet4d.ui.pygame.runtime_ui.audio import (
    AudioSettings,
    initialize_audio,
    set_audio_settings,
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
    width, height = normalize_windowed_size(settings.windowed_size)
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
    width, height = normalize_windowed_size(size)
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


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


def _sync_saved_keybinding_profile() -> None:
    initialize_keybinding_files()
    payload = load_app_settings_payload()
    profile = payload.get("active_profile") if isinstance(payload, dict) else None
    if isinstance(profile, str) and profile.strip():
        set_active_key_profile(profile)
    load_active_profile_bindings()


def initialize_runtime(*, sync_audio_state: bool = True) -> RuntimeSettings:
    pygame.init()
    _sync_saved_keybinding_profile()
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
    min_width: int = MIN_WINDOW_WIDTH,
    min_height: int = MIN_WINDOW_HEIGHT,
) -> DisplaySettings:
    if display_settings.fullscreen:
        return display_settings
    surface = pygame.display.get_surface()
    if surface is None:
        return display_settings
    width, height = normalize_windowed_size(
        surface.get_size(),
        min_width=min_width,
        min_height=min_height,
        fallback=display_settings.windowed_size,
    )
    if (width, height) == display_settings.windowed_size:
        return display_settings
    updated = DisplaySettings(fullscreen=False, windowed_size=(width, height))
    save_display_settings(windowed_size=updated.windowed_size)
    return updated


def capture_windowed_display_settings_from_event(
    display_settings: DisplaySettings,
    *,
    event: pygame.event.Event,
    min_width: int = MIN_WINDOW_WIDTH,
    min_height: int = MIN_WINDOW_HEIGHT,
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

    save_display_settings(windowed_size=normalized.windowed_size)
    return normalized


