from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "project" / "secret_scan.json"


@dataclass(frozen=True)
class SecretPattern:
    pattern_id: str
    regex: re.Pattern[str]


@dataclass(frozen=True)
class AllowlistRule:
    path_glob: str
    pattern_ids: tuple[str, ...]
    contains: str | None


@dataclass(frozen=True)
class Finding:
    pattern_id: str
    rel_path: str
    line_no: int
    preview: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Failed reading {path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a top-level JSON object")
    return payload


def _string_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise SystemExit(f"{field} must be a list[str]")
    return list(value)


def _compile_patterns(payload: dict[str, Any]) -> list[SecretPattern]:
    raw_patterns = payload.get("patterns")
    if not isinstance(raw_patterns, list) or not raw_patterns:
        raise SystemExit("patterns must be a non-empty list")
    compiled: list[SecretPattern] = []
    for idx, entry in enumerate(raw_patterns, start=1):
        if not isinstance(entry, dict):
            raise SystemExit(f"patterns[{idx}] must be an object")
        pattern_id = entry.get("id")
        regex_text = entry.get("regex")
        if not isinstance(pattern_id, str) or not pattern_id.strip():
            raise SystemExit(f"patterns[{idx}].id must be a non-empty string")
        if not isinstance(regex_text, str) or not regex_text.strip():
            raise SystemExit(f"patterns[{idx}].regex must be a non-empty string")
        try:
            regex = re.compile(regex_text)
        except re.error as exc:
            raise SystemExit(
                f"Invalid regex for patterns[{idx}] ({pattern_id}): {exc}"
            ) from exc
        compiled.append(SecretPattern(pattern_id.strip(), regex))
    return compiled


def _compile_allowlist(payload: dict[str, Any]) -> list[AllowlistRule]:
    raw_rules = payload.get("allowlist", [])
    if not isinstance(raw_rules, list):
        raise SystemExit("allowlist must be a list")
    rules: list[AllowlistRule] = []
    for idx, entry in enumerate(raw_rules, start=1):
        if not isinstance(entry, dict):
            raise SystemExit(f"allowlist[{idx}] must be an object")
        path_glob = entry.get("path_glob", "*")
        if not isinstance(path_glob, str) or not path_glob:
            raise SystemExit(f"allowlist[{idx}].path_glob must be a non-empty string")
        raw_ids = entry.get("pattern_ids", [])
        if not isinstance(raw_ids, list) or any(
            not isinstance(item, str) for item in raw_ids
        ):
            raise SystemExit(f"allowlist[{idx}].pattern_ids must be a list[str]")
        contains = entry.get("contains")
        if contains is not None and (not isinstance(contains, str) or not contains):
            raise SystemExit(
                f"allowlist[{idx}].contains must be a non-empty string when set"
            )
        rules.append(
            AllowlistRule(
                path_glob=path_glob,
                pattern_ids=tuple(raw_ids),
                contains=contains,
            )
        )
    return rules


def _is_binary(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:2048]
    except OSError:
        return True
    return b"\0" in sample


def _iter_candidate_files(
    *,
    scan_roots: list[str],
    exclude_dirs: set[str],
    exclude_globs: list[str],
    max_file_bytes: int,
) -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    for root_rel in scan_roots:
        root = (PROJECT_ROOT / root_rel).resolve()
        project_root = PROJECT_ROOT.resolve()
        if root != project_root and project_root not in root.parents:
            continue
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            rel = _relative_path_in_project(path, project_root)
            if rel is None:
                continue
            if _should_skip_candidate(
                path,
                rel,
                exclude_dirs=exclude_dirs,
                exclude_globs=exclude_globs,
                max_file_bytes=max_file_bytes,
            ):
                continue
            candidates.append((rel, path))
    return candidates


def _relative_path_in_project(path: Path, project_root: Path) -> str | None:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return None


def _should_skip_candidate(
    path: Path,
    rel: str,
    *,
    exclude_dirs: set[str],
    exclude_globs: list[str],
    max_file_bytes: int,
) -> bool:
    parts = rel.split("/")
    if any(part in exclude_dirs for part in parts[:-1]):
        return True
    if any(fnmatch(rel, pattern) for pattern in exclude_globs):
        return True
    try:
        size = path.stat().st_size
    except OSError:
        return True
    if size > max_file_bytes:
        return True
    return _is_binary(path)


def _allowlisted(
    *,
    rel_path: str,
    pattern_id: str,
    token: str,
    rules: list[AllowlistRule],
) -> bool:
    for rule in rules:
        if not fnmatch(rel_path, rule.path_glob):
            continue
        if rule.pattern_ids and pattern_id not in rule.pattern_ids:
            continue
        if rule.contains is not None and rule.contains not in token:
            continue
        return True
    return False


def _token_preview(token: str) -> str:
    if len(token) <= 12:
        return token
    return token[:4] + "..." + token[-4:]


def run_scan() -> list[Finding]:
    payload = _load_json(CONFIG_PATH)
    scan_roots = _string_list(payload.get("scan_roots", ["."]), field="scan_roots")
    exclude_dirs = set(
        _string_list(payload.get("exclude_dirs", []), field="exclude_dirs")
    )
    exclude_globs = _string_list(
        payload.get("exclude_globs", []), field="exclude_globs"
    )
    max_file_bytes = payload.get("max_file_bytes", 1_048_576)
    if (
        isinstance(max_file_bytes, bool)
        or not isinstance(max_file_bytes, int)
        or max_file_bytes <= 0
    ):
        raise SystemExit("max_file_bytes must be a positive integer")

    patterns = _compile_patterns(payload)
    allowlist_rules = _compile_allowlist(payload)

    findings: list[Finding] = []
    for rel, path in _iter_candidate_files(
        scan_roots=scan_roots,
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        max_file_bytes=max_file_bytes,
    ):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        for pattern in patterns:
            for match in pattern.regex.finditer(text):
                token = match.group(0)
                if _allowlisted(
                    rel_path=rel,
                    pattern_id=pattern.pattern_id,
                    token=token,
                    rules=allowlist_rules,
                ):
                    continue
                line_no = text.count("\n", 0, match.start()) + 1
                findings.append(
                    Finding(
                        pattern_id=pattern.pattern_id,
                        rel_path=rel,
                        line_no=line_no,
                        preview=_token_preview(token),
                    )
                )
    return findings


def main() -> int:
    findings = run_scan()
    if not findings:
        print("Secret scan passed: no potential secret patterns detected.")
        return 0

    print("Secret scan failed: potential secret patterns detected.")
    for finding in findings:
        print(
            f"- [{finding.pattern_id}] {finding.rel_path}:{finding.line_no} "
            f"match={finding.preview!r}"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
