from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LANE_CONFIG_PATH = PROJECT_ROOT / "config/project/codex_ci_lanes.json"


class LaneSelectionError(ValueError):
    """Raised when CI-lane configuration or resolver output is invalid."""


@dataclass(frozen=True)
class LaneConfig:
    resolution_schema_version: int
    lane_order: tuple[str, ...]
    always_run_lanes: tuple[str, ...]
    requirement_to_lanes: tuple[tuple[str, tuple[str, ...]], ...]
    manual_requirements: tuple[str, ...]
    full_repository_gate_lanes: tuple[str, ...]

    @property
    def lane_mapping(self) -> dict[str, tuple[str, ...]]:
        return dict(self.requirement_to_lanes)


@dataclass(frozen=True)
class LaneSelection:
    resolution_schema_version: int
    repository_changed: bool
    verification_requirements: tuple[str, ...]
    selected_lanes: tuple[str, ...]
    manual_requirements: tuple[str, ...]
    requires_full_repository_gate: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "resolution_schema_version": self.resolution_schema_version,
            "repository_changed": self.repository_changed,
            "verification_requirements": list(self.verification_requirements),
            "selected_lanes": list(self.selected_lanes),
            "manual_requirements": list(self.manual_requirements),
            "requires_full_repository_gate": self.requires_full_repository_gate,
        }


