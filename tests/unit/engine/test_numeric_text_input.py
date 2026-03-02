from __future__ import annotations

from tet4d.ui.pygame.menu.numeric_text_input import (
    append_numeric_text,
    numeric_digits_only,
    parse_numeric_text,
)


def _sanitize_text(value: str, max_length: int) -> str:
    return value[:max_length]


def test_numeric_digits_only_filters_non_digits() -> None:
    assert (
        numeric_digits_only(
            "a1b2-3",
            max_length=16,
            sanitize_text=_sanitize_text,
        )
        == "123"
    )


def test_append_numeric_text_replaces_on_first_type() -> None:
    buffer, replace_flag = append_numeric_text(
        current_buffer="99",
        incoming_text="42",
        replace_on_type=True,
        max_length=4,
        sanitize_text=_sanitize_text,
    )
    assert buffer == "42"
    assert replace_flag is False


def test_append_numeric_text_appends_until_max_length() -> None:
    buffer, replace_flag = append_numeric_text(
        current_buffer="123",
        incoming_text="45",
        replace_on_type=False,
        max_length=4,
        sanitize_text=_sanitize_text,
    )
    assert buffer == "1234"
    assert replace_flag is False


def test_parse_numeric_text_returns_none_for_invalid_input() -> None:
    assert parse_numeric_text("", max_length=8, sanitize_text=_sanitize_text) is None
    assert (
        parse_numeric_text("abc", max_length=8, sanitize_text=_sanitize_text) is None
    )


def test_parse_numeric_text_returns_integer() -> None:
    assert parse_numeric_text("x007", max_length=8, sanitize_text=_sanitize_text) == 7
