from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.experiments.governance_manifest_quality import baseline
from tools.experiments.governance_manifest_quality.baseline import (
    POLICY_PATH,
    ROOT,
    WORKSPACE_LOCK_PATH,
    WORKSPACE_PACK_PATH,
    BaselineMismatchError,
    load_frozen_baseline,
    measure_fingerprint,
    measure_frozen_baseline_snapshot,
    require_frozen_baseline,
    require_frozen_baseline_snapshot,
    validate_fingerprint,
)
from tools.experiments.governance_manifest_quality.cli import main
from tools.governance.policy_pack_io import load_policy_pack
from tools.governance.validate_governance_surface import (
    physical_loc_of,
    policy_structure_metrics,
)
from tools.workspace_governance.validators.core import pack_hash

BASELINE_COMMIT = "7ca7f2e0697068ac0113c12d2d0a0a9d9ac14875"
MACHINE_POLICY_SHA = "44c126b6a80e9b37a9b2300badcaae1dfb124cc9cf605a247f508a68c4b798a3"
WORKSPACE_GOVERNANCE_SHA = (
    "6a3ca68304589a367b0eacfb593336ceef13c80221c1ff4bd7e9775432c3ccae"
)


def _snapshot_fingerprint() -> dict:
    """The historical treatment, read from its own Git commit."""
    return measure_frozen_baseline_snapshot(ROOT)


def _checkout_fingerprint() -> dict:
    """The strict reproduction producer, measuring the working checkout."""
    return measure_fingerprint(ROOT, baseline_commit=BASELINE_COMMIT)


def _mismatch_names(fingerprint: dict) -> set[str]:
    return {
        mismatch.split(": measured", 1)[0]
        for mismatch in validate_fingerprint(fingerprint, load_frozen_baseline())
    }


def test_fingerprint_independently_measures_all_three_identity_domains() -> None:
    fingerprint = _snapshot_fingerprint()
    repository = fingerprint["repository"]
    workspace = fingerprint["workspace_governance"]
    policy = fingerprint["machine_policy"]

    assert repository["baseline_commit"] == BASELINE_COMMIT
    assert repository["snapshot_commit"] == BASELINE_COMMIT
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
    assert fingerprint["fingerprint_source"] == "historical_git_snapshot"


def test_historical_snapshot_survives_an_evolved_current_treatment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_pack_hash = baseline.pack_hash

    def evolved_pack_hash(*args: object, **kwargs: object) -> tuple[str, list[str]]:
        _, files = original_pack_hash(*args, **kwargs)
        return "0" * 64, files

    monkeypatch.setattr(baseline, "pack_hash", evolved_pack_hash)
    with pytest.raises(BaselineMismatchError, match="content SHA-256"):
        require_frozen_baseline(ROOT)
    fingerprint = require_frozen_baseline_snapshot(ROOT)
    assert validate_fingerprint(fingerprint, load_frozen_baseline()) == []


def test_workspace_digest_is_accepted_only_in_workspace_domain() -> None:
    fingerprint = _snapshot_fingerprint()
    fingerprint["machine_policy"]["raw_sha256"] = WORKSPACE_GOVERNANCE_SHA
    assert _mismatch_names(fingerprint) == {"machine-policy raw SHA-256"}


def test_machine_policy_digest_is_accepted_only_in_policy_domain() -> None:
    fingerprint = _snapshot_fingerprint()
    fingerprint["workspace_governance"]["content_sha256"] = MACHINE_POLICY_SHA
    assert _mismatch_names(fingerprint) == {"workspace-governance content SHA-256"}


def test_swapping_digest_domains_fails_both_identities() -> None:
    fingerprint = _snapshot_fingerprint()
    fingerprint["workspace_governance"]["content_sha256"] = MACHINE_POLICY_SHA
    fingerprint["machine_policy"]["raw_sha256"] = WORKSPACE_GOVERNANCE_SHA
    assert _mismatch_names(fingerprint) == {
        "workspace-governance content SHA-256",
        "machine-policy raw SHA-256",
    }


