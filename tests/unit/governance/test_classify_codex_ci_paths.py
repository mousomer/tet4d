from __future__ import annotations

import copy
import json

import pytest

from tools.governance.classify_codex_ci_paths import (
    DEFAULT_LANE_CONFIG_PATH,
    PathClassificationConfig,
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
            "platform": [],
            "platform_macos": ["platform_macos"],
            "platform_windows": [],
            "platform_ipados": ["platform_ipados"],
            "release_acceptance": ["release_acceptance"],
        },
        "manual_requirements": ["human_visual", "platform_windows"],
        "abstract_requirements": {
            "platform": [
                "platform_macos",
                "platform_windows",
                "platform_ipados",
            ]
        },
        "path_classification": {
            "schema_version": 1,
            "unknown_path_policy": "full_repository_gate",
            "cross_layer_requirements": [
                "python",
                "godot",
                "native",
                "packaging",
            ],
            "cross_layer_verification_requirement": "integration",
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
                {
                    "id": "packaging",
                    "patterns": ["packaging/**"],
                    "requirements": ["packaging"],
                },
                {
                    "id": "packaging_macos_platform",
                    "patterns": ["packaging/godot/build_macos.sh"],
                    "requirements": ["packaging", "platform", "platform_macos"],
                },
                {
                    "id": "packaging_ipados_platform",
                    "patterns": [
                        "packaging/godot/build_ipados.sh",
                        "tests/test_ipados_native_packaging.py",
                    ],
                    "requirements": ["packaging", "platform", "platform_ipados"],
                },
            ],
        },
    }


