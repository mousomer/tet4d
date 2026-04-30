from __future__ import annotations

import json
import unittest
from pathlib import Path

from tet4d.engine.runtime.menu_structure_schema import validate_structure_payload


def _structure_payload() -> dict[str, object]:
    path = Path(__file__).resolve().parents[3] / "config" / "menu" / "structure.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _menu_item(payload: dict[str, object], *, menu_id: str, item_id: str) -> dict[str, object]:
    menus = payload.get("menus", {})
    if not isinstance(menus, dict):
        raise TypeError("structure payload missing menus object")
    menu = menus.get(menu_id)
    if not isinstance(menu, dict):
        raise KeyError(menu_id)
    items = menu.get("items", [])
    if not isinstance(items, list):
        raise TypeError(f"{menu_id}.items must be a list")
    for item in items:
        if isinstance(item, dict) and str(item.get("id", "")).strip().lower() == item_id:
            return item
    raise KeyError(f"{menu_id}:{item_id}")


class TestMenuStructureStorageMetadataValidation(unittest.TestCase):
    def test_selector_rejects_non_enum_semantic_type(self) -> None:
        payload = _structure_payload()
        item = _menu_item(payload, menu_id="settings_gameplay", item_id="game_random_mode")
        item["semantic_type"] = "int"
        with self.assertRaises(RuntimeError):
            validate_structure_payload(payload)  # type: ignore[arg-type]

    def test_slider_rejects_enum_semantic_type(self) -> None:
        payload = _structure_payload()
        item = _menu_item(
            payload,
            menu_id="settings_gameplay",
            item_id="rotation_animation_duration_ms_2d",
        )
        item["semantic_type"] = "enum"
        with self.assertRaises(RuntimeError):
            validate_structure_payload(payload)  # type: ignore[arg-type]

    def test_toggle_rejects_int_index_storage_type(self) -> None:
        payload = _structure_payload()
        item = _menu_item(
            payload,
            menu_id="settings_board_setup_defaults",
            item_id="game_topology_advanced",
        )
        item["storage_type"] = "int_index"
        with self.assertRaises(RuntimeError):
            validate_structure_payload(payload)  # type: ignore[arg-type]

    def test_numeric_rejects_int_index_storage_type(self) -> None:
        payload = _structure_payload()
        item = _menu_item(
            payload,
            menu_id="settings_gameplay",
            item_id="rotation_animation_duration_ms_2d",
        )
        item["storage_type"] = "int_index"
        with self.assertRaises(RuntimeError):
            validate_structure_payload(payload)  # type: ignore[arg-type]

    def test_numeric_rejects_int_bool_legacy_storage_type(self) -> None:
        payload = _structure_payload()
        item = _menu_item(
            payload,
            menu_id="settings_gameplay",
            item_id="rotation_animation_duration_ms_2d",
        )
        item["legacy_storage_type"] = "int_bool"
        with self.assertRaises(RuntimeError):
            validate_structure_payload(payload)  # type: ignore[arg-type]

