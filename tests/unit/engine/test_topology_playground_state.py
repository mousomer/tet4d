from __future__ import annotations

import inspect
import unittest

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    default_topology_profile_state,
)
from tet4d.engine.runtime import topology_playground_state
from tet4d.engine.runtime.topology_playground_state import (
    GRAVITY_MODE_EXPLORATION,
    GRAVITY_MODE_FALLING,
    PLAYABILITY_STATUS_WARNING,
    PRESET_SOURCE_DESIGNER,
    PRESET_SOURCE_EXPLORER,
    TOOL_PROBE,
    TRANSPORT_OWNER_EXPLORER,
    TRANSPORT_OWNER_LEGACY,
    TopologyPlaygroundGluingDraft,
    TopologyPlaygroundGravityMode,
    TopologyPlaygroundLaunchSettings,
    TopologyPlaygroundCanonicalOwnershipState,
    TopologyPlaygroundDerivedOwnershipState,
    TopologyPlaygroundEditorOwnershipState,
    TopologyPlaygroundInspectorOwnershipState,
    TopologyPlaygroundSandboxOwnershipState,
    TopologyPlaygroundMovementSummary,
    TopologyPlaygroundPlayabilityAnalysis,
    TopologyPlaygroundPresetMetadata,
    TopologyPlaygroundPresetSelection,
    TopologyPlaygroundProbeState,
    TopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig,
    default_topology_playground_state,
)
from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)


