from __future__ import annotations

from typing import Callable

import pygame

from tet4d.ui.pygame.projection3d import Face

VisibleCell3D = tuple[tuple[float, float, float], int, bool, bool]


def split_faces_for_cells(
    cells: list[VisibleCell3D],
    *,
    build_faces_fn: Callable[
        [tuple[float, float, float], tuple[int, int, int], bool], list[Face]
    ],
    color_for_cell_fn: Callable[[int], tuple[int, int, int]],
) -> tuple[list[Face], list[Face], list[Face]]:
    locked_faces: list[Face] = []
    active_faces: list[Face] = []
    overlay_faces: list[Face] = []
    for coord, cell_id, active, is_overlay in cells:
        cell_faces = build_faces_fn(coord, color_for_cell_fn(cell_id), active)
        if is_overlay:
            overlay_faces.extend(cell_faces)
        elif active:
            active_faces.extend(cell_faces)
        else:
            locked_faces.extend(cell_faces)
    return locked_faces, active_faces, overlay_faces


def draw_sorted_faces(surface: pygame.Surface, faces: list[Face]) -> None:
    faces.sort(key=lambda x: x[0], reverse=True)
    for _depth, poly, color, active in faces:
        pygame.draw.polygon(surface, color, poly)
        border = (255, 255, 255) if active else (25, 25, 35)
        pygame.draw.polygon(surface, border, poly, 2 if active else 1)


def draw_translucent_faces(
    surface: pygame.Surface,
    faces: list[Face],
    *,
    fill_alpha: int,
    outline_alpha: int,
) -> None:
    if not faces:
        return
    faces.sort(key=lambda x: x[0], reverse=True)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for _depth, poly, color, active in faces:
        pygame.draw.polygon(overlay, (*color, fill_alpha), poly)
        border = (
            (255, 255, 255, outline_alpha)
            if active
            else (25, 25, 35, max(24, outline_alpha - 40))
        )
        pygame.draw.polygon(overlay, border, poly, 2 if active else 1)
    surface.blit(overlay, (0, 0))


def overlay_alpha_label(overlay_transparency: float) -> str:
    clamped = max(0.0, min(1.0, float(overlay_transparency)))
    return f"{int(round(clamped * 100.0))}%"


def overlay_opacity_scale(overlay_transparency: float) -> float:
    # Settings store transparency; renderer needs opacity.
    clamped = max(0.0, min(1.0, float(overlay_transparency)))
    return 1.0 - clamped


def draw_cells(
    surface: pygame.Surface,
    *,
    cells: list[VisibleCell3D],
    build_faces_fn: Callable[
        [tuple[float, float, float], tuple[int, int, int], bool], list[Face]
    ],
    color_for_cell_fn: Callable[[int], tuple[int, int, int]],
    overlay_transparency: float,
    assist_overlay_opacity_scale: float,
) -> None:
    locked_faces, active_faces, overlay_faces = split_faces_for_cells(
        cells,
        build_faces_fn=build_faces_fn,
        color_for_cell_fn=color_for_cell_fn,
    )
    if locked_faces:
        locked_alpha = overlay_opacity_scale(overlay_transparency)
        draw_translucent_faces(
            surface,
            locked_faces,
            fill_alpha=int(round(255 * locked_alpha)),
            outline_alpha=max(70, int(round(255 * min(1.0, locked_alpha + 0.12)))),
        )
    draw_sorted_faces(surface, active_faces)
    if overlay_faces:
        draw_translucent_faces(
            surface,
            overlay_faces,
            fill_alpha=int(round(255 * assist_overlay_opacity_scale)),
            outline_alpha=max(
                70, int(round(255 * min(1.0, assist_overlay_opacity_scale + 0.12)))
            ),
        )
