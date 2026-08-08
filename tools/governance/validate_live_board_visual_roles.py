"""Targeted drift protection for live-board semantic colour consumers."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VISUALS = ROOT / "godot/Tet4D.Godot/scripts/ui/replay_visuals.gd"
GRID = ROOT / "godot/Tet4D.Godot/scripts/rendering/grid_renderer.gd"
CAMERA = ROOT / "godot/Tet4D.Godot/scripts/rendering/camera_rig.gd"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _visual_role_issues(visuals: str) -> list[str]:
    issues: list[str] = []
    required_visual_tokens = (
        "ROLE_BOARD_GRID := ROLE_LIVE_BOARD_GRID",
        "ROLE_BOARD_WIREFRAME := ROLE_BOARD_OUTLINE",
        'ROLE_BOARD_FRAME_ACTIVE := "board_frame_active"',
        "ROLE_CELL_GHOST_FILL := ROLE_GHOST_CELL",
        "ROLE_AXIS_W := ShellStyleRolesScript.AXIS_W",
        "ROLE_BOARD_OUTLINE: manager.get_color(ShellStyleRolesScript.GRID_MINOR)",
        "ROLE_LIVE_BOARD_GRID: manager.get_color(ShellStyleRolesScript.GRID_MAJOR)",
    )
    for token in required_visual_tokens:
        if token not in visuals:
            issues.append(f"replay_visuals missing governed live-board role: {token}")
    return issues


def _grid_issues(grid: str) -> list[str]:
    issues: list[str] = []
    for token in (
        "ReplayVisuals.live_board_grid_material",
        "ReplayVisuals.board_outline_material",
        "ReplayVisuals.board_active_frame_material",
    ):
        if token not in grid:
            issues.append(
                f"grid_renderer must consume shared semantic role via {token}"
            )
    return issues


def _camera_issues(camera: str) -> list[str]:
    issues: list[str] = []
    if "ReplayVisuals.axis_color(label_text)" not in camera:
        issues.append(
            "camera orientation gizmo must resolve axis colour from ReplayVisuals.axis_color"
        )
    if '_add_gizmo_axis("Slice"' in camera or '_update_gizmo_axis("Slice"' in camera:
        issues.append("camera orientation gizmo must never render the slice axis")
    return issues


def _local_colour_literal_issues(grid: str, camera: str) -> list[str]:
    issues: list[str] = []
    for path, text in ((GRID, grid), (CAMERA, camera)):
        for line_number, line in enumerate(text.splitlines(), 1):
            if "Color(" not in line:
                continue
            if (
                path == CAMERA
                and "AxisOrigin" not in line
                and 'Color("d8dde3")' in line
            ):
                continue
            if path == GRID:
                issues.append(
                    f"{path.relative_to(ROOT)}:{line_number}: local colour literal in governed grid consumer"
                )
    return issues


def main() -> int:
    issues: list[str] = []
    visuals = _read(VISUALS)
    grid = _read(GRID)
    camera = _read(CAMERA)
    issues.extend(_visual_role_issues(visuals))
    issues.extend(_grid_issues(grid))
    issues.extend(_camera_issues(camera))
    issues.extend(_local_colour_literal_issues(grid, camera))

    if issues:
        print("Live-board visual-role validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Live-board visual-role validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
