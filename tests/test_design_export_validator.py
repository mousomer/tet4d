from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools/design_lab/validate_design_export.py"
REGISTRY_PATH = ROOT / "godot/Tet4D.Godot/config/shell_settings_registry.json"


def _module():
    spec = importlib.util.spec_from_file_location("design_export_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bundle(tmp_path: Path) -> Path:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    properties = {entry["id"]: entry["default"] for entry in registry["settings"]}
    owners = {entry["id"]: entry["semantic_owner"] for entry in registry["settings"]}
    bundle = tmp_path / "candidate"
    bundle.mkdir()
    preset_id = "validator_candidate_v1"
    (bundle / "preset.json").write_text(
        json.dumps(
            {
                "preset_type": "tet4d.design_candidate_preset",
                "preset_schema_version": 1,
                "preset_id": preset_id,
                "display_name": "Validator Candidate",
                "presentation_profile_schema_version": 1,
                "properties": properties,
                "semantic_owners": owners,
            }
        ),
        encoding="utf-8",
    )
    (bundle / "comparison_summary.json").write_text(
        json.dumps(
            {
                "summary_type": "tet4d.design_comparison_summary",
                "summary_schema_version": 1,
                "nominated_preset_id": preset_id,
                "evaluated_scenario_ids": ["plain_4d_dense_v1"],
                "evaluation_records": [
                    {
                        "scenario_id": "plain_4d_dense_v1",
                        "presets": {"A": {"preset_id": "reference"}, "B": {"preset_id": preset_id}},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (bundle / "DESIGN_PROPOSAL.md").write_text(
        f"# Design Proposal: Validator\n\n> Review input only.\n\nPreset ID: `{preset_id}`\n\n## Canonical property changes\n",
        encoding="utf-8",
    )
    return bundle


def test_valid_bundle_resolves_every_property_and_owner(tmp_path: Path) -> None:
    validator = _module()
    result = validator.validate_bundle(_bundle(tmp_path), REGISTRY_PATH)
    assert result["property_count"] == 29
    assert result["evaluation_count"] == 1


@pytest.mark.parametrize("mutation", ["unknown_property", "wrong_owner", "out_of_range"])
def test_invalid_candidate_cannot_cross_promotion_boundary(tmp_path: Path, mutation: str) -> None:
    validator = _module()
    bundle = _bundle(tmp_path)
    preset = json.loads((bundle / "preset.json").read_text(encoding="utf-8"))
    invalid = copy.deepcopy(preset)
    if mutation == "unknown_property":
        invalid["properties"]["gameplay.hidden"] = True
        invalid["semantic_owners"]["gameplay.hidden"] = "GAMEPLAY"
    elif mutation == "wrong_owner":
        invalid["semantic_owners"]["ghost.opacity"] = "BOARD_PRESENTATION"
    else:
        invalid["properties"]["ghost.opacity"] = 100.0
    (bundle / "preset.json").write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(validator.ValidationError):
        validator.validate_bundle(bundle, REGISTRY_PATH)
