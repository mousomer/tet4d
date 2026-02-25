from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import pygame

from .project_config import PROJECT_ROOT


_ICON_FG = (224, 236, 252)
_ICON_CACHE_LIMIT = 192
_ICON_SURFACE_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}
_ICON_MAP_FILE = PROJECT_ROOT / "config" / "help" / "icon_map.json"

_DEFAULT_ICON_MAP: dict[str, Any] = {
    "pack_root": "assets/help/icons/transform/svg",
    "default_theme": "dark",
    "themes": ["dark", "light"],
    "available_sizes": [16, 64],
    "action_map": {
        "move_x_neg": "move_x_neg",
        "move_x_pos": "move_x_pos",
        "move_y_neg": "move_y_neg",
        "move_y_pos": "move_y_pos",
        "move_z_neg": "move_z_neg",
        "move_z_pos": "move_z_pos",
        "move_w_neg": "move_w_neg",
        "move_w_pos": "move_w_pos",
        "rotate_xy_neg": "rot_xy_neg",
        "rotate_xy_pos": "rot_xy_pos",
        "rotate_xz_neg": "rot_xz_neg",
        "rotate_xz_pos": "rot_xz_pos",
        "rotate_yz_neg": "rot_yz_neg",
        "rotate_yz_pos": "rot_yz_pos",
        "rotate_xw_neg": "rot_xw_neg",
        "rotate_xw_pos": "rot_xw_pos",
        "rotate_yw_neg": "rot_yw_neg",
        "rotate_yw_pos": "rot_yw_pos",
        "rotate_zw_neg": "rot_zw_neg",
        "rotate_zw_pos": "rot_zw_pos",
    },
}

_MOVE_ICON_MAP: dict[str, tuple[str, int]] = {
    "move_x_neg": ("x", -1),
    "move_x_pos": ("x", 1),
    "move_y_neg": ("y", -1),
    "move_y_pos": ("y", 1),
    "move_z_neg": ("z", -1),
    "move_z_pos": ("z", 1),
    "move_w_neg": ("w", -1),
    "move_w_pos": ("w", 1),
}


def clear_action_icon_cache() -> None:
    _ICON_SURFACE_CACHE.clear()


def action_icon_cache_size() -> int:
    return len(_ICON_SURFACE_CACHE)


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


def _normalize_relative_asset_path(raw: object, *, default_relative: str) -> str:
    if not isinstance(raw, str):
        return default_relative
    text = raw.strip().replace("\\", "/")
    if not text:
        return default_relative
    candidate = Path(text)
    if candidate.is_absolute():
        return default_relative
    parts = [part for part in candidate.parts if part not in ("", ".")]
    if (
        not parts
        or any(part == ".." for part in parts)
        or any(":" in part for part in parts)
    ):
        return default_relative
    return "/".join(parts)


def _resolve_repo_asset_root(relative_path: str, default_relative: str) -> Path:
    root = PROJECT_ROOT.resolve()
    fallback = (PROJECT_ROOT / default_relative).resolve()
    resolved = (PROJECT_ROOT / relative_path).resolve()
    if resolved == root or root in resolved.parents:
        return resolved
    return fallback


def _normalized_size_list(raw_sizes: object) -> tuple[int, ...]:
    if not isinstance(raw_sizes, list):
        return (16, 64)
    sizes: list[int] = []
    for value in raw_sizes:
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        if value < 8:
            continue
        sizes.append(value)
    deduped = sorted(set(sizes))
    if not deduped:
        return (16, 64)
    return tuple(deduped)


def _normalized_theme_list(raw_themes: object) -> tuple[str, ...]:
    if not isinstance(raw_themes, list):
        return ("dark", "light")
    themes: list[str] = []
    for value in raw_themes:
        if not isinstance(value, str):
            continue
        theme = value.strip().lower()
        if not theme:
            continue
        themes.append(theme)
    deduped = tuple(dict.fromkeys(themes))
    if not deduped:
        return ("dark", "light")
    return deduped


