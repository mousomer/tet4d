from __future__ import annotations

PARITY_ACTION_IDS: frozenset[str] = frozenset(
    {
        "settings",
        "keybindings",
        "help",
        "leaderboard",
        "bot_options",
        "quit",
    }
)

LAUNCHER_ACTION_IDS: frozenset[str] = frozenset(
    {
        "play",
        "play_2d",
        "play_3d",
        "play_4d",
        "play_last_custom_topology",
        "continue",
        "tutorial_2d",
        "tutorial_3d",
        "tutorial_4d",
        "tutorial_how_to_play",
        "tutorial_controls_reference",
        "settings",
        "settings_display",
        "settings_audio",
        "settings_profiles",
        "settings_advanced",
        "settings_legacy_topology_editor",
        "keybindings",
        "help",
        "leaderboard",
        "bot_options",
        "topology_lab",
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
