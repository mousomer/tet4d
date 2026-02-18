from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pygame

from .control_helper import control_groups_for_dimension, draw_grouped_control_helper
from .keybindings import (
    binding_action_description,
    binding_group_label,
    runtime_binding_groups_for_dimension,
)
from .menu_config import settings_category_docs

try:
    from PIL import Image, ImageSequence
except ModuleNotFoundError:  # pragma: no cover - exercised when Pillow is missing
    Image = None
    ImageSequence = None


_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_MUTED_COLOR = (192, 200, 228)
_HIGHLIGHT = (255, 224, 128)
_ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "help"
_PAGE_COUNT = 6
_SETTINGS_DOCS = settings_category_docs()


@dataclass(frozen=True)
class _GifClip:
    frames: tuple[pygame.Surface, ...]
    durations_ms: tuple[int, ...]
    total_ms: int


@dataclass
class _HelpState:
    page: int = 0
    dimension: int = 2
    running: bool = True
    elapsed_ms: int = 0


def _draw_gradient(surface: pygame.Surface) -> None:
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(_BG_TOP[0] * (1 - t) + _BG_BOTTOM[0] * t),
            int(_BG_TOP[1] * (1 - t) + _BG_BOTTOM[1] * t),
            int(_BG_TOP[2] * (1 - t) + _BG_BOTTOM[2] * t),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))


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
    total_ms = sum(durations)
    return _GifClip(tuple(frames), tuple(durations), total_ms)


@lru_cache(maxsize=8)
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


