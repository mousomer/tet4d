from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PACK_REL = "config/project/policy_pack.json"
POLICY_PACK_PATH = REPO_ROOT / POLICY_PACK_REL


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


def load_policy_pack(root: Path | None = None) -> dict[str, Any] | None:
    target = (root or REPO_ROOT) / POLICY_PACK_REL
    return load_optional_json_object(target)


def _load_policy_section(root: Path | None, section: str) -> dict[str, Any] | None:
    payload = load_policy_pack(root)
    if not isinstance(payload, dict):
        return None
    section_payload = payload.get(section)
    return section_payload if isinstance(section_payload, dict) else None


def load_unified_governance(root: Path | None = None) -> dict[str, Any] | None:
    return _load_policy_section(root, "governance")


def load_unified_code_rules(root: Path | None = None) -> dict[str, Any] | None:
    return _load_policy_section(root, "code_rules")


def load_maintenance_contract(root: Path | None = None) -> dict[str, Any] | None:
    return _load_policy_section(root, "maintenance_contract")


def load_maintenance_docs(root: Path | None = None) -> dict[str, Any] | None:
    return _load_policy_section(root, "maintenance_docs")


def load_deprecated_authorities(root: Path | None = None) -> dict[str, Any] | None:
    return _load_policy_section(root, "deprecated_authorities")
