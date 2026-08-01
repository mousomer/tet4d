from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tet4d.engine.topology_explorer import (
    CanonicalTopologyContract,
    canonical_topology_payload,
    canonicalize_topology_contract,
    topology_contract_identity,
    topology_contract_profile,
)
from tet4d.engine.topology_explorer.glue_model import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    mobius_strip_profile_2d,
    sphere_profile_4d,
    swapped_xz_profile_3d,
)
from tet4d.generated.topology_contract_v1 import (
    MAXIMUM_AXIS_LENGTH,
    MAXIMUM_INDEXABLE_VOLUME,
)

FIXTURE = Path("tests/fixtures/parity/canonical_topology_contract_v1.json")


@pytest.mark.parametrize(
    ("profile", "dims"),
    [
        (mobius_strip_profile_2d(), (5, 7)),
        (swapped_xz_profile_3d(), (4, 6, 4)),
        (sphere_profile_4d(), (4, 4, 4, 4)),
    ],
)
def test_contract_round_trip_is_idempotent_and_stable(profile, dims) -> None:
    payload = canonical_topology_payload(profile, dims)
    restored = CanonicalTopologyContract.from_payload(payload)

    assert restored.payload == payload
    assert canonicalize_topology_contract(restored.payload) == payload
    assert restored.identity == topology_contract_identity(payload)
    assert len(restored.identity) == 64


def test_equivalent_order_direction_ids_and_disabled_rows_normalize_identically() -> (
    None
):
    profile = axis_wrap_profile(dimension=2, wrapped_axes=(0, 1))
    first = canonical_topology_payload(profile, (5, 7))
    reversed_profile = ExplorerTopologyProfile(
        dimension=2,
        gluings=tuple(
            type(glue)(
                glue_id=f"display-{index}",
                source=glue.target,
                target=glue.source,
                transform=glue.transform.inverse(),
                enabled=True,
            )
            for index, glue in enumerate(reversed(profile.gluings))
        )
        + (
            type(profile.gluings[0])(
                glue_id="disabled-editor-row",
                source=profile.gluings[0].source,
                target=profile.gluings[0].target,
                transform=profile.gluings[0].transform,
                enabled=False,
            ),
        ),
    )

    second = canonical_topology_payload(reversed_profile, (5, 7))
    assert second == first
    assert topology_contract_identity(second) == topology_contract_identity(first)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda row: row.__setitem__("schema_version", 2), "schema version"),
        (lambda row: row.__setitem__("dimension", 5), "between 2 and 4"),
        (lambda row: row.__setitem__("board_dimensions", [4, 0]), "at least 1"),
        (
            lambda row: row["gluings"][0]["source"].__setitem__("axis", "w"),
            "outside the contract dimension",
        ),
        (
            lambda row: row["gluings"][0]["transform"].__setitem__("signs", [0]),
            "must be one of -1, 1",
        ),
        (
            lambda row: row["gluings"][0]["transform"].__setitem__(
                "permutation", ["0"]
            ),
            "must be an integer",
        ),
        (lambda row: row.__setitem__("unexpected", True), "fields must be exactly"),
    ],
)
def test_contract_rejects_invalid_payloads(mutation, message: str) -> None:
    payload = canonical_topology_payload(mobius_strip_profile_2d(), (4, 5))
    broken = copy.deepcopy(payload)
    mutation(broken)

    with pytest.raises(ValueError, match=message):
        topology_contract_profile(broken)


def test_contract_rejects_non_bijective_cross_axis_dimensions() -> None:
    with pytest.raises(ValueError, match="not bijective"):
        canonical_topology_payload(swapped_xz_profile_3d(), (4, 6, 7))


def test_board_dimensions_participate_in_identity() -> None:
    profile = axis_wrap_profile(dimension=2, wrapped_axes=(0,))
    assert topology_contract_identity(
        canonical_topology_payload(profile, (4, 5))
    ) != topology_contract_identity(canonical_topology_payload(profile, (6, 5)))


def test_shared_2d_3d_4d_contract_fixture_is_strict_and_canonical() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["schema_version"] == 1
    assert [case["name"] for case in fixture["cases"]] == [
        "bounded_2d",
        "reflected_2d",
        "cross_axis_3d",
        "reflected_4d",
    ]
    for case in fixture["cases"]:
        contract = CanonicalTopologyContract.from_payload(case["contract"])
        assert contract.payload == case["contract"]
        assert len(contract.identity) == 64


@pytest.mark.parametrize("version", [True, False, 1.0, "1", None, [], {}])
def test_contract_version_requires_exact_integer_one(version: object) -> None:
    payload = canonical_topology_payload(mobius_strip_profile_2d(), (4, 5))
    payload["schema_version"] = version

    with pytest.raises(ValueError, match="schema_version|schema version"):
        topology_contract_profile(payload)