def test_changed_policy_bytes_fail_raw_digest_and_length() -> None:
    fingerprint = _snapshot_fingerprint()
    fingerprint["machine_policy"]["raw_sha256"] = hashlib.sha256(b"changed").hexdigest()
    fingerprint["machine_policy"]["serialized_bytes"] += 1
    assert _mismatch_names(fingerprint) == {
        "machine-policy raw SHA-256",
        "machine-policy serialized bytes",
    }


def test_changed_workspace_lock_digest_fails_locked_identity() -> None:
    fingerprint = _snapshot_fingerprint()
    fingerprint["workspace_governance"]["locked_content_sha256"] = "0" * 64
    assert _mismatch_names(fingerprint) == {
        "workspace-governance locked content SHA-256"
    }


def test_wrong_policy_byte_length_fails_independently() -> None:
    fingerprint = _snapshot_fingerprint()
    fingerprint["machine_policy"]["serialized_bytes"] = 74149
    assert _mismatch_names(fingerprint) == {"machine-policy serialized bytes"}


def test_wrong_repository_baseline_identity_fails() -> None:
    fingerprint = _snapshot_fingerprint()
    fingerprint["repository"]["baseline_commit"] = "0" * 40
    assert _mismatch_names(fingerprint) == {"baseline repository commit"}


def test_negative_control_rejects_old_cross_domain_policy_comparison() -> None:
    fingerprint = _snapshot_fingerprint()
    broken = deepcopy(fingerprint)
    broken["machine_policy"]["raw_sha256"] = broken["workspace_governance"][
        "content_sha256"
    ]
    assert "machine-policy raw SHA-256" in _mismatch_names(broken)


def test_fingerprint_cli_preserves_strict_reproduction_status(tmp_path: Path) -> None:
    output = tmp_path / "fingerprint.json"
    status = main(["fingerprint", "--root", str(ROOT), "--output", str(output)])
    payload = json.loads(output.read_text(encoding="utf-8"))
    try:
        require_frozen_baseline(ROOT)
    except BaselineMismatchError as exc:
        assert status == 2
        assert payload["baseline_validation"] == {
            "status": "mismatch",
            "mismatches": exc.mismatches,
        }
    else:
        assert status == 0
        assert payload["baseline_validation"] == {"status": "match", "mismatches": []}
    assert payload["fingerprint_source"] == "current_checkout"


# --- Strict (current-checkout) producer ------------------------------------------
# These assert where each identity comes from rather than that the checkout still
# equals the frozen declaration. Byte-equality is exactly what this PR stops
# requiring of later checkouts, so a control that assumed it would fail the moment
# governance legitimately evolves.


def test_checkout_producer_reads_each_identity_from_its_own_source() -> None:
    fingerprint = _checkout_fingerprint()
    policy_bytes = (ROOT / POLICY_PATH).read_bytes()
    lock = json.loads((ROOT / WORKSPACE_LOCK_PATH).read_text(encoding="utf-8"))
    pack_digest, pack_files = pack_hash(ROOT / WORKSPACE_PACK_PATH)

    machine_policy = fingerprint["machine_policy"]
    assert machine_policy["raw_sha256"] == hashlib.sha256(policy_bytes).hexdigest()
    assert machine_policy["serialized_bytes"] == len(policy_bytes)

    workspace = fingerprint["workspace_governance"]
    assert workspace["content_sha256"] == pack_digest
    assert workspace["locked_content_sha256"] == lock["content_sha256"]
    assert workspace["locked_revision"] == lock["revision"]
    assert workspace["pack_path"] == lock["pack_path"]
    assert workspace["locked_files_match_computed"] == (lock["files"] == pack_files)

    # The two digest domains must never be sourced from each other.
    assert machine_policy["raw_sha256"] != workspace["content_sha256"]

    assert fingerprint["repository"]["baseline_commit"] == BASELINE_COMMIT
    assert fingerprint["fingerprint_source"] == "current_checkout"
    assert isinstance(fingerprint["governance_surface_issues"], list)


