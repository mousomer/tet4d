from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pygame

from tet4d.ui.pygame.menu.menu_controls import apply_menu_actions, gather_menu_actions


@dataclass
class _DummySettings:
    width: int = 8
    height: int = 16
    depth: int = 6
    fourth: int = 4


@dataclass
class _DummyState:
    settings: _DummySettings
    selected_index: int = 0
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False
    active_profile: str = "small"
    rebind_mode: bool = False
    rebind_index: int = 0
    rebind_targets: list[tuple[str, str]] | None = None
    rebind_conflict_mode: str = "replace"
    run_dry_run: bool = False
    numeric_text_mode: bool = False
    numeric_text_attr_name: str = ""
    numeric_text_label: str = ""
    numeric_text_buffer: str = ""
    numeric_text_replace_on_type: bool = False


def _keydown(key: int, unicode: str = "") -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode)


def _textinput(text: str) -> pygame.event.Event:
    return pygame.event.Event(pygame.TEXTINPUT, text=text)


def _collect_and_apply(state: _DummyState, fields) -> None:
    actions = gather_menu_actions(state, 4)
    apply_menu_actions(state, actions, fields, 4)


def test_numeric_entry_commits_setup_value() -> None:
    pygame.init()
    try:
        state = _DummyState(settings=_DummySettings(width=8))
        fields = [("Width", "width", 4, 40), ("Height", "height", 8, 60)]
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_2, '2')]):
            _collect_and_apply(state, fields)
        assert state.numeric_text_mode is True
        assert state.numeric_text_buffer == '2'
        with patch.object(pygame.event, 'get', return_value=[_textinput('4')]):
            _collect_and_apply(state, fields)
        assert state.numeric_text_buffer == '24'
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_RETURN)]):
            _collect_and_apply(state, fields)
        assert state.numeric_text_mode is False
        assert state.settings.width == 24
    finally:
        pygame.quit()


def test_numeric_entry_backspace_and_cancel_preserves_value() -> None:
    pygame.init()
    try:
        state = _DummyState(settings=_DummySettings(width=18))
        fields = [("Width", "width", 4, 40), ("Height", "height", 8, 60)]
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_2, '2')]):
            _collect_and_apply(state, fields)
        with patch.object(pygame.event, 'get', return_value=[_textinput('4')]):
            _collect_and_apply(state, fields)
        assert state.numeric_text_buffer == '24'
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_BACKSPACE)]):
            _collect_and_apply(state, fields)
        assert state.numeric_text_buffer == '2'
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_ESCAPE)]):
            _collect_and_apply(state, fields)
        assert state.numeric_text_mode is False
        assert state.settings.width == 18
    finally:
        pygame.quit()


def test_numeric_entry_clamps_nd_dimension_value() -> None:
    pygame.init()
    try:
        state = _DummyState(settings=_DummySettings(fourth=4), selected_index=0)
        fields = [("Fourth", "fourth", 2, 8)]
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_9, '9')]):
            _collect_and_apply(state, fields)
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_RETURN)]):
            _collect_and_apply(state, fields)
        assert state.settings.fourth == 8
    finally:
        pygame.quit()
