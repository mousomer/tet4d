from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
)
from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    MoveStep,
)
from tet4d.engine.topology_explorer.presets import (
    projective_plane_profile_2d,
    projective_space_profile_3d,
)
from tet4d.ui.pygame.topology_lab.app import (
    build_explorer_playground_config,
    build_explorer_playground_launch,
    build_explorer_playground_settings,
    mode_settings_snapshot_for_dimension,
)
from tet4d.ui.pygame import frontend_nd_setup
from tet4d.ui.pygame.topology_lab.scene_state import TOOL_EDIT, TOOL_SANDBOX

class TestTopologyLabApp(unittest.TestCase):
    def _invalid_profile_3d(self) -> ExplorerTopologyProfile:
        return ExplorerTopologyProfile(
            dimension=3,
            gluings=(
                GluingDescriptor(
                    glue_id="invalid_dims",
                    source=BoundaryRef(dimension=3, axis=0, side="-"),
                    target=BoundaryRef(dimension=3, axis=1, side="+"),
                    transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                ),
            ),
        )

    def test_build_explorer_launch_defaults_to_sandbox_for_explorer_entry(self) -> None:
        profile = ExplorerTopologyProfile(dimension=3, gluings=())
        launch = build_explorer_playground_launch(
            dimension=3,
            explorer_profile=profile,
        )
        self.assertEqual(launch.dimension, 3)
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_EXPLORER)
        self.assertEqual(launch.initial_tool, TOOL_SANDBOX)
        self.assertEqual(launch.entry_source, "explorer")
        self.assertIs(launch.explorer_profile, profile)

    def test_build_launcher_launch_defaults_to_edit_for_launcher_entry(self) -> None:
        profile = ExplorerTopologyProfile(dimension=4, gluings=())
        launch = build_explorer_playground_launch(
            dimension=4,
            explorer_profile=profile,
            entry_source="launcher",
        )
        self.assertEqual(launch.dimension, 4)
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_EXPLORER)
        self.assertEqual(launch.initial_tool, TOOL_EDIT)
        self.assertEqual(launch.entry_source, "launcher")
        self.assertIs(launch.explorer_profile, profile)

    def test_build_lab_launch_defaults_to_edit_for_lab_entry(self) -> None:
        launch = build_explorer_playground_launch(
            dimension=4,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
            entry_source="lab",
        )
        self.assertEqual(launch.dimension, 4)
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_NORMAL)
        self.assertEqual(launch.initial_tool, TOOL_EDIT)
        self.assertEqual(launch.entry_source, "lab")

    def test_build_explorer_settings_use_compact_under_nine_board_defaults(
        self,
    ) -> None:
        self.assertEqual(
            build_explorer_playground_settings(dimension=2).board_dims,
            (8, 8),
        )
        self.assertEqual(
            build_explorer_playground_settings(dimension=3).board_dims,
            (8, 8, 8),
        )
        self.assertEqual(
            build_explorer_playground_settings(dimension=4).board_dims,
            (8, 8, 8, 8),
        )

    def test_build_explorer_launch_treats_generic_3d_nd_defaults_as_untouched(
        self,
    ) -> None:
        launch = build_explorer_playground_launch(
            dimension=3,
            source_settings=frontend_nd_setup.GameSettingsND(),
        )
        self.assertEqual(launch.settings_snapshot.board_dims, (8, 8, 8))
        self.assertEqual(launch.settings_snapshot.game_seed, 1337)

    def test_build_explorer_launch_uses_compact_defaults_for_untouched_mode_sizes(
        self,
    ) -> None:
        launch = build_explorer_playground_launch(
            dimension=4,
            source_settings=SimpleNamespace(
                width=10,
                height=20,
                depth=6,
                fourth=4,
                piece_set_index=0,
                speed_level=1,
                random_mode_index=0,
                game_seed=1337,
            ),
        )
        self.assertEqual(launch.settings_snapshot.board_dims, (8, 8, 8, 8))

    def test_mode_settings_snapshot_for_dimension_merges_saved_payload(self) -> None:
        with mock.patch(
            "tet4d.ui.pygame.topology_lab.app.load_app_settings_payload",
            return_value={
                "settings": {
                    "4d": {
                        "width": 11,
                        "height": 17,
                        "depth": 7,
                        "fourth": 5,
                        "piece_set_index": 3,
                    }
                }
            },
        ):
            snapshot = mode_settings_snapshot_for_dimension(4)

        self.assertEqual(
            (snapshot.width, snapshot.height, snapshot.depth, snapshot.fourth),
            (11, 17, 7, 5),
        )
        self.assertEqual(snapshot.explorer_width, 8)
        self.assertEqual(snapshot.explorer_fourth, 8)

    def test_build_explorer_launch_uses_source_settings_snapshot(self) -> None:
        settings = SimpleNamespace(
            width=11,
            height=17,
            depth=7,
            fourth=5,
            piece_set_index=3,
            speed_level=4,
            random_mode_index=1,
            game_seed=1234,
            rigid_play_mode="off",
        )
        launch = build_explorer_playground_launch(
            dimension=4,
            source_settings=settings,
        )
        self.assertEqual(launch.settings_snapshot.board_dims, (11, 17, 7, 5))
        self.assertEqual(launch.settings_snapshot.piece_set_index, 3)
        self.assertEqual(launch.settings_snapshot.speed_level, 4)
        self.assertEqual(launch.settings_snapshot.random_mode_index, 1)
        self.assertEqual(launch.settings_snapshot.game_seed, 1234)
        self.assertEqual(launch.settings_snapshot.rigid_play_mode, "off")

    def test_build_explorer_and_launcher_launch_preserve_invalid_3d_profile(
        self,
    ) -> None:
        invalid = self._invalid_profile_3d()
        for entry_source in ("explorer", "launcher"):
            with self.subTest(entry_source=entry_source):
                launch = build_explorer_playground_launch(
                    dimension=3,
                    explorer_profile=invalid,
                    entry_source=entry_source,
                    source_settings=SimpleNamespace(
                        width=7,
                        height=18,
                        depth=6,
                        piece_set_index=0,
                        speed_level=1,
                        random_mode_index=0,
                        game_seed=0,
                    ),
                )
                self.assertIsNotNone(launch.startup_notice)
                self.assertIn(
                    "Stored explorer topology is invalid", launch.startup_notice
                )
                self.assertIs(launch.explorer_profile, invalid)

    def test_build_lab_launch_preserves_invalid_3d_profile_for_manual_repair(
        self,
    ) -> None:
        invalid = self._invalid_profile_3d()
        launch = build_explorer_playground_launch(
            dimension=3,
            explorer_profile=invalid,
            entry_source="lab",
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            source_settings=SimpleNamespace(
                width=7,
                height=18,
                depth=6,
                piece_set_index=0,
                speed_level=1,
                random_mode_index=0,
                game_seed=0,
            ),
        )
        self.assertIs(launch.explorer_profile, invalid)
        self.assertIsNone(launch.startup_notice)

    def test_build_explorer_playground_config_uses_2d_builder(self) -> None:
        profile = ExplorerTopologyProfile(dimension=2, gluings=())
        sentinel = SimpleNamespace(width=8, height=8)
        with mock.patch(
            "tet4d.ui.pygame.front2d_setup.config_from_settings",
            return_value=sentinel,
        ) as build_cfg:
            cfg = build_explorer_playground_config(
                dimension=2,
                explorer_profile=profile,
                settings_snapshot=build_explorer_playground_launch(
                    dimension=2,
                    source_settings=SimpleNamespace(
                        width=12,
                        height=18,
                        piece_set_index=2,
                        speed_level=5,
                        random_mode_index=1,
                        game_seed=99,
                    ),
                ).settings_snapshot,
            )
        self.assertIs(cfg, sentinel)
        settings_arg = build_cfg.call_args.args[0]
        self.assertEqual((settings_arg.width, settings_arg.height), (12, 18))
        self.assertEqual(settings_arg.piece_set_index, 2)
        self.assertEqual(settings_arg.speed_level, 5)
        self.assertIs(
            build_cfg.call_args.kwargs["explorer_topology_profile_override"], profile
        )

    def test_build_explorer_playground_config_uses_nd_builder(self) -> None:
        profile = ExplorerTopologyProfile(dimension=4, gluings=())
        sentinel = SimpleNamespace(dims=(8, 9, 7, 6))
        with mock.patch(
            "tet4d.ui.pygame.frontend_nd_setup.build_config",
            return_value=sentinel,
        ) as build_cfg:
            cfg = build_explorer_playground_config(
                dimension=4,
                explorer_profile=profile,
                settings_snapshot=build_explorer_playground_launch(
                    dimension=4,
                    source_settings=SimpleNamespace(
                        width=13,
                        height=19,
                        depth=8,
                        fourth=6,
                        piece_set_index=4,
                        speed_level=6,
                        random_mode_index=2,
                        game_seed=77,
                    ),
                ).settings_snapshot,
            )
        self.assertIs(cfg, sentinel)
        settings_arg = build_cfg.call_args.args[0]
        self.assertEqual(
            (
                settings_arg.width,
                settings_arg.height,
                settings_arg.depth,
                settings_arg.fourth,
            ),
            (13, 19, 8, 6),
        )
        self.assertEqual(settings_arg.piece_set_index, 4)
        self.assertEqual(settings_arg.speed_level, 6)
        self.assertEqual(build_cfg.call_args.args[1], 4)
        self.assertIs(
            build_cfg.call_args.kwargs["explorer_topology_profile_override"], profile
        )

    def test_build_explorer_playground_config_rebuilds_2d_transport_for_snapshot_dims(
        self,
    ) -> None:
        profile = projective_plane_profile_2d()
        snapshot = build_explorer_playground_launch(
            dimension=2,
            source_settings=SimpleNamespace(
                width=7,
                height=5,
                piece_set_index=0,
                speed_level=3,
                random_mode_index=0,
                game_seed=11,
            ),
        ).settings_snapshot

        cfg = build_explorer_playground_config(
            dimension=2,
            explorer_profile=profile,
            settings_snapshot=snapshot,
        )

        self.assertEqual((cfg.width, cfg.height), (7, 5))
        self.assertEqual(cfg.explorer_transport.dims, (7, 5))
        self.assertFalse(cfg.explorer_rigid_play_enabled)
        self.assertEqual(len(cfg.explorer_transport.directed_seams), 4)
        self.assertEqual(
            cfg.explorer_transport.resolve_cell_step(
                (0, 1),
                MoveStep(axis=0, delta=-1),
            ).target,
            (6, 3),
        )
        self.assertEqual(
            cfg.explorer_transport.resolve_cell_step(
                (2, 0),
                MoveStep(axis=1, delta=-1),
            ).target,
            (4, 4),
        )

    def test_build_explorer_playground_config_rebuilds_3d_transport_for_snapshot_dims(
        self,
    ) -> None:
        profile = projective_space_profile_3d()
        snapshot = build_explorer_playground_launch(
            dimension=3,
            source_settings=SimpleNamespace(
                width=7,
                height=5,
                depth=6,
                piece_set_index=0,
                speed_level=3,
                random_mode_index=0,
                game_seed=11,
            ),
        ).settings_snapshot

        cfg = build_explorer_playground_config(
            dimension=3,
            explorer_profile=profile,
            settings_snapshot=snapshot,
        )

        self.assertEqual(cfg.dims, (7, 5, 6))
        self.assertEqual(cfg.explorer_transport.dims, (7, 5, 6))
        self.assertFalse(cfg.explorer_rigid_play_enabled)
        self.assertEqual(len(cfg.explorer_transport.directed_seams), 6)
        self.assertEqual(
            {
                seam.source_boundary.label
                for seam in cfg.explorer_transport.directed_seams
            },
            {"x-", "x+", "y-", "y+", "z-", "z+"},
        )


if __name__ == "__main__":
    unittest.main()
