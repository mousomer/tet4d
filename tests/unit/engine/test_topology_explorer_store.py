from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from tet4d.engine.runtime.project_config import (
    explorer_topology_profiles_file_default_path,
    state_dir_path,
)
from tet4d.engine.runtime.settings_schema import write_json_object
from tet4d.engine.runtime.topology_explorer_store import (
    load_explorer_topology_profile,
    save_explorer_topology_profile,
)
from tet4d.engine.runtime.topology_persistence import (
    CURRENT_TOPOLOGY_PERSISTENCE_VERSION,
    load_topology_profile_document,
    topology_profiles_document,
)
from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    canonical_topology_payload,
    topology_contract_identity,
)


class TestTopologyExplorerStore(unittest.TestCase):
    def test_malformed_persistence_scalars_fall_back_without_domain_coercion(
        self,
    ) -> None:
        valid_gluing = {
            "id": "wrap_x",
            "enabled": True,
            "source": {"axis": "x", "side": "-"},
            "target": {"axis": "x", "side": "+"},
            "transform": {"permutation": [0], "signs": [1]},
        }
        mutations = (
            ("string boolean", ("enabled",), "false"),
            ("numeric boolean", ("enabled",), 1),
            ("numeric axis string", ("source", "axis"), "0"),
            ("fractional permutation", ("transform", "permutation"), [0.9]),
            ("fractional sign", ("transform", "signs"), [1.8]),
            ("non-string side", ("source", "side"), -1),
            ("non-string id", ("id",), 7),
        )
        for label, path, malformed_value in mutations:
            with self.subTest(case=label):
                root = (
                    state_dir_path()
                    / "pytest_temp"
                    / f"topology_explorer_store_malformed_{uuid4().hex}"
                )
                root.mkdir(parents=True, exist_ok=False)
                try:
                    gluing = {
                        **valid_gluing,
                        "source": dict(valid_gluing["source"]),
                        "target": dict(valid_gluing["target"]),
                        "transform": dict(valid_gluing["transform"]),
                    }
                    owner = gluing
                    for key in path[:-1]:
                        owner = owner[key]
                    owner[path[-1]] = malformed_value
                    write_json_object(
                        explorer_topology_profiles_file_default_path(root_dir=root),
                        {
                            "version": 1,
                            "explorer_topology_profiles": {
                                "2d": {"dimension": 2, "gluings": [gluing]},
                            },
                        },
                    )

                    result = load_explorer_topology_profile(2, root_dir=root)
                    self.assertEqual(result.profile, ExplorerTopologyProfile(2, ()))
                    self.assertFalse(result.used_fallback)
                    self.assertEqual(
                        tuple(item.code for item in result.diagnostics)[-1],
                        "malformed_seam_discarded",
                    )
                finally:
                    shutil.rmtree(root, ignore_errors=True)

    def test_round_trip_persists_profile_per_dimension(self) -> None:
        root = (
            state_dir_path() / "pytest_temp" / f"topology_explorer_store_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = ExplorerTopologyProfile(
                dimension=3,
                gluings=(
                    GluingDescriptor(
                        glue_id="wrap_x",
                        source=BoundaryRef(3, 0, "-"),
                        target=BoundaryRef(3, 0, "+"),
                        transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                    ),
                ),
            )
            ok, message = save_explorer_topology_profile(profile, root_dir=root)
            self.assertTrue(ok, message)

            loaded = load_explorer_topology_profile(3, root_dir=root).profile
            untouched = load_explorer_topology_profile(4, root_dir=root).profile
            also_empty_2d = load_explorer_topology_profile(2, root_dir=root).profile
            self.assertEqual(loaded, profile)
            self.assertEqual(untouched.gluings, ())
            self.assertEqual(also_empty_2d.gluings, ())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_round_trip_persists_profile_per_dimension_including_2d(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_store_2d_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            profile = ExplorerTopologyProfile(
                dimension=2,
                gluings=(
                    GluingDescriptor(
                        glue_id="wrap_x",
                        source=BoundaryRef(2, 0, "-"),
                        target=BoundaryRef(2, 0, "+"),
                        transform=BoundaryTransform(permutation=(0,), signs=(1,)),
                    ),
                ),
            )
            ok, message = save_explorer_topology_profile(profile, root_dir=root)
            self.assertTrue(ok, message)

            loaded = load_explorer_topology_profile(2, root_dir=root).profile
            untouched = load_explorer_topology_profile(3, root_dir=root).profile
            self.assertEqual(loaded, profile)
            self.assertEqual(untouched.gluings, ())
        finally:
            shutil.rmtree(root, ignore_errors=True)


class TestTopologyPersistencePolicy(unittest.TestCase):
    @staticmethod
    def _glue(
        *,
        glue_id: str = "wrap_x",
        enabled: object = True,
        source_axis: object = "x",
        source_side: object = "-",
        target_axis: object = "x",
        target_side: object = "+",
        permutation: object = None,
        signs: object = None,
    ) -> dict[str, object]:
        return {
            "id": glue_id,
            "enabled": enabled,
            "source": {"axis": source_axis, "side": source_side},
            "target": {"axis": target_axis, "side": target_side},
            "transform": {
                "permutation": [0] if permutation is None else permutation,
                "signs": [1] if signs is None else signs,
            },
        }

    @classmethod
    def _document(
        cls,
        glue: dict[str, object] | None = None,
        *,
        version: object = 1,
    ) -> dict[str, object]:
        document: dict[str, object] = {
            "explorer_topology_profiles": {
                "2d": {
                    "dimension": 2,
                    "gluings": [] if glue is None else [glue],
                }
            }
        }
        if version is not None:
            document["version"] = version
        return document

    def test_language_neutral_fixture_matrix(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "topology_persistence_cases.json"
        )
        cases = json.loads(fixture_path.read_text(encoding="utf-8"))["cases"]
        for case in cases:
            with self.subTest(case=case["id"]):
                result = load_topology_profile_document(
                    case["document"], case["dimension"]
                )
                self.assertEqual(result.source_version, case["source_version"])
                self.assertEqual(
                    len(result.profile.gluings), case["expected_glue_count"]
                )
                self.assertEqual(
                    [item.code for item in result.diagnostics],
                    case["expected_diagnostics"],
                )
                self.assertEqual(result.migrated, case["migrated"])
                self.assertEqual(result.used_fallback, case["used_fallback"])

    def test_current_boolean_policy_accepts_only_json_booleans(self) -> None:
        for accepted in (True, False):
            with self.subTest(value=accepted):
                result = load_topology_profile_document(
                    self._document(self._glue(enabled=accepted)), 2
                )
                self.assertEqual(result.profile.gluings[0].enabled, accepted)
                self.assertEqual(result.diagnostics, ())
        for rejected in (1, 0, 1.0, 0.0, "true", "FALSE", "1", None, [], {}):
            with self.subTest(value=rejected):
                result = load_topology_profile_document(
                    self._document(self._glue(enabled=rejected)), 2
                )
                self.assertEqual(result.profile.gluings, ())
                self.assertIn(
                    "invalid_enabled", [item.code for item in result.diagnostics]
                )

    def test_legacy_boolean_policy_is_named_and_non_truthy(self) -> None:
        for alias, expected in (
            (True, True),
            (False, False),
            ("true", True),
            ("False", False),
            (" TRUE ", True),
            (" false ", False),
        ):
            with self.subTest(value=alias):
                result = load_topology_profile_document(
                    self._document(self._glue(enabled=alias), version=None), 2
                )
                self.assertEqual(result.profile.gluings[0].enabled, expected)
        for rejected in (1, 0, 1.0, 0.0, "1", "0", 2, -1, None, [], {}):
            with self.subTest(value=rejected):
                result = load_topology_profile_document(
                    self._document(self._glue(enabled=rejected), version=None), 2
                )
                self.assertEqual(result.profile.gluings, ())
                self.assertIn(
                    "malformed_seam_discarded",
                    [item.code for item in result.diagnostics],
                )

    def test_integer_policy_rejects_coercible_values(self) -> None:
        for rejected in (True, 2.0, 2.9, "2", "2.0", None):
            with self.subTest(value=rejected):
                result = load_topology_profile_document(
                    self._document(
                        self._glue(permutation=[rejected]),
                        version=None,
                    ),
                    2,
                )
                self.assertEqual(result.profile.gluings, ())
                self.assertIn("wrong_type", [item.code for item in result.diagnostics])

    def test_maximum_rank_current_profile_and_non_identity_transform(self) -> None:
        document = {
            "version": 1,
            "explorer_topology_profiles": {
                "4d": {
                    "dimension": 4,
                    "gluings": [
                        {
                            "id": "swap_tangent_axes",
                            "enabled": True,
                            "source": {"axis": "w", "side": "-"},
                            "target": {"axis": "w", "side": "+"},
                            "transform": {
                                "permutation": [2, 0, 1],
                                "signs": [-1, 1, -1],
                            },
                        }
                    ],
                }
            },
        }
        result = load_topology_profile_document(document, 4)
        self.assertEqual(result.diagnostics, ())
        self.assertEqual(result.profile.dimension, 4)
        self.assertEqual(result.profile.gluings[0].transform.signs, (-1, 1, -1))

    def test_missing_current_fields_and_unknown_fields_are_not_guessed(self) -> None:
        missing_enabled = self._glue()
        del missing_enabled["enabled"]
        result = load_topology_profile_document(self._document(missing_enabled), 2)
        self.assertEqual(result.profile.gluings, ())
        self.assertEqual(
            [item.code for item in result.diagnostics],
            ["missing_required_field", "malformed_seam_discarded"],
        )

        missing_transform = self._glue()
        del missing_transform["transform"]
        result = load_topology_profile_document(
            self._document(missing_transform, version=None), 2
        )
        self.assertEqual(result.profile.gluings, ())
        self.assertEqual(
            [item.code for item in result.diagnostics],
            [
                "missing_version",
                "missing_required_field",
                "malformed_seam_discarded",
            ],
        )

        legacy_alias = self._glue()
        legacy_alias["glue_id"] = legacy_alias.pop("id")
        result = load_topology_profile_document(
            self._document(legacy_alias, version=None), 2
        )
        self.assertEqual(result.profile.gluings, ())
        self.assertIn(
            "missing_required_field", [item.code for item in result.diagnostics]
        )

        misspelled = self._glue()
        misspelled["enable"] = misspelled.pop("enabled")
        result = load_topology_profile_document(self._document(misspelled), 2)
        self.assertEqual(result.profile.gluings, ())
        self.assertEqual(
            [item.code for item in result.diagnostics],
            ["missing_required_field", "malformed_seam_discarded"],
        )

    def test_exact_and_reversed_duplicates_are_deduplicated(self) -> None:
        first = self._glue(glue_id="first")
        duplicate = self._glue(glue_id="second")
        reversed_row = self._glue(
            glue_id="reversed",
            source_side="+",
            target_side="-",
        )
        document = self._document()
        profile = document["explorer_topology_profiles"]["2d"]
        profile["gluings"] = [first, duplicate, reversed_row]
        result = load_topology_profile_document(document, 2)
        self.assertEqual(len(result.profile.gluings), 1)
        self.assertEqual(
            [item.code for item in result.diagnostics],
            ["duplicate_seam_deduplicated", "duplicate_seam_deduplicated"],
        )

    def test_conflicting_seams_discard_every_conflicting_row(self) -> None:
        document = self._document()
        profile = document["explorer_topology_profiles"]["2d"]
        profile["gluings"] = [
            self._glue(glue_id="x_wrap"),
            self._glue(
                glue_id="cross_axis",
                target_axis="y",
                target_side="+",
            ),
        ]
        result = load_topology_profile_document(document, 2)
        self.assertEqual(result.profile.gluings, ())
        self.assertEqual(
            [item.code for item in result.diagnostics],
            ["conflicting_seam_discarded", "conflicting_seam_discarded"],
        )
        self.assertEqual(
            [item.path for item in result.diagnostics],
            [
                "$.explorer_topology_profiles.2d.gluings[0]",
                "$.explorer_topology_profiles.2d.gluings[1]",
            ],
        )

    def test_enabled_disabled_conflict_discards_both_rows(self) -> None:
        document = self._document()
        profile = document["explorer_topology_profiles"]["2d"]
        profile["gluings"] = [
            self._glue(glue_id="enabled", enabled=True),
            self._glue(glue_id="disabled", enabled=False),
        ]
        result = load_topology_profile_document(document, 2)
        self.assertEqual(result.profile.gluings, ())
        self.assertEqual(
            [item.code for item in result.diagnostics],
            ["conflicting_seam_discarded", "conflicting_seam_discarded"],
        )

    def test_duplicate_id_with_different_geometry_discards_both_rows(self) -> None:
        document = self._document()
        profile = document["explorer_topology_profiles"]["2d"]
        profile["gluings"] = [
            self._glue(glue_id="reused"),
            self._glue(
                glue_id="reused",
                source_axis="y",
                target_axis="y",
            ),
        ]
        result = load_topology_profile_document(document, 2)
        self.assertEqual(result.profile.gluings, ())
        self.assertEqual(
            [item.code for item in result.diagnostics],
            ["conflicting_seam_discarded", "conflicting_seam_discarded"],
        )

    def test_malformed_json_reports_structured_fallback(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_store_bad_json_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            path = explorer_topology_profiles_file_default_path(root_dir=root)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{not json", encoding="utf-8")
            result = load_explorer_topology_profile(2, root_dir=root)
            self.assertTrue(result.used_fallback)
            self.assertEqual(
                [item.code for item in result.diagnostics],
                ["malformed_json", "malformed_profile_fallback"],
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_writer_reports_recovery_and_emits_only_current_format(self) -> None:
        root = (
            state_dir_path()
            / "pytest_temp"
            / f"topology_explorer_store_rewrite_{uuid4().hex}"
        )
        root.mkdir(parents=True, exist_ok=False)
        try:
            path = explorer_topology_profiles_file_default_path(root_dir=root)
            write_json_object(
                path,
                self._document(self._glue(enabled="false"), version=None),
            )
            profile = ExplorerTopologyProfile(2, ())
            ok, message = save_explorer_topology_profile(profile, root_dir=root)
            self.assertTrue(ok, message)
            self.assertIn("recovered", message)
            written = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(written["version"], 1)
            result = load_topology_profile_document(written, 2)
            self.assertEqual(result.diagnostics, ())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_legacy_migration_round_trip_emits_clean_current_format(self) -> None:
        legacy = self._document(self._glue(enabled="TRUE"), version=None)
        migrated = load_topology_profile_document(legacy, 2)
        self.assertTrue(migrated.migrated)
        self.assertFalse(migrated.used_fallback)

        current = topology_profiles_document((migrated.profile,))
        self.assertEqual(current["version"], CURRENT_TOPOLOGY_PERSISTENCE_VERSION)
        enabled = current["explorer_topology_profiles"]["2d"]["gluings"][0]["enabled"]
        self.assertIs(type(enabled), bool)
        strict = load_topology_profile_document(current, 2)
        self.assertEqual(strict.profile, migrated.profile)
        self.assertFalse(strict.migrated)
        self.assertEqual(strict.diagnostics, ())

        before = canonical_topology_payload(migrated.profile, (4, 5))
        after = canonical_topology_payload(strict.profile, (4, 5))
        self.assertEqual(before, after)
        self.assertEqual(
            topology_contract_identity(before),
            topology_contract_identity(after),
        )


if __name__ == "__main__":
    unittest.main()
