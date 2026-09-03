from __future__ import annotations

import json
from pathlib import Path

import pytest

import tools.governance.validate_project_contracts as contracts


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str, *, append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if append and path.exists():
        path.write_text(path.read_text(encoding="utf-8") + content, encoding="utf-8")
        return
    path.write_text(content, encoding="utf-8")


def test_canonical_governance_sync_detects_missing_owner_token(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack_path = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack_path,
        {
            "governance": {
                "canonical_governance_contract": {
                    "required_tokens": ["docs/governance/VERIFICATION.md"]
                }
            }
        },
    )
    dispatch_path = tmp_path / "AGENTS.md"
    _write_text(dispatch_path, "docs/governance/ENGINEERING.md\n")

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack_path)
    monkeypatch.setattr(contracts, "GOVERNANCE_DISPATCH_PATH", dispatch_path)

    issues = contracts._validate_canonical_governance_sync()

    assert issues
    assert any("VERIFICATION.md" in issue.message for issue in issues)


def test_canonical_governance_sync_reads_required_tokens_from_policy_pack(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack_path = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack_path,
        {
            "governance": {
                "canonical_governance_contract": {
                    "required_tokens": ["docs/governance/LOCAL_OWNER.md"]
                }
            }
        },
    )
    dispatch_path = tmp_path / "AGENTS.md"
    _write_text(dispatch_path, "docs/governance/ENGINEERING.md\n")

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack_path)
    monkeypatch.setattr(contracts, "GOVERNANCE_DISPATCH_PATH", dispatch_path)

    issues = contracts._validate_canonical_governance_sync()

    assert any("docs/governance/LOCAL_OWNER.md" in issue.message for issue in issues)


