from __future__ import annotations

import json

import pytest

from tools.migration.export_endgame_trace import ENDGAME_FLOAT_PRECISION
from tools.migration.trace_schema import (
    assert_trace_hygiene,
    canonical_json,
    coord_payload,
    coords_payload,
    frame_payload,
    stable_hash,
    to_jsonable,
)


def test_canonical_json_sorts_keys_and_ends_with_newline() -> None:
    payload = {"z": 1, "a": {"b": 2}}
    text = canonical_json(payload)

    assert text == '{\n  "a": {\n    "b": 2\n  },\n  "z": 1\n}\n'
    assert json.loads(text) == payload


def test_stable_hash_uses_canonical_payload_not_python_hash() -> None:
    left = {"b": [2, 1], "a": {"x": True}}
    right = {"a": {"x": True}, "b": [2, 1]}

    assert stable_hash(left) == stable_hash(right)
    assert stable_hash(left) != stable_hash({"a": {"x": False}, "b": [2, 1]})
    assert stable_hash(left) == (
        "ab9d72b9a3119dee4ebd5fdd0dde517f81590c69d3046bb45a29797eceea82ac"
    )


def test_stable_hash_preserves_scalar_type_and_optional_value_semantics() -> None:
    assert stable_hash({"value": True}) != stable_hash({"value": 1})
    assert stable_hash({"value": 1}) != stable_hash({"value": 1.0})
    assert stable_hash({"optional": None, "value": 1.25}) == (
        "16273c8b5cdb4473e235c316a36819ebbfc45e8cd944299cc59d9a69d22edec0"
    )
    assert stable_hash({"ordered": [1, 2]}) != stable_hash({"ordered": [2, 1]})


def test_diagnostics_do_not_affect_explicit_semantic_identity_material() -> None:
    left = {"semantic": {"coord": [1, 2]}, "diagnostics": ["first"]}
    right = {"semantic": {"coord": [1, 2]}, "diagnostics": ["second"]}

    assert stable_hash(left["semantic"]) == stable_hash(right["semantic"])
    assert stable_hash(left) != stable_hash(right)


@pytest.mark.parametrize("near_miss", [True, 1.0, "1"])
def test_coordinate_materializers_reject_integer_near_misses(
    near_miss: object,
) -> None:
    with pytest.raises(TypeError):
        coord_payload((near_miss, 2))

    with pytest.raises(TypeError):
        coords_payload(((1, 2), (near_miss, 3)))


@pytest.mark.parametrize("near_miss", [True, 1.0, "1"])
def test_frame_payload_rejects_index_near_misses(near_miss: object) -> None:
    with pytest.raises(TypeError):
        frame_payload(near_miss)


@pytest.mark.parametrize(
    "value",
    [
        object(),
        {1: "non-string key"},
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_trace_materializer_rejects_unowned_values(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        to_jsonable(value)

    with pytest.raises((TypeError, ValueError)):
        stable_hash(value)


def test_endgame_trace_precision_is_fixed() -> None:
    assert ENDGAME_FLOAT_PRECISION == 6


def test_trace_hygiene_rejects_timestamps_paths_and_memory_reprs() -> None:
    with pytest.raises(AssertionError):
        assert_trace_hygiene({"generated_at": "2026-05-05T00:00:00Z"})

    with pytest.raises(AssertionError):
        local_user_path = "/" + "Users" + "/example/project/file.json"
        assert_trace_hygiene({"path": local_user_path})

    with pytest.raises(AssertionError):
        assert_trace_hygiene({"repr": "<Thing object at 0xabc123>"})
