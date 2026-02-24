from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from tet4d.engine.menu_graph_linter import lint_menu_graph

    issues = lint_menu_graph()
    if issues:
        print("Menu graph lint failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    print("Menu graph lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
