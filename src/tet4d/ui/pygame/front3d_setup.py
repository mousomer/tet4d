from __future__ import annotations

from typing import Optional, TypeAlias

import pygame

from tet4d.engine.api import (
    GameConfigND,
    GameStateND,
    front3d_setup_build_config_nd,
    front3d_setup_create_initial_state_nd,
    front3d_setup_game_settings_type,
    front3d_setup_gravity_interval_ms_from_config_nd,
    front3d_setup_run_menu_nd,
)


# 3D setup now reuses the shared ND setup/menu implementation.
GameSettings3D: TypeAlias = front3d_setup_game_settings_type()


def run_menu(screen: pygame.Surface, fonts) -> Optional[GameSettings3D]:
    return front3d_setup_run_menu_nd(screen, fonts, 3)


def build_config(settings: GameSettings3D) -> GameConfigND:
    return front3d_setup_build_config_nd(settings, 3)


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    return front3d_setup_create_initial_state_nd(cfg)


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    return front3d_setup_gravity_interval_ms_from_config_nd(cfg)
