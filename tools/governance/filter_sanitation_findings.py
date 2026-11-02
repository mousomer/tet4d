"""Filter only exact, reviewed advisory path references; retain all other matches."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

REFERENCE_REGISTER = Path("config/project/policy/manifests/sanitation_references.json")
WARNING_CLASSES = {"absolute-unix", "absolute-windows", "parent-traversal"}


def reviewed_references(
    repository: Path, warning_class: str
) -> Counter[tuple[str, str]]:
    """Return exact file/content identities, never patterns or whole-file grants."""
    register = repository / REFERENCE_REGISTER
    if not register.is_file():
        return Counter()
    data = json.loads(register.read_text(encoding="utf-8"))
    if set(data) != {"schema_version", "references"} or data["schema_version"] != 1:
        raise ValueError("invalid sanitation reference register schema")
    result: Counter[tuple[str, str]] = Counter()
    for entry in data["references"]:
        if set(entry) != {"path", "warning_class", "line_sha256", "reason"}:
            raise ValueError("invalid sanitation reference fields")
        path = entry["path"]
        if (
            not isinstance(path, str)
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or not path
            or entry["warning_class"] not in WARNING_CLASSES
            or not isinstance(entry["reason"], str)
            or not entry["reason"].strip()
            or not isinstance(entry["line_sha256"], list)
            or not entry["line_sha256"]
        ):
            raise ValueError("invalid sanitation reference identity or reason")
        for digest in entry["line_sha256"]:
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("invalid sanitation reference digest")
            if entry["warning_class"] == warning_class:
                result[path, digest] += 1
    return result


def filter_findings(findings: str, references: Counter[tuple[str, str]]) -> str:
    """A new file or changed source line cannot inherit an existing exception."""
    retained = []
    remaining = references.copy()
    for finding in findings.splitlines():
        fields = finding.split(":", 2)
        if len(fields) != 3 or not fields[1].isdigit():
            retained.append(finding)
            continue
        path, _, source = fields
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        if remaining[path, digest] > 0:
            remaining[path, digest] -= 1
        else:
            retained.append(finding)
    return "\n".join(retained)


def main() -> int:
    repository, warning_class = sys.argv[1:]
    if warning_class not in WARNING_CLASSES:
        raise ValueError("unknown sanitation warning class")
    references = reviewed_references(Path(repository), warning_class)
    retained = filter_findings(sys.stdin.read(), references)
    if retained:
        print(retained)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
