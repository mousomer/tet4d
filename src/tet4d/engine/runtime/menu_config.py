from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..core.rng import RNG_MODE_OPTIONS
from .menu_field_spec import FieldOption, FieldSpec
from .endgame_presets import (
    ENDGAME_BOUNDARY_RESPONSES,
    ENDGAME_PARTICLE_COLLISION_MODES,
    ENDGAME_PRESET_IDS,
)
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
from tet4d.engine.gameplay.pieces2d import PIECE_SET_2D_OPTIONS, piece_set_2d_label
from tet4d.engine.gameplay.pieces_nd import piece_set_label, piece_set_options_for_dimension

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
    preset_labels = payload["settings_option_labels"].get("game_endgame_preset")
    if preset_labels is None:
        raise RuntimeError(
            "structure.settings_option_labels must include game_endgame_preset labels"
        )
    if len(preset_labels) != len(ENDGAME_PRESET_IDS):
        raise RuntimeError(
            "structure.settings_option_labels.game_endgame_preset must match configured endgame presets"
        )
    boundary_response_labels = payload["settings_option_labels"].get(
        "game_endgame_boundary_response"
    )
    if boundary_response_labels is None:
        raise RuntimeError(
            "structure.settings_option_labels must include game_endgame_boundary_response labels"
        )
    if len(boundary_response_labels) != len(ENDGAME_BOUNDARY_RESPONSES):
        raise RuntimeError(
            "structure.settings_option_labels.game_endgame_boundary_response must match configured endgame boundary responses"
        )
    particle_collision_labels = payload["settings_option_labels"].get(
        "game_endgame_particle_collisions"
    )
    if particle_collision_labels is None:
        raise RuntimeError(
            "structure.settings_option_labels must include game_endgame_particle_collisions labels"
        )
    if len(particle_collision_labels) != len(ENDGAME_PARTICLE_COLLISION_MODES):
        raise RuntimeError(
            "structure.settings_option_labels.game_endgame_particle_collisions must match configured endgame particle collision modes"
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


def authored_menu_graph() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["authored_menus"])


def menu_graph() -> dict[str, dict[str, Any]]:
    return deepcopy(_structure_payload()["runtime_menus"])


def launcher_menu_id() -> str:
    return str(_structure_payload()["runtime_menu_entrypoints"]["launcher"])


def pause_menu_id() -> str:
    return str(_structure_payload()["runtime_menu_entrypoints"]["pause"])


def settings_menu_id() -> str:
    return str(_structure_payload()["runtime_menu_entrypoints"]["settings"])


def keybindings_menu_id() -> str:
    return str(_structure_payload()["runtime_menu_entrypoints"]["keybindings"])


def authored_menu_definition(menu_id: str) -> dict[str, Any]:
    clean_menu_id = as_non_empty_string(menu_id, path="menu_id").lower()
    menu = _structure_payload()["authored_menus"].get(clean_menu_id)
    if menu is None:
        raise KeyError(f"Unknown authored menu id: {clean_menu_id}")
    return deepcopy(menu)


def authored_menu_items(menu_id: str) -> tuple[dict[str, str], ...]:
    return tuple(authored_menu_definition(menu_id)["items"])


def runtime_menu_id_for_item(item_id: str) -> str | None:
    clean_item_id = as_non_empty_string(item_id, path="item_id").lower()
    for menu_id, menu in _structure_payload()["runtime_menus"].items():
        items = menu.get("items", ())
        for item in items:
            if menu_item_id(item) == clean_item_id:
                return str(menu_id)
    return None


def resolve_runtime_menu_id(
    menu_id: str,
    *,
    item_id: str | None = None,
    fallback_menu_id: str | None = None,
) -> str:
    clean_menu_id = as_non_empty_string(menu_id, path="menu_id").lower()
    runtime_menus = _structure_payload()["runtime_menus"]
    if clean_menu_id in runtime_menus:
        return clean_menu_id

    clean_item_id = str(item_id or "").strip().lower()
    if clean_item_id:
        item_menu_id = runtime_menu_id_for_item(clean_item_id)
        if item_menu_id is not None:
            return item_menu_id

    compile_result = _structure_payload()["runtime_menu_compile_results"].get(clean_menu_id)
    if compile_result is not None:
        target_menu_id = str(getattr(compile_result, "target_menu_id", "")).strip().lower()
        if target_menu_id in runtime_menus:
            return target_menu_id
        inline_items = tuple(getattr(compile_result, "inline_items", ()))
        for item in inline_items:
            item_menu_id = runtime_menu_id_for_item(menu_item_id(item))
            if item_menu_id is not None:
                return item_menu_id

    if fallback_menu_id:
        fallback = as_non_empty_string(fallback_menu_id, path="fallback_menu_id").lower()
        if fallback in runtime_menus:
            return fallback
    return settings_menu_id()


