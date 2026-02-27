from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment guard
    raise unittest.SkipTest(
        "pygame-ce is required for keybinding menu model tests"
    ) from exc

from tet4d.ui.pygame.menu.keybindings_menu_model import rows_for_scope
from tet4d.ui.pygame.keybindings import runtime_binding_groups_for_dimension


def _header_titles(scope: str) -> list[str]:
    rendered_rows, _ = rows_for_scope(scope)
    return [
        row.text
        for row in rendered_rows
        if row.kind == "header" and row.text and not row.text.startswith("  ")
    ]


def _binding_tuples(scope: str) -> set[tuple[int, str, str]]:
    _, binding_rows = rows_for_scope(scope)
    return {(row.dimension, row.group, row.action) for row in binding_rows}


def _expected_scope_bindings(scope: str) -> set[tuple[int, str, str]]:
    expected: set[tuple[int, str, str]] = set()
    if scope == "general":
        groups = runtime_binding_groups_for_dimension(2)
        for action in groups.get("system", {}):
            expected.add((2, "system", action))
        return expected
    if scope == "all":
        shared_system = runtime_binding_groups_for_dimension(2).get("system", {})
        for action in shared_system:
            expected.add((2, "system", action))
        for dimension in (2, 3, 4):
            groups = runtime_binding_groups_for_dimension(dimension)
            for group in ("game", "camera"):
                for action in groups.get(group, {}):
                    expected.add((dimension, group, action))
        return expected
    dimension = int(scope[0])
    groups = runtime_binding_groups_for_dimension(dimension)
    for group in ("game", "camera"):
        for action in groups.get(group, {}):
            expected.add((dimension, group, action))
    return expected


class TestKeybindingsMenuModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_3d_scope_splits_translation_and_rotation(self) -> None:
        headers = _header_titles("3d")
        self.assertIn("3D Gameplay / Translation", headers)
        self.assertIn("3D Gameplay / Rotation", headers)
        self.assertIn("3D Camera / View", headers)
        self.assertNotIn("3D General / System", headers)

    def test_4d_scope_splits_translation_and_rotation(self) -> None:
        headers = _header_titles("4d")
        self.assertIn("4D Gameplay / Translation", headers)
        self.assertIn("4D Gameplay / Rotation", headers)
        self.assertIn("4D Camera / View", headers)
        self.assertNotIn("4D General / System", headers)

    def test_general_scope_contains_shared_system_only(self) -> None:
        headers = _header_titles("general")
        self.assertEqual(headers, ["General / System"])

    def test_all_scope_has_shared_system_and_no_slice_sections(self) -> None:
        headers = _header_titles("all")
        self.assertIn("General / System (shared)", headers)
        self.assertTrue(any("Gameplay / Translation" in title for title in headers))
        self.assertTrue(any("Gameplay / Rotation" in title for title in headers))
        self.assertFalse(any("slice" in title.lower() for title in headers))

    def test_scope_rows_match_runtime_binding_groups(self) -> None:
        for scope in ("general", "2d", "3d", "4d", "all"):
            self.assertEqual(
                _binding_tuples(scope),
                _expected_scope_bindings(scope),
                msg=f"scope binding rows drifted for {scope}",
            )
