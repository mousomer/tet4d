from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..core.rng import RNG_MODE_OPTIONS
from .menu_structure.graph import (
    collect_actions_for_menu_ids,
    collect_reachable_menu_ids,
)
from .menu_structure_schema import resolve_field_max, validate_structure_payload
from .project_config import project_root_path
from .runtime_config import kick_level_names, playbot_budget_table_for_ndim
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
_BOARD_DIMENSION_FIELDS = ("width", "height", "depth", "fourth")
_EXPLORER_BOARD_DIMENSION_FIELDS = (
    "explorer_width",
    "explorer_height",
    "explorer_depth",
    "explorer_fourth",
)


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
    defaults = validate_defaults_payload(
        _read_json_payload(DEFAULTS_FILE),
        runtime_budget_for_mode_fn=_runtime_budget_for_mode,
    )
    max_kick_index = max(0, len(kick_level_names()) - 1)
    for mode_key in MODE_KEYS:
        kick_index = int(defaults["settings"][mode_key].get("kick_level_index", 0))
        if not (0 <= kick_index <= max_kick_index):
            raise RuntimeError(
                f"defaults.settings.{mode_key}.kick_level_index must be within configured kick levels"
            )
    return defaults


@lru_cache(maxsize=1)
def _structure_payload() -> dict[str, Any]:
    payload = validate_structure_payload(_read_json_payload(STRUCTURE_FILE))
    kick_labels = payload["settings_option_labels"].get("game_kick_level")
    if kick_labels is None:
        raise RuntimeError(
            "structure.settings_option_labels must include game_kick_level labels"
        )
    if len(kick_labels) != len(kick_level_names()):
        raise RuntimeError(
            "structure.settings_option_labels.game_kick_level must match configured kick levels"
        )
    return payload


def default_settings_payload() -> dict[str, Any]:
    return deepcopy(_defaults_payload())


def explorer_default_board_dims(dimension: int) -> tuple[int, ...]:
    dim = int(dimension)
    if not 2 <= dim <= len(_BOARD_DIMENSION_FIELDS):
        raise ValueError(f"unsupported explorer dimension: {dimension}")
    mode_key = mode_key_for_dimension(dim)
    mode_defaults = _defaults_payload()["settings"][mode_key]
    dims: list[int] = []
    for attr_name in _EXPLORER_BOARD_DIMENSION_FIELDS[:dim]:
        raw_value = mode_defaults.get(attr_name)
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise RuntimeError(
                f"defaults.settings.{mode_key}.{attr_name} must be a positive integer"
            )
        value = int(raw_value)
        if value <= 0:
            raise RuntimeError(f"defaults.settings.{mode_key}.{attr_name} must be > 0")
        dims.append(value)
    return tuple(dims)


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
    normalized: list[tuple[str, str]] = []
    for item in menu_items(launcher_menu_id()):
        label = str(item.get("label", ""))
        item_type = str(item.get("type", ""))
        if item_type == "action":
            action = str(item.get("action_id", ""))
        elif item_type == "submenu":
            action = label.strip().lower().replace(" ", "_")
        else:
            continue
        if action:
            normalized.append((action, label))
    return tuple(normalized)


def launcher_subtitles() -> dict[str, str]:
    return deepcopy(_structure_payload()["launcher_subtitles"])


def launcher_route_actions() -> dict[str, str]:
    return deepcopy(_structure_payload()["launcher_route_actions"])


def branding_copy() -> dict[str, str]:
    return deepcopy(_structure_payload()["branding"])


def ui_copy_payload() -> dict[str, Any]:
    return deepcopy(_structure_payload()["ui_copy"])


def ui_copy_section(section: str) -> dict[str, Any]:
    clean_section = as_non_empty_string(section, path="section").lower()
    copy_payload = _structure_payload()["ui_copy"]
    copy_section = copy_payload.get(clean_section)
    if not isinstance(copy_section, dict):
        raise KeyError(f"Unknown ui_copy section: {clean_section}")
    return deepcopy(copy_section)


def settings_hub_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["settings_hub_rows"])


def bot_options_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["bot_options_rows"])


def settings_hub_layout_rows() -> tuple[tuple[str, str, str], ...]:
    rows = _structure_payload()["settings_hub_layout_rows"]
    return tuple((row["kind"], row["label"], row["row_key"]) for row in rows)


def settings_sections() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["settings_sections"])


def settings_section(section_id: str) -> dict[str, Any]:
    clean_section_id = as_non_empty_string(section_id, path="section_id").lower()
    section = _structure_payload()["settings_sections"].get(clean_section_id)
    if not isinstance(section, dict):
        raise KeyError(f"Unknown settings section: {clean_section_id}")
    return deepcopy(section)