def test_documentation_only_change_stays_focused() -> None:
    result = classify_paths(
        ["docs/governance/CHANGE_GOVERNANCE.md"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("documentation",)
    assert result.cross_layer_detected is False
    assert result.requires_full_repository_gate is False
    assert result.unmatched_paths == ()


def test_multiple_matching_rules_compose_by_union() -> None:
    result = classify_paths(
        ["src/tet4d/engine/gameplay/state.py"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("python", "deterministic")
    assert result.classified_paths[0].matched_rules == ("python", "deterministic")
    assert result.cross_layer_detected is False


def test_cross_subsystem_paths_add_integration() -> None:
    result = classify_paths(
        ["godot/Tet4D.Godot/main.gd", "native/tet4d_core/src/query.cpp"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("godot", "native", "integration")
    assert result.cross_layer_detected is True
    assert result.requires_full_repository_gate is False


def test_python_and_native_paths_add_integration() -> None:
    result = classify_paths(
        ["src/tet4d/engine/core/query.py", "native/tet4d_core/src/query.cpp"],
        config=load_path_classification_config(_payload()),
    )

    assert result.verification_requirements == ("python", "native", "integration")
    assert result.cross_layer_detected is True


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
    assert result.cross_layer_detected is True


def test_no_changed_paths_produces_review_only_shape() -> None:
    result = classify_paths([], config=load_path_classification_config(_payload()))

    assert result.changed_paths == ()
    assert result.verification_requirements == ()
    assert result.cross_layer_detected is False
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


def test_cross_layer_contract_requires_two_requirements() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    block["cross_layer_requirements"] = ["python"]

    with pytest.raises(PathClassificationError, match="at least two"):
        load_path_classification_config(payload)


def test_cross_layer_contract_rejects_manual_requirement() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    block["cross_layer_requirements"] = ["python", "human_visual"]

    with pytest.raises(PathClassificationError, match="unknown or manual"):
        load_path_classification_config(payload)


def test_cross_layer_verification_requirement_must_be_known() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    block["cross_layer_verification_requirement"] = "unknown"

    with pytest.raises(PathClassificationError, match="is unknown"):
        load_path_classification_config(payload)


def test_abstract_requirement_must_expand_to_known_requirements() -> None:
    payload = copy.deepcopy(_payload())
    payload["abstract_requirements"] = {"platform": ["platform_unknown"]}

    with pytest.raises(PathClassificationError, match="unknown requirements"):
        load_path_classification_config(payload)


def test_abstract_requirement_must_not_expand_to_itself() -> None:
    payload = copy.deepcopy(_payload())
    payload["abstract_requirements"] = {"platform": ["platform"]}

    with pytest.raises(PathClassificationError, match="must not expand to itself"):
        load_path_classification_config(payload)


def test_rule_naming_a_platform_family_needs_an_explicit_platform() -> None:
    payload = copy.deepcopy(_payload())
    block = payload["path_classification"]
    assert isinstance(block, dict)
    rules = block["rules"]
    assert isinstance(rules, list)
    rule = rules[-1]
    assert isinstance(rule, dict)
    rule["requirements"] = ["packaging", "platform"]

    with pytest.raises(PathClassificationError, match="without any explicit expansion"):
        load_path_classification_config(payload)


def test_platform_rules_do_not_leak_across_platforms() -> None:
    config = load_path_classification_config(_payload())

    ipados = classify_paths(["packaging/godot/build_ipados.sh"], config=config)
    macos = classify_paths(["packaging/godot/build_macos.sh"], config=config)

    assert "platform_ipados" in ipados.verification_requirements
    assert "platform_macos" not in ipados.verification_requirements
    assert "platform_macos" in macos.verification_requirements
    assert "platform_ipados" not in macos.verification_requirements


# --- Regression tests against the repository's real lane configuration ----


def _repository_config() -> PathClassificationConfig:
    return load_path_classification_config(
        json.loads(DEFAULT_LANE_CONFIG_PATH.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_ipados_native_packaging.py",
        "tests/test_ipados_xcode_project_validator.py",
        "tests/test_android_godot_export_validator.py",
        "tests/test_windows_godot_package_validator.py",
        "tests/test_leveling.py",
        "tests/conftest.py",
    ],
)
def test_root_level_python_tests_are_classified(path: str) -> None:
    result = classify_paths([path], config=_repository_config())

    assert result.unmatched_paths == ()
    assert "python" in result.verification_requirements
    assert result.requires_full_repository_gate is False


def test_nested_python_tests_stay_classified() -> None:
    result = classify_paths(
        [
            "tests/unit/engine/test_release_metadata.py",
            "tests/unit/boundary/test_godot_release_packaging.py",
        ],
        config=_repository_config(),
    )

    assert result.unmatched_paths == ()
    assert "python" in result.verification_requirements


def test_repository_unknown_path_still_forces_the_full_gate() -> None:
    result = classify_paths(["assets/unrouted_binary.dat"], config=_repository_config())

    assert result.unmatched_paths == ("assets/unrouted_binary.dat",)
    assert result.requires_full_repository_gate is True


def test_ipados_packaging_diff_is_proportional_and_platform_specific() -> None:
    result = classify_paths(
        [
            "packaging/godot/build_ipados.sh",
            "packaging/godot/ipados_native.py",
            "packaging/godot/validate_ipados_project.py",
            "tests/test_ipados_native_packaging.py",
            "tests/test_ipados_xcode_project_validator.py",
            "docs/rds/RDS_PACKAGING.md",
        ],
        config=_repository_config(),
    )

    assert result.unmatched_paths == ()
    assert result.requires_full_repository_gate is False
    assert "platform_ipados" in result.verification_requirements
    assert "platform" in result.verification_requirements
    assert "packaging" in result.verification_requirements
    assert "platform_macos" not in result.verification_requirements
    assert "platform_windows" not in result.verification_requirements
    assert "platform_android" not in result.verification_requirements


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("packaging/godot/build_macos.sh", "platform_macos"),
        ("packaging/godot/build_windows.sh", "platform_windows"),
        ("packaging/godot/build_android.sh", "platform_android"),
        ("packaging/godot/build_ipados.sh", "platform_ipados"),
    ],
)
def test_repository_platform_paths_select_only_their_own_platform(
    path: str, expected: str
) -> None:
    result = classify_paths([path], config=_repository_config())
    platform_requirements = {
        requirement
        for requirement in result.verification_requirements
        if requirement.startswith("platform_")
    }

    assert platform_requirements == {expected}
    assert "packaging" in result.verification_requirements


def test_shared_godot_pack_reader_selects_every_platform_that_uses_it() -> None:
    result = classify_paths(
        ["packaging/godot/godot_pack.py"], config=_repository_config()
    )
    platform_requirements = {
        requirement
        for requirement in result.verification_requirements
        if requirement.startswith("platform_")
    }

    assert platform_requirements == {"platform_android", "platform_ipados"}
