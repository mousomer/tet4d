from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.governance.select_codex_ci_lanes import (
    LaneSelectionError,
    github_outputs,
    load_lane_config,
    select_lanes,
    write_github_outputs,
)


def _config_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "resolution_schema_version": 1,
        "lane_order": [
            "baseline",
            "documentation_governance",
            "python",
            "godot",
            "native",
            "deterministic_parity",
            "integration",
            "packaging",
            "platform_macos",
            "platform_ipados",
            "release_acceptance",
        ],
        "always_run_lanes": ["baseline"],
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
        "full_repository_gate_lanes": [
            "baseline",
            "documentation_governance",
            "python",
            "godot",
            "native",
            "deterministic_parity",
            "integration",
            "packaging",
            "platform_macos",
            "platform_ipados",
            "release_acceptance",
        ],
    }


def _resolution(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "repository_changed": True,
        "verification_requirements": ["native", "deterministic"],
        "requires_full_repository_gate": False,
    }
    payload.update(overrides)
    return payload


def test_requirements_map_to_ordered_deduplicated_lanes() -> None:
    selection = select_lanes(
        _resolution(
            verification_requirements=[
                "native",
                "deterministic",
                "parity_or_conformance",
                "integration",
                "godot",
            ]
        ),
        config=load_lane_config(_config_payload()),
    )

    assert selection.selected_lanes == (
        "baseline",
        "godot",
        "native",
        "deterministic_parity",
        "integration",
    )
    assert selection.manual_requirements == ()


def test_full_repository_gate_selects_every_lane() -> None:
    config = load_lane_config(_config_payload())
    selection = select_lanes(
        _resolution(requires_full_repository_gate=True),
        config=config,
    )

    assert selection.selected_lanes == config.lane_order


def test_review_only_resolution_selects_no_lanes() -> None:
    selection = select_lanes(
        _resolution(
            repository_changed=False,
            verification_requirements=[],
            requires_full_repository_gate=False,
        ),
        config=load_lane_config(_config_payload()),
    )

    assert selection.selected_lanes == ()
    assert selection.manual_requirements == ()


def test_manual_requirement_is_reported_without_automated_lane() -> None:
    selection = select_lanes(
        _resolution(verification_requirements=["godot", "human_visual"]),
        config=load_lane_config(_config_payload()),
    )

    assert selection.selected_lanes == ("baseline", "godot")
    assert selection.manual_requirements == ("human_visual",)


def test_unknown_requirement_is_rejected() -> None:
    with pytest.raises(LaneSelectionError, match="not mapped"):
        select_lanes(
            _resolution(verification_requirements=["unknown"]),
            config=load_lane_config(_config_payload()),
        )


def test_invalid_lane_reference_is_rejected() -> None:
    payload = copy.deepcopy(_config_payload())
    mapping = payload["requirement_to_lanes"]
    assert isinstance(mapping, dict)
    mapping["python"] = ["unknown"]

    with pytest.raises(LaneSelectionError, match="unknown lanes"):
        load_lane_config(payload)


def test_automated_requirement_needs_a_lane() -> None:
    payload = copy.deepcopy(_config_payload())
    mapping = payload["requirement_to_lanes"]
    assert isinstance(mapping, dict)
    mapping["python"] = []

    with pytest.raises(LaneSelectionError, match="at least one lane"):
        load_lane_config(payload)


def test_manual_requirement_cannot_map_to_automated_lane() -> None:
    payload = copy.deepcopy(_config_payload())
    mapping = payload["requirement_to_lanes"]
    assert isinstance(mapping, dict)
    mapping["human_visual"] = ["godot"]

    with pytest.raises(LaneSelectionError, match="must not map"):
        load_lane_config(payload)


def test_resolution_schema_mismatch_is_rejected() -> None:
    with pytest.raises(LaneSelectionError, match="schema version"):
        select_lanes(
            _resolution(schema_version=2),
            config=load_lane_config(_config_payload()),
        )


def test_repository_change_requires_verification_requirements() -> None:
    with pytest.raises(LaneSelectionError, match="must select"):
        select_lanes(
            _resolution(verification_requirements=[]),
            config=load_lane_config(_config_payload()),
        )