def test_policy_manifest_string_safety_detects_path_like_literals(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project"
    manifests_dir = policy_root / "policy" / "manifests"
    path_like_literal = r"value:[ \t]*\n[ \t]*" + "C:" + r"\\temp"
    _write_json(
        policy_root / "policy_pack.json",
        {
            "governance": {"schema_version": 1},
            "code_rules": {"schema_version": 1},
            "maintenance_contract": {"schema_version": 1},
            "maintenance_docs": {},
            "deprecated_authorities": {},
        },
    )
    _write_json(
        manifests_dir / "help_assets_manifest.json",
        {"rules": [{"id": "test", "example": path_like_literal}]},
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_root / "policy_pack.json")
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues
    assert any("path-like literal" in issue.message for issue in issues)


def test_policy_manifest_string_safety_allows_clean_manifests(
    tmp_path: Path, monkeypatch
) -> None:
    policy_root = tmp_path / "config" / "project"
    manifests_dir = policy_root / "policy" / "manifests"
    _write_json(
        policy_root / "policy_pack.json",
        {
            "governance": {"schema_version": 1},
            "code_rules": {"schema_version": 1},
            "maintenance_contract": {"schema_version": 1},
            "maintenance_docs": {},
            "deprecated_authorities": {},
        },
    )
    _write_json(
        manifests_dir / "help_assets_manifest.json",
        {"rules": [{"id": "test", "forbidden_regex": [r"value:[ \t]*\n[ \t]*x"]}]},
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_root / "policy_pack.json")
    monkeypatch.setattr(contracts, "POLICY_MANIFEST_DIR", manifests_dir)
    issues = contracts._validate_policy_manifest_string_safety()
    assert issues == []


def test_required_paths_detect_untracked_file(tmp_path: Path, monkeypatch) -> None:
    rel = "docs/governance/ENGINEERING.md"
    workflow_doc = tmp_path / rel
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("workflow", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: set())

    issues = contracts._validate_required_paths(
        {"required_paths": {"root_docs": [rel]}}
    )

    assert any(
        issue.message == f"required path is not tracked in git: {rel}"
        for issue in issues
    )


def test_required_paths_accept_git_tracked_file(tmp_path: Path, monkeypatch) -> None:
    rel = "docs/governance/ENGINEERING.md"
    workflow_doc = tmp_path / rel
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("workflow", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: {rel})

    issues = contracts._validate_required_paths(
        {"required_paths": {"root_docs": [rel]}}
    )

    assert issues == []


def test_architecture_evidence_required_paths_detect_missing_document(
    tmp_path: Path, monkeypatch
) -> None:
    payload = json.loads(contracts.POLICY_PACK_PATH.read_text(encoding="utf-8"))
    evidence_paths = payload["maintenance_contract"]["required_paths"][
        "architecture_evidence"
    ]
    missing_rel = "docs/architecture/parity_pilot_audit_and_promotion_gates.md"

    assert evidence_paths == [
        "docs/architecture/first_subsystem_parity_pilot.md",
        missing_rel,
        "docs/architecture/second_parity_slice_candidate_selection.md",
        "docs/architecture/trace_metadata_identity_digest_parity.md",
        "docs/architecture/topology_identifier_normalization_parity.md",
        "docs/architecture/parity_evidence_review_and_third_slice_selection.md",
        "docs/architecture/parity_evidence_package_review.md",
        "docs/architecture/trace_schema_version_normalization_parity.md",
    ]

    for rel in evidence_paths:
        if rel == missing_rel:
            continue
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("evidence\n", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        contracts, "_git_tracked_paths", lambda issues: set(evidence_paths)
    )

    issues = contracts._validate_required_paths(
        {"required_paths": {"architecture_evidence": evidence_paths}}
    )

    assert [issue.message for issue in issues] == [
        f"missing required path: {missing_rel}"
    ]


def test_workspace_bundle_governance_routes_validator(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_workspace_bundle_governance()

    assert any(
        "tools/templates/governance/README.md" in issue.message for issue in issues
    )


def test_governance_directives_include_staged_migration_contract() -> None:
    payload = json.loads(contracts.POLICY_PACK_PATH.read_text(encoding="utf-8"))
    directives = payload["governance"]["contributor_directives"]["directives"]
    directive_ids = {item["id"] for item in directives}
    assert {
        "staged_migration_honesty",
        "additive_migration_first",
        "delta_report_required",
    }.issubset(directive_ids)


def test_change_governance_rule_requires_compositional_routing_tokens() -> None:
    manifest = contracts._load_manifest()
    rules = manifest["content_rules"]
    change_rule = next(
        rule for rule in rules if rule["file"] == "docs/governance/CHANGE_GOVERNANCE.md"
    )
    must_contain = set(change_rule["must_contain"])
    assert "Authority order" in must_contain
    assert "config/project/policy_pack.json" in must_contain
    assert "## Compositional routing" in must_contain
    assert "`review_only`" in must_contain
    assert "`governance_and_tooling`" in must_contain
    assert "VERIFICATION.md" in must_contain


def test_current_state_rule_enforces_restart_only_scope() -> None:
    manifest = contracts._load_manifest()
    rules = manifest["content_rules"]
    current_state_rule = next(
        rule for rule in rules if rule["file"] == "CURRENT_STATE.md"
    )

    must_contain = set(current_state_rule["must_contain"])
    must_not_contain = set(current_state_rule["must_not_contain"])
    must_not_match_regex = set(current_state_rule["must_not_match_regex"])

    assert "## Active Focus" in must_contain
    assert "## Next Acceptance Boundary" in must_contain
    assert "## Known Watchouts" not in must_contain
    assert "docs/history/current_state_archive_2026-07-30.md" not in must_contain
    assert "docs/PROJECT_STRUCTURE.md" in must_contain
    assert "## Active Batch Note" in must_not_contain
    assert "## What This Batch Changed" in must_not_contain
    assert "^Branch:" in must_not_match_regex


def test_menu_simplification_rule_reads_required_rows_from_policy_pack(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_simplification_manifest_rule": {
                    "rule_id": "menu-simplification-common-settings",
                    "required_shared_row_keys": ["shared_test_key"],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "menus": {"settings_game_root": {"items": []}},
            "setup_fields": {"runtime": [{"attr": "shared_test_key"}]},
        },
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    issues = contracts._validate_menu_simplification_rule()

    assert any("shared_test_key" in issue.message for issue in issues)


def test_menu_structure_single_source_reads_policy_pack_contract_data(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    literal_target = (
        tmp_path
        / "src"
        / "tet4d"
        / "ui"
        / "pygame"
        / "launch"
        / "settings_hub_model.py"
    )
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_structure_single_source": {
                    "required_menus": ["settings_root"],
                    "required_submenu_labels": [
                        {"menu_id": "settings_root", "labels": ["Custom"]}
                    ],
                    "required_item_labels": [],
                    "required_item_types": ["submenu"],
                    "banned_python_literals": [
                        {
                            "file": "src/tet4d/ui/pygame/launch/settings_hub_model.py",
                            "literal": "FORBIDDEN_LITERAL =",
                            "message": "custom drift",
                        }
                    ],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "menus": {
                "settings_root": {"items": [{"type": "submenu", "label": "Different"}]}
            }
        },
    )
    _write_text(literal_target, "FORBIDDEN_LITERAL = True\n")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    issues = contracts._validate_menu_structure_single_source_of_truth()

    assert any("Custom" in issue.message for issue in issues)
    assert any(issue.message == "custom drift" for issue in issues)


def test_menu_structure_single_option_policy_detects_redundant_pages() -> None:
    payload = {
        "menus": {
            "submenu_wrapper": {
                "items": [{"type": "submenu", "label": "Child", "menu_id": "child"}]
            },
            "action_back": {
                "items": [
                    {"type": "action", "label": "Open", "action_id": "open"},
                    {"type": "action", "label": "Back", "action_id": "back"},
                ]
            },
            "setting_back": {
                "items": [
                    {
                        "type": "toggle",
                        "label": "Enabled",
                        "semantic_type": "bool",
                        "setting_id": "enabled",
                    },
                    {"type": "action", "label": "Back", "action_id": "back"},
                ]
            },
            "capture_exempt": {
                "layout_role": "capture",
                "items": [
                    {"type": "action", "label": "Confirm", "action_id": "confirm"}
                ],
            },
            "allow_exempt": {
                "allow_single_option": True,
                "allow_single_option_reason": "Intentional landing page.",
                "items": [{"type": "action", "label": "Open", "action_id": "open"}],
            },
        }
    }

    issues = contracts._validate_menu_structure_single_option_menus(
        "config/menu/structure.json",
        payload,
    )

    messages = "\n".join(issue.message for issue in issues)
    assert "submenu_wrapper" in messages
    assert "action_back" in messages
    assert "setting_back" in messages
    assert "capture_exempt" not in messages
    assert "allow_exempt" not in messages


def test_menu_control_typing_detects_mismatched_semantic_controls(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_control_typing_contract": {
                    "setting_semantic_types": ["bool", "enum", "int", "float"],
                    "menu_control_types": ["toggle", "selector", "slider", "stepper"],
                    "setup_control_types": [
                        "toggle",
                        "selector",
                        "slider",
                        "stepper",
                        "numeric_entry",
                    ],
                    "selector_options_key_required": True,
                    "enum_setup_option_source_tokens": ["piece_set_labels"],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "settings_option_labels": {"good_enum": ["A", "B"]},
            "menus": {
                "settings_game_root": {
                    "items": [
                        {
                            "id": "bad_enum_slider",
                            "type": "slider",
                            "semantic_type": "enum",
                            "setting_id": "bad_enum_slider",
                        }
                    ]
                }
            },
            "setup_fields": {
                "2d": [
                    {
                        "label": "Topology",
                        "attr": "topology_mode",
                        "semantic_type": "enum",
                        "control": "slider",
                        "min": 0,
                        "max": 2,
                    }
                ]
            },
        },
    )

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    issues = contracts._validate_menu_control_typing()

    assert any("bad_enum_slider" in issue.message for issue in issues)
    assert any(
        "enum fields must use control=selector" in issue.message for issue in issues
    )


