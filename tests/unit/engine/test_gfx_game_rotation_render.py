from __future__ import annotations

import math
import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for 2D render tests")

from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.rotation_anim import _RotationTween
from tet4d.ui.pygame import front2d_frame, front2d_loop
from tet4d.ui.pygame.front2d_session import LoopContext2D
from tet4d.ui.pygame.keybindings import KEYS_2D
from tet4d.ui.pygame.render import gfx_game
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings


class TestGfxGameRotationRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.fonts = gfx_game.init_fonts()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    @staticmethod
    def _rotation_key() -> int:
        keys = KEYS_2D["rotate_xy_pos"]
        if not keys:
            raise AssertionError("missing 2D rotation key")
        return int(keys[0])

    @staticmethod
    def _create_loop(mode_name: str) -> LoopContext2D:
        cfg = GameConfig(width=10, height=20, gravity_axis=1, speed_level=1)
        loop = LoopContext2D.create(
            cfg,
            rotation_animation_mode=mode_name,
            rotation_animation_duration_ms=160.0,
            translation_animation_duration_ms=120.0,
        )
        loop.state.board.cells.clear()
        loop.state.next_bag = [PieceShape2D("next", [(0, 0)], color_id=7)]
        loop.state.current_piece = ActivePiece2D(
            shape=PieceShape2D("el", [(0, 0), (1, 0), (0, 1)], color_id=3),
            pos=(4, 6),
            rotation=0,
        )
        loop.rotation_anim.reset()
        return loop

    @classmethod
    def _render_mid_rotation_frame(
        cls,
        mode_name: str,
    ) -> tuple[bytes, list[pygame.Rect], list[dict[str, object]]]:
        screen = pygame.Surface((1024, 840), pygame.SRCALPHA)
        loop = cls._create_loop(mode_name)
        piece = loop.state.current_piece
        if piece is None:
            raise AssertionError("expected active piece")
        piece_color = gfx_game.color_for_cell(piece.shape.color_id)
        board_offset, _panel_offset = gfx_game.compute_game_layout(screen, loop.cfg)
        board_rect = pygame.Rect(
            board_offset[0],
            board_offset[1],
            loop.cfg.width * gfx_game.CELL_SIZE,
            loop.cfg.height * gfx_game.CELL_SIZE,
        )

        with patch.object(front2d_frame.pygame.display, "flip"):
            front2d_frame._run_game_frame_2d(
                screen=screen,
                fonts=cls.fonts,
                loop=loop,
                dt=0,
                clear_anim_duration_ms=320.0,
            )

        result = loop.keydown_handler(
            pygame.event.Event(pygame.KEYDOWN, {"key": cls._rotation_key()})
        )
        if result != "continue":
            raise AssertionError(f"unexpected keydown result: {result}")

        with patch.object(front2d_frame.pygame.display, "flip"):
            front2d_frame._run_game_frame_2d(
                screen=screen,
                fonts=cls.fonts,
                loop=loop,
                dt=0,
                clear_anim_duration_ms=320.0,
            )

        screen_piece_rects: list[pygame.Rect] = []
        rotozoom_calls: list[dict[str, object]] = []
        original_rect = gfx_game.pygame.draw.rect
        original_rotozoom = gfx_game.pygame.transform.rotozoom

        def record_rect(surface, color, rect, width=0, *args, **kwargs):
            if (
                surface is screen
                and tuple(color)[:3] == piece_color
                and width == 0
                and isinstance(rect, pygame.Rect)
                and rect.width == gfx_game.CELL_SIZE - 2
                and rect.height == gfx_game.CELL_SIZE - 2
                and board_rect.contains(rect)
            ):
                screen_piece_rects.append(rect.copy())
            return original_rect(surface, color, rect, width, *args, **kwargs)

        def record_rotozoom(surface, angle, scale):
            rotozoom_calls.append(
                {
                    "surface": surface,
                    "angle": float(angle),
                    "scale": float(scale),
                    "size": surface.get_size(),
                    "flags": int(surface.get_flags()),
                    "rgba": pygame.image.tobytes(surface, "RGBA"),
                }
            )
            return original_rotozoom(surface, angle, scale)

        with (
            patch.object(gfx_game.pygame.draw, "rect", side_effect=record_rect),
            patch.object(
                gfx_game.pygame.transform,
                "rotozoom",
                side_effect=record_rotozoom,
            ),
            patch.object(front2d_frame.pygame.display, "flip"),
        ):
            front2d_frame._run_game_frame_2d(
                screen=screen,
                fonts=cls.fonts,
                loop=loop,
                dt=80,
                clear_anim_duration_ms=320.0,
            )

        return pygame.image.tobytes(screen, "RGBA"), screen_piece_rects, rotozoom_calls

    def test_rigid_midframe_uses_rotated_piece_surface_path(self) -> None:
        frame_bytes, screen_piece_rects, rotozoom_calls = self._render_mid_rotation_frame(
            "rigid_piece_rotation"
        )
        self.assertTrue(frame_bytes)
        self.assertFalse(screen_piece_rects)
        self.assertEqual(len(rotozoom_calls), 1)
        call = rotozoom_calls[0]
        self.assertEqual(call["scale"], 1.0)
        self.assertGreater(abs(float(call["angle"])), 1.0)
        self.assertLess(abs(float(call["angle"])), 89.0)
        width, height = call["size"]
        self.assertGreater(width, gfx_game.CELL_SIZE)
        self.assertGreater(height, gfx_game.CELL_SIZE)
        self.assertTrue(int(call["flags"]) & int(pygame.SRCALPHA))
        alphas = call["rgba"][3::4]
        self.assertTrue(any(alpha == 0 for alpha in alphas))
        self.assertTrue(any(alpha > 0 for alpha in alphas))

    def test_rigid_rotozoom_angle_is_positive_for_forward_rotation(self) -> None:
        """rotozoom(+deg) = CCW on screen, matching rotate_xy_pos (steps_cw=1 = CCW-screen)."""
        _, _, rotozoom_calls = self._render_mid_rotation_frame("rigid_piece_rotation")
        self.assertEqual(len(rotozoom_calls), 1)
        angle = float(rotozoom_calls[0]["angle"])
        self.assertGreater(angle, 0.0, "forward rotation must use a positive rotozoom angle (CCW-screen)")

    def test_rigid_cell_positions_match_rotozoom_angle(self) -> None:
        """_interpolated_rel_rigid_rotation and interpolated_rotation_deg agree."""
        # Build a minimal tween matching the el-piece scenario: 3 blocks, pivot (0.5, 0.5).
        start_rel: tuple[tuple[float, float], ...] = (
            (0.0, 0.0), (1.0, 0.0), (0.0, 1.0)
        )
        end_rel: tuple[tuple[float, float], ...] = (
            (0.0, 1.0), (0.0, 0.0), (1.0, 1.0)
        )
        pivot: tuple[float, float] = (0.5, 0.5)
        tween = _RotationTween(
            start_rel=start_rel,
            end_rel=end_rel,
            start_pos=(0.0, 0.0),
            end_pos=(0.0, 0.0),
            duration_ms=160.0,
            elapsed_ms=80.0,      # half-way
            rotation_plane=(0, 1),
            rotation_steps=1,
            rigid_rotation=True,
            rotation_pivot=pivot,
        )
        # The angle the rotozoom path uses.
        angle_deg = tween.interpolated_rotation_deg()
        # The intermediate cell positions from the rigid fallback path.
        cells = tween.interpolated_rel()
        # Recompute the expected positions from angle_deg using the same convention.
        # rotozoom(+deg) = CCW-screen; standard math CCW by -deg in y-up = CCW-screen.
        angle_rad = -math.radians(angle_deg)
        cos_t = math.cos(angle_rad)
        sin_t = math.sin(angle_rad)
        expected = []
        for bx, by in start_rel:
            rel_a = bx - pivot[0]
            rel_b = by - pivot[1]
            expected.append((
                rel_a * cos_t - rel_b * sin_t + pivot[0],
                rel_a * sin_t + rel_b * cos_t + pivot[1],
            ))
        for (cx, cy), (ex, ey) in zip(cells, expected):
            self.assertAlmostEqual(cx, ex, places=10)
            self.assertAlmostEqual(cy, ey, places=10)

    def test_cellwise_midframe_uses_upright_per_cell_path(self) -> None:
        frame_bytes, screen_piece_rects, rotozoom_calls = self._render_mid_rotation_frame(
            "cellwise_sliding"
        )
        self.assertTrue(frame_bytes)
        self.assertTrue(screen_piece_rects)
        self.assertEqual(len(screen_piece_rects), 3)
        self.assertFalse(rotozoom_calls)

    def test_midframe_rigid_and_cellwise_frames_differ(self) -> None:
        rigid_frame, _rigid_rects, _rigid_rotozoom = self._render_mid_rotation_frame(
            "rigid_piece_rotation"
        )
        cellwise_frame, _cellwise_rects, _cellwise_rotozoom = (
            self._render_mid_rotation_frame("cellwise_sliding")
        )
        self.assertNotEqual(rigid_frame, cellwise_frame)

    def test_saved_rotation_mode_reaches_live_2d_render_loop(self) -> None:
        screen = pygame.Surface((640, 480), pygame.SRCALPHA)
        display_settings = DisplaySettings(fullscreen=False, windowed_size=(640, 480))
        cfg = GameConfig(width=10, height=20, gravity_axis=1, speed_level=1)
        observed_modes: list[str] = []

        def capture_frame(*, loop, **_kwargs):
            observed_modes.append(loop.rotation_anim.rotation_animation_mode)
            raise StopIteration

        with (
            patch.object(
                front2d_loop.menu_settings_state,
                "mode_rotation_animation_mode",
                return_value="cellwise_sliding",
            ),
            patch.object(
                front2d_frame,
                "_handle_loop_event_cycle",
                return_value=(screen, display_settings, None, False),
            ),
            patch.object(front2d_frame, "_run_game_frame_2d", side_effect=capture_frame),
            patch.object(front2d_frame, "_configure_game_loop"),
            patch.object(
                front2d_loop,
                "_load_animation_settings_for_mode",
                return_value=(160.0, 120.0),
            ),
            patch.object(
                front2d_loop,
                "_load_speedup_settings_for_mode",
                return_value=(0, 10),
            ),
            patch.object(
                front2d_loop,
                "_load_overlay_transparency_for_runtime_2d",
                return_value=0.25,
            ),
            patch.object(
                front2d_loop.pygame.time,
                "Clock",
                return_value=SimpleNamespace(tick=lambda _fps: 0),
            ),
        ):
            with self.assertRaises(StopIteration):
                front2d_loop.run_game_loop(
                    screen=screen,
                    cfg=cfg,
                    fonts=self.fonts,
                    display_settings=display_settings,
                )

        self.assertEqual(observed_modes, ["cellwise_sliding"])


if __name__ == "__main__":
    unittest.main()
