from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LANE_CONFIG_PATH = PROJECT_ROOT / "config/project/codex_ci_lanes.json"


class PathClassificationError(ValueError):
    """Raised when changed paths or their machine classification are invalid."""


@dataclass(frozen=True)
class PathRule:
    rule_id: str
    patterns: tuple[str, ...]
    requirements: tuple[str, ...]
    requires_full_repository_gate: bool


@dataclass(frozen=True)
class PathClassificationConfig:
    requirement_order: tuple[str, ...]
    automated_requirements: tuple[str, ...]
    unknown_path_policy: str
    cross_layer_requirements: tuple[str, ...]
    cross_layer_verification_requirement: str
    rules: tuple[PathRule, ...]


@dataclass(frozen=True)
class ClassifiedPath:
    path: str
    matched_rules: tuple[str, ...]
    requirements: tuple[str, ...]
    requires_full_repository_gate: bool


@dataclass(frozen=True)
class PathClassification:
    changed_paths: tuple[str, ...]
    classified_paths: tuple[ClassifiedPath, ...]
    unmatched_paths: tuple[str, ...]
    verification_requirements: tuple[str, ...]
    cross_layer_detected: bool
    requires_full_repository_gate: bool
    full_gate_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "repository_changed": bool(self.changed_paths),
            "changed_paths": list(self.changed_paths),
            "classified_paths": [
                {
                    "path": item.path,
                    "matched_rules": list(item.matched_rules),
                    "requirements": list(item.requirements),
                    "requires_full_repository_gate": (
                        item.requires_full_repository_gate
                    ),
                }
                for item in self.classified_paths
            ],
            "unmatched_paths": list(self.unmatched_paths),
            "verification_requirements": list(self.verification_requirements),
            "cross_layer_detected": self.cross_layer_detected,
            "requires_full_repository_gate": self.requires_full_repository_gate,
            "full_gate_reasons": list(self.full_gate_reasons),
        }


