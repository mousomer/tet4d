from __future__ import annotations

from types import SimpleNamespace
import unittest

import pygame

from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)
from tet4d.ui.pygame.topology_lab.arrow_overlay import _glue_style
from tet4d.ui.pygame.topology_lab import projection_scene
from tet4d.ui.pygame.topology_lab import scene2d
from tet4d.ui.pygame.topology_lab.projection_scene import (
    projection_hidden_label,
    projection_pairs_for_dimension,
)
from tet4d.ui.pygame.topology_lab.scene2d import draw_scene as draw_scene_2d
from tet4d.ui.pygame.topology_lab.scene3d import draw_scene as draw_scene_3d
from tet4d.ui.pygame.topology_lab.scene4d import draw_scene as draw_scene_4d
from tet4d.ui.pygame.ui_utils import fit_text


class TestTopologyLabScenes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def _fonts(self):
        return SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )

    def _profile_3d(self) -> ExplorerTopologyProfile:
        return ExplorerTopologyProfile(
            dimension=3,
            gluings=(
                GluingDescriptor(
                    glue_id="glue_001",
                    source=BoundaryRef(dimension=3, axis=0, side="-"),
                    target=BoundaryRef(dimension=3, axis=0, side="+"),
                    transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                ),
            ),
        )

    def _profile_4d(self) -> ExplorerTopologyProfile:
        return ExplorerTopologyProfile(
            dimension=4,
            gluings=(
                GluingDescriptor(
                    glue_id="glue_001",
                    source=BoundaryRef(dimension=4, axis=0, side="-"),
                    target=BoundaryRef(dimension=4, axis=3, side="+"),
                    transform=BoundaryTransform(permutation=(0, 1, 2), signs=(1, 1, 1)),
                ),
            ),
        )

    def _assert_sandbox_cells_render(
        self,
        *,
        dimension: int,
        surface_size: tuple[int, int],
        area: pygame.Rect,
        preview_dims: tuple[int, ...],
        probe_coord: tuple[int, ...],
        sandbox_cells: tuple[tuple[int, ...], ...],
    ) -> None:
        fonts = self._fonts()
        profile = self._profile_3d() if dimension == 3 else self._profile_4d()
        boundaries = tuple(
            BoundaryRef(dimension=dimension, axis=axis, side=side)
            for axis in range(dimension)
            for side in ("-", "+")
        )
        control = pygame.Surface(surface_size)
        rendered = pygame.Surface(surface_size)
        draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
        common_kwargs = dict(
            area=area,
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[-1],
            active_glue_ids={boundary.label: "free" for boundary in boundaries},
            basis_arrows=(),
            preview_dims=preview_dims,
            profile=profile,
            active_tool="piece_sandbox",
            probe_coord=probe_coord,
        )
        draw_scene(control, fonts, **common_kwargs)
        hits = draw_scene(rendered, fonts, **common_kwargs, sandbox_cells=sandbox_cells)
        target = next(
            hit
            for hit in hits
            if hit.kind == "projection_cell" and hit.value == sandbox_cells[0]
        )
        self.assertNotEqual(
            rendered.get_at(target.rect.center),
            control.get_at(target.rect.center),
        )

    def _assert_projection_overlay_projects_hidden_slices(
        self,
        *,
        dimension: int,
        surface_size: tuple[int, int],
        area: pygame.Rect,
        preview_dims: tuple[int, ...],
        probe_coord: tuple[int, ...],
        target_value: tuple[int, ...],
        extra_kwargs: dict[str, object],
    ) -> None:
        fonts = self._fonts()
        profile = self._profile_3d() if dimension == 3 else self._profile_4d()
        boundaries = tuple(
            BoundaryRef(dimension=dimension, axis=axis, side=side)
            for axis in range(dimension)
            for side in ("-", "+")
        )
        control = pygame.Surface(surface_size)
        rendered = pygame.Surface(surface_size)
        draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
        common_kwargs = dict(
            area=area,
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[-1],
            active_glue_ids={boundary.label: "free" for boundary in boundaries},
            basis_arrows=(),
            preview_dims=preview_dims,
            profile=profile,
            active_tool="piece_sandbox",
            probe_coord=probe_coord,
        )
        merged_kwargs = dict(common_kwargs)
        merged_kwargs.update(extra_kwargs)
        control_hits = draw_scene(control, fonts, **common_kwargs)
        draw_scene(rendered, fonts, **merged_kwargs)
        target = next(
            hit
            for hit in control_hits
            if hit.kind == "projection_cell" and hit.value == target_value
        )
        self.assertNotEqual(
            rendered.get_at(target.rect.center),
            control.get_at(target.rect.center),
        )

    def test_projection_pairs_match_required_primary_views(self) -> None:
        self.assertEqual(projection_pairs_for_dimension(3), ((0, 1), (0, 2), (1, 2)))
        self.assertEqual(
            projection_pairs_for_dimension(4),
            ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)),
        )

    def test_projection_hidden_labels_expose_hidden_coordinates(self) -> None:
        self.assertEqual(
            projection_hidden_label(3, (0, 1), (1, 2, 3)),
            "hidden z=3  slice",
        )
        self.assertEqual(
            projection_hidden_label(4, (0, 1), (1, 2, 3, 0)),
            "hidden z=3  w=0  slice",
        )

    def test_scene3d_returns_three_projection_panels_and_clickable_cells(self) -> None:
        surface = pygame.Surface((960, 760))
        fonts = self._fonts()
        profile = self._profile_3d()
        boundaries = tuple(
            BoundaryRef(dimension=3, axis=axis, side=side)
            for axis in range(3)
            for side in ("-", "+")
        )
        hits = draw_scene_3d(
            surface,
            fonts,
            area=pygame.Rect(40, 80, 620, 360),
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[1],
            active_glue_ids={
                "x-": "glue_001",
                "x+": "glue_001",
                "y-": "free",
                "y+": "free",
                "z-": "free",
                "z+": "free",
            },
            basis_arrows=(),
            preview_dims=(4, 5, 3),
            profile=profile,
            probe_coord=(1, 2, 1),
        )
        panel_hits = [target for target in hits if target.kind == "projection_panel"]
        cell_hits = [target for target in hits if target.kind == "projection_cell"]
        glue_hits = [target for target in hits if target.kind == "glue_pick"]
        boundary_hits = [target for target in hits if target.kind == "boundary_pick"]
        self.assertEqual(sorted(target.value for target in panel_hits), ["xy", "xz", "yz"])
        self.assertGreater(len(cell_hits), 0)
        self.assertEqual(len(glue_hits), 1)
        self.assertEqual(len(boundary_hits), 6)

    def test_scene4d_returns_six_projection_panels_and_clickable_cells(self) -> None:
        surface = pygame.Surface((1100, 820))
        fonts = self._fonts()
        profile = self._profile_4d()
        boundaries = tuple(
            BoundaryRef(dimension=4, axis=axis, side=side)
            for axis in range(4)
            for side in ("-", "+")
        )
        hits = draw_scene_4d(
            surface,
            fonts,
            area=pygame.Rect(40, 80, 760, 420),
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[7],
            active_glue_ids={
                "x-": "glue_001",
                "x+": "free",
                "y-": "free",
                "y+": "free",
                "z-": "free",
                "z+": "free",
                "w-": "free",
                "w+": "glue_001",
            },
            basis_arrows=(),
            preview_dims=(3, 4, 5, 2),
            profile=profile,
            probe_coord=(1, 2, 3, 0),
        )
        panel_hits = [target for target in hits if target.kind == "projection_panel"]
        cell_hits = [target for target in hits if target.kind == "projection_cell"]
        self.assertEqual(
            sorted(target.value for target in panel_hits),
            sorted(["xy", "xz", "xw", "yz", "yw", "zw"]),
        )
        self.assertGreater(len(cell_hits), 0)
        self.assertIn((0, 0, 3, 0), {tuple(target.value) for target in cell_hits})

    def test_sandbox_cells_render_in_projection_panels(self) -> None:
        for params in (
            dict(
                dimension=3,
                surface_size=(960, 760),
                area=pygame.Rect(40, 80, 620, 360),
                preview_dims=(4, 5, 3),
                probe_coord=(0, 2, 1),
                sandbox_cells=((1, 2, 1), (2, 2, 1)),
            ),
            dict(
                dimension=4,
                surface_size=(1100, 820),
                area=pygame.Rect(40, 80, 760, 420),
                preview_dims=(3, 4, 5, 2),
                probe_coord=(0, 2, 3, 0),
                sandbox_cells=((1, 2, 3, 0), (2, 2, 3, 0)),
            ),
        ):
            with self.subTest(dimension=params["dimension"]):
                self._assert_sandbox_cells_render(**params)

    def test_sandbox_cells_remain_visible_when_hidden_slices_differ(self) -> None:
        for params in (
            dict(
                dimension=3,
                surface_size=(960, 760),
                area=pygame.Rect(40, 80, 620, 360),
                preview_dims=(4, 5, 4),
                probe_coord=(0, 2, 0),
                target_value=(1, 2, 0),
                extra_kwargs={"sandbox_cells": ((1, 2, 3), (2, 2, 3))},
            ),
            dict(
                dimension=4,
                surface_size=(1100, 820),
                area=pygame.Rect(40, 80, 760, 420),
                preview_dims=(3, 4, 5, 3),
                probe_coord=(0, 2, 0, 0),
                target_value=(1, 2, 0, 0),
                extra_kwargs={"sandbox_cells": ((1, 2, 4, 2), (2, 2, 4, 2))},
            ),
        ):
            with self.subTest(dimension=params["dimension"]):
                self._assert_projection_overlay_projects_hidden_slices(**params)

    def test_probe_trace_projects_across_hidden_slices_in_4d(self) -> None:
        self._assert_projection_overlay_projects_hidden_slices(
            dimension=4,
            surface_size=(1100, 820),
            area=pygame.Rect(40, 80, 760, 420),
            preview_dims=(3, 4, 5, 3),
            probe_coord=(0, 0, 0, 0),
            target_value=(1, 2, 0, 0),
            extra_kwargs={
                "active_tool": "inspect_boundary",
                "probe_path": ((1, 2, 4, 2), (2, 2, 4, 2)),
            },
        )

    def test_neighbor_markers_render_as_dots_without_link_lines_in_2d(self) -> None:
        surface = pygame.Surface((720, 520))
        control = pygame.Surface((720, 520))
        fonts = self._fonts()
        area = pygame.Rect(40, 80, 360, 280)
        boundaries = tuple(
            BoundaryRef(dimension=2, axis=axis, side=side)
            for axis in range(2)
            for side in ("-", "+")
        )
        common_kwargs = dict(
            area=area,
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[1],
            active_glue_ids={boundary.label: "free" for boundary in boundaries},
            basis_arrows=(),
            preview_dims=(5, 4),
            probe_coord=(0, 0),
        )
        draw_scene_2d(control, fonts, **common_kwargs)
        draw_scene_2d(
            surface,
            fonts,
            **common_kwargs,
            neighbor_markers=((1, 1), (3, 1)),
        )
        board, cell_size = scene2d._board_rect(area, (5, 4))
        marker_center = scene2d._cell_rect(board, cell_size, (1, 1)).center
        midpoint = scene2d._cell_rect(board, cell_size, (2, 1)).center
        self.assertNotEqual(surface.get_at(marker_center), control.get_at(marker_center))
        self.assertEqual(surface.get_at(midpoint), control.get_at(midpoint))

    def test_neighbor_markers_project_across_hidden_slices_in_3d_and_4d(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, marker_coord in (
            (3, (960, 760), pygame.Rect(40, 80, 620, 360), (4, 5, 4), (0, 2, 0), (1, 2, 3)),
            (4, (1100, 820), pygame.Rect(40, 80, 760, 420), (3, 4, 5, 3), (0, 2, 0, 0), (1, 2, 4, 2)),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                control.fill((0, 0, 0))
                rendered.fill((0, 0, 0))
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool="inspect_boundary",
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    neighbor_markers=(marker_coord,),
                )
                panels, _info_rect = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                marker_center = projection_scene._cell_rect(
                    board_rect,
                    cell_size,
                    (1, 2),
                ).center
                changed = False
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        point = (marker_center[0] + dx, marker_center[1] + dy)
                        if rendered.get_at(point) != control.get_at(point):
                            changed = True
                            break
                    if changed:
                        break
                self.assertTrue(
                    changed,
                )

    def test_nd_neighbor_markers_do_not_drop_early_cells_when_many_are_visible(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, marker_coords, expected_pairs in (
            (
                3,
                (960, 760),
                pygame.Rect(40, 80, 620, 360),
                (5, 5, 5),
                (2, 2, 2),
                (
                    (0, 2, 2),
                    (4, 2, 2),
                    (2, 0, 2),
                    (2, 4, 2),
                    (1, 2, 2),
                    (3, 2, 2),
                    (2, 1, 2),
                    (2, 3, 2),
                    (1, 1, 2),
                    (3, 1, 2),
                    (1, 3, 2),
                    (3, 3, 2),
                    (0, 1, 2),
                    (4, 3, 2),
                ),
                ((0, 2), (4, 2), (2, 0), (2, 4)),
            ),
            (
                4,
                (1100, 820),
                pygame.Rect(40, 80, 760, 420),
                (5, 5, 5, 5),
                (2, 2, 2, 2),
                (
                    (0, 2, 2, 2),
                    (4, 2, 2, 2),
                    (2, 0, 2, 2),
                    (2, 4, 2, 2),
                    (1, 2, 2, 2),
                    (3, 2, 2, 2),
                    (2, 1, 2, 2),
                    (2, 3, 2, 2),
                    (1, 1, 2, 2),
                    (3, 1, 2, 2),
                    (1, 3, 2, 2),
                    (3, 3, 2, 2),
                    (0, 1, 2, 2),
                    (4, 3, 2, 2),
                ),
                ((0, 2), (4, 2), (2, 0), (2, 4)),
            ),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool="piece_sandbox",
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    neighbor_markers=marker_coords,
                )
                panels, _ = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                for pair in expected_pairs:
                    point = projection_scene._cell_rect(board_rect, cell_size, pair).center
                    self.assertNotEqual(
                        rendered.get_at(point),
                        control.get_at(point),
                    )

    def test_sandbox_mode_without_neighbor_markers_does_not_paint_neighbor_cells_in_nd(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, sandbox_cells, empty_pair in (
            (3, (960, 760), pygame.Rect(40, 80, 620, 360), (4, 5, 4), (2, 2, 2), ((2, 2, 2), (3, 2, 2), (2, 3, 2), (2, 2, 3)), (1, 2)),
            (4, (1100, 820), pygame.Rect(40, 80, 760, 420), (4, 5, 5, 4), (2, 2, 2, 2), ((2, 2, 2, 2), (3, 2, 2, 2), (2, 3, 2, 2), (2, 2, 3, 2), (2, 2, 2, 3)), (1, 2)),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                control.fill((0, 0, 0))
                rendered.fill((0, 0, 0))
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool="piece_sandbox",
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    sandbox_cells=sandbox_cells,
                    neighbor_markers=(),
                )
                panels, _info_rect = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                target_rect = projection_scene._cell_rect(board_rect, cell_size, empty_pair)
                self.assertEqual(
                    rendered.get_at(target_rect.center),
                    control.get_at(target_rect.center),
                )

    def test_nd_sandbox_cells_render_as_boxes_not_center_dots(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, sandbox_cells in (
            (
                3,
                (960, 760),
                pygame.Rect(40, 80, 620, 360),
                (4, 5, 4),
                (2, 2, 2),
                ((2, 2, 2), (3, 2, 2)),
            ),
            (
                4,
                (1100, 820),
                pygame.Rect(40, 80, 760, 420),
                (4, 5, 5, 4),
                (2, 2, 2, 2),
                ((2, 2, 2, 2), (3, 2, 2, 2)),
            ),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool="piece_sandbox",
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    sandbox_cells=sandbox_cells,
                )
                panels, _ = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                target_rect = projection_scene._cell_rect(board_rect, cell_size, (3, 2))
                edge_point = (target_rect.x + 2, target_rect.centery)
                upper_edge_point = (target_rect.centerx, target_rect.y + 2)
                self.assertNotEqual(
                    rendered.get_at(edge_point),
                    control.get_at(edge_point),
                )
                self.assertNotEqual(
                    rendered.get_at(upper_edge_point),
                    control.get_at(upper_edge_point),
                )

    def test_wider_analysis_column_keeps_long_menu_labels_readable(self) -> None:
        menu_font = self._fonts().menu_font
        menu_w = 536
        row_width = menu_w - 28
        label_width = max(252, min(row_width - 132, int(menu_w * 0.74)))
        self.assertEqual(
            fit_text(menu_font, "Export Explorer Preview", label_width),
            "Export Explorer Preview",
        )
        self.assertEqual(
            fit_text(menu_font, "Build Experiment Pack", label_width),
            "Build Experiment Pack",
        )
        self.assertEqual(fit_text(menu_font, "Workspace Path", label_width), "Workspace Path")

    def test_arrow_overlay_glue_style_emphasizes_selection(self) -> None:
        normal = _glue_style("glue_001", None, None)
        highlighted = _glue_style("glue_001", None, "glue_001")
        selected = _glue_style("glue_001", "glue_001", None)
        self.assertEqual(normal[3], 2)
        self.assertEqual(highlighted[3], 4)
        self.assertEqual(selected[3], 6)
        self.assertTrue(selected[0])
        self.assertFalse(selected[1])


if __name__ == "__main__":
    unittest.main()
