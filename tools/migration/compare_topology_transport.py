from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from tet4d.engine.topology_explorer.topology_transport import (
    TopologyTransportError,
    validate_topology_transport_profile,
    validate_topology_transport_query,
)
from tet4d.generated.topology_contract_v1 import AXIS_NAMES

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    ROOT / "godot" / "Tet4D.Godot" / "tests" / "fixtures" / "topology_transport_v1.json"
)
OUTPUT_PREFIX = "TET4D_TOPOLOGY_TRANSPORT_PARITY="


def _materialize(value: object) -> object:
    if type(value) is dict:
        row = value
        if set(row) == {"$float"}:
            return float(row["$float"])
        return {key: _materialize(item) for key, item in row.items()}
    if type(value) is list:
        return [_materialize(item) for item in value]
    return value


def _fixture() -> dict[str, Any]:
    payload = _materialize(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
    if not isinstance(payload, dict) or payload.get("slice") != "topology_transport_v1":
        raise ValueError("invalid topology transport parity fixture")
    return payload


def _replace_path(payload: object, path: list[object], value: object) -> object:
    result = copy.deepcopy(payload)
    parent = result
    for component in path[:-1]:
        parent = parent[component]
    parent[path[-1]] = value
    return result


def _query_payload(source: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in source.items() if key != "profile"}


def _native_profile_shape(profile: dict[str, object]) -> dict[str, object]:
    seams = []
    for seam in profile["seams"]:
        row = copy.deepcopy(seam)
        row["source"]["axis"] = AXIS_NAMES[row["source"]["axis"]]
        row["target"]["axis"] = AXIS_NAMES[row["target"]["axis"]]
        seams.append(row)
    return {
        "contract_version": profile["contract_version"],
        "rank": profile["rank"],
        "dimensions": profile["dimensions"],
        "seams": seams,
    }


def _error_result(error: TopologyTransportError) -> dict[str, object]:
    return {"accepted": False, "code": error.code, "path": error.path}


def python_results() -> dict[str, object]:
    fixture = _fixture()
    profiles = fixture["profiles"]
    results: dict[str, object] = {}
    for case in fixture["valid_profile_cases"]:
        profile = validate_topology_transport_profile(profiles[case["profile"]])
        results[f"profile:{case['id']}"] = {
            "accepted": True,
            "value": _native_profile_shape(profile),
        }
    for case in fixture["invalid_profile_cases"]:
        supplied = _replace_path(profiles[case["base"]], case["path"], case["value"])
        try:
            validate_topology_transport_profile(supplied)
        except TopologyTransportError as error:
            results[f"profile:{case['id']}"] = _error_result(error)
        else:
            raise AssertionError(f"Python accepted invalid profile {case['id']}")
    queries = fixture["queries"]
    for case in fixture["valid_query_cases"]:
        source = queries[case["query"]]
        profile = validate_topology_transport_profile(profiles[source["profile"]])
        query = validate_topology_transport_query(_query_payload(source), profile)
        results[f"query:{case['id']}"] = {"accepted": True, "value": query}
    for case in fixture["invalid_query_cases"]:
        source = _replace_path(queries[case["base"]], case["path"], case["value"])
        profile = validate_topology_transport_profile(profiles[source["profile"]])
        try:
            validate_topology_transport_query(_query_payload(source), profile)
        except TopologyTransportError as error:
            results[f"query:{case['id']}"] = _error_result(error)
        else:
            raise AssertionError(f"Python accepted invalid query {case['id']}")
    return results


def native_results(path: Path) -> dict[str, object]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(OUTPUT_PREFIX):
            payload = json.loads(line.removeprefix(OUTPUT_PREFIX))
            if not isinstance(payload, dict):
                break
            return payload
    raise ValueError("native topology transport parity output is missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-output", type=Path, required=True)
    args = parser.parse_args()
    expected = python_results()
    actual = native_results(args.native_output)
    if actual != expected:
        missing = sorted(set(expected).difference(actual))
        extra = sorted(set(actual).difference(expected))
        mismatched = sorted(
            case_id
            for case_id in set(expected).intersection(actual)
            if expected[case_id] != actual[case_id]
        )
        raise SystemExit(
            "topology transport parity mismatch: "
            f"missing={missing}, extra={extra}, mismatched={mismatched}"
        )
    print(f"topology transport parity passed: {len(expected)} shared cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
