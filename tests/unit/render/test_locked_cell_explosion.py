from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from tet4d.engine.topology_explorer.glue_model import BoundaryRef
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    explorer_presets_for_dimension,
    mobius_strip_profile_2d,
)
from tet4d.engine.topology_explorer.transport_resolver import (
    build_explorer_transport_resolver,
)
from tet4d.ui.pygame.locked_cell_explosion import (
    EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
    EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
    EXPLOSION_PARTICLE_COLLISIONS_OFF,
    EXPLOSION_PARTICLE_COLLISIONS_ON,
    ExplosionSeedCell,
    ExplosionTopologyInput,
    StandaloneExplosionConfig,
    build_locked_cell_explosion,
)
from tet4d.ui.pygame.locked_cell_explosion.audio import aggregate_audio_events
from tet4d.ui.pygame.locked_cell_explosion import launcher as explosion_launcher
from tet4d.ui.pygame.locked_cell_explosion.model import (
    ExplosionAudioEvent,
    ExplosionAudioState,
)
from tet4d.ui.pygame.locked_cell_explosion.topology import build_explosion_topology_adapter


class TestLockedCellExplosion(unittest.TestCase):
    def _fonts(self):
        pygame.font.init()
        return SimpleNamespace(
            title_font=pygame.font.SysFont(None, 30),
            menu_font=pygame.font.SysFont(None, 22),
            hint_font=pygame.font.SysFont(None, 18),
        )

    def _config(
        self,
        *,
        dimension: int,
        board_dims: tuple[int, ...] | None = None,
        boundary_response: str = EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
        particle_collisions: str = EXPLOSION_PARTICLE_COLLISIONS_OFF,
        topology: ExplosionTopologyInput | None = None,
    ) -> StandaloneExplosionConfig:
        dims = board_dims or tuple(4 for _ in range(dimension))
        return StandaloneExplosionConfig(
            dimension=dimension,
            topology=topology or ExplosionTopologyInput(board_dims=dims),
            occupied_cells=(
                ExplosionSeedCell(
                    source_coord=tuple(1 for _ in range(dimension)),
                    color_id=3,
                ),
                ExplosionSeedCell(
                    source_coord=tuple(
                        2 if axis == 0 else 1 for axis in range(dimension)
                    ),
                    color_id=5,
                ),
            ),
            random_seed=1337,
            boundary_response=boundary_response,
            particle_collisions=particle_collisions,
            speed_preset="normal",
            sound_enabled=True,
        )

    def test_launches_are_deterministic_in_2d_3d_and_4d(self) -> None:
        for dimension in (2, 3, 4):
            with self.subTest(dimension=dimension):
                config = self._config(dimension=dimension)
                controller_a = build_locked_cell_explosion(config)
                controller_b = build_locked_cell_explosion(config)

                controller_a.step(120.0)
                controller_b.step(120.0)

                states_a = tuple(
                    (particle.position_nd, particle.velocity_nd)
                    for particle in controller_a.particles
                )
                states_b = tuple(
                    (particle.position_nd, particle.velocity_nd)
                    for particle in controller_b.particles
                )

                self.assertEqual(states_a, states_b)
                self.assertTrue(
                    any(
                        particle.position_nd
                        != tuple(float(v) for v in particle.source_coord)
                        for particle in controller_a.particles
                    )
                )

    def test_config_matrix_covers_all_boundary_and_collision_combinations(self) -> None:
        expected = {
            (
                EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                EXPLOSION_PARTICLE_COLLISIONS_OFF,
            ),
            (
                EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                EXPLOSION_PARTICLE_COLLISIONS_ON,
            ),
            (
                EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                EXPLOSION_PARTICLE_COLLISIONS_OFF,
            ),
            (
                EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                EXPLOSION_PARTICLE_COLLISIONS_ON,
            ),
        }
        observed = set()
        for boundary_response, particle_collisions in sorted(expected):
            controller = build_locked_cell_explosion(
                self._config(
                    dimension=2,
                    boundary_response=boundary_response,
                    particle_collisions=particle_collisions,
                )
            )
            observed.add(
                (
                    controller.simulation.boundary_response,
                    controller.simulation.particle_collisions,
                )
            )
        self.assertEqual(observed, expected)

    def test_connected_seams_transport_in_all_four_config_combinations(self) -> None:
        combinations = (
            (
                EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                EXPLOSION_PARTICLE_COLLISIONS_OFF,
            ),
            (
                EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                EXPLOSION_PARTICLE_COLLISIONS_ON,
            ),
            (
                EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                EXPLOSION_PARTICLE_COLLISIONS_OFF,
            ),
            (
                EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                EXPLOSION_PARTICLE_COLLISIONS_ON,
            ),
        )
        for boundary_response, particle_collisions in combinations:
            with self.subTest(
                boundary_response=boundary_response,
                particle_collisions=particle_collisions,
            ):
                controller = build_locked_cell_explosion(
                    self._config(
                        dimension=2,
                        boundary_response=boundary_response,
                        particle_collisions=particle_collisions,
                        topology=ExplosionTopologyInput(
                            board_dims=(4, 4),
                            explorer_topology_profile=axis_wrap_profile(
                                dimension=2,
                                wrapped_axes=(0,),
                            ),
                        ),
                    )
                )
                particle = controller.simulation.particles[0]
                particle.position_nd = (3.4, 1.5)
                particle.velocity_nd = (2.0, 0.0)

                events = controller.step(200.0)

                self.assertFalse(particle.escaped)
                self.assertLess(particle.position_nd[0], 1.0)
                self.assertGreater(particle.velocity_nd[0], 0.0)
                self.assertTrue(
                    any(event.startswith("explosion_seam_") for event in events)
                )

    def test_non_connected_escape_boundary_does_not_reflect(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_ON,
            )
        )
        particle = controller.simulation.particles[0]
        particle.position_nd = (3.4, 1.5)
        particle.velocity_nd = (2.0, 0.0)

        controller.step(200.0)

        self.assertTrue(particle.escaped)
        self.assertGreater(particle.position_nd[0], 3.5)
        self.assertGreater(particle.velocity_nd[0], 0.0)

    def test_non_connected_bounce_boundary_reflects(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_OFF,
            )
        )
        particle = controller.simulation.particles[0]
        particle.position_nd = (3.4, 1.5)
        particle.velocity_nd = (2.0, 0.0)
        controller.simulation.particles[1].active = False

        events = controller.step(200.0)

        self.assertFalse(particle.escaped)
        self.assertLess(particle.velocity_nd[0], 0.0)
        self.assertLess(particle.position_nd[0], 3.5)
        self.assertIn("explosion_bounce_soft", events)

    def test_particle_collisions_off_does_not_resolve_particle_particle_contacts(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_OFF,
            )
        )
        left, right = controller.simulation.particles
        left.position_nd = (1.8, 1.5)
        left.velocity_nd = (1.0, 0.0)
        left.collision_radius = 0.6
        right.position_nd = (2.2, 1.5)
        right.velocity_nd = (-1.0, 0.0)
        right.collision_radius = 0.6

        controller.step(0.0)

        self.assertEqual(left.velocity_nd, (1.0, 0.0))
        self.assertEqual(right.velocity_nd, (-1.0, 0.0))
        self.assertLess(abs(right.position_nd[0] - left.position_nd[0]), 1.2)

    def test_particle_collisions_on_resolves_particle_particle_contacts(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_ON,
            )
        )
        left, right = controller.simulation.particles
        left.position_nd = (1.8, 1.5)
        left.velocity_nd = (1.0, 0.0)
        left.collision_radius = 0.6
        right.position_nd = (2.2, 1.5)
        right.velocity_nd = (-1.0, 0.0)
        right.collision_radius = 0.6

        controller.step(180.0)

        self.assertAlmostEqual(
            abs(right.position_nd[0] - left.position_nd[0]),
            left.collision_radius + right.collision_radius,
            places=5,
        )
        self.assertNotEqual(left.velocity_nd, (1.0, 0.0))
        self.assertNotEqual(right.velocity_nd, (-1.0, 0.0))

    def test_connected_seam_transports_position_and_velocity(self) -> None:
        profile = mobius_strip_profile_2d()
        dims = (5, 4)
        build_explosion_transport = build_explorer_transport_resolver(profile, dims)
        adapter = build_explosion_topology_adapter(
            ExplosionTopologyInput(
                board_dims=dims,
                explorer_transport=build_explosion_transport,
            )
        )
        directed_seam = next(iter(build_explosion_transport.directed_seams))
        seam = adapter.seam_for_boundary(directed_seam.source_boundary)
        assert seam is not None
        sample_source, sample_target = directed_seam.boundary_coord_map[0]
        boundary_position = list(float(value) for value in sample_source)
        boundary_position[directed_seam.source_boundary.axis] += (
            0.5 * float(directed_seam.exit_step.delta)
        )
        expected_position = list(float(value) for value in sample_target)
        expected_position[directed_seam.target_boundary.axis] -= (
            0.5 * float(directed_seam.entry_step.delta)
        )
        velocity = (1.25, -0.75)
        expected_velocity = [0.0, 0.0]
        for source_axis, target_axis in enumerate(
            directed_seam.piece_frame_transform.permutation
        ):
            expected_velocity[int(target_axis)] = (
                float(velocity[source_axis])
                * float(directed_seam.piece_frame_transform.signs[source_axis])
            )

        resolved_position = seam.transform_position(tuple(boundary_position))
        resolved_velocity = seam.transform_velocity(velocity)

        self.assertEqual(
            tuple(round(value, 6) for value in resolved_position),
            tuple(round(value, 6) for value in expected_position),
        )
        self.assertEqual(
            tuple(round(value, 6) for value in resolved_velocity),
            tuple(round(value, 6) for value in expected_velocity),
        )

    def test_standalone_surface_uses_explorer_preset_registry_for_topology(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        preset_ids = {
            str(preset.preset_id) for preset in explorer_presets_for_dimension(3)
        }

        self.assertIn(state.topology_preset_id, preset_ids)
        selected = next(
            preset
            for preset in explorer_presets_for_dimension(3)
            if preset.preset_id == state.topology_preset_id
        )
        config = explosion_launcher.build_standalone_explosion_config(state)
        self.assertEqual(config.topology.explorer_topology_profile, selected.profile)

    def test_explorer_seeded_surface_inherits_profile_and_locks_topology_rows(self) -> None:
        profile = axis_wrap_profile(dimension=2, wrapped_axes=(0,))
        seed_cells = (
            explosion_launcher.ExplosionSeedCell(source_coord=(1, 1), color_id=2),
        )

        state = explosion_launcher.build_explorer_explosion_surface_state(
            dimension=2,
            board_dims=(6, 8),
            explorer_profile=profile,
            occupied_cells=seed_cells,
            random_seed=99,
        )

        self.assertEqual(state.topology_profile_override, profile)
        self.assertEqual(state.board_dims_override, (6, 8))
        self.assertEqual(state.occupied_cells_override, seed_cells)
        self.assertEqual(
            state.snapshot_source_id,
            explosion_launcher._SNAPSHOT_SOURCE_INHERITED,
        )
        self.assertTrue(
            {"dimension", "topology", "snapshot_source", "seed"}.issubset(
                state.locked_rows
            )
        )

    def test_simulator_scene_routes_true_board_view_by_default(self) -> None:
        controller = SimpleNamespace(
            particles=(SimpleNamespace(position_nd=(1.0, 1.0, 1.0, 1.0), color_id=2),)
        )

        with (
            patch.object(explosion_launcher, "_draw_native_board_preview") as draw_native,
            patch.object(
                explosion_launcher,
                "_draw_projection_reference_scene",
            ) as draw_projection,
        ):
            for dimension in (2, 3, 4):
                with self.subTest(dimension=dimension):
                    draw_native.reset_mock()
                    draw_projection.reset_mock()
                    state = explosion_launcher.build_standalone_explosion_surface_state(
                        dimension=dimension
                    )
                    explosion_launcher._draw_simulation_scene(
                        object(),
                        fonts=object(),
                        area=pygame.Rect(0, 0, 320, 240),
                        controller=controller,
                        state=state,
                    )
                    self.assertTrue(draw_native.called)
                    self.assertFalse(draw_projection.called)

    def test_projection_reference_mode_uses_projection_scene_route(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)
        state.view_mode = explosion_launcher._VIEW_MODE_PROJECTION_REFERENCE

        with (
            patch.object(explosion_launcher, "_draw_native_board_preview") as draw_native,
            patch.object(
                explosion_launcher,
                "_draw_projection_reference_scene",
            ) as draw_projection,
        ):
            explosion_launcher._draw_simulation_scene(
                object(),
                fonts=object(),
                area=pygame.Rect(0, 0, 320, 240),
                controller=None,
                state=state,
            )

        self.assertFalse(draw_native.called)
        self.assertTrue(draw_projection.called)

    def test_single_cell_snapshot_uses_explicit_coordinate(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        state.snapshot_source_id = explosion_launcher._SNAPSHOT_SOURCE_SINGLE_CELL
        state.cell_origin = (1, 2, 3, 0)

        config = explosion_launcher.build_standalone_explosion_config(state)

        self.assertEqual(
            config.occupied_cells,
            (
                explosion_launcher.ExplosionSeedCell(
                    source_coord=(1, 2, 3),
                    color_id=1,
                    source_group_id="single_cell",
                ),
            ),
        )

    def test_single_piece_snapshot_uses_canonical_piece_definition(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=2)
        state.snapshot_source_id = explosion_launcher._SNAPSHOT_SOURCE_SINGLE_PIECE
        state.piece_set_id = "classic"
        state.piece_shape_name = "O"

        config = explosion_launcher.build_standalone_explosion_config(state)
        origin = explosion_launcher._exploration_spawn_origin(
            ((0, 0), (1, 0), (0, 1), (1, 1)),
            explosion_launcher._board_dims_for_state(state),
        )
        expected = sorted(
            (
                origin[0] + dx,
                origin[1] + dy,
            )
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))
        )

        self.assertEqual(
            sorted(cell.source_coord for cell in config.occupied_cells),
            expected,
        )
        self.assertGreater(len({cell.color_id for cell in config.occupied_cells}), 1)

    def test_piece_change_snapshot_uses_engine_bag_transition(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        state.snapshot_source_id = explosion_launcher._SNAPSHOT_SOURCE_PIECE_CHANGE

        current_shape, next_shape = explosion_launcher._piece_change_shapes_for_state(
            state,
            board_dims=explosion_launcher._board_dims_for_state(state),
        )
        config = explosion_launcher.build_standalone_explosion_config(state)

        self.assertGreaterEqual(len(config.occupied_cells), len(current_shape.blocks))
        self.assertIn("->", explosion_launcher._piece_change_summary_text(state))
        self.assertNotEqual(current_shape.name, "")
        self.assertNotEqual(next_shape.name, "")
        self.assertGreater(len({cell.color_id for cell in config.occupied_cells}), 1)

    def test_total_kinetic_energy_is_available_on_controller(self) -> None:
        controller = build_locked_cell_explosion(self._config(dimension=2))
        initial = controller.total_kinetic_energy

        controller.step(100.0)

        self.assertGreater(initial, 0.0)
        self.assertGreater(controller.total_kinetic_energy, 0.0)

    def test_surface_layout_wraps_long_text_without_overlapping_footer(self) -> None:
        fonts = self._fonts()
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)
        state.snapshot_source_id = explosion_launcher._SNAPSHOT_SOURCE_PIECE_CHANGE
        state.topology_label_override = (
            "Very Long Topology Preset Label Used To Verify Wrapped Layout Behavior"
        )
        state.status = (
            "This is a deliberately long simulator status line that must wrap cleanly "
            "and stay visible above the footer without being obscured by the preview panel."
        )

        layout = explosion_launcher._surface_layout(
            screen_size=(1280, 820),
            fonts=fonts,
            state=state,
        )
        row_layouts = explosion_launcher._build_row_layouts(
            state,
            fonts,
            panel_width=layout.left_rect.width,
        )

        self.assertGreater(len(layout.footer_lines), 2)
        self.assertGreater(len(row_layouts), 0)
        self.assertLess(layout.row_viewport.bottom, layout.footer_rect.bottom)
        self.assertLess(layout.row_viewport.bottom, layout.footer_rect.y)

    def test_wrapped_row_layouts_reserve_distinct_vertical_space(self) -> None:
        fonts = self._fonts()
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        state.snapshot_source_id = explosion_launcher._SNAPSHOT_SOURCE_SINGLE_PIECE
        state.topology_label_override = (
            "An Intentionally Long Topology Label To Force The Wrapped Row Layout Path"
        )

        row_layouts = explosion_launcher._build_row_layouts(
            state,
            fonts,
            panel_width=380,
        )

        row_gap = 6
        running_y = 0
        rects = []
        for layout in row_layouts:
            rect = pygame.Rect(0, running_y, 360, layout.row_height)
            rects.append(rect)
            running_y += layout.row_height + row_gap

        for previous, current in zip(rects, rects[1:]):
            self.assertLessEqual(previous.bottom, current.top)

    def test_audio_aggregation_keeps_seams_audible_under_dense_motion(self) -> None:
        playback = aggregate_audio_events(
            (
                ExplosionAudioEvent(family="collision", strength=1.4),
                ExplosionAudioEvent(family="collision", strength=1.6),
                ExplosionAudioEvent(family="collision", strength=1.9),
                ExplosionAudioEvent(family="collision", strength=2.1),
                ExplosionAudioEvent(family="seam", strength=1.4),
                ExplosionAudioEvent(family="seam", strength=1.1),
            ),
            elapsed_ms=100.0,
            sound_enabled=True,
            state=ExplosionAudioState(),
        )

        self.assertTrue(
            any(event.startswith("explosion_seam_") for event in playback)
        )
        self.assertLessEqual(len(playback), 2)

    def test_audio_aggregation_strongly_caps_dense_collision_windows(self) -> None:
        state = ExplosionAudioState()

        outputs = [
            aggregate_audio_events(
                tuple(
                    ExplosionAudioEvent(family="collision", strength=1.7 + index * 0.1)
                    for index in range(10)
                ),
                elapsed_ms=float(step * 60),
                sound_enabled=True,
                state=state,
            )
            for step in range(10)
        ]

        emitted = [window for window in outputs if window]
        self.assertLessEqual(len(emitted), 3)
        self.assertTrue(
            all(window == ("explosion_collision_cluster",) for window in emitted)
        )

    def test_boundary_adapter_exposes_connected_seams(self) -> None:
        adapter = build_explosion_topology_adapter(
            ExplosionTopologyInput(
                board_dims=(4, 4),
                explorer_topology_profile=axis_wrap_profile(
                    dimension=2,
                    wrapped_axes=(0,),
                ),
            )
        )

        seam = adapter.seam_for_boundary(BoundaryRef(dimension=2, axis=0, side="+"))

        self.assertIsNotNone(seam)
