from __future__ import annotations

from types import SimpleNamespace
import unittest

import pygame

from tet4d.engine.topology_explorer import BoundaryRef
from tet4d.ui.pygame.topology_lab.scene3d import draw_scene as draw_scene_3d
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


if __name__ == '__main__':
    unittest.main()
