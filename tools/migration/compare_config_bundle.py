from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.migration.export_config_bundle import check_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare a checked-in migration config bundle with regenerated output."
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    return check_bundle(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
