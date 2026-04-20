from __future__ import annotations

import json
from pathlib import Path

import tools.governance.check_policy_runtime_rules as runtime_rules


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    _write(path, json.dumps(payload, indent=2))


def _seed_authoritative_sources(root: Path) -> None:
    _write_json(root / "config/project/constants.json", {"version": 1})
    _write_json(root / "config/gameplay/tuning.json", {"version": 1})
    _write_json(root / "config/menu/defaults.json", {"version": 1})


def _code_rules_payload() -> dict[str, object]:
    return {
        "sanitation": {"entrypoints": []},
        "magic_numbers": {"entrypoints": []},
        "config_backed_runtime_constants": {
            "authoritative_sources": [
                {"path": "config/project/constants.json"},
                {"path": "config/gameplay/tuning.json"},
                {"path": "config/menu/defaults.json"},
            ],
            "source_roots": ["src/tet4d", "cli"],
            "exclude_globs": ["tests/**", "**/test_*.py", "**/*_test.py"],
            "target_module_globs": [
                "src/tet4d/engine/runtime/leaderboard.py",
                "src/tet4d/engine/tutorial/runtime.py",
                "src/tet4d/ui/pygame/front2d_loop.py",
                "src/tet4d/ui/pygame/launch/leaderboard_menu.py",
                "src/tet4d/ui/pygame/projection3d.py",
                "src/tet4d/ui/pygame/render/gfx_game.py",
                "src/tet4d/ui/pygame/render/projected_occlusion.py",
                "src/tet4d/ui/pygame/render/text_render_cache.py",
                "src/tet4d/ui/pygame/runtime_ui/tutorial_loop_common.py",
                "src/tet4d/ui/pygame/ui_utils.py",
            ],
            "allowed_loader_modules": [
                "tet4d.engine.runtime.project_config",
                "tet4d.engine.runtime.runtime_config",
                "tet4d.engine.runtime.menu_config",
            ],
            "allowed_loader_symbols": [
                "constants_payload",
                "default_settings_payload",
                "gameplay_tuning_payload",
                "project_constant_color",
                "project_constant_float",
                "project_constant_int",
            ],
            "enforcement": {
                "module_level_assignments_only": True,
                "name_patterns": {
                    "constant_like": r"^_?[A-Z][A-Z0-9_]*$",
                    "runtime_owned": (
                        r"(?:DEFAULT|THRESH|LIMIT|CACHE|MARGIN|PADDING|WIDTH|HEIGHT|"
                        r"GAP|LAYOUT|ANIMATION|DURATION|DELAY|TIMING|TIMEOUT|SPEED|"
                        r"SCORE|TUNING|ROWS|ENTRIES|PAGE|PANEL|CELL|LAYER|RADIUS|"
                        r"SIZE|ALPHA|FPS|COUNT|MAX|MIN)"
                    ),
                },
                "selected_file_bans": [
                    {
                        "path": "src/tet4d/engine/runtime/leaderboard.py",
                        "name_regex": r"^_DEFAULT_MAX_ENTRIES$",
                        "message": (
                            "leaderboard max entries must come from "
                            "config/project/constants.json via project_constant_int"
                        ),
                    }
                ],
            },
            "exception_categories": {
                "third_party_constants_enums": {
                    "allowed_import_roots": ["pygame", "enum", "pathlib"]
                },
                "schema_versions": {
                    "allowed_name_regexes": [r"^_?SCHEMA_VERSION$", r"^_?VERSION$"],
                    "allowed_module_globs": ["src/tet4d/**/schema*.py"],
                },
                "protocol_dunder": {
                    "allowed_name_regexes": [r"^__.*__$", r"^__all__$"]
                },
                "sentinels": {
                    "allowed_name_regexes": [
                        r"^_?[A-Z0-9_]*(MISSING|UNSET|SENTINEL|UNKNOWN)[A-Z0-9_]*$"
                    ]
                },
                "tests": {
                    "path_globs": [
                        "tests/**",
                        "**/test_*.py",
                        "**/*_test.py",
                        "**/conftest.py",
                    ]
                },
                "allowed_invariant_name_regex": [r"^_?EPSILON$"],
                "allowed_invariant_module_globs": [],
            },
        },
    }


