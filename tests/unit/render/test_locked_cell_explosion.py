from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pygame

from tet4d.engine.ui_logic.view_modes import GridMode, ShadowMode
from tet4d.engine.topology_explorer.glue_model import BoundaryRef
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    explorer_preset_sections_for_dimension,
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
    EXPLOSION_TRAIL_MAX_LIFETIME_MS,
    EXPLOSION_TRAIL_MAX_SAMPLES,
    EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING,
    EXPLOSION_TRAIL_MIN_TIME_SPACING_MS,
    EXPLOSION_TRAIL_RETENTION_MAX_MS,
    EXPLOSION_TRAIL_RETENTION_MIN_MS,
    ExplosionSeedCell,
    ExplosionTrailSample,
    ExplosionTopologyInput,
    StandaloneExplosionConfig,
    build_locked_cell_explosion,
)
from tet4d.ui.pygame.locked_cell_explosion.audio import aggregate_audio_events
from tet4d.ui.pygame.locked_cell_explosion import board_view as explosion_board_view
from tet4d.ui.pygame.locked_cell_explosion import launcher as explosion_launcher
from tet4d.ui.pygame.locked_cell_explosion import surface as explosion_surface
from tet4d.ui.pygame.projection3d import box_raw_corners
from tet4d.ui.pygame.render.active_piece_projection_guides import (
    build_boundary_projection_face_primitives,
    build_boundary_projection_segments_2d,
    boundary_targets_for_mode,
)
from tet4d.ui.pygame.render.board_boundary import board_boundary_coordinate
from tet4d.ui.pygame.render.grid_mode_render import build_projected_grid_primitives
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

    def test_trail_sample_history_is_capped(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                board_dims=(20, 20),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
            )
        )
        particle = controller.simulation.particles[0]
        particle.velocity_nd = (6.0, 0.0)
        controller.simulation.particles[1].active = False

        for _ in range(80):
            controller.step(40.0)

        self.assertLessEqual(len(particle.trail_samples), EXPLOSION_TRAIL_MAX_SAMPLES)

    def test_trail_contract_is_longer_but_still_bounded(self) -> None:
        self.assertGreater(EXPLOSION_TRAIL_MAX_LIFETIME_MS, 1000.0)
        self.assertGreater(EXPLOSION_TRAIL_MAX_SAMPLES, 18)

        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                board_dims=(120, 20),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
            )
        )
        particle = controller.simulation.particles[0]
        controller.simulation.particles[1].active = False
        particle.velocity_nd = (6.0, 0.0)

        for _ in range(24):
            controller.step(40.0)

        self.assertGreater(len(particle.trail_samples), 18)
        self.assertLessEqual(len(particle.trail_samples), EXPLOSION_TRAIL_MAX_SAMPLES)

    def test_trace_retention_setting_controls_lifetime_and_sample_budget(self) -> None:
        config = replace(
            self._config(dimension=2),
            trace_retention_ms=EXPLOSION_TRAIL_RETENTION_MAX_MS,
        )
        controller = build_locked_cell_explosion(config)
        particle = controller.simulation.particles[0]

        self.assertEqual(particle.trail_max_lifetime_ms, EXPLOSION_TRAIL_RETENTION_MAX_MS)
        self.assertGreater(particle.trail_max_samples, EXPLOSION_TRAIL_MAX_SAMPLES)

    def test_old_trail_samples_expire(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                board_dims=(20, 20),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
            )
        )
        particle = controller.simulation.particles[0]
        particle.velocity_nd = (6.0, 0.0)
        controller.simulation.particles[1].active = False

        for _ in range(68):
            controller.step(40.0)

        self.assertTrue(particle.trail_samples)
        self.assertGreater(controller.elapsed_ms, EXPLOSION_TRAIL_MAX_LIFETIME_MS)
        self.assertGreaterEqual(
            min(sample.elapsed_ms for sample in particle.trail_samples),
            controller.elapsed_ms - EXPLOSION_TRAIL_MAX_LIFETIME_MS,
        )

    def test_trail_sampling_respects_time_and_movement_spacing(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                board_dims=(20, 20),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
            )
        )
        particle = controller.simulation.particles[0]
        controller.simulation.particles[1].active = False
        particle.velocity_nd = (
            (EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING * 0.05)
            / (EXPLOSION_TRAIL_MIN_TIME_SPACING_MS / 1000.0),
            0.0,
        )

        for _ in range(8):
            controller.step(EXPLOSION_TRAIL_MIN_TIME_SPACING_MS)

        self.assertEqual(len(particle.trail_samples), 1)

        particle.velocity_nd = (
            (EXPLOSION_TRAIL_MIN_MOVEMENT_SPACING * 1.25)
            / (EXPLOSION_TRAIL_MIN_TIME_SPACING_MS / 1000.0),
            0.0,
        )
        controller.step(EXPLOSION_TRAIL_MIN_TIME_SPACING_MS)

        self.assertGreater(len(particle.trail_samples), 1)

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

    def test_seam_crossing_inserts_trail_segment_break(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
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
        particle.trail_samples = (
            [
                ExplosionTrailSample(
                    position_nd=(3.4, 1.5),
                    elapsed_ms=0.0,
                )
            ]
        )
        controller.simulation.particles[1].active = False

        controller.step(200.0)

        self.assertTrue(any(sample.segment_break for sample in particle.trail_samples))

    def test_trail_primitives_are_projected_in_2d_3d_and_4d(self) -> None:
        render_context_4d = SimpleNamespace(
            basis_axis_map=((0, 1), (1, 1), (2, 1), (3, 1)),
            layer_count=4,
            w_movement_animation_style="fade",
        )
        for dimension in (2, 3, 4):
            with self.subTest(dimension=dimension):
                controller = build_locked_cell_explosion(
                    self._config(
                        dimension=dimension,
                        board_dims=tuple(8 for _ in range(dimension)),
                        boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                    )
                )
                particle = controller.simulation.particles[0]
                controller.simulation.particles[1].active = False
                particle.velocity_nd = tuple(
                    4.0 if axis == 0 else 0.0 for axis in range(dimension)
                )
                for _ in range(4):
                    controller.step(40.0)
                rendered = controller.render_particles(
                    render_context=(render_context_4d if dimension == 4 else None)
                )

                self.assertTrue(rendered[0].trail_segments)
                self.assertEqual(
                    rendered[0].trail_segments[-1].head_render_position,
                    rendered[0].render_position,
                )
                if dimension == 4:
                    self.assertTrue(rendered[0].trail_segments[-1].head_layer_weights)

    def test_4d_box_size_render_reuses_layer_scale_behavior(self) -> None:
        render_context_4d = SimpleNamespace(
            basis_axis_map=((0, 1), (1, 1), (2, 1), (3, 1)),
            layer_count=4,
            w_movement_animation_style="box_size",
        )
        controller = build_locked_cell_explosion(
            self._config(
                dimension=4,
                board_dims=(8, 8, 8, 4),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
            )
        )
        particle = controller.simulation.particles[0]
        controller.simulation.particles[1].active = False
        particle.position_nd = (1.0, 1.0, 1.0, 1.5)

        rendered = controller.render_particles(render_context=render_context_4d)[0]

        self.assertEqual(rendered.layer_weights, ((1, 0.5), (2, 0.5)))
        self.assertEqual(rendered.layer_scales, ((1, 0.5), (2, 0.5)))

    def test_trail_taper_and_fade_increase_toward_head(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
                board_dims=(20, 20),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
            )
        )
        particle = controller.simulation.particles[0]
        controller.simulation.particles[1].active = False
        particle.velocity_nd = (6.0, 0.0)

        for _ in range(6):
            controller.step(40.0)

        rendered = controller.render_particles(render_context=None)[0]
        alphas = [segment.alpha for segment in rendered.trail_segments]
        widths = [segment.width for segment in rendered.trail_segments]

        self.assertGreater(len(alphas), 1)
        self.assertEqual(alphas, sorted(alphas))
        self.assertEqual(widths, sorted(widths))

    def test_trail_segments_do_not_span_wrap_seam_jumps(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=2,
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
        particle.trail_samples = (
            [
                ExplosionTrailSample(
                    position_nd=(3.4, 1.5),
                    elapsed_ms=0.0,
                )
            ]
        )
        controller.simulation.particles[1].active = False

        controller.step(200.0)

        rendered = controller.render_particles(render_context=None)[0]
        self.assertTrue(rendered.trail_segments)
        self.assertTrue(
            all(
                abs(segment.head_position_nd[0] - segment.tail_position_nd[0]) < 2.0
                for segment in rendered.trail_segments
            )
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

    def test_bounce_containment_keeps_particles_inside_board_in_2d_3d_and_4d(self) -> None:
        for dimension in (2, 3, 4):
            with self.subTest(dimension=dimension):
                dims = tuple(4 for _ in range(dimension))
                controller = build_locked_cell_explosion(
                    self._config(
                        dimension=dimension,
                        board_dims=dims,
                        boundary_response=EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                        particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_OFF,
                    )
                )
                particle = controller.simulation.particles[0]
                controller.simulation.particles[1].active = False
                particle.position_nd = tuple(
                    3.4 if axis == 0 else 1.5 for axis in range(dimension)
                )
                particle.velocity_nd = tuple(
                    2.0 if axis == 0 else 0.0 for axis in range(dimension)
                )

                controller.step(55.0)

                for axis, size in enumerate(dims):
                    self.assertGreaterEqual(particle.position_nd[axis], -0.5)
                    self.assertLessEqual(particle.position_nd[axis], float(size) - 0.5)

    def test_bounce_contact_stays_on_true_boundary_in_2d_3d_and_4d(self) -> None:
        for dimension in (2, 3, 4):
            with self.subTest(dimension=dimension):
                controller = build_locked_cell_explosion(
                    self._config(
                        dimension=dimension,
                        board_dims=tuple(4 for _ in range(dimension)),
                        boundary_response=EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                        particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_OFF,
                    )
                )
                particle = controller.simulation.particles[0]
                controller.simulation.particles[1].active = False
                particle.position_nd = tuple(
                    3.4 if axis == 0 else 1.5 for axis in range(dimension)
                )
                particle.velocity_nd = tuple(
                    2.0 if axis == 0 else 0.0 for axis in range(dimension)
                )

                controller.step(55.0)

                self.assertLess(particle.position_nd[0], 3.5)
                self.assertLess(particle.velocity_nd[0], 0.0)

    def test_boundary_targets_reuse_true_boundary_coordinates_in_2d_3d_and_4d(self) -> None:
        for dims in ((4, 5), (4, 5, 6), (4, 5, 6, 7)):
            with self.subTest(dims=dims):
                all_targets = boundary_targets_for_mode(
                    dims=dims,
                    gravity_axis=1,
                    grid_mode=GridMode.ALL_BOUNDARIES,
                )
                self.assertEqual(len(all_targets), len(dims) * 2)
                for target in all_targets:
                    self.assertEqual(
                        target.coordinate,
                        board_boundary_coordinate(
                            dims=dims,
                            axis=target.axis,
                            side=target.side,
                        ),
                    )

                bottom_target = boundary_targets_for_mode(
                    dims=dims,
                    gravity_axis=1,
                    grid_mode=GridMode.BOTTOM_BOUNDARY,
                )
                self.assertEqual(len(bottom_target), 1)
                self.assertEqual(bottom_target[0].axis, 1)
                self.assertEqual(bottom_target[0].side, "+")
                self.assertEqual(
                    bottom_target[0].coordinate,
                    board_boundary_coordinate(dims=dims, axis=1, side="+"),
                )

    def test_seam_transport_contact_stays_on_true_boundary_in_2d_3d_and_4d(self) -> None:
        for dimension in (2, 3, 4):
            with self.subTest(dimension=dimension):
                controller = build_locked_cell_explosion(
                    self._config(
                        dimension=dimension,
                        topology=ExplosionTopologyInput(
                            board_dims=tuple(4 for _ in range(dimension)),
                            explorer_topology_profile=axis_wrap_profile(
                                dimension=dimension,
                                wrapped_axes=(0,),
                            ),
                        ),
                    )
                )
                particle = controller.simulation.particles[0]
                controller.simulation.particles[1].active = False
                particle.position_nd = tuple(
                    3.4 if axis == 0 else 1.5 for axis in range(dimension)
                )
                particle.velocity_nd = tuple(
                    2.0 if axis == 0 else 0.0 for axis in range(dimension)
                )

                controller.step(55.0)

                seam_positions = [
                    round(float(sample.position_nd[0]), 6)
                    for sample in particle.trail_samples
                ]
                self.assertIn(3.5, seam_positions)
                self.assertIn(-0.5, seam_positions)
                self.assertLess(particle.position_nd[0], -0.48)
                self.assertGreater(particle.velocity_nd[0], 0.0)

    def test_3d_bounce_preserves_kinetic_energy_within_tolerance(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=3,
                board_dims=(4, 4, 4),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_BOUNCE,
                particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_OFF,
            )
        )
        particle = controller.simulation.particles[0]
        controller.simulation.particles[1].active = False
        particle.position_nd = (3.4, 1.5, 1.5)
        particle.velocity_nd = (2.0, 0.25, -0.5)
        initial = 0.5 * particle.collision_mass * (
            (2.0 * 2.0) + (0.25 * 0.25) + (0.5 * 0.5)
        )

        controller.step(55.0)

        self.assertAlmostEqual(controller.total_kinetic_energy, initial, delta=1e-6)

    def test_3d_particle_collision_preserves_kinetic_energy_within_tolerance(self) -> None:
        controller = build_locked_cell_explosion(
            self._config(
                dimension=3,
                board_dims=(6, 6, 6),
                boundary_response=EXPLOSION_BOUNDARY_RESPONSE_ESCAPE,
                particle_collisions=EXPLOSION_PARTICLE_COLLISIONS_ON,
            )
        )
        left, right = controller.simulation.particles
        left.position_nd = (2.2, 3.0, 3.0)
        left.velocity_nd = (1.0, 0.0, 0.0)
        left.collision_radius = 0.6
        left.collision_mass = 1.0
        right.position_nd = (3.0, 3.0, 3.0)
        right.velocity_nd = (-1.0, 0.0, 0.0)
        right.collision_radius = 0.6
        right.collision_mass = 1.0
        initial = 1.0

        controller.step(1.0)

        self.assertAlmostEqual(controller.total_kinetic_energy, initial, delta=1e-6)

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

    def test_connected_seam_velocity_transform_preserves_norm(self) -> None:
        profile = mobius_strip_profile_2d()
        dims = (5, 4)
        resolver = build_explorer_transport_resolver(profile, dims)
        adapter = build_explosion_topology_adapter(
            ExplosionTopologyInput(
                board_dims=dims,
                explorer_transport=resolver,
            )
        )
        seam = adapter.seam_for_boundary(next(iter(resolver.directed_seams)).source_boundary)
        assert seam is not None
        velocity = (1.25, -0.75)

        resolved_velocity = seam.transform_velocity(velocity)

        self.assertAlmostEqual(
            sum(component * component for component in resolved_velocity),
            sum(component * component for component in velocity),
            delta=1e-9,
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

    def test_standalone_surface_reuses_grouped_preset_authority(self) -> None:
        flattened = tuple(
            preset
            for section in explorer_preset_sections_for_dimension(4)
            for preset in section.presets
        )

        self.assertEqual(
            explosion_launcher._preset_options_for_dimension(4),
            flattened,
        )

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
            patch.object(explosion_surface, "_draw_native_board_preview") as draw_native,
            patch.object(
                explosion_surface,
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
                    explosion_surface._draw_simulation_scene(
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
            patch.object(explosion_surface, "_draw_native_board_preview") as draw_native,
            patch.object(
                explosion_surface,
                "_draw_projection_reference_scene",
            ) as draw_projection,
        ):
            explosion_surface._draw_simulation_scene(
                object(),
                fonts=object(),
                area=pygame.Rect(0, 0, 320, 240),
                controller=None,
                state=state,
            )

        self.assertFalse(draw_native.called)
        self.assertTrue(draw_projection.called)

    def test_trace_toggle_routes_to_native_board_preview(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        state.trace_enabled = True
        state.grid_mode = GridMode.FULL
        state.shadow_mode = ShadowMode.ALL_BOUNDARIES

        with patch.object(explosion_surface, "draw_native_board_view") as draw_board:
            explosion_surface._draw_native_board_preview(
                pygame.Surface((640, 480)),
                fonts=self._fonts(),
                area=pygame.Rect(0, 0, 320, 240),
                controller=None,
                state=state,
            )

        self.assertTrue(draw_board.called)
        self.assertTrue(draw_board.call_args.kwargs["show_trace"])
        self.assertEqual(draw_board.call_args.kwargs["grid_mode"], GridMode.FULL)
        self.assertEqual(draw_board.call_args.kwargs["shadow_mode"], ShadowMode.ALL_BOUNDARIES)

    def test_4d_w_movement_animation_routes_to_native_board_preview(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)
        state.w_movement_animation_style = explosion_launcher._W_MOVEMENT_ANIMATION_BOX_SIZE

        with patch.object(explosion_surface, "draw_native_board_view") as draw_board:
            explosion_surface._draw_native_board_preview(
                pygame.Surface((640, 480)),
                fonts=self._fonts(),
                area=pygame.Rect(0, 0, 320, 240),
                controller=None,
                state=state,
            )

        self.assertEqual(
            draw_board.call_args.kwargs["w_movement_animation_style"],
            explosion_launcher._W_MOVEMENT_ANIMATION_BOX_SIZE,
        )

    def test_trace_toggle_routes_to_projection_reference_scene(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)
        state.trace_enabled = True

        with patch.object(explosion_surface, "_draw_scene_4d") as draw_scene:
            explosion_surface._draw_projection_reference_scene(
                pygame.Surface((640, 480)),
                fonts=self._fonts(),
                area=pygame.Rect(0, 0, 320, 240),
                controller=None,
                state=state,
            )

        self.assertTrue(draw_scene.called)
        self.assertTrue(draw_scene.call_args.kwargs["explosion_trace_enabled"])

    def test_numeric_rows_use_shared_numeric_control_kind(self) -> None:
        self.assertEqual(explosion_launcher._row_control_kind("trace_retention"), "numeric")
        self.assertEqual(explosion_launcher._row_control_kind("seed"), "numeric")
        self.assertEqual(explosion_launcher._row_control_kind("cell_x"), "numeric")
        self.assertEqual(explosion_launcher._row_control_kind("grid_mode"), "dropdown")
        self.assertEqual(explosion_launcher._row_control_kind("shadow_mode"), "dropdown")
        self.assertEqual(explosion_launcher._row_control_kind("boundary_response"), "dropdown")

    def test_trace_retention_adjustment_updates_live_controller_budget(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        before = state.controller.simulation.particles[0].trail_max_samples

        changed = explosion_launcher._adjust_simulation_row(
            state,
            row_key="trace_retention",
            step=1,
        )

        self.assertTrue(changed)
        self.assertGreater(state.trace_retention_ms, EXPLOSION_TRAIL_MAX_LIFETIME_MS)
        self.assertGreater(
            state.controller.simulation.particles[0].trail_max_samples,
            before,
        )

    def test_trace_retention_is_clamped_to_bounded_range(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=2)
        state.trace_retention_ms = EXPLOSION_TRAIL_RETENTION_MIN_MS

        explosion_launcher._adjust_simulation_row(
            state,
            row_key="trace_retention",
            step=-100,
        )

        self.assertEqual(state.trace_retention_ms, EXPLOSION_TRAIL_RETENTION_MIN_MS)

    def test_trace_retention_text_input_commits_and_clamps(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        state.trace_retention_input_text = "999.00"

        changed = explosion_launcher._commit_trace_retention_input(state)

        self.assertTrue(changed)
        self.assertEqual(state.trace_retention_ms, EXPLOSION_TRAIL_RETENTION_MAX_MS)
        self.assertEqual(
            state.trace_retention_input_text,
            f"{EXPLOSION_TRAIL_RETENTION_MAX_MS / 1000.0:.2f}",
        )

    def test_trace_retention_text_input_invalid_value_is_safe(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        original_ms = state.trace_retention_ms
        original_text = state.trace_retention_input_text
        state.trace_retention_input_text = "abc"

        changed = explosion_launcher._commit_trace_retention_input(state)

        self.assertFalse(changed)
        self.assertEqual(state.trace_retention_ms, original_ms)
        self.assertEqual(state.trace_retention_input_text, original_text)
        self.assertTrue(state.status_error)

    def test_seed_numeric_text_entry_commits(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)

        started = explosion_launcher._start_numeric_text_mode(state, "seed", incoming_text="42")
        changed = explosion_launcher._commit_numeric_text_mode(state)

        self.assertTrue(started)
        self.assertTrue(changed)
        self.assertEqual(state.seed, 42)

    def test_seed_slider_mouse_drag_updates_value(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        screen = pygame.Surface((960, 720))
        fonts = self._fonts()
        layout = explosion_launcher._surface_layout(
            screen_size=screen.get_size(),
            fonts=fonts,
            state=state,
        )
        row_layouts, row_rects = explosion_surface._interactive_row_geometry(
            state,
            layout=layout,
            fonts=fonts,
        )
        seed_index = next(
            index for index, row in enumerate(row_layouts) if row.row_key == "seed"
        )
        state.selected_index = seed_index
        row_layouts, row_rects = explosion_surface._interactive_row_geometry(
            state,
            layout=layout,
            fonts=fonts,
        )
        slider_rect = explosion_surface._slider_rect_for_row(
            row_rects[seed_index],
            row_layouts[seed_index],
        )
        assert slider_rect is not None

        down_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (slider_rect.right - 1, slider_rect.centery)},
        )
        move_event = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (slider_rect.right - 1, slider_rect.centery)},
        )
        up_event = pygame.event.Event(
            pygame.MOUSEBUTTONUP,
            {"button": 1, "pos": (slider_rect.right - 1, slider_rect.centery)},
        )

        with patch("pygame.event.get", return_value=[down_event, move_event, up_event]):
            self.assertTrue(
                explosion_surface._process_launcher_events(
                    state,
                    screen=screen,
                    fonts=fonts,
                )
            )

        self.assertGreaterEqual(state.seed, 9990)

    def test_3d_camera_keys_route_through_shared_scene_camera_controls(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        camera_module = SimpleNamespace(handle_scene_camera_key=Mock(return_value=True))

        with patch.object(
            explosion_surface,
            "_camera_controls_module",
            return_value=camera_module,
        ):
            explosion_surface._handle_launcher_keydown(state, pygame.K_q)

        camera_module.handle_scene_camera_key.assert_called_once_with(
            3,
            pygame.K_q,
            state.camera_3d,
        )

    def test_4d_camera_mouse_routes_through_shared_scene_camera_controls(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)
        screen = pygame.Surface((960, 720))
        fonts = self._fonts()
        real_camera_module = explosion_launcher._camera_controls_module()
        layout = explosion_launcher._surface_layout(
            screen_size=screen.get_size(),
            fonts=fonts,
            state=state,
        )
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 3, "pos": layout.preview_scene_rect.center},
        )

        with (
            patch("pygame.event.get", return_value=[event]),
            patch.object(
                explosion_surface,
                "_camera_controls_module",
                return_value=SimpleNamespace(
                    ensure_scene_camera=real_camera_module.ensure_scene_camera,
                    ensure_mouse_orbit_state=real_camera_module.ensure_mouse_orbit_state,
                    handle_scene_camera_mouse_event=Mock(return_value=True)
                ),
            ) as camera_module_factory,
        ):
            self.assertTrue(
                explosion_surface._process_launcher_events(
                    state,
                    screen=screen,
                    fonts=fonts,
                )
            )

        camera_module_factory.return_value.handle_scene_camera_mouse_event.assert_called_once_with(
            4,
            event,
            state.view_4d,
            state.mouse_orbit,
        )

    def test_native_board_view_draws_trace_lines_only_when_enabled(self) -> None:
        surface = pygame.Surface((320, 240), pygame.SRCALPHA)
        particle = SimpleNamespace(
            source_coord=(0, 0),
            render_position=(1.25, 1.5, 0.0),
            rotation_deg=(0.0, 0.0, 0.0),
            color_id=2,
        )
        controller = SimpleNamespace(
            render_particles=lambda *, render_context: (particle,),
        )

        with patch("tet4d.ui.pygame.locked_cell_explosion.board_view.pygame.draw.line") as draw_line:
            explosion_board_view.draw_native_board_view(
                surface,
                rect=pygame.Rect(0, 0, 320, 240),
                fonts=self._fonts(),
                controller=controller,
                dimension=2,
                board_dims=(4, 4),
                show_trace=False,
            )
            without_trace = draw_line.call_count

        with patch("tet4d.ui.pygame.locked_cell_explosion.board_view.pygame.draw.line") as draw_line:
            explosion_board_view.draw_native_board_view(
                surface,
                rect=pygame.Rect(0, 0, 320, 240),
                fonts=self._fonts(),
                controller=controller,
                dimension=2,
                board_dims=(4, 4),
                show_trace=True,
            )
            with_trace = draw_line.call_count

        self.assertGreater(with_trace, without_trace)

    def test_grid_mode_row_cycles_without_restart(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)

        changed = explosion_launcher._adjust_simulation_row(
            state,
            row_key="grid_mode",
            step=1,
        )

        self.assertTrue(changed)
        self.assertEqual(state.grid_mode, GridMode.EDGE)
        self.assertFalse(explosion_launcher._requires_restart_for_row("grid_mode"))

    def test_grid_dropdown_uses_none_edge_full_options(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)

        options = explosion_launcher._dropdown_values_for_row(state, "grid_mode")

        self.assertEqual(
            options,
            (
                ("off", "NONE"),
                ("edge", "EDGE"),
                ("full", "FULL"),
            ),
        )

    def test_edge_grid_emits_boundary_only_projected_primitives(self) -> None:
        primitives = build_projected_grid_primitives(
            dims=(4, 4, 4),
            grid_mode=GridMode.EDGE,
            project_raw=lambda raw: (raw[0], raw[1]),
            transform_raw=lambda raw: raw,
            depth_denominator=lambda depth: 1.0 + depth,
        )
        full_primitives = build_projected_grid_primitives(
            dims=(4, 4, 4),
            grid_mode=GridMode.FULL,
            project_raw=lambda raw: (raw[0], raw[1]),
            transform_raw=lambda raw: raw,
            depth_denominator=lambda depth: 1.0 + depth,
        )

        self.assertTrue(primitives)
        self.assertNotEqual(primitives, full_primitives)
        self.assertTrue(any(fragment.source_type == "gridline" for fragment in primitives))
        self.assertTrue(any(fragment.source_type == "box_edge" for fragment in primitives))

    def test_projected_box_and_edge_grid_share_canonical_boundary_coordinates(self) -> None:
        dims = (4, 5, 6)
        expected = {
            board_boundary_coordinate(dims=dims, axis=axis, side=side)
            for axis in range(3)
            for side in ("-", "+")
        }

        corners = box_raw_corners(dims)
        corner_values = {coordinate for corner in corners for coordinate in corner}
        self.assertTrue(expected.issubset(corner_values))
        guide_faces = build_boundary_projection_face_primitives(
            cells=(((1.25, 2.0, 3.5), 0.9),),
            dims=dims,
            gravity_axis=1,
            grid_mode=GridMode.ALL_BOUNDARIES,
            project_raw=lambda raw: (raw[0], raw[1]),
            transform_raw=lambda raw: raw,
            depth_denominator=lambda depth: 1.0 + depth,
            color=(255, 0, 0),
        )
        face_values = {
            float(value)
            for primitive in guide_faces
            for point in primitive.polygon
            for value in point
        }
        self.assertTrue(expected.intersection(face_values))

    def test_2d_projection_segments_use_canonical_boundary_coordinates(self) -> None:
        dims = (4, 5)
        segments = build_boundary_projection_segments_2d(
            cells=(((1.25, 2.0), 0.9),),
            dims=dims,
            gravity_axis=1,
            grid_mode=GridMode.ALL_BOUNDARIES,
            color=(255, 0, 0),
        )
        coordinates = {
            round(float(value), 6)
            for segment in segments
            for value in (
                segment.start[segment.axis],
                segment.end[segment.axis],
            )
        }
        expected = {
            round(board_boundary_coordinate(dims=dims, axis=axis, side=side), 6)
            for axis in range(2)
            for side in ("-", "+")
        }
        self.assertEqual(coordinates, expected)

    def test_2d_edge_grid_is_distinct_from_none_and_full(self) -> None:
        surface = pygame.Surface((320, 240), pygame.SRCALPHA)
        line_calls: list[tuple[tuple[int, int], tuple[int, int]]] = []

        def record_line(_surface, _color, start, end, _width=1):
            line_calls.append((tuple(start), tuple(end)))

        with patch("tet4d.ui.pygame.locked_cell_explosion.board_view.pygame.draw.line", side_effect=record_line):
            explosion_board_view._draw_2d_grid(
                surface,
                board_rect=pygame.Rect(20, 20, 80, 80),
                cell_size=20.0,
                width_cells=4,
                height_cells=4,
                grid_mode=GridMode.EDGE,
            )
        edge_calls = len(line_calls)
        line_calls.clear()
        with patch("tet4d.ui.pygame.locked_cell_explosion.board_view.pygame.draw.line", side_effect=record_line):
            explosion_board_view._draw_2d_grid(
                surface,
                board_rect=pygame.Rect(20, 20, 80, 80),
                cell_size=20.0,
                width_cells=4,
                height_cells=4,
                grid_mode=GridMode.FULL,
            )
        full_calls = len(line_calls)

        self.assertGreater(edge_calls, 0)
        self.assertNotEqual(edge_calls, full_calls)

    def test_shadow_mode_row_cycles_without_restart(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)

        changed = explosion_launcher._adjust_simulation_row(
            state,
            row_key="shadow_mode",
            step=1,
        )

        self.assertTrue(changed)
        self.assertEqual(state.shadow_mode, ShadowMode.BOTTOM_BOUNDARY)
        self.assertFalse(explosion_launcher._requires_restart_for_row("shadow_mode"))

    def test_grid_and_shadow_modes_are_independent(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        state.grid_mode = GridMode.OFF
        state.shadow_mode = ShadowMode.ALL_BOUNDARIES

        self.assertEqual(state.grid_mode, GridMode.OFF)
        self.assertEqual(state.shadow_mode, ShadowMode.ALL_BOUNDARIES)

    def test_dropdown_layout_reserves_space_for_affordance(self) -> None:
        fonts = self._fonts()
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)
        state.topology_label_override = (
            "A Very Long Topology Label That Would Previously Sit Under The Dropdown Button"
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
        topology_index = next(
            index for index, row in enumerate(row_layouts) if row.row_key == "topology"
        )
        row_rect = explosion_launcher._row_rects(
            layout=layout,
            row_layouts=row_layouts,
            selected_index=int(state.selected_index),
        )[topology_index]
        topology_row = row_layouts[topology_index]

        self.assertGreaterEqual(
            topology_row.value_right_padding,
            12 + explosion_launcher._DROPDOWN_AFFORDANCE_WIDTH,
        )
        self.assertLess(
            row_rect.right - topology_row.value_right_padding,
            row_rect.right - 12,
        )

    def test_mouse_click_opens_dropdown_and_selects_option(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        screen = pygame.Surface((960, 720))
        fonts = self._fonts()
        layout = explosion_launcher._surface_layout(
            screen_size=screen.get_size(),
            fonts=fonts,
            state=state,
        )
        row_layouts = explosion_launcher._build_row_layouts(
            state,
            fonts,
            panel_width=layout.left_rect.width,
        )
        grid_index = next(
            index for index, row in enumerate(row_layouts) if row.row_key == "grid_mode"
        )
        row_rect = explosion_launcher._row_rects(
            layout=layout,
            row_layouts=row_layouts,
            selected_index=int(state.selected_index),
        )[grid_index]
        menu_rect = explosion_launcher._dropdown_menu_rect(
            row_rect,
            option_count=len(explosion_launcher._dropdown_values_for_row(state, "grid_mode")),
            viewport=layout.row_viewport,
            font=fonts.menu_font,
        )
        option_height = fonts.menu_font.get_height() + 10
        select_pos = (
            menu_rect.centerx,
            menu_rect.y + 4 + option_height + option_height // 2,
        )
        open_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": row_rect.center},
        )
        select_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": select_pos},
        )

        with patch("pygame.event.get", return_value=[open_event, select_event]):
            self.assertTrue(
                explosion_surface._process_launcher_events(
                    state,
                    screen=screen,
                    fonts=fonts,
                )
            )

        self.assertEqual(state.grid_mode, GridMode.EDGE)
        self.assertIsNone(state.open_dropdown_row_key)

    def test_dropdown_hover_and_click_outside_close(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=3)
        screen = pygame.Surface((960, 720))
        fonts = self._fonts()
        layout = explosion_launcher._surface_layout(
            screen_size=screen.get_size(),
            fonts=fonts,
            state=state,
        )
        row_layouts, row_rects = explosion_surface._interactive_row_geometry(
            state,
            layout=layout,
            fonts=fonts,
        )
        grid_index = next(
            index for index, row in enumerate(row_layouts) if row.row_key == "grid_mode"
        )
        row_rect = row_rects[grid_index]
        state.selected_index = grid_index
        state.open_dropdown_row_key = "grid_mode"
        menu_rect = explosion_launcher._dropdown_menu_rect(
            row_rect,
            option_count=len(explosion_launcher._dropdown_values_for_row(state, "grid_mode")),
            viewport=layout.row_viewport,
            font=fonts.menu_font,
        )
        hover_pos = (menu_rect.centerx, menu_rect.y + 8)
        move_event = pygame.event.Event(pygame.MOUSEMOTION, {"pos": hover_pos})
        outside_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (layout.right_rect.centerx, layout.right_rect.centery)},
        )

        with patch("pygame.event.get", return_value=[move_event, outside_event]):
            self.assertTrue(
                explosion_surface._process_launcher_events(
                    state,
                    screen=screen,
                    fonts=fonts,
                )
            )

        self.assertEqual(state.dropdown_hover_index, 0)
        self.assertIsNone(state.open_dropdown_row_key)

    def test_dropdown_wheel_scroll_updates_visible_slice(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)
        screen = pygame.Surface((960, 720))
        fonts = self._fonts()
        state.selected_index = 1
        state.open_dropdown_row_key = "topology"
        wheel_event = pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1})

        with patch("pygame.event.get", return_value=[wheel_event]):
            self.assertTrue(
                explosion_surface._process_launcher_events(
                    state,
                    screen=screen,
                    fonts=fonts,
                )
            )

        self.assertGreaterEqual(state.dropdown_scroll_offset, 1)

    def test_4d_w_movement_animation_row_is_available_and_cycles(self) -> None:
        state = explosion_launcher.build_standalone_explosion_surface_state(dimension=4)

        self.assertIn("w_movement_animation", explosion_launcher._dynamic_row_keys(state))
        changed = explosion_launcher._adjust_simulation_row(
            state,
            row_key="w_movement_animation",
            step=1,
        )

        self.assertTrue(changed)
        self.assertEqual(
            state.w_movement_animation_style,
            explosion_launcher._W_MOVEMENT_ANIMATION_BOX_SIZE,
        )

    def test_native_board_view_uses_projected_occlusion_for_3d_and_4d(self) -> None:
        surface = pygame.Surface((320, 240), pygame.SRCALPHA)
        for dimension in (3, 4):
            with self.subTest(dimension=dimension):
                particle = SimpleNamespace(
                    source_coord=tuple(0 for _ in range(dimension)),
                    render_position=(1.25, 1.5, 1.0),
                    rotation_deg=(0.0, 0.0, 0.0),
                    alpha=1.0,
                    color_id=2,
                    layer_weights=((1, 1.0),) if dimension == 4 else (),
                )
                controller = SimpleNamespace(
                    render_particles=lambda *, render_context, _particle=particle: (_particle,),
                )
                with patch(
                    "tet4d.ui.pygame.locked_cell_explosion.board_view.resolve_board_line_occlusion"
                ) as resolve_occlusion:
                    explosion_board_view.draw_native_board_view(
                        surface,
                        rect=pygame.Rect(0, 0, 320, 240),
                        fonts=self._fonts(),
                        controller=controller,
                        dimension=dimension,
                        board_dims=tuple(4 for _ in range(dimension)),
                        show_trace=False,
                        grid_mode=GridMode.FULL,
                        shadow_mode=ShadowMode.OFF,
                    )
                self.assertTrue(resolve_occlusion.called)

    def test_shadow_modes_emit_render_only_boundary_guides_in_2d_3d_and_4d(self) -> None:
        surface = pygame.Surface((320, 240), pygame.SRCALPHA)
        for dimension in (2, 3, 4):
            with self.subTest(dimension=dimension):
                particle = SimpleNamespace(
                    source_coord=tuple(0 for _ in range(dimension)),
                    render_position=(1.25, 1.5, 1.0),
                    rotation_deg=(0.0, 0.0, 0.0),
                    alpha=1.0,
                    color_id=2,
                    layer_weights=((1, 1.0),) if dimension == 4 else (),
                )
                controller = SimpleNamespace(
                    render_particles=lambda *, render_context, _particle=particle: (_particle,),
                )
                patch_target = (
                    "tet4d.ui.pygame.locked_cell_explosion.board_view.draw_boundary_projection_segments_2d"
                    if dimension == 2
                    else "tet4d.ui.pygame.locked_cell_explosion.board_view.draw_boundary_projection_faces"
                )
                with patch(patch_target) as draw_projection:
                    explosion_board_view.draw_native_board_view(
                        surface,
                        rect=pygame.Rect(0, 0, 320, 240),
                        fonts=self._fonts(),
                        controller=controller,
                        dimension=dimension,
                        board_dims=tuple(4 for _ in range(dimension)),
                        show_trace=False,
                        grid_mode=GridMode.OFF,
                        shadow_mode=ShadowMode.BOTTOM_BOUNDARY,
                    )
                    self.assertTrue(draw_projection.called)
                    draw_projection.reset_mock()
                    explosion_board_view.draw_native_board_view(
                        surface,
                        rect=pygame.Rect(0, 0, 320, 240),
                        fonts=self._fonts(),
                        controller=controller,
                        dimension=dimension,
                        board_dims=tuple(4 for _ in range(dimension)),
                        show_trace=False,
                        grid_mode=GridMode.OFF,
                        shadow_mode=ShadowMode.ALL_BOUNDARIES,
                    )
                    self.assertTrue(draw_projection.called)

    def test_grid_only_mode_does_not_emit_shadow_guides(self) -> None:
        surface = pygame.Surface((320, 240), pygame.SRCALPHA)
        particle = SimpleNamespace(
            source_coord=(0, 0, 0),
            render_position=(1.25, 1.5, 1.0),
            rotation_deg=(0.0, 0.0, 0.0),
            alpha=1.0,
            color_id=2,
            layer_weights=(),
        )
        controller = SimpleNamespace(
            render_particles=lambda *, render_context: (particle,),
        )

        with patch(
            "tet4d.ui.pygame.locked_cell_explosion.board_view.draw_boundary_projection_faces"
        ) as draw_projection:
            explosion_board_view.draw_native_board_view(
                surface,
                rect=pygame.Rect(0, 0, 320, 240),
                fonts=self._fonts(),
                controller=controller,
                dimension=3,
                board_dims=(4, 4, 4),
                show_trace=False,
                grid_mode=GridMode.FULL,
                shadow_mode=ShadowMode.OFF,
            )

        self.assertFalse(draw_projection.called)

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
