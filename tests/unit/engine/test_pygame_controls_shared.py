from __future__ import annotations

from types import SimpleNamespace
import unittest

import pygame

from tet4d.ui.pygame.controls import (
    NumericRowSpec,
    append_numeric_text_input,
    build_control_row_layouts,
    commit_numeric_text_mode,
    dropdown_menu_rect,
    dropdown_option_index_at_position,
    dropdown_option_rects,
    open_dropdown,
    select_dropdown_option_from_click,
    set_slider_value_from_pointer,
    slider_fraction_for_row,
    slider_rect_for_row,
    start_numeric_text_mode,
    step_numeric_row,
    update_dropdown_hover_index,
    update_dropdown_scroll,
)


class TestPygameControlsShared(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.font.init()

    def tearDown(self) -> None:
        pygame.quit()

    def _font(self) -> pygame.font.Font:
        return pygame.font.SysFont(None, 22)

    def test_dropdown_select_and_outside_click_close(self) -> None:
        state = SimpleNamespace(
            open_dropdown_row_key=None,
            dropdown_hover_index=None,
            dropdown_scroll_offset=0,
        )
        row_layouts = build_control_row_layouts(
            ("grid_mode",),
            font=self._font(),
            panel_width=320,
            dropdown_affordance_width=34,
            label_for_row=lambda _: "Grid",
            value_for_row=lambda _: "FULL",
            control_kind_for_row=lambda _: "dropdown",
            slider_fraction_for_row=lambda _: None,
        )
        row_rects = (pygame.Rect(20, 20, 280, row_layouts[0].row_height),)
        viewport = pygame.Rect(20, 20, 280, 220)
        options = (("off", "NONE"), ("edge", "EDGE"), ("full", "FULL"))
        selected: list[tuple[str, str]] = []

        open_dropdown(state, row_key="grid_mode")
        menu_rect = dropdown_menu_rect(
            row_rects[0],
            option_count=len(options),
            viewport=viewport,
            font=self._font(),
            menu_width=220,
            option_vertical_padding=10,
        )
        option_rect = dropdown_option_rects(
            state,
            menu_rect=menu_rect,
            option_count=len(options),
            font=self._font(),
            option_vertical_padding=10,
        )[1][1]
        row_key, changed = select_dropdown_option_from_click(
            state,
            position=option_rect.center,
            row_layouts=row_layouts,
            row_rects=row_rects,
            layout_viewport=viewport,
            font=self._font(),
            options_for_row=lambda _: options,
            apply_value=lambda key, raw_value: selected.append((key, raw_value)) or True,
            menu_width=220,
            option_vertical_padding=10,
        )

        self.assertEqual(("grid_mode", True), (row_key, changed))
        self.assertEqual([("grid_mode", "edge")], selected)
        self.assertIsNone(state.open_dropdown_row_key)

        open_dropdown(state, row_key="grid_mode")
        row_key, changed = select_dropdown_option_from_click(
            state,
            position=(viewport.right + 40, viewport.bottom + 40),
            row_layouts=row_layouts,
            row_rects=row_rects,
            layout_viewport=viewport,
            font=self._font(),
            options_for_row=lambda _: options,
            apply_value=lambda *_: True,
            menu_width=220,
            option_vertical_padding=10,
        )
        self.assertEqual((None, False), (row_key, changed))
        self.assertIsNone(state.open_dropdown_row_key)

    def test_dropdown_hover_hitbox_and_scroll(self) -> None:
        state = SimpleNamespace(
            open_dropdown_row_key="topology",
            dropdown_hover_index=None,
            dropdown_scroll_offset=0,
        )
        options = tuple((f"preset_{idx}", f"Preset {idx}") for idx in range(12))
        row_layouts = build_control_row_layouts(
            ("topology",),
            font=self._font(),
            panel_width=320,
            dropdown_affordance_width=34,
            label_for_row=lambda _: "Topology",
            value_for_row=lambda _: "Preset 0",
            control_kind_for_row=lambda _: "dropdown",
            slider_fraction_for_row=lambda _: None,
        )
        row_rects = (pygame.Rect(20, 20, 280, row_layouts[0].row_height),)
        viewport = pygame.Rect(20, 20, 280, 120)
        menu_rect = dropdown_menu_rect(
            row_rects[0],
            option_count=len(options),
            viewport=viewport,
            font=self._font(),
            menu_width=220,
            option_vertical_padding=10,
        )
        option_rect = dropdown_option_rects(
            state,
            menu_rect=menu_rect,
            option_count=len(options),
            font=self._font(),
            option_vertical_padding=10,
        )[0][1]

        update_dropdown_hover_index(
            state,
            row_layouts=row_layouts,
            row_rects=row_rects,
            layout_viewport=viewport,
            font=self._font(),
            position=option_rect.center,
            options_for_row=lambda _: options,
            menu_width=220,
            option_vertical_padding=10,
        )
        self.assertEqual(0, state.dropdown_hover_index)
        self.assertEqual(
            0,
            dropdown_option_index_at_position(
                state,
                row_layouts=row_layouts,
                row_rects=row_rects,
                layout_viewport=viewport,
                font=self._font(),
                position=option_rect.center,
                options_for_row=lambda _: options,
                menu_width=220,
                option_vertical_padding=10,
            ),
        )

        wheel_event = pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1})
        self.assertTrue(
            update_dropdown_scroll(
                state,
                wheel_event,
                row_layouts=row_layouts,
                row_rects=row_rects,
                layout_viewport=viewport,
                font=self._font(),
                options_for_row=lambda _: options,
                menu_width=220,
                option_vertical_padding=10,
            )
        )
        self.assertGreaterEqual(state.dropdown_scroll_offset, 1)

    def test_numeric_text_entry_commit_and_validation(self) -> None:
        state = SimpleNamespace(
            numeric_text_row_key="",
            numeric_text_buffer="",
            numeric_text_replace_on_type=False,
            status="",
            status_error=False,
            seed=1337,
        )
        specs = {"seed": NumericRowSpec("seed", 0.0, 9999.0, 1.0, 0)}

        self.assertTrue(
            start_numeric_text_mode(
                state,
                "seed",
                spec_for_row=specs.get,
                value_for_row=lambda key: float(getattr(state, key)),
            )
        )
        self.assertTrue(
            append_numeric_text_input(
                state,
                "42",
                spec_for_row=specs.get,
            )
        )
        committed = commit_numeric_text_mode(
            state,
            spec_for_row=specs.get,
            set_value_for_row=lambda key, value: setattr(state, key, int(value)),
            row_label_text=lambda _: "Seed",
        )

        self.assertTrue(committed)
        self.assertEqual(42, state.seed)
        self.assertEqual("Seed updated.", state.status)

        start_numeric_text_mode(
            state,
            "seed",
            spec_for_row=specs.get,
            value_for_row=lambda key: float(getattr(state, key)),
        )
        state.numeric_text_buffer = "."
        self.assertFalse(
            commit_numeric_text_mode(
                state,
                spec_for_row=specs.get,
                set_value_for_row=lambda key, value: setattr(state, key, int(value)),
                row_label_text=lambda _: "Seed",
            )
        )
        self.assertTrue(state.status_error)

    def test_slider_drag_and_stepper_update_numeric_values(self) -> None:
        state = SimpleNamespace(base_mass=1.0)
        specs = {"base_mass": NumericRowSpec("base_mass", 0.5, 2.0, 0.05, 2)}
        row_layouts = build_control_row_layouts(
            ("base_mass",),
            font=self._font(),
            panel_width=360,
            dropdown_affordance_width=34,
            label_for_row=lambda _: "Base Mass",
            value_for_row=lambda _: "1.00",
            control_kind_for_row=lambda _: "numeric",
            slider_fraction_for_row=lambda _: slider_fraction_for_row(
                "base_mass",
                spec_for_row=specs.get,
                value_for_row=lambda key: float(getattr(state, key)),
            ),
        )
        row_rect = pygame.Rect(20, 20, 320, row_layouts[0].row_height)
        slider_rect = slider_rect_for_row(row_rect, row_layouts[0])
        assert slider_rect is not None

        self.assertTrue(
            set_slider_value_from_pointer(
                "base_mass",
                pointer_x=slider_rect.right,
                slider_rect=slider_rect,
                spec_for_row=specs.get,
                set_value_for_row=lambda key, value: setattr(state, key, round(value, 2)),
            )
        )
        self.assertGreaterEqual(state.base_mass, 1.95)

        stepped = step_numeric_row(
            "base_mass",
            -1,
            spec_for_row=specs.get,
            value_for_row=lambda key: float(getattr(state, key)),
            set_value_for_row=lambda key, value: setattr(state, key, round(value, 2)),
        )
        self.assertTrue(stepped)
        self.assertLess(state.base_mass, 2.0)

    def test_wrapped_label_value_layout_reserves_non_overlap_space(self) -> None:
        long_label = "Explosion diagnostics label that must wrap without obscuring the value block"
        long_value = "A deliberately long current value preview"
        row_layouts = build_control_row_layouts(
            ("diagnostics_mode",),
            font=self._font(),
            panel_width=280,
            dropdown_affordance_width=34,
            label_for_row=lambda _: long_label,
            value_for_row=lambda _: long_value,
            control_kind_for_row=lambda _: "dropdown",
            slider_fraction_for_row=lambda _: None,
        )
        row = row_layouts[0]

        self.assertGreater(len(row.label_lines), 1)
        self.assertGreater(len(row.value_lines), 0)
        self.assertGreaterEqual(row.value_right_padding, 46)
        self.assertGreater(row.row_height, self._font().get_height() + 10)


if __name__ == "__main__":
    unittest.main()
