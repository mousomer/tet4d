from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

from tools.governance import validate_product_platform_matrix as matrix
from tools.release.release_metadata import ARTIFACT_SPECS

ROOT = Path(__file__).resolve().parents[3]


def _inputs() -> tuple[dict[str, object], str, str, str, str, str]:
    return (
        json.loads((ROOT / "config/project/policy_pack.json").read_text()),
        (ROOT / ".github/workflows/release-packaging.yml").read_text(),
        (ROOT / "godot/Tet4D.Godot/export_presets.cfg").read_text(),
        (ROOT / "docs/governance/CHANGE_GOVERNANCE.md").read_text(),
        (ROOT / "docs/rds/RDS_PACKAGING.md").read_text(),
        (ROOT / "docs/BACKLOG.md").read_text(),
    )


def _validate(
    inputs: tuple[dict[str, object], str, str, str, str, str]
) -> list[str]:
    return matrix.validate_contract(*inputs)


def test_authoritative_contract_has_exact_three_product_matrix() -> None:
    policy = _inputs()[0]
    contract = policy["product_platform_contract"]
    assert isinstance(contract, dict)
    products = contract["products"]
    assert isinstance(products, dict)
    assert tuple(products) == ("python_tet4d", "godot_game", "godot_designer")
    assert contract["target_platforms"] == {
        "python_tet4d": ["macos", "windows", "linux"],
        "godot_game": ["macos", "windows", "linux", "android", "ipados"],
        "godot_designer": ["macos", "windows"],
    }


def test_current_consumers_pass_without_claiming_missing_targets_implemented() -> None:
    assert _validate(_inputs()) == []


def test_unimplemented_godot_game_linux_and_ipados_are_explicit_backlog_gaps() -> None:
    policy, *_unused, backlog = _inputs()
    consumers = policy["product_platform_contract"]["packaging_consumers"]
    implemented = {
        (item["product_id"], item["platform_id"])
        for item in consumers
        if item["status"] == "implemented"
    }

    assert ("godot_game", "linux") not in implemented
    assert ("godot_game", "ipados") not in implemented
    assert "Godot game / Linux" in backlog
    assert "Godot game / iPadOS" in backlog
    assert _validate(_inputs()) == []


def test_adding_android_to_designer_fails_rds_consistency_probe() -> None:
    inputs = list(_inputs())
    policy = copy.deepcopy(inputs[0])
    policy["product_platform_contract"]["target_platforms"]["godot_designer"].append(
        "android"
    )
    inputs[0] = policy

    issues = _validate(tuple(inputs))

    assert any("RDS matrix for godot_designer" in issue for issue in issues)


def test_removing_ipados_from_game_fails_rds_consistency_probe() -> None:
    inputs = list(_inputs())
    policy = copy.deepcopy(inputs[0])
    policy["product_platform_contract"]["target_platforms"]["godot_game"].remove(
        "ipados"
    )
    inputs[0] = policy

    issues = _validate(tuple(inputs))

    assert any("RDS matrix for godot_game" in issue for issue in issues)


def test_game_macos_cannot_be_mislabelled_designer_with_game_identity() -> None:
    inputs = list(_inputs())
    policy = copy.deepcopy(inputs[0])
    consumers = policy["product_platform_contract"]["packaging_consumers"]
    macos = next(item for item in consumers if item["consumer_id"] == "godot_game_macos")
    macos["product_id"] = "godot_designer"
    inputs[0] = policy

    issues = _validate(tuple(inputs))

    assert any("does not match godot_designer identity" in issue for issue in issues)


def test_designer_linux_release_configuration_is_forbidden() -> None:
    inputs = list(_inputs())
    policy = copy.deepcopy(inputs[0])
    policy["product_platform_contract"]["packaging_consumers"].append(
        {
            "consumer_id": "forbidden_designer_linux",
            "product_id": "godot_designer",
            "platform_id": "linux",
            "status": "implemented",
            "workflow_job": "package-forbidden-designer-linux",
        }
    )
    inputs[0] = policy
    inputs[1] += chr(10).join(
        ("", "  package-forbidden-designer-linux:", "    name: package Designer Linux", "")
    )

    issues = _validate(tuple(inputs))

    assert "forbidden implemented pairing: godot_designer / linux" in issues


