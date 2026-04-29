from __future__ import annotations

PARITY_ACTION_IDS: frozenset[str] = frozenset(
    {
        "settings",
        "help",
        "leaderboard",
        "bot_options",
    }
)

LAUNCHER_ACTION_IDS: frozenset[str] = frozenset(
    {
        "play",
        "play_2d",
        "play_3d",
        "play_4d",
        "setup_2d",
        "setup_3d",
        "setup_4d",
        "play_last_custom_topology",
        "continue",
        "tutorial_2d",
        "tutorial_3d",
        "tutorial_4d",
        "tutorial_how_to_play",
        "tutorial_controls_reference",
        "settings",
        "help",
        "leaderboard",
        "bot_options",
        "topology_lab",
        "locked_cell_explosion",
        "quit",
    }
)

PAUSE_ACTION_IDS: frozenset[str] = frozenset(
    {
        "resume",
        "restart",
        "settings",
        "bot_options",
        "keybindings",
        "leaderboard",
        "profile_prev",
        "profile_next",
        "save_bindings",
        "load_bindings",
        "help",
        "menu",
        "quit",
    }
)