def test_unchanged_repository_rejects_full_gate() -> None:
    with pytest.raises(LaneSelectionError, match="must not require"):
        select_lanes(
            _resolution(
                repository_changed=False,
                verification_requirements=[],
                requires_full_repository_gate=True,
            ),
            config=load_lane_config(_config_payload()),
        )


def test_full_gate_configuration_must_cover_every_lane() -> None:
    payload = copy.deepcopy(_config_payload())
    payload["full_repository_gate_lanes"] = ["baseline", "python"]

    with pytest.raises(LaneSelectionError, match="every configured lane"):
        load_lane_config(payload)


def test_github_outputs_include_boolean_for_every_lane() -> None:
    config = load_lane_config(_config_payload())
    selection = select_lanes(
        _resolution(verification_requirements=["godot", "human_visual"]),
        config=config,
    )

    outputs = github_outputs(selection, config=config)

    assert outputs["lane_baseline"] == "true"
    assert outputs["lane_godot"] == "true"
    assert outputs["lane_python"] == "false"
    assert outputs["selected_lanes"] == '["baseline","godot"]'
    assert outputs["manual_requirements"] == '["human_visual"]'
    assert outputs["requires_full_repository_gate"] == "false"


def test_github_outputs_are_appended_in_stable_order(tmp_path: Path) -> None:
    config = load_lane_config(_config_payload())
    selection = select_lanes(_resolution(), config=config)
    output_path = tmp_path / "github_output.txt"
    output_path.write_text("existing=value\n", encoding="utf-8")

    write_github_outputs(output_path, selection, config=config)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "existing=value"
    assert lines[1] == "lane_baseline=true"
    assert "lane_native=true" in lines
    assert "lane_deterministic_parity=true" in lines
    assert lines[-1] == "requires_full_repository_gate=false"


def test_abstract_requirement_must_not_map_to_a_lane_of_its_own() -> None:
    payload = copy.deepcopy(_config_payload())
    mapping = payload["requirement_to_lanes"]
    assert isinstance(mapping, dict)
    mapping["platform"] = ["platform_macos"]

    with pytest.raises(LaneSelectionError, match="must not map to a lane of its own"):
        load_lane_config(payload)


def test_requirement_cannot_be_both_abstract_and_manual() -> None:
    payload = copy.deepcopy(_config_payload())
    manual = payload["manual_requirements"]
    assert isinstance(manual, list)
    manual.append("platform")

    with pytest.raises(LaneSelectionError, match="both abstract and manual"):
        load_lane_config(payload)


def test_abstract_requirement_alone_cannot_select_a_platform_lane() -> None:
    with pytest.raises(LaneSelectionError, match="explicit expansion"):
        select_lanes(
            _resolution(verification_requirements=["packaging", "platform"]),
            config=load_lane_config(_config_payload()),
        )


def test_explicit_platform_requirement_selects_only_its_own_lane() -> None:
    selection = select_lanes(
        _resolution(
            verification_requirements=["packaging", "platform", "platform_ipados"]
        ),
        config=load_lane_config(_config_payload()),
    )

    assert selection.selected_lanes == ("baseline", "packaging", "platform_ipados")
    assert selection.platform_requirements == ("platform_ipados",)
    assert "platform_macos" not in selection.selected_lanes


def test_unhosted_platform_requirement_is_reported_not_substituted() -> None:
    selection = select_lanes(
        _resolution(
            verification_requirements=["packaging", "platform", "platform_windows"]
        ),
        config=load_lane_config(_config_payload()),
    )

    assert selection.selected_lanes == ("baseline", "packaging")
    assert selection.manual_requirements == ("platform_windows",)
    assert selection.platform_requirements == ("platform_windows",)


def test_github_outputs_name_the_selected_platform_requirements() -> None:
    config = load_lane_config(_config_payload())
    selection = select_lanes(
        _resolution(
            verification_requirements=["packaging", "platform", "platform_ipados"]
        ),
        config=config,
    )

    outputs = github_outputs(selection, config=config)

    assert outputs["lane_platform_ipados"] == "true"
    assert outputs["lane_platform_macos"] == "false"
    assert outputs["platform_requirements"] == '["platform_ipados"]'
