"""Bounded secret-pattern checks over Git-visible text; semantic review remains required."""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import stat
import subprocess
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_FINDINGS = 50
PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("openai-token", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b")),
)


def read_text(root_fd: int, relative: Path) -> tuple[str, str | None]:
    if relative.is_absolute() or ".." in relative.parts:
        return "", "unreadable-text"
    try:
        with ExitStack() as stack:
            parent = root_fd
            for component in relative.parts[:-1]:
                parent = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=parent,
                )
                stack.callback(os.close, parent)
            mode = os.stat(relative.name, dir_fd=parent, follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                return "", "symlink"
            if not stat.S_ISREG(mode):
                return "", "non-regular"
            fd = os.open(
                relative.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=parent,
            )
            stack.callback(os.close, fd)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                return "", "non-regular"
            with os.fdopen(fd, "rb", closefd=False) as stream:
                data = stream.read(MAX_BYTES + 1)
        return classify_bytes(data)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            return "", "symlink"
        return "", "unreadable-text"


def classify_bytes(data: bytes) -> tuple[str, str | None]:
    if len(data) > MAX_BYTES:
        return "", "size-bound"
    if b"\0" in data:
        return "", "binary"
    try:
        return data.decode("utf-8"), None
    except UnicodeError:
        return "", "binary-or-encoding"


def bounded_append(collection: list, item: dict) -> None:
    if len(collection) < MAX_FINDINGS:
        collection.append(item)


def scan(root: Path) -> dict:
    root = root.resolve()
    listed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        capture_output=True,
        check=False,
        timeout=30,
    )
    if listed.returncode:
        raise ValueError("secret scan requires an observable Git checkout")
    findings, skipped, errors = [], [], []
    inspected = 0
    finding_count = 0
    skipped_count = 0
    error_count = 0
    reasons = Counter()
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for raw in sorted(set(listed.stdout.split(b"\0")) - {b""}):
            relative = Path(os.fsdecode(raw))
            content, reason = read_text(root_fd, relative)
            if reason is not None:
                reasons[reason] += 1
                collection = errors if reason == "unreadable-text" else skipped
                error_count += int(reason == "unreadable-text")
                skipped_count += int(reason != "unreadable-text")
                bounded_append(collection, {"reason": reason})
                continue
            inspected += 1
            for pattern_id, pattern in PATTERNS:
                for match in pattern.finditer(content):
                    finding_count += 1
                    bounded_append(
                        findings,
                        {
                            "pattern_id": pattern_id,
                            "line": content.count("\n", 0, match.start()) + 1,
                        },
                    )
    finally:
        os.close(root_fd)
    return {
        "schema_version": 2,
        "execution": "completed",
        "coverage_counts": dict(reasons),
        "profile": "git-visible-text-patterns-v1",
        "inspected_files": inspected,
        "findings": findings[:MAX_FINDINGS],
        "finding_count": finding_count,
        "skipped": skipped[:MAX_FINDINGS],
        "skipped_count": skipped_count,
        "errors": errors[:MAX_FINDINGS],
        "error_count": error_count,
        "limits": "Known patterns only; binary, symlink and oversized files require other evidence. Ignored files and Git history are outside this check.",
    }


def main() -> int:
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "Invalid scanner arguments.\n")

    parser = SafeParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = scan(args.root)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        print(
            json.dumps(
                {
                    "schema_version": 2,
                    "execution": "failed",
                    "reason": "Git-visible inputs could not be inspected",
                }
            )
        )
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 1 if result["finding_count"] else 2 if result["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
