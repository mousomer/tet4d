from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

import pygame

from tet4d.engine.runtime.menu_field_spec import FieldSpec
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
        fields = [
            FieldSpec("Width", "width", "int", "stepper", min_value=4, max_value=40),
            FieldSpec("Height", "height", "int", "stepper", min_value=8, max_value=60),
        ]
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
        fields = [
            FieldSpec("Width", "width", "int", "stepper", min_value=4, max_value=40),
            FieldSpec("Height", "height", "int", "stepper", min_value=8, max_value=60),
        ]
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
        fields = [
            FieldSpec("Fourth", "fourth", "int", "stepper", min_value=2, max_value=8)
        ]
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_9, '9')]):
            _collect_and_apply(state, fields)
        with patch.object(pygame.event, 'get', return_value=[_keydown(pygame.K_RETURN)]):
            _collect_and_apply(state, fields)
        assert state.settings.fourth == 8
    finally:
        pygame.quit()


def test_nd_setup_draw_menu_renders_one_frame_for_3d_and_4d() -> None:
    pygame.init()
    try:
        from tet4d.ui.pygame import frontend_nd_setup

        fonts = frontend_nd_setup.init_fonts()
        screen = pygame.Surface((960, 720), pygame.SRCALPHA)
        state = frontend_nd_setup.MenuState()
        for dimension in (3, 4):
            fields = frontend_nd_setup.menu_fields_for_settings(state.settings, dimension)
            assert fields
            assert all(isinstance(field, FieldSpec) for field in fields)
            frontend_nd_setup.draw_menu(
                screen,
                fonts,
                state,
                dimension,
                menu_fields=fields,
            )
    finally:
        pygame.quit()


def test_setup_menu_runner_forwards_fields_to_draw_frame() -> None:
    pygame.init()
    try:
        from tet4d.ui.pygame.menu import setup_menu_runner

        screen = pygame.Surface((320, 200), pygame.SRCALPHA)
        sentinel_fields = [
            FieldSpec(
                "Foo",
                "foo",
                "int",
                "stepper",
                min_value=0,
                max_value=10,
            )
        ]
        state = SimpleNamespace(
            settings=SimpleNamespace(foo=1),
            selected_index=0,
            running=True,
            start_game=False,
            bindings_status="",
            bindings_status_error=False,
            active_profile="small",
            run_dry_run=False,
        )
        captured = {}

        def _fields_for_state(_settings):
            return sentinel_fields

        def _draw_frame(_screen, current_state, fields):
            captured["fields"] = fields
            current_state.running = False

        with (
            patch.object(setup_menu_runner, "load_active_profile_bindings"),
            patch.object(setup_menu_runner, "load_menu_settings", return_value=(False, "nope")),
            patch.object(setup_menu_runner, "set_active_key_profile"),
            patch.object(setup_menu_runner, "save_menu_settings", return_value=(True, "")),
            patch.object(setup_menu_runner, "gather_menu_actions", return_value=()),
            patch.object(setup_menu_runner, "apply_menu_actions"),
            patch.object(setup_menu_runner.pygame.display, "flip"),
        ):
            result = setup_menu_runner.run_setup_menu_loop(
                screen=screen,
                state=state,
                dimension=3,
                fields_for_state=_fields_for_state,
                draw_frame=_draw_frame,
            )

        assert result is None
        assert captured.get("fields") is sentinel_fields
    finally:
        pygame.quit()
