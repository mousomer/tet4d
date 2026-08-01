from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import tools.codegen.generate_topology_contract as generator


def _source() -> dict[str, object]:
    return json.loads(generator.SOURCE_PATH.read_text(encoding="utf-8"))


def test_authoritative_source_generates_current_bindings() -> None:
    payload = generator.load_contract_source()

    assert generator.check_outputs(generator.expected_outputs(payload)) == 0
    assert generator.contract_fingerprint(payload) == (
        "42f7b78b05cd5456657a991d2fa56499d4298333af8150c6299aabd9f84b5e9c"
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("contract_version",), True),
        (("contract_version",), 1.0),
        (("contract_version",), "1"),
        (("rank", "minimum"), False),
        (("axis_length", "maximum"), 1_000_000.0),
        (("maximum_indexable_volume",), "9223372036854775807"),
        (("transform_signs",), [-1, True]),
        (("movement_deltas",), [-1, 1.0]),
    ],
)
def test_source_rejects_non_json_integer_values(
    path: tuple[str, ...],
    value: object,
) -> None:
    payload = _source()
    target = payload
    for key in path[:-1]:
        child = target[key]
        assert isinstance(child, dict)
        target = child
    target[path[-1]] = value

    with pytest.raises(ValueError):
        generator.validate_contract_source(payload)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.pop("rank"),
        lambda row: row.__setitem__("unknown", 1),
        lambda row: row.__setitem__("transform_signs", [-1, -1]),
        lambda row: row.__setitem__("boundary_sides", ["-", "left"]),
        lambda row: row.__setitem__("rank", {"minimum": 4, "maximum": 2}),
        lambda row: row.__setitem__(
            "maximum_indexable_volume",
            9_223_372_036_854_775_808,
        ),
    ],
)
def test_source_rejects_invalid_structure_and_values(mutation) -> None:
    payload = _source()
    mutation(payload)

    with pytest.raises(ValueError):
        generator.validate_contract_source(payload)


def test_fingerprint_ignores_source_key_order_and_whitespace() -> None:
    payload = generator.validate_contract_source(_source())
    reordered = dict(reversed(tuple(payload.items())))

    assert generator.contract_fingerprint(reordered) == generator.contract_fingerprint(
        payload
    )


def test_check_mode_detects_missing_and_manually_edited_bindings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    first = tmp_path / "generated.py"
    second = tmp_path / "generated.hpp"
    outputs = {first: "python\n", second: "cpp\n"}

    assert generator.check_outputs(outputs) == 1
    first.write_text("python\n", encoding="utf-8")
    second.write_text("manually edited\n", encoding="utf-8")
    assert generator.check_outputs(outputs) == 1
    second.write_text("cpp\n", encoding="utf-8")
    assert generator.check_outputs(outputs) == 0


def test_rendering_is_deterministic_and_does_not_mutate_source() -> None:
    payload = generator.load_contract_source()
    original = copy.deepcopy(payload)

    assert generator.expected_outputs(payload) == generator.expected_outputs(payload)
    assert payload == original
