"""Standalone entry point for the topology explorer playground."""
from __future__ import annotations

import sys

from tet4d.ui.pygame.topology_lab.entrypoint import (
    parse_topology_playground_dimension,
    run_direct_topology_playground,
)


def _parse_dimension(argv: list[str]) -> int:
    if len(argv) <= 1:
        return 2
    return parse_topology_playground_dimension(argv[1]) or 2


def main() -> None:
    dimension = _parse_dimension(sys.argv)
    run_direct_topology_playground(dimension)


if __name__ == "__main__":
    main()
