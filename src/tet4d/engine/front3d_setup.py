from __future__ import annotations

from typing import Optional, TypeAlias

import pygame

from .frontend_nd import (
    GameSettingsND,
    build_config as build_config_nd,
    create_initial_state as create_initial_state_nd,
    gravity_interval_ms_from_config as gravity_interval_ms_from_config_nd,
    run_menu as run_menu_nd,
)
from .gameplay.game_nd import GameConfigND, GameStateND


# 3D setup now reuses the shared ND setup/menu implementation.
GameSettings3D: TypeAlias = GameSettingsND


def run_menu(screen: pygame.Surface, fonts) -> Optional[GameSettings3D]:
    return run_menu_nd(screen, fonts, 3)


def build_config(settings: GameSettings3D) -> GameConfigND:
    return build_config_nd(settings, 3)


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    return create_initial_state_nd(cfg)


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    return gravity_interval_ms_from_config_nd(cfg)
