"""Pure reconstruction tests use a committed-source fixture, never mutable Git state."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.governance import export_governance_inventory as inventory


@pytest.fixture
def fixture_ledger(monkeypatch: pytest.MonkeyPatch) -> dict:
    files = {
        inventory.PROJECT: json.dumps({"authorities": [], "routes": {}}).encode(),
        inventory.POLICY: json.dumps(
            {
                "authority_model": {
                    "canonical_human_owners": {"engineering": "policy.md"}
                },
                "governance_surface": {"validator_provenance": {"sample": "policy.md"}},
            }
        ).encode(),
        inventory.PYTHON_RUNNER: b'def _checks():\n    return (GovernanceCheck("sample", checker.main),)\n',
        inventory.SHELL_RUNNER: b"# No shell-owned families in this fixture.\n",
        "policy.md": b"Keep a single source owner.\n",
    }
    requested_commits: set[str] = set()

    def committed_bytes(commit: str, path: str) -> bytes:
        requested_commits.add(commit)
        assert requested_commits == {"a" * 40}
        return files[inventory._relative(path)]

    monkeypatch.setattr(inventory, "_git_bytes", committed_bytes)
    return {
        "schema_version": 1,
        "provenance": {"baseline_commit": "a" * 40},
        "obligation_columns": inventory.COLUMNS,
        "source_catalog": {"policy": {"path": "policy.md"}},
        "dispositions": {"human_review": "Meaning requires review."},
        "obligations": [
            [
                "one-owner",
                "Keep a single source owner.",
                "policy:1-1",
                "human_review",
                [],
            ]
        ],
        "family_coverage": {"sample": "The checker has a bounded proof boundary."},
        "mechanisms": {},
        "baseline_decisions": [],
    }


def test_rebuild_is_deterministic_and_binds_sources_and_runner(
    fixture_ledger: dict,
) -> None:
    first = inventory.rebuild(copy.deepcopy(fixture_ledger))
    second = inventory.rebuild(copy.deepcopy(fixture_ledger))
    assert first == second
    assert first["provenance"]["baseline_commit"] == "a" * 40
    generated = first["generated"]
    assert generated["source_sha256"]["policy.md"] == inventory._sha(
        b"Keep a single source owner.\n"
    )
    assert generated["anchor_sha256"]["policy:1-1"]["lines"] == [1, 1]
    assert generated["enforcement_families"]["sample"]["owner_source"] == "policy.md"
    assert generated["counts"]["provisional_repository_entries"] == 1
    assert json.loads(inventory.render(first)) == first


@pytest.mark.parametrize(
    "mutation,message",
    [
        ("mutable_baseline", "immutable Git commit"),
        ("session_rule", "non-portable"),
        ("duplicate_rule", "duplicate"),
        ("unknown_mechanism", "unknown mechanism"),
        ("out_of_range_anchor", "invalid source span"),
        ("missing_coverage", "coverage notes"),
        ("changed_columns", "obligation columns"),
    ],
)
def test_rejects_unsupported_provenance_and_coverage(
    fixture_ledger: dict, mutation: str, message: str
) -> None:
    data = copy.deepcopy(fixture_ledger)
    if mutation == "mutable_baseline":
        data["provenance"]["baseline_commit"] = "HEAD"
    elif mutation == "session_rule":
        data["obligations"][0][0] = "session-global-doctrine"
    elif mutation == "duplicate_rule":
        data["obligations"].append(copy.deepcopy(data["obligations"][0]))
    elif mutation == "unknown_mechanism":
        data["obligations"][0][4] = ["imagined-check"]
    elif mutation == "out_of_range_anchor":
        data["obligations"][0][2] = "policy:1-2"
    elif mutation == "missing_coverage":
        data["family_coverage"] = {}
    elif mutation == "changed_columns":
        data["obligation_columns"] = ["different-schema"]
    with pytest.raises(ValueError, match=message):
        inventory.rebuild(data)


def test_check_fails_when_recorded_hash_was_tampered(
    fixture_ledger: dict, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "ledger.json"
    expected = inventory.rebuild(copy.deepcopy(fixture_ledger))
    path.write_text(inventory.render(expected))
    assert inventory.main(["--check", "--ledger", str(path)]) == 0
    expected["generated"]["source_sha256"]["policy.md"] = "0" * 64
    path.write_text(inventory.render(expected))
    assert inventory.main(["--check", "--ledger", str(path)]) == 1
    assert "stale metadata" in capsys.readouterr().err
