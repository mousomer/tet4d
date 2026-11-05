from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tet4d.engine.topology_explorer.canonical_contract import (
    canonical_topology_payload,
    topology_contract_profile,
)
from tet4d.engine.topology_explorer.glue_model import ExplorerTopologyProfile, MoveStep
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    cylinder_profile_2d,
    klein_bottle_profile_2d,
    mobius_strip_profile_2d,
    projective_plane_profile_2d,
    sphere_profile_2d,
    torus_profile_2d,
)
from tet4d.engine.topology_explorer.transport_resolver import (
    build_explorer_transport_resolver,
)
from tools.migration.explorer_topology_contracts import (
    FIXTURES,
    ROOT,
    canonical_digest,
    check_catalog,
    check_schema,
    check_transport,
    construction_identity,
    profile_identity,
    recipe_for_profile,
    validate_package,
)
from tools.migration.square_quotient_evidence import analyze_square, link_kind
from tools.workspace_governance.validators.core import load_manifest_json


def package():
    return [
        load_manifest_json(ROOT / FIXTURES / name)
        for name in ("catalog_v1.json", "quotients_v1.json", "transport_v1.json")
    ]


def test_complete_design_package():
    assert validate_package() == {
        "catalog_entries": 7,
        "quotient_witnesses": 9,
        "transport_cases": 22,
        "negative_specs": 19,
    }


@pytest.mark.parametrize(
    "name,factory",
    [
        ("empty_2d", lambda: ExplorerTopologyProfile(dimension=2, gluings=())),
        ("cylinder_2d", cylinder_profile_2d),
        ("torus_2d", torus_profile_2d),
        ("mobius_2d", mobius_strip_profile_2d),
        ("klein_2d", klein_bottle_profile_2d),
        ("projective_2d", projective_plane_profile_2d),
        ("sphere_2d", sphere_profile_2d),
    ],
)
def test_catalog_maps_actual_unchanged_presets(name, factory):
    catalog, _, _ = package()
    entry = next(e for e in catalog["entries"] if e["id"] == name)
    assert entry["profile"] == canonical_topology_payload(factory(), (4, 4))
    assert entry["availability"] == "planned" and not entry["selectable"]
    assert entry["certification"] != "verified"


def test_three_identity_levels_and_tangent_changes():
    a = canonical_topology_payload(torus_profile_2d(), (4, 4))
    b = canonical_topology_payload(torus_profile_2d(), (4, 5))
    assert recipe_for_profile(a) == recipe_for_profile(b)
    assert profile_identity(a) != profile_identity(b)
    x = canonical_topology_payload(cylinder_profile_2d(), (4, 4))
    y = canonical_topology_payload(
        axis_wrap_profile(dimension=2, wrapped_axes=(1,)), (4, 4)
    )
    mobius = canonical_topology_payload(mobius_strip_profile_2d(), (4, 4))
    assert (
        len({construction_identity(recipe_for_profile(p)) for p in (x, y, mobius)}) == 3
    )
    assert analyze_square(recipe_for_profile(x))["orientable"]
    assert analyze_square(recipe_for_profile(y))["orientable"]
    assert not analyze_square(recipe_for_profile(mobius))["orientable"]


def test_equivalent_authored_seams_keep_both_identities():
    profile = torus_profile_2d()
    reversed_rows = tuple(
        type(g)(
            glue_id=f"label-{i}",
            source=g.target,
            target=g.source,
            transform=g.transform.inverse(),
        )
        for i, g in enumerate(reversed(profile.gluings))
    )
    disabled = type(profile.gluings[0])(
        glue_id="ignored",
        source=profile.gluings[0].source,
        target=profile.gluings[0].target,
        transform=profile.gluings[0].transform,
        enabled=False,
    )
    authored = ExplorerTopologyProfile(dimension=2, gluings=reversed_rows + (disabled,))
    first, second = [canonical_topology_payload(p, (4, 4)) for p in (profile, authored)]
    assert profile_identity(first) == profile_identity(second)
    assert construction_identity(recipe_for_profile(first)) == construction_identity(
        recipe_for_profile(second)
    )


def test_projective_and_sphere_names_do_not_supply_the_proof():
    rp = analyze_square(
        recipe_for_profile(
            canonical_topology_payload(projective_plane_profile_2d(), (4, 4))
        )
    )
    legacy = analyze_square(
        recipe_for_profile(canonical_topology_payload(sphere_profile_2d(), (4, 4)))
    )
    assert rp["vertex_classes"] == [["A", "C"], ["B", "D"]]
    assert rp["euler_characteristic"] == 1 and not rp["orientable"]
    assert legacy["vertex_classes"] == [list("ABCD")]
    assert legacy["euler_characteristic"] == 0 and not legacy["orientable"]
    assert legacy["vertex_links"] == [
        {"corners": list("ABCD"), "kind": "circle", "degrees": [2, 2, 2, 2]}
    ]
    assert not legacy["boundary_cycles"]