def test_python_tablet_release_configurations_are_forbidden() -> None:
    for platform_id in ("android", "ipados"):
        inputs = list(_inputs())
        policy = copy.deepcopy(inputs[0])
        job_id = f"package-forbidden-python-{platform_id}"
        policy["product_platform_contract"]["packaging_consumers"].append(
            {
                "consumer_id": f"forbidden_python_{platform_id}",
                "product_id": "python_tet4d",
                "platform_id": platform_id,
                "status": "implemented",
                "workflow_job": job_id,
            }
        )
        inputs[0] = policy
        inputs[1] += f"\n  {job_id}:\n    name: package Python Tet4D {platform_id}\n"

        issues = _validate(tuple(inputs))

        assert f"forbidden implemented pairing: python_tet4d / {platform_id}" in issues


def test_transitional_designer_tablet_artifacts_cannot_claim_implementation() -> None:
    for consumer_id, platform_id in (
        ("legacy_designer_android", "android"),
        ("legacy_designer_ipados", "ipados"),
    ):
        inputs = list(_inputs())
        policy = copy.deepcopy(inputs[0])
        consumers = policy["product_platform_contract"]["packaging_consumers"]
        consumer = next(
            item for item in consumers if item["consumer_id"] == consumer_id
        )
        consumer["status"] = "implemented"
        inputs[0] = policy

        issues = _validate(tuple(inputs))

        assert (
            f"forbidden implemented pairing: godot_designer / {platform_id}" in issues
        )


def test_new_designer_linux_transitional_consumer_is_forbidden() -> None:
    inputs = list(_inputs())
    policy = copy.deepcopy(inputs[0])
    policy["product_platform_contract"]["packaging_consumers"].append(
        {
            "consumer_id": "invented_designer_linux",
            "product_id": "godot_designer",
            "platform_id": "linux",
            "status": "transitional_mismatch",
            "workflow_job": "package-invented-designer-linux",
        }
    )
    inputs[0] = policy
    inputs[1] += chr(10).join(
        ("", "  package-invented-designer-linux:", "    name: transitional not a target", "")
    )

    issues = _validate(tuple(inputs))

    assert "transitional mismatch is not a grandfathered consumer: invented_designer_linux" in issues


def test_new_designer_android_transitional_consumer_is_forbidden() -> None:
    inputs = list(_inputs())
    policy = copy.deepcopy(inputs[0])
    policy["product_platform_contract"]["packaging_consumers"].append(
        {
            "consumer_id": "invented_designer_android",
            "product_id": "godot_designer",
            "platform_id": "android",
            "status": "transitional_mismatch",
            "workflow_job": "package-invented-designer-android",
        }
    )
    inputs[0] = policy
    inputs[1] += chr(10).join(
        ("", "  package-invented-designer-android:", "    name: transitional not a target", "")
    )

    issues = _validate(tuple(inputs))

    assert "transitional mismatch is not a grandfathered consumer: invented_designer_android" in issues


def test_macos_game_release_artifact_cannot_be_reclassified_as_designer() -> None:
    altered_specs = tuple(
        replace(spec, product_id="godot_designer")
        if spec.consumer_id == "godot_game_macos"
        else spec
        for spec in ARTIFACT_SPECS
    )

    issues = matrix.validate_contract(*_inputs(), artifact_specs=altered_specs)

    assert any(
        "release artifact godot_game_macos product/platform does not match" in issue
        for issue in issues
    )


def test_rds_parser_ignores_unrelated_three_column_table() -> None:
    inputs = list(_inputs())
    inputs[4] += (
        "\n## Appendix\n\n| Product ID | Product | Required targets |\n"
        "| --- | --- | --- |\n"
        "| `godot_game` | unrelated fixture | Linux |\n"
    )

    assert _validate(tuple(inputs)) == []


def test_python_backlog_label_is_not_reported_as_designer() -> None:
    issues: list[str] = []
    matrix._validate_backlog(
        {"python_tet4d": {"macos"}},
        set(),
        _inputs()[0]["product_platform_contract"]["products"],
        "",
        issues,
    )

    assert issues == [
        "required unimplemented target is absent from backlog: Python Tet4D / macOS"
    ]


def test_matrix_governance_registration_cannot_disappear() -> None:
    inputs = list(_inputs())
    inputs[3] = inputs[3].replace("controlled product-plan\ncontract", "ordinary data")

    issues = _validate(tuple(inputs))

    assert any("controlled product-plan contract" in issue for issue in issues)
