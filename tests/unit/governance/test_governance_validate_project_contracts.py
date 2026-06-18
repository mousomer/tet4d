from __future__ import annotations

import json
from pathlib import Path

import tools.governance.validate_project_contracts as contracts


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_policy_index_sync_detects_missing_unified_contract_token(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack_path = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack_path,
        {
            "governance": {
                "contracts": {
                    "policy_pack": "config/project/policy_pack.json",
                    "secret_scan": "config/project/policy/manifests/secret_scan.json",
                }
            }
        },
    )
    index_path = tmp_path / "docs" / "policies" / "INDEX.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        "docs/policies/CI_COMPLIANCE_RUNBOOK.md\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack_path)
    monkeypatch.setattr(contracts, "POLICY_INDEX_PATH", index_path)

    issues = contracts._validate_policy_index_sync()

    assert issues
    assert any("policy_pack.json" in issue.message for issue in issues)


def test_policy_index_sync_reads_required_tokens_from_policy_pack(
    tmp_path: Path, monkeypatch
) -> None:
    policy_pack_path = tmp_path / "config" / "project" / "policy_pack.json"
    _write_json(
        policy_pack_path,
        {
            "governance": {
                "policy_index_contract": {
                    "required_tokens": ["docs/policies/LOCAL_POLICY.md"]
                },
                "contracts": {},
            }
        },
    )
    index_path = tmp_path / "docs" / "policies" / "INDEX.md"
    _write_text(index_path, "config/project/policy_pack.json\n")

    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack_path)
    monkeypatch.setattr(contracts, "POLICY_INDEX_PATH", index_path)

    issues = contracts._validate_policy_index_sync()

    assert any("docs/policies/LOCAL_POLICY.md" in issue.message for issue in issues)


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
    rel = "docs/WORKFLOW_CODEX.md"
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
    rel = "docs/WORKFLOW_CODEX.md"
    workflow_doc = tmp_path / rel
    workflow_doc.parent.mkdir(parents=True, exist_ok=True)
    workflow_doc.write_text("workflow", encoding="utf-8")

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "_git_tracked_paths", lambda issues: {rel})

    issues = contracts._validate_required_paths(
        {"required_paths": {"root_docs": [rel]}}
    )

    assert issues == []


def _write_minimal_cpp_safety_policy(root: Path) -> None:
    _write_text(
        root / "docs" / "governance" / "cpp_safety_policy.md",
        "\n".join(
            [
                "# C++ Safety Policy",
                "Python remains the semantic oracle.",
                "Use RAII.",
                "No raw owning pointers.",
                "No naked new or delete.",
                "Document the GDExtension boundary.",
                "Require parity evidence.",
                "Update the authority map.",
            ]
        ),
    )


def _write_minimal_native_tooling_governance(root: Path) -> None:
    _write_text(
        root / "tools" / "governance" / "validate_native_cpp_tooling.py",
        "def main():\n    return 0\n",
    )
    _write_text(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_native_cpp_tooling\n",
    )


def test_native_cpp_safety_governance_requires_style_files(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any(".clang-format" in issue.message for issue in issues)
    assert any(".clang-tidy" in issue.message for issue in issues)


def test_native_cpp_safety_governance_rejects_warnings_as_errors_star(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*\nWarningsAsErrors: '*'\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any("WarningsAsErrors" in issue.message for issue in issues)


def test_native_cpp_safety_governance_requires_tooling_validator(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*, cppcoreguidelines-*\nWarningsAsErrors: ''\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_native_cpp_safety_governance()

    assert any("validate_native_cpp_tooling.py" in issue.message for issue in issues)


def test_native_cpp_safety_governance_accepts_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp", "")
    _write_text(
        tmp_path / "native" / "AGENTS.md",
        "See docs/governance/cpp_safety_policy.md\n",
    )
    _write_minimal_cpp_safety_policy(tmp_path)
    _write_minimal_native_tooling_governance(tmp_path)
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(
        tmp_path / ".clang-tidy",
        "Checks: clang-analyzer-*, cppcoreguidelines-*\nWarningsAsErrors: ''\n",
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_native_cpp_safety_governance() == []


def test_governance_directives_include_staged_migration_contract() -> None:
    payload = json.loads(contracts.POLICY_PACK_PATH.read_text(encoding="utf-8"))
    directives = payload["governance"]["contributor_directives"]["directives"]
    directive_ids = {item["id"] for item in directives}
    assert {
        "staged_migration_honesty",
        "additive_migration_first",
        "delta_report_required",
    }.issubset(directive_ids)


def test_workflow_codex_rule_requires_control_contract_tokens() -> None:
    manifest = contracts._load_manifest()
    rules = manifest["content_rules"]
    workflow_rule = next(
        rule for rule in rules if rule["file"] == "docs/WORKFLOW_CODEX.md"
    )
    must_contain = set(workflow_rule["must_contain"])
    assert "Workflow authority" in must_contain
    assert "config/project/policy_pack.json" in must_contain
    assert "Authority files must be tracked in Git" in must_contain
    assert "## Context-switch profiles" in must_contain
    assert "## Boundary model" in must_contain
    assert "CODEX_MODE=1 ./scripts/verify.sh" in must_contain


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
    assert "## Known Watchouts" in must_contain
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
                    "setup_control_types": ["toggle", "selector", "slider", "stepper"],
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
                    "setup_control_types": ["toggle", "selector", "slider", "stepper"],
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
                "reference_checks": [],
            }
        },
    )

    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(contracts, "POLICY_PACK_PATH", policy_pack)

    issues = contracts._validate_deprecated_authorities()

    assert issues
    assert any("deprecated authority path present" in issue.message for issue in issues)
