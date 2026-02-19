from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment guard
    raise unittest.SkipTest("pygame-ce is required for keybinding menu model tests") from exc

from tetris_nd.keybindings_menu_model import rows_for_scope


def _header_titles(scope: str) -> list[str]:
    rendered_rows, _ = rows_for_scope(scope)
    return [
        row.text
        for row in rendered_rows
        if row.kind == "header" and row.text and not row.text.startswith("  ")
    ]


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
        self.assertIn("3D General / System", headers)

    def test_4d_scope_splits_translation_and_rotation(self) -> None:
        headers = _header_titles("4d")
        self.assertIn("4D Gameplay / Translation", headers)
        self.assertIn("4D Gameplay / Rotation", headers)
        self.assertIn("4D Camera / View", headers)
        self.assertIn("4D General / System", headers)

    def test_all_scope_has_shared_system_and_no_slice_sections(self) -> None:
        headers = _header_titles("all")
        self.assertIn("General / System (shared)", headers)
        self.assertTrue(any("Gameplay / Translation" in title for title in headers))
        self.assertTrue(any("Gameplay / Rotation" in title for title in headers))
        self.assertFalse(any("slice" in title.lower() for title in headers))

