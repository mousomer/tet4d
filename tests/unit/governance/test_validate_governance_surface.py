from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.governance import validate_governance_surface as surface

OWNERS = {
    "engineering": "docs/governance/ENGINEERING.md",
    "verification": "docs/governance/VERIFICATION.md",
    "security_and_sanitation": "docs/governance/SECURITY_AND_SANITATION.md",
    "config_and_generated_data": "docs/governance/CONFIG_AND_GENERATED_DATA.md",
    "native_and_platform": "docs/governance/NATIVE_AND_PLATFORM.md",
    "change_governance": "docs/governance/CHANGE_GOVERNANCE.md",
}
HUMAN = [*sorted(surface.STATIC_HUMAN_PATHS), *OWNERS.values()]


def _write(path: Path, text: str = "current\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _policy() -> dict[str, object]:
    provenance = {
        family: OWNERS["change_governance"] for family in surface.PROVENANCE_FAMILIES
    }
    return {
        "authority_model": {
            "change_governance": OWNERS["change_governance"],
            "canonical_human_owners": dict(OWNERS),
        },
        "codex_routing": {
            "routes": {
                "governance_and_tooling": {
                    "authority_keys": ["change_governance"],
                    "dispatch_paths": ["AGENTS.md"],
                }
            }
        },
        "deprecated_authorities": {"blocked_paths": []},
        "governance_surface": {
            "document_roles": {
                "governance": HUMAN,
                "current_state": ["CURRENT_STATE.md"],
                "active_task": [],
                "planning": ["docs/plans"],
                "history": ["docs/history"],
                "architecture": [
                    "docs/ARCHITECTURE_CONTRACT.md",
                    "docs/architecture",
                ],
                "product_contract": ["docs/rds"],
                "template": ["tools/templates/governance"],
                "generated_reference": [
                    "docs/CONFIGURATION_REFERENCE.md",
                    "docs/USER_SETTINGS_REFERENCE.md",
                    "docs/PROJECT_STRUCTURE.md",
                ],
            },
            "active_governance": {
                "human": HUMAN,
                "machine": [surface.POLICY_REL],
                "operational": ["CURRENT_STATE.md", "docs/BACKLOG.md"],
                "active_task": [],
            },
            "aggregate_hard_limit": 2500,
            "active_task_limit": 250,
            "per_file_limits": {
                **surface.FIXED_LIMITS,
                **{path: 300 for path in OWNERS.values()},
            },
            "lifecycle": {
                "forbidden_active_heading_regex": [
                    r"^#{1,6}\s+(?:Previous|Prior)\s+(?:Task|Stage|Work|Completion(?:\s+Report)?)\s*$"
                ],
                "volatile_test_count_regex": (
                    r"(?i)(?:\bpytest(?:\s+result)?\s*:\s*\d[\d,]*\s+passed\b|"
                    r"\b\d[\d,]*\s+tests?\s+passed\b|"
                    r"\b(?:the\s+)?suite\s+has\s+\d[\d,]*\s+tests?\b)"
                ),
            },
            "validator_provenance": provenance,
        },
    }


def _fixture(root: Path) -> dict[str, object]:
    policy = _policy()
    for rel in HUMAN + [
        "CURRENT_STATE.md",
        "docs/BACKLOG.md",
        "docs/ARCHITECTURE_CONTRACT.md",
        "docs/CONFIGURATION_REFERENCE.md",
        "docs/USER_SETTINGS_REFERENCE.md",
        "docs/PROJECT_STRUCTURE.md",
        "docs/architecture/README.md",
        "docs/rds/README.md",
        "docs/plans/README.md",
        "docs/history/README.md",
        "tools/templates/governance/README.md",
    ]:
        _write(root / rel)
    _write(root / surface.POLICY_REL, json.dumps(policy, indent=2) + "\n")
    return policy


def _issues(root: Path) -> list[surface.SurfaceIssue]:
    issues, _measurement = surface.validate_surface(
        root, expected_provenance=surface.PROVENANCE_FAMILIES
    )
    return issues


def _messages(root: Path) -> list[str]:
    return [issue.message for issue in _issues(root)]


def test_actual_governance_surface_is_within_all_limits() -> None:
    issues, measurement = surface.validate_surface(
        surface.ROOT, expected_provenance=surface.PROVENANCE_FAMILIES
    )
    assert issues == []
    assert measurement is not None
    assert measurement.human <= 698 + 100
    assert measurement.machine <= 1000
    assert measurement.operational <= 400
    assert measurement.total <= 2500


def test_canonical_owner_file_ceiling_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write(tmp_path / OWNERS["engineering"], "line\n" * 301)
    assert any("ENGINEERING.md: 301 LOC" in message for message in _messages(tmp_path))


@pytest.mark.parametrize(
    ("rel", "lines", "expected"),
    [("CURRENT_STATE.md", 151, "150"), ("docs/BACKLOG.md", 251, "250")],
)
def test_operational_file_ceiling_fails(
    tmp_path: Path, rel: str, lines: int, expected: str
) -> None:
    _fixture(tmp_path)
    _write(tmp_path / rel, "line\n" * lines)
    assert any(f"hard limit {expected}" in message for message in _messages(tmp_path))


def test_policy_pack_ceiling_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    policy_path = tmp_path / surface.POLICY_REL
    policy_path.write_text(policy_path.read_text(encoding="utf-8") + "\n" * 1001)
    assert any(
        "policy_pack.json" in message and "1000" in message
        for message in _messages(tmp_path)
    )


def test_aggregate_ceiling_fails_while_guarded_files_pass(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write(tmp_path / "CLAUDE.md", "line\n" * 1300)
    _write(tmp_path / "CONTRIBUTING.md", "line\n" * 1300)
    assert any("active governance total" in message for message in _messages(tmp_path))
    assert not any(
        "CLAUDE.md:" in message or "CONTRIBUTING.md:" in message
        for message in _messages(tmp_path)
    )


def test_missing_duplicate_and_seventh_owner_fail(tmp_path: Path) -> None:
    policy = _fixture(tmp_path)
    owners = policy["authority_model"]["canonical_human_owners"]
    owners.pop("engineering")
    owners["seventh"] = OWNERS["verification"]
    _write(tmp_path / surface.POLICY_REL, json.dumps(policy, indent=2) + "\n")
    messages = _messages(tmp_path)
    assert any("exactly the six" in message for message in messages)
    assert any("paths must be unique" in message for message in messages)


def test_history_route_fails(tmp_path: Path) -> None:
    policy = _fixture(tmp_path)
    _write(tmp_path / "docs/history/routed.md")
    policy["authority_model"]["historical"] = "docs/history/routed.md"
    policy["codex_routing"]["routes"]["governance_and_tooling"]["authority_keys"] = [
        "historical"
    ]
    _write(tmp_path / surface.POLICY_REL, json.dumps(policy, indent=2) + "\n")
    assert any("enters history" in message for message in _messages(tmp_path))


def test_append_only_heading_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write(tmp_path / "CURRENT_STATE.md", "# Current\n## Previous Task\n")
    assert any(
        "append-only history heading" in message for message in _messages(tmp_path)
    )


def test_unowned_provenance_family_fails(tmp_path: Path) -> None:
    policy = _fixture(tmp_path)
    policy["governance_surface"]["validator_provenance"]["synthetic_unowned"] = OWNERS[
        "change_governance"
    ]
    _write(tmp_path / surface.POLICY_REL, json.dumps(policy, indent=2) + "\n")
    assert any(
        "unowned validator rule family" in message for message in _messages(tmp_path)
    )


def test_volatile_count_rejects_inventory_but_allows_immutable_reference_and_history(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _write(tmp_path / "docs/BACKLOG.md", "127 tests passed\n")
    assert any("volatile test inventory" in message for message in _messages(tmp_path))

    _write(tmp_path / "docs/BACKLOG.md", "PR #83 passed\n")
    _write(tmp_path / "docs/history/README.md", "pytest: 127 passed\n")
    assert _issues(tmp_path) == []


def test_template_or_retired_authority_cannot_be_active(tmp_path: Path) -> None:
    policy = _fixture(tmp_path)
    policy["governance_surface"]["active_governance"]["active_task"] = [
        "tools/templates/governance/README.md"
    ]
    policy["deprecated_authorities"]["blocked_paths"] = ["AGENTS.md"]
    _write(tmp_path / surface.POLICY_REL, json.dumps(policy, indent=2) + "\n")
    messages = _messages(tmp_path)
    assert any(
        "excluded role entered active governance" in message for message in messages
    )
    assert any("retired authority is active" in message for message in messages)
