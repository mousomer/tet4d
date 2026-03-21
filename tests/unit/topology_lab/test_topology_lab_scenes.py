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
