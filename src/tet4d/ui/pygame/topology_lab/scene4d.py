from __future__ import annotations

import pygame

from tet4d.engine.topology_explorer import BoundaryRef, ExplorerTopologyProfile

from .common import TopologyLabHitTarget
from .projection_scene import draw_projection_scene


def draw_scene(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    basis_arrows: list[dict[str, object]] | tuple[dict[str, object], ...],
    preview_dims: tuple[int, ...],
    profile: ExplorerTopologyProfile | None = None,
    active_tool: str | None = None,
    selected_glue_id: str | None = None,
    highlighted_glue_id: str | None = None,
    hovered_boundary_index: int | None = None,
    selected_boundary_index: int | None = None,
    probe_coord: tuple[int, ...] | None = None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None = None,
    neighbor_markers: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None = None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None = None,
    sandbox_valid: bool | None = None,
    sandbox_message: str = "",
    view: object | None = None,
) -> list[TopologyLabHitTarget]:
    del basis_arrows, view
    return draw_projection_scene(
        surface,
        fonts,
        dimension=4,
        area=area,
        boundaries=boundaries,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        active_glue_ids=active_glue_ids,
        preview_dims=preview_dims,
        profile=profile,
        active_tool=active_tool,
        selected_glue_id=selected_glue_id,
        highlighted_glue_id=highlighted_glue_id,
        hovered_boundary_index=hovered_boundary_index,
        selected_boundary_index=selected_boundary_index,
        probe_coord=probe_coord,
        probe_path=probe_path,
        neighbor_markers=neighbor_markers,
        sandbox_cells=sandbox_cells,
        sandbox_valid=sandbox_valid,
        sandbox_message=sandbox_message,
    )


__all__ = ["draw_scene"]
