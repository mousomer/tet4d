"""Dependency-light startup; deliberately compatible with pre-tomllib Python."""

import json
import re
import runpy
import sys
from pathlib import Path


def main(check_only=False):
    root = Path(__file__).resolve().parents[3]
    try:
        # Read only the existing project's lower bound before importing modern code.
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
        project = re.search(r"(?ms)^\[project\]\s*$(.*?)(?=^\[|\Z)", text)
        requirement = (
            re.search(r'requires-python\s*=\s*["\']([^"\']+)', project.group(1))
            if project
            else None
        )
        floor = (
            re.search(r">=\s*(\d+(?:\.\d+)*)", requirement.group(1))
            if requirement
            else None
        )
        if floor is None:
            raise ValueError(
                "Cannot read project.requires-python lower bound for bootstrap"
            )
        if sys.version_info[:3] < tuple(int(n) for n in floor.group(1).split(".")):
            raise ValueError(
                "Bootstrap Python does not satisfy " + requirement.group(1)
            )
        if check_only:
            return 0
        sys.path.insert(0, str(root))
        runpy.run_module("tools.workspace_governance.cli.gov", run_name="__main__")
    except (ImportError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "ENVIRONMENT_INVALID",
                    "diagnostics": [
                        {
                            "code": "ENVIRONMENT_MISMATCH",
                            "fact": "bootstrap.interpreter",
                            "owner": "environment",
                            "sources": ["pyproject.toml"],
                            "reason": str(exc),
                            "repair": "Select a supported interpreter using the launcher bootstrap override",
                        }
                    ],
                }
            ),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
