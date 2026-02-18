from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pygame

try:
    from PIL import Image, ImageSequence
except ModuleNotFoundError:  # pragma: no cover - exercised when Pillow is missing
    Image = None
    ImageSequence = None


_ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "help"
_PANEL_BG = (0, 0, 0, 132)
_BOX_BG = (0, 0, 0, 110)
_LABEL_COLOR = (188, 197, 228)
_MISSING_COLOR = (255, 160, 160)


@dataclass(frozen=True)
class _GifClip:
    frames: tuple[pygame.Surface, ...]
    durations_ms: tuple[int, ...]
    total_ms: int


def _load_clip(path: Path, size: tuple[int, int]) -> _GifClip | None:
    if Image is None or ImageSequence is None:
        return None
    if not path.exists():
        return None

    image = Image.open(path)
    frames: list[pygame.Surface] = []
    durations: list[int] = []
    for frame in ImageSequence.Iterator(image):
        rgba = frame.convert("RGBA")
        surf = pygame.image.fromstring(rgba.tobytes(), rgba.size, "RGBA").convert_alpha()
        if surf.get_size() != size:
            surf = pygame.transform.smoothscale(surf, size)
        frames.append(surf)
        duration = frame.info.get("duration", 90)
        duration_ms = int(duration) if isinstance(duration, int) and duration > 0 else 90
        durations.append(duration_ms)
    if not frames:
        return None
    return _GifClip(tuple(frames), tuple(durations), sum(durations))


@lru_cache(maxsize=24)
def _cached_clip(name: str, width: int, height: int) -> _GifClip | None:
    return _load_clip(_ASSET_DIR / name, (width, height))


def _frame_for_elapsed(clip: _GifClip, elapsed_ms: int) -> pygame.Surface:
    if clip.total_ms <= 0:
        return clip.frames[0]
    t = elapsed_ms % clip.total_ms
    accum = 0
    for frame, duration in zip(clip.frames, clip.durations_ms):
        accum += duration
        if t < accum:
            return frame
    return clip.frames[-1]


def _draw_clip_panel(
    surface: pygame.Surface,
    fonts,
    rect: pygame.Rect,
    *,
    label: str,
    clip_name: str,
    elapsed_ms: int,
) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, _BOX_BG, panel.get_rect(), border_radius=9)
    surface.blit(panel, rect.topleft)

    label_surf = fonts.hint_font.render(label, True, _LABEL_COLOR)
    surface.blit(label_surf, (rect.x + 8, rect.y + 6))

    image_w = max(8, rect.width - 16)
    image_h = max(8, rect.height - label_surf.get_height() - 14)
    image_x = rect.x + 8
    image_y = rect.y + label_surf.get_height() + 10
    clip = _cached_clip(clip_name, image_w, image_h)
    if clip is None:
        missing = fonts.hint_font.render(f"{clip_name} missing", True, _MISSING_COLOR)
        surface.blit(missing, (image_x, image_y + 4))
        return
    frame = _frame_for_elapsed(clip, elapsed_ms)
    surface.blit(frame, (image_x, image_y))


def draw_translation_rotation_guides(
    surface: pygame.Surface,
    fonts,
    *,
    rect: pygame.Rect,
    title: str = "Control Guides",
    elapsed_ms: int | None = None,
) -> None:
    if rect.width < 140 or rect.height < 82:
        return
    if elapsed_ms is None:
        elapsed_ms = pygame.time.get_ticks()

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, _PANEL_BG, panel.get_rect(), border_radius=11)
    surface.blit(panel, rect.topleft)

    title_surf = fonts.hint_font.render(title, True, _LABEL_COLOR)
    surface.blit(title_surf, (rect.x + 10, rect.y + 6))

    inner_y = rect.y + title_surf.get_height() + 11
    inner_h = rect.bottom - inner_y - 8
    if inner_h < 28:
        return

    gap = 10
    if rect.width < 300:
        box_w = rect.width - 20
        box_h = (inner_h - gap) // 2
        if box_h < 26:
            return
        left = pygame.Rect(rect.x + 10, inner_y, box_w, box_h)
        right = pygame.Rect(rect.x + 10, left.bottom + gap, box_w, box_h)
    else:
        box_w = (rect.width - 30 - gap) // 2
        left = pygame.Rect(rect.x + 10, inner_y, box_w, inner_h)
        right = pygame.Rect(left.right + gap, inner_y, box_w, inner_h)
    _draw_clip_panel(
        surface,
        fonts,
        left,
        label="Translation",
        clip_name="translation_keys.gif",
        elapsed_ms=elapsed_ms,
    )
    _draw_clip_panel(
        surface,
        fonts,
        right,
        label="Rotation",
        clip_name="rotation_keys.gif",
        elapsed_ms=elapsed_ms,
    )
