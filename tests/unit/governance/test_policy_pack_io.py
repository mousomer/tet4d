from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.governance import policy_pack_io
from tools.governance import update_tech_debt_budgets as update_budgets


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "governance": {
            "tech_debt_budget": {
                "baseline": {"arch_stage": 1, "score": 2.0, "status": "low"}
            }
        },
    }


def test_current_policy_pack_is_canonical() -> None:
    assert policy_pack_io.check_canonical_policy_pack() == []


def test_collapsed_valid_policy_is_not_canonical(tmp_path: Path) -> None:
    path = tmp_path / "policy_pack.json"
    path.write_text(json.dumps(_payload()) + "\n", encoding="utf-8")
    assert policy_pack_io.check_canonical_policy_pack(path)


def test_generic_pretty_policy_is_not_canonical(tmp_path: Path) -> None:
    path = tmp_path / "policy_pack.json"
    path.write_text(json.dumps(_payload(), indent=2) + "\n", encoding="utf-8")
    assert policy_pack_io.check_canonical_policy_pack(path)


def test_duplicate_policy_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "policy_pack.json"
    path.write_text(
        '{"governance_surface":{"validator_provenance":'
        '{"contracts":"owner-a","contracts":"owner-b"}}}\n',
        encoding="utf-8",
    )
    issues = policy_pack_io.check_canonical_policy_pack(path)
    assert any("duplicate JSON key: contracts" in issue for issue in issues)


def test_tech_debt_writer_preserves_canonical_format(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "config/project/policy_pack.json"
    path.parent.mkdir(parents=True)
    policy_pack_io.write_policy_pack(_payload(), path)
    metrics = {"arch_stage": 2, "tech_debt": {"score": 1.5, "status": "low"}}
    completed = subprocess.CompletedProcess(
        args=["arch_metrics"], returncode=0, stdout=json.dumps(metrics), stderr=""
    )
    monkeypatch.setattr(update_budgets, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        update_budgets.subprocess, "run", lambda *args, **kwargs: completed
    )

    assert update_budgets.main() == 0
    assert policy_pack_io.check_canonical_policy_pack(path) == []
    updated = policy_pack_io.load_policy_pack(path)
    assert updated["governance"]["tech_debt_budget"]["baseline"] == {
        "arch_stage": 2,
        "score": 1.5,
        "status": "low",
    }
