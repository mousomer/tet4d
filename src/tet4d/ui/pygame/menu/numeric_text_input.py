from __future__ import annotations

from collections.abc import Callable

SanitizeTextFn = Callable[[str, int], str]


def numeric_digits_only(
    text: str,
    *,
    max_length: int,
    sanitize_text: SanitizeTextFn,
) -> str:
    sanitized = sanitize_text(text, max_length)
    return "".join(ch for ch in sanitized if ch.isdigit())


def append_numeric_text(
    *,
    current_buffer: str,
    incoming_text: str,
    replace_on_type: bool,
    max_length: int,
    sanitize_text: SanitizeTextFn,
) -> tuple[str, bool]:
    digits = numeric_digits_only(
        incoming_text,
        max_length=max_length,
        sanitize_text=sanitize_text,
    )
    if not digits:
        return current_buffer, replace_on_type
    next_buffer = "" if replace_on_type else current_buffer
    next_buffer = (next_buffer + digits)[:max_length]
    return next_buffer, False


def parse_numeric_text(
    text: str,
    *,
    max_length: int,
    sanitize_text: SanitizeTextFn,
) -> int | None:
    digits = numeric_digits_only(
        text,
        max_length=max_length,
        sanitize_text=sanitize_text,
    )
    if not digits:
        return None
    return int(digits)
