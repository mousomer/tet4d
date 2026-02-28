from __future__ import annotations

from collections.abc import Sequence

import pygame


_KEY_NAME_OVERRIDES = {
    "escape": "Esc",
    "return": "Enter",
    "space": "Space",
    "left shift": "LShift",
    "right shift": "RShift",
    "left": "Left",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "left bracket": "[",
    "right bracket": "]",
    "semicolon": ";",
    "quote": "'",
    "comma": ",",
    "period": ".",
}


def display_key_name(key: int) -> str:
    raw = pygame.key.name(key)
    if not raw:
        return str(key)
    lowered = raw.lower()
    if lowered in _KEY_NAME_OVERRIDES:
        return _KEY_NAME_OVERRIDES[lowered]
    if len(raw) == 1:
        return raw.upper()
    words = []
    for word in raw.split():
        if word == "kp":
            words.append("Numpad")
        else:
            words.append(word.capitalize())
    return " ".join(words)


def format_key_tuple(keys: Sequence[int]) -> str:
    if not keys:
        return "-"
    return "/".join(display_key_name(key) for key in keys)
