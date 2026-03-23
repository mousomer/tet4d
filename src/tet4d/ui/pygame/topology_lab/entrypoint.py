from __future__ import annotations

import pygame

from tet4d.engine.runtime.topology_explorer_runtime import (
    load_runtime_explorer_topology_profile,
)
from tet4d.ui.pygame.launch.topology_lab_menu import run_explorer_playground
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    initialize_runtime,
    open_display,
)
from tet4d.ui.pygame.render.font_profiles import init_fonts as init_fonts_for_profile
from tet4d.ui.pygame.topology_lab.app import (
    build_explorer_playground_launch,
    mode_settings_snapshot_for_dimension,
)


def parse_topology_playground_dimension(raw_value: object) -> int | None:
    if raw_value is None:
        return None
    try:
        dimension = int(raw_value)
    except (TypeError, ValueError):
        print(f"Unsupported dimension: {raw_value}. Use 2, 3, or 4.")
        raise SystemExit(1) from None
    if dimension not in (2, 3, 4):
        print(f"Unsupported dimension: {dimension}. Use 2, 3, or 4.")
        raise SystemExit(1)
    return dimension


def run_direct_topology_playground(dimension: int) -> None:
    runtime = initialize_runtime(sync_audio_state=False)
    display_settings = DisplaySettings(
        fullscreen=runtime.display_settings.fullscreen,
        windowed_size=runtime.display_settings.windowed_size,
    )
    fonts = init_fonts_for_profile("nd")
    fonts_2d = init_fonts_for_profile("2d")
    screen = open_display(
        display_settings,
        caption=f"Explorer {dimension}D Playground",
    )
    ok, message = run_explorer_playground(
        screen,
        fonts,
        launch=build_explorer_playground_launch(
            dimension=dimension,
            explorer_profile=load_runtime_explorer_topology_profile(dimension),
            display_settings=display_settings,
            fonts_2d=fonts_2d,
            gameplay_mode="explorer",
            entry_source="cli",
            source_settings=mode_settings_snapshot_for_dimension(dimension),
        ),
    )
    pygame.quit()
    if not ok:
        raise SystemExit(message)
    raise SystemExit(0)


__all__ = [
    "parse_topology_playground_dimension",
    "run_direct_topology_playground",
]
