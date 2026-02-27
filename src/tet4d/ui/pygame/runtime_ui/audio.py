from __future__ import annotations

import math
from array import array
from dataclasses import dataclass

import pygame

import tet4d.engine.api as engine_api


@dataclass
class AudioSettings:
    master_volume: float = 0.8
    sfx_volume: float = 0.7
    mute: bool = False


_EVENT_SPECS: dict[str, tuple[float, int, float]] = (
    engine_api.audio_event_specs_runtime()
)


class AudioEngine:
    def __init__(self) -> None:
        self.settings = AudioSettings()
        self.enabled = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._sample_rate = 44100
        self._channels = 2

    def initialize(self) -> None:
        if self.enabled:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            init = pygame.mixer.get_init()
            if init is None:
                return
            self._sample_rate, _fmt, self._channels = init
            self.enabled = True
            self._sounds.clear()
        except pygame.error:
            self.enabled = False

    def apply_settings(self, settings: AudioSettings) -> None:
        self.settings = AudioSettings(
            master_volume=max(0.0, min(1.0, settings.master_volume)),
            sfx_volume=max(0.0, min(1.0, settings.sfx_volume)),
            mute=bool(settings.mute),
        )

    def _volume_scale(self) -> float:
        if self.settings.mute:
            return 0.0
        return self.settings.master_volume * self.settings.sfx_volume

    def _tone_buffer(
        self, frequency: float, duration_ms: int, amplitude: float
    ) -> bytes:
        frame_count = max(1, int(self._sample_rate * (duration_ms / 1000.0)))
        peak = int(32767 * max(0.0, min(1.0, amplitude)))
        wave = array("h")
        for idx in range(frame_count):
            t = idx / self._sample_rate
            sample = int(peak * math.sin(2.0 * math.pi * frequency * t))
            if self._channels <= 1:
                wave.append(sample)
            else:
                for _ in range(self._channels):
                    wave.append(sample)
        return wave.tobytes()

    def _get_sound(self, event_name: str) -> pygame.mixer.Sound | None:
        if not self.enabled:
            return None
        if event_name not in _EVENT_SPECS:
            return None
        cached = self._sounds.get(event_name)
        if cached is not None:
            return cached
        frequency, duration_ms, amplitude = _EVENT_SPECS[event_name]
        try:
            sound = pygame.mixer.Sound(
                buffer=self._tone_buffer(frequency, duration_ms, amplitude)
            )
        except pygame.error:
            return None
        self._sounds[event_name] = sound
        return sound

    def play(self, event_name: str) -> None:
        if not self.enabled:
            return
        volume = self._volume_scale()
        if volume <= 0.0:
            return
        sound = self._get_sound(event_name)
        if sound is None:
            return
        try:
            sound.set_volume(volume)
            sound.play()
        except pygame.error:
            return


_ENGINE = AudioEngine()


def initialize_audio(settings: AudioSettings | None = None) -> None:
    _ENGINE.initialize()
    if settings is not None:
        _ENGINE.apply_settings(settings)


def set_audio_settings(*, master_volume: float, sfx_volume: float, mute: bool) -> None:
    _ENGINE.apply_settings(
        AudioSettings(
            master_volume=master_volume,
            sfx_volume=sfx_volume,
            mute=mute,
        )
    )


def play_sfx(event_name: str) -> None:
    _ENGINE.play(event_name)
