#!/usr/bin/env python3
"""Validate a Design Laboratory nomination without promoting it.

This helper deliberately performs no repository writes. A successful result
means the portable candidate conforms to the current registry and ownership
map; human review and an ordinary repository change remain mandatory.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

PRESET_TYPE = "tet4d.design_candidate_preset"
PRESET_SCHEMA_VERSION = 1
SUMMARY_TYPE = "tet4d.design_comparison_summary"
SUMMARY_SCHEMA_VERSION = 1
SAFE_ID = re.compile(r"^[a-z0-9_-]{1,80}$")
REQUIRED_FILES = ("preset.json", "comparison_summary.json", "DESIGN_PROPOSAL.md")


class ValidationError(ValueError):
    """A portable design bundle violates the current promotion contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path.name}: unreadable JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path.name}: root must be an object")
    return value


def validate_bundle(bundle_dir: Path, registry_path: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_FILES if not (bundle_dir / name).is_file()]
    if missing:
        raise ValidationError(f"missing required outputs: {', '.join(missing)}")
    registry = load_json(registry_path)
    specs = load_registry_specs(registry)
    preset_id, properties = validate_preset(bundle_dir / "preset.json", specs)
    records = validate_summary(bundle_dir / "comparison_summary.json", preset_id)
    validate_proposal(bundle_dir / "DESIGN_PROPOSAL.md", preset_id)
    return {
        "preset_id": preset_id,
        "property_count": len(properties),
        "evaluation_count": len(records),
        "registry_schema_version": registry["schema_version"],
    }


def load_registry_specs(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    settings = registry.get("settings")
    if registry.get("schema_version") != 3 or not isinstance(settings, list):
        raise ValidationError("canonical settings registry is unsupported")
    specs: dict[str, dict[str, Any]] = {}
    for raw in settings:
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
            raise ValidationError(
                "canonical settings registry contains a malformed entry"
            )
        setting_id = raw["id"]
        if setting_id in specs:
            raise ValidationError(
                f"canonical registry has duplicate property {setting_id}"
            )
        owner = raw.get("semantic_owner")
        if not isinstance(owner, str) or not owner:
            raise ValidationError(
                f"canonical property {setting_id} does not have exactly one owner"
            )
        specs[setting_id] = raw
    return specs


def validate_preset(
    preset_path: Path,
    specs: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    preset = load_json(preset_path)
    if (
        preset.get("preset_type") != PRESET_TYPE
        or preset.get("preset_schema_version") != PRESET_SCHEMA_VERSION
    ):
        raise ValidationError("preset.json: unsupported envelope")
    preset_id = preset.get("preset_id")
    if not isinstance(preset_id, str) or SAFE_ID.fullmatch(preset_id) is None:
        raise ValidationError("preset.json: invalid stable preset ID")
    properties = preset.get("properties")
    owners = preset.get("semantic_owners")
    if not isinstance(properties, dict) or not isinstance(owners, dict):
        raise ValidationError(
            "preset.json: properties and semantic_owners must be objects"
        )
    expected_ids = set(specs)
    actual_ids = set(properties)
    if actual_ids != expected_ids:
        unknown = sorted(actual_ids - expected_ids)
        missing_properties = sorted(expected_ids - actual_ids)
        raise ValidationError(
            "preset.json: property inventory mismatch"
            f"; unknown={unknown}; missing={missing_properties}"
        )
    if set(owners) != actual_ids:
        raise ValidationError(
            "preset.json: semantic-owner map must cover every property exactly once"
        )
    for setting_id, value in properties.items():
        spec = specs[setting_id]
        validate_value(setting_id, value, spec)
        if owners[setting_id] != spec["semantic_owner"]:
            raise ValidationError(
                f"preset.json: {setting_id} owner {owners[setting_id]!r} "
                f"does not match {spec['semantic_owner']!r}"
            )
    return preset_id, properties


def validate_summary(summary_path: Path, preset_id: str) -> list[Any]:
    summary = load_json(summary_path)
    if (
        summary.get("summary_type") != SUMMARY_TYPE
        or summary.get("summary_schema_version") != SUMMARY_SCHEMA_VERSION
    ):
        raise ValidationError("comparison_summary.json: unsupported envelope")
    if summary.get("nominated_preset_id") != preset_id:
        raise ValidationError(
            "comparison_summary.json: nominated preset identity disagrees"
        )
    records = summary.get("evaluation_records")
    if not isinstance(records, list):
        raise ValidationError(
            "comparison_summary.json: evaluation_records must be an array"
        )
    for index, record in enumerate(records):
        if not isinstance(record, dict) or record.get("scenario_id") not in summary.get(
            "evaluated_scenario_ids", []
        ):
            raise ValidationError(
                f"comparison_summary.json: record {index} is internally inconsistent"
            )
        presets = record.get("presets")
        if not isinstance(presets, dict) or not any(
            isinstance(presets.get(arm), dict)
            and presets[arm].get("preset_id") == preset_id
            for arm in ("A", "B")
        ):
            raise ValidationError(
                f"comparison_summary.json: record {index} does not compare the nominee"
            )
    return records


def validate_proposal(proposal_path: Path, preset_id: str) -> None:
    proposal = proposal_path.read_text(encoding="utf-8")
    for required_text in (
        "Review input only",
        "## Canonical property changes",
        f"Preset ID: `{preset_id}`",
    ):
        if required_text not in proposal:
            raise ValidationError(f"DESIGN_PROPOSAL.md: missing {required_text!r}")


def validate_value(setting_id: str, value: Any, spec: dict[str, Any]) -> None:
    value_type = spec.get("value_type")
    if value_type == "bool":
        if type(value) is not bool:
            raise ValidationError(f"preset.json: {setting_id} must be boolean")
        return
    if value_type == "enum":
        options = {
            option.get("value")
            for option in spec.get("options", [])
            if isinstance(option, dict)
        }
        if not isinstance(value, str) or value not in options:
            raise ValidationError(
                f"preset.json: {setting_id} has invalid enum value {value!r}"
            )
        return
    if value_type == "float":
        if type(value) not in (int, float) or not math.isfinite(float(value)):
            raise ValidationError(f"preset.json: {setting_id} must be finite numeric")
        if not float(spec["min"]) <= float(value) <= float(spec["max"]):
            raise ValidationError(f"preset.json: {setting_id} is out of range")
        return
    if value_type == "size":
        if (
            not isinstance(value, list)
            or len(value) != 2
            or any(type(item) is not int for item in value)
            or any(
                value[index] < spec["min"][index] or value[index] > spec["max"][index]
                for index in range(2)
            )
        ):
            raise ValidationError(
                f"preset.json: {setting_id} must be a legal integer size"
            )
        return
    raise ValidationError(
        f"canonical registry exposes unsupported value type {value_type!r}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bundle",
        type=Path,
        help="Directory containing preset.json and proposal evidence",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("godot/Tet4D.Godot/config/shell_settings_registry.json"),
        help="Canonical settings registry (default: repository path)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = validate_bundle(args.bundle, args.registry)
    except ValidationError as exc:
        print(f"Design export INVALID: {exc}")
        return 1
    print(
        "Design export VALID: "
        f"{result['preset_id']} · {result['property_count']} canonical properties · "
        f"{result['evaluation_count']} evaluation records"
    )
    print(
        "Promotion remains manual: compare baseline, update design authority/catalog/fixtures, then run repository verification."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