def _normalized_action_map(raw_map: object) -> dict[str, str]:
    if not isinstance(raw_map, dict):
        return dict(_DEFAULT_ICON_MAP["action_map"])
    mapped: dict[str, str] = {}
    for key, value in raw_map.items():
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        action = key.strip().lower()
        icon = value.strip().lower()
        if not action or not icon:
            continue
        mapped[action] = icon
    if not mapped:
        return dict(_DEFAULT_ICON_MAP["action_map"])
    return mapped


@lru_cache(maxsize=1)
def _icon_map_payload() -> dict[str, Any]:
    loaded = _read_json_object(_ICON_MAP_FILE)
    merged = _merge_objects(_DEFAULT_ICON_MAP, loaded)
    default_rel = str(_DEFAULT_ICON_MAP["pack_root"])
    pack_rel = _normalize_relative_asset_path(
        merged.get("pack_root"), default_relative=default_rel
    )
    pack_root = _resolve_repo_asset_root(pack_rel, default_rel)
    themes = _normalized_theme_list(merged.get("themes"))
    default_theme = str(merged.get("default_theme", "dark")).strip().lower()
    if default_theme not in themes:
        default_theme = themes[0]
    return {
        "pack_root": pack_root,
        "available_sizes": _normalized_size_list(merged.get("available_sizes")),
        "themes": themes,
        "default_theme": default_theme,
        "action_map": _normalized_action_map(merged.get("action_map")),
    }


def _draw_arrow(
    surface: pygame.Surface,
    *,
    start: tuple[int, int],
    end: tuple[int, int],
    color: tuple[int, int, int],
    width: int = 2,
    head: int = 6,
) -> None:
    pygame.draw.line(surface, color, start, end, width)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max(1.0, math.hypot(dx, dy))
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    left = (
        int(end[0] - ux * head + px * (head * 0.45)),
        int(end[1] - uy * head + py * (head * 0.45)),
    )
    right = (
        int(end[0] - ux * head - px * (head * 0.45)),
        int(end[1] - uy * head - py * (head * 0.45)),
    )
    pygame.draw.polygon(surface, color, [end, left, right])