def _load_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PathClassificationError(f"missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PathClassificationError(f"invalid {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PathClassificationError(f"{label} must be a JSON object")
    return payload


def _positive_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise PathClassificationError(f"{field} must be a positive integer")
    return value


def _non_empty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PathClassificationError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(
    value: object,
    *,
    field: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise PathClassificationError(f"{field} must be a list[str]")
    values = tuple(_non_empty_string(item, field=f"{field}[]") for item in value)
    if not allow_empty and not values:
        raise PathClassificationError(f"{field} must not be empty")
    if len(values) != len(set(values)):
        raise PathClassificationError(f"{field} must not contain duplicates")
    return values


def _bool(value: object, *, field: str, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise PathClassificationError(f"{field} must be a boolean")
    return value


def _requirement_order(payload: dict[str, object]) -> tuple[str, ...]:
    mapping = payload.get("requirement_to_lanes")
    if not isinstance(mapping, dict) or not mapping:
        raise PathClassificationError("requirement_to_lanes must be a non-empty object")
    return tuple(
        _non_empty_string(key, field="requirement_to_lanes key") for key in mapping
    )


def _automated_requirements(
    payload: dict[str, object], requirement_order: tuple[str, ...]
) -> tuple[str, ...]:
    manual = set(
        _string_list(
            payload.get("manual_requirements", []),
            field="manual_requirements",
            allow_empty=True,
        )
    )
    unknown = sorted(manual - set(requirement_order))
    if unknown:
        raise PathClassificationError(
            "manual_requirements references unknown requirements: " + ", ".join(unknown)
        )
    return tuple(item for item in requirement_order if item not in manual)


def _parse_rule(
    raw: object,
    *,
    index: int,
    known_requirements: tuple[str, ...],
) -> PathRule:
    field = f"path_classification.rules[{index}]"
    if not isinstance(raw, dict):
        raise PathClassificationError(f"{field} must be an object")
    rule_id = _non_empty_string(raw.get("id"), field=f"{field}.id")
    patterns = _string_list(raw.get("patterns"), field=f"{field}.patterns")
    for pattern in patterns:
        if pattern.startswith("/") or "\\" in pattern:
            raise PathClassificationError(
                f"{field}.patterns must use repository-relative POSIX globs"
            )
        if ".." in PurePosixPath(pattern).parts:
            raise PathClassificationError(
                f"{field}.patterns must not contain parent traversal"
            )
    requirements = _string_list(raw.get("requirements"), field=f"{field}.requirements")
    unknown = sorted(set(requirements) - set(known_requirements))
    if unknown:
        raise PathClassificationError(
            f"{field}.requirements contains unknown identifiers: " + ", ".join(unknown)
        )
    return PathRule(
        rule_id=rule_id,
        patterns=patterns,
        requirements=requirements,
        requires_full_repository_gate=_bool(
            raw.get("requires_full_repository_gate"),
            field=f"{field}.requires_full_repository_gate",
        ),
    )


def _cross_layer_contract(
    block: dict[str, object],
    *,
    requirement_order: tuple[str, ...],
    automated_requirements: tuple[str, ...],
) -> tuple[tuple[str, ...], str]:
    layer_requirements = _string_list(
        block.get("cross_layer_requirements"),
        field="path_classification.cross_layer_requirements",
    )
    if len(layer_requirements) < 2:
        raise PathClassificationError(
            "path_classification.cross_layer_requirements must contain at least two ids"
        )
    unknown = sorted(set(layer_requirements) - set(automated_requirements))
    if unknown:
        raise PathClassificationError(
            "path_classification.cross_layer_requirements contains unknown or manual "
            "requirements: " + ", ".join(unknown)
        )
    integration_requirement = _non_empty_string(
        block.get("cross_layer_verification_requirement"),
        field="path_classification.cross_layer_verification_requirement",
    )
    if integration_requirement not in requirement_order:
        raise PathClassificationError(
            "path_classification.cross_layer_verification_requirement is unknown"
        )
    return layer_requirements, integration_requirement


def load_path_classification_config(
    payload: dict[str, object],
) -> PathClassificationConfig:
    _positive_int(payload.get("schema_version"), field="schema_version")
    requirement_order = _requirement_order(payload)
    automated_requirements = _automated_requirements(payload, requirement_order)
    block = payload.get("path_classification")
    if not isinstance(block, dict):
        raise PathClassificationError("path_classification must be an object")
    _positive_int(
        block.get("schema_version"), field="path_classification.schema_version"
    )
    unknown_path_policy = _non_empty_string(
        block.get("unknown_path_policy"),
        field="path_classification.unknown_path_policy",
    )
    if unknown_path_policy != "full_repository_gate":
        raise PathClassificationError(
            "path_classification.unknown_path_policy must be 'full_repository_gate'"
        )
    cross_layer_requirements, integration_requirement = _cross_layer_contract(
        block,
        requirement_order=requirement_order,
        automated_requirements=automated_requirements,
    )
    raw_rules = block.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise PathClassificationError(
            "path_classification.rules must be a non-empty list"
        )
    rules = tuple(
        _parse_rule(
            raw,
            index=index,
            known_requirements=requirement_order,
        )
        for index, raw in enumerate(raw_rules)
    )
    ids = tuple(rule.rule_id for rule in rules)
    if len(ids) != len(set(ids)):
        raise PathClassificationError(
            "path_classification.rules must not contain duplicate ids"
        )
    return PathClassificationConfig(
        requirement_order=requirement_order,
        automated_requirements=automated_requirements,
        unknown_path_policy=unknown_path_policy,
        cross_layer_requirements=cross_layer_requirements,
        cross_layer_verification_requirement=integration_requirement,
        rules=rules,
    )


def _normalise_path(raw: str) -> str:
    value = _non_empty_string(raw, field="changed path")
    if "\\" in value:
        raise PathClassificationError(
            f"changed path must use POSIX separators: {value!r}"
        )
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or value.startswith("./"):
        raise PathClassificationError(
            f"changed path must be canonical and repository-relative: {value!r}"
        )
    return path.as_posix()


def _ordered_subset(values: set[str], order: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(item for item in order if item in values)


def _matching_rules(path: str, rules: tuple[PathRule, ...]) -> tuple[PathRule, ...]:
    return tuple(
        rule
        for rule in rules
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in rule.patterns)
    )


def _apply_cross_layer_requirement(
    requirements: set[str], config: PathClassificationConfig
) -> bool:
    selected_layers = requirements.intersection(config.cross_layer_requirements)
    cross_layer_detected = len(selected_layers) >= 2
    if cross_layer_detected:
        requirements.add(config.cross_layer_verification_requirement)
    return cross_layer_detected


def classify_paths(
    changed_paths: list[str] | tuple[str, ...],
    *,
    config: PathClassificationConfig,
) -> PathClassification:
    normalised = tuple(dict.fromkeys(_normalise_path(path) for path in changed_paths))
    classified: list[ClassifiedPath] = []
    unmatched: list[str] = []
    requirements: set[str] = set()
    full_gate_reasons: list[str] = []

    for path in normalised:
        matches = _matching_rules(path, config.rules)
        if not matches:
            unmatched.append(path)
            full_gate_reasons.append(f"unmatched path: {path}")
            continue
        path_requirements = {
            requirement for rule in matches for requirement in rule.requirements
        }
        path_full_gate = any(rule.requires_full_repository_gate for rule in matches)
        requirements.update(path_requirements)
        if path_full_gate:
            full_gate_reasons.append(
                f"full-gate rule for {path}: "
                + ", ".join(
                    rule.rule_id
                    for rule in matches
                    if rule.requires_full_repository_gate
                )
            )
        classified.append(
            ClassifiedPath(
                path=path,
                matched_rules=tuple(rule.rule_id for rule in matches),
                requirements=_ordered_subset(
                    path_requirements, config.requirement_order
                ),
                requires_full_repository_gate=path_full_gate,
            )
        )

    requires_full_gate = bool(unmatched or full_gate_reasons)
    if unmatched:
        requirements.update(config.automated_requirements)
    cross_layer_detected = _apply_cross_layer_requirement(requirements, config)
    if normalised and not requirements:
        raise PathClassificationError(
            "repository-changing paths cannot resolve to an empty requirement set"
        )
    return PathClassification(
        changed_paths=normalised,
        classified_paths=tuple(classified),
        unmatched_paths=tuple(unmatched),
        verification_requirements=_ordered_subset(
            requirements, config.requirement_order
        ),
        cross_layer_detected=cross_layer_detected,
        requires_full_repository_gate=requires_full_gate,
        full_gate_reasons=tuple(dict.fromkeys(full_gate_reasons)),
    )


def _read_paths(path: str) -> list[str]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    return [line for line in raw.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify changed repository paths into verification requirements."
    )
    parser.add_argument(
        "paths",
        help="newline-delimited changed-path file, or - for stdin",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_LANE_CONFIG_PATH,
        help="CI lane and path-classification configuration",
    )
    args = parser.parse_args(argv)
    try:
        config = load_path_classification_config(
            _load_json_object(args.config, label="lane config")
        )
        result = classify_paths(_read_paths(args.paths), config=config)
    except (OSError, PathClassificationError) as exc:
        print(f"CI path classification failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
