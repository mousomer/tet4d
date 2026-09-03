"""Semantic gates binding platform verification identity to executable CI jobs.

These tests read the real machine configuration, the real CI workflow, and the
real product/platform contract. They exist because a lane name alone proves
nothing: a `platform` requirement is only meaningful when the selected job
actually exercises that platform's governed build path.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from tools.governance.classify_codex_ci_paths import (
    classify_paths,
    load_path_classification_config,
)
from tools.governance.select_codex_ci_lanes import (
    LaneSelectionError,
    load_lane_config,
    select_lanes,
)

ROOT = Path(__file__).resolve().parents[3]
LANE_CONFIG_PATH = ROOT / "config/project/codex_ci_lanes.json"
POLICY_PATH = ROOT / "config/project/policy_pack.json"
CI_WORKFLOW_PATH = ROOT / ".github/workflows/ci.yml"
RELEASE_WORKFLOW_PATH = ROOT / ".github/workflows/release-packaging.yml"

IPADOS_PACKAGING_DIFF = (
    "packaging/godot/build_ipados.sh",
    "packaging/godot/ipados_native.py",
    "packaging/godot/validate_ipados_project.py",
    "tests/test_ipados_native_packaging.py",
    "tests/test_ipados_xcode_project_validator.py",
    "docs/rds/RDS_PACKAGING.md",
)
PLATFORM_LABELS = {
    "macos": "macos",
    "windows": "windows",
    "linux": "linux",
    "android": "android",
    "ipados": "ipados",
}


def _lane_payload() -> dict[str, object]:
    return json.loads(LANE_CONFIG_PATH.read_text(encoding="utf-8"))


def _policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _workflow_jobs(path: Path) -> dict[str, str]:
    """Split a workflow into job identifier -> job text, without a YAML parser."""
    text = path.read_text(encoding="utf-8")
    jobs: dict[str, list[str]] = {}
    current = ""
    in_jobs = False
    for line in text.splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        match = re.fullmatch(r"  ([a-z0-9-]+):", line)
        if match:
            current = match.group(1)
            jobs[current] = []
            continue
        if current:
            jobs[current].append(line)
    return {job: "\n".join(lines) for job, lines in jobs.items()}


def _platform_evidence() -> dict[str, object]:
    block = _lane_payload()["platform_evidence"]
    assert isinstance(block, dict)
    return block


def _hosted_lanes() -> dict[str, dict[str, str]]:
    hosted = _platform_evidence()["hosted_lanes"]
    assert isinstance(hosted, dict)
    return hosted


def _resolve(changed_paths: tuple[str, ...]):
    payload = _lane_payload()
    classification = classify_paths(
        list(changed_paths),
        config=load_path_classification_config(payload),
    )
    return classification, select_lanes(
        classification.to_dict(), config=load_lane_config(payload)
    )


def _tracked(prefix: str) -> tuple[str, ...]:
    output = subprocess.run(
        ["git", "ls-files", prefix],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return tuple(line for line in output.splitlines() if line.strip())


# --- Platform identity is derived, never a second matrix ------------------


def test_platform_requirement_ids_cover_exactly_the_contract_platforms() -> None:
    contract = _policy()["product_platform_contract"]
    assert isinstance(contract, dict)
    ids = _platform_evidence()["platform_requirement_ids"]
    assert isinstance(ids, dict)

    assert sorted(ids) == sorted(contract["platform_ids"])
    for platform_id, requirement in ids.items():
        assert requirement == f"platform_{platform_id}"


def test_abstract_platform_requirement_expands_to_every_platform_id() -> None:
    payload = _lane_payload()
    evidence = _platform_evidence()
    abstract = payload["abstract_requirements"]
    assert isinstance(abstract, dict)
    ids = evidence["platform_requirement_ids"]
    assert isinstance(ids, dict)

    assert evidence["abstract_requirement"] == "platform"
    assert sorted(abstract["platform"]) == sorted(ids.values())


def test_unhosted_platform_requirements_are_declared_manual() -> None:
    payload = _lane_payload()
    evidence = _platform_evidence()
    ids = evidence["platform_requirement_ids"]
    assert isinstance(ids, dict)
    hosted = set(_hosted_lanes())
    manual = payload["manual_requirements"]
    assert isinstance(manual, list)

    unhosted = evidence["unhosted_platform_requirements"]
    assert isinstance(unhosted, list)
    assert sorted(unhosted) == sorted(set(ids.values()) - hosted)
    # A platform CI cannot run is reported as unprovided evidence, never
    # silently satisfied by a different platform's package job.
    assert set(unhosted).issubset(manual)


# --- Semantic gate A: a lane maps to executable platform evidence ---------


def test_hosted_platform_lanes_bind_to_real_gated_workflow_jobs() -> None:
    payload = _lane_payload()
    lane_order = payload["lane_order"]
    assert isinstance(lane_order, list)
    mapping = payload["requirement_to_lanes"]
    assert isinstance(mapping, dict)
    jobs = _workflow_jobs(CI_WORKFLOW_PATH)

    for requirement, binding in _hosted_lanes().items():
        lane = binding["lane"]
        assert lane in lane_order
        assert mapping[requirement] == [lane]
        job_text = jobs[binding["workflow_job"]]
        assert f"needs.plan.outputs.lane_{lane} == 'true'" in job_text
        assert binding["build_entrypoint"] in job_text


def test_hosted_platform_lanes_run_their_canonical_governed_command() -> None:
    commands = _policy()["governance"]["godot_toolchain"]["canonical_commands"]

    for binding in _hosted_lanes().values():
        command = commands[binding["canonical_command"]]
        assert binding["build_entrypoint"] in command


def test_hosted_platform_lanes_name_a_registered_packaging_consumer() -> None:
    contract = _policy()["product_platform_contract"]
    assert isinstance(contract, dict)
    consumers = {
        consumer["consumer_id"]: consumer
        for consumer in contract["packaging_consumers"]
    }

    for binding in _hosted_lanes().values():
        consumer = consumers[binding["packaging_consumer"]]
        assert consumer["platform_id"] == binding["platform_id"]


def test_ipados_lane_executes_the_release_export_and_final_link() -> None:
    _classification, selection = _resolve(IPADOS_PACKAGING_DIFF)
    binding = _hosted_lanes()["platform_ipados"]
    job_text = _workflow_jobs(CI_WORKFLOW_PATH)[binding["workflow_job"]]
    build_script = (ROOT / binding["build_entrypoint"]).read_text(encoding="utf-8")

    assert binding["lane"] in selection.selected_lanes
    # Release mode is the mode that produces final-link evidence; the
    # configuration-only mode would not compile the exported project.
    assert "build_ipados.sh" in job_text
    assert "--configuration-only" not in job_text
    assert "--export-release" in build_script
    assert "xcodebuild -create-xcframework" in build_script
    assert "-sdk iphonesimulator" in build_script
    assert "CODE_SIGNING_ALLOWED=NO" in build_script
    assert "validate_ipados_project.py" in build_script


# --- Semantic gate B: no cross-platform substitution ----------------------


def test_macos_package_job_cannot_provide_ipados_evidence() -> None:
    jobs = _workflow_jobs(CI_WORKFLOW_PATH)
    hosted = _hosted_lanes()
    macos_job = jobs[hosted["platform_macos"]["workflow_job"]]
    ipados_job = jobs[hosted["platform_ipados"]["workflow_job"]]

    assert "build_ipados.sh" not in macos_job
    assert "build_macos.sh" not in ipados_job
    # Both run on macOS hosts; a shared runner is not shared evidence.
    assert "runs-on: macos-latest" in macos_job
    assert "runs-on: macos-latest" in ipados_job


def test_substituting_the_macos_lane_does_not_satisfy_ipados_evidence() -> None:
    payload = _lane_payload()
    mapping = payload["requirement_to_lanes"]
    assert isinstance(mapping, dict)
    macos_lane = _hosted_lanes()["platform_macos"]["lane"]
    ipados_lane = _hosted_lanes()["platform_ipados"]["lane"]

    assert macos_lane not in mapping["platform_ipados"]
    assert ipados_lane not in mapping["platform_macos"]

    _classification, selection = _resolve(IPADOS_PACKAGING_DIFF)
    assert "platform_ipados" in selection.verification_requirements
    assert "platform_macos" not in selection.verification_requirements
    assert macos_lane not in selection.selected_lanes


def test_abstract_platform_requirement_alone_is_rejected() -> None:
    config = load_lane_config(_lane_payload())

    with pytest.raises(LaneSelectionError, match="explicit expansion"):
        select_lanes(
            {
                "schema_version": 1,
                "repository_changed": True,
                "verification_requirements": ["packaging", "platform"],
                "requires_full_repository_gate": False,
            },
            config=config,
        )


# --- Semantic gate C/D: product truth is untouched by CI routing ----------


def test_target_platform_matrix_is_unchanged_by_ci_routing() -> None:
    contract = _policy()["product_platform_contract"]
    assert isinstance(contract, dict)

    assert contract["target_platforms"] == {
        "python_tet4d": ["macos", "windows", "linux"],
        "godot_game": ["macos", "windows", "linux", "android", "ipados"],
        "godot_designer": ["macos", "windows"],
    }


def test_legacy_designer_ipados_remains_transitional() -> None:
    contract = _policy()["product_platform_contract"]
    assert isinstance(contract, dict)
    consumer = next(
        item
        for item in contract["packaging_consumers"]
        if item["consumer_id"] == "legacy_designer_ipados"
    )
    release_jobs = _workflow_jobs(RELEASE_WORKFLOW_PATH)
    ipados_ci_job = _workflow_jobs(CI_WORKFLOW_PATH)[
        _hosted_lanes()["platform_ipados"]["workflow_job"]
    ]

    assert consumer["status"] == "transitional_mismatch"
    assert consumer["product_id"] == "godot_designer"
    assert consumer["workflow_job"] in release_jobs
    # The hosted CI lane names the transitional Designer artifact it builds and
    # never claims the godot_game/ipados target or physical-device acceptance.
    assert "transitional" in ipados_ci_job.casefold()
    assert "not physical-device acceptance" in ipados_ci_job


# --- Semantic gate E: the conservative fallback is untouched --------------


def test_unknown_path_still_forces_the_full_repository_gate() -> None:
    classification, selection = _resolve(("assets/some_new_binary.dat",))

    assert classification.unmatched_paths == ("assets/some_new_binary.dat",)
    assert classification.requires_full_repository_gate is True
    assert selection.selected_lanes == tuple(
        load_lane_config(_lane_payload()).lane_order
    )


# --- Semantic gate F: outputs name the platform actually exercised --------


def test_plan_exposes_an_output_for_every_selectable_lane() -> None:
    payload = _lane_payload()
    lane_order = payload["lane_order"]
    assert isinstance(lane_order, list)
    always_run = payload["always_run_lanes"]
    assert isinstance(always_run, list)
    plan_job = _workflow_jobs(CI_WORKFLOW_PATH)["plan"]

    for lane in lane_order:
        if lane in always_run:
            continue
        assert f"lane_{lane}: " in plan_job
    assert "platform_requirements: " in plan_job


def test_no_ambiguous_platform_lane_survives() -> None:
    workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "lane_platform:" not in workflow
    assert "Current Godot platform package" not in workflow
    for binding in _hosted_lanes().values():
        job_text = _workflow_jobs(CI_WORKFLOW_PATH)[binding["workflow_job"]]
        label = PLATFORM_LABELS[binding["platform_id"]]
        name = next(
            line for line in job_text.splitlines() if line.startswith("    name: ")
        )
        assert label in name.casefold()


# --- Routing coverage: no Godot platform file escapes platform evidence ---


def test_every_godot_packaging_path_selects_explicit_platform_evidence() -> None:
    config = load_path_classification_config(_lane_payload())
    platform_ids = _platform_evidence()["platform_requirement_ids"]
    assert isinstance(platform_ids, dict)
    known = set(platform_ids.values())

    for path in _tracked("packaging/godot"):
        result = classify_paths([path], config=config)
        selected = known.intersection(result.verification_requirements)
        assert selected, f"{path} selects no explicit platform evidence"
