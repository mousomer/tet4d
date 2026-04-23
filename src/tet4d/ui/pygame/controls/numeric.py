from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame


@dataclass(frozen=True)
class NumericRowSpec:
    row_key: str
    minimum: float
    maximum: float
    step: float
    decimals: int
    unit_suffix: str = ""


def _format_numeric_value(value: float, *, decimals: int) -> str:
    if decimals <= 0:
        return str(int(round(value)))
    return f"{value:.{decimals}f}"


def numeric_display_text(
    state,
    *,
    row_key: str,
    spec_for_row: Callable[[str], NumericRowSpec | None],
    value_for_row: Callable[[str], float],
    custom_formatters: dict[str, Callable[[float], str]] | None = None,
) -> str:
    spec = spec_for_row(row_key)
    if spec is None:
        return ""
    if state.numeric_text_row_key == row_key:
        return f"{state.numeric_text_buffer or ''}{spec.unit_suffix}"
    formatter = (custom_formatters or {}).get(row_key)
    if formatter is not None:
        return f"{formatter(value_for_row(row_key))}{spec.unit_suffix}"
    return f"{_format_numeric_value(value_for_row(row_key), decimals=spec.decimals)}{spec.unit_suffix}"


def start_numeric_text_mode(
    state,
    row_key: str,
    *,
    spec_for_row: Callable[[str], NumericRowSpec | None],
    value_for_row: Callable[[str], float],
    display_value_for_edit: Callable[[str, float, NumericRowSpec], str] | None = None,
    incoming_text: str = "",
) -> bool:
    spec = spec_for_row(row_key)
    if spec is None:
        return False
    current_value = value_for_row(row_key)
    if display_value_for_edit is not None:
        state.numeric_text_buffer = display_value_for_edit(row_key, current_value, spec)
    else:
        state.numeric_text_buffer = _format_numeric_value(current_value, decimals=spec.decimals)
    state.numeric_text_row_key = row_key
    state.numeric_text_replace_on_type = True
    if incoming_text:
        return append_numeric_text_input(
            state,
            incoming_text,
            spec_for_row=spec_for_row,
        )
    return True


def stop_numeric_text_mode(state) -> None:
    state.numeric_text_row_key = ""
    state.numeric_text_buffer = ""
    state.numeric_text_replace_on_type = False


def append_numeric_text_input(
    state,
    incoming_text: str,
    *,
    spec_for_row: Callable[[str], NumericRowSpec | None],
) -> bool:
    spec = spec_for_row(state.numeric_text_row_key)
    if spec is None:
        return False
    allowed_chars = "0123456789"
    if spec.decimals > 0:
        allowed_chars += "."
    filtered = "".join(ch for ch in incoming_text if ch in allowed_chars)
    if not filtered:
        return False
    next_buffer = "" if state.numeric_text_replace_on_type else state.numeric_text_buffer
    for char in filtered:
        if char == "." and "." in next_buffer:
            continue
        next_buffer += char
    state.numeric_text_buffer = next_buffer[:12]
    state.numeric_text_replace_on_type = False
    return True


def commit_numeric_text_mode(
    state,
    *,
    spec_for_row: Callable[[str], NumericRowSpec | None],
    set_value_for_row: Callable[[str, float], None],
    row_label_text: Callable[[str], str],
    value_transformers: dict[str, Callable[[float], float]] | None = None,
    allow_partial: bool = False,
) -> bool:
    row_key = state.numeric_text_row_key
    spec = spec_for_row(row_key)
    if spec is None:
        return False
    raw = state.numeric_text_buffer.strip()
    if not raw or raw == ".":
        if allow_partial:
            return False
        state.status = f"{row_label_text(row_key)} input must be numeric."
        state.status_error = True
        stop_numeric_text_mode(state)
        return False
    try:
        parsed = float(raw)
    except ValueError:
        if allow_partial:
            return False
        state.status = f"{row_label_text(row_key)} input must be numeric."
        state.status_error = True
        stop_numeric_text_mode(state)
        return False
    transformer = (value_transformers or {}).get(row_key)
    if transformer is not None:
        parsed = transformer(parsed)
    set_value_for_row(row_key, parsed)
    state.status = f"{row_label_text(row_key)} updated."
    state.status_error = False
    stop_numeric_text_mode(state)
    return True


def handle_numeric_text_keydown(
    state,
    key: int,
    *,
    row_key: str,
    spec_for_row: Callable[[str], NumericRowSpec | None],
    start_numeric_mode: Callable[[str], bool],
    append_input: Callable[[str], bool],
    commit_mode: Callable[[], bool],
) -> bool:
    spec = spec_for_row(row_key)
    if spec is None:
        return False
    if state.numeric_text_row_key != row_key and key not in (
        pygame.K_BACKSPACE,
        pygame.K_PERIOD,
        pygame.K_KP_PERIOD,
    ) and not (pygame.K_0 <= key <= pygame.K_9):
        return False
    if state.numeric_text_row_key != row_key:
        start_numeric_mode(row_key)
    if key == pygame.K_BACKSPACE:
        state.numeric_text_buffer = str(state.numeric_text_buffer)[:-1]
        return True
    if key in (pygame.K_PERIOD, pygame.K_KP_PERIOD):
        if spec.decimals > 0 and "." not in str(state.numeric_text_buffer):
            state.numeric_text_buffer = f"{state.numeric_text_buffer}."
        return True
    if pygame.K_0 <= key <= pygame.K_9:
        return append_input(chr(key))
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return commit_mode()
    return False


def slider_fraction_for_row(
    row_key: str,
    *,
    spec_for_row: Callable[[str], NumericRowSpec | None],
    value_for_row: Callable[[str], float],
) -> float | None:
    spec = spec_for_row(row_key)
    if spec is None:
        return None
    span = max(1.0, float(spec.maximum) - float(spec.minimum))
    return max(0.0, min(1.0, (float(value_for_row(row_key)) - float(spec.minimum)) / span))


def slider_fraction_from_pointer(slider_rect: pygame.Rect, pointer_x: int) -> float:
    return max(
        0.0,
        min(
            1.0,
            (float(pointer_x) - float(slider_rect.x))
            / max(1.0, float(max(1, slider_rect.width - 1))),
        ),
    )


def set_slider_value_from_pointer(
    row_key: str,
    *,
    pointer_x: int,
    slider_rect: pygame.Rect,
    spec_for_row: Callable[[str], NumericRowSpec | None],
    set_value_for_row: Callable[[str, float], None],
) -> bool:
    spec = spec_for_row(row_key)
    if spec is None:
        return False
    fraction = slider_fraction_from_pointer(slider_rect, pointer_x)
    value = float(spec.minimum) + fraction * (float(spec.maximum) - float(spec.minimum))
    if spec.decimals <= 0:
        value = round(value / max(1.0, spec.step)) * spec.step
    set_value_for_row(row_key, value)
    return True


def step_numeric_row(
    row_key: str,
    direction: int,
    *,
    spec_for_row: Callable[[str], NumericRowSpec | None],
    value_for_row: Callable[[str], float],
    set_value_for_row: Callable[[str, float], None],
) -> bool:
    spec = spec_for_row(row_key)
    if spec is None:
        return False
    set_value_for_row(
        row_key,
        value_for_row(row_key) + (float(direction) * float(spec.step)),
    )
    return True
