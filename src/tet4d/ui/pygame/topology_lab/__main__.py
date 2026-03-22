"""Standalone entry point for the topology explorer playground."""
from __future__ import annotations

import sys

from tet4d.ui.pygame.render.font_profiles import init_fonts
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    initialize_runtime,
    open_display,
)
from tet4d.ui.pygame.launch.topology_lab_menu import run_explorer_playground


def main() -> None:
    dimension = 2
    if len(sys.argv) > 1:
        dimension = int(sys.argv[1])
    if dimension not in (2, 3, 4):
        print(f"Unsupported dimension: {dimension}. Use 2, 3, or 4.")
        sys.exit(1)

    runtime = initialize_runtime(sync_audio_state=False)
    display_settings = DisplaySettings(
        fullscreen=runtime.display_settings.fullscreen,
        windowed_size=runtime.display_settings.windowed_size,
    )
    fonts = init_fonts()
    screen = open_display(
        display_settings,
        caption=f"Explorer {dimension}D Playground",
    )
    run_explorer_playground(
        screen,
        fonts,
        dimension=dimension,
        display_settings=display_settings,
    )


if __name__ == "__main__":
    main()