@pytest.mark.parametrize("dimension", [2, 4])
def test_contract_accepts_shared_rank_boundaries(dimension: int) -> None:
    payload = {
        "schema": "tet4d.topology_contract",
        "schema_version": 1,
        "dimension": dimension,
        "board_dimensions": [1] * dimension,
        "gluings": [],
    }

    assert topology_contract_profile(payload)[1] == (1,) * dimension


@pytest.mark.parametrize("dimension", [1, 5])
def test_contract_rejects_rank_outside_shared_boundaries(dimension: int) -> None:
    payload = {
        "schema": "tet4d.topology_contract",
        "schema_version": 1,
        "dimension": dimension,
        "board_dimensions": [1] * dimension,
        "gluings": [],
    }

    with pytest.raises(ValueError, match="dimension must be between 2 and 4"):
        topology_contract_profile(payload)


@pytest.mark.parametrize(
    "size",
    [True, False, 3.0, 3.9, "3", None, [], {}, 0, -1, MAXIMUM_AXIS_LENGTH + 1],
)
def test_contract_board_dimensions_require_bounded_exact_integers(
    size: object,
) -> None:
    payload = canonical_topology_payload(mobius_strip_profile_2d(), (4, 5))
    payload["board_dimensions"][0] = size

    with pytest.raises(ValueError, match=r"board_dimensions\[0\]"):
        topology_contract_profile(payload)


@pytest.mark.parametrize(
    "dims",
    [(3.9, 4.8), ("3", "4"), (True, 4), (0, 4), (-1, 4)],
)
def test_canonical_producer_rejects_coercible_dimensions(dims) -> None:
    with pytest.raises(ValueError, match="board_dimensions"):
        canonical_topology_payload(mobius_strip_profile_2d(), dims)


def test_contract_accepts_axis_and_volume_boundaries() -> None:
    bounded_2d = ExplorerTopologyProfile(2, ())
    bounded_4d = ExplorerTopologyProfile(4, ())
    assert canonical_topology_payload(
        bounded_2d,
        (1, MAXIMUM_AXIS_LENGTH),
    )["board_dimensions"] == [1, MAXIMUM_AXIS_LENGTH]
    exact_maximum = (454_279, 337, 92_737, 649_657)
    assert canonical_topology_payload(
        bounded_4d,
        exact_maximum,
    )["board_dimensions"] == list(exact_maximum)
    assert 454_279 * 337 * 92_737 * 649_657 == MAXIMUM_INDEXABLE_VOLUME


def test_contract_rejects_indexable_volume_overflow() -> None:
    with pytest.raises(ValueError, match="product exceeds"):
        canonical_topology_payload(
            ExplorerTopologyProfile(4, ()),
            (MAXIMUM_AXIS_LENGTH,) * 4,
        )


@pytest.mark.parametrize("side", [True, 1, 1.0, None, [], {}])
def test_contract_boundary_side_requires_string_before_normalization(
    side: object,
) -> None:
    payload = canonical_topology_payload(mobius_strip_profile_2d(), (4, 5))
    payload["gluings"][0]["source"]["side"] = side

    with pytest.raises(ValueError, match=r"source\.side must be a string"):
        topology_contract_profile(payload)


@pytest.mark.parametrize("axis", [True, 0, 0.0, None, [], {}])
def test_contract_boundary_axis_requires_string_before_normalization(
    axis: object,
) -> None:
    payload = canonical_topology_payload(mobius_strip_profile_2d(), (4, 5))
    payload["gluings"][0]["source"]["axis"] = axis

    with pytest.raises(ValueError, match=r"source\.axis must be a string"):
        topology_contract_profile(payload)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, [], {}])
def test_contract_transform_sign_requires_exact_integer(value: object) -> None:
    payload = canonical_topology_payload(mobius_strip_profile_2d(), (4, 5))
    payload["gluings"][0]["transform"]["signs"][0] = value

    with pytest.raises(ValueError, match=r"signs\[0\]"):
        topology_contract_profile(payload)


@pytest.mark.parametrize("value", [True, False, 0.0, "0", None, [], {}])
def test_contract_transform_permutation_requires_exact_integer(value: object) -> None:
    payload = canonical_topology_payload(mobius_strip_profile_2d(), (4, 5))
    payload["gluings"][0]["transform"]["permutation"][0] = value

    with pytest.raises(ValueError, match=r"permutation\[0\]"):
        topology_contract_profile(payload)


def test_existing_fixture_identities_remain_stable() -> None:
    expected = {
        "bounded_2d": "89e73b7ef54523ac862a59cbaf1cf8518df9fb51b573cfee48fcbe10825a6039",
        "reflected_2d": "7b3e8a9d387a22129cbc9a4187c3e6e6704f75f09af82f2b268e7c45ef9e0908",
        "cross_axis_3d": "b7c243a32f9a40e646b2c74e7f440ad5db44ad882085fe48ab78cf089b52fd03",
        "reflected_4d": "1da52732a0494f1a1af8d1bd824dafc338269416c8471a045bd8ad5b50c71fb9",
    }
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert {
        case["name"]: topology_contract_identity(case["contract"])
        for case in fixture["cases"]
    } == expected