def test_menu_control_typing_accepts_semantic_type_aligned_controls(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    menu_path = tmp_path / "config" / "menu" / "structure.json"
    _write_json(
        policy_pack,
        {
            "governance": {
                "menu_control_typing_contract": {
                    "setting_semantic_types": ["bool", "enum", "int", "float"],
                    "menu_control_types": ["toggle", "selector", "slider", "stepper"],
                    "setup_control_types": [
                        "toggle",
                        "selector",
                        "slider",
                        "stepper",
                        "numeric_entry",
                    ],
                    "selector_options_key_required": True,
                    "enum_setup_option_source_tokens": ["piece_set_labels"],
                }
            }
        },
    )
    _write_json(
        menu_path,
        {
            "settings_option_labels": {
                "game_random_mode": ["Fixed seed", "True random"]
            },
            "menus": {
                "settings_game_root": {
                    "items": [
                        {
                            "id": "game_random_mode",
                            "type": "selector",
                            "semantic_type": "enum",
                            "options_key": "game_random_mode",
                            "setting_id": "game_random_mode",
                        },
                        {
                            "id": "game_seed",
                            "type": "stepper",
                            "semantic_type": "int",
                            "setting_id": "game_seed",
                        },
                        {
                            "id": "display_fullscreen",
                            "type": "toggle",
                            "semantic_type": "bool",
                            "setting_id": "display_fullscreen",
                        },
                    ]
                }
            },
            "setup_fields": {
                "2d": [
                    {
                        "label": "Piece set",
                        "attr": "piece_set_index",
                        "semantic_type": "enum",
                        "control": "selector",
                        "options_source": "piece_set_labels",
                    },
                    {
                        "label": "Board width",
                        "attr": "width",
                        "semantic_type": "int",
                        "control": "stepper",
                        "min": 6,
                        "max": 16,
                    },
                ]
            },
        },
    )

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)
    monkeypatch.setattr(contracts, "MENU_STRUCTURE_PATH", menu_path)

    assert contracts._validate_menu_control_typing() == []


