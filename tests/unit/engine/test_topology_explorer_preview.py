from __future__ import annotations

import json
import shutil
import unittest
import warnings
from unittest import mock
from uuid import uuid4

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.project_config import (
    explorer_topology_preview_cache_dir_path,
    explorer_topology_preview_dims,
    explorer_topology_preview_file_default_path,
    state_dir_path,
)
from tet4d.engine.runtime.topology_cache import (
    clear_topology_cache,
    read_cached_graph_rows,
    read_cached_playability_analysis,
    read_topology_cache_entry,
    topology_cache_usage,
    write_cached_playability_analysis,
)
from tet4d.engine.runtime.topology_explorer_bridge import (
    explorer_profile_from_legacy_profile,
    export_explorer_preview_from_legacy_profile,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    _PREVIEW_LOCAL_CACHE_VERSION,
    advance_explorer_probe,
    compile_explorer_topology_preview,
    explorer_probe_options,
    export_explorer_topology_preview,
    recommended_explorer_probe_coord,
)
from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.movement_graph import (
    build_movement_graph,
    movement_graph_from_rows,
    movement_graph_rows,
)
from tet4d.engine.topology_explorer.presets import (
    mobius_strip_profile_2d,
    sphere_profile_2d,
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
                "tet4d.engine.runtime.topology_explorer_preview.movement_graph_rows",
            ) as graph_rows,
        ):
            coord = recommended_explorer_probe_coord(profile, dims=(6, 6))
        self.assertEqual(coord, (3, 3))
        validate_profile.assert_called_once_with(profile, dims=(6, 6))
        graph_rows.assert_not_called()

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

    def test_probe_keeps_local_direction_frame_across_sphere_corner(self) -> None:
        coord, result = advance_explorer_probe(
            sphere_profile_2d(),
            dims=(8, 8),
            coord=(7, 7),
            step_label="y+",
        )
        self.assertEqual(coord, (7, 0))
        self.assertEqual(tuple(result["frame_permutation"]), (1, 0))
        self.assertEqual(tuple(result["frame_signs"]), (-1, -1))

        coord, result = advance_explorer_probe(
            sphere_profile_2d(),
            dims=(8, 8),
            coord=coord,
            step_label="x+",
            frame_permutation=tuple(result["frame_permutation"]),
            frame_signs=tuple(result["frame_signs"]),
        )
        self.assertEqual(coord, (0, 0))
        self.assertEqual(tuple(result["frame_permutation"]), (0, 1))
        self.assertEqual(tuple(result["frame_signs"]), (1, 1))

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

    def test_compile_preview_reuses_local_cache_for_same_signature(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_preview_local_cache_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            preview = compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="local_cache_seed",
                root_dir=root,
            )
            cache_dir = explorer_topology_preview_cache_dir_path(root_dir=root)
            self.assertTrue(cache_dir.exists())
            with mock.patch(
                "tet4d.engine.runtime.topology_explorer_preview.movement_graph_rows",
                side_effect=AssertionError("cache miss"),
            ):
                cached = compile_explorer_topology_preview(
                    profile,
                    dims=(6, 6),
                    source="local_cache_hit",
                    root_dir=root,
                )
            self.assertEqual(cached["source"], "local_cache_hit")
            self.assertEqual(cached["movement_graph"], preview["movement_graph"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_missing_local_cache_file_is_silent_cache_miss(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_preview_missing_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                entry = read_topology_cache_entry(
                    profile,
                    dims=(6, 6),
                    root_dir=root,
                )
            self.assertIsNone(entry)
            self.assertEqual(caught, [])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_preview_cache_identity_rejects_dimension_near_misses(self) -> None:
        profile = mobius_strip_profile_2d()

        for dims in ((6, True), (6, 6.0), (6, "6")):
            with self.subTest(dims=dims), self.assertRaises(ValueError):
                compile_explorer_topology_preview(profile, dims=dims)

    def test_compile_preview_recomputes_when_cache_version_changes(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_preview_versioned_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="local_cache_seed",
                root_dir=root,
            )
            with (
                mock.patch(
                    "tet4d.engine.runtime.topology_explorer_preview._PREVIEW_LOCAL_CACHE_VERSION",
                    _PREVIEW_LOCAL_CACHE_VERSION + 1,
                ),
                mock.patch(
                    "tet4d.engine.runtime.topology_explorer_preview.movement_graph_rows",
                    wraps=movement_graph_rows,
                ) as build_graph,
            ):
                preview = compile_explorer_topology_preview(
                    profile,
                    dims=(6, 6),
                    source="local_cache_version_bump",
                    root_dir=root,
                )
            build_graph.assert_called_once_with(profile, dims=(6, 6))
            self.assertEqual(preview["source"], "local_cache_version_bump")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_compile_preview_falls_back_after_corrupt_local_cache(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_preview_corrupt_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="local_cache_seed",
                root_dir=root,
            )
            cache_file = next(
                explorer_topology_preview_cache_dir_path(root_dir=root).glob("*.json")
            )
            cache_file.write_text("{not-json", encoding="utf-8")
            with (
                warnings.catch_warnings(record=True) as caught,
                mock.patch(
                    "tet4d.engine.runtime.topology_explorer_preview.movement_graph_rows",
                    wraps=movement_graph_rows,
                ) as build_graph,
            ):
                warnings.simplefilter("always")
                preview = compile_explorer_topology_preview(
                    profile,
                    dims=(6, 6),
                    source="local_cache_rebuild",
                    root_dir=root,
                )
            build_graph.assert_called_once_with(profile, dims=(6, 6))
            self.assertEqual(caught, [])
            self.assertEqual(preview["source"], "local_cache_rebuild")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_compile_preview_persists_graph_rows_in_cache(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_graph_rows_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="graph_rows_seed",
                root_dir=root,
            )
            rows = read_cached_graph_rows(profile, dims=(6, 6), root_dir=root)
            self.assertIsNotNone(rows)
            assert rows is not None
            self.assertEqual(
                movement_graph_from_rows(rows),
                build_movement_graph(profile, dims=(6, 6)),
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_playability_analysis_roundtrips_through_topology_cache(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_playability_cache_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="playability_seed",
                root_dir=root,
            )
            analysis = TopologyPlaygroundPlayabilityAnalysis(
                status="playable",
                validity="valid",
                explorer_usability="cellwise_explorable",
                rigid_playability="rigid_playable",
                summary="cached analysis",
                rigid_reason="Rigid transport is ready.",
            )
            write_cached_playability_analysis(
                profile,
                dims=(6, 6),
                analysis=analysis,
                root_dir=root,
            )
            cached = read_cached_playability_analysis(
                profile,
                dims=(6, 6),
                root_dir=root,
            )
            self.assertEqual(cached, analysis)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_cache_metadata_near_misses_are_identity_misses_and_rebuild(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_cache_identity_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            authoritative = compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="identity_seed",
                root_dir=root,
            )
            cache_file = next(
                explorer_topology_preview_cache_dir_path(root_dir=root).glob("*.json")
            )
            original = json.loads(cache_file.read_text(encoding="utf-8"))
            cases = []
            for near_miss in (True, 3.0, "3"):
                case = json.loads(json.dumps(original))
                case["cache_version"] = near_miss
                cases.append(case)
            wrong_key = json.loads(json.dumps(original))
            wrong_key["cache_key"] = "0" * 64
            cases.append(wrong_key)
            wrong_dims = json.loads(json.dumps(original))
            wrong_dims["dims"] = [6, 7]
            cases.append(wrong_dims)

            for case in cases:
                cache_file.write_text(json.dumps(case), encoding="utf-8")
                self.assertIsNone(
                    read_topology_cache_entry(
                        profile,
                        dims=(6, 6),
                        root_dir=root,
                    )
                )
                rebuilt = compile_explorer_topology_preview(
                    profile,
                    dims=(6, 6),
                    source="identity_rebuild",
                    root_dir=root,
                )
                self.assertEqual(
                    rebuilt["movement_graph"],
                    authoritative["movement_graph"],
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_cached_graph_rows_reject_semantic_near_misses(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_graph_strict_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="graph_strict_seed",
                root_dir=root,
            )
            cache_file = next(
                explorer_topology_preview_cache_dir_path(root_dir=root).glob("*.json")
            )
            original = json.loads(cache_file.read_text(encoding="utf-8"))
            malformed_rows = []

            bad_coord = json.loads(json.dumps(original))
            bad_coord["graph_rows"][0]["coord"][0] = True
            malformed_rows.append(bad_coord)

            bad_step = json.loads(json.dumps(original))
            bad_step["graph_rows"][0]["edges"][0]["step"] = 1
            malformed_rows.append(bad_step)

            bad_target = json.loads(json.dumps(original))
            bad_target["graph_rows"][0]["edges"][0]["target"][0] = "1"
            malformed_rows.append(bad_target)

            omitted_seam = json.loads(json.dumps(original))
            seam_removed = False
            for row in omitted_seam["graph_rows"]:
                for edge_index, edge in enumerate(row["edges"]):
                    if edge["traversal"] is not None:
                        row["edges"].pop(edge_index)
                        seam_removed = True
                        break
                if seam_removed:
                    break
            self.assertTrue(seam_removed)
            malformed_rows.append(omitted_seam)

            for malformed in malformed_rows:
                cache_file.write_text(json.dumps(malformed), encoding="utf-8")
                self.assertIsNone(
                    read_cached_graph_rows(
                        profile,
                        dims=(6, 6),
                        root_dir=root,
                    )
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_cached_playability_rejects_count_near_misses(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_playability_strict_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="playability_strict_seed",
                root_dir=root,
            )
            analysis = TopologyPlaygroundPlayabilityAnalysis(
                status="playable",
                validity="valid",
                explorer_usability="cellwise_explorable",
                rigid_playability="rigid_playable",
                summary="strict cached analysis",
            )
            write_cached_playability_analysis(
                profile,
                dims=(6, 6),
                analysis=analysis,
                root_dir=root,
            )
            cache_file = next(
                explorer_topology_preview_cache_dir_path(root_dir=root).glob("*.json")
            )
            original = json.loads(cache_file.read_text(encoding="utf-8"))

            for near_miss in (True, 1.0, "1"):
                malformed = json.loads(json.dumps(original))
                malformed["playability_analysis"]["movement_summary"]["cell_count"] = (
                    near_miss
                )
                cache_file.write_text(json.dumps(malformed), encoding="utf-8")
                self.assertIsNone(
                    read_cached_playability_analysis(
                        profile,
                        dims=(6, 6),
                        root_dir=root,
                    )
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_clear_topology_cache_removes_persisted_files(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_cache_clear_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = mobius_strip_profile_2d()
            compile_explorer_topology_preview(
                profile,
                dims=(6, 6),
                source="cache_clear_seed",
                root_dir=root,
            )
            file_count, total_bytes = topology_cache_usage(root_dir=root)
            self.assertGreater(file_count, 0)
            self.assertGreater(total_bytes, 0)
            cleared_count, cleared_bytes = clear_topology_cache(root_dir=root)
            self.assertEqual(cleared_count, file_count)
            self.assertEqual(cleared_bytes, total_bytes)
            self.assertEqual(topology_cache_usage(root_dir=root), (0, 0))
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
