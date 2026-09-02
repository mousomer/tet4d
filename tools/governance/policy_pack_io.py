from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PACK_REL = "config/project/policy_pack.json"
POLICY_PACK_PATH = REPO_ROOT / POLICY_PACK_REL


class PolicyPackError(ValueError):
    """Raised when the policy pack cannot be loaded without ambiguity."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PolicyPackError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_policy_pack(path: Path = POLICY_PACK_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except FileNotFoundError as exc:
        raise PolicyPackError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyPackError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PolicyPackError(f"{path} must be a JSON object")
    return payload


def _compact_json(value: Any, level: int = 0) -> str:
    """Render the stable compact policy format without uncontrolled minification."""
    indent = "  " * level
    child_indent = "  " * (level + 1)
    if isinstance(value, dict):
        encoded = json.dumps(value, ensure_ascii=False)
        if all(not isinstance(item, (dict, list)) for item in value.values()):
            return encoded
        lines = ["{"]
        items = list(value.items())
        for index, (key, nested) in enumerate(items):
            rendered = _compact_json(nested, level + 1).splitlines()
            lines.append(f"{child_indent}{json.dumps(key)}: {rendered[0]}")
            lines.extend(rendered[1:])
            if index < len(items) - 1:
                lines[-1] += ","
        lines.append(f"{indent}}}")
        return "\n".join(lines)
    if isinstance(value, list):
        encoded = json.dumps(value, ensure_ascii=False)
        if not value or all(not isinstance(item, (dict, list)) for item in value):
            return encoded
        lines = ["["]
        for index, nested in enumerate(value):
            rendered = _compact_json(nested, level + 1).splitlines()
            lines.append(child_indent + rendered[0])
            lines.extend(rendered[1:])
            if index < len(value) - 1:
                lines[-1] += ","
        lines.append(f"{indent}]")
        return "\n".join(lines)
    return json.dumps(value, ensure_ascii=False)


def serialize_policy_pack(payload: dict[str, Any]) -> str:
    return _compact_json(payload) + "\n"


def write_policy_pack(payload: dict[str, Any], path: Path = POLICY_PACK_PATH) -> None:
    path.write_text(serialize_policy_pack(payload), encoding="utf-8")


def check_canonical_policy_pack(path: Path = POLICY_PACK_PATH) -> list[str]:
    try:
        actual = path.read_text(encoding="utf-8")
        expected = serialize_policy_pack(load_policy_pack(path))
    except (OSError, PolicyPackError) as exc:
        return [str(exc)]
    if actual != expected:
        return [
            (
                f"{path} is not in canonical compact format; "
                "run tools/governance/policy_pack_io.py --write"
            )
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canonicalize the policy pack")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--path", type=Path, default=POLICY_PACK_PATH)
    args = parser.parse_args(argv)

    if args.write:
        try:
            write_policy_pack(load_policy_pack(args.path), args.path)
        except (OSError, PolicyPackError) as exc:
            print(f"Policy-pack serialization failed: {exc}")
            return 1
        print(f"Wrote canonical policy pack: {args.path}")
        return 0

    issues = check_canonical_policy_pack(args.path)
    if issues:
        print("Canonical policy-pack validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    raw = args.path.read_bytes()
    print(
        f"Canonical policy pack passed: {len(raw.splitlines())} LOC, {len(raw)} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
