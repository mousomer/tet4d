from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_PATH = REPO_ROOT / "config/project/policy/governance.json"
CODE_RULES_PATH = REPO_ROOT / "config/project/policy/code_rules.json"


def load_json_object(path: Path, rel: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing required file: {rel}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {rel}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{rel} must be a JSON object")
    return payload


def as_str_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be list[str]")
    return value


def iter_python_files(root: Path, *, roots: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for base in roots:
        base_path = root / base
        if not base_path.exists():
            continue
        for path in base_path.rglob("*.py"):
            out.append(path.relative_to(root).as_posix())
    return sorted(out)


def load_optional_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must be a JSON object")
    return payload


def load_unified_governance(root: Path | None = None) -> dict[str, Any] | None:
    target = (root or REPO_ROOT) / "config/project/policy/governance.json"
    return load_optional_json_object(target)


def load_unified_code_rules(root: Path | None = None) -> dict[str, Any] | None:
    target = (root or REPO_ROOT) / "config/project/policy/code_rules.json"
    return load_optional_json_object(target)