def _draw_overview_page(surface: pygame.Surface, fonts, state: _HelpState, context_label: str) -> None:
    width, _ = surface.get_size()
    lines = [
        f"Context: {context_label}",
        "",
        "This menu explains controls, scoring, piece sets, bots, and slicing.",
        "Use Left/Right to switch pages.",
        "Use Up/Down to switch dimension on the Controls page.",
        "",
        "Quick summary:",
        "1. Key Reference page lists every active key and what it does.",
        "2. Controls page shows grouped controls with animated translation/rotation guides.",
        "3. Settings page explains audio/display/profile/bot/setup settings.",
        "4. Workflows page explains menu structure and profile flow.",
        "5. Concepts page explains slicing, scoring, and reset/autosave rules.",
        "6. Up/Down switches dimension to inspect 2D/3D/4D key maps.",
    ]
    y = 132
    for line in lines:
        color = (
            _TEXT_COLOR
            if line and not line.startswith(("1.", "2.", "3.", "4.", "5.", "6."))
            else _MUTED_COLOR
        )
        surf = fonts.hint_font.render(line, True, color)
        surface.blit(surf, ((width - surf.get_width()) // 2, y))
        y += surf.get_height() + 6


def _display_key_name(key: int) -> str:
    raw = pygame.key.name(key)
    if not raw:
        return str(key)
    if len(raw) == 1:
        return raw.upper()
    return raw.replace("left shift", "LShift").replace("right shift", "RShift").title()


def _format_keys(keys: tuple[int, ...]) -> str:
    if not keys:
        return "-"
    return "/".join(_display_key_name(key) for key in keys)


def _draw_key_reference_page(surface: pygame.Surface, fonts, state: _HelpState) -> None:
    width, height = surface.get_size()
    title = fonts.hint_font.render(
        f"Key Reference ({state.dimension}D + General)",
        True,
        _HIGHLIGHT,
    )
    surface.blit(title, ((width - title.get_width()) // 2, 120))

    groups = runtime_binding_groups_for_dimension(state.dimension)
    group_order = ("system", "game", "camera", "slice")
    y = 154
    line_h = fonts.hint_font.get_height() + 4
    for group_name in group_order:
        if group_name not in groups:
            continue
        header = fonts.hint_font.render(binding_group_label(group_name), True, _HIGHLIGHT)
        surface.blit(header, (36, y))
        y += header.get_height() + 3

        actions = groups[group_name]
        for action_name in sorted(actions.keys()):
            key_text = _format_keys(tuple(actions[action_name]))
            desc = binding_action_description(action_name)
            row = f"{key_text:<18} {desc}"
            row_surf = fonts.hint_font.render(row, True, _TEXT_COLOR)
            surface.blit(row_surf, (52, y))
            y += line_h
            if y > height - 56:
                overflow = fonts.hint_font.render("... (switch dimension for other key maps)", True, _MUTED_COLOR)
                surface.blit(overflow, (52, y))
                return
        y += 6


def _draw_controls_page(surface: pygame.Surface, fonts, state: _HelpState) -> None:
    width, height = surface.get_size()
    header = fonts.hint_font.render(f"Controls for {state.dimension}D", True, _HIGHLIGHT)
    surface.blit(header, ((width - header.get_width()) // 2, 120))

    gif_w = min(300, max(180, (width - 80) // 2))
    gif_h = min(170, max(120, (height // 4)))
    left_rect = pygame.Rect(24, 154, gif_w, gif_h)
    right_rect = pygame.Rect(width - gif_w - 24, 154, gif_w, gif_h)

    for rect in (left_rect, right_rect):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 145), panel.get_rect(), border_radius=12)
        surface.blit(panel, rect.topleft)

    trans_clip = _cached_clip("translation_keys.gif", left_rect.width - 20, left_rect.height - 42)
    rot_clip = _cached_clip("rotation_keys.gif", right_rect.width - 20, right_rect.height - 42)

    trans_title = fonts.hint_font.render("Translation Guide", True, _MUTED_COLOR)
    rot_title = fonts.hint_font.render("Rotation Guide", True, _MUTED_COLOR)
    surface.blit(trans_title, (left_rect.x + 10, left_rect.y + 8))
    surface.blit(rot_title, (right_rect.x + 10, right_rect.y + 8))

    if trans_clip is not None:
        frame = _frame_for_elapsed(trans_clip, state.elapsed_ms)
        surface.blit(frame, (left_rect.x + 10, left_rect.y + 30))
    else:
        missing = fonts.hint_font.render("translation_keys.gif missing", True, (255, 160, 160))
        surface.blit(missing, (left_rect.x + 10, left_rect.y + 36))

    if rot_clip is not None:
        frame = _frame_for_elapsed(rot_clip, state.elapsed_ms)
        surface.blit(frame, (right_rect.x + 10, right_rect.y + 30))
    else:
        missing = fonts.hint_font.render("rotation_keys.gif missing", True, (255, 160, 160))
        surface.blit(missing, (right_rect.x + 10, right_rect.y + 36))

    groups_rect = pygame.Rect(24, left_rect.bottom + 12, width - 48, height - (left_rect.bottom + 26))
    draw_grouped_control_helper(
        surface,
        groups=control_groups_for_dimension(state.dimension),
        rect=groups_rect,
        panel_font=fonts.panel_font,
        hint_font=fonts.hint_font,
    )


def _draw_settings_page(surface: pygame.Surface, fonts) -> None:
    width, _ = surface.get_size()
    title = fonts.hint_font.render("Settings Reference", True, _HIGHLIGHT)
    surface.blit(title, ((width - title.get_width()) // 2, 120))

    lines: list[str] = [
        "Settings are grouped into categories and shared across launcher and pause menus.",
        "Reset actions require confirmation. Autosave is silent and complements explicit Save.",
        "",
        "Core categories:",
        "Audio: master volume, SFX volume, mute.",
        "Display: fullscreen/window size and apply/save flow.",
        "Bot: mode, run speed, hard-drop policy, planning budget.",
        "Profiles: active profile, save-as, rename, delete custom.",
        "Setup: board size, piece-set choices, challenge layers.",
        "",
        "Config files:",
        "Audio/display defaults and menu categories are loaded from config/menu/*.json.",
        "",
        "Extended category docs:",
    ]
    for entry in _SETTINGS_DOCS:
        lines.append(f"{entry['label']}: {entry['description']}")

    y = 154
    for line in lines:
        color = _TEXT_COLOR if line else _MUTED_COLOR
        surf = fonts.hint_font.render(line, True, color)
        surface.blit(surf, ((width - surf.get_width()) // 2, y))
        y += surf.get_height() + 6


def _draw_workflows_page(surface: pygame.Surface, fonts) -> None:
    width, _ = surface.get_size()
    lines = [
        "Menu & Profile Workflow",
        "",
        "Launcher main menu:",
        "Play 2D / 3D / 4D, Settings, Keybindings Setup, Bot Options, Help, Quit.",
        "",
        "Keybindings Setup:",
        "1. Section menu: General, 2D, 3D, 4D.",
        "2. Inside a section: bindings grouped by System/Game/Camera/Slice.",
        "3. Enter starts rebinding selected action.",
        "4. L loads and S saves keybinding files for current scope.",
        "5. N create profile, F2 rename, F3 save as, [/] cycle profile.",
        "",
        "Pause menu sync:",
        "Pause menus expose the same settings/keybindings/help/bot options flows.",
    ]
    y = 132
    for line in lines:
        color = _HIGHLIGHT if line.endswith(":") or line == "Menu & Profile Workflow" else _TEXT_COLOR
        if line == "":
            y += fonts.hint_font.get_height() // 2
            continue
        surf = fonts.hint_font.render(line, True, color)
        surface.blit(surf, ((width - surf.get_width()) // 2, y))
        y += surf.get_height() + 6


def _draw_concepts_page(surface: pygame.Surface, fonts) -> None:
    width, _ = surface.get_size()
    lines = [
        "Concepts",
        "",
        "Slicing:",
        "A slice fixes one non-gravity axis to a selected coordinate.",
        "In 4D, each w layer is rendered as its own 3D board view.",
        "",
        "Scoring:",
        "Base points are awarded for piece placement and cleared lines/layers.",
        "Assist settings (bot, grid helpers, speed boosts) adjust the score multiplier.",
        "",
        "Settings and resets:",
        "Resets require confirmation to avoid accidental data loss.",
        "Autosave paths do not ask confirmation and complement explicit Save actions.",
        "",
        "Menu sync:",
        "Main and pause menus both expose settings, keybindings, help, bot options, and quit.",
    ]
    y = 132
    for line in lines:
        color = _HIGHLIGHT if line in {"Concepts", "Slicing:", "Scoring:", "Settings and resets:"} else _TEXT_COLOR
        if line == "":
            y += fonts.hint_font.get_height() // 2
            continue
        surf = fonts.hint_font.render(line, True, color)
        surface.blit(surf, ((width - surf.get_width()) // 2, y))
        y += surf.get_height() + 6


def _draw_help(surface: pygame.Surface, fonts, state: _HelpState, context_label: str) -> None:
    _draw_gradient(surface)
    width, _ = surface.get_size()
    title = fonts.title_font.render("Help & Explanations", True, _TEXT_COLOR)
    subtitle = fonts.hint_font.render(
        "Left/Right page   Up/Down dimension   Esc back",
        True,
        _MUTED_COLOR,
    )
    page_label = fonts.hint_font.render(f"Page {state.page + 1}/{_PAGE_COUNT}", True, _MUTED_COLOR)
    surface.blit(title, ((width - title.get_width()) // 2, 34))
    surface.blit(subtitle, ((width - subtitle.get_width()) // 2, 82))
    surface.blit(page_label, (width - page_label.get_width() - 20, 16))

    if state.page == 0:
        _draw_overview_page(surface, fonts, state, context_label)
    elif state.page == 1:
        _draw_key_reference_page(surface, fonts, state)
    elif state.page == 2:
        _draw_controls_page(surface, fonts, state)
    elif state.page == 3:
        _draw_settings_page(surface, fonts)
    elif state.page == 4:
        _draw_workflows_page(surface, fonts)
    else:
        _draw_concepts_page(surface, fonts)


def run_help_menu(
    screen: pygame.Surface,
    fonts,
    *,
    dimension: int = 2,
    context_label: str = "Launcher",
) -> pygame.Surface:
    state = _HelpState(dimension=max(2, min(4, int(dimension))))
    clock = pygame.time.Clock()

    while state.running:
        dt = clock.tick(60)
        state.elapsed_ms += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return screen
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                state.running = False
                break
            if event.key == pygame.K_LEFT:
                state.page = (state.page - 1) % _PAGE_COUNT
                continue
            if event.key == pygame.K_RIGHT:
                state.page = (state.page + 1) % _PAGE_COUNT
                continue
            if event.key == pygame.K_UP:
                state.dimension = 4 if state.dimension == 2 else state.dimension - 1
                continue
            if event.key == pygame.K_DOWN:
                state.dimension = 2 if state.dimension == 4 else state.dimension + 1
                continue

        _draw_help(screen, fonts, state, context_label)
        pygame.display.flip()

    return screen