def _draw_move_icon(
    surface: pygame.Surface, rect: pygame.Rect, axis: str, direction: int
) -> None:
    cx = rect.centerx
    cy = rect.centery
    span = max(6, min(rect.width, rect.height) // 2 - 4)

    if axis == "x":
        start = (cx - span, cy)
        end = (cx + span, cy)
    elif axis == "y":
        start = (cx, cy - span)
        end = (cx, cy + span)
    elif axis == "z":
        start = (cx, cy + span)
        end = (cx, cy - span)
    else:  # w-axis visualized as diagonal in icon space
        start = (cx - span + 2, cy + span - 2)
        end = (cx + span - 2, cy - span + 2)

    if direction < 0:
        start, end = end, start
    _draw_arrow(surface, start=start, end=end, color=_ICON_FG)


def _draw_drop_icon(surface: pygame.Surface, rect: pygame.Rect, hard: bool) -> None:
    cx = rect.centerx
    top = rect.y + 5
    bottom = rect.bottom - 5
    _draw_arrow(surface, start=(cx, top), end=(cx, bottom), color=_ICON_FG)
    if hard:
        _draw_arrow(surface, start=(cx, top + 4), end=(cx, bottom), color=_ICON_FG)


def _rotation_direction(action: str) -> int:
    return -1 if action.endswith("_neg") else 1


def _draw_rotate_icon(surface: pygame.Surface, rect: pygame.Rect, action: str) -> None:
    direction = _rotation_direction(action)
    ring = rect.inflate(-10, -10)
    start_ang = math.radians(210 if direction > 0 else 30)
    end_ang = math.radians(20 if direction > 0 else 200)
    pygame.draw.arc(surface, _ICON_FG, ring, start_ang, end_ang, 2)

    if direction > 0:
        tip = (ring.right - 2, ring.centery - 2)
        tail = (tip[0] - 7, tip[1] + 5)
    else:
        tip = (ring.left + 2, ring.centery + 2)
        tail = (tip[0] + 7, tip[1] - 5)
    _draw_arrow(surface, start=tail, end=tip, color=_ICON_FG, width=2, head=5)


def action_icon_action(action: str | None) -> str | None:
    if not action:
        return None
    if action.startswith("move_"):
        return action
    if action.startswith("rotate_"):
        return action
    if action in {"soft_drop", "hard_drop"}:
        return action
    return None


def draw_action_icon(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    action: str | None,
) -> None:
    mapped = action_icon_action(action)
    if mapped is None or rect.width < 14 or rect.height < 14:
        return
    icon = _cached_icon_surface(mapped, rect.width, rect.height)
    surface.blit(icon, rect.topleft)


def _cached_icon_surface(action: str, width: int, height: int) -> pygame.Surface:
    key = (action, width, height)
    cached = _ICON_SURFACE_CACHE.get(key)
    if cached is not None:
        return cached
    icon = _build_icon_surface(action, width=width, height=height)
    if len(_ICON_SURFACE_CACHE) >= _ICON_CACHE_LIMIT:
        _ICON_SURFACE_CACHE.clear()
    _ICON_SURFACE_CACHE[key] = icon
    return icon


def _mapped_asset_name(action: str) -> str | None:
    settings = _icon_map_payload()
    normalized = action.strip().lower()
    action_map = settings["action_map"]
    mapped = action_map.get(normalized)
    if isinstance(mapped, str) and mapped:
        return mapped
    if normalized.startswith("move_"):
        return normalized
    if normalized.startswith("rotate_"):
        return f"rot_{normalized[len('rotate_') :]}"
    if normalized.startswith("rot_"):
        return normalized
    return None


def _icon_candidate_paths(action: str, *, width: int, height: int) -> tuple[Path, ...]:
    asset_name = _mapped_asset_name(action)
    if asset_name is None:
        return tuple()
    settings = _icon_map_payload()
    root: Path = settings["pack_root"]
    sizes: tuple[int, ...] = settings["available_sizes"]
    themes: tuple[str, ...] = settings["themes"]
    default_theme: str = settings["default_theme"]
    target_size = max(width, height)
    ordered_sizes = sorted(sizes, key=lambda size: (abs(size - target_size), size))
    ordered_themes = [default_theme] + [
        theme for theme in themes if theme != default_theme
    ]
    return tuple(
        root / str(size) / theme / f"{asset_name}.svg"
        for size in ordered_sizes
        for theme in ordered_themes
    )


def _load_svg_icon(path: Path, *, width: int, height: int) -> pygame.Surface | None:
    if not path.exists():
        return None
    try:
        loaded = pygame.image.load(str(path))
    except (OSError, pygame.error, ValueError):
        return None
    if loaded.get_width() != width or loaded.get_height() != height:
        loaded = pygame.transform.smoothscale(loaded, (width, height))
    return loaded


def _vector_icon_surface(
    action: str, *, width: int, height: int
) -> pygame.Surface | None:
    for path in _icon_candidate_paths(action, width=width, height=height):
        loaded = _load_svg_icon(path, width=width, height=height)
        if loaded is not None:
            return loaded
    return None


def _build_icon_surface(action: str, *, width: int, height: int) -> pygame.Surface:
    loaded = _vector_icon_surface(action, width=width, height=height)
    if loaded is not None:
        return loaded

    icon = pygame.Surface((width, height), pygame.SRCALPHA)
    icon_rect = icon.get_rect()
    move_spec = _MOVE_ICON_MAP.get(action)
    if move_spec is not None:
        axis, direction = move_spec
        _draw_move_icon(icon, icon_rect, axis=axis, direction=direction)
        return icon
    if action == "soft_drop":
        _draw_drop_icon(icon, icon_rect, hard=False)
        return icon
    if action == "hard_drop":
        _draw_drop_icon(icon, icon_rect, hard=True)
        return icon
    _draw_rotate_icon(icon, icon_rect, action)
    return icon
