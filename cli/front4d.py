# ruff: noqa: E402
import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(1, str(_REPO_ROOT))


def _parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="tet4d 4D launcher",
    )
    return parser.parse_known_args(argv)[0]


def main(argv=None):
    _parse_cli_args(sys.argv[1:] if argv is None else argv)
    from tet4d.engine import api as engine_api

    engine_api.run_front4d_ui()


if __name__ == "__main__":
    main()