def menu_definition(menu_id: str) -> dict[str, Any]:
    clean_menu_id = as_non_empty_string(menu_id, path="menu_id").lower()
    menu = _structure_payload()["runtime_menus"].get(clean_menu_id)
    if menu is None:
        raise KeyError(f"Unknown menu id: {clean_menu_id}")
    return deepcopy(menu)


def menu_items(menu_id: str) -> tuple[dict[str, str], ...]:
    return tuple(menu_definition(menu_id)["items"])


def reachable_action_ids(start_menu_id: str) -> tuple[str, ...]:
    clean_start = as_non_empty_string(start_menu_id, path="start_menu_id").lower()
    payload = _structure_payload()
    reachable_menus = collect_reachable_menu_ids(
        payload["runtime_menus"],
        start_menu_id=clean_start,
    )
    actions = collect_actions_for_menu_ids(
        payload["runtime_menus"],
        menu_ids=reachable_menus,
    )
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


def bot_options_rows() -> tuple[str, ...]:
    return tuple(_structure_payload()["bot_options_rows"])


def menu_item_id(item: dict[str, Any]) -> str:
    return str(item.get("id", "")).strip().lower()


def settings_help_entries() -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    for category in settings_top_level_categories():
        entries.append(
            {
                "id": str(category["id"]),
                "label": str(category["label"]),
                "description": str(category["description"]),
            }
        )
    return tuple(entries)


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
        label = str(raw_field["label"])
        attr_name = str(raw_field["attr"])
        semantic_type = str(raw_field["semantic_type"])
        control_family = str(raw_field["control"])
        if semantic_type == "enum":
            literal_options = tuple(str(option) for option in raw_field.get("options", ()))
            options_source = str(raw_field.get("options_source", "")).strip().lower()
            option_labels = literal_options
            if options_source:
                if options_source != "piece_set_labels":
                    raise RuntimeError(
                        f"Unknown setup field options_source for {mode_key}.{attr_name}: {options_source}"
                    )
                if dimension == 2:
                    option_labels = tuple(
                        piece_set_2d_label(piece_set_id)
                        for piece_set_id in PIECE_SET_2D_OPTIONS
                    )
                else:
                    option_labels = tuple(
                        piece_set_label(piece_set_id)
                        for piece_set_id in piece_set_options_for_dimension(dimension)
                    )
            if not option_labels:
                raise RuntimeError(
                    f"Enum setup field {mode_key}.{attr_name} must resolve at least one option"
                )
            fields.append(
                FieldSpec(
                    label=label,
                    attr_name=attr_name,
                    semantic_type="enum",
                    control_family="selector",
                    options=tuple(
                        FieldOption(value=index, label=option_label)
                        for index, option_label in enumerate(option_labels)
                    ),
                )
            )
            continue
        if semantic_type == "bool":
            fields.append(
                FieldSpec(
                    label=label,
                    attr_name=attr_name,
                    semantic_type="bool",
                    control_family="toggle",
                )
            )
            continue
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
        fields.append(
            FieldSpec(
                label=label,
                attr_name=attr_name,
                semantic_type=str(semantic_type),
                control_family=str(control_family),
                min_value=min_val,
                max_value=max_val,
            )
        )
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
        return [field for field in fields if field.attr_name not in hidden]
    if dimension >= 3:
        fields = [field for field in fields if field.attr_name != "topology_profile_index"]
    if bool(topology_advanced):
        return fields
    return [field for field in fields if field.attr_name != "topology_profile_index"]


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
    top_level: list[dict[str, str]] = []
    for item in menu_items(settings_menu_id()):
        if str(item.get("type", "")).lower() != "submenu":
            continue
        target_menu_id = str(item.get("menu_id", "")).strip().lower()
        target_menu = menu_definition(target_menu_id)
        top_level.append(
            {
                "id": menu_item_id(item),
                "label": str(item["label"]),
                "title": str(target_menu["title"]),
                "description": str(item.get("description", "")).strip(),
                "menu_id": target_menu_id,
            }
        )
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