def test_menu_control_typing_rejects_godot_control_type_absent_from_policy(
    tmp_path: Path, monkeypatch
) -> None:
    spec_path = tmp_path / "setup_field_spec.gd"
    spec_path.write_text(
        'const ALLOWED_CONTROL_TYPES := ["selector", "future_control"]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(contracts, "GODOT_SETUP_FIELD_SPEC_PATH", spec_path)

    issues: list[contracts.ValidationIssue] = []
    contracts._validate_godot_setup_control_vocabulary(
        {"selector", "numeric_entry"}, issues
    )

    assert any(
        "future_control" in issue.message
        and "menu_control_typing_contract.setup_control_types" in issue.message
        for issue in issues
    )


def test_deprecated_authority_checks_detect_reintroduced_path(
    tmp_path: Path, monkeypatch
) -> None:
    blocked = tmp_path / "docs" / "RDS_AND_CODEX.md"
    blocked.parent.mkdir(parents=True, exist_ok=True)
    blocked.write_text("stale redirect", encoding="utf-8")
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack,
        {
            "deprecated_authorities": {
                "blocked_paths": ["docs/RDS_AND_CODEX.md"],
                "reference_checks": {
                    "files": ["AGENTS.md"],
                    "must_not_contain": ["docs/RDS_AND_CODEX.md"],
                },
            }
        },
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)

    issues = contracts._validate_deprecated_authorities()

    assert issues
    assert any("deprecated authority path present" in issue.message for issue in issues)


def test_deprecated_authority_checks_detect_stale_active_reference(
    tmp_path: Path, monkeypatch
) -> None:
    active_path = tmp_path / ".github" / "pull_request_template.md"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text("docs/governance/task_contract.md\n", encoding="utf-8")
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack,
        {
            "deprecated_authorities": {
                "blocked_paths": [],
                "reference_checks": {
                    "files": [".github/pull_request_template.md"],
                    "must_not_contain": ["docs/governance/task_contract.md"],
                },
            }
        },
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)

    issues = contracts._validate_deprecated_authorities()

    assert any(
        "still references deprecated authority token" in issue.message
        for issue in issues
    )


