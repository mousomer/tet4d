from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest import mock

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

    def test_scene3d_routes_probe_glyphs_through_projection_circle_path(self) -> None:
        surface = pygame.Surface((960, 760))
        fonts = self._fonts()
        profile = self._profile_3d()
        boundaries = tuple(
            BoundaryRef(dimension=3, axis=axis, side=side)
            for axis in range(3)
            for side in ("-", "+")
        )
        with mock.patch.object(
            projection_scene, "_draw_selected_cell"
        ) as draw_selected_cell:
            draw_scene_3d(
                surface,
                fonts,
                area=pygame.Rect(40, 80, 620, 360),
                boundaries=boundaries,
                source_boundary=boundaries[0],
                target_boundary=boundaries[1],
                active_glue_ids={},
                basis_arrows=(),
                preview_dims=(4, 5, 3),
                profile=profile,
                active_tool="probe",
                probe_coord=(1, 2, 1),
            )
        self.assertEqual(draw_selected_cell.call_count, 3)
        self.assertTrue(
            all(
                call.kwargs["active_tool"] == "probe"
                for call in draw_selected_cell.call_args_list
            )
        )

    def test_scene4d_routes_probe_glyphs_through_projection_circle_path(self) -> None:
        surface = pygame.Surface((1100, 820))
        fonts = self._fonts()
        profile = self._profile_4d()
        boundaries = tuple(
            BoundaryRef(dimension=4, axis=axis, side=side)
            for axis in range(4)
            for side in ("-", "+")
        )
        with mock.patch.object(
            projection_scene, "_draw_selected_cell"
        ) as draw_selected_cell:
            draw_scene_4d(
                surface,
                fonts,
                area=pygame.Rect(40, 80, 760, 420),
                boundaries=boundaries,
                source_boundary=boundaries[0],
                target_boundary=boundaries[7],
                active_glue_ids={},
                basis_arrows=(),
                preview_dims=(3, 4, 5, 2),
                profile=profile,
                active_tool="probe",
                probe_coord=(1, 2, 3, 0),
            )
        self.assertEqual(draw_selected_cell.call_count, 6)
        self.assertTrue(
            all(
                call.kwargs["active_tool"] == "probe"
                for call in draw_selected_cell.call_args_list
            )
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
        self.assertEqual(fit_text(menu_font, "Path", label_width), "Path")

    def test_arrow_overlay_glue_style_emphasizes_selection(self) -> None:
        normal = _glue_style("glue_001", None, None)
        highlighted = _glue_style("glue_001", None, "glue_001")
        selected = _glue_style("glue_001", "glue_001", None)
        self.assertEqual(normal[3], 2)
        self.assertEqual(highlighted[3], 4)
        self.assertEqual(selected[3], 6)
        self.assertTrue(selected[0])
        self.assertFalse(selected[1])

    def test_editor_probe_draws_as_dot_not_box_in_projection_scene(self) -> None:
        surface = pygame.Surface((240, 240))
        board_rect = pygame.Rect(20, 20, 160, 160)
        expected_center = pygame.Rect(60, 60, 40, 40).center

        with (
            mock.patch.object(projection_scene.pygame.draw, "rect") as draw_rect,
            mock.patch.object(
                projection_scene, "draw_probe_center_glyph"
            ) as draw_probe_center_glyph,
        ):
            projection_scene._draw_selected_cell(
                surface,
                board_rect=board_rect,
                cell_size=40,
                axes=(0, 1),
                selected_coord=(1, 1, 0),
                active_tool="probe",
            )

        draw_rect.assert_not_called()
        draw_probe_center_glyph.assert_called_once_with(
            surface,
            center=expected_center,
            cell_size=40,
        )

    def test_editor_probe_draws_as_circle_in_2d_scene(self) -> None:
        surface = pygame.Surface((240, 240))
        board_rect = pygame.Rect(20, 20, 160, 160)
        expected_center = pygame.Rect(60, 60, 40, 40).center

        with (
            mock.patch.object(scene2d.pygame.draw, "rect") as draw_rect,
            mock.patch.object(scene2d, "draw_probe_center_glyph") as draw_probe_center_glyph,
        ):
            scene2d._draw_probe(
                surface,
                board=board_rect,
                cell_size=40,
                preview_dims=(4, 4),
                probe_coord=(1, 1),
            )

        draw_rect.assert_not_called()
        draw_probe_center_glyph.assert_called_once_with(
            surface,
            center=expected_center,
            cell_size=40,
        )

    def test_sandbox_focus_and_cells_keep_box_semantics_in_projection_scene(self) -> None:
        surface = pygame.Surface((240, 240))
        board_rect = pygame.Rect(20, 20, 160, 160)

        with (
            mock.patch.object(projection_scene.pygame.draw, "rect") as draw_rect,
            mock.patch.object(
                projection_scene.pygame.draw, "circle"
            ) as draw_circle,
        ):
            projection_scene._draw_selected_cell(
                surface,
                board_rect=board_rect,
                cell_size=40,
                axes=(0, 1),
                selected_coord=(1, 1, 0),
                active_tool="piece_sandbox",
            )
            projection_scene._draw_sandbox_cells(
                surface,
                board_rect=board_rect,
                cell_size=40,
                axes=(0, 1),
                dimension=3,
                selected_coord=(1, 1, 0),
                sandbox_cells=((1, 1, 0),),
                sandbox_valid=True,
                slab_radius=0,
            )

        self.assertGreaterEqual(draw_rect.call_count, 3)
        draw_circle.assert_not_called()

    def test_neighbor_markers_render_as_dots_in_projection_scene(self) -> None:
        surface = pygame.Surface((240, 240))
        board_rect = pygame.Rect(20, 20, 160, 160)
        expected_centers = [pygame.Rect(20, 60, 40, 40).center, pygame.Rect(100, 60, 40, 40).center]

        with (
            mock.patch.object(projection_scene.pygame.draw, "rect") as draw_rect,
            mock.patch.object(
                projection_scene, "draw_probe_neighbor_glyphs"
            ) as draw_probe_neighbor_glyphs,
        ):
            projection_scene._draw_neighbor_markers(
                surface,
                board_rect=board_rect,
                cell_size=40,
                axes=(0, 1),
                neighbor_markers=((0, 1, 0), (2, 1, 0)),
            )

        draw_rect.assert_not_called()
        draw_probe_neighbor_glyphs.assert_called_once_with(
            surface,
            centers=expected_centers,
            cell_size=40,
        )

    def test_probe_path_reuses_2d_glyph_helper_in_projection_scene(self) -> None:
        surface = pygame.Surface((240, 240))
        board_rect = pygame.Rect(20, 20, 160, 160)
        expected_centers = [
            pygame.Rect(20, 20, 40, 40).center,
            pygame.Rect(60, 20, 40, 40).center,
            pygame.Rect(60, 60, 40, 40).center,
        ]

        with mock.patch.object(
            projection_scene, "draw_probe_path_glyphs"
        ) as draw_probe_path_glyphs:
            projection_scene._draw_probe_path(
                surface,
                board_rect=board_rect,
                cell_size=40,
                axes=(0, 1),
                dimension=3,
                selected_coord=(1, 1, 0),
                probe_path=((0, 0, 0), (1, 0, 0), (1, 1, 0)),
                slab_radius=0,
            )

        draw_probe_path_glyphs.assert_called_once_with(
            surface,
            centers=expected_centers,
            cell_size=40,
        )

    def test_probe_trace_path_renders_as_line_without_intermediate_dots(self) -> None:
        surface = pygame.Surface((240, 240))
        centers = [(20, 20), (60, 20), (60, 60)]

        with (
            mock.patch.object(projection_scene.pygame.draw, "lines") as draw_lines,
            mock.patch.object(projection_scene.pygame.draw, "circle") as draw_circle,
        ):
            projection_scene.draw_probe_path_glyphs(
                surface,
                centers=centers,
                cell_size=40,
            )

        draw_lines.assert_called_once_with(
            surface,
            (88, 170, 214),
            False,
            centers,
            2,
        )
        draw_circle.assert_not_called()


if __name__ == "__main__":
    unittest.main()
