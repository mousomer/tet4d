from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import tools.codegen.generate_board_extent_contract as generator


def _source() -> dict[str, object]:
    return json.loads(generator.SOURCE_PATH.read_text(encoding="utf-8"))


def test_authoritative_source_generates_current_bindings() -> None:
    payload = generator.load_contract_source()

    assert generator.check_outputs(generator.expected_outputs(payload)) == 0
    assert generator.contract_fingerprint(payload) == (
        "c0fca19302599068efc1e6c3e68c76b2b3ba9ca3c840bb928c534bf7552e5c3e"
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("contract_version",), True),
        (("contract_version",), 1.0),
        (("contract_version",), "1"),
        (("modes", 0, "rank"), False),
        (("modes", 1, "axis_minima", 0), "4"),
        (("modes", 2, "axis_maxima", 3), 12.0),
        (("modes", 0, "native_maximum_cells"), "480"),
    ],
)
def test_source_rejects_non_json_integer_values(
    path: tuple[str | int, ...], value: object
) -> None:
    with pytest.raises(ValueError):
        generator.validate_contract_source(_source_with_mutation(path, value))


def _source_with_mutation(
    path: tuple[str | int, ...], value: object
) -> dict[str, object]:
    source = _source()
    target: object = source
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    return source


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["modes"][0].pop("rank"),
        lambda value: value["modes"][0].__setitem__("unknown", 1),
        lambda value: value["modes"][1].__setitem__("axis_order", ["X", "Y"]),
        lambda value: value["modes"][2].__setitem__("axis_minima", [4, 6, 2, 13]),
        lambda value: value["modes"][1].__setitem__(
            "canonical_default_shape", [6, 25, 6]
        ),
        lambda value: value["modes"][0].__setitem__("native_maximum_cells", 481),
    ],
)
def test_source_rejects_invalid_structure_and_values(mutation) -> None:
    payload = _source()
    mutation(payload)

    with pytest.raises(ValueError):
        generator.validate_contract_source(payload)


def test_checked_product_rejects_overflow() -> None:
    with pytest.raises(ValueError, match="overflows"):
        generator._checked_product([generator.SIGNED_64_MAX, 2], "test")


def test_check_mode_detects_missing_and_manually_edited_bindings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