def test_deprecated_authority_checks_allow_historical_reference(
    tmp_path: Path, monkeypatch
) -> None:
    active_path = tmp_path / ".github" / "pull_request_template.md"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(
        "docs/history/tasks/task_contract_ledger_through_2026-08-31.md\n",
        encoding="utf-8",
    )
    policy_pack = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack,
        {
            "deprecated_authorities": {
                "blocked_paths": ["docs/governance/task_contract.md"],
                "reference_checks": {
                    "files": [".github/pull_request_template.md"],
                    "must_not_contain": ["docs/governance/task_contract.md"],
                },
            }
        },
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)

    assert contracts._validate_deprecated_authorities() == []


def test_retired_active_ledgers_stay_out_of_machine_governance() -> None:
    payload = json.loads(contracts.POLICY_PACK_PATH.read_text(encoding="utf-8"))
    retired = {
        "docs/governance/task_contract.md",
        "docs/governance/completion_report.md",
    }

    maintenance = payload["maintenance_contract"]
    required_paths = {
        path for paths in maintenance["required_paths"].values() for path in paths
    }
    content_rule_files = {rule["file"] for rule in maintenance["content_rules"]}
    assert retired.isdisjoint(required_paths)
    assert retired.isdisjoint(content_rule_files)

    deprecated = payload["deprecated_authorities"]
    assert retired.issubset(set(deprecated["blocked_paths"]))

    checks = deprecated["reference_checks"]
    active_files = {
        "AGENTS.md",
        "docs/governance/ENGINEERING.md",
        "docs/governance/VERIFICATION.md",
        "docs/governance/SECURITY_AND_SANITATION.md",
        "docs/governance/CONFIG_AND_GENERATED_DATA.md",
        "docs/governance/NATIVE_AND_PLATFORM.md",
        "docs/governance/CHANGE_GOVERNANCE.md",
        ".github/pull_request_template.md",
        "godot/AGENTS.md",
        "native/AGENTS.md",
        "CURRENT_STATE.md",
    }
    assert active_files.issubset(set(checks["files"]))
    assert retired.issubset(set(checks["must_not_contain"]))


# Codex routing model contract


def _codex_authority_model() -> dict[str, str]:
    return {
        "machine_authority": "config/project/policy_pack.json",
        "dispatch_file": "AGENTS.md",
        "handoff_doc": "CURRENT_STATE.md",
        "product_requirements_root": "docs/rds/",
        "architecture_contract": "docs/ARCHITECTURE_CONTRACT.md",
        "topology_current_authority": "docs/architecture/topology_playground_current_authority.md",
        **contracts.CODEX_AUTHORITY_POINTERS,
    }


def _codex_routes() -> dict[str, object]:
    return {
        "product_planning": {
            "authority_keys": ["professional_product_programme"],
            "typical_verification_requirements": ["documentation"],
        },
        "python_reference_engine": {
            "authority_keys": ["architecture_contract"],
            "typical_verification_requirements": ["python", "deterministic"],
        },
        "godot_product_shell": {
            "dispatch_paths": ["godot/AGENTS.md"],
            "authority_keys": ["subsystem_authority_map"],
            "typical_verification_requirements": ["godot"],
        },
        "native_deterministic_core": {
            "dispatch_paths": ["native/AGENTS.md"],
            "authority_keys": ["authority_transfer_and_establishment_protocol"],
            "typical_verification_requirements": ["native", "deterministic"],
        },
        "topology_and_explorer": {
            "authority_keys": ["topology_current_authority"],
            "typical_verification_requirements": ["deterministic"],
        },
        "governance_and_tooling": {
            "authority_keys": ["machine_authority", "change_governance"],
            "typical_verification_requirements": ["governance_structure"],
        },
        "packaging_and_release": {
            "dispatch_paths": ["docs/RELEASE_CHECKLIST.md"],
            "typical_verification_requirements": ["packaging", "platform"],
        },
    }


def _codex_policy_payload() -> dict[str, object]:
    return {
        "authority_model": _codex_authority_model(),
        "codex_routing": {
            "schema_version": 2,
            "routes": _codex_routes(),
            "workflow_modifiers": sorted(contracts.SUPPORTED_CODEX_WORKFLOW_MODIFIERS),
            "verification_requirements": sorted(
                contracts.SUPPORTED_CODEX_VERIFICATION_REQUIREMENTS
            ),
        },
    }


