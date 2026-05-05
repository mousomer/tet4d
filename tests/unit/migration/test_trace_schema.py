from __future__ import annotations

import json

import pytest

from tools.migration.trace_schema import (
    assert_trace_hygiene,
    canonical_json,
    stable_hash,
)
from tools.migration.export_endgame_trace import ENDGAME_FLOAT_PRECISION


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
