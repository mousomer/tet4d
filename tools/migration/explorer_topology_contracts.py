"""Validate T1 declarative design evidence, not native piece conformance."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from tet4d.engine.topology_explorer.canonical_contract import (
    canonicalize_topology_contract,
    topology_contract_identity,
)
from tet4d.generated.topology_contract_v1 import MAXIMUM_AXIS_LENGTH
from tools.migration.square_quotient_evidence import EDGES, analyze_square
from tools.workspace_governance.validators.core import (
    _schema_issues,
    load_manifest_json,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path("tests/fixtures/explorer_topology")
MAX_INTEGER = (1 << 63) - 1


def canonical_digest(value: object) -> str:
    data = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique_rows(rows: list[dict], key: str = "id") -> dict[str, dict]:
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), f"duplicate {key}")
    return result


def recipe_for_profile(profile: dict) -> dict:
    symbolic = dict(profile, board_dimensions=[2, 2])
    canonical = canonicalize_topology_contract(symbolic)
    require(canonical["dimension"] == 2, "recipe is only one square")
    return {
        "schema": "tet4d.square_quotient",
        "schema_version": 1,
        "dimension": 2,
        "domain": "unit_square",
        "operator_version": 1,
        "parameters": {},
        "gluings": canonical["gluings"],
    }


def construction_identity(recipe: dict) -> str:
    return "square-quotient-v1:sha256:" + canonical_digest(recipe)


def profile_identity(profile: dict) -> str:
    require(canonicalize_topology_contract(profile) == profile, "noncanonical profile")
    return "topology-v1:sha256:" + topology_contract_identity(profile)


def check_recipe(recipe: dict, identity: str) -> None:
    profile = {
        "schema": "tet4d.topology_contract",
        "schema_version": 1,
        "dimension": 2,
        "board_dimensions": [2, 2],
        "gluings": recipe["gluings"],
    }
    require(recipe == recipe_for_profile(profile), "noncanonical or unsupported recipe")
    require(construction_identity(recipe) == identity, "construction identity mismatch")


def check_schema(value: dict, name: str, root: Path = ROOT) -> None:
    json.dumps(value, allow_nan=False)  # JSON evidence cannot contain NaN/Infinity.
    path = root / f"config/schema/explorer_topology_{name}_v1.schema.json"
    schema = load_manifest_json(path)
    issues = _schema_issues(value, schema, path=name, source=path.name)
    require(not issues, "; ".join(f"{i.fact}: {i.reason}" for i in issues))


def _review_accepted(review: dict) -> bool:
    reference = review["reference"]
    return bool(
        review["status"] == "accepted"
        and review["reviewer"].strip()
        and re.fullmatch(
            r"https://github\.com/mousomer/tet4d/pull/[0-9]+#pullrequestreview-[0-9]+",
            reference,
        )
    )


def check_proofs(catalog: dict, proofs: dict, root: Path = ROOT) -> dict:
    check_schema(proofs, "quotients", root)
    require(
        proofs["domain"]
        == {
            "vertices": list("ABCD"),
            "edges": [{"id": e, "endpoints": list(v)} for e, v in EDGES.items()],
            "face_word": ["y-+", "x++", "y+-", "x--"],
        },
        "proof domain incidence differs from the unit square",
    )
    recipes = catalog["entries"] + proofs["comparison_constructions"]
    by_construction = {}
    for row in recipes:
        check_recipe(row["recipe"], row["construction_id"])
        by_construction[row["construction_id"]] = row["recipe"]
    cases = unique_rows(proofs["cases"])
    spaces = unique_rows(catalog["space_classes"])
    for case in cases.values():
        require(
            case["construction_id"] in by_construction, "missing proof construction"
        )
        actual = analyze_square(by_construction[case["construction_id"]])
        require(actual == case["expected"], f"quotient witness mismatch: {case['id']}")
        space = spaces[case["derived_space_class_id"]]
        require(
            all(
                actual[k] == space[k]
                for k in ("compact", "connected", "orientable", "euler_characteristic")
            ),
            "proof class invariants disagree",
        )
        require(
            len(actual["boundary_cycles"]) == space["boundary_components"],
            "proof boundary count disagrees",
        )
        derivation = case["derivation"].split("#", 1)[0]
        require(
            derivation
            == "docs/architecture/explorer_topology_catalog_certification_contract.md"
            and (root / derivation).is_file(),
            "missing proof derivation",
        )
        if case["review"]["status"] == "accepted":
            require(
                _review_accepted(case["review"]), "invalid accepted review provenance"
            )
            require(
                case["assertions_status"] == "independently_reviewed",
                "review state mismatch",
            )
        else:
            require(
                case["assertions_status"] == "derived_pending_review",
                "unreviewed proof promoted",
            )
    return cases


def _check_space_classes(catalog: dict) -> None:
    rows = unique_rows(catalog["space_classes"])
    signatures = set()
    for row in rows.values():
        require(bool(re.fullmatch(r"surface\.[a-z]+", row["id"])), "invalid space ID")
        genus = row["genus"]
        chi = (
            2 - (2 * genus if row["orientable"] else genus) - row["boundary_components"]
        )
        require(row["orientable"] or genus >= 1, "nonorientable genus must be positive")
        require(chi == row["euler_characteristic"], "space class chi mismatch")
        signature = (row["orientable"], genus, row["boundary_components"])
        require(signature not in signatures, "duplicate registered surface class")
        signatures.add(signature)


def _check_runtime(entry: dict, root: Path) -> None:
    evidence = entry["runtime_evidence"]
    require(
        entry["selectable"] == (entry["availability"] != "planned"),
        "availability/selectable mismatch",
    )
    if entry["availability"] == "planned":
        require(not evidence, "planned sample cannot claim active runtime evidence")
        return
    kinds = set()
    for row in evidence:
        artifact = (root / row["artifact_path"]).resolve()
        require(
            not Path(row["artifact_path"]).is_absolute()
            and artifact.is_relative_to(root.resolve())
            and artifact.is_file(),
            "missing or unconfined runtime artifact",
        )
        require(
            hashlib.sha256(artifact.read_bytes()).hexdigest() == row["artifact_sha256"],
            "stale runtime artifact",
        )
        require(
            row["fixture_sha256"]
            == hashlib.sha256(
                (root / FIXTURES / "transport_v1.json").read_bytes()
            ).hexdigest(),
            "stale runtime fixture binding",
        )
        require(
            row["profile_id"] == entry["profile_id"],
            "runtime evidence profile mismatch",
        )
        require(row["outcome"] == "passed", "runtime conformance has not passed")
        require(
            bool(re.fullmatch(r"[0-9a-f]{40}", row["source_commit"])),
            "runtime evidence commit missing",
        )
        require(
            _review_accepted(
                {
                    "status": "accepted",
                    "reviewer": row["reviewer"],
                    "reference": row["review_reference"],
                }
            ),
            "runtime review provenance missing",
        )
        kinds.add(row["kind"])
    required = {"native_conformance", "godot_adapter"}
    if entry["availability"] == "implemented":
        required |= {"authority_transfer", "product_acceptance"}
    require(required <= kinds, "runtime evidence incomplete")


def _check_math(entry: dict, proof: dict) -> None:
    values = proof["expected"]
    expected = {
        key: values[key]
        for key in ("orientable", "euler_characteristic", "compact", "connected")
    }
    expected.update(
        boundary_components=len(values["boundary_cycles"]),
        computed_space_class_id=proof["derived_space_class_id"],
        evidence_state=proof["assertions_status"],
    )
    require(entry["invariants"] == expected, "catalog invariants disagree with proof")
    if entry["certification"] == "verified":
        require(
            _review_accepted(proof["review"]),
            "certification lacks independent accepted review",
        )
        require(
            entry["association"] == "proved" and not entry["unknown_invariants"],
            "invalid verified association",
        )
        require(
            entry["space_class_id"] == proof["derived_space_class_id"],
            "certified class contradicts quotient",
        )
    else:
        require(
            entry["association"] in {"proposed", "unresolved"},
            "uncertified association promoted",
        )
        require(
            (entry["space_class_id"] == "unknown")
            == (entry["association"] == "unresolved"),
            "unknown class association mismatch",
        )


def check_catalog(catalog: dict, proofs: dict, root: Path = ROOT) -> None:
    check_schema(catalog, "catalog", root)
    _check_space_classes(catalog)
    cases = check_proofs(catalog, proofs, root)
    entries = unique_rows(catalog["entries"])
    classes = {row["id"] for row in catalog["space_classes"]} | {"unknown"}
    aliases = set(entries)
    orders = set()
    for entry in entries.values():
        require(
            bool(re.fullmatch(r"[a-z][a-z0-9_]*", entry["id"])), "invalid catalog ID"
        )
        require(entry["space_class_id"] in classes, "unknown space class reference")
        require(entry["order"] not in orders, "duplicate catalog order")
        orders.add(entry["order"])
        for alias in entry["aliases"]:
            require(
                bool(re.fullmatch(r"[a-z][a-z0-9_]*", alias)) and alias not in aliases,
                "ambiguous historical alias",
            )
            aliases.add(alias)
        require(
            profile_identity(entry["profile"]) == entry["profile_id"],
            "profile digest mismatch",
        )
        require(
            recipe_for_profile(entry["profile"]) == entry["recipe"],
            "profile recipe mismatch",
        )
        require(
            entry["diagram"]
            == {
                "kind": "unit_square_edges",
                "construction_id": entry["construction_id"],
                "seam_ids": [s["id"] for s in entry["recipe"]["gluings"]],
            },
            "diagram duplicates or changes recipe",
        )
        require(
            len(entry["evidence"]) == 1,
            "one exact mathematical proof reference required",
        )
        evidence = entry["evidence"][0]
        require(
            evidence["path"] == str(FIXTURES / "quotients_v1.json"),
            "unknown evidence owner",
        )
        require(evidence["record_id"] in cases, "missing evidence record")
        proof = cases[evidence["record_id"]]
        require(
            evidence["record_sha256"] == canonical_digest(proof),
            "stale evidence digest",
        )
        require(
            evidence["review_state"] == proof["review"]["status"],
            "evidence review state mismatch",
        )
        require(
            proof["construction_id"] == entry["construction_id"],
            "evidence construction mismatch",
        )
        _check_math(entry, proof)
        _check_runtime(entry, root)
    for example in catalog["identity_examples"]:
        require(
            profile_identity(example["profile"]) == example["profile_id"],
            "identity vector mismatch",
        )
        require(
            construction_identity(recipe_for_profile(example["profile"]))
            == example["construction_id"],
            "construction vector mismatch",
        )


def _check_frame(frame: dict) -> None:
    require(
        sorted(frame["permutation"]) == [0, 1] and len(frame["signs"]) == 2,
        "invalid fixture frame",
    )
    require(
        all(type(s) is int and s in (-1, 1) for s in frame["signs"]),
        "invalid fixture signs",
    )


def _check_cells(cells: list[dict], dims: list[int]) -> None:
    unique_rows(cells)
    occupied = set()
    for cell in cells:
        _check_frame(cell["frame"])
        coord = tuple(cell["coordinate"])
        require(
            all(0 <= v < n for v, n in zip(coord, dims, strict=True)),
            "fixture center outside board",
        )
        require(coord not in occupied, "duplicate fixture occupancy")
        occupied.add(coord)


def _check_state(state: dict, profiles: dict) -> None:
    require(state["profile_ref"] in profiles, "missing state profile")
    require(
        bool(re.fullmatch(r"[0-9a-f]{32}", state["object_key"]["namespace"])),
        "bad object namespace",
    )
    require(
        state["object_key"]["ordinal"] <= MAX_INTEGER
        and state["revision"] <= MAX_INTEGER,
        "fixture integer overflow",
    )
    rest = state["rest_cells"]
    require(
        [c["id"] for c in rest] == list(range(len(rest))), "rest IDs must be canonical"
    )
    coordinates = [tuple(c["coordinate"]) for c in rest]
    require(coordinates == sorted(set(coordinates)), "rest geometry not canonical")
    require(
        all(min(c[a] for c in coordinates) == 0 for a in range(2)),
        "rest geometry not normalized",
    )
    require(
        all(0 <= v < MAXIMUM_AXIS_LENGTH for c in coordinates for v in c),
        "rest coordinate bound",
    )
    reached = {coordinates[0]}
    while True:
        added = {
            c
            for c in coordinates
            if any(
                sum(abs(a - b) for a, b in zip(c, r, strict=True)) == 1 for r in reached
            )
        } - reached
        if not added:
            break
        reached |= added
    require(len(reached) == len(rest), "disconnected rest geometry")
    require(
        [c["id"] for c in state["cells"]] == list(range(len(rest))),
        "source IDs not conserved",
    )
    _check_cells(
        state["cells"], profiles[state["profile_ref"]]["payload"]["board_dimensions"]
    )


def _check_action(action: dict) -> None:
    if action.get("kind") == "translate":
        require(
            set(action) == {"kind", "axis", "delta"} and action["axis"] in (0, 1),
            "invalid fixture translation",
        )
    else:
        require(
            set(action) == {"kind", "axis_a", "axis_b", "quarter_turn"}
            and {action["axis_a"], action["axis_b"]} == {0, 1},
            "invalid fixture rotation",
        )


def _check_resolution_rows(case: dict) -> None:
    for row in case["per_cell"]:
        if row["resolution_status"] == "resolved":
            require(len(row["target"]) == 2, "resolved cell lacks target")
            _check_frame(row["frame"])
            _check_frame(row["transport"])
            if case["action"]["kind"] == "translate":
                require(
                    len(row["reverse_step"]) == 2
                    and row["reverse_step"][0] in (0, 1)
                    and row["reverse_step"][1] in (-1, 1),
                    "missing directed inverse witness",
                )
        else:
            require(
                not row["target"]
                and not row["frame"]["permutation"]
                and not row["transport"]["permutation"],
                "unresolved cell has applicable result",
            )


def _check_case(case: dict, state: dict, profile: dict, root: Path) -> None:
    _check_action(case["action"])
    _check_resolution_rows(case)
    success = case["classification"] != "blocked"
    require(
        success == case["candidate"]["present"] == case["inverse"]["present"],
        "candidate/inverse presence mismatch",
    )
    require(success == (case["blocked_reason"] == ""), "blocked reason mismatch")
    require(
        case["atomic"]
        == ("single_envelope_swap" if success else "entire_envelope_unchanged"),
        "atomicity assertion mismatch",
    )
    ids = [c["id"] for c in state["cells"]]
    require([w["id"] for w in case["per_cell"]] == ids, "incomplete per-ID evidence")
    require(
        all((root / case[key]).is_file() for key in ("native_owner", "godot_owner")),
        "missing future test owner",
    )
    if not success:
        if case["blocked_reason"] == "destination_collision":
            targets = [tuple(row["target"]) for row in case["per_cell"]]
            require(
                all(len(c) == 2 for c in targets) and len(set(targets)) < len(targets),
                "collision has no duplicate destination witness",
            )
        require(
            not case["candidate"]["cells"] and not case["inverse"]["forward_action"],
            "blocked result applies a candidate",
        )
        return
    require(
        all(row["resolution_status"] == "resolved" for row in case["per_cell"]),
        "success has unresolved cells",
    )
    if case["action"]["kind"] == "rotate":
        evidence = case["rotation_evidence"]
        require(
            set(evidence) == {"developed", "pivot_doubled", "rotated_lift"},
            "incomplete rotation development witness",
        )
        require(
            len(evidence["developed"]) == len(ids) == len(evidence["rotated_lift"]),
            "rotation development count mismatch",
        )
    else:
        require(not case["rotation_evidence"], "translation has rotation witness")
    rows = case["candidate"]["cells"]
    require([c["id"] for c in rows] == ids, "destination IDs not conserved")
    _check_cells(rows, profile["payload"]["board_dimensions"])
    for source, target, witness in zip(
        state["cells"], rows, case["per_cell"], strict=True
    ):
        require(
            witness["target"] == target["coordinate"]
            and witness["frame"] == target["frame"],
            "candidate and witness disagree",
        )
        f, t = source["frame"], witness["transport"]
        _check_frame(t)
        composed = {
            "permutation": [t["permutation"][j] for j in f["permutation"]],
            "signs": [
                f["signs"][j] * t["signs"][f["permutation"][j]] for j in range(2)
            ],
        }
        require(composed == target["frame"], "frame composition witness mismatch")
    inv = case["inverse"]
    require(
        inv["version"] == "explorer-piece-inverse/1"
        and inv["expected_recovery"] == "exact_source_semantic_state",
        "inverse version or recovery mismatch",
    )
    require(
        inv["source_ref"] == state["id"]
        and inv["forward_action"] == case["action"]
        and inv["revision_delta"] == 2,
        "inverse descriptor mismatch",
    )


def check_transport(data: dict, catalog: dict, root: Path = ROOT) -> None:
    check_schema(data, "transport_fixtures", root)
    require(
        data["normative_contract"]
        == "docs/architecture/explorer_topology_piece_transport_contract.md"
        and (root / data["normative_contract"]).is_file(),
        "missing normative piece owner",
    )
    profiles = unique_rows(data["profiles"])
    entries = unique_rows(catalog["entries"])
    for profile in profiles.values():
        require(
            profile_identity(profile["payload"]) == profile["profile_id"],
            "fixture profile ID mismatch",
        )
        require(
            construction_identity(recipe_for_profile(profile["payload"]))
            == profile["construction_id"],
            "fixture construction mismatch",
        )
        if profile["catalog_id"] != "none":
            require(
                entries[profile["catalog_id"]]["construction_id"]
                == profile["construction_id"],
                "catalog fixture recipe mismatch",
            )
    states, cases = unique_rows(data["states"]), unique_rows(data["cases"])
    for state in states.values():
        _check_state(state, profiles)
        require(state["initial_state_ref"] in states, "missing initial state")
    for case in cases.values():
        state = states[case["source_state_ref"]]
        _check_case(case, state, profiles[state["profile_ref"]], root)
    unique_rows(data["negative_cases"])
    for row in data["negative_cases"]:
        require(row["base_case"] in cases, "missing negative base case")
        require(
            all(type(p) in (str, int) for p in row["path"]), "invalid mutation path"
        )
        require(
            row["phase"] == "apply" or not row["synchronize_current_revision"],
            "revision setup only applies to commit",
        )
    for lifecycle in data["lifecycle"]:
        require(lifecycle["prepare_case"] in cases, "missing lifecycle proposal")
        initial = states[cases[lifecycle["prepare_case"]]["source_state_ref"]]
        require(
            lifecycle["expected_revision"] == initial["revision"] + 1
            and lifecycle["after_intervening_inverse_revision"]
            == initial["revision"] + 2,
            "stale lifecycle revision mismatch",
        )
    for sequence in data["sequences"]:
        require(
            sequence["inverse_order"] == list(reversed(sequence["steps"])),
            "wrong inverse sequence order",
        )
        require(
            sequence["revision_delta"] == 2 * len(sequence["steps"]),
            "sequence revision mismatch",
        )
        current = states[sequence["initial_state_ref"]]
        for name in sequence["steps"]:
            case = cases[name]
            template = states[case["source_state_ref"]]
            require(
                all(
                    current[k] == template[k]
                    for k in ("profile_ref", "rest_cells", "cells")
                ),
                "sequence continuity mismatch",
            )
            current = dict(current, cells=case["candidate"]["cells"])
        require(
            current["cells"] == sequence["expected_final_cells"],
            "sequence endpoint mismatch",
        )
    require(
        {e["id"] for e in catalog["entries"] if e["family"] == "core"}
        == set(data["enumeration"]["catalog_ids"]),
        "incomplete five-core enumeration",
    )


def validate_package(root: Path = ROOT) -> dict[str, int]:
    catalog, proofs, transport = [
        load_manifest_json(root / FIXTURES / name)
        for name in ("catalog_v1.json", "quotients_v1.json", "transport_v1.json")
    ]
    check_catalog(catalog, proofs, root)
    check_transport(transport, catalog, root)
    return {
        "catalog_entries": len(catalog["entries"]),
        "quotient_witnesses": len(proofs["cases"]),
        "transport_cases": len(transport["cases"]),
        "negative_specs": len(transport["negative_cases"]),
    }


if __name__ == "__main__":
    print(json.dumps(validate_package(), sort_keys=True))
    print("T1 specification checks passed; native/Godot piece conformance not run.")
