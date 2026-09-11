from __future__ import annotations

import argparse
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

if __package__ in {None, ""}:
    root_hint = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root_hint))

from tools.workspace_governance.resolver.core import GovernanceError, GovernanceResolver
from tools.workspace_governance.validators.core import (
    doctor,
    load_manifest_json,
    pack_hash,
)


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
    if not lock_path.is_file():
        raise ValueError(f"pack lock does not exist: {lock_rel}")
    existing = load_manifest_json(lock_path)
    pack_rel = existing["pack_path"]
    pack_root = root / pack_rel
    if not pack_root.is_dir():
        raise ValueError(f"locked pack path does not exist: {pack_rel}")
    manifest = load_manifest_json(pack_root / "MANIFEST.json")
    digest, files = pack_hash(pack_root)
    version = (pack_root / manifest["version_file"]).read_text(encoding="utf-8").strip()
    lock = {
        "schema_version": 1,
        "pack_path": pack_rel,
        "pack_name": manifest["name"],
        "version": version,
        "revision": manifest["revision"],
        "content_sha256": digest,
        "files": files,
        "lock_algorithm": manifest["lock_algorithm"],
    }
    lock_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return lock


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in raw_argv
    raw_argv = [item for item in raw_argv if item != "--json"]
    parser = argparse.ArgumentParser(prog="gov")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit JSON (accepted before or after the subcommand)",
    )
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
    args = parser.parse_args(raw_argv)
    args.json = as_json or args.json
    root = args.root.resolve()
    try:
        resolver = GovernanceResolver.for_root(root)
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
            if args.query is None and args.task is None:
                explain.print_usage(sys.stderr)
                return 2
            _emit(resolver.explain(args.query, task=args.task), as_json=args.json)
            return 0
        if args.command == "sync":
            _emit(_sync(root, resolver), as_json=args.json)
            return 0
        _, project, _ = resolver.load()
        local, local_tiers = resolver.local_overlay()
        result, issues = doctor(
            root, project, local, route=args.route, local_tiers=local_tiers
        )
        if args.print_interpreter and not issues:
            print(result["interpreter"])
        elif args.print_interpreter:
            with redirect_stdout(sys.stderr):
                _emit([item.to_dict() for item in issues], as_json=False)
        else:
            payload = {**result, "diagnostics": [item.to_dict() for item in issues]}
            _emit(payload, as_json=args.json)
        return 1 if issues else 0
    except (
        GovernanceError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        StopIteration,
        ImportError,
    ) as exc:
        diagnostics = exc.diagnostics if isinstance(exc, GovernanceError) else []
        if diagnostics:
            _emit([item.to_dict() for item in diagnostics], as_json=args.json)
        else:
            payload = {
                "status": "ENVIRONMENT_INVALID"
                if args.command == "doctor"
                else "invalid",
                "diagnostics": [
                    {
                        "code": "ENVIRONMENT_MISMATCH"
                        if isinstance(exc, ImportError) or args.command == "doctor"
                        else "BROKEN_REFERENCE",
                        "fact": args.command,
                        "owner": "environment"
                        if args.command == "doctor"
                        else "project",
                        "sources": [],
                        "reason": str(exc),
                        "repair": "repair the referenced metadata or dependency",
                    }
                ],
            }
            with redirect_stdout(
                sys.stderr if getattr(args, "print_interpreter", False) else sys.stdout
            ):
                _emit(payload, as_json=args.json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