def _load_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LaneSelectionError(f"missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LaneSelectionError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise LaneSelectionError(f"{label} must be a JSON object")
    return payload


def _positive_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise LaneSelectionError(f"{field} must be a positive integer")
    return value


def _non_empty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LaneSelectionError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(
    value: object,
    *,
    field: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise LaneSelectionError(f"{field} must be a list[str]")
    items = tuple(_non_empty_string(item, field=f"{field}[]") for item in value)
    if not allow_empty and not items:
        raise LaneSelectionError(f"{field} must not be empty")
    if len(items) != len(set(items)):
        raise LaneSelectionError(f"{field} must not contain duplicates")
    return items


def _bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise LaneSelectionError(f"{field} must be a boolean")
    return value


def _ordered_subset(values: set[str], order: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(item for item in order if item in values)


def _validate_lane_subset(
    values: tuple[str, ...],
    *,
    known_lanes: tuple[str, ...],
    field: str,
) -> None:
    unknown = sorted(set(values) - set(known_lanes))
    if unknown:
        raise LaneSelectionError(
            f"{field} references unknown lanes: {', '.join(unknown)}"
        )


def _requirement_mapping(
    raw: object,
    *,
    lane_order: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not isinstance(raw, dict) or not raw:
        raise LaneSelectionError("requirement_to_lanes must be a non-empty object")
    mapping: list[tuple[str, tuple[str, ...]]] = []
    for raw_requirement, raw_lanes in raw.items():
        requirement = _non_empty_string(
            raw_requirement, field="requirement_to_lanes key"
        )
        lanes = _string_list(
            raw_lanes,
            field=f"requirement_to_lanes.{requirement}",
            allow_empty=True,
        )
        _validate_lane_subset(
            lanes,
            known_lanes=lane_order,
            field=f"requirement_to_lanes.{requirement}",
        )
        mapping.append((requirement, lanes))
    return tuple(mapping)


def load_lane_config(payload: dict[str, object]) -> LaneConfig:
    _positive_int(payload.get("schema_version"), field="schema_version")
    resolution_schema_version = _positive_int(
        payload.get("resolution_schema_version"),
        field="resolution_schema_version",
    )
    lane_order = _string_list(payload.get("lane_order"), field="lane_order")
    always_run_lanes = _string_list(
        payload.get("always_run_lanes"), field="always_run_lanes"
    )
    full_gate_lanes = _string_list(
        payload.get("full_repository_gate_lanes"),
        field="full_repository_gate_lanes",
    )
    _validate_lane_subset(
        always_run_lanes,
        known_lanes=lane_order,
        field="always_run_lanes",
    )
    _validate_lane_subset(
        full_gate_lanes,
        known_lanes=lane_order,
        field="full_repository_gate_lanes",
    )
    if set(full_gate_lanes) != set(lane_order):
        raise LaneSelectionError(
            "full_repository_gate_lanes must contain every configured lane"
        )
    if not set(always_run_lanes).issubset(full_gate_lanes):
        raise LaneSelectionError(
            "full_repository_gate_lanes must include every always-run lane"
        )

    mapping = _requirement_mapping(
        payload.get("requirement_to_lanes"), lane_order=lane_order
    )
    mapping_dict = dict(mapping)
    manual_requirements = _string_list(
        payload.get("manual_requirements"),
        field="manual_requirements",
        allow_empty=True,
    )
    unknown_manual = sorted(set(manual_requirements) - set(mapping_dict))
    if unknown_manual:
        raise LaneSelectionError(
            "manual_requirements references unknown requirements: "
            + ", ".join(unknown_manual)
        )
    for requirement, lanes in mapping:
        is_manual = requirement in manual_requirements
        if is_manual and lanes:
            raise LaneSelectionError(
                f"manual requirement {requirement!r} must not map to automated lanes"
            )
        if not is_manual and not lanes:
            raise LaneSelectionError(
                f"automated requirement {requirement!r} must map to at least one lane"
            )

    return LaneConfig(
        resolution_schema_version=resolution_schema_version,
        lane_order=lane_order,
        always_run_lanes=always_run_lanes,
        requirement_to_lanes=mapping,
        manual_requirements=manual_requirements,
        full_repository_gate_lanes=full_gate_lanes,
    )


def _resolution_requirements(payload: dict[str, object]) -> tuple[str, ...]:
    return _string_list(
        payload.get("verification_requirements"),
        field="verification_requirements",
        allow_empty=True,
    )


def select_lanes(
    resolution: dict[str, object],
    *,
    config: LaneConfig,
) -> LaneSelection:
    resolution_schema_version = _positive_int(
        resolution.get("schema_version"), field="resolution.schema_version"
    )
    if resolution_schema_version != config.resolution_schema_version:
        raise LaneSelectionError(
            "resolution schema version does not match lane configuration"
        )
    repository_changed = _bool(
        resolution.get("repository_changed"), field="repository_changed"
    )
    requirements = _resolution_requirements(resolution)
    requires_full_gate = _bool(
        resolution.get("requires_full_repository_gate"),
        field="requires_full_repository_gate",
    )

    if not repository_changed:
        if requirements:
            raise LaneSelectionError(
                "unchanged repository resolution must not select verification requirements"
            )
        if requires_full_gate:
            raise LaneSelectionError(
                "unchanged repository resolution must not require the full gate"
            )
        return LaneSelection(
            resolution_schema_version=resolution_schema_version,
            repository_changed=False,
            verification_requirements=(),
            selected_lanes=(),
            manual_requirements=(),
            requires_full_repository_gate=False,
        )
    if not requirements:
        raise LaneSelectionError(
            "repository-changing resolution must select verification requirements"
        )

    mapping = config.lane_mapping
    unknown_requirements = sorted(set(requirements) - set(mapping))
    if unknown_requirements:
        raise LaneSelectionError(
            "verification requirements are not mapped to lanes: "
            + ", ".join(unknown_requirements)
        )

    selected = set(config.always_run_lanes)
    for requirement in requirements:
        selected.update(mapping[requirement])
    if requires_full_gate:
        selected.update(config.full_repository_gate_lanes)

    manual = tuple(
        requirement
        for requirement in requirements
        if requirement in config.manual_requirements
    )
    return LaneSelection(
        resolution_schema_version=resolution_schema_version,
        repository_changed=True,
        verification_requirements=requirements,
        selected_lanes=_ordered_subset(selected, config.lane_order),
        manual_requirements=manual,
        requires_full_repository_gate=requires_full_gate,
    )


def github_outputs(
    selection: LaneSelection,
    *,
    config: LaneConfig,
) -> dict[str, str]:
    selected = set(selection.selected_lanes)
    outputs = {
        f"lane_{lane}": "true" if lane in selected else "false"
        for lane in config.lane_order
    }
    outputs.update(
        {
            "repository_changed": ("true" if selection.repository_changed else "false"),
            "selected_lanes": json.dumps(
                list(selection.selected_lanes), separators=(",", ":")
            ),
            "manual_requirements": json.dumps(
                list(selection.manual_requirements), separators=(",", ":")
            ),
            "requires_full_repository_gate": (
                "true" if selection.requires_full_repository_gate else "false"
            ),
        }
    )
    return outputs


def write_github_outputs(
    path: Path,
    selection: LaneSelection,
    *,
    config: LaneConfig,
) -> None:
    with path.open("a", encoding="utf-8") as output_file:
        for key, value in github_outputs(selection, config=config).items():
            output_file.write(f"{key}={value}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Map Codex verification requirements to stable CI lanes."
    )
    parser.add_argument("resolution", type=Path, help="resolver output JSON")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_LANE_CONFIG_PATH,
        help="CI lane mapping configuration",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="append deterministic lane outputs to a GitHub Actions output file",
    )
    args = parser.parse_args(argv)
    try:
        config = load_lane_config(_load_json_object(args.config, label="lane config"))
        resolution = _load_json_object(args.resolution, label="resolver output")
        selection = select_lanes(resolution, config=config)
        if args.github_output is not None:
            write_github_outputs(args.github_output, selection, config=config)
    except (OSError, LaneSelectionError) as exc:
        print(f"CI lane selection failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(selection.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
