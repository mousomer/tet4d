from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pygame

from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.ui.pygame import (
    endgame_animation,
    front2d_frame,
    front3d_game,
    front3d_render,
    front4d_game,
    front4d_render,
)
from tet4d.ui.pygame.front2d_session import LoopContext2D
from tet4d.ui.pygame.render import gfx_game
from tet4d.ui.pygame.runtime_ui import loop_runner_nd


class TestEndgameAnimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.fonts_2d = gfx_game.init_fonts()
        cls.fonts_3d = front3d_render.init_fonts()
        cls.fonts_4d = front4d_game.init_fonts()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    @staticmethod
    def _surface_bytes(surface: pygame.Surface) -> bytes:
        return pygame.image.tobytes(surface, "RGBA")

    @staticmethod
    def _sample_snapshot() -> endgame_animation.EndgameSnapshot:
        return endgame_animation.create_snapshot(
            dimension=2,
            board_dims=(6, 8),
            render_dims=(6, 8, 1),
            locked_cells=(
                endgame_animation.SnapshotCell(
                    source_coord=(1, 6),
                    position=(1.0, 6.0, 0.0),
                    color_id=3,
                ),
                endgame_animation.SnapshotCell(
                    source_coord=(4, 5),
                    position=(4.0, 5.0, 0.0),
                    color_id=6,
                ),
            ),
            base_seed=1337,
            render_context=endgame_animation.EndgameRenderContext(mode_key="2d"),
        )

    def test_terminal_transition_creates_2d_endgame_snapshot(self) -> None:
        loop = LoopContext2D.create(GameConfig(width=6, height=8, speed_level=1))
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 6)] = 3
        loop.state.board.cells[(4, 5)] = 6
        loop.state.game_over = True

        with patch.object(front2d_frame, "play_sfx"):
            front2d_frame._update_feedback_and_animation(
                loop=loop,
                dt=16,
                clear_anim_duration_ms=320.0,
            )

        self.assertIsNotNone(loop.endgame_animation)
        assert loop.endgame_animation is not None
        snapshot = loop.endgame_animation.snapshot
        self.assertEqual(loop.terminal_phase, endgame_animation.TERMINAL_PHASE_GAME_OVER_ANIMATING)
        self.assertEqual(snapshot.board_dims, (6, 8))
        self.assertEqual(snapshot.render_dims, (6, 8, 1))
        self.assertEqual(snapshot.locked_cells[0].source_coord, (1, 6))
        self.assertEqual(snapshot.locked_cells[1].source_coord, (4, 5))
        self.assertEqual(snapshot.render_context.mode_key, "2d")

    def test_fragment_generation_is_deterministic_for_fixed_seed(self) -> None:
        snapshot = self._sample_snapshot()

        animation_a = endgame_animation.build_endgame_animation_state(snapshot)
        animation_b = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(animation_a.snapshot.rng_seed, animation_b.snapshot.rng_seed)
        self.assertEqual(animation_a.cell_fragments, animation_b.cell_fragments)
        self.assertEqual(animation_a.shell_fragments, animation_b.shell_fragments)

    def test_fragment_updates_match_expected_known_timestamp(self) -> None:
        fragment = endgame_animation.CellFragment(
            source_coord=(1, 2),
            base_geometry="cell",
            initial_position=(1.0, 2.0, 0.0),
            velocity=(4.0, 0.0, 0.0),
            acceleration=(0.0, 1.0, 0.0),
            angular_velocity_deg=(0.0, 0.0, 90.0),
            detach_start_ms=100.0,
            fade_start_ms=400.0,
            lifetime_ms=700.0,
            color_id=5,
            jitter_offset=(2.0, 0.0, 0.0),
        )

        position_pre, rotation_pre, alpha_pre = endgame_animation.transform_for_cell_fragment(
            fragment,
            elapsed_ms=50.0,
            drag_per_second=0.5,
        )
        self.assertEqual(position_pre, (2.0, 2.0, 0.0))
        self.assertEqual(rotation_pre, (0.0, 0.0, 0.0))
        self.assertEqual(alpha_pre, 1.0)

        position_post, rotation_post, alpha_post = endgame_animation.transform_for_cell_fragment(
            fragment,
            elapsed_ms=600.0,
            drag_per_second=0.5,
        )
        self.assertAlmostEqual(position_post[0], 2.6)
        self.assertAlmostEqual(position_post[1], 2.125)
        self.assertAlmostEqual(position_post[2], 0.0)
        self.assertAlmostEqual(rotation_post[2], 45.0)
        self.assertAlmostEqual(alpha_post, 1.0)

    def test_normal_gameplay_updates_stop_once_terminal_animation_takes_over(self) -> None:
        state = SimpleNamespace(
            config=SimpleNamespace(exploration_mode=False),
            game_over=False,
            step_gravity=Mock(),
        )
        loop = SimpleNamespace(
            terminal_phase=endgame_animation.TERMINAL_PHASE_GAME_OVER_ANIMATING,
            gravity_accumulator=64,
            bot=SimpleNamespace(tick_nd=Mock(), controls_descent=False),
            state=state,
        )

        loop_runner_nd._advance_simulation_step(
            loop=loop,
            dt=16,
            gravity_interval_ms=100,
        )

        self.assertEqual(loop.gravity_accumulator, 0)
        loop.bot.tick_nd.assert_not_called()
        state.step_gravity.assert_not_called()

    def test_endgame_animation_stays_animating_after_configured_duration(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(self._sample_snapshot())

        animation.step(animation.tuning.total_duration_ms)

        self.assertEqual(
            animation.phase,
            endgame_animation.TERMINAL_PHASE_GAME_OVER_ANIMATING,
        )

    def test_endgame_prompt_becomes_ready_before_animation_completion(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(self._sample_snapshot())

        animation.step(animation.tuning.crack_onset_duration_ms)

        self.assertEqual(
            animation.phase,
            endgame_animation.TERMINAL_PHASE_GAME_OVER_ANIMATING,
        )
        self.assertTrue(endgame_animation.endgame_prompt_ready(animation))

    def test_endgame_sfx_events_follow_shared_phase_thresholds(self) -> None:
        tuning = endgame_animation.load_endgame_animation_tuning()
        crack_events = endgame_animation.endgame_sfx_events_between(
            previous_elapsed_ms=0.0,
            current_elapsed_ms=tuning.crack_onset_duration_ms,
            tuning=tuning,
        )
        pop_events = endgame_animation.endgame_sfx_events_between(
            previous_elapsed_ms=tuning.crack_onset_duration_ms,
            current_elapsed_ms=tuning.crack_onset_duration_ms
            + (tuning.release_duration_ms * 0.5),
            tuning=tuning,
        )
        boom_events = endgame_animation.endgame_sfx_events_between(
            previous_elapsed_ms=tuning.crack_onset_duration_ms
            + (tuning.release_duration_ms * 0.5),
            current_elapsed_ms=tuning.crack_onset_duration_ms
            + tuning.release_duration_ms,
            tuning=tuning,
        )

        self.assertEqual(crack_events, ("endgame_crack",))
        self.assertEqual(pop_events, ("endgame_pop",))
        self.assertEqual(boom_events, ("endgame_boom",))

    def test_2d_renderer_uses_frozen_snapshot_not_mutated_live_board(self) -> None:
        cfg = GameConfig(width=8, height=10, speed_level=1)
        loop = LoopContext2D.create(cfg)
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 8)] = 1
        loop.state.board.cells[(2, 8)] = 2
        loop.state.game_over = True

        with patch.object(front2d_frame, "play_sfx"):
            front2d_frame._update_feedback_and_animation(
                loop=loop,
                dt=16,
                clear_anim_duration_ms=320.0,
            )
        assert loop.endgame_animation is not None

        surface_a = pygame.Surface((980, 780), pygame.SRCALPHA)
        gfx_game.draw_game_frame(
            surface_a,
            cfg,
            loop.state,
            self.fonts_2d,
            endgame_animation=loop.endgame_animation,
        )

        loop.state.board.cells.clear()
        loop.state.board.cells[(7, 0)] = 7
        loop.state.current_piece = None

        surface_b = pygame.Surface((980, 780), pygame.SRCALPHA)
        gfx_game.draw_game_frame(
            surface_b,
            cfg,
            loop.state,
            self.fonts_2d,
            endgame_animation=loop.endgame_animation,
        )

        self.assertEqual(self._surface_bytes(surface_a), self._surface_bytes(surface_b))

    def test_projected_3d_renderer_uses_frozen_snapshot_not_mutated_live_board(self) -> None:
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        loop = front3d_game.LoopContext3D.create(cfg)
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 8, 2)] = 4
        loop.state.board.cells[(3, 7, 3)] = 6
        loop.state.game_over = True
        loop.endgame_animation = endgame_animation.build_endgame_animation_state(
            front3d_game._capture_endgame_snapshot_3d(loop)
        )
        loop.terminal_phase = endgame_animation.TERMINAL_PHASE_GAME_OVER_ANIMATING

        surface_a = pygame.Surface((1180, 840), pygame.SRCALPHA)
        front3d_render.draw_game_frame(
            surface_a,
            loop.state,
            loop.camera,
            self.fonts_3d,
            grid_mode=loop.grid_mode,
            endgame_animation=loop.endgame_animation,
        )

        loop.state.board.cells.clear()
        loop.state.board.cells[(5, 0, 5)] = 7

        surface_b = pygame.Surface((1180, 840), pygame.SRCALPHA)
        front3d_render.draw_game_frame(
            surface_b,
            loop.state,
            loop.camera,
            self.fonts_3d,
            grid_mode=loop.grid_mode,
            endgame_animation=loop.endgame_animation,
        )

        self.assertEqual(self._surface_bytes(surface_a), self._surface_bytes(surface_b))

    def test_projected_4d_renderer_uses_frozen_snapshot_not_mutated_live_board(self) -> None:
        cfg = GameConfigND(dims=(5, 8, 5, 3), gravity_axis=1, speed_level=1)
        loop = front4d_game.LoopContext4D.create(cfg)
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 6, 2, 0)] = 2
        loop.state.board.cells[(3, 5, 1, 2)] = 5
        loop.state.game_over = True
        loop.endgame_animation = endgame_animation.build_endgame_animation_state(
            front4d_game._capture_endgame_snapshot_4d(loop)
        )
        loop.terminal_phase = endgame_animation.TERMINAL_PHASE_GAME_OVER_ANIMATING

        surface_a = pygame.Surface((1320, 880), pygame.SRCALPHA)
        front4d_render.draw_game_frame(
            surface_a,
            loop.state,
            loop.view,
            self.fonts_4d,
            grid_mode=loop.grid_mode,
            endgame_animation=loop.endgame_animation,
        )

        loop.state.board.cells.clear()
        loop.state.board.cells[(4, 0, 4, 1)] = 7

        surface_b = pygame.Surface((1320, 880), pygame.SRCALPHA)
        front4d_render.draw_game_frame(
            surface_b,
            loop.state,
            loop.view,
            self.fonts_4d,
            grid_mode=loop.grid_mode,
            endgame_animation=loop.endgame_animation,
        )

        self.assertEqual(self._surface_bytes(surface_a), self._surface_bytes(surface_b))

    def test_regression_scenarios_cover_sparse_dense_near_full_and_projected_3d(self) -> None:
        scenarios = {
            "sparse": {(1, 8): 1, (5, 6): 4},
            "dense": {(x, y): (x % 7) + 1 for x in range(8) for y in range(5, 10)},
            "near_full": {(x, y): ((x + y) % 7) + 1 for x in range(8) for y in range(1, 10)},
        }

        for label, cells in scenarios.items():
            with self.subTest(label=label):
                loop = LoopContext2D.create(GameConfig(width=8, height=10, speed_level=1))
                loop.state.board.cells.clear()
                loop.state.board.cells.update(cells)
                loop.state.game_over = True
                with patch.object(front2d_frame, "play_sfx"):
                    front2d_frame._update_feedback_and_animation(
                        loop=loop,
                        dt=16,
                        clear_anim_duration_ms=320.0,
                    )
                assert loop.endgame_animation is not None
                self.assertEqual(len(loop.endgame_animation.cell_fragments), len(cells))
                self.assertGreater(len(loop.endgame_animation.shell_fragments), 0)

        cfg_3d = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        loop_3d = front3d_game.LoopContext3D.create(cfg_3d)
        loop_3d.state.board.cells.clear()
        loop_3d.state.board.cells.update(
            {
                (1, 8, 2): 3,
                (2, 7, 3): 5,
                (4, 6, 1): 7,
            }
        )
        loop_3d.state.game_over = True
        loop_3d.endgame_animation = endgame_animation.build_endgame_animation_state(
            front3d_game._capture_endgame_snapshot_3d(loop_3d)
        )
        self.assertEqual(len(loop_3d.endgame_animation.cell_fragments), 3)
        self.assertGreater(len(loop_3d.endgame_animation.shell_fragments), 0)


if __name__ == "__main__":
    unittest.main()
