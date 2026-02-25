from __future__ import annotations

PARITY_ACTION_IDS: frozenset[str] = frozenset(
    {
        "settings",
        "keybindings",
        "help",
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
        "continue",
        "settings",
        "keybindings",
        "help",
        "bot_options",
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
        "profile_prev",
        "profile_next",
        "save_bindings",
        "load_bindings",
        "help",
        "menu",
        "quit",
    }
)