class TestTopologyPlaygroundState(unittest.TestCase):
    def test_module_stays_ui_free(self) -> None:
        source = inspect.getsource(topology_playground_state)
        self.assertNotIn("pygame", source)
        self.assertNotIn("tet4d.ui", source)

    def test_default_state_exposes_required_stage1_contract(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
        )

        self.assertEqual(state.dimension, 3)
        self.assertEqual(state.axis_sizes, (6, 12, 6))
        self.assertIsNotNone(state.topology_config)
        self.assertTrue(hasattr(state, "selected_boundary"))
        self.assertTrue(hasattr(state, "selected_gluing"))
        self.assertTrue(hasattr(state, "active_tool"))
        self.assertTrue(hasattr(state, "probe_state"))
        self.assertTrue(hasattr(state, "sandbox_piece_state"))
        self.assertTrue(hasattr(state, "transport_policy"))
        self.assertTrue(hasattr(state, "gravity_mode"))
        self.assertTrue(hasattr(state, "playability_analysis"))
        self.assertTrue(hasattr(state, "preset_metadata"))
        self.assertTrue(hasattr(state, "dirty"))
        self.assertFalse(hasattr(state, "mouse_targets"))
        self.assertFalse(hasattr(state, "scene_camera"))
        self.assertFalse(hasattr(state, "running"))
        self.assertFalse(hasattr(state, "status"))

    def test_state_can_represent_full_unified_playground_config(self) -> None:
        legacy_profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        glue = GluingDescriptor(
            glue_id="glue_001",
            source=BoundaryRef(dimension=3, axis=0, side="-"),
            target=BoundaryRef(dimension=3, axis=2, side="+"),
            transform=BoundaryTransform(permutation=(1, 0), signs=(1, -1)),
        )
        state = TopologyPlaygroundState(
            dimension=3,
            axis_sizes=(8, 10, 6),
            topology_config=TopologyPlaygroundTopologyConfig(
                legacy_profile=legacy_profile,
                explorer_profile=ExplorerTopologyProfile(
                    dimension=3,
                    gluings=(glue,),
                ),
                gluing_draft=TopologyPlaygroundGluingDraft(
                    slot_index=1,
                    source_boundary=glue.source,
                    target_boundary=glue.target,
                    permutation=(1, 0),
                    signs=(1, -1),
                ),
            ),
            selected_boundary=glue.source,
            selected_gluing=glue.glue_id,
            active_tool=TOOL_PROBE,
            probe_state=TopologyPlaygroundProbeState(
                coord=(1, 2, 3),
                path=((0, 2, 3), (1, 2, 3)),
                trace=("x+: [0, 2, 3] -> [1, 2, 3]",),
                highlighted_gluing=glue.glue_id,
                frame_permutation=(2, 1, 0),
                frame_signs=(1, -1, 1),
                last_step="x+",
            ),
            sandbox_piece_state=TopologyPlaygroundSandboxPieceState(
                enabled=True,
                piece_index=2,
                origin=(3, 5, 2),
                local_blocks=((0, 0, 0), (1, 0, 0)),
                trace=("spawn",),
                seam_crossings=("wrap_0: x- -> x+",),
                show_trace=False,
            ),
            launch_settings=TopologyPlaygroundLaunchSettings(
                piece_set_index=3,
                speed_level=4,
                random_mode_index=1,
                game_seed=99,
            ),
            gravity_mode=TopologyPlaygroundGravityMode(
                name=GRAVITY_MODE_EXPLORATION,
                gravity_axis=1,
                tick_enabled=False,
                locking_enabled=False,
                wrap_gravity_axis=True,
            ),
            playability_analysis=TopologyPlaygroundPlayabilityAnalysis(
                status=PLAYABILITY_STATUS_WARNING,
                summary="Disconnected movement graph",
                warnings=("Movement graph has 2 disconnected components.",),
                movement_summary=TopologyPlaygroundMovementSummary(
                    cell_count=480,
                    directed_edge_count=960,
                    boundary_traversal_count=32,
                    component_count=2,
                ),
                recommended_next_preset="full_wrap_3d",
            ),
            preset_metadata=TopologyPlaygroundPresetMetadata(
                topology_preset=TopologyPlaygroundPresetSelection(
                    preset_id=legacy_profile.preset_id,
                    label="Use selected mode",
                    source=PRESET_SOURCE_DESIGNER,
                ),
                explorer_preset=TopologyPlaygroundPresetSelection(
                    preset_id="full_wrap_3d",
                    label="Full Wrap",
                    source=PRESET_SOURCE_EXPLORER,
                ),
            ),
            dirty=True,
        )

        self.assertEqual(state.selected_boundary, glue.source)
        self.assertEqual(state.selected_gluing, "glue_001")
        self.assertEqual(state.active_tool, TOOL_PROBE)
        self.assertEqual(state.probe_state.coord, (1, 2, 3))
        self.assertEqual(state.probe_state.frame_permutation, (2, 1, 0))
        self.assertEqual(state.probe_state.frame_signs, (1, -1, 1))
        self.assertEqual(state.sandbox_piece_state.origin, (3, 5, 2))
        self.assertEqual(state.transport_policy.owner, TRANSPORT_OWNER_EXPLORER)
        self.assertEqual(state.gravity_mode.name, GRAVITY_MODE_EXPLORATION)
        self.assertEqual(
            state.playability_analysis.movement_summary.component_count,
            2,
        )
        self.assertEqual(
            state.preset_metadata.explorer_preset.preset_id,
            "full_wrap_3d",
        )
        self.assertTrue(state.dirty)

    def test_state_exposes_explicit_ownership_views(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
            active_tool=TOOL_PROBE,
        )

        canonical = state.canonical_state
        editor = state.editor_state
        inspector = state.inspector_state
        sandbox = state.sandbox_state
        derived = state.derived_state

        self.assertIsInstance(canonical, TopologyPlaygroundCanonicalOwnershipState)
        self.assertEqual(canonical.axis_sizes, (6, 12, 6))
        self.assertIsInstance(editor, TopologyPlaygroundEditorOwnershipState)
        self.assertEqual(editor.active_tool, TOOL_PROBE)
        self.assertIsInstance(inspector, TopologyPlaygroundInspectorOwnershipState)
        self.assertIs(inspector.probe_state, state.probe_state)
        self.assertIsInstance(sandbox, TopologyPlaygroundSandboxOwnershipState)
        self.assertIs(sandbox.sandbox_piece_state, state.sandbox_piece_state)
        self.assertIsInstance(derived, TopologyPlaygroundDerivedOwnershipState)
        self.assertIs(derived.transport_policy, state.transport_policy)
        self.assertIs(derived.gravity_mode, state.gravity_mode)

    def test_probe_state_preserves_unavailable_inspect_state(self) -> None:
        legacy_profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = TopologyPlaygroundState(
            dimension=3,
            axis_sizes=(5, 8, 8),
            topology_config=TopologyPlaygroundTopologyConfig(
                legacy_profile=legacy_profile,
                explorer_profile=ExplorerTopologyProfile(dimension=3, gluings=()),
            ),
            probe_state=TopologyPlaygroundProbeState(
                coord=None,
                path=(),
                trace=("Probe unavailable",),
            ),
        )

        self.assertIsNone(state.probe_state.coord)
        self.assertEqual(state.probe_state.path, ())
        self.assertEqual(state.probe_state.trace, ("Probe unavailable",))

    def test_normal_mode_defaults_to_legacy_transport_policy(self) -> None:
        legacy_profile = default_topology_profile_state(
            dimension=2,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )
        state = TopologyPlaygroundState(
            dimension=2,
            axis_sizes=(10, 20),
            topology_config=TopologyPlaygroundTopologyConfig(
                legacy_profile=legacy_profile
            ),
        )

        self.assertEqual(state.transport_policy.owner, TRANSPORT_OWNER_LEGACY)
        self.assertEqual(state.gravity_mode.name, GRAVITY_MODE_FALLING)
        self.assertFalse(state.gravity_mode.wrap_gravity_axis)


if __name__ == "__main__":
    unittest.main()
