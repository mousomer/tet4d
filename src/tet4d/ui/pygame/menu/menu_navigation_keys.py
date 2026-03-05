from __future__ import annotations

import pygame
from tet4d.ui.pygame.keybindings import PROFILE_TINY, active_key_profile


_TINY_NAV_ALIASES: dict[int, int] = {
    pygame.K_i: pygame.K_UP,
    pygame.K_k: pygame.K_DOWN,
    pygame.K_j: pygame.K_LEFT,
    pygame.K_l: pygame.K_RIGHT,
}


def normalize_menu_navigation_key(key: int) -> int:
    key_code = int(key)
    if active_key_profile() != PROFILE_TINY:
        return key_code
    return _TINY_NAV_ALIASES.get(key_code, key_code)
