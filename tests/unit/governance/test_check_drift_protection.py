from __future__ import annotations

import json
from pathlib import Path

import tools.governance.check_drift_protection as drift


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "manifest_id": "drift_protection",
        "hotspot_scan": {"roots": ["src", "cli"], "top_n": 2},
        "thin_wrapper_budgets": [
            {
                "path": "cli/front.py",
                "max_real_loc": 10,
                "role": "compatibility launcher wrapper",
            }
        ],
        "tutorial_copy_contract": {
            "lessons_path": "config/tutorial/lessons.json",
            "overlay_path": "src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py",
            "forbidden_prefixes": ["Goal:", "Action:"],
            "required_overlay_tokens": ["Do this:", "Tip:", "USE:"],
        },
    }


def test_drift_protection_passes_with_compliant_repo(monkeypatch, tmp_path: Path) -> None:
    _write(tmp_path / "cli/front.py", "def main():\n    return 1\n")
    _write(tmp_path / "src/a.py", "def a():\n    return 1\n")
    _write(
        tmp_path / "config/tutorial/lessons.json",
        json.dumps(
            {
                "lessons": [
                    {
                        "lesson_id": "4d_core",
                        "steps": [
                            {
                                "id": "move",
                                "ui": {"text": "Do this: move the piece", "hint": "Tip: use the prompt"}
                            }
                        ],
                    }
                ]
            }
        ),
    )
    _write(
        tmp_path / "src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py",
        'LABELS = ["Do this:", "Tip:", "USE:"]\n',
    )
    manifest_path = tmp_path / "config/project/policy/manifests/drift_protection.json"
    _write(manifest_path, json.dumps(_manifest(), indent=2))

    monkeypatch.setattr(drift, "ROOT", tmp_path)
    monkeypatch.setattr(drift, "MANIFEST_PATH", manifest_path)

    assert drift.evaluate_drift_protection() == []


def test_drift_protection_reports_budget_and_tutorial_copy_drift(monkeypatch, tmp_path: Path) -> None:
    _write(tmp_path / "cli/front.py", "def main():\n    value = 1\n    other = 2\n    third = 3\n    fourth = 4\n    return value + other + third + fourth\n")
    _write(tmp_path / "src/a.py", "def a():\n    return 1\n")
    _write(
        tmp_path / "config/tutorial/lessons.json",
        json.dumps(
            {
                "lessons": [
                    {
                        "lesson_id": "4d_core",
                        "steps": [
                            {
                                "id": "move",
                                "ui": {"text": "Goal: move the piece", "hint": "Action: use the prompt"}
                            }
                        ],
                    }
                ]
            }
        ),
    )
    _write(
        tmp_path / "src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py",
        'LABELS = ["Do this:", "USE:"]\n',
    )
    manifest = _manifest()
    manifest["thin_wrapper_budgets"][0]["max_real_loc"] = 3
    manifest_path = tmp_path / "config/project/policy/manifests/drift_protection.json"
    _write(manifest_path, json.dumps(manifest, indent=2))

    monkeypatch.setattr(drift, "ROOT", tmp_path)
    monkeypatch.setattr(drift, "MANIFEST_PATH", manifest_path)

    messages = [issue.message for issue in drift.evaluate_drift_protection()]
    assert any("exceeds drift budget" in message for message in messages)
    assert any("forbidden prefix 'Goal:'" in message or 'forbidden prefix "Goal:"' in message for message in messages)
    assert any("forbidden prefix 'Action:'" in message or 'forbidden prefix "Action:"' in message for message in messages)
    assert any("missing required tutorial overlay token: Tip:" in message for message in messages)