def settings_help_entries() -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    for category in settings_top_level_categories():
        section = settings_section(str(category["id"]))
        entries.append(
            {
                "id": str(category["id"]),
                "label": str(category["label"]),
                "description": str(section["subtitle"]),
            }
        )
    return tuple(entries)


def launcher_settings_routes() -> dict[str, dict[str, str]]:
    return deepcopy(_structure_payload()["launcher_settings_routes"])


def launcher_settings_route(action_id: str) -> dict[str, str]:
    clean_action_id = as_non_empty_string(action_id, path="action_id").lower()
    route = _structure_payload()["launcher_settings_routes"].get(clean_action_id)
    if not isinstance(route, dict):
        raise KeyError(f"Unknown launcher settings action: {clean_action_id}")
    return deepcopy(route)


def settings_option_labels() -> dict[str, tuple[str, ...]]:
    return deepcopy(_structure_payload().get("settings_option_labels", {}))


def random_mode_ids() -> tuple[str, ...]:
    return tuple(str(mode_id) for mode_id in RNG_MODE_OPTIONS)


def random_mode_id_from_index(index: int) -> str:
    mode_ids = random_mode_ids()
    safe_index = max(0, min(len(mode_ids) - 1, int(index)))
    return mode_ids[safe_index]


def random_mode_label_for_index(index: int) -> str:
    labels = tuple(settings_option_labels()["game_random_mode"])
    safe_index = max(0, min(len(labels) - 1, int(index)))
    return labels[safe_index]


def kick_level_name_for_index(index: int) -> str:
    names = kick_level_names()
    safe_index = max(0, min(len(names) - 1, int(index)))
    return names[safe_index]


def pause_menu_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["pause_menu_rows"])


def pause_menu_actions() -> tuple[str, ...]:
    return tuple(_structure_payload()["pause_menu_actions"])


def pause_copy() -> dict[str, Any]:
    copy = _structure_payload()["pause_copy"]
    return {
        "subtitle_template": str(copy["subtitle_template"]),
        "hints": tuple(copy["hints"]),
    }


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


def setup_fields_for_settings(
    dimension: int,
    *,
    piece_set_max: int = 0,
    topology_profile_max: int = 0,
    topology_advanced: bool = False,
    exploration_mode: bool = False,
) -> list[FieldSpec]:
    fields = setup_fields_for_dimension(
        dimension,
        piece_set_max=piece_set_max,
        topology_profile_max=topology_profile_max,
    )
    if bool(exploration_mode):
        hidden = {"topology_mode", "topology_advanced", "topology_profile_index"}
        return [field for field in fields if field[1] not in hidden]
    if dimension >= 3:
        fields = [field for field in fields if field[1] != "topology_profile_index"]
    if bool(topology_advanced):
        return fields
    return [field for field in fields if field[1] != "topology_profile_index"]


def keybinding_category_docs() -> dict[str, Any]:
    from tet4d.engine.ui_logic.keybindings_catalog import (
        binding_group_docs,
        binding_scope_order,
    )

    return {
        "scope_order": binding_scope_order(),
        "groups": binding_group_docs(),
    }


def settings_category_docs() -> tuple[dict[str, str], ...]:
    return deepcopy(_structure_payload()["settings_category_docs"])


def settings_split_rules() -> dict[str, Any]:
    return deepcopy(_structure_payload()["settings_split_rules"])


def settings_category_metrics() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["settings_category_metrics"])


def settings_top_level_categories() -> tuple[dict[str, str], ...]:
    payload = _structure_payload()
    sections: dict[str, dict[str, Any]] = payload["settings_sections"]
    layout_rows: tuple[dict[str, str], ...] = payload["settings_hub_layout_rows"]
    layout_header_order = [
        row["label"] for row in layout_rows if row["kind"] == "header"
    ]
    header_index = {label: idx for idx, label in enumerate(layout_header_order)}
    top_level: list[dict[str, str]] = []
    for section_id, section in sections.items():
        headers = tuple(str(label) for label in section["headers"])
        if not headers:
            continue
        first_header = headers[0]
        top_level.append(
            {
                "id": str(section_id),
                "label": first_header,
                "title": str(section["title"]),
            }
        )
    top_level.sort(key=lambda entry: header_index.get(entry["label"], 10**9))
    return tuple(top_level)


def setup_hints_for_dimension(dimension: int) -> tuple[str, ...]:
    mode_key = mode_key_for_dimension(dimension)
    return tuple(_structure_payload()["setup_hints"][mode_key])


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
