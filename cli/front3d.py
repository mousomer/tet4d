# ruff: noqa: E402
import argparse
import sys
from pathlib import Path


def _parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="tet4d 3D launcher",
    )
    return parser.parse_known_args(argv)[0]


def main(argv=None):
    _parse_cli_args(sys.argv[1:] if argv is None else argv)
    from tet4d.engine import api as engine_api

    engine_api.run_front3d_ui()


if __name__ == "__main__":
    main()
