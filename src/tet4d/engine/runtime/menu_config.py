from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from .menu_structure_schema import (
    collect_actions_for_menu_ids,
    collect_reachable_menu_ids,
    resolve_field_max,
    validate_structure_payload,
)
from .project_config import project_root_path
from .runtime_config import playbot_budget_table_for_ndim
from .settings_schema import (
    MODE_KEYS,
    as_non_empty_string,
    mode_key_for_dimension,
    read_json_object_or_raise,
    validate_defaults_payload,
)

FieldSpec = tuple[str, str, int, int]

CONFIG_DIR = project_root_path() / "config" / "menu"
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"
STRUCTURE_FILE = CONFIG_DIR / "structure.json"


def _read_json_payload(path: Path) -> dict[str, Any]:
    payload = read_json_object_or_raise(path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _runtime_budget_for_mode(mode_key: str) -> int:
    ndims = {"2d": 2, "3d": 3, "4d": 4}[mode_key]
    return int(playbot_budget_table_for_ndim(ndims)[1])


@lru_cache(maxsize=1)
def _defaults_payload() -> dict[str, Any]:
    return validate_defaults_payload(
        _read_json_payload(DEFAULTS_FILE),
        runtime_budget_for_mode_fn=_runtime_budget_for_mode,
    )


@lru_cache(maxsize=1)
def _structure_payload() -> dict[str, Any]:
    return validate_structure_payload(_read_json_payload(STRUCTURE_FILE))


def default_settings_payload() -> dict[str, Any]:
    return deepcopy(_defaults_payload())


def menu_graph() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["menus"])


def menu_entrypoints() -> dict[str, str]:
    return deepcopy(_structure_payload()["menu_entrypoints"])


def launcher_menu_id() -> str:
    return str(_structure_payload()["menu_entrypoints"]["launcher"])


def pause_menu_id() -> str:
    return str(_structure_payload()["menu_entrypoints"]["pause"])


def menu_definition(menu_id: str) -> dict[str, Any]:
    clean_menu_id = as_non_empty_string(menu_id, path="menu_id").lower()
    menu = _structure_payload()["menus"].get(clean_menu_id)
    if menu is None:
        raise KeyError(f"Unknown menu id: {clean_menu_id}")
    return deepcopy(menu)


def menu_items(menu_id: str) -> tuple[dict[str, str], ...]:
    return tuple(menu_definition(menu_id)["items"])


def reachable_action_ids(start_menu_id: str) -> tuple[str, ...]:
    clean_start = as_non_empty_string(start_menu_id, path="start_menu_id").lower()
    payload = _structure_payload()
    reachable_menus = collect_reachable_menu_ids(
        payload["menus"],
        start_menu_id=clean_start,
    )
    actions = collect_actions_for_menu_ids(payload["menus"], menu_ids=reachable_menus)
    return tuple(sorted(actions))


def launcher_menu_items() -> tuple[tuple[str, str], ...]:
    return tuple(_structure_payload()["launcher_menu"])


def settings_hub_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["settings_hub_rows"])


def bot_options_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["bot_options_rows"])


def settings_hub_layout_rows() -> tuple[tuple[str, str, str], ...]:
    rows = _structure_payload()["settings_hub_layout_rows"]
    return tuple((row["kind"], row["label"], row["row_key"]) for row in rows)


def settings_option_labels() -> dict[str, tuple[str, ...]]:
    return deepcopy(_structure_payload().get("settings_option_labels", {}))


def pause_menu_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["pause_menu_rows"])


def pause_menu_actions() -> tuple[str, ...]:
    return tuple(_structure_payload()["pause_menu_actions"])


def setup_fields_for_dimension(
    dimension: int,
    *,
    piece_set_max: int = 0,
    topology_profile_max: int = 0,
) -> list[FieldSpec]:
    mode_key = mode_key_for_dimension(dimension)
    raw_fields = _structure_payload()["setup_fields"][mode_key]
    fields: list[FieldSpec] = []
    for raw_field in raw_fields:
        label = raw_field["label"]
        attr_name = raw_field["attr"]
        min_val = raw_field["min"]
        max_val = resolve_field_max(
            raw_field["max"],
            piece_set_max,
            topology_profile_max,
            mode_key,
            attr_name,
        )
        if min_val > max_val:
            raise RuntimeError(
                f"Invalid field bounds for {mode_key}.{attr_name}: "
                f"min {min_val} > max {max_val}"
            )
        fields.append((label, attr_name, min_val, max_val))
    return fields


def keybinding_category_docs() -> dict[str, Any]:
    return deepcopy(_structure_payload()["keybinding_category_docs"])


def settings_category_docs() -> tuple[dict[str, str], ...]:
    return deepcopy(_structure_payload()["settings_category_docs"])


def settings_split_rules() -> dict[str, Any]:
    return deepcopy(_structure_payload()["settings_split_rules"])


def settings_category_metrics() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["settings_category_metrics"])


def settings_top_level_categories() -> tuple[dict[str, str], ...]:
    payload = _structure_payload()
    docs: tuple[dict[str, str], ...] = payload["settings_category_docs"]
    metrics: dict[str, dict[str, Any]] = payload.get("settings_category_metrics", {})
    if not metrics:
        fallback_rows = set(payload["settings_hub_rows"])
        return tuple(entry for entry in docs if entry["label"] in fallback_rows)
    top_level_ids = {
        category_id
        for category_id, entry in metrics.items()
        if bool(entry.get("top_level"))
    }
    return tuple(entry for entry in docs if entry["id"] in top_level_ids)


def setup_hints_for_dimension(dimension: int) -> tuple[str, ...]:
    mode_key = mode_key_for_dimension(dimension)
    payload = _structure_payload()
    hints = payload.get("setup_hints", {})
    if isinstance(hints, dict):
        mode_hints = hints.get(mode_key)
        if isinstance(mode_hints, list) and all(isinstance(h, str) for h in mode_hints):
            return tuple(mode_hints)
    return tuple()


@lru_cache(maxsize=1)
def _bot_defaults_by_mode() -> dict[str, dict[str, int]]:
    defaults = _defaults_payload()
    settings = defaults["settings"]
    bot_defaults: dict[str, dict[str, int]] = {}
    for mode_key in MODE_KEYS:
        mode_settings = settings[mode_key]
        bot_values = {
            attr_name: value
            for attr_name, value in mode_settings.items()
            if attr_name.startswith("bot_")
        }
        if not bot_values:
            raise RuntimeError(f"defaults.settings.{mode_key} must contain bot_* keys")
        bot_defaults[mode_key] = bot_values
    return bot_defaults


def bot_defaults_by_mode() -> dict[str, dict[str, int]]:
    return deepcopy(_bot_defaults_by_mode())
