from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    root_hint = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root_hint))

from tools.workspace_governance.resolver.core import GovernanceError, GovernanceResolver
from tools.workspace_governance.validators.core import doctor, pack_hash


def _emit(value: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                print(f"{item['code']}: {item['fact']}")
                print(f"  owner: {item['owner']}")
                print(f"  sources: {', '.join(item['sources'])}")
                print(f"  reason: {item['reason']}")
                print(f"  repair: {item['repair']}")
            else:
                print(item)
        return
    print(json.dumps(value, indent=2, sort_keys=True))


def _sync(root: Path, resolver: GovernanceResolver) -> dict[str, object]:
    workspace, _, _ = resolver.load()
    lock_rel = workspace["governance_pack"]["lock"]
    lock_path = root / lock_rel
    existing = (
        json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {}
    )
    pack_rel = existing.get("pack_path", "tools/workspace_governance")
    digest, files = pack_hash(root / pack_rel)
    version = (root / pack_rel / "VERSION").read_text(encoding="utf-8").strip()
    lock = {
        "schema_version": 1,
        "pack_path": pack_rel,
        "version": version,
        "revision": existing.get("revision", "vendored-v0.1"),
        "content_sha256": digest,
        "files": files,
    }
    lock_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return lock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gov")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("resolve").add_argument(
        "--mode", choices=("LOCAL_FIX", "FEATURE", "STRUCTURAL_CHANGE")
    )
    explain = sub.add_parser("explain")
    explain.add_argument("query", nargs="?")
    explain.add_argument("--task")
    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument("--print-interpreter", action="store_true")
    doctor_parser.add_argument("--route")
    sub.add_parser("sync")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    resolver = GovernanceResolver.for_root(root)
    try:
        if args.command == "check":
            issues = resolver.check()
            _emit(
                [item.to_dict() for item in issues] if issues else {"status": "ok"},
                as_json=args.json,
            )
            return 1 if issues else 0
        if args.command == "resolve":
            _emit(resolver.resolve(mode=args.mode), as_json=args.json)
            return 0
        if args.command == "explain":
            _emit(resolver.explain(args.query, task=args.task), as_json=args.json)
            return 0
        if args.command == "sync":
            _emit(_sync(root, resolver), as_json=args.json)
            return 0
        _, project, local = resolver.load()
        result, issues = doctor(root, project, local, route=args.route)
        if args.print_interpreter and not issues:
            print(result["interpreter"])
        elif args.print_interpreter:
            _emit([item.to_dict() for item in issues], as_json=False)
        else:
            payload = {**result, "diagnostics": [item.to_dict() for item in issues]}
            _emit(payload, as_json=args.json)
        return 1 if issues else 0
    except (GovernanceError, OSError, ValueError, json.JSONDecodeError) as exc:
        diagnostics = exc.diagnostics if isinstance(exc, GovernanceError) else []
        if diagnostics:
            _emit([item.to_dict() for item in diagnostics], as_json=args.json)
        else:
            _emit({"status": "invalid", "reason": str(exc)}, as_json=args.json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
