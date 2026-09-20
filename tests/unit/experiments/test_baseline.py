from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from tools.experiments.governance_manifest_quality.baseline import (
    ROOT,
    load_frozen_baseline,
    measure_fingerprint,
    require_frozen_baseline,
    validate_fingerprint,
)
from tools.experiments.governance_manifest_quality.cli import main

BASELINE_COMMIT = "7ca7f2e0697068ac0113c12d2d0a0a9d9ac14875"
MACHINE_POLICY_SHA = "44c126b6a80e9b37a9b2300badcaae1dfb124cc9cf605a247f508a68c4b798a3"
WORKSPACE_GOVERNANCE_SHA = (
    "6a3ca68304589a367b0eacfb593336ceef13c80221c1ff4bd7e9775432c3ccae"
)


def _fingerprint() -> dict:
    return measure_fingerprint(ROOT, baseline_commit=BASELINE_COMMIT)


def _mismatch_names(fingerprint: dict) -> set[str]:
    return {
        mismatch.split(": measured", 1)[0]
        for mismatch in validate_fingerprint(fingerprint, load_frozen_baseline())
    }


def test_fingerprint_independently_measures_all_three_identity_domains() -> None:
    fingerprint = _fingerprint()
    repository = fingerprint["repository"]
    workspace = fingerprint["workspace_governance"]
    policy = fingerprint["machine_policy"]

    assert repository["baseline_commit"] == BASELINE_COMMIT
    assert repository["checkout_commit"]
    assert repository["baseline_commit_exists"] is True
    assert repository["baseline_is_ancestor_of_checkout"] is True
    assert repository["frozen_treatment_paths_match_baseline"] is True
    assert workspace["revision"] == "v0.1-integrity-8"
    assert workspace["pack_name"] == "workspace-governance"
    assert workspace["pack_path"] == "tools/workspace_governance"
    assert workspace["lock_algorithm"] == "sha256-path-and-content-v1"
    assert workspace["content_sha256"] == WORKSPACE_GOVERNANCE_SHA
    assert workspace["locked_content_sha256"] == WORKSPACE_GOVERNANCE_SHA
    assert workspace["locked_files_match_computed"] is True
    assert policy["path"] == "config/project/policy_pack.json"
    assert policy["raw_sha256"] == MACHINE_POLICY_SHA
    assert policy["serialized_bytes"] == 74150
    assert policy["node_count"] > 0
    assert policy["leaf_count"] > 0
    assert policy["maximum_nesting_depth"] > 0
    assert policy["largest_top_level_section"]["bytes"] > 0
    assert (
        "config/project/policy_pack.json"
        in fingerprint["active_governance_files"]["machine"]
    )
    assert fingerprint["schema_identity"]["project_manifest_schema_version"] == 1


def test_corrected_baseline_gate_passes() -> None:
    fingerprint = require_frozen_baseline(ROOT)
    assert validate_fingerprint(fingerprint, load_frozen_baseline()) == []


def test_workspace_digest_is_accepted_only_in_workspace_domain() -> None:
    fingerprint = _fingerprint()
    fingerprint["machine_policy"]["raw_sha256"] = WORKSPACE_GOVERNANCE_SHA
    assert _mismatch_names(fingerprint) == {"machine-policy raw SHA-256"}


def test_machine_policy_digest_is_accepted_only_in_policy_domain() -> None:
    fingerprint = _fingerprint()
    fingerprint["workspace_governance"]["content_sha256"] = MACHINE_POLICY_SHA
    assert _mismatch_names(fingerprint) == {"workspace-governance content SHA-256"}


def test_swapping_digest_domains_fails_both_identities() -> None:
    fingerprint = _fingerprint()
    fingerprint["workspace_governance"]["content_sha256"] = MACHINE_POLICY_SHA
    fingerprint["machine_policy"]["raw_sha256"] = WORKSPACE_GOVERNANCE_SHA
    assert _mismatch_names(fingerprint) == {
        "workspace-governance content SHA-256",
        "machine-policy raw SHA-256",
    }


def test_changed_policy_bytes_fail_raw_digest_and_length() -> None:
    fingerprint = _fingerprint()
    raw = (ROOT / "config/project/policy_pack.json").read_bytes() + b"\n"
    fingerprint["machine_policy"]["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    fingerprint["machine_policy"]["serialized_bytes"] = len(raw)
    assert _mismatch_names(fingerprint) == {
        "machine-policy raw SHA-256",
        "machine-policy serialized bytes",
    }


def test_changed_workspace_lock_digest_fails_locked_identity() -> None:
    fingerprint = _fingerprint()
    fingerprint["workspace_governance"]["locked_content_sha256"] = "0" * 64
    assert _mismatch_names(fingerprint) == {
        "workspace-governance locked content SHA-256"
    }


def test_wrong_policy_byte_length_fails_independently() -> None:
    fingerprint = _fingerprint()
    fingerprint["machine_policy"]["serialized_bytes"] = 74149
    assert _mismatch_names(fingerprint) == {"machine-policy serialized bytes"}


def test_wrong_repository_baseline_identity_fails() -> None:
    fingerprint = _fingerprint()
    fingerprint["repository"]["baseline_commit"] = "0" * 40
    assert _mismatch_names(fingerprint) == {"baseline repository commit"}


def test_negative_control_rejects_old_cross_domain_policy_comparison() -> None:
    fingerprint = _fingerprint()
    broken = deepcopy(fingerprint)
    broken["machine_policy"]["raw_sha256"] = broken["workspace_governance"][
        "content_sha256"
    ]
    assert "machine-policy raw SHA-256" in _mismatch_names(broken)


def test_fingerprint_cli_emits_matching_record(tmp_path: Path) -> None:
    output = tmp_path / "fingerprint.json"
    status = main(["fingerprint", "--root", str(ROOT), "--output", str(output)])
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["baseline_validation"] == {"status": "match", "mismatches": []}
    assert payload["machine_policy"]["raw_sha256"] == MACHINE_POLICY_SHA