def test_rejects_hardcoded_runtime_constant_without_loader_import(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_authoritative_sources(tmp_path)
    _write(tmp_path / "src/tet4d/engine/runtime/leaderboard.py", "MARGIN = 24\n")

    monkeypatch.setattr(runtime_rules, "ROOT", tmp_path)

    issues, warnings = runtime_rules.evaluate_runtime_rules(_code_rules_payload())

    assert warnings == []
    messages = [issue.message for issue in issues]
    assert any("repo-owned runtime constant 'MARGIN'" in message for message in messages)


def test_accepts_value_loaded_through_approved_config_path(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_authoritative_sources(tmp_path)
    _write(
        tmp_path / "src/tet4d/engine/runtime/leaderboard.py",
        (
            "from tet4d.engine.runtime.project_config import project_constant_int\n"
            "MARGIN = project_constant_int((\"rendering\", \"3d\", \"margin\"), 20)\n"
        ),
    )

    monkeypatch.setattr(runtime_rules, "ROOT", tmp_path)

    issues, warnings = runtime_rules.evaluate_runtime_rules(_code_rules_payload())

    assert issues == []
    assert warnings == []


def test_accepts_imported_third_party_api_constants(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_authoritative_sources(tmp_path)
    _write(
        tmp_path / "src/tet4d/engine/runtime/leaderboard.py",
        "from pygame import K_SPACE as SPACE_KEY\n__all__ = [\"SPACE_KEY\"]\n",
    )

    monkeypatch.setattr(runtime_rules, "ROOT", tmp_path)

    issues, warnings = runtime_rules.evaluate_runtime_rules(_code_rules_payload())

    assert issues == []
    assert warnings == []


def test_accepts_explicit_exception_categories(monkeypatch, tmp_path: Path) -> None:
    _seed_authoritative_sources(tmp_path)
    _write(
        tmp_path / "src/tet4d/engine/runtime/leaderboard.py",
        "_SCHEMA_VERSION = 1\n_MISSING = \"missing\"\n",
    )

    monkeypatch.setattr(runtime_rules, "ROOT", tmp_path)

    issues, warnings = runtime_rules.evaluate_runtime_rules(_code_rules_payload())

    assert issues == []
    assert warnings == []


def test_rejects_selected_file_duplication_when_config_authority_exists(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_authoritative_sources(tmp_path)
    _write(
        tmp_path / "src/tet4d/engine/runtime/leaderboard.py",
        "_DEFAULT_MAX_ENTRIES = 10\n",
    )

    monkeypatch.setattr(runtime_rules, "ROOT", tmp_path)

    issues, _warnings = runtime_rules.evaluate_runtime_rules(_code_rules_payload())

    assert any(
        "leaderboard max entries must come from config/project/constants.json"
        in issue.message
        for issue in issues
    )


def test_invalid_policy_rule_shape_reports_schema_issue(
    monkeypatch, tmp_path: Path
) -> None:
    _seed_authoritative_sources(tmp_path)
    _write(tmp_path / "src/tet4d/engine/runtime/leaderboard.py", "MARGIN = 24\n")
    bad_payload = _code_rules_payload()
    bad_payload["config_backed_runtime_constants"] = {
        "authoritative_sources": [{"path": "config/project/constants.json"}],
        "source_roots": "src/tet4d",
    }

    monkeypatch.setattr(runtime_rules, "ROOT", tmp_path)

    issues, warnings = runtime_rules.evaluate_runtime_rules(bad_payload)

    assert warnings == []
    assert any(
        issue.kind == "schema"
        and "config_backed_runtime_constants.source_roots must be list[str]"
        in issue.message
        for issue in issues
    )