def test_local_links_keep_loops_parallel_arcs_and_require_connectedness():
    assert link_kind([("a", "a")]) == ("circle", [2])
    assert link_kind([("a", "b"), ("a", "b")]) == ("circle", [2, 2])
    assert link_kind([("a", "a"), ("b", "b")])[0] == "singular"
    assert link_kind([("a", "b"), ("b", "c"), ("b", "d")])[0] == "singular"


@pytest.mark.parametrize(
    "field,value",
    [
        ("availability", "implemented"),
        ("availability", "experimental"),
        ("selectable", True),
        ("certification", "verified"),
        ("association", "proved"),
        ("profile_id", "topology-v1:sha256:" + "0" * 64),
        ("construction_id", "square-quotient-v1:sha256:" + "0" * 64),
    ],
)
def test_unearned_status_or_identity_changes_reject(field, value):
    catalog, proofs, _ = package()
    catalog["entries"][0][field] = value
    with pytest.raises(ValueError):
        check_catalog(catalog, proofs)


def test_verified_math_does_not_activate_runtime():
    catalog, proofs, _ = package()
    proof, entry = proofs["cases"][0], catalog["entries"][0]
    # Synthetic metadata tests the admission rule; never persisted as proof review.
    proof["review"] = {
        "status": "accepted",
        "reviewer": "fixture-reviewer",
        "reference": "https://github.com/mousomer/tet4d/pull/1#pullrequestreview-1",
    }
    proof["assertions_status"] = "independently_reviewed"
    entry["certification"], entry["association"] = "verified", "proved"
    entry["invariants"]["evidence_state"] = "independently_reviewed"
    entry["evidence"][0].update(
        record_sha256=canonical_digest(proof), review_state="accepted"
    )
    check_catalog(catalog, proofs)
    assert entry["availability"] == "planned" and not entry["selectable"]


