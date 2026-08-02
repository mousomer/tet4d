from __future__ import annotations

import hashlib
import json
import shutil
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
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
    CURRENT_V1_POLICY,
    LEGACY_V0_POLICY,
    load_topology_profile_document,
    topology_profile_payload,
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


@contextmanager
def _temporary_state_dir(label: str) -> Iterator[Path]:
    root = state_dir_path() / "pytest_temp" / f"{label}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


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
        with _temporary_state_dir("topology_explorer_store_malformed") as root:
            for label, path, malformed_value in mutations:
                with self.subTest(case=label):
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

    def test_round_trip_persists_each_profile_dimension(self) -> None:
        for dimension in (2, 3):
            with (
                self.subTest(dimension=dimension),
                _temporary_state_dir(f"topology_explorer_store_{dimension}d") as root,
            ):
                tangent = tuple(range(dimension - 1))
                profile = ExplorerTopologyProfile(
                    dimension,
                    (
                        GluingDescriptor(
                            "wrap_x",
                            BoundaryRef(dimension, 0, "-"),
                            BoundaryRef(dimension, 0, "+"),
                            BoundaryTransform(tangent, (1,) * (dimension - 1)),
                        ),
                    ),
                )
                ok, message = save_explorer_topology_profile(profile, root_dir=root)
                self.assertTrue(ok, message)
                self.assertEqual(
                    load_explorer_topology_profile(dimension, root_dir=root).profile,
                    profile,
                )
                other = 3 if dimension == 2 else 2
                self.assertEqual(
                    load_explorer_topology_profile(
                        other, root_dir=root
                    ).profile.gluings,
                    (),
                )


class TestTopologyPersistencePolicy(unittest.TestCase):
    _FIXTURE_PROJECTION_SHA256 = (
        "6124cbb5c3a2804a09b4d285d5403a07eff55d261e6fd20b6b259d430fb8a28d"
    )

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
        projection = {}
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
                projection[case["id"]] = {
                    "profile": topology_profile_payload(result.profile),
                    "source_version": result.source_version,
                    "migrated": result.migrated,
                    "recovered": result.recovered,
                    "used_fallback": result.used_fallback,
                    "diagnostics": [
                        {
                            "severity": item.severity,
                            "code": item.code,
                            "path": item.path,
                            "recovery": item.recovery,
                        }
                        for item in result.diagnostics
                    ],
                }
        encoded = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(
            hashlib.sha256(encoded).hexdigest(),
            self._FIXTURE_PROJECTION_SHA256,
        )

    def test_format_policies_are_explicit_distinct_and_immutable(self) -> None:
        cases = (
            (CURRENT_V1_POLICY, (False, "exact", "reject", "reject")),
            (
                LEGACY_V0_POLICY,
                (
                    True,
                    "legacy_string_aliases",
                    "default_true_with_diagnostic",
                    "use_trusted_slot_with_diagnostic",
                ),
            ),
        )
        for policy, expected in cases:
            with self.subTest(version=policy.source_version):
                actual = (
                    policy.migrated,
                    policy.boolean_policy,
                    policy.missing_enabled_policy,
                    policy.missing_dimension_policy,
                )
                self.assertEqual(actual, expected)
        with self.assertRaises(FrozenInstanceError):
            CURRENT_V1_POLICY.migrated = True
        with self.assertRaises(AttributeError):
            CURRENT_V1_POLICY.document_fields.add("metadata")

    def test_boolean_policies_are_table_driven_and_non_truthy(self) -> None:
        cases = (
            (
                1,
                ((True, True), (False, False)),
                (1, 0, 1.0, 0.0, "true", "FALSE", "1", None, [], {}),
                "invalid_enabled",
            ),
            (
                None,
                (
                    (True, True),
                    (False, False),
                    ("true", True),
                    ("False", False),
                    (" TRUE ", True),
                    (" false ", False),
                ),
                (1, 0, 1.0, 0.0, "1", "0", 2, -1, None, [], {}),
                "malformed_seam_discarded",
            ),
        )
        for version, accepted, rejected, rejection_code in cases:
            for value, expected in accepted:
                with self.subTest(version=version, value=value):
                    result = load_topology_profile_document(
                        self._document(self._glue(enabled=value), version=version), 2
                    )
                    self.assertEqual(result.profile.gluings[0].enabled, expected)
            for value in rejected:
                with self.subTest(version=version, value=value):
                    result = load_topology_profile_document(
                        self._document(self._glue(enabled=value), version=version), 2
                    )
                    self.assertEqual(result.profile.gluings, ())
                    self.assertIn(
                        rejection_code, [item.code for item in result.diagnostics]
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
        cases = (
            ("enabled", None, 1),
            ("transform", None, None),
            ("id", "glue_id", None),
            ("enabled", "enable", 1),
        )
        for field, alias, version in cases:
            with self.subTest(field=field, alias=alias, version=version):
                glue = self._glue()
                value = glue.pop(field)
                if alias is not None:
                    glue[alias] = value
                result = load_topology_profile_document(
                    self._document(glue, version=version), 2
                )
                self.assertEqual(result.profile.gluings, ())
                expected = ("missing_required_field", "malformed_seam_discarded")
                if version is None:
                    expected = ("missing_version", *expected)
                self.assertEqual(
                    tuple(item.code for item in result.diagnostics), expected
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

    def test_conflict_policies_discard_every_conflicting_row(self) -> None:
        cases = (
            (
                "active boundary",
                self._glue(glue_id="x_wrap"),
                self._glue(glue_id="cross_axis", target_axis="y"),
            ),
            (
                "enabled state",
                self._glue(glue_id="enabled", enabled=True),
                self._glue(glue_id="disabled", enabled=False),
            ),
            (
                "duplicate id",
                self._glue(glue_id="reused"),
                self._glue(glue_id="reused", source_axis="y", target_axis="y"),
            ),
        )
        for label, first, second in cases:
            with self.subTest(case=label):
                document = self._document()
                document["explorer_topology_profiles"]["2d"]["gluings"] = [
                    first,
                    second,
                ]
                result = load_topology_profile_document(document, 2)
                self.assertEqual(result.profile.gluings, ())
                self.assertEqual(
                    [item.code for item in result.diagnostics],
                    ["conflicting_seam_discarded"] * 2,
                )
                self.assertEqual(
                    [item.path for item in result.diagnostics],
                    [
                        f"$.explorer_topology_profiles.2d.gluings[{index}]"
                        for index in range(2)
                    ],
                )

    def test_malformed_json_reports_structured_fallback(self) -> None:
        with _temporary_state_dir("topology_explorer_store_bad_json") as root:
            path = explorer_topology_profiles_file_default_path(root_dir=root)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{not json", encoding="utf-8")
            result = load_explorer_topology_profile(2, root_dir=root)
            self.assertTrue(result.used_fallback)
            self.assertEqual(
                [item.code for item in result.diagnostics],
                ["malformed_json", "malformed_profile_fallback"],
            )

    def test_writer_reports_recovery_and_emits_only_current_format(self) -> None:
        with _temporary_state_dir("topology_explorer_store_rewrite") as root:
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
