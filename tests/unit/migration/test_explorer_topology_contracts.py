from __future__ import annotations

import copy
from collections import Counter
from fractions import Fraction
from itertools import product
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

# T1 mathematical evidence only: these do not exercise a native commit engine.
from tools.migration.explorer_rotation_contract_evidence import (
    IDENTITY,
    apply_frame,
    classify_correspondence,
    compose,
    identity_wrap_axes,
    nearest_centroid_ids,
    pivot_doubled,
    rotation_evidence,
    turn_lift,
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
        "transport_cases": 23,
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
    source = rotation_state(((0, 0), (0, 1)), [(0, 0), (0, 1)])["cells"]
    target = copy.deepcopy(source)
    target[0]["coordinate"], target[1]["coordinate"] = [0, 3], [0, 0]
    assert (
        classify_correspondence(source, target, first)
        == classify_correspondence(source, target, second)
        == "plain_translation"
    )
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


ROTATION_SHAPES = {
    "domino_v": ((0, 0), (0, 1)),
    "domino_h": ((0, 0), (1, 0)),
    "I3": ((0, 0), (0, 1), (0, 2)),
    "I4": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "L3": ((0, 0), (0, 1), (1, 0)),
    "L4": ((0, 0), (0, 1), (0, 2), (1, 0)),
    "S4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "T4": ((0, 0), (1, 0), (1, 1), (2, 0)),
    "asymmetric5": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    "singleton": ((0, 0),),
}
TURN = {"kind": "rotate", "axis_a": 0, "axis_b": 1, "quarter_turn": 1}


def rotation_state(shape, coords, frame=IDENTITY):
    return {
        "version": "explorer-piece-transport/1",
        "object_key": {"namespace": "0" * 31 + "1", "ordinal": 42},
        "profile_ref": "test_profile",
        "rest_cells": [{"id": i, "coordinate": list(c)} for i, c in enumerate(shape)],
        "cells": [
            {"id": i, "domain": 0, "coordinate": list(c), "frame": copy.deepcopy(frame)}
            for i, c in enumerate(coords)
        ],
        "revision": 11,
        "initial_state_ref": "initial",
        "undo": ["retained-descriptor"],
        "trace": ["retained-event"],
    }


def semantic(state):
    return {
        **{
            k: v
            for k, v in state.items()
            if k not in {"revision", "undo", "trace", "cells"}
        },
        "cells": sorted(state["cells"], key=lambda c: c["id"]),
    }


def evidence_step(state, profile, sign):
    before = copy.deepcopy(state)
    result = rotation_evidence(state, profile, dict(TURN, quarter_turn=sign))
    assert state == before  # pure calculation, including retained history/revision
    if result["reason"]:
        assert result["cells"] == []
        return state, result["reason"]
    # Test-only sequencing of semantic outputs, no runtime transaction claim.
    return dict(state, cells=result["cells"], revision=state["revision"] + 1), ""


def test_exact_domino_drift_old_rule_and_stable_id_correction():
    source = {0: (3, 3), 1: (3, 4)}
    old = dict(source)
    observed = []
    for _ in range(4):
        # Independent old-rule witness: the two cells always tie at their centroid.
        selected = min(old.values())
        px, py = selected
        old = {i: (px + y - py, py - x + px) for i, (x, y) in old.items()}
        observed.append(sorted(old.values()))
    assert observed == [
        [(3, 3), (4, 3)],
        [(3, 2), (3, 3)],
        [(3, 2), (4, 2)],
        [(3, 1), (3, 2)],
    ]
    assert old != source
    old_opposite = dict(source)
    for sign in (-1, 1):
        px, py = min(old_opposite.values())
        old_opposite = {
            i: (px + sign * (y - py), py - sign * (x - px))
            for i, (x, y) in old_opposite.items()
        }
    assert old_opposite == {0: (2, 2), 1: (2, 3)}
    assert old_opposite != source
    profile = canonical_topology_payload(
        ExplorerTopologyProfile(dimension=2, gluings=()), (8, 8)
    )
    initial = rotation_state(ROTATION_SHAPES["domino_v"], source.values())
    for signs in ((1,) * 4, (-1,) * 4, (1, -1), (-1, 1)):
        state = initial
        for sign in signs:
            state, reason = evidence_step(state, profile, sign)
            assert not reason
        assert semantic(state) == semantic(initial)
        assert state["revision"] == 11 + len(signs)
    assert rotation_evidence(initial, profile, TURN)["cells"][1]["coordinate"] == [4, 3]
    # Non-index identity: row zero is ID 1, while ID 0 still fixes (3,3).
    shuffled = copy.deepcopy(initial)
    shuffled["cells"].reverse()
    shuffled["rest_cells"].reverse()
    assert rotation_evidence(shuffled, profile, TURN) == rotation_evidence(
        initial, profile, TURN
    )


@pytest.mark.parametrize("shape", ROTATION_SHAPES.values(), ids=ROTATION_SHAPES.keys())
def test_pivot_candidate_set_and_midpoint_equivariance(shape):
    # Deliberately nonconsecutive IDs: choosing row/index zero cannot pass.
    developed = {100 - 3 * i: c for i, c in enumerate(shape)}
    for sign in (-1, 1):
        for shift in ((0, 0), (8, -5), (-16, 10)):
            current = {
                i: (c[0] + shift[0], c[1] + shift[1]) for i, c in developed.items()
            }
            for _ in range(4):
                # Independent exact centroid set, using rational means.
                mean = tuple(
                    Fraction(sum(c[j] for c in current.values()), len(current))
                    for j in range(2)
                )
                distances = {
                    i: sum((c[j] - mean[j]) ** 2 for j in range(2))
                    for i, c in current.items()
                }
                tied = tuple(
                    sorted(
                        i for i, v in distances.items() if v == min(distances.values())
                    )
                )
                assert nearest_centroid_ids(current) == tied
                spans = [
                    max(c[j] for c in current.values())
                    - min(c[j] for c in current.values())
                    for j in range(2)
                ]
                pivot = pivot_doubled(current)
                if spans[0] % 2 != spans[1] % 2:
                    assert pivot == tuple(2 * v for v in current[min(tied)])
                rotated = turn_lift(current, pivot, sign)
                assert nearest_centroid_ids(rotated) == tied
                assert pivot_doubled(rotated) == pivot
                assert pivot_doubled(dict(reversed(list(rotated.items())))) == pivot
                current = rotated


def check_rotation_sequence(initial, profile, signs):
    state = initial
    for sign in signs:
        result = rotation_evidence(state, profile, dict(TURN, quarter_turn=sign))
        reordered = copy.deepcopy(state)
        reordered["cells"] = reordered["cells"][1:] + reordered["cells"][:1]
        reordered["rest_cells"].reverse()
        assert (
            rotation_evidence(reordered, profile, dict(TURN, quarter_turn=sign))
            == result
        )
        next_state, reason = evidence_step(state, profile, sign)
        if reason:
            assert next_state is state
            return reason
        # Every accepted forward turn has an independently requested opposite.
        recovered, reverse_reason = evidence_step(next_state, profile, -sign)
        assert not reverse_reason
        assert semantic(recovered) == semantic(state)
        state = next_state
    assert semantic(state) == semantic(initial)
    assert state["revision"] == initial["revision"] + len(signs)
    return "restored"


def test_supported_rotation_identity_matrix(capsys):
    factories = {
        "bounded": lambda: ExplorerTopologyProfile(dimension=2, gluings=()),
        "cylinder": cylinder_profile_2d,
        "torus": torus_profile_2d,
        "mobius": mobius_strip_profile_2d,
        "klein": klein_bottle_profile_2d,
    }
    configs = [(name, (8, 8)) for name in factories] + [
        ("torus", dims)
        for dims in ((4, 5), (2, 3), (3, 2), (1, 1), (1, 3), (3, 1), (2, 2))
    ]
    frames = [
        {"permutation": list(p), "signs": list(s)}
        for p in ((0, 1), (1, 0))
        for s in product((-1, 1), repeat=2)
    ]
    sequences = {
        "positive4": (1,) * 4,
        "negative4": (-1,) * 4,
        "positive_negative": (1, -1),
        "negative_positive": (-1, 1),
    }
    counts, admitted = Counter(), Counter()
    for name, dims in configs:
        profile = canonical_topology_payload(factories[name](), dims)
        axes = identity_wrap_axes(profile) if name in {"torus", "cylinder"} else set()
        positions = (
            product((0, 3, 7), repeat=2)
            if dims == (8, 8)
            else product(range(dims[0]), range(dims[1]))
        )
        label = f"{name}_{dims[0]}x{dims[1]}"
        for position, shape, frame in product(
            list(positions), ROTATION_SHAPES.values(), frames
        ):
            coords = []
            for q in shape:
                f = apply_frame(frame, q)
                coords.append(
                    tuple(
                        (position[j] + f[j]) % dims[j]
                        if j in axes
                        else position[j] + f[j]
                        for j in range(2)
                    )
                )
            if len(set(coords)) != len(coords) or any(
                not 0 <= c[j] < dims[j] for c in coords for j in range(2)
            ):
                continue  # inadmissible SOURCE, not a skipped rotation sequence
            initial = rotation_state(shape, coords, frame)
            initial["profile_ref"] = profile_identity(profile)
            admitted[label] += 1
            for sequence, signs in sequences.items():
                outcome = check_rotation_sequence(initial, profile, signs)
                counts[(label, sequence, outcome)] += 1
    assert dict(admitted) == {
        "bounded_8x8": 424,
        "cylinder_8x8": 552,
        "torus_8x8": 720,
        "mobius_8x8": 424,
        "klein_8x8": 424,
        "torus_4x5": 1600,
        "torus_2x3": 312,
        "torus_3x2": 312,
        "torus_1x1": 8,
        "torus_1x3": 60,
        "torus_3x1": 60,
        "torus_2x2": 160,
    }
    for seq in sequences:
        totals = Counter()
        for (label, sequence, outcome), count in counts.items():
            if sequence == seq:
                totals[outcome] += count
        assert totals == (
            {"restored": 4072, "rotation_undefined": 768, "destination_collision": 216}
            if seq.endswith("4")
            else {
                "restored": 4300,
                "rotation_undefined": 540,
                "destination_collision": 216,
            }
        )
    assert any(key[2] == "destination_collision" for key in counts)
    assert any(key[2] == "rotation_undefined" for key in counts)
    with capsys.disabled():
        print("\nT1 rotation evidence (not runtime):", dict(admitted))
        for label in admitted:
            print(
                label,
                {
                    seq: {
                        outcome: counts[label, seq, outcome]
                        for outcome in (
                            "restored",
                            "rotation_undefined",
                            "destination_collision",
                        )
                    }
                    for seq in sequences
                },
            )


@pytest.mark.parametrize(
    "case_id,expected",
    [
        ("E2", "plain_translation"),
        ("E3", "plain_translation"),
        ("bounded_interior", "plain_translation"),
        ("E7_torus", "rigid_transform"),
        ("E4", "rigid_transform"),
        ("E5_second", "cellwise_deformation"),
        ("E10_third", "plain_translation"),
        ("E9", "plain_translation"),
        ("mobius_self", "rigid_transform"),
    ],
)
def test_periodic_classification_and_row_order(case_id, expected):
    _, _, data = package()
    case = next(c for c in data["cases"] if c["id"] == case_id)
    state = next(s for s in data["states"] if s["id"] == case["source_state_ref"])
    profile = next(
        p["payload"] for p in data["profiles"] if p["id"] == state["profile_ref"]
    )
    for source in (state["cells"], list(reversed(state["cells"]))):
        for target in (
            case["candidate"]["cells"],
            list(reversed(case["candidate"]["cells"])),
        ):
            assert classify_correspondence(source, target, profile) == expected


def test_period_equivalence_does_not_leak_to_twisted_axes_or_global_isometry():
    source = rotation_state(ROTATION_SHAPES["domino_v"], [(0, 0), (0, 1)])["cells"]
    target = copy.deepcopy(source)
    target[0]["coordinate"], target[1]["coordinate"] = [0, 3], [0, 0]
    torus = canonical_topology_payload(torus_profile_2d(), (4, 4))
    mobius = canonical_topology_payload(mobius_strip_profile_2d(), (4, 4))
    klein = canonical_topology_payload(klein_bottle_profile_2d(), (4, 4))
    assert identity_wrap_axes(mobius) == set()
    assert identity_wrap_axes(klein) == {0}
    assert classify_correspondence(source, target, torus) == "plain_translation"
    assert classify_correspondence(source, target, mobius) == "cellwise_deformation"
    assert classify_correspondence(source, target, klein) == "cellwise_deformation"
    # A finite in-chart rigid rotation is coherent on a rectangular torus even
    # though Q(4,0)=(0,-4) is not in its 4x5 period lattice.
    rectangular = canonical_topology_payload(torus_profile_2d(), (4, 5))
    state = rotation_state(ROTATION_SHAPES["domino_v"], [(1, 1), (1, 2)])
    result = rotation_evidence(state, rectangular, TURN)
    assert (
        classify_correspondence(state["cells"], result["cells"], rectangular)
        == "rigid_transform"
    )
    assert (-4) % 5 != 0
    # Changing lift across unequal periods need not pass the canonical-source
    # affine criterion, but does not change rotation validity or round trips.
    state = rotation_state(ROTATION_SHAPES["domino_v"], [(0, 4), (0, 0)])
    result = rotation_evidence(state, rectangular, TURN)
    assert not result["reason"]
    assert (
        classify_correspondence(state["cells"], result["cells"], rectangular)
        == "cellwise_deformation"
    )
    # Klein's identity X seam alone cannot enable rotation projection.
    state = rotation_state(ROTATION_SHAPES["domino_h"], [(3, 1), (0, 1)])
    assert rotation_evidence(state, klein, TURN)["reason"] == "rotation_undefined"


def test_literal_mobius_and_collision_witnesses_and_recorded_inverse():
    _, _, data = package()
    for case in data["cases"]:
        if case["action"]["kind"] != "rotate":
            continue
        state = next(s for s in data["states"] if s["id"] == case["source_state_ref"])
        profile = next(
            p["payload"] for p in data["profiles"] if p["id"] == state["profile_ref"]
        )
        result = rotation_evidence(state, profile, case["action"])
        assert result["reason"] == case["blocked_reason"]
        if case["id"] == "E7_mobius":
            assert [c["coordinate"] for c in result["cells"]] == [[3, 2], [2, 2]]
            assert all(
                c["frame"] == {"permutation": [1, 0], "signs": [-1, -1]}
                for c in result["cells"]
            )
        if case["id"] == "rotation_crossing_undefined":
            assert result["evidence"]["rotated_lift"] == [[3, 2], [4, 2]]
        if case["id"] == "E7_rotation_collision":
            assert result["evidence"]["pivot_doubled"] == [0, 2]
            assert result["evidence"]["rotated_lift"] == [[-1, 1], [0, 1], [1, 1]]
            assert [(c["id"], c["coordinate"]) for c in result["tentative"]] == [
                (0, [1, 1]),
                (1, [0, 1]),
                (2, [1, 1]),
            ]
            assert not case["candidate"]["present"] and not case["inverse"]["present"]
            assert case["atomic"] == "entire_envelope_unchanged"
            with pytest.raises(ValueError, match="injective"):
                classify_correspondence(state["cells"], result["tentative"], profile)
        if result["reason"]:
            assert (
                evidence_step(state, profile, case["action"]["quarter_turn"])[0]
                is state
            )
            continue
        evidence = result["evidence"]
        lifted = dict(enumerate(map(tuple, evidence["rotated_lift"])))
        recovered = turn_lift(
            lifted, evidence["pivot_doubled"], -case["action"]["quarter_turn"]
        )
        assert list(map(list, recovered.values())) == evidence["developed"]
        reverse_q = {
            "permutation": [1, 0],
            "signs": [case["action"]["quarter_turn"], -case["action"]["quarter_turn"]],
        }
        assert [compose(reverse_q, c["frame"]) for c in result["cells"]] == [
            c["frame"] for c in state["cells"]
        ]


@pytest.mark.parametrize("case_id", ["E3", "E7_torus", "E10_third"])
def test_old_chart_classifications_fail_validation(case_id):
    catalog, _, data = package()
    next(c for c in data["cases"] if c["id"] == case_id)["classification"] = (
        "cellwise_deformation"
    )
    with pytest.raises(ValueError, match="classification witness"):
        check_transport(data, catalog)


def test_old_mobius_pivot_and_fake_collision_fail_validation():
    catalog, _, data = package()
    case = next(c for c in data["cases"] if c["id"] == "E7_mobius")
    case["rotation_evidence"]["pivot_doubled"] = [6, 2]
    with pytest.raises(ValueError, match="pivot witness"):
        check_transport(data, catalog)
    catalog, _, data = package()
    case = next(c for c in data["cases"] if c["id"] == "E7_rotation_collision")
    case["per_cell"][0]["target"] = [0, 1]  # still a collision, but wrong IDs/site
    with pytest.raises(ValueError, match="projected witness"):
        check_transport(data, catalog)


def test_rejected_rotation_cannot_retain_an_inverse_descriptor():
    catalog, _, data = package()
    case = next(c for c in data["cases"] if c["id"] == "E7_rotation_collision")
    case["inverse"]["source_ref"] = "rotate_collision"
    with pytest.raises(ValueError, match="retains inverse data"):
        check_transport(data, catalog)
