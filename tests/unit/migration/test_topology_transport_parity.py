from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tet4d.engine.topology_explorer.topology_transport import (
    TopologyTransportError,
    validate_topology_transport_profile,
    validate_topology_transport_query,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "godot"
    / "Tet4D.Godot"
    / "tests"
    / "fixtures"
    / "topology_transport_v1.json"
)


def _fixture() -> dict[str, object]:
    payload = _materialize(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))
    assert isinstance(payload, dict)
    assert payload["slice"] == "topology_transport_v1"
    return payload


def _materialize(value: object) -> object:
    if type(value) is dict:
        if set(value) == {"$float"}:  # type: ignore[arg-type]
            return float(value["$float"])  # type: ignore[index]
        return {key: _materialize(item) for key, item in value.items()}  # type: ignore[union-attr]
    if type(value) is list:
        return [_materialize(item) for item in value]
    return value


def _replace_path(payload: object, path: list[object], value: object) -> object:
    result = copy.deepcopy(payload)
    parent = result
    for component in path[:-1]:
        parent = parent[component]  # type: ignore[index]
    parent[path[-1]] = value  # type: ignore[index]
    return result


def _query_payload(row: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in row.items() if key != "profile"}


@pytest.mark.parametrize("case", _fixture()["valid_profile_cases"])
def test_python_accepts_shared_valid_profile_cases(case: dict[str, object]) -> None:
    fixture = _fixture()
    source = fixture["profiles"][case["profile"]]
    result = validate_topology_transport_profile(source)
    assert result["contract_version"] == 1
    assert result["rank"] == len(result["dimensions"])


@pytest.mark.parametrize("case", _fixture()["invalid_profile_cases"])
def test_python_rejects_shared_invalid_profile_cases(case: dict[str, object]) -> None:
    fixture = _fixture()
    source = fixture["profiles"][case["base"]]
    supplied = _replace_path(source, case["path"], case["value"])
    with pytest.raises(TopologyTransportError) as captured:
        validate_topology_transport_profile(supplied)
    assert captured.value.code == case["code"]
    assert captured.value.path == case["error_path"]


@pytest.mark.parametrize("case", _fixture()["valid_query_cases"])
def test_python_accepts_shared_valid_query_cases(case: dict[str, object]) -> None:
    fixture = _fixture()
    query = fixture["queries"][case["query"]]
    profile = validate_topology_transport_profile(fixture["profiles"][query["profile"]])
    result = validate_topology_transport_query(_query_payload(query), profile)
    assert result["delta"] in (-1, 1)


@pytest.mark.parametrize("case", _fixture()["invalid_query_cases"])
def test_python_rejects_shared_invalid_query_cases(case: dict[str, object]) -> None:
    fixture = _fixture()
    base = fixture["queries"][case["base"]]
    supplied = _replace_path(base, case["path"], case["value"])
    profile = validate_topology_transport_profile(
        fixture["profiles"][supplied["profile"]]
    )
    with pytest.raises(TopologyTransportError) as captured:
        validate_topology_transport_query(_query_payload(supplied), profile)
    assert captured.value.code == case["code"]
    assert captured.value.path == case["error_path"]


def test_original_boolean_integer_blocker_is_explicitly_closed() -> None:
    fixture = _fixture()
    accepted = validate_topology_transport_profile(fixture["profiles"]["wrapped_2d"])
    assert accepted["contract_version"] == 1
    cases = {case["id"]: case for case in fixture["invalid_profile_cases"]}
    assert cases["version_boolean"]["value"] is True
    assert type(cases["version_float"]["value"]) is float
    assert cases["version_string"]["value"] == "1"
