from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tet4d.generated import topology_contract_v1 as contract

REPO_ROOT = Path(__file__).resolve().parents[3]
NATIVE_TEST_BIN = (
    REPO_ROOT
    / "native"
    / "tet4d_core"
    / "build"
    / "tests"
    / "topology_contract_foundation_tests"
)


def _native_metadata() -> dict[str, object]:
    if not NATIVE_TEST_BIN.exists():
        pytest.skip("native topology contract foundation test binary is not built")
    completed = subprocess.run(
        [str(NATIVE_TEST_BIN), "--contract-metadata"],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_generated_python_and_cpp_contract_metadata_match() -> None:
    assert _native_metadata() == {
        "axis_length": {
            "maximum": contract.MAXIMUM_AXIS_LENGTH,
            "minimum": contract.MINIMUM_AXIS_LENGTH,
        },
        "axis_names": list(contract.AXIS_NAMES),
        "boundary_sides": list(contract.VALID_BOUNDARY_SIDES),
        "contract": contract.CONTRACT_NAME,
        "contract_fingerprint": contract.CONTRACT_FINGERPRINT,
        "contract_version": contract.CONTRACT_VERSION,
        "maximum_indexable_volume": contract.MAXIMUM_INDEXABLE_VOLUME,
        "movement_deltas": list(contract.VALID_MOVEMENT_DELTAS),
        "rank": {
            "maximum": contract.MAXIMUM_RANK,
            "minimum": contract.MINIMUM_RANK,
        },
        "transform_signs": list(contract.VALID_TRANSFORM_SIGNS),
    }
