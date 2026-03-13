from __future__ import annotations

import shutil
import unittest
from unittest import mock
from uuid import uuid4

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.project_config import (
    explorer_topology_preview_dims,
    explorer_topology_preview_file_default_path,
    state_dir_path,
)
from tet4d.engine.runtime.topology_explorer_bridge import (
    explorer_profile_from_legacy_profile,
    export_explorer_preview_from_legacy_profile,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    advance_explorer_probe,
    compile_explorer_topology_preview,
    explorer_probe_options,
    export_explorer_topology_preview,
    recommended_explorer_probe_coord,
)
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.presets import (
    mobius_strip_profile_2d,
    swapped_xz_profile_3d,
)
from tet4d.engine.topology_explorer.transport_resolver import (
    build_explorer_transport_resolver,
)


class TestTopologyExplorerPreview(unittest.TestCase):
    def test_bridge_converts_symmetric_wrap_profile(self) -> None:
        legacy = validate_topology_profile_state(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            gravity_axis=1,
            topology_mode="bounded",
            edge_rules=(
                (EDGE_WRAP, EDGE_WRAP),
                (EDGE_BOUNDED, EDGE_BOUNDED),
                (EDGE_BOUNDED, EDGE_BOUNDED),
            ),
        )
        profile = explorer_profile_from_legacy_profile(legacy)
        preview = compile_explorer_topology_preview(
            profile,
            dims=(4, 4, 4),
            source="legacy_edge_rules_bridge",
        )
        self.assertEqual(preview["glue_count"], 1)
        self.assertEqual(preview["movement_graph"]["cell_count"], 64)
        self.assertGreater(preview["movement_graph"]["boundary_traversal_count"], 0)

    def test_bridge_rejects_asymmetric_legacy_profile(self) -> None:
        legacy = validate_topology_profile_state(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            gravity_axis=1,
            topology_mode="bounded",
            edge_rules=(
                (EDGE_WRAP, EDGE_BOUNDED),
                (EDGE_BOUNDED, EDGE_BOUNDED),
                (EDGE_BOUNDED, EDGE_BOUNDED),
            ),
        )
        with self.assertRaises(ValueError):
            explorer_profile_from_legacy_profile(legacy)

    def test_export_preview_from_legacy_profile_bridges_then_exports(self) -> None:
        legacy = validate_topology_profile_state(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=2,
            gravity_axis=1,
            topology_mode="bounded",
            edge_rules=((EDGE_WRAP, EDGE_WRAP), (EDGE_BOUNDED, EDGE_BOUNDED)),
        )
        with mock.patch(
            "tet4d.engine.runtime.topology_explorer_bridge.export_explorer_topology_preview",
            return_value=(True, "ok", "preview.json"),
        ) as export_preview:
            result = export_explorer_preview_from_legacy_profile(
                legacy,
                dims=(8, 8),
                source="legacy_bridge_test",
            )

        self.assertEqual(result, (True, "ok", "preview.json"))
        exported_profile = export_preview.call_args.args[0]
        self.assertEqual(exported_profile.dimension, 2)
        self.assertEqual(len(exported_profile.gluings), 1)
        export_preview.assert_called_once_with(
            exported_profile,
            dims=(8, 8),
            source="legacy_bridge_test",
        )

    def test_preview_reports_orientation_reversing_warning(self) -> None:
        preview = compile_explorer_topology_preview(
            mobius_strip_profile_2d(),
            dims=(6, 6),
            source="preset",
        )
        self.assertIn(
            "Contains orientation-reversing seam transforms.",
            preview["warnings"],
        )

    def test_preview_exports_basis_arrow_mapping(self) -> None:
        preview = compile_explorer_topology_preview(
            mobius_strip_profile_2d(),
            dims=(6, 6),
            source="preset",
        )
        self.assertEqual(preview["basis_arrows"][0]["crossing"], "x- -> x+")
        self.assertEqual(
            preview["basis_arrows"][0]["basis_pairs"], [{"from": "+y", "to": "-y"}]
        )

    def test_probe_options_report_available_steps(self) -> None:
        options = explorer_probe_options(
            mobius_strip_profile_2d(),
            dims=(6, 6),
            coord=(0, 0),
        )
        self.assertEqual(
            [option["step"] for option in options], ["x-", "x+", "y-", "y+"]
        )
        self.assertTrue(any(option["traversal"] is not None for option in options))

    def test_recommended_probe_coord_prefers_center_when_valid(self) -> None:
        coord = recommended_explorer_probe_coord(
            mobius_strip_profile_2d(),
            dims=(6, 6),
        )
        self.assertEqual(coord, (3, 3))

    def test_recommended_probe_coord_skips_graph_build_when_dims_validate(self) -> None:
        profile = mobius_strip_profile_2d()
        with (
            mock.patch(
                "tet4d.engine.runtime.topology_explorer_preview.validate_explorer_topology_profile",
                return_value=profile,
            ) as validate_profile,
            mock.patch(
                "tet4d.engine.runtime.topology_explorer_preview.build_movement_graph",
            ) as build_graph,
        ):
            coord = recommended_explorer_probe_coord(profile, dims=(6, 6))
        self.assertEqual(coord, (3, 3))
        validate_profile.assert_called_once_with(profile, dims=(6, 6))
        build_graph.assert_not_called()

    def test_advance_probe_reports_boundary_traversal_message(self) -> None:
        coord, result = advance_explorer_probe(
            mobius_strip_profile_2d(),
            dims=(6, 6),
            coord=(0, 0),
            step_label="x-",
        )
        self.assertEqual(coord, (5, 5))
        self.assertFalse(result["blocked"])
        self.assertIn("x- -> x+", result["message"])
        self.assertEqual(result["traversal"]["glue_id"], "mobius_x")

    def test_probe_matches_shared_transport_resolver_on_cross_axis_seam(self) -> None:
        profile = swapped_xz_profile_3d()
        coord, result = advance_explorer_probe(
            profile,
            dims=(4, 4, 4),
            coord=(0, 1, 2),
            step_label="x-",
        )
        transport_result = build_explorer_transport_resolver(
            profile,
            (4, 4, 4),
        ).resolve_cell_step((0, 1, 2), MoveStep(axis=0, delta=-1))

        self.assertEqual(coord, transport_result.target)
        self.assertEqual(coord, (2, 1, 3))
        self.assertEqual(
            result["traversal"]["glue_id"], transport_result.traversal.glue_id
        )
        self.assertEqual(
            result["traversal"]["source_boundary"],
            transport_result.traversal.source_boundary.label,
        )
        self.assertEqual(
            result["traversal"]["target_boundary"],
            transport_result.traversal.target_boundary.label,
        )

    def test_export_uses_precompiled_preview_payload_without_recompile(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_preview_cached_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            preview = compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="topology_lab_live_preview",
            )
            with mock.patch(
                "tet4d.engine.runtime.topology_explorer_preview.compile_explorer_topology_preview"
            ) as compile_preview:
                ok, message, path = export_explorer_topology_preview(
                    profile,
                    dims=(6, 6),
                    source="topology_lab_2d_mvp",
                    root_dir=root,
                    preview_payload=preview,
                )
            self.assertTrue(ok, message)
            compile_preview.assert_not_called()
            assert path is not None
            payload = path.read_text(encoding="utf-8")
            self.assertIn('"source": "topology_lab_2d_mvp"', payload)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_export_writes_preview_payload_to_runtime_path(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_preview_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            legacy = validate_topology_profile_state(
                gameplay_mode=GAMEPLAY_MODE_EXPLORER,
                dimension=4,
                gravity_axis=1,
                topology_mode="bounded",
                edge_rules=(
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                    (EDGE_WRAP, EDGE_WRAP),
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                    (EDGE_BOUNDED, EDGE_BOUNDED),
                ),
            )
            profile = explorer_profile_from_legacy_profile(legacy)
            dims = explorer_topology_preview_dims(4)
            ok, message, path = export_explorer_topology_preview(
                profile,
                dims=dims,
                source="legacy_edge_rules_bridge",
                root_dir=root,
            )
            self.assertTrue(ok, message)
            self.assertEqual(
                path, explorer_topology_preview_file_default_path(root_dir=root)
            )
            self.assertTrue(path.exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
