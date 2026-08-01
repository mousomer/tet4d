from __future__ import annotations

import pytest

from tet4d.engine.topology_explorer.contract_validation import (
    checked_dimension_product,
    require_bounded_json_int,
    require_json_bool,
    require_json_int,
    require_json_int_sequence,
    require_json_string,
)
from tet4d.generated.topology_contract_v1 import MAXIMUM_INDEXABLE_VOLUME


@pytest.mark.parametrize("value", [True, False, 1.0, 3.9, "1", None, [], {}])
def test_require_json_int_rejects_coercible_values(value: object) -> None:
    with pytest.raises(ValueError, match="field must be an integer"):
        require_json_int(value, "field")


def test_exact_scalar_helpers_accept_only_their_owned_types() -> None:
    assert require_json_int(1, "integer") == 1
    assert require_json_bool(True, "boolean") is True
    assert require_json_string("x", "string") == "x"
    with pytest.raises(ValueError, match="boolean"):
        require_json_bool(1, "boolean")
    with pytest.raises(ValueError, match="string"):
        require_json_string(1, "string")


def test_bounded_integer_and_sequence_report_field_paths() -> None:
    assert require_bounded_json_int(4, "rank", minimum=2, maximum=4) == 4
    assert require_json_int_sequence(
        [0, 1],
        "permutation",
        minimum=0,
        maximum=1,
    ) == (0, 1)
    with pytest.raises(ValueError, match=r"permutation\[1\]"):
        require_json_int_sequence([0, True], "permutation")


def test_checked_dimension_product_accepts_exact_signed_64_maximum() -> None:
    dimensions = (454_279, 337, 92_737, 649_657)

    assert checked_dimension_product(dimensions) == MAXIMUM_INDEXABLE_VOLUME


def test_checked_dimension_product_rejects_overflow_before_multiplication() -> None:
    with pytest.raises(ValueError, match="board_dimensions product exceeds"):
        checked_dimension_product((1_000_000,) * 4)


@pytest.mark.parametrize("value", [True, 1.0, "1", 0, -1])
def test_checked_dimension_product_rejects_invalid_components(value: object) -> None:
    with pytest.raises(ValueError, match=r"board_dimensions\[0\]"):
        checked_dimension_product((value, 4))