def test_checkout_producer_surfaces_an_evolved_pack_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A changed pack must fail the workspace domain and only that domain."""
    original = baseline.pack_hash

    def evolved(*args: object, **kwargs: object) -> tuple[str, list[str]]:
        _, files = original(*args, **kwargs)
        return "0" * 64, files

    monkeypatch.setattr(baseline, "pack_hash", evolved)
    fingerprint = _checkout_fingerprint()
    assert fingerprint["workspace_governance"]["content_sha256"] == "0" * 64
    assert fingerprint["machine_policy"]["raw_sha256"] == MACHINE_POLICY_SHA
    # Domain isolation, not an exact global set: once the pack legitimately
    # advances past the frozen declaration the checkout carries other, real
    # workspace mismatches, and permitting exactly that is the point of the
    # snapshot split.
    mismatches = _mismatch_names(fingerprint)
    assert "workspace-governance content SHA-256" in mismatches
    assert "machine-policy raw SHA-256" not in mismatches
    assert "machine-policy serialized bytes" not in mismatches


def test_checkout_producer_surfaces_a_pack_file_list_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pack whose file list drifts from the lock must fail the lock identity."""
    original = baseline.pack_hash

    def extra_file(*args: object, **kwargs: object) -> tuple[str, list[str]]:
        digest, files = original(*args, **kwargs)
        return digest, [*files, "unlocked_addition.md"]

    monkeypatch.setattr(baseline, "pack_hash", extra_file)
    fingerprint = _checkout_fingerprint()
    assert fingerprint["workspace_governance"]["locked_files_match_computed"] is False
    assert "workspace-governance locked files" in _mismatch_names(fingerprint)


# --- Producer parity --------------------------------------------------------------


def test_historical_metrics_match_the_checkout_structure_helpers(
    tmp_path: Path,
) -> None:
    """Both producers must measure identical content identically.

    The historical producer reads Git blobs and the strict producer reads files.
    Duplicating either measurement is how a node count silently drifts, so this
    materializes the frozen commit and drives the checkout-side helpers over it.
    """
    snapshot = _snapshot_fingerprint()
    commit = load_frozen_baseline().baseline_repository_commit

    def materialize(rel: str) -> Path:
        blob = subprocess.run(
            ["git", "show", f"{commit}:{rel}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        return path

    policy = load_policy_pack(materialize(POLICY_PATH.as_posix()))
    nodes, leaves, depth = policy_structure_metrics(policy)
    machine_policy = snapshot["machine_policy"]
    assert machine_policy["node_count"] == nodes
    assert machine_policy["leaf_count"] == leaves
    assert machine_policy["maximum_nesting_depth"] == depth
    assert machine_policy["largest_top_level_section"]["bytes"] == max(
        len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
        for value in policy.values()
    )

    human = policy["governance_surface"]["active_governance"]["human"]
    assert snapshot["human_governance_loc"] == sum(
        physical_loc_of(materialize(rel).read_text(encoding="utf-8")) for rel in human
    )


def test_historical_snapshot_reports_no_surface_verdict() -> None:
    """A historical treatment is not judged by the contemporary validator."""
    snapshot = _snapshot_fingerprint()
    assert snapshot["governance_surface_issues"] is None
    assert snapshot["fingerprint_source"] == "historical_git_snapshot"


def test_historical_pack_hash_rejects_an_undeclared_algorithm() -> None:
    """The historical hasher must not silently apply v1 framing to a v2 pack."""
    commit = load_frozen_baseline().baseline_repository_commit
    lock = json.loads((ROOT / WORKSPACE_LOCK_PATH).read_text(encoding="utf-8"))
    manifest = {
        "lock_algorithm": "sha256-path-and-content-v2",
        "pack_hash_excludes": [],
    }
    with pytest.raises(ValueError, match="unsupported pack hash algorithm"):
        baseline._historical_pack_hash(ROOT, commit, lock["pack_path"], manifest)
