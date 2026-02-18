from __future__ import annotations

from dataclasses import dataclass

import pygame


CONFIRM_KEYS: tuple[int, ...] = (pygame.K_RETURN, pygame.K_KP_ENTER)


@dataclass
class MenuLoopState:
    selected: int = 0
    running: bool = True
    status: str = ""
    status_error: bool = False


def is_confirm_key(key: int) -> bool:
    return key in CONFIRM_KEYS


def cycle_index(current: int, size: int, step: int) -> int:
    if size <= 0:
        return 0
    return (current + step) % size


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    return max(minimum, min(maximum, int(value)))
