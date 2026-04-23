from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import math
import shutil
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import pygame

from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
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
    def _custom_tuning(**updates: float | bool | int | tuple[tuple[str, int], ...]):
        return replace(endgame_animation.load_endgame_animation_tuning(), **updates)

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
        self.assertEqual(len(snapshot.live_locked_cells), 2)

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

    def test_endgame_animation_uses_shared_runtime_defaults_builder(self) -> None:
        snapshot = self._sample_snapshot()

        with patch.object(
            endgame_animation,
            "build_runtime_explosion_config",
            wraps=endgame_animation.build_runtime_explosion_config,
        ) as build_config:
            animation = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(build_config.call_count, 1)
        defaults = build_config.call_args.kwargs["defaults"]
        launch = build_config.call_args.kwargs["launch"]
        self.assertEqual(defaults.boundary_response, snapshot.boundary_response)
        self.assertEqual(defaults.trace_retention_ms, snapshot.trace_retention_ms)
        self.assertEqual(launch.dimension, snapshot.dimension)
        self.assertEqual(launch.random_seed, snapshot.rng_seed)
        self.assertEqual(
            tuple(cell.source_coord for cell in launch.occupied_cells),
            tuple(cell.source_coord for cell in snapshot.live_locked_cells),
        )
        self.assertEqual(
            animation.explosion_controller.config.boundary_response,
            snapshot.boundary_response,
        )

    def test_endgame_live_cell_count_uses_fraction_floor_and_cap(self) -> None:
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=2,
                board_dims=(10, 20),
                available_locked_cells=17,
                live_fraction=0.12,
            ),
            17,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=2,
                board_dims=(40, 20),
                available_locked_cells=500,
                live_fraction=0.12,
            ),
            96,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=3,
                board_dims=(4, 4, 4),
                available_locked_cells=55,
                live_fraction=0.01,
            ),
            40,
        )
        self.assertEqual(
            endgame_animation.endgame_live_cell_count(
                dimension=4,
                board_dims=(4, 4, 4, 4),
                available_locked_cells=48,
                live_fraction=0.12,
            ),
            48,
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
            board_dims=(5, 5, 5),
            dimension=3,
            seed=1337,
            live_fraction=0.03,
        )
        selected_b = endgame_animation.select_endgame_live_locked_cells(
            locked_cells=tuple(reversed(locked_cells)),
            board_dims=(5, 5, 5),
            dimension=3,
            seed=1337,
            live_fraction=0.03,
        )

        self.assertEqual(selected_a, selected_b)

    def test_endgame_snapshot_limits_live_explosion_subset(self) -> None:
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
        self.assertEqual(len(snapshot.live_locked_cells), 48)
        self.assertEqual(
            len(animation.explosion_controller.simulation.particles),
            len(snapshot.live_locked_cells),
        )
        self.assertLess(
            len(snapshot.live_locked_cells),
            len(snapshot.locked_cells),
        )

    def test_small_board_floor_prevents_empty_endgame_subset(self) -> None:
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

        self.assertEqual(len(snapshot.live_locked_cells), 20)

    def test_preset_registry_resolves_required_relic_field_presets(self) -> None:
        tuning = endgame_animation.load_endgame_animation_tuning()
        registry = {
            config.preset_id: config
            for config in endgame_animation.endgame_preset_registry(tuning)
        }

        self.assertEqual(registry["wrap_all"].field_kind, "wrap")
        self.assertEqual(registry["invert_all"].field_kind, "invert")
        self.assertEqual(registry["sphere"].field_kind, "sphere")

    def test_boundary_and_collision_axes_normalize_without_changing_preset_identity(
        self,
    ) -> None:
        wrap_snapshot = self._sample_snapshot(
            preset_id="wrap_all",
            boundary_response="escape",
            particle_collisions="off",
        )
        collide_snapshot = self._sample_snapshot(
            preset_id="wrap_all",
            boundary_response="bounce",
            particle_collisions="on",
        )
        wrap_animation = endgame_animation.build_endgame_animation_state(wrap_snapshot)
        collide_animation = endgame_animation.build_endgame_animation_state(
            collide_snapshot
        )

        self.assertEqual(wrap_animation.preset_id, "wrap_all")
        self.assertEqual(collide_animation.preset_id, "wrap_all")
        self.assertEqual(wrap_animation.boundary_response, "escape")
        self.assertEqual(wrap_animation.particle_collisions, "off")
        self.assertEqual(collide_animation.boundary_response, "bounce")
        self.assertEqual(collide_animation.particle_collisions, "on")

    def test_fragment_generation_is_deterministic_for_fixed_seed(self) -> None:
        snapshot = self._sample_snapshot()

        animation_a = endgame_animation.build_endgame_animation_state(snapshot)
        animation_b = endgame_animation.build_endgame_animation_state(snapshot)

        self.assertEqual(animation_a.snapshot.rng_seed, animation_b.snapshot.rng_seed)
        self.assertEqual(animation_a.cell_relics, animation_b.cell_relics)
        self.assertEqual(animation_a.shell_fragments, animation_b.shell_fragments)

    def test_cell_relic_updates_match_expected_known_timestamp(self) -> None:
        tuning = self._custom_tuning(
            crack_onset_duration_ms=100.0,
            shatter_duration_ms=1000.0,
            capture_transition_duration_ms=300.0,
            burst_drag_per_second=0.5,
        )
        relic = endgame_animation.CellRelic(
            source_coord=(1, 2),
            base_geometry="cell",
            initial_position=(1.0, 2.0, 0.0),
            burst_velocity=(4.0, 0.0, 0.0),
            burst_acceleration=(0.0, 1.0, 0.0),
            burst_angular_velocity_deg=(0.0, 0.0, 90.0),
            detach_start_ms=100.0,
            capture_anchor=(5.0, 4.0, 0.0),
            path_family="ellipse",
            field_basis_u=(1.0, 0.0, 0.0),
            field_basis_v=(0.0, 1.0, 0.0),
            field_basis_w=(0.0, 0.0, 0.0),
            field_phase=0.0,
            field_phase_secondary=0.0,
            field_speed=0.0,
            field_precession_speed=0.0,
            orbit_radius_a=1.5,
            orbit_radius_b=2.0,
            depth_amplitude=0.0,
            relic_spin_deg=(10.0, 20.0, 30.0),
            color_id=5,
            jitter_offset=(2.0, 0.0, 0.0),
        )

        position_pre, rotation_pre, alpha_pre = (
            endgame_animation.transform_for_cell_relic(
                relic,
                elapsed_ms=50.0,
                tuning=tuning,
            )
        )
        self.assertEqual(position_pre, (2.0, 2.0, 0.0))
        self.assertEqual(rotation_pre, (0.0, 0.0, 0.0))
        self.assertEqual(alpha_pre, 1.0)

        position_post, rotation_post, alpha_post = (
            endgame_animation.transform_for_cell_relic(
                relic,
                elapsed_ms=1200.0,
                tuning=tuning,
            )
        )
        self.assertAlmostEqual(position_post[0], 6.5)
        self.assertAlmostEqual(position_post[1], 4.0)
        self.assertAlmostEqual(position_post[2], 0.0)
        self.assertAlmostEqual(rotation_post[0], 5.0)
        self.assertAlmostEqual(rotation_post[1], 24.0)
        self.assertAlmostEqual(rotation_post[2], 15.0)
        self.assertAlmostEqual(alpha_post, 1.0)

    def test_wrap_all_keeps_relics_wrapped_inside_field_bounds(self) -> None:
        tuning = self._custom_tuning(
            crack_onset_duration_ms=100.0,
            shatter_duration_ms=1000.0,
            capture_transition_duration_ms=200.0,
        )
        snapshot = self._sample_snapshot(preset_id="wrap_all")
        relic = endgame_animation.CellRelic(
            source_coord=(1, 2),
            base_geometry="cell",
            initial_position=(1.0, 2.0, 0.0),
            burst_velocity=(0.0, 0.0, 0.0),
            burst_acceleration=(0.0, 0.0, 0.0),
            burst_angular_velocity_deg=(0.0, 0.0, 0.0),
            detach_start_ms=100.0,
            capture_anchor=(8.5, 2.0, 0.0),
            path_family="ellipse",
            field_basis_u=(1.0, 0.0, 0.0),
            field_basis_v=(0.0, 1.0, 0.0),
            field_basis_w=(0.0, 0.0, 0.0),
            field_phase=0.0,
            field_phase_secondary=0.0,
            field_speed=0.0,
            field_precession_speed=0.0,
            orbit_radius_a=0.0,
            orbit_radius_b=0.0,
            depth_amplitude=0.0,
            relic_spin_deg=(0.0, 0.0, 0.0),
            color_id=2,
            preset_id="wrap_all",
            field_drift_velocity=(3.0, 0.0, 0.0),
        )

        position, _rotation, _alpha = endgame_animation.transform_for_cell_relic(
            relic,
            elapsed_ms=2400.0,
            tuning=tuning,
            snapshot=snapshot,
        )
        preset = endgame_animation.resolve_endgame_preset_config(
            "wrap_all",
            tuning=tuning,
        )
        max_x = (
            ((snapshot.render_dims[0] - 1) * 0.5 * tuning.field_extent_multiplier)
            * preset.extent_scale
        ) + tuning.wrap_margin
        self.assertLessEqual(abs(position[0] - snapshot.board_center[0]), max_x + 1e-6)

    def test_invert_all_applies_coherent_reflection_rule(self) -> None:
        tuning = self._custom_tuning(
            crack_onset_duration_ms=100.0,
            shatter_duration_ms=1000.0,
            capture_transition_duration_ms=200.0,
        )
        snapshot = self._sample_snapshot(preset_id="invert_all")
        relic = endgame_animation.CellRelic(
            source_coord=(1, 2),
            base_geometry="cell",
            initial_position=(1.0, 2.0, 0.0),
            burst_velocity=(0.0, 0.0, 0.0),
            burst_acceleration=(0.0, 0.0, 0.0),
            burst_angular_velocity_deg=(0.0, 0.0, 0.0),
            detach_start_ms=100.0,
            capture_anchor=(7.8, 2.0, 0.0),
            path_family="ellipse",
            field_basis_u=(1.0, 0.0, 0.0),
            field_basis_v=(0.0, 1.0, 0.0),
            field_basis_w=(0.0, 0.0, 0.0),
            field_phase=0.0,
            field_phase_secondary=0.0,
            field_speed=0.0,
            field_precession_speed=0.0,
            orbit_radius_a=0.0,
            orbit_radius_b=0.0,
            depth_amplitude=0.0,
            relic_spin_deg=(0.0, 0.0, 18.0),
            color_id=2,
            preset_id="invert_all",
            field_drift_velocity=(3.0, 0.0, 0.0),
        )

        position, rotation, _alpha = endgame_animation.transform_for_cell_relic(
            relic,
            elapsed_ms=2600.0,
            tuning=tuning,
            snapshot=snapshot,
        )
        self.assertLess(position[0], snapshot.board_center[0] + 2.0)
        self.assertNotEqual(rotation[2], 0.0)

    def test_sphere_preset_keeps_relics_inside_spherical_field(self) -> None:
        snapshot = self._sample_snapshot(preset_id="sphere")
        animation = endgame_animation.build_endgame_animation_state(snapshot)
        relic = animation.cell_relics[0]
        position, _rotation, _alpha = endgame_animation.transform_for_cell_relic(
            relic,
            elapsed_ms=animation.tuning.shatter_duration_ms + 40_000.0,
            tuning=animation.tuning,
            snapshot=snapshot,
        )
        preset = endgame_animation.resolve_endgame_preset_config(
            "sphere",
            tuning=animation.tuning,
        )
        radius_limit = (
            (min(snapshot.render_dims[:2]) * 0.5 * preset.sphere_radius_scale)
            + animation.tuning.wrap_margin
            + 0.75
        )
        self.assertLessEqual(math.dist(position, snapshot.board_center), radius_limit)

    def test_4d_relic_motion_updates_hidden_axis_before_projection(self) -> None:
        snapshot = self._sample_snapshot_4d(
            preset_id="wrap_all",
            relic_speed_scale=1.35,
        )
        animation = endgame_animation.build_endgame_animation_state(snapshot)
        relic = animation.cell_relics[0]
        motion_state = endgame_animation.motion_state_for_cell_relic(
            relic,
            elapsed_ms=animation.tuning.shatter_duration_ms + 4200.0,
            tuning=animation.tuning,
            snapshot=snapshot,
        )

        self.assertEqual(len(motion_state.position_nd), 4)
        self.assertNotAlmostEqual(
            motion_state.position_nd[3],
            float(relic.source_coord[3]),
        )

    def test_4d_render_states_preserve_hidden_axis_layer_motion(self) -> None:
        snapshot = self._sample_snapshot_4d(preset_id="invert_all")
        animation = endgame_animation.build_endgame_animation_state(snapshot)
        assert animation.explosion_controller is not None
        particle = animation.explosion_controller.simulation.particles[0]
        particle.position_nd = (1.0, 6.0, 2.0, 1.75)
        particle.velocity_nd = (0.0, 0.0, 0.0, 0.0)

        render_states = endgame_animation.render_relics_for_animation(animation)

        self.assertEqual(len(render_states[0].position_nd), 4)
        self.assertGreaterEqual(len(render_states[0].layer_weights), 1)
        self.assertAlmostEqual(
            sum(weight for _layer, weight in render_states[0].layer_weights),
            1.0,
        )
        self.assertEqual(render_states[0].position_nd[3], 1.75)

    def test_relic_speed_scale_changes_persistent_nd_motion_without_changing_preset(
        self,
    ) -> None:
        slow_snapshot = self._sample_snapshot_4d(
            preset_id="wrap_all",
            relic_speed_scale=0.6,
        )
        fast_snapshot = self._sample_snapshot_4d(
            preset_id="wrap_all",
            relic_speed_scale=1.8,
        )
        slow_animation = endgame_animation.build_endgame_animation_state(slow_snapshot)
        fast_animation = endgame_animation.build_endgame_animation_state(fast_snapshot)
        elapsed_ms = slow_animation.tuning.shatter_duration_ms + 2600.0

        slow_state = endgame_animation.motion_state_for_cell_relic(
            slow_animation.cell_relics[0],
            elapsed_ms=elapsed_ms,
            tuning=slow_animation.tuning,
            snapshot=slow_snapshot,
        )
        fast_state = endgame_animation.motion_state_for_cell_relic(
            fast_animation.cell_relics[0],
            elapsed_ms=elapsed_ms,
            tuning=fast_animation.tuning,
            snapshot=fast_snapshot,
        )

        self.assertEqual(slow_snapshot.preset_id, fast_snapshot.preset_id)
        self.assertNotEqual(slow_state.position_nd, fast_state.position_nd)

    def test_endgame_transitions_from_shatter_to_relic_field(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot()
        )

        animation.step(animation.tuning.shatter_duration_ms - 1.0)
        self.assertEqual(
            animation.phase,
            endgame_animation.TERMINAL_PHASE_ENDGAME_SHATTER,
        )

        animation.step(1.0)
        self.assertEqual(
            animation.phase,
            endgame_animation.TERMINAL_PHASE_ENDGAME_RELIC_FIELD,
        )

    def test_endgame_prompt_becomes_ready_when_relic_field_starts(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot()
        )

        animation.step(animation.tuning.shatter_duration_ms)

        self.assertEqual(
            animation.phase,
            endgame_animation.TERMINAL_PHASE_ENDGAME_RELIC_FIELD,
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

    def test_shell_fragments_expire_while_cell_relics_persist(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot()
        )
        shell_fragment = animation.shell_fragments[0]
        cell_relic = animation.cell_relics[0]
        long_elapsed_ms = animation.tuning.shatter_duration_ms + 10_000.0

        _geometry, shell_alpha = endgame_animation.transform_shell_geometry(
            shell_fragment,
            elapsed_ms=long_elapsed_ms,
            drag_per_second=animation.tuning.burst_drag_per_second,
        )
        relic_position, _rotation, relic_alpha = (
            endgame_animation.transform_for_cell_relic(
                cell_relic,
                elapsed_ms=long_elapsed_ms,
                tuning=animation.tuning,
            )
        )

        self.assertEqual(shell_alpha, 0.0)
        self.assertEqual(relic_alpha, 1.0)
        self.assertTrue(all(math.isfinite(component) for component in relic_position))

    def test_relic_field_wraps_phase_and_stays_bounded(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot()
        )
        relic = animation.cell_relics[0]
        huge_elapsed_ms = animation.tuning.shatter_duration_ms + 1_000_000.0

        phase = endgame_animation.relic_field_phase_radians(
            relic,
            elapsed_ms=huge_elapsed_ms,
            tuning=animation.tuning,
        )
        position, _rotation, alpha = endgame_animation.transform_for_cell_relic(
            relic,
            elapsed_ms=huge_elapsed_ms,
            tuning=animation.tuning,
        )
        max_extent = (
            max(animation.snapshot.render_dims)
            + animation.tuning.orbit_radius_max
            + 4.0
        )

        self.assertGreaterEqual(phase, 0.0)
        self.assertLess(phase, math.tau)
        self.assertEqual(alpha, 1.0)
        self.assertLessEqual(max(abs(component) for component in position), max_extent)

    def test_collision_mode_is_deterministic_for_fixed_seed_state(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot(
                preset_id="wrap_all",
                boundary_response="bounce",
                particle_collisions="on",
            )
        )
        assert animation.explosion_controller is not None
        particles = animation.explosion_controller.simulation.particles
        particles[0].position_nd = (2.0, 2.0)
        particles[0].velocity_nd = (1.0, 0.0)
        particles[0].collision_radius = 0.5
        particles[1].position_nd = (2.8, 2.0)
        particles[1].velocity_nd = (-1.0, 0.0)
        particles[1].collision_radius = 0.5

        animation.step(200.0)
        transforms_a = endgame_animation.transform_relics_for_animation(animation)
        transforms_b = endgame_animation.transform_relics_for_animation(animation)

        self.assertEqual(transforms_a, transforms_b)

    def test_non_collision_mode_skips_collision_pass(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot(
                preset_id="wrap_all",
                boundary_response="escape",
                particle_collisions="off",
            )
        )
        animation.elapsed_ms = animation.tuning.shatter_duration_ms + 5000.0

        with patch.object(
            endgame_animation,
            "_apply_relic_collisions",
            wraps=endgame_animation._apply_relic_collisions,
        ) as collision_pass:
            transforms = endgame_animation.transform_relics_for_animation(animation)

        self.assertEqual(len(transforms), len(animation.cell_relics))
        collision_pass.assert_not_called()

    def test_game_end_render_tracks_explosion_controller_motion(self) -> None:
        animation = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot(preset_id="wrap_all")
        )
        assert animation.explosion_controller is not None
        before = endgame_animation.render_relics_for_animation(animation)

        animation.step(180.0)
        after = endgame_animation.render_relics_for_animation(animation)

        self.assertNotEqual(before[0].position_nd, after[0].position_nd)

    def test_particle_collision_axis_changes_behavior_without_changing_preset(self) -> None:
        wrap_none = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot(
                preset_id="wrap_all",
                boundary_response="escape",
                particle_collisions="off",
            )
        )
        wrap_full = endgame_animation.build_endgame_animation_state(
            self._sample_snapshot(
                preset_id="wrap_all",
                boundary_response="escape",
                particle_collisions="on",
            )
        )
        assert wrap_none.explosion_controller is not None
        assert wrap_full.explosion_controller is not None
        for animation in (wrap_none, wrap_full):
            particles = animation.explosion_controller.simulation.particles
            particles[0].position_nd = (2.0, 2.0)
            particles[0].velocity_nd = (1.0, 0.0)
            particles[0].collision_radius = 0.55
            particles[1].position_nd = (2.8, 2.0)
            particles[1].velocity_nd = (-1.0, 0.0)
            particles[1].collision_radius = 0.55

        wrap_none.step(220.0)
        wrap_full.step(220.0)

        none_particles = wrap_none.explosion_controller.simulation.particles
        full_particles = wrap_full.explosion_controller.simulation.particles

        self.assertEqual(wrap_none.preset_id, wrap_full.preset_id)
        self.assertGreater(none_particles[0].velocity_nd[0], 0.0)
        self.assertLess(none_particles[1].velocity_nd[0], 0.0)
        self.assertLess(full_particles[0].velocity_nd[0], 0.0)
        self.assertGreater(full_particles[1].velocity_nd[0], 0.0)

    def test_render_states_preserve_nd_positions_not_projected_screen_overlap(
        self,
    ) -> None:
        snapshot = self._sample_snapshot_4d(
            preset_id="wrap_all",
            boundary_response="bounce",
            particle_collisions="on",
        )
        animation = endgame_animation.build_endgame_animation_state(snapshot)
        assert animation.explosion_controller is not None
        particles = animation.explosion_controller.simulation.particles
        particles[0].position_nd = (2.0, 2.0, 2.0, 0.0)
        particles[0].velocity_nd = (0.0, 0.0, 0.0, 0.0)
        particles[1].position_nd = (2.0, 2.0, 2.0, 2.0)
        particles[1].velocity_nd = (0.0, 0.0, 0.0, 0.0)

        render_states = endgame_animation.render_relics_for_animation(animation)

        self.assertEqual(render_states[0].position_nd, (2.0, 2.0, 2.0, 0.0))
        self.assertEqual(render_states[1].position_nd, (2.0, 2.0, 2.0, 2.0))

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
                self.assertEqual(len(loop.endgame_animation.cell_relics), len(cells))
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
        self.assertEqual(len(loop_3d.endgame_animation.cell_relics), 3)
        self.assertGreater(len(loop_3d.endgame_animation.shell_fragments), 0)


if __name__ == "__main__":
    unittest.main()
