from __future__ import annotations

import json

from tools.experiments.governance_manifest_quality.baseline import (
    BASELINE_PATH,
    ROOT,
    require_frozen_baseline_snapshot,
)
from tools.experiments.governance_manifest_quality.measurement import (
    measure_trajectory,
    normalize_trajectory,
)
from tools.experiments.governance_manifest_quality.postmortem import (
    build_postmortem_aggregate,
    postmortem_from_trajectory,
)
from tools.experiments.governance_manifest_quality.reporting import build_aggregate

SCHEMA_ROOT = ROOT / "tools/experiments/governance_manifest_quality/schemas"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def _assert_required_properties(schema: dict, payload: dict) -> None:
    assert set(schema["required"]) <= set(payload)
    assert set(payload) <= set(schema["properties"])


def test_all_experiment_schemas_are_json_objects() -> None:
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"


def test_frozen_declaration_matches_its_structural_schema() -> None:
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    schema = _schema("frozen_baseline.schema.json")
    _assert_required_properties(schema, payload)
    for field in ("repository", "workspace_governance", "machine_policy", "thresholds"):
        _assert_required_properties(schema["properties"][field], payload[field])


def test_generated_records_match_declared_top_level_contracts() -> None:
    fingerprint = require_frozen_baseline_snapshot(ROOT)
    trajectory = normalize_trajectory(
        {
            "schema_version": 1,
            "source": {"source_id": "schema-contract", "source_format": "test"},
            "events": [],
        }
    )
    aggregate = build_aggregate([measure_trajectory(trajectory)], [])
    _assert_required_properties(
        _schema("baseline_fingerprint.schema.json"), fingerprint
    )
    _assert_required_properties(_schema("trajectory.schema.json"), trajectory)
    _assert_required_properties(_schema("aggregate.schema.json"), aggregate)


def test_postmortem_records_match_declared_top_level_contracts() -> None:
    trajectory = normalize_trajectory(
        {
            "schema_version": 1,
            "source": {"source_id": "postmortem-schema", "source_format": "test"},
            "events": [],
        }
    )
    record = postmortem_from_trajectory(trajectory)
    aggregate = build_postmortem_aggregate([record])
    _assert_required_properties(_schema("postmortem.schema.json"), record)
    _assert_required_properties(_schema("postmortem_aggregate.schema.json"), aggregate)
