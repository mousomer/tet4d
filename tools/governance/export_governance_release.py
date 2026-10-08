"""Compatibility entrypoint for the portable release exporter."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.workspace_governance.release import BASELINE_FILES, export_release, main

__all__ = ["BASELINE_FILES", "export_release"]


if __name__ == "__main__":
    raise SystemExit(main())
