from __future__ import annotations

from types import SimpleNamespace
import unittest

import pygame

from tet4d.engine.topology_explorer import BoundaryRef
from tet4d.ui.pygame.front3d_render import Camera3D
from tet4d.ui.pygame.front4d_render import LayerView3D
from tet4d.ui.pygame.topology_lab.arrow_overlay import _glue_style
from tet4d.ui.pygame.topology_lab.scene3d import _project_coord
from tet4d.ui.pygame.topology_lab.scene3d import draw_scene as draw_scene_3d
from tet4d.ui.pygame.topology_lab.scene4d import _path_preview_labels
from tet4d.ui.pygame.topology_lab.scene4d import draw_scene as draw_scene_4d


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

    def _basis_arrow(self, source: str, target: str, glue_id: str = 'glue_001'):
        return {
            'id': glue_id,
            'crossing': f'{source} -> {target}',
            'source_boundary': source,
            'target_boundary': target,
            'basis_pairs': (
                {'from': '+x', 'to': '+x'},
                {'from': '+y', 'to': '+y'},
            ),
        }

    def test_scene3d_returns_face_and_glue_targets(self) -> None:
        surface = pygame.Surface((900, 700))
        fonts = self._fonts()
        boundaries = tuple(
            BoundaryRef(dimension=3, axis=axis, side=side)
            for axis in range(3)
            for side in ('-', '+')
        )
        hits = draw_scene_3d(
            surface,
            fonts,
            area=pygame.Rect(40, 80, 560, 320),
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[1],
            active_glue_ids={boundary.label: 'free' for boundary in boundaries},
            basis_arrows=[self._basis_arrow('x-', 'x+')],
            preview_dims=(8, 9, 7),
            selected_glue_id='glue_001',
            highlighted_glue_id='glue_001',
        )
        boundary_hits = [target for target in hits if target.kind == 'boundary_pick']
        glue_hits = [target for target in hits if target.kind == 'glue_pick']
        self.assertEqual(len(boundary_hits), 6)
        self.assertEqual(len(glue_hits), 1)

    def test_scene4d_returns_hyperface_and_glue_targets(self) -> None:
        surface = pygame.Surface((980, 760))
        fonts = self._fonts()
        boundaries = tuple(
            BoundaryRef(dimension=4, axis=axis, side=side)
            for axis in range(4)
            for side in ('-', '+')
        )
        hits = draw_scene_4d(
            surface,
            fonts,
            area=pygame.Rect(40, 80, 620, 420),
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[7],
            active_glue_ids={boundary.label: 'free' for boundary in boundaries},
            basis_arrows=[self._basis_arrow('x-', 'w+')],
            preview_dims=(8, 9, 7, 6),
            selected_glue_id='glue_001',
            highlighted_glue_id='glue_001',
        )
        boundary_hits = [target for target in hits if target.kind == 'boundary_pick']
        glue_hits = [target for target in hits if target.kind == 'glue_pick']
        self.assertEqual(len(boundary_hits), 8)
        self.assertEqual(len(glue_hits), 1)

    def test_scene4d_accepts_view_state(self) -> None:
        surface = pygame.Surface((980, 760))
        fonts = self._fonts()
        boundaries = tuple(
            BoundaryRef(dimension=4, axis=axis, side=side)
            for axis in range(4)
            for side in ('-', '+')
        )
        view = LayerView3D()
        view.yaw_deg = 22.0
        view.pitch_deg = -18.0
        view.xw_deg = 14.0
        view.zw_deg = -12.0
        hits = draw_scene_4d(
            surface,
            fonts,
            area=pygame.Rect(40, 80, 620, 420),
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[7],
            active_glue_ids={boundary.label: 'free' for boundary in boundaries},
            basis_arrows=[self._basis_arrow('x-', 'w+')],
            preview_dims=(8, 9, 7, 6),
            selected_glue_id='glue_001',
            highlighted_glue_id='glue_001',
            view=view,
        )
        self.assertTrue(any(target.kind == 'boundary_pick' for target in hits))

    def test_scene3d_project_coord_uses_depth_projection(self) -> None:
        front = pygame.Rect(100, 120, 200, 160)
        dims = (8, 9, 7)
        near = _project_coord(front, (2, 3, 0), dims)
        far = _project_coord(front, (2, 3, 6), dims)
        self.assertNotEqual(near, far)
        self.assertGreater(far[0], near[0])
        self.assertLess(far[1], near[1])

    def test_scene3d_project_coord_changes_with_camera(self) -> None:
        front = pygame.Rect(100, 120, 200, 160)
        dims = (8, 9, 7)
        camera = Camera3D()
        camera.reset()
        camera.yaw_deg = 48.0
        camera.pitch_deg = -18.0
        camera.zoom = 54.0
        baseline = _project_coord(front, (2, 3, 4), dims)
        moved = _project_coord(front, (2, 3, 4), dims, camera=camera)
        self.assertNotEqual(baseline, moved)

    def test_scene4d_path_preview_labels_limit_to_last_four(self) -> None:
        labels = _path_preview_labels(
            [(0, 0, 0, 0), (1, 0, 0, 0), (2, 0, 0, 0), (3, 0, 0, 0), (4, 0, 0, 0)]
        )
        self.assertEqual(
            labels,
            ['[1, 0, 0, 0]', '[2, 0, 0, 0]', '[3, 0, 0, 0]', '[4, 0, 0, 0]'],
        )

    def test_arrow_overlay_glue_style_emphasizes_selection(self) -> None:
        normal = _glue_style('glue_001', None, None)
        highlighted = _glue_style('glue_001', None, 'glue_001')
        selected = _glue_style('glue_001', 'glue_001', None)
        self.assertEqual(normal[3], 2)
        self.assertEqual(highlighted[3], 4)
        self.assertEqual(selected[3], 6)
        self.assertTrue(selected[0])
        self.assertFalse(selected[1])


if __name__ == '__main__':
    unittest.main()
