from __future__ import annotations

from dataclasses import replace
import inspect
from pathlib import Path
from types import SimpleNamespace
import shutil
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import pygame

from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_INVERT, EDGE_WRAP
from tet4d.engine.runtime import menu_settings_state
from tet4d.engine.runtime.project_config import state_dir_path
from tet4d.ui.pygame import (
    endgame_animation,
    front2d_frame,
    front3d_game,
    front3d_render,
    front4d_game,
    front4d_render,
)
from tet4d.ui.pygame.front2d_session import LoopContext2D
from tet4d.ui.pygame.locked_cell_explosion import defaults_store as explosion_defaults_store
from tet4d.ui.pygame.locked_cell_explosion import (
    ExplosionRenderTrailSegment,
    build_standalone_explosion_surface_state,
)
from tet4d.ui.pygame.render import gfx_game
from tet4d.ui.pygame.runtime_ui import loop_runner_nd


def _new_workspace_temp_dir(prefix: str) -> Path:
    root = state_dir_path() / "pytest_temp"
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / f"{prefix}_{uuid4().hex}"
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


class _TempMenuSettingsRoot:
    def __init__(self) -> None:
        self.root = _new_workspace_temp_dir("endgame_settings")
        self.state_dir = self.root / "state"
        self.patches = [
            patch.object(menu_settings_state, "STATE_DIR", self.state_dir),
            patch.object(
                menu_settings_state, "STATE_FILE", self.state_dir / "menu_settings.json"
            ),
        ]

    def start(self) -> None:
        for active in self.patches:
            active.start()

    def stop(self) -> None:
        for active in reversed(self.patches):
            active.stop()
        shutil.rmtree(self.root, ignore_errors=True)


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

    def _temp_settings_root(self) -> _TempMenuSettingsRoot:
        root = _TempMenuSettingsRoot()
        root.start()
        self.addCleanup(root.stop)
        return root

    @staticmethod
    def _sample_snapshot(
        *,
        preset_id: str = "default_orbit",
        boundary_response: str = "escape",
        particle_collisions: str = "off",
    ) -> endgame_animation.EndgameSnapshot:
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
            preset_id=preset_id,
            boundary_response=boundary_response,
            particle_collisions=particle_collisions,
        )

    @staticmethod
    def _sample_snapshot_4d(
        *,
        preset_id: str = "wrap_all",
        boundary_response: str = "escape",
        particle_collisions: str = "off",
        relic_speed_scale: float = 1.0,
    ) -> endgame_animation.EndgameSnapshot:
        return endgame_animation.create_snapshot(
            dimension=4,
            board_dims=(5, 8, 5, 4),
            render_dims=(5, 8, 5),
            locked_cells=(
                endgame_animation.SnapshotCell(
                    source_coord=(1, 6, 2, 0),
                    position=(1.0, 6.0, 2.0, 0.0),
                    color_id=2,
                ),
                endgame_animation.SnapshotCell(
                    source_coord=(3, 5, 1, 3),
                    position=(3.0, 5.0, 1.0, 3.0),
                    color_id=5,
                ),
            ),
            base_seed=2026,
            render_context=endgame_animation.EndgameRenderContext(
                mode_key="4d",
                layer_axis_label="w",
                layer_count=4,
                basis_axis_map=((0, 1), (1, 1), (2, 1), (3, 1)),
                layer_axis=3,
                layer_sign=1,
            ),
            preset_id=preset_id,
            boundary_response=boundary_response,
            particle_collisions=particle_collisions,
            relic_speed_scale=relic_speed_scale,
        )

    @staticmethod
    def _locked_cells_for_dims(
        dims: tuple[int, ...],
        count: int,
    ) -> tuple[endgame_animation.SnapshotCell, ...]:
        cells: list[endgame_animation.SnapshotCell] = []
        for index in range(count):
            remainder = index
            coord: list[int] = []
            for size in dims:
                coord.append(remainder % int(size))
                remainder //= int(size)
            cells.append(
                endgame_animation.SnapshotCell(
                    source_coord=tuple(coord),
                    position=tuple(float(axis) for axis in coord),
                    color_id=(index % 7) + 1,
                )
            )
        return tuple(cells)

    def _artifact_snapshot(
        self,
        *,
        dimension: int,
        locked_count: int,
        live_fraction: float = 0.12,
        reversed_cells: bool = False,
    ) -> endgame_animation.EndgameSnapshot:
        dims_by_dimension = {
            2: (20, 20),
            3: (10, 10, 10),
            4: (8, 8, 8, 4),
        }
        dims = dims_by_dimension[dimension]
        locked_cells = self._locked_cells_for_dims(dims, locked_count)
        if reversed_cells:
            locked_cells = tuple(reversed(locked_cells))
        return endgame_animation.create_snapshot(
            dimension=dimension,
            board_dims=dims,
            render_dims=(dims[0], dims[1], dims[2] if dimension >= 3 else 1),
            locked_cells=locked_cells,
            base_seed=2026,
            render_context=endgame_animation.EndgameRenderContext(
                mode_key=f"{dimension}d",
                layer_count=dims[3] if dimension == 4 else 1,
                basis_axis_map=((0, 1), (1, 1), (2, 1), (3, 1))
                if dimension == 4
                else (),
            ),
            endgame_live_cell_fraction=live_fraction,
        )

    def test_terminal_transition_creates_2d_endgame_snapshot(self) -> None:
        self._temp_settings_root()
        ok, msg = explosion_defaults_store.save_mode_explosion_defaults(
            "2d",
            explosion_defaults_store.ExplosionDefaults(
                boundary_response="bounce",
                particle_collisions="on",
            ),
        )
        self.assertTrue(ok, msg)
        loop = LoopContext2D.create(GameConfig(width=6, height=8, speed_level=1))
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 6)] = 3
        loop.state.board.cells[(4, 5)] = 6
        loop.state.game_over = True

        with (
            patch.object(front2d_frame, "play_sfx"),
            patch.object(
                front2d_frame,
                "mode_endgame_settings",
                return_value=("wrap_all", "bounce", "on", 140, 80),
            ),
        ):
            front2d_frame._update_feedback_and_animation(
                loop=loop,
                dt=16,
                clear_anim_duration_ms=320.0,
            )

        self.assertIsNotNone(loop.endgame_animation)
        assert loop.endgame_animation is not None
        snapshot = loop.endgame_animation.snapshot
        self.assertEqual(
            loop.terminal_phase,
            endgame_animation.TERMINAL_PHASE_ENDGAME_SHATTER,
        )
        self.assertEqual(snapshot.board_dims, (6, 8))
        self.assertEqual(snapshot.render_dims, (6, 8, 1))
        self.assertEqual(snapshot.locked_cells[0].source_coord, (1, 6))
        self.assertEqual(snapshot.locked_cells[1].source_coord, (4, 5))
        self.assertEqual(snapshot.render_context.mode_key, "2d")
        self.assertEqual(snapshot.preset_id, "wrap_all")
        self.assertEqual(snapshot.boundary_response, "bounce")
        self.assertEqual(snapshot.particle_collisions, "on")
        self.assertAlmostEqual(snapshot.relic_speed_scale, 1.4)
        self.assertAlmostEqual(snapshot.shatter_speed_scale, 0.8)
        self.assertEqual(len(snapshot.persistent_live_cells), 1)

    def test_saved_explosion_defaults_feed_endgame_snapshot_and_controller(self) -> None:
        self._temp_settings_root()
        saved_defaults = explosion_defaults_store.ExplosionDefaults(
            boundary_response="bounce",
            particle_collisions="on",
            mass_mode="random",
            base_mass=1.6,
            random_mass_min=0.8,
            random_mass_max=2.4,
            collision_elasticity=0.3,
            diagnostics_mode="summary",
            grid_mode="edge",
            shadow_mode="all_boundaries",
            trace_enabled=True,
            trace_retention_ms=1800.0,
            speed_preset="fast",
            w_movement_animation_style="box_size",
            endgame_live_cell_fraction=0.45,
            sound_enabled=False,
            seed=8080,
        )
        ok, msg = explosion_defaults_store.save_mode_explosion_defaults(
            "2d",
            saved_defaults,
        )
        self.assertTrue(ok, msg)
        persisted = menu_settings_state.load_app_settings_payload()
        persisted_defaults = persisted["explosion_defaults"]["2d"]
        self.assertEqual(persisted_defaults["boundary_response"], "bounce")
        self.assertEqual(persisted_defaults["particle_collisions"], "on")
        self.assertEqual(persisted_defaults["mass_mode"], "random")
        self.assertEqual(persisted_defaults["grid_mode"], "edge")
        self.assertEqual(persisted_defaults["shadow_mode"], "all_boundaries")
        self.assertTrue(persisted_defaults["trace_enabled"])
        self.assertAlmostEqual(persisted_defaults["trace_retention_ms"], 1800.0)
        self.assertEqual(persisted_defaults["w_movement_animation_style"], "box_size")

        reloaded_defaults = explosion_defaults_store.mode_explosion_defaults("2d")
        self.assertEqual(reloaded_defaults, saved_defaults)
        simulator_state = build_standalone_explosion_surface_state(dimension=2)
        self.assertEqual(simulator_state.boundary_response, "bounce")
        self.assertEqual(simulator_state.particle_collisions, "on")
        self.assertEqual(simulator_state.mass_mode, "random")
        self.assertEqual(simulator_state.grid_mode.value, "edge")
        self.assertEqual(simulator_state.shadow_mode.value, "all_boundaries")
        self.assertTrue(simulator_state.trace_enabled)
        self.assertAlmostEqual(simulator_state.trace_retention_ms, 1800.0)
        loop = LoopContext2D.create(GameConfig(width=6, height=8, speed_level=1))
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 6)] = 3
        loop.state.board.cells[(4, 5)] = 6

        with patch.object(
            front2d_frame,
            "mode_endgame_settings",
            return_value=("wrap_all", "escape", "off", 100, 100),
        ):
            snapshot = front2d_frame._capture_endgame_snapshot_2d(loop)

        self.assertEqual(snapshot.boundary_response, "bounce")
        self.assertEqual(snapshot.particle_collisions, "on")
        self.assertEqual(snapshot.mass_mode, "random")
        self.assertAlmostEqual(snapshot.base_mass, 1.6)
        self.assertAlmostEqual(snapshot.random_mass_min, 0.8)
        self.assertAlmostEqual(snapshot.random_mass_max, 2.4)
        self.assertAlmostEqual(snapshot.collision_elasticity, 0.3)
        self.assertEqual(snapshot.diagnostics_mode, "summary")
        self.assertEqual(snapshot.grid_mode, "edge")
        self.assertEqual(snapshot.shadow_mode, "all_boundaries")
        self.assertTrue(snapshot.trace_enabled)
        self.assertAlmostEqual(snapshot.trace_retention_ms, 1800.0)
        self.assertEqual(snapshot.w_movement_animation_style, "box_size")
        self.assertEqual(snapshot.speed_preset, "fast")
        self.assertAlmostEqual(snapshot.endgame_live_cell_fraction, 0.45)
        self.assertFalse(snapshot.sound_enabled)

        animation = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(animation.explosion_controller.config.boundary_response, "bounce")
        self.assertEqual(animation.explosion_controller.config.particle_collisions, "on")
        self.assertEqual(animation.explosion_controller.config.mass_mode, "random")
        self.assertAlmostEqual(animation.explosion_controller.config.base_mass, 1.6)
        self.assertAlmostEqual(
            animation.explosion_controller.config.random_mass_min, 0.8
        )
        self.assertAlmostEqual(
            animation.explosion_controller.config.random_mass_max, 2.4
        )
        self.assertAlmostEqual(
            animation.explosion_controller.config.collision_elasticity, 0.3
        )
        self.assertEqual(animation.explosion_controller.config.diagnostics_mode, "summary")
        self.assertAlmostEqual(
            animation.explosion_controller.config.trace_retention_ms, 1800.0
        )
        self.assertEqual(animation.explosion_controller.config.speed_preset, "fast")
        self.assertFalse(animation.explosion_controller.config.sound_enabled)

    def test_topology_mode_reaches_endgame_runtime_topology_input(self) -> None:
        cfg = GameConfigND(
            dims=(6, 10, 6),
            gravity_axis=1,
            topology_mode="wrap_all",
            speed_level=1,
        )
        loop = front3d_game.LoopContext3D.create(cfg)
        loop.state.board.cells.clear()
        loop.state.board.cells.update(
            {
                (1, 8, 2): 3,
                (2, 7, 3): 5,
                (4, 6, 1): 7,
            }
        )

        with patch.object(
            front3d_game,
            "mode_endgame_settings",
            return_value=("default_orbit", "escape", "off", 100, 100),
        ):
            snapshot = front3d_game._capture_endgame_snapshot_3d(loop)

        self.assertEqual(
            snapshot.topology.topology_edge_rules,
            front3d_game._endgame_topology_edge_rules_3d(cfg),
        )
        self.assertEqual(snapshot.topology.topology_edge_rules[1], (EDGE_WRAP, EDGE_WRAP))

    def test_bounded_wrap_and_invert_topology_change_runtime_adapter(self) -> None:
        def _animation_for_mode(mode: str):
            snapshot = endgame_animation.create_snapshot(
                dimension=3,
                board_dims=(6, 10, 6),
                render_dims=(6, 10, 6),
                locked_cells=self._locked_cells_for_dims((6, 10, 6), 80),
                base_seed=2026,
                render_context=endgame_animation.EndgameRenderContext(mode_key="3d"),
                topology_edge_rules=front3d_game._endgame_topology_edge_rules_3d(
                    GameConfigND(
                        dims=(6, 10, 6),
                        gravity_axis=1,
                        topology_mode=mode,
                    )
                ),
            )
            return endgame_animation.build_endgame_animation_state(snapshot)

        bounded = _animation_for_mode("bounded")
        wrapped = _animation_for_mode("wrap_all")
        inverted = _animation_for_mode("invert_all")

        self.assertEqual(
            len(bounded.explosion_controller.topology.seams_by_boundary),
            0,
        )
        self.assertGreater(
            len(wrapped.explosion_controller.topology.seams_by_boundary),
            0,
        )
        self.assertGreater(
            len(inverted.explosion_controller.topology.seams_by_boundary),
            0,
        )
        self.assertIn(
            (EDGE_INVERT, EDGE_INVERT),
            inverted.snapshot.topology.topology_edge_rules,
        )
        self.assertIn(
            (EDGE_BOUNDED, EDGE_BOUNDED),
            bounded.snapshot.topology.topology_edge_rules,
        )
        self.assertEqual(
            wrapped.snapshot.topology.topology_edge_rules[1],
            (EDGE_WRAP, EDGE_WRAP),
        )
        self.assertEqual(
            inverted.snapshot.topology.topology_edge_rules[1],
            (EDGE_INVERT, EDGE_INVERT),
        )

    def test_4d_endgame_topology_includes_y_seams_for_presets(self) -> None:
        wrap_cfg = GameConfigND(
            dims=(5, 8, 5, 4),
            gravity_axis=1,
            topology_mode="wrap_all",
        )
        invert_cfg = GameConfigND(
            dims=(5, 8, 5, 4),
            gravity_axis=1,
            topology_mode="invert_all",
        )

        self.assertEqual(
            front4d_game._endgame_topology_edge_rules_4d(wrap_cfg)[1],
            (EDGE_WRAP, EDGE_WRAP),
        )
        self.assertEqual(
            front4d_game._endgame_topology_edge_rules_4d(invert_cfg)[1],
            (EDGE_INVERT, EDGE_INVERT),
        )

    def test_trace_enabled_controls_projected_endgame_trail_rendering(self) -> None:
        trail = ExplosionRenderTrailSegment(
            tail_position_nd=(1.0, 1.0),
            head_position_nd=(2.0, 1.0),
            tail_render_position=(1.0, 1.0, 0.0),
            head_render_position=(2.0, 1.0, 0.0),
            alpha=1.0,
            width=1.0,
        )
        relic_state = SimpleNamespace(
            color_id=1,
            trail_segments=(trail,),
            render_position=(1.0, 1.0, 0.0),
            rotation_deg=(0.0, 0.0, 0.0),
            alpha=0.0,
        )

        def _draw_line_count(*, trace_enabled: bool) -> int:
            snapshot = endgame_animation.create_snapshot(
                dimension=2,
                board_dims=(4, 4),
                render_dims=(4, 4, 1),
                locked_cells=(),
                base_seed=2026,
                render_context=endgame_animation.EndgameRenderContext(mode_key="2d"),
                trace_enabled=trace_enabled,
            )
            animation = SimpleNamespace(
                snapshot=snapshot,
                shell_fragments=(),
                grid_break_marks=(),
                escaping_artifacts=(),
                elapsed_ms=0.0,
                tuning=endgame_animation.load_endgame_animation_tuning(),
                explosion_controller=SimpleNamespace(
                    render_particles=Mock(return_value=(relic_state,))
                ),
            )
            surface = pygame.Surface((200, 200), pygame.SRCALPHA)
            with patch.object(pygame.draw, "line", wraps=pygame.draw.line) as draw_line:
                gfx_game._draw_endgame_board_2d(
                    surface,
                    board_rect=pygame.Rect(0, 0, 120, 120),
                    board_offset=(0, 0),
                    endgame_animation=animation,
                )
            return int(draw_line.call_count)

        self.assertEqual(_draw_line_count(trace_enabled=False), 0)
        self.assertGreater(_draw_line_count(trace_enabled=True), 0)

    def test_projected_3d_endgame_render_consumes_shadow_mode(self) -> None:
        relic_state = SimpleNamespace(
            color_id=1,
            trail_segments=(),
            render_position=(1.0, 1.0, 1.0),
            rotation_deg=(0.0, 0.0, 0.0),
            alpha=0.0,
        )

        def _shadow_draw_calls(shadow_mode: str) -> int:
            snapshot = endgame_animation.create_snapshot(
                dimension=3,
                board_dims=(4, 4, 4),
                render_dims=(4, 4, 4),
                locked_cells=(),
                base_seed=2026,
                render_context=endgame_animation.EndgameRenderContext(
                    mode_key="3d",
                    zoom=42.0,
                ),
                shadow_mode=shadow_mode,
            )
            animation = SimpleNamespace(
                snapshot=snapshot,
                shell_fragments=(),
                grid_break_marks=(),
                escaping_artifacts=(),
                elapsed_ms=0.0,
                tuning=endgame_animation.load_endgame_animation_tuning(),
                explosion_controller=SimpleNamespace(
                    render_particles=Mock(return_value=(relic_state,))
                ),
            )
            surface = pygame.Surface((360, 280), pygame.SRCALPHA)
            with patch.object(
                front3d_render,
                "draw_boundary_projection_faces",
                wraps=front3d_render.draw_boundary_projection_faces,
            ) as draw_faces:
                front3d_render._draw_endgame_board_3d(
                    surface,
                    board_rect=pygame.Rect(0, 0, 240, 220),
                    endgame_animation=animation,
                )
            return int(draw_faces.call_count)

        self.assertEqual(_shadow_draw_calls("off"), 0)
        self.assertGreater(_shadow_draw_calls("bottom_boundary"), 0)
        self.assertGreater(_shadow_draw_calls("all_boundaries"), 0)

    def test_w_movement_setting_reaches_endgame_render_context(self) -> None:
        snapshot = endgame_animation.create_snapshot(
            dimension=4,
            board_dims=(5, 8, 5, 4),
            render_dims=(5, 8, 5),
            locked_cells=self._locked_cells_for_dims((5, 8, 5, 4), 80),
            base_seed=2026,
            render_context=endgame_animation.EndgameRenderContext(
                mode_key="4d",
                layer_count=4,
                basis_axis_map=((0, 1), (1, 1), (2, 1), (3, 1)),
            ),
            w_movement_animation_style="box_size",
        )
        animation = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(
            animation.snapshot.render_context.w_movement_animation_style,
            "box_size",
        )
        assert animation.explosion_controller is not None
        animation.explosion_controller.render_particles(
            render_context=animation.snapshot.render_context
        )

    def test_4d_endgame_render_uses_box_size_layer_scale(self) -> None:
        relic_state = SimpleNamespace(
            color_id=1,
            render_position=(1.0, 1.0, 1.0),
            rotation_deg=(0.0, 0.0, 0.0),
            alpha=1.0,
            layer_weights=((0, 1.0),),
            layer_scales=((0, 1.0), (1, 0.45)),
            trail_segments=(),
        )

        def _draw_calls(style: str) -> int:
            snapshot = endgame_animation.create_snapshot(
                dimension=4,
                board_dims=(5, 8, 5, 4),
                render_dims=(5, 8, 5),
                locked_cells=(),
                base_seed=2026,
                render_context=endgame_animation.EndgameRenderContext(
                    mode_key="4d",
                    layer_axis_label="w",
                    layer_count=4,
                    basis_axis_map=((0, 1), (1, 1), (2, 1), (3, 1)),
                    w_movement_animation_style=style,
                ),
                shadow_mode="off",
                w_movement_animation_style=style,
            )
            animation = SimpleNamespace(
                snapshot=snapshot,
                shell_fragments=(),
                grid_break_marks=(),
                escaping_artifacts=(),
                elapsed_ms=0.0,
                tuning=endgame_animation.load_endgame_animation_tuning(),
                explosion_controller=SimpleNamespace(
                    render_particles=Mock(return_value=(relic_state,))
                ),
            )
            surface = pygame.Surface((640, 480), pygame.SRCALPHA)
            with patch.object(
                front4d_render,
                "build_oriented_cube_faces",
                return_value=(
                    (0.0, [(0, 0), (8, 0), (8, 8)], (10, 20, 30), True),
                ),
            ) as build_faces:
                front4d_render._draw_endgame_layer_board(
                    surface,
                    rect=pygame.Rect(0, 0, 220, 180),
                    layer_index=1,
                    snapshot=snapshot,
                    context=snapshot.render_context,
                    fonts=self.fonts_4d,
                    endgame_animation=animation,
                )
            return int(build_faces.call_count)

        self.assertEqual(_draw_calls("fade"), 0)
        self.assertGreater(_draw_calls("box_size"), 0)

    def test_endgame_live_cell_count_uses_available_locked_cells_fraction(self) -> None:
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=2,
                available_locked_cells=17,
                live_fraction=0.12,
            ),
            2,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=2,
                available_locked_cells=500,
                live_fraction=0.12,
            ),
            60,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=3,
                available_locked_cells=55,
                live_fraction=0.01,
            ),
            1,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=4,
                available_locked_cells=48,
                live_fraction=0.12,
            ),
            6,
        )

    def test_endgame_live_cell_floor_caps_to_available_locked_cells(self) -> None:
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=2,
                available_locked_cells=8,
                live_fraction=0.0,
            ),
            1,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=3,
                available_locked_cells=12,
                live_fraction=0.0,
            ),
            1,
        )

    def test_endgame_live_cell_selection_is_deterministic_and_order_stable(self) -> None:
        locked_cells = (
            endgame_animation.SnapshotCell(
                source_coord=(3, 0, 1),
                position=(3.0, 0.0, 1.0),
                color_id=2,
            ),
            endgame_animation.SnapshotCell(
                source_coord=(0, 2, 1),
                position=(0.0, 2.0, 1.0),
                color_id=5,
            ),
            endgame_animation.SnapshotCell(
                source_coord=(1, 1, 1),
                position=(1.0, 1.0, 1.0),
                color_id=4,
            ),
            endgame_animation.SnapshotCell(
                source_coord=(2, 3, 0),
                position=(2.0, 3.0, 0.0),
                color_id=1,
            ),
            endgame_animation.SnapshotCell(
                source_coord=(0, 0, 3),
                position=(0.0, 0.0, 3.0),
                color_id=7,
            ),
        )

        selected_a = endgame_animation.select_endgame_live_locked_cells(
            locked_cells=locked_cells,
            dimension=3,
            seed=1337,
            live_fraction=0.03,
        )
        selected_b = endgame_animation.select_endgame_live_locked_cells(
            locked_cells=tuple(reversed(locked_cells)),
            dimension=3,
            seed=1337,
            live_fraction=0.03,
        )

        self.assertEqual(selected_a, selected_b)

    def test_endgame_snapshot_splits_persistent_and_escaping_cells_as_exact_complement(
        self,
    ) -> None:
        locked_cells = tuple(
            endgame_animation.SnapshotCell(
                source_coord=(index % 5, index // 5),
                position=(float(index % 5), float(index // 5), 0.0),
                color_id=(index % 7) + 1,
            )
            for index in range(60)
        )

        snapshot = endgame_animation.create_snapshot(
            dimension=2,
            board_dims=(20, 20),
            render_dims=(20, 20, 1),
            locked_cells=locked_cells,
            base_seed=2026,
            render_context=endgame_animation.EndgameRenderContext(mode_key="2d"),
            endgame_live_cell_fraction=0.12,
        )
        animation = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(len(snapshot.locked_cells), 60)
        self.assertEqual(len(snapshot.persistent_live_cells), 7)
        self.assertEqual(len(snapshot.escaping_cells), 53)
        self.assertEqual(
            set(snapshot.persistent_live_cells).intersection(
                set(snapshot.escaping_cells)
            ),
            set(),
        )
        self.assertEqual(
            set(snapshot.persistent_live_cells).union(set(snapshot.escaping_cells)),
            set(snapshot.locked_cells),
        )
        assert animation.explosion_controller is not None
        self.assertEqual(
            len(animation.explosion_controller.simulation.particles),
            len(snapshot.persistent_live_cells),
        )
        self.assertEqual(
            tuple(
                tuple(int(axis) for axis in particle.source_coord)
                for particle in animation.explosion_controller.simulation.particles
            ),
            tuple(cell.source_coord for cell in snapshot.persistent_live_cells),
        )
        self.assertEqual(
            len(
                animation.explosion_controller.render_particles(
                    render_context=animation.snapshot.render_context
                )
            ),
            len(snapshot.persistent_live_cells),
        )
        self.assertLess(
            len(snapshot.persistent_live_cells),
            len(snapshot.locked_cells),
        )

    def test_small_board_live_fraction_keeps_nonempty_subset(self) -> None:
        locked_cells = tuple(
            endgame_animation.SnapshotCell(
                source_coord=(index % 6, index // 6),
                position=(float(index % 6), float(index // 6), 0.0),
                color_id=1,
            )
            for index in range(24)
        )

        snapshot = endgame_animation.create_snapshot(
            dimension=2,
            board_dims=(6, 6),
            render_dims=(6, 6, 1),
            locked_cells=locked_cells,
            base_seed=99,
            render_context=endgame_animation.EndgameRenderContext(mode_key="2d"),
            endgame_live_cell_fraction=0.12,
        )

        self.assertEqual(len(snapshot.persistent_live_cells), 3)
        self.assertEqual(len(snapshot.escaping_cells), 21)

    def test_endgame_live_cell_count_uses_same_rule_for_2d_3d_and_4d(self) -> None:
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=2,
                available_locked_cells=200,
                live_fraction=0.12,
            ),
            24,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=3,
                available_locked_cells=200,
                live_fraction=0.12,
            ),
            24,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=4,
                available_locked_cells=200,
                live_fraction=0.12,
            ),
            24,
        )

    def test_endgame_live_fraction_changes_controller_particle_count_3d_4d(
        self,
    ) -> None:
        for dimension, dims, locked_count in (
            (3, (6, 10, 6), 48),
            (3, (8, 10, 8), 220),
            (4, (5, 8, 5, 4), 48),
            (4, (6, 8, 6, 4), 220),
        ):
            with self.subTest(dimension=dimension, locked_count=locked_count):
                locked_cells = self._locked_cells_for_dims(dims, locked_count)
                snapshot_low = endgame_animation.create_snapshot(
                    dimension=dimension,
                    board_dims=dims,
                    render_dims=(dims[0], dims[1], dims[2]),
                    locked_cells=locked_cells,
                    base_seed=2026,
                    render_context=endgame_animation.EndgameRenderContext(
                        mode_key=f"{dimension}d",
                        layer_count=dims[3] if dimension == 4 else 1,
                        basis_axis_map=((0, 1), (1, 1), (2, 1), (3, 1))
                        if dimension == 4
                        else (),
                    ),
                    endgame_live_cell_fraction=0.12,
                )
                snapshot_high = endgame_animation.create_snapshot(
                    dimension=dimension,
                    board_dims=dims,
                    render_dims=(dims[0], dims[1], dims[2]),
                    locked_cells=locked_cells,
                    base_seed=2026,
                    render_context=snapshot_low.render_context,
                    endgame_live_cell_fraction=0.50,
                )
                animation_low = endgame_animation.build_endgame_animation_state(
                    snapshot_low
                )
                animation_high = endgame_animation.build_endgame_animation_state(
                    snapshot_high
                )
                assert animation_low.explosion_controller is not None
                assert animation_high.explosion_controller is not None
                self.assertLess(
                    len(animation_low.explosion_controller.simulation.particles),
                    locked_count,
                )
                self.assertGreater(
                    len(animation_high.explosion_controller.simulation.particles),
                    len(animation_low.explosion_controller.simulation.particles),
                )

    def test_shell_artifact_count_is_capped_by_dimension(self) -> None:
        scenarios = (
            (2, 140, 32),
            (3, 180, 40),
            (4, 220, 48),
        )
        for dimension, locked_count, expected_cap in scenarios:
            with self.subTest(dimension=dimension):
                animation = endgame_animation.build_endgame_animation_state(
                    self._artifact_snapshot(
                        dimension=dimension,
                        locked_count=locked_count,
                    )
                )
                self.assertEqual(len(animation.escaping_artifacts), expected_cap)

    def test_shell_artifacts_derive_only_from_escaping_cells(self) -> None:
        snapshot = self._artifact_snapshot(dimension=3, locked_count=120)
        animation = endgame_animation.build_endgame_animation_state(snapshot)
        escaping_coords = {cell.source_coord for cell in snapshot.escaping_cells}
        persistent_coords = {
            cell.source_coord for cell in snapshot.persistent_live_cells
        }

        self.assertTrue(animation.escaping_artifacts)
        self.assertTrue(
            all(
                artifact.source_coord in escaping_coords
                for artifact in animation.escaping_artifacts
            )
        )
        self.assertTrue(
            all(
                artifact.source_coord not in persistent_coords
                for artifact in animation.escaping_artifacts
            )
        )

    def test_shell_artifact_sampling_is_deterministic_for_reversed_input(self) -> None:
        animation_a = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=4, locked_count=180)
        )
        animation_b = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(
                dimension=4,
                locked_count=180,
                reversed_cells=True,
            )
        )

        self.assertEqual(animation_a.escaping_artifacts, animation_b.escaping_artifacts)

    def test_shell_artifacts_do_not_change_survivor_controller_particles(self) -> None:
        snapshot = self._artifact_snapshot(dimension=2, locked_count=90)
        animation = endgame_animation.build_endgame_animation_state(snapshot)
        assert animation.explosion_controller is not None

        self.assertEqual(
            tuple(
                tuple(int(axis) for axis in particle.source_coord)
                for particle in animation.explosion_controller.simulation.particles
            ),
            tuple(cell.source_coord for cell in snapshot.persistent_live_cells),
        )
        self.assertTrue(animation.escaping_artifacts)

    def test_4d_shell_artifacts_are_not_full_cell_render_states(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=4, locked_count=160)
        )

        self.assertTrue(animation.escaping_artifacts)
        self.assertTrue(
            all(
                not hasattr(artifact, "render_position")
                and not hasattr(artifact, "layer_weights")
                and not hasattr(artifact, "trail_segments")
                for artifact in animation.escaping_artifacts
            )
        )

    def test_shell_artifacts_expire_before_persistent_residue_phase(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=3, locked_count=120)
        )
        elapsed_ms = float(animation.tuning.shatter_duration_ms)

        self.assertTrue(animation.escaping_artifacts)
        self.assertTrue(
            all(
                endgame_animation.transform_shell_artifact(
                    artifact,
                    elapsed_ms=elapsed_ms,
                )[2]
                == 0.0
                for artifact in animation.escaping_artifacts
            )
        )

    def test_grid_break_mark_count_is_capped_by_dimension(self) -> None:
        scenarios = (
            (2, 140, 12),
            (3, 180, 16),
            (4, 220, 20),
        )
        for dimension, locked_count, expected_cap in scenarios:
            with self.subTest(dimension=dimension):
                animation = endgame_animation.build_endgame_animation_state(
                    self._artifact_snapshot(
                        dimension=dimension,
                        locked_count=locked_count,
                    )
                )
                self.assertEqual(len(animation.grid_break_marks), expected_cap)

    def test_grid_break_marks_derive_only_from_shell_artifacts(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=3, locked_count=150)
        )
        artifact_coords = {
            artifact.source_coord for artifact in animation.escaping_artifacts
        }

        self.assertTrue(animation.grid_break_marks)
        self.assertTrue(
            all(mark.source_coord in artifact_coords for mark in animation.grid_break_marks)
        )

    def test_grid_break_marks_are_deterministic_for_same_input(self) -> None:
        snapshot = self._artifact_snapshot(dimension=4, locked_count=180)
        animation_a = endgame_animation.build_endgame_animation_state(snapshot)
        animation_b = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(animation_a.grid_break_marks, animation_b.grid_break_marks)

    def test_grid_break_marks_leave_low_alpha_persistent_residue(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=3, locked_count=150)
        )
        elapsed_ms = float(animation.tuning.shatter_duration_ms)

        self.assertTrue(animation.grid_break_marks)
        self.assertTrue(
            all(
                endgame_animation.transform_grid_break_mark(
                    mark,
                    elapsed_ms=elapsed_ms,
                )[2]
                == mark.residue_alpha
                for mark in animation.grid_break_marks
            )
        )
        self.assertTrue(
            all(0.0 < mark.residue_alpha <= 0.25 for mark in animation.grid_break_marks)
        )

    def test_cracked_board_residue_remains_available_after_persistent_phase_starts(
        self,
    ) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=4, locked_count=180)
        )
        elapsed_ms = float(animation.tuning.shatter_duration_ms)

        self.assertGreater(
            endgame_animation.board_shell_residue_alpha(
                elapsed_ms=elapsed_ms,
                tuning=animation.tuning,
            ),
            0.0,
        )
        self.assertTrue(
            any(
                endgame_animation.transform_grid_break_mark(
                    mark,
                    elapsed_ms=elapsed_ms,
                )[2]
                > 0.0
                for mark in animation.grid_break_marks
            )
        )

    def test_artifact_timing_uses_endgame_tuning_values(self) -> None:
        base_tuning = endgame_animation.load_endgame_animation_tuning()
        tuning = replace(
            base_tuning,
            shatter_duration_ms=2000.0,
            capture_transition_duration_ms=1000.0,
            shell_artifact_birth_spread_ms=0.0,
            shell_artifact_lifetime_min_ms=777.0,
            shell_artifact_lifetime_max_ms=777.0,
            grid_break_birth_lead_ms=123.0,
            grid_break_lifetime_ms=456.0,
        )
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=3, locked_count=150),
            tuning=tuning,
        )

        self.assertTrue(animation.escaping_artifacts)
        self.assertTrue(animation.grid_break_marks)
        self.assertTrue(
            all(
                artifact.birth_ms == tuning.capture_start_ms
                and artifact.lifetime_ms == 777.0
                and artifact.length_scale == tuning.shell_artifact_length_scale
                for artifact in animation.escaping_artifacts
            )
        )
        self.assertTrue(
            all(
                mark.birth_ms == tuning.capture_start_ms - 123.0
                and mark.lifetime_ms == 456.0
                and mark.residue_alpha == tuning.grid_break_residue_alpha
                for mark in animation.grid_break_marks
            )
        )

    def test_artifact_visibility_lasts_past_initial_rupture_window(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=3, locked_count=150)
        )
        self.assertGreaterEqual(animation.tuning.crack_onset_duration_ms, 120.0)
        self.assertLessEqual(animation.tuning.crack_onset_duration_ms, 200.0)
        self.assertGreaterEqual(animation.tuning.capture_start_ms, 350.0)
        self.assertLessEqual(animation.tuning.capture_start_ms, 700.0)
        self.assertGreaterEqual(animation.tuning.shell_fragment_lifetime_ms, 1700.0)
        self.assertGreater(animation.tuning.rupture_flash_alpha, 0.0)
        self.assertGreaterEqual(animation.tuning.rupture_flash_duration_ms, 400.0)
        self.assertLessEqual(animation.tuning.rupture_flash_duration_ms, 700.0)
        self.assertGreater(
            endgame_animation.rupture_flash_alpha(
                elapsed_ms=animation.tuning.capture_start_ms + 120.0,
                tuning=animation.tuning,
            ),
            0.0,
        )
        elapsed_ms = animation.tuning.capture_start_ms + 500.0

        self.assertTrue(
            any(
                endgame_animation.transform_shell_artifact(
                    artifact,
                    elapsed_ms=elapsed_ms,
                )[2]
                > 0.0
                for artifact in animation.escaping_artifacts
            )
        )

    def test_4d_grid_break_marks_are_not_full_cell_render_states(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._artifact_snapshot(dimension=4, locked_count=180)
        )

        self.assertTrue(animation.grid_break_marks)
        self.assertTrue(
            all(
                not hasattr(mark, "render_position")
                and not hasattr(mark, "layer_weights")
                and not hasattr(mark, "trail_segments")
                for mark in animation.grid_break_marks
            )
        )

    def test_preset_registry_resolves_required_endgame_presets(self) -> None:
        tuning = endgame_animation.load_endgame_animation_tuning()
        registry = {
            config.preset_id: config
            for config in endgame_animation.endgame_preset_registry(tuning)
        }

        self.assertEqual(registry["wrap_all"].field_kind, "wrap")
        self.assertEqual(registry["invert_all"].field_kind, "invert")
        self.assertEqual(registry["sphere"].field_kind, "sphere")

    def test_fragment_generation_is_deterministic_for_fixed_seed(self) -> None:
        snapshot = self._sample_snapshot()

        animation_a = endgame_animation.build_endgame_animation_state(snapshot)
        animation_b = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(animation_a.snapshot.rng_seed, animation_b.snapshot.rng_seed)
        assert animation_a.explosion_controller is not None
        assert animation_b.explosion_controller is not None
        self.assertEqual(
            animation_a.explosion_controller.render_particles(
                render_context=animation_a.snapshot.render_context
            ),
            animation_b.explosion_controller.render_particles(
                render_context=animation_b.snapshot.render_context
            ),
        )
        self.assertEqual(animation_a.shell_fragments, animation_b.shell_fragments)

    def test_endgame_sfx_events_follow_shared_phase_thresholds(self) -> None:
        tuning = endgame_animation.load_endgame_animation_tuning()
        crack_events = endgame_animation.endgame_sfx_events_between(
            previous_elapsed_ms=0.0,
            current_elapsed_ms=tuning.crack_onset_duration_ms,
            tuning=tuning,
        )
        pop_events = endgame_animation.endgame_sfx_events_between(
            previous_elapsed_ms=tuning.crack_onset_duration_ms,
            current_elapsed_ms=tuning.capture_start_ms,
            tuning=tuning,
        )
        boom_events = endgame_animation.endgame_sfx_events_between(
            previous_elapsed_ms=tuning.capture_start_ms,
            current_elapsed_ms=tuning.shatter_duration_ms,
            tuning=tuning,
        )

        self.assertEqual(crack_events, ("endgame_crack",))
        self.assertEqual(pop_events, ("endgame_pop",))
        self.assertEqual(boom_events, ("endgame_boom",))

    def test_draw_native_board_view_has_no_extra_render_particles_argument(self) -> None:
        from tet4d.ui.pygame.locked_cell_explosion.board_view import (
            draw_native_board_view,
        )

        self.assertNotIn(
            "extra_render_particles",
            inspect.signature(draw_native_board_view).parameters,
        )

    def test_normal_gameplay_updates_stop_once_terminal_animation_takes_over(
        self,
    ) -> None:
        state = SimpleNamespace(
            config=SimpleNamespace(exploration_mode=False),
            game_over=False,
            step_gravity=Mock(),
        )
        loop = SimpleNamespace(
            terminal_phase=endgame_animation.TERMINAL_PHASE_ENDGAME_SHATTER,
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

    def test_projected_3d_renderer_uses_frozen_snapshot_not_mutated_live_board(
        self,
    ) -> None:
        cfg = GameConfigND(dims=(6, 10, 6), gravity_axis=1, speed_level=1)
        loop = front3d_game.LoopContext3D.create(cfg)
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 8, 2)] = 4
        loop.state.board.cells[(3, 7, 3)] = 6
        loop.state.game_over = True
        loop.endgame_animation = endgame_animation.build_endgame_animation_state(
            front3d_game._capture_endgame_snapshot_3d(loop)
        )
        loop.terminal_phase = endgame_animation.TERMINAL_PHASE_ENDGAME_SHATTER

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

    def test_projected_4d_renderer_uses_frozen_snapshot_not_mutated_live_board(
        self,
    ) -> None:
        cfg = GameConfigND(dims=(5, 8, 5, 3), gravity_axis=1, speed_level=1)
        loop = front4d_game.LoopContext4D.create(cfg)
        loop.state.board.cells.clear()
        loop.state.board.cells[(1, 6, 2, 0)] = 2
        loop.state.board.cells[(3, 5, 1, 2)] = 5
        loop.state.game_over = True
        loop.endgame_animation = endgame_animation.build_endgame_animation_state(
            front4d_game._capture_endgame_snapshot_4d(loop)
        )
        loop.terminal_phase = endgame_animation.TERMINAL_PHASE_ENDGAME_SHATTER

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

    def test_regression_scenarios_cover_sparse_dense_near_full_and_projected_3d(
        self,
    ) -> None:
        scenarios = {
            "sparse": {(1, 8): 1, (5, 6): 4},
            "dense": {(x, y): (x % 7) + 1 for x in range(8) for y in range(5, 10)},
            "near_full": {
                (x, y): ((x + y) % 7) + 1 for x in range(8) for y in range(1, 10)
            },
        }

        for label, cells in scenarios.items():
            with self.subTest(label=label):
                loop = LoopContext2D.create(
                    GameConfig(width=8, height=10, speed_level=1)
                )
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
                assert loop.endgame_animation.explosion_controller is not None
                self.assertEqual(
                    len(loop.endgame_animation.explosion_controller.simulation.particles),
                    len(loop.endgame_animation.snapshot.persistent_live_cells),
                )
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
        assert loop_3d.endgame_animation.explosion_controller is not None
        self.assertEqual(
            len(loop_3d.endgame_animation.explosion_controller.simulation.particles),
            len(loop_3d.endgame_animation.snapshot.persistent_live_cells),
        )
        self.assertGreater(len(loop_3d.endgame_animation.shell_fragments), 0)


if __name__ == "__main__":
    unittest.main()