def _install_codex_policy_fixture(
    tmp_path: Path, monkeypatch, payload: dict[str, object]
) -> set[str]:
    policy_path = tmp_path / "config/project/policy_pack.json"
    _write_json(policy_path, payload)
    paths = {
        *contracts.CODEX_AUTHORITY_POINTERS.values(),
        "godot/AGENTS.md",
        "native/AGENTS.md",
        "docs/RELEASE_CHECKLIST.md",
    }
    for rel in paths:
        _write_text(tmp_path / rel, rel + "\n")
    tracked = {"config/project/policy_pack.json", *paths}
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: tracked)
    return tracked


def test_codex_routing_accepts_complete_contract(tmp_path: Path, monkeypatch) -> None:
    _install_codex_policy_fixture(tmp_path, monkeypatch, _codex_policy_payload())
    assert contracts._validate_codex_routing_model() == []


def test_codex_routing_rejects_missing_pointer(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["authority_model"].pop("professional_product_programme")
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("professional_product_programme" in issue.message for issue in issues)


def test_codex_routing_rejects_empty_pointer(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["authority_model"]["professional_product_programme"] = ""
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("professional_product_programme" in issue.message for issue in issues)


def test_codex_routing_rejects_absolute_pointer(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["authority_model"]["professional_product_programme"] = "/tmp/programme.md"
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("repository-relative" in issue.message for issue in issues)


def test_codex_routing_rejects_traversal_pointer(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["authority_model"]["professional_product_programme"] = "../programme.md"
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("repository-relative" in issue.message for issue in issues)


def test_codex_routing_rejects_missing_pointer_target(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    target = (
        tmp_path / contracts.CODEX_AUTHORITY_POINTERS["professional_product_programme"]
    )
    target.unlink()
    issues = contracts._validate_codex_routing_model()
    assert any("target does not exist" in issue.message for issue in issues)


def test_codex_routing_rejects_untracked_pointer_target(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    tracked = _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    target = contracts.CODEX_AUTHORITY_POINTERS["professional_product_programme"]
    monkeypatch.setattr(
        contracts, "_git_tracked_paths", lambda issues: tracked - {target}
    )
    issues = contracts._validate_codex_routing_model()
    assert any(
        "not tracked" in issue.message and target in issue.message for issue in issues
    )


def test_codex_routing_rejects_unknown_route(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["unknown_route"] = payload["codex_routing"][
        "routes"
    ].pop("product_planning")
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("unknown_route" in issue.message for issue in issues)
    assert any("product_planning" in issue.message for issue in issues)


def test_codex_routing_rejects_unknown_modifier(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["workflow_modifiers"][-1] = "unknown_modifier"
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("unknown_modifier" in issue.message for issue in issues)


def test_codex_routing_rejects_unknown_requirement(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["verification_requirements"][-1] = "unknown_requirement"
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("unknown_requirement" in issue.message for issue in issues)


def test_codex_routing_rejects_unknown_authority_key(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["product_planning"]["authority_keys"] = [
        "missing_authority"
    ]
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("missing_authority" in issue.message for issue in issues)


def test_codex_routing_rejects_invalid_dispatch_path(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["packaging_and_release"]["dispatch_paths"] = [
        "../release.md"
    ]
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("repository-relative" in issue.message for issue in issues)


def test_codex_routing_rejects_unknown_typical_requirement(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["product_planning"][
        "typical_verification_requirements"
    ] = ["unknown_requirement"]
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any("unknown_requirement" in issue.message for issue in issues)


def test_codex_routing_accepts_authority_only_route(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["product_planning"].pop("dispatch_paths", None)
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    assert contracts._validate_codex_routing_model() == []


def test_codex_routing_accepts_dispatch_only_route(tmp_path: Path, monkeypatch) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["packaging_and_release"].pop(
        "authority_keys", None
    )
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    assert contracts._validate_codex_routing_model() == []


def test_codex_routing_accepts_route_with_authority_and_dispatch(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    route = payload["codex_routing"]["routes"]["godot_product_shell"]
    assert "authority_keys" in route and "dispatch_paths" in route
    assert contracts._validate_codex_routing_model() == []


def test_codex_routing_rejects_route_without_context(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    route = payload["codex_routing"]["routes"]["product_planning"]
    route.pop("authority_keys", None)
    route.pop("dispatch_paths", None)
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any(
        "must define authority_keys or dispatch_paths" in issue.message
        for issue in issues
    )


def test_codex_routing_rejects_empty_authority_keys(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["product_planning"]["authority_keys"] = []
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any(
        "authority_keys must be a non-empty" in issue.message for issue in issues
    )


def test_codex_routing_rejects_empty_dispatch_paths(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    payload["codex_routing"]["routes"]["packaging_and_release"]["dispatch_paths"] = []
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    issues = contracts._validate_codex_routing_model()
    assert any(
        "dispatch_paths must be a non-empty" in issue.message for issue in issues
    )


def test_codex_routing_is_structural_not_roadmap_prose(
    tmp_path: Path, monkeypatch
) -> None:
    payload = _codex_policy_payload()
    _install_codex_policy_fixture(tmp_path, monkeypatch, payload)
    assert "Stage 54" not in json.dumps(payload)
    assert contracts._validate_codex_routing_model() == []


def _write_legacy_redirect(root: Path, payload: object) -> None:
    (root / "config" / "project").mkdir(parents=True, exist_ok=True)
    (root / "config" / "project" / "policy_pack.json").write_text(
        "{}\n", encoding="utf-8"
    )
    _write_json(root / contracts.LEGACY_POLICY_MANIFEST_REL, payload)


def _redirect_issues(root: Path, monkeypatch) -> list[str]:
    monkeypatch.setattr(contracts, "PROJECT_ROOT", root)
    return [
        issue.message for issue in contracts._validate_legacy_policy_manifest_redirect()
    ]


def test_legacy_policy_manifest_redirect_accepts_canonical_target(
    tmp_path: Path, monkeypatch
) -> None:
    _write_legacy_redirect(
        tmp_path, {"deprecated": True, "replaced_by": contracts.POLICY_PACK_REL}
    )

    assert _redirect_issues(tmp_path, monkeypatch) == []


def test_legacy_policy_manifest_redirect_absence_is_not_an_issue(
    tmp_path: Path, monkeypatch
) -> None:
    assert _redirect_issues(tmp_path, monkeypatch) == []


@pytest.mark.parametrize(
    ("payload", "fragment"),
    [
        (
            {"deprecated": "true", "replaced_by": "config/project/policy_pack.json"},
            "exactly true",
        ),
        ({"deprecated": True}, "non-empty relative path"),
        ({"deprecated": True, "replaced_by": ""}, "non-empty relative path"),
        ({"deprecated": True, "replaced_by": "/etc/policy_pack.json"}, "absolute"),
        ({"deprecated": True, "replaced_by": "~/policy_pack.json"}, "absolute"),
        ({"deprecated": True, "replaced_by": "../policy_pack.json"}, "escape"),
        ({"deprecated": True, "replaced_by": "config/../policy_pack.json"}, "escape"),
        (
            {"deprecated": True, "replaced_by": "config/project/policy/pack.json"},
            "canonical",
        ),
        (
            {"deprecated": True, "replaced_by": "config/project/policy/pack.json"},
            "does not exist",
        ),
    ],
)
def test_legacy_policy_manifest_redirect_rejects_malformed_variants(
    tmp_path: Path, monkeypatch, payload: object, fragment: str
) -> None:
    _write_legacy_redirect(tmp_path, payload)

    messages = _redirect_issues(tmp_path, monkeypatch)

    assert any(fragment in message for message in messages), messages


def test_legacy_policy_manifest_redirect_rejects_non_object(
    tmp_path: Path, monkeypatch
) -> None:
    _write_legacy_redirect(tmp_path, ["deprecated"])

    assert any("JSON object" in m for m in _redirect_issues(tmp_path, monkeypatch))


def test_legacy_policy_manifest_redirect_is_part_of_manifest_validation() -> None:
    assert not any(issue.kind == "redirect" for issue in contracts.validate_manifest())
