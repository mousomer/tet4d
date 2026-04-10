from __future__ import annotations

import pygame

from tet4d.ui.pygame.keybindings import active_key_profile, list_key_profiles

SETTINGS_PROFILE_PLACEHOLDER_ACTION = "settings_profiles"
SETTINGS_PROFILE_ACTION_PREFIX = "settings_profile__"
SETTINGS_PROFILES_MENU_ID = "launcher_settings_profiles"


def profile_action_id(profile: str) -> str:
    return f"{SETTINGS_PROFILE_ACTION_PREFIX}{str(profile).strip().lower()}"


def profile_label(profile: str) -> str:
    active = active_key_profile()
    clean = str(profile).strip()
    return f"Profile: {clean} (Active)" if clean == active else f"Profile: {clean}"


def expand_settings_profile_rows(
    items: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    expanded: list[dict[str, str]] = []
    for item in items:
        action_id = str(item.get("action_id", "")).strip().lower()
        if action_id != SETTINGS_PROFILE_PLACEHOLDER_ACTION:
            expanded.append(dict(item))
            continue
        for profile in list_key_profiles():
            expanded.append(
                {
                    "type": "action",
                    "label": profile_label(profile),
                    "action_id": profile_action_id(profile),
                }
            )
    return tuple(expanded)


def is_profile_prev_key(key: int) -> bool:
    return key in (
        pygame.K_LEFTBRACKET,
        pygame.K_MINUS,
        pygame.K_PAGEUP,
    )


def is_profile_next_key(key: int) -> bool:
    return key in (
        pygame.K_RIGHTBRACKET,
        pygame.K_EQUALS,
        pygame.K_PAGEDOWN,
    )
