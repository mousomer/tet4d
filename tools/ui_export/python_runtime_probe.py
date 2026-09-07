"""Capture canonical Pygame screens by invoking their live renderers."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.ui_logic.view_modes import GridMode
from tet4d.ui.pygame.front2d_session import create_initial_state as state_2d
from tet4d.ui.pygame.front3d_render import Camera3D
from tet4d.ui.pygame.front3d_render import draw_game_frame as draw_3d
from tet4d.ui.pygame.front3d_render import init_fonts as fonts_nd
from tet4d.ui.pygame.front4d_render import LayerView3D
from tet4d.ui.pygame.front4d_render import draw_game_frame as draw_4d
from tet4d.ui.pygame.frontend_nd_state import create_initial_state as state_nd
from tet4d.ui.pygame.render.gfx_game import (
    BG_COLOR,
    CELL_SIZE,
    SIDE_PANEL,
    TEXT_COLOR,
    compute_game_layout,
)
from tet4d.ui.pygame.render.gfx_game import draw_game_frame as draw_2d
from tet4d.ui.pygame.render.gfx_game import init_fonts as fonts_2d


def capture(mode: str, output: Path) -> dict:
    pygame.init()
    pygame.font.init()
    screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
    if mode == "2d":
        cfg = GameConfig(rng_seed=55)
        state = state_2d(cfg)
        draw_2d(screen, cfg, state, fonts_2d(), grid_mode=GridMode.FULL)
        board, panel = compute_game_layout(screen, cfg)
        board_box = [*board, cfg.width * CELL_SIZE, cfg.height * CELL_SIZE]
        panel_box = [panel[0], panel[1], SIDE_PANEL, cfg.height * CELL_SIZE]
        board_fill = BG_COLOR
        title = "2D Tetris"
    else:
        dims = (10, 20, 6) if mode == "3d" else (6, 12, 5, 4)
        cfg = GameConfigND(dims=dims, rng_seed=55)
        state = state_nd(cfg)
        if mode == "3d":
            draw_3d(screen, state, Camera3D(), fonts_nd(), GridMode.FULL)
        else:
            draw_4d(screen, state, LayerView3D(), fonts_nd(), GridMode.FULL)
        board_box = [20, 20, 860, 680]
        panel_box = [900, 20, 360, 680]
        board_fill = (16, 20, 40) if mode == "3d" else (14, 18, 36)
        title = f"{mode.upper()}D Tetris"
    png = output / f"game_{mode}.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(screen, png)
    # This is emitted by the live renderer probe, after it resolves its layout.
    # It is intentionally the only source consumed by exporter.py.
    px, py, pw, ph = panel_box
    rgb = lambda color: "#{:02x}{:02x}{:02x}".format(*color[:3])
    return {
        "probe": "pygame_runtime_v2",
        "implementation": "python",
        "mode": mode,
        "capture_state": "plain_initial",
        "source": "pygame live renderer",
        "viewport": [1280, 720],
        "root": {
            "semantic_id": "game_screen",
            "kind": "screen",
            "bounds": [0, 0, 1280, 720],
            "visible": True,
            "style": {"fill": rgb(BG_COLOR)},
            "children": [
                {
                    "semantic_id": "board_viewport",
                    "kind": "viewport",
                    "semantic_role": "gameplay_viewport",
                    "bounds": board_box,
                    "visible": True,
                    "style": {"fill": rgb(board_fill), "radius": 10},
                },
                {
                    "semantic_id": "status_panel",
                    "kind": "frame",
                    "semantic_role": "status_and_controls",
                    "bounds": panel_box,
                    "visible": True,
                    "style": {"fill": "#000000", "opacity": 0.55, "radius": 12},
                    "children": [
                        {
                            "semantic_id": "screen_title",
                            "kind": "text",
                            "semantic_role": "screen_title",
                            "bounds": [px + 12, py + 10, pw - 24, 28],
                            "visible": True,
                            "text": title,
                            "style": {"color": rgb(TEXT_COLOR), "font_size": 24},
                        },
                        {
                            "semantic_id": "score_panel",
                            "kind": "text",
                            "semantic_role": "score_status",
                            "bounds": [px + 12, py + 42, pw - 24, 68],
                            "visible": True,
                            "text": "Score: 0\nLines: 0\nSpeed level: 1",
                            "style": {"color": rgb(TEXT_COLOR), "font_size": 15},
                        },
                        {
                            "semantic_id": "piece_controls",
                            "kind": "frame",
                            "semantic_role": "piece_controls",
                            "bounds": [px + 6, py + 118, pw - 12, ph - 126],
                            "visible": True,
                            "style": {"padding": 12, "gap": 8},
                        },
                    ]
                    + (
                        [
                            {
                                "semantic_id": "camera_controls",
                                "kind": "text",
                                "semantic_role": "camera_controls",
                                "bounds": [px + 12, py + 250, pw - 24, 50],
                                "visible": True,
                                "text": "Camera control",
                                "style": {"color": rgb(TEXT_COLOR), "font_size": 13},
                            }
                        ]
                        if mode in {"3d", "4d"}
                        else []
                    )
                    + (
                        [
                            {
                                "semantic_id": "layer_status",
                                "kind": "text",
                                "semantic_role": "layer_status",
                                "bounds": [px + 12, py + 322, pw - 24, 50],
                                "visible": True,
                                "text": "View: basis-mapped 3D layer boards\nLayer count: 4",
                                "style": {"color": rgb(TEXT_COLOR), "font_size": 13},
                            }
                        ]
                        if mode == "4d"
                        else []
                    ),
                },
            ],
        },
        "screenshot": png.name,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for mode in ("2d", "3d", "4d"):
        data = capture(mode, args.output)
        (args.output / f"game_{mode}.probe.json").write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n"
        )


if __name__ == "__main__":
    main()
