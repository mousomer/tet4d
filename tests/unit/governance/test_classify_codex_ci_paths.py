from __future__ import annotations

import copy

import pytest

from tools.governance.classify_codex_ci_paths import (
    PathClassificationError,
    classify_paths,
    load_path_classification_config,
)


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "requirement_to_lanes": {
            "documentation": ["documentation_governance"],
            "governance_structure": ["documentation_governance"],
            "python": ["python"],
            "godot": ["godot"],
            "native": ["native"],
            "deterministic": ["deterministic_parity"],
            "parity_or_conformance": ["deterministic_parity"],
            "integration": ["integration"],
            "human_visual": [],
            "packaging": ["packaging"],
            "platform": ["platform"],
            "release_acceptance": ["release_acceptance"],
        },
        "manual_requirements": ["human_visual"],
        "path_classification": {
            "schema_version": 1,
            "unknown_path_policy": "full_repository_gate",
            "rules": [
                {
                    "id": "documentation",
                    "patterns": ["*.md", "**/*.md"],
                    "requirements": ["documentation"],
                },
                {
                    "id": "governance",
                    "patterns": ["tools/governance/**"],
                    "requirements": ["governance_structure", "python"],
                },
                {
                    "id": "python",
                    "patterns": ["src/**/*.py", "tests/**/*.py"],
                    "requirements": ["python"],
                },
                {
                    "id": "deterministic",
                    "patterns": ["src/tet4d/engine/gameplay/**"],
                    "requirements": ["python", "deterministic"],
                },
                {
                    "id": "godot",
                    "patterns": ["godot/**"],
                    "requirements": ["godot"],
                },
                {
                    "id": "native",
                    "patterns": ["native/**"],
                    "requirements": ["native"],
                },
                {
                    "id": "ci",
                    "patterns": [".github/workflows/**"],
                    "requirements": ["governance_structure", "python"],
                    "requires_full_repository_gate": True,
                },
            ],
        },
    }


def test_documentation_only_change_stays_focused() -> None:
    result = classify_paths(
        ["docs/WORKFLOW_CODEX.md"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("documentation",)
    assert result.requires_full_repository_gate is False
    assert result.unmatched_paths == ()


def test_multiple_matching_rules_compose_by_union() -> None:
    result = classify_paths(
        ["src/tet4d/engine/gameplay/state.py"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("python", "deterministic")
    assert result.classified_paths[0].matched_rules == ("python", "deterministic")


def test_cross_subsystem_paths_compose_requirements() -> None:
    result = classify_paths(
        ["godot/Tet4D.Godot/main.gd", "native/tet4d_core/src/query.cpp"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("godot", "native")
    assert result.requires_full_repository_gate is False


def test_full_gate_rule_preserves_local_requirements() -> None:
    result = classify_paths(
        [".github/workflows/ci.yml"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("governance_structure", "python")
    assert result.requires_full_repository_gate is True
    assert result.full_gate_reasons == (
        "full-gate rule for .github/workflows/ci.yml: ci",
    )


def test_unmatched_path_forces_full_gate_and_all_automated_requirements() -> None:
    config = load_path_classification_config(_payload())
    result = classify_paths(["assets/new_binary.dat"], config=config)

    assert result.requires_full_repository_gate is True
    assert result.unmatched_paths == ("assets/new_binary.dat",)
    assert "human_visual" not in result.verification_requirements
    assert set(result.verification_requirements) == set(config.automated_requirements)


def test_no_changed_paths_produces_review_only_shape() -> None:
    result = classify_paths([], config=load_path_classification_config(_payload()))

    assert result.changed_paths == ()
    assert result.verification_requirements == ()
    assert result.requires_full_repository_gate is False


def test_duplicate_changed_paths_are_deduplicated_in_order() -> None:
    result = classify_paths(
        ["README.md", "README.md", "docs/README.md"],
        config=load_path_classification_config(_payload()),
    )

    assert result.changed_paths == ("README.md", "docs/README.md")


def test_parent_traversal_path_is_rejected() -> None:
    with pytest.raises(PathClassificationError, match="repository-relative"):
        classify_paths(
            ["../outside.py"],
            config=load_path_classification_config(_payload()),
        )


def test_backslash_path_is_rejected() -> None:
    with pytest.raises(PathClassificationError, match="POSIX separators"):
        classify_paths(
            [r"src\tet4d\engine.py"],
            config=load_path_classification_config(_payload()),
        )


def test_duplicate_rule_ids_are_rejected() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    rules = block["rules"]
    assert isinstance(rules, list)
    rules.append(copy.deepcopy(rules[0]))

    with pytest.raises(PathClassificationError, match="duplicate ids"):
        load_path_classification_config(payload)


def test_unknown_rule_requirement_is_rejected() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    rules = block["rules"]
    assert isinstance(rules, list)
    rule = rules[0]
    assert isinstance(rule, dict)
    rule["requirements"] = ["unknown"]

    with pytest.raises(PathClassificationError, match="unknown identifiers"):
        load_path_classification_config(payload)


def test_unknown_path_policy_is_conservative_and_fixed() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    block["unknown_path_policy"] = "ignore"

    with pytest.raises(PathClassificationError, match="full_repository_gate"):
        load_path_classification_config(payload)


def test_absolute_rule_pattern_is_rejected() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    rules = block["rules"]
    assert isinstance(rules, list)
    rule = rules[0]
    assert isinstance(rule, dict)
    rule["patterns"] = ["/tmp/**"]

    with pytest.raises(PathClassificationError, match="repository-relative"):
        load_path_classification_config(payload)