def test_stale_missing_or_wrong_proof_cannot_certify():
    catalog, proofs, _ = package()
    catalog["entries"][0]["evidence"][0]["record_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="stale evidence"):
        check_catalog(catalog, proofs)
    catalog, proofs, _ = package()
    proofs["cases"][0]["expected"]["euler_characteristic"] = 2
    with pytest.raises(ValueError, match="quotient witness"):
        check_catalog(catalog, proofs)
    catalog, proofs, _ = package()
    catalog["entries"][0]["evidence"][0]["record_id"] = "missing"
    with pytest.raises(ValueError, match="missing evidence"):
        check_catalog(catalog, proofs)


@pytest.mark.parametrize(
    "name,index", [("catalog", 0), ("quotients", 1), ("transport_fixtures", 2)]
)
@pytest.mark.parametrize("value", [True, 1.0, "1", 2])
def test_envelopes_do_not_coerce_versions(name, index, value):
    data = package()[index]
    data["schema_version"] = value
    with pytest.raises(ValueError):
        check_schema(data, name)


@pytest.mark.parametrize(
    "index,name,path",
    [
        (0, "catalog", ["entries", 0]),
        (0, "catalog", ["entries", 0, "recipe"]),
        (1, "quotients", ["cases", 0, "expected", "vertex_links", 0]),
        (2, "transport_fixtures", ["states", 0, "cells", 0, "frame"]),
    ],
)
def test_unknown_nested_fields_reject(index, name, path):
    data = package()[index]
    node = data
    for key in path:
        node = node[key]
    node["unexpected"] = True
    with pytest.raises(ValueError, match="undeclared field"):
        check_schema(data, name)


def test_duplicate_keys_reject(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":1,"schema_version":2}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_manifest_json(path)


def test_fixture_frames_correspondence_and_sequence_fail_closed():
    catalog, _, data = package()
    broken = copy.deepcopy(data)
    case = next(c for c in broken["cases"] if c["id"] == "E4")
    case["candidate"]["cells"][0]["frame"]["signs"] = [1, 1]
    with pytest.raises(ValueError, match="witness disagree"):
        check_transport(broken, catalog)
    broken = copy.deepcopy(data)
    broken["sequences"][1]["inverse_order"].reverse()
    with pytest.raises(ValueError, match="inverse sequence"):
        check_transport(broken, catalog)


def test_translation_witnesses_match_existing_cell_reference_only():
    _, _, data = package()
    states = {s["id"]: s for s in data["states"]}
    profiles = {p["id"]: p for p in data["profiles"]}
    for case in data["cases"]:
        if case["action"]["kind"] != "translate":
            continue
        state = states[case["source_state_ref"]]
        profile, dims = topology_contract_profile(
            profiles[state["profile_ref"]]["payload"]
        )
        resolver = build_explorer_transport_resolver(profile, dims)
        action = case["action"]
        step = MoveStep(axis=action["axis"], delta=action["delta"])
        for source, witness in zip(state["cells"], case["per_cell"], strict=True):
            result = resolver.resolve_cell_step(source["coordinate"], step)
            assert list(result.target or ()) == witness["target"]
            if result.target is not None:
                transport = result.piece_frame_transform
                assert (
                    list(transport.permutation) == witness["transport"]["permutation"]
                )
                assert list(transport.signs) == witness["transport"]["signs"]
        if case["id"] == "E6":
            legacy = resolver.resolve_piece_step(
                [c["coordinate"] for c in state["cells"]], step
            )
            assert legacy.kind == "cellwise_deformation"
            assert case["classification"] == "blocked"
            assert case["blocked_reason"] == "destination_collision"


def test_fixture_coverage_and_no_fabricated_execution_results():
    _, _, data = package()
    assert len(data["enumeration"]["catalog_ids"]) == 5
    assert all(
        board in data["enumeration"]["boards"]
        for board in ([1, 1], [1, 2], [2, 1], [2, 2], [4, 4], [4, 5])
    )
    ids = (
        {c["id"] for c in data["cases"]}
        | {c["id"] for c in data["sequences"]}
        | {c["id"] for c in data["lifecycle"]}
    )
    assert {
        "E1",
        "E2",
        "E3",
        "E4",
        "E5",
        "E6",
        "E8",
        "E9",
        "E10",
        "E7_bounded",
        "E7_torus",
        "E7_mobius",
        "E7_undefined",
    } <= ids
    reasons = {c["expected_reason"] for c in data["negative_cases"]} | {
        c["blocked_reason"] for c in data["cases"]
    }
    assert {
        "unconnected_boundary",
        "destination_collision",
        "ambiguous_destination",
        "inverse_mismatch",
        "rotation_undefined",
        "invalid_piece_state",
        "invalid_profile",
        "stale_candidate",
        "candidate_mismatch",
        "unsupported_representation",
        "invalid_action",
        "resource_limit",
    } <= reasons
    for case in data["cases"] + data["negative_cases"]:
        assert case["native_result"] == case["godot_result"] == "not_run"
    assert Path(data["normative_contract"]).is_file()


def test_catalog_label_does_not_promote_or_change_identity():
    catalog, proofs, _ = package()
    entry = catalog["entries"][0]
    identity = (entry["construction_id"], entry["profile_id"])
    entry["label"] = "New display label"
    entry["description"] = "Description edit only"
    check_catalog(catalog, proofs)
    assert identity == (entry["construction_id"], entry["profile_id"])
    assert entry["availability"] == "planned" and entry["certification"] == "unverified"


def test_alias_collision_and_profile_version_mismatch_reject():
    catalog, proofs, _ = package()
    catalog["entries"][0]["aliases"] = ["torus_2d"]
    with pytest.raises(ValueError, match="ambiguous historical alias"):
        check_catalog(catalog, proofs)
    catalog, proofs, _ = package()
    catalog["entries"][0]["profile"]["schema_version"] = 2
    with pytest.raises(ValueError):
        check_catalog(catalog, proofs)


def test_pending_runtime_artifact_cannot_activate_experimental_entry():
    catalog, proofs, _ = package()
    entry = catalog["entries"][0]
    entry["availability"], entry["selectable"] = "experimental", True
    entry["runtime_evidence"] = [
        {
            "profile_id": entry["profile_id"],
            "contract_version": "explorer-piece-transport/1",
            "source_commit": "0" * 40,
            "command": "future-native-runner",
            "outcome": "passed",
            "kind": "native_conformance",
            "reviewer": "fixture-reviewer",
            "review_reference": "https://github.com/mousomer/tet4d/pull/1#pullrequestreview-1",
            "artifact_path": "tests/fixtures/explorer_topology/nonexistent-result.json",
            "artifact_sha256": "0" * 64,
            "fixture_sha256": "0" * 64,
        }
    ]
    with pytest.raises(ValueError, match="runtime artifact"):
        check_catalog(catalog, proofs)


def test_collision_reason_requires_collision_evidence():
    catalog, _, data = package()
    case = next(c for c in data["cases"] if c["id"] == "E6")
    case["per_cell"][0]["target"] = [1, 0]
    with pytest.raises(ValueError, match="no duplicate destination"):
        check_transport(data, catalog)


def test_success_requires_complete_rotation_and_inverse_witness():
    catalog, _, data = package()
    case = next(c for c in data["cases"] if c["id"] == "E7_torus")
    del case["rotation_evidence"]["developed"]
    with pytest.raises(ValueError, match="incomplete rotation"):
        check_transport(data, catalog)
    catalog, _, data = package()
    data["cases"][1]["inverse"]["version"] = "explorer-piece-inverse/2"
    with pytest.raises(ValueError, match="inverse version"):
        check_transport(data, catalog)
