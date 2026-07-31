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
        (lambda row: row.__setitem__("dimension", 5), "board_dimensions length"),
        (lambda row: row.__setitem__("board_dimensions", [4, 0]), "positive integers"),
        (
            lambda row: row["gluings"][0]["source"].__setitem__("axis", "w"),
            "outside the contract dimension",
        ),
        (
            lambda row: row["gluings"][0]["transform"].__setitem__("signs", [0]),
            "signs must contain",
        ),
        (
            lambda row: row["gluings"][0]["transform"].__setitem__(
                "permutation", ["0"]
            ),
            "permutation must contain integers",
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
