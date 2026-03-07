# ruff: noqa: E402
import argparse
import sys
from pathlib import Path


def _parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="tet4d 2D launcher",
    )
    return parser.parse_known_args(argv)[0]


def main(argv=None):
    _parse_cli_args(sys.argv[1:] if argv is None else argv)
    from tet4d.ui.pygame.front2d_game import run

    run()


if __name__ == "__main__":
    main()