from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
CONFIG_ROOT = PROJECT_ROOT / "config"
CONFIG_DOC_PATH = PROJECT_ROOT / "docs" / "CONFIGURATION_REFERENCE.md"
USER_SETTINGS_DOC_PATH = PROJECT_ROOT / "docs" / "USER_SETTINGS_REFERENCE.md"
CONFIG_SCHEMA_DIR = CONFIG_ROOT / "schema"
MENU_SETTINGS_SCHEMA_PATH = CONFIG_SCHEMA_DIR / "menu_settings.schema.json"
KEYBINDINGS_DEFAULTS_PATH = CONFIG_ROOT / "keybindings" / "defaults.json"
MAX_EXAMPLES = 3
MAX_LITERAL_LENGTH = 72

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@dataclass
class PathEntry:
    path: str
    node_kind: str
    scalar_kinds: set[str] = field(default_factory=set)
    array_item_kinds: set[str] = field(default_factory=set)
    examples: list[str] = field(default_factory=list)
    observation_count: int = 0

    def add_example(self, value: object) -> None:
        literal = _format_literal(value)
        if literal not in self.examples and len(self.examples) < MAX_EXAMPLES:
            self.examples.append(literal)


@dataclass(frozen=True)
class ConfigDocTarget:
    rel_path: str
    kind: str


@dataclass(frozen=True)
class UserSettingsOptionLabelSet:
    active_profile_labels: tuple[str, ...]
    random_mode_labels: tuple[str, ...] | None
    kick_level_labels: tuple[str, ...] | None
    topology_mode_labels: tuple[str, ...]
    bot_mode_labels: tuple[str, ...]
    bot_profile_labels: tuple[str, ...]
    bot_algorithm_labels: tuple[str, ...]
    piece_set_labels_by_dimension: dict[int, tuple[str, ...]]
    topology_profile_labels_by_dimension: dict[int, tuple[str, ...]]


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _config_targets() -> list[ConfigDocTarget]:
    targets: list[ConfigDocTarget] = []
    for path in sorted(CONFIG_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.is_relative_to(CONFIG_SCHEMA_DIR):
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if path.suffix == ".json":
            targets.append(ConfigDocTarget(rel_path=rel, kind="json"))
            continue
        if path.suffix == ".txt":
            targets.append(ConfigDocTarget(rel_path=rel, kind="text"))
    return targets


def _json_kind(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _format_literal(value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if len(rendered) <= MAX_LITERAL_LENGTH:
        return rendered
    return rendered[: MAX_LITERAL_LENGTH - 3] + "..."


def _add_scalar_entry(
    entries: dict[str, PathEntry],
    path: str,
    value: object,
) -> None:
    entry = entries.setdefault(path, PathEntry(path=path, node_kind="scalar"))
    entry.scalar_kinds.add(_json_kind(value))
    entry.observation_count += 1
    entry.add_example(value)


def _add_array_entry(
    entries: dict[str, PathEntry],
    path: str,
    items: list[object],
) -> None:
    entry = entries.setdefault(path, PathEntry(path=path, node_kind="array"))
    if not items:
        entry.array_item_kinds.add("empty")
        return
    for item in items:
        kind = _json_kind(item)
        entry.array_item_kinds.add(kind)
        if kind not in {"array", "object"}:
            entry.observation_count += 1
            entry.scalar_kinds.add(kind)
            entry.add_example(item)


def _collect_json_entries(payload: object) -> dict[str, PathEntry]:
    entries: dict[str, PathEntry] = {}

    def walk(node: object, prefix: str) -> None:
        if isinstance(node, dict):
            for key in sorted(node):
                next_prefix = f"{prefix}.{key}" if prefix else key
                walk(node[key], next_prefix)
            return
        if isinstance(node, list):
            array_path = f"{prefix}[]" if prefix else "[]"
            _add_array_entry(entries, array_path, node)
            for item in node:
                if isinstance(item, (dict, list)):
                    walk(item, array_path)
            return
        _add_scalar_entry(entries, prefix, node)

    walk(payload, "")
    return entries


def _top_level_keys(payload: object) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    return tuple(sorted(payload))


def _render_scalar_entry(entry: PathEntry) -> str:
    kind_text = ", ".join(sorted(entry.scalar_kinds))
    if entry.observation_count <= 1 and len(entry.examples) == 1:
        return f"- `{entry.path}`: `{entry.examples[0]}` (`{kind_text}`)"
    if entry.examples:
        examples = ", ".join(f"`{value}`" for value in entry.examples)
        return f"- `{entry.path}`: varies (`{kind_text}`); examples: {examples}"
    return f"- `{entry.path}`: varies (`{kind_text}`)"


def _render_array_entry(entry: PathEntry) -> str:
    item_text = ", ".join(sorted(entry.array_item_kinds)) or "empty"
    if entry.examples:
        examples = ", ".join(f"`{value}`" for value in entry.examples)
        return f"- `{entry.path}`: array[`{item_text}`]; examples: {examples}"
    return f"- `{entry.path}`: array[`{item_text}`]"


def _render_json_target(target: ConfigDocTarget) -> str:
    path = PROJECT_ROOT / target.rel_path
    payload = _load_json(path)
    entries = _collect_json_entries(payload)
    lines = [f"### `{target.rel_path}`"]
    top_level = _top_level_keys(payload)
    if top_level:
        joined = ", ".join(f"`{key}`" for key in top_level)
        lines.append(f"Top-level keys: {joined}")
    lines.append("Parameters:")
    for key in sorted(entries):
        entry = entries[key]
        if entry.node_kind == "array":
            lines.append(_render_array_entry(entry))
        else:
            lines.append(_render_scalar_entry(entry))
    lines.append("")
    return "\n".join(lines)


def _render_text_target(target: ConfigDocTarget) -> str:
    path = PROJECT_ROOT / target.rel_path
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rendered = [f"### `{target.rel_path}`", "Entries:"]
    for line in lines:
        rendered.append(f"- `{line}`")
    rendered.append("")
    return "\n".join(rendered)


def render_configuration_reference() -> str:
    targets = _config_targets()
    lines = [
        "# Configuration Reference",
        "",
        "Generated from repo config sources by "
        "`tools/governance/generate_configuration_reference.py`.",
        "Do not edit this file manually.",
        "",
        "Coverage:",
        "- Includes source-controlled config assets under `config/`.",
        "- Excludes `config/schema/`, which defines validation contracts rather "
        "than runtime parameter values.",
        "- User override state lives in `state/menu_settings.json`; its default "
        "shape is driven by `config/menu/defaults.json` and the menu settings "
        "schema.",
        "",
        "## Included files",
    ]
    for target in targets:
        lines.append(f"- `{target.rel_path}`")
    lines.append("")
    lines.append("## Parameters")
    lines.append("")
    for target in targets:
        if target.kind == "json":
            lines.append(_render_json_target(target))
        else:
            lines.append(_render_text_target(target))
    return "\n".join(lines).rstrip() + "\n"


def _menu_settings_schema_payload() -> dict[str, object]:
    payload = _load_json(MENU_SETTINGS_SCHEMA_PATH)
    if not isinstance(payload, dict):
        raise RuntimeError("menu settings schema must be a JSON object")
    return payload


def _user_settings_defaults_payload() -> dict[str, object]:
    from tet4d.engine.runtime.menu_config import default_settings_payload

    return default_settings_payload()


def _keybindings_defaults_payload() -> dict[str, object]:
    payload = _load_json(KEYBINDINGS_DEFAULTS_PATH)
    if not isinstance(payload, dict):
        raise RuntimeError("keybindings defaults must be a JSON object")
    return payload


def _settings_option_labels_payload() -> dict[str, tuple[str, ...]]:
    from tet4d.engine.runtime.menu_config import settings_option_labels

    return settings_option_labels()


def _settings_category_docs_payload() -> dict[str, dict[str, str]]:
    from tet4d.engine.runtime.menu_config import settings_category_docs

    rows = settings_category_docs()
    docs: dict[str, dict[str, str]] = {}
    for row in rows:
        category_id = str(row["id"])
        docs[category_id] = {
            "label": str(row["label"]),
            "description": str(row["description"]),
        }
    return docs


def _keybinding_category_docs_payload() -> dict[str, object]:
    from tet4d.engine.runtime.menu_config import keybinding_category_docs

    payload = keybinding_category_docs()
    if not isinstance(payload, dict):
        raise RuntimeError("keybinding category docs must be a mapping")
    return payload


def _topology_mode_labels() -> tuple[str, ...]:
    from tet4d.engine.gameplay.topology import (
        TOPOLOGY_MODE_OPTIONS,
        topology_mode_label,
    )

    return tuple(topology_mode_label(mode) for mode in TOPOLOGY_MODE_OPTIONS)


def _bot_mode_labels() -> tuple[str, ...]:
    from tet4d.ai.playbot.types import BOT_MODE_OPTIONS, bot_mode_label

    return tuple(bot_mode_label(mode) for mode in BOT_MODE_OPTIONS)


def _bot_profile_labels() -> tuple[str, ...]:
    from tet4d.ai.playbot.types import (
        BOT_PLANNER_PROFILE_OPTIONS,
        bot_planner_profile_label,
    )

    return tuple(
        bot_planner_profile_label(profile) for profile in BOT_PLANNER_PROFILE_OPTIONS
    )


def _bot_algorithm_labels() -> tuple[str, ...]:
    from tet4d.ai.playbot.types import (
        BOT_PLANNER_ALGORITHM_OPTIONS,
        bot_planner_algorithm_label,
    )

    return tuple(
        bot_planner_algorithm_label(algorithm)
        for algorithm in BOT_PLANNER_ALGORITHM_OPTIONS
    )


def _piece_set_labels_by_dimension() -> dict[int, tuple[str, ...]]:
    from tet4d.engine.gameplay.api import (
        piece_set_2d_label_gameplay,
        piece_set_2d_options_gameplay,
        piece_set_label_gameplay,
        piece_set_options_for_dimension_gameplay,
    )

    return {
        2: tuple(
            piece_set_2d_label_gameplay(piece_set_id)
            for piece_set_id in piece_set_2d_options_gameplay()
        ),
        3: tuple(
            piece_set_label_gameplay(piece_set_id)
            for piece_set_id in piece_set_options_for_dimension_gameplay(3)
        ),
        4: tuple(
            piece_set_label_gameplay(piece_set_id)
            for piece_set_id in piece_set_options_for_dimension_gameplay(4)
        ),
    }


def _topology_profile_labels_by_dimension() -> dict[int, tuple[str, ...]]:
    from tet4d.engine.gameplay.api import (
        topology_designer_profile_label_runtime,
        topology_designer_profiles_runtime,
    )

    labels: dict[int, tuple[str, ...]] = {}
    for dimension in (2, 3, 4):
        profiles = topology_designer_profiles_runtime(dimension)
        labels[dimension] = tuple(
            topology_designer_profile_label_runtime(dimension, index)
            for index, _profile in enumerate(profiles)
        )
    return labels


def _resolve_local_ref(schema_root: dict[str, object], ref: str) -> dict[str, object]:
    if not ref.startswith("#/"):
        raise RuntimeError(f"unsupported schema ref: {ref}")
    current: object = schema_root
    for part in ref[2:].split("/"):
        if not isinstance(current, dict) or part not in current:
            raise RuntimeError(f"invalid schema ref: {ref}")
        current = current[part]
    if not isinstance(current, dict):
        raise RuntimeError(f"schema ref must resolve to object: {ref}")
    return current


def _merge_schema_dicts(
    left: dict[str, object],
    right: dict[str, object],
) -> dict[str, object]:
    merged: dict[str, object] = dict(left)
    for key, value in right.items():
        if key == "properties":
            existing = merged.get("properties", {})
            existing_props = existing if isinstance(existing, dict) else {}
            value_props = value if isinstance(value, dict) else {}
            merged[key] = {**existing_props, **value_props}
            continue
        if key == "required":
            combined: list[object] = []
            for source in (merged.get("required", []), value):
                if isinstance(source, list):
                    for item in source:
                        if item not in combined:
                            combined.append(item)
            merged[key] = combined
            continue
        merged[key] = value
    return merged


def _expand_schema_node(
    schema_root: dict[str, object],
    node: dict[str, object],
) -> dict[str, object]:
    expanded: dict[str, object] = {}
    ref = node.get("$ref")
    if isinstance(ref, str):
        expanded = _merge_schema_dicts(
            expanded,
            _expand_schema_node(schema_root, _resolve_local_ref(schema_root, ref)),
        )
    all_of = node.get("allOf")
    if isinstance(all_of, list):
        for item in all_of:
            if isinstance(item, dict):
                expanded = _merge_schema_dicts(
                    expanded,
                    _expand_schema_node(schema_root, item),
                )
    current = {k: v for k, v in node.items() if k not in {"$ref", "allOf"}}
    return _merge_schema_dicts(expanded, current)


def _schema_node_for_path(
    schema_root: dict[str, object],
    path_parts: tuple[str, ...],
) -> dict[str, object] | None:
    current: dict[str, object] = _expand_schema_node(schema_root, schema_root)
    for part in path_parts:
        properties = current.get("properties")
        if not isinstance(properties, dict):
            return None
        next_node = properties.get(part)
        if not isinstance(next_node, dict):
            return None
        current = _expand_schema_node(schema_root, next_node)
    return current


def _iter_leaf_paths(
    payload: object,
    prefix: str = "",
) -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            rows.extend(_iter_leaf_paths(value, next_prefix))
        return rows
    rows.append((prefix, payload))
    return rows


def _format_range_constraint(node: dict[str, object]) -> str:
    minimum = node.get("minimum")
    maximum = node.get("maximum")
    if minimum is not None and maximum is not None:
        return f"range: {minimum}..{maximum}"
    if minimum is not None:
        return f"min: {minimum}"
    if maximum is not None:
        return f"max: {maximum}"
    return ""


def _format_length_constraint(node: dict[str, object]) -> str:
    min_length = node.get("minLength")
    max_length = node.get("maxLength")
    if min_length is not None and max_length is not None:
        return f"length: {min_length}..{max_length}"
    if min_length is not None:
        return f"min length: {min_length}"
    if max_length is not None:
        return f"max length: {max_length}"
    return ""


def _format_item_count_constraint(node: dict[str, object]) -> str:
    min_items = node.get("minItems")
    max_items = node.get("maxItems")
    if min_items is not None and max_items is not None and min_items == max_items:
        return f"items: {min_items}"
    if min_items is not None and max_items is not None:
        return f"items: {min_items}..{max_items}"
    if min_items is not None:
        return f"min items: {min_items}"
    if max_items is not None:
        return f"max items: {max_items}"
    return ""


def _format_item_bounds(node: dict[str, object]) -> str:
    items = node.get("items")
    if not isinstance(items, list) or not items:
        return ""
    item_parts: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        item_min = item.get("minimum")
        item_max = item.get("maximum")
        snippet = str(item_type) if isinstance(item_type, str) else "value"
        if item_min is not None and item_max is not None:
            snippet += f" {item_min}..{item_max}"
        elif item_min is not None:
            snippet += f" >= {item_min}"
        elif item_max is not None:
            snippet += f" <= {item_max}"
        item_parts.append(snippet)
    if not item_parts:
        return ""
    return "item bounds: " + ", ".join(item_parts)


def _format_schema_constraints(node: dict[str, object] | None) -> str:
    if not node:
        return ""
    parts: list[str] = []
    node_type = node.get("type")
    if isinstance(node_type, str):
        parts.append(node_type)
    enum = node.get("enum")
    if isinstance(enum, list) and enum:
        rendered = ", ".join(str(item) for item in enum)
        parts.append(f"options: {rendered}")
    for formatter in (
        _format_range_constraint,
        _format_length_constraint,
        _format_item_count_constraint,
        _format_item_bounds,
    ):
        rendered = formatter(node)
        if rendered:
            parts.append(rendered)
    return "; ".join(parts)


def _format_index_labels(labels: tuple[str, ...] | None) -> str:
    if not labels:
        return ""
    rendered = ", ".join(f"{idx}={label}" for idx, label in enumerate(labels))
    return f"choices: {rendered}"


def _format_selected_option(value: object, labels: tuple[str, ...] | None) -> str:
    if not labels:
        return ""
    if isinstance(value, bool):
        return ""
    if isinstance(value, int) and 0 <= value < len(labels):
        return f"default option: {labels[value]}"
    return ""


def _settings_dimension_for_path(path: str) -> int | None:
    parts = path.split(".")
    if len(parts) < 3 or parts[0] != "settings":
        return None
    return {"2d": 2, "3d": 3, "4d": 4}.get(parts[1])


def _exact_option_labels_for_path(
    path: str,
    labels: UserSettingsOptionLabelSet,
) -> tuple[str, ...] | None:
    if path == "active_profile":
        return labels.active_profile_labels
    if path == "last_mode":
        return ("2d", "3d", "4d")
    return None


def _dimension_option_labels_for_path(
    path: str,
    labels: UserSettingsOptionLabelSet,
) -> tuple[str, ...] | None:
    dimension = _settings_dimension_for_path(path)
    if dimension is None:
        return None
    if path.endswith(".piece_set_index"):
        return labels.piece_set_labels_by_dimension.get(dimension)
    if path.endswith(".topology_profile_index"):
        return labels.topology_profile_labels_by_dimension.get(dimension)
    return None


def _suffix_option_labels_for_path(
    path: str,
    labels: UserSettingsOptionLabelSet,
) -> tuple[str, ...] | None:
    suffix_pairs = (
        (".random_mode_index", labels.random_mode_labels),
        (".kick_level_index", labels.kick_level_labels),
        (".topology_mode", labels.topology_mode_labels),
        (".bot_mode_index", labels.bot_mode_labels),
        (".bot_profile_index", labels.bot_profile_labels),
        (".bot_algorithm_index", labels.bot_algorithm_labels),
    )
    for suffix, option_labels in suffix_pairs:
        if path.endswith(suffix):
            return option_labels
    if path.endswith(
        (".topology_advanced", ".exploration_mode", ".auto_speedup_enabled")
    ):
        return ("Off", "On")
    return None


def _option_labels_for_path(
    path: str,
    labels: UserSettingsOptionLabelSet,
) -> tuple[str, ...] | None:
    for resolver in (
        _exact_option_labels_for_path,
        _dimension_option_labels_for_path,
        _suffix_option_labels_for_path,
    ):
        option_labels = resolver(path, labels)
        if option_labels is not None:
            return option_labels
    return None


def _render_user_setting_line(
    path: str,
    value: object,
    *,
    schema_node: dict[str, object] | None,
    option_labels: tuple[str, ...] | None,
) -> str:
    details: list[str] = []
    schema_text = _format_schema_constraints(schema_node)
    if schema_text:
        details.append(schema_text)
    selected_text = _format_selected_option(value, option_labels)
    if selected_text:
        details.append(selected_text)
    option_text = _format_index_labels(option_labels)
    if option_text:
        details.append(option_text)
    detail_text = f"; {'; '.join(details)}" if details else ""
    return f"- `{path}`: `{_format_literal(value)}`{detail_text}"


_GLOBAL_SETTINGS_BUCKETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("profiles", ("active_profile",)),
    (
        "display",
        (
            "display.fullscreen",
            "display.windowed_size",
            "display.overlay_transparency",
        ),
    ),
    ("audio", ("audio.master_volume", "audio.sfx_volume", "audio.mute")),
    ("analytics", ("analytics.score_logging_enabled",)),
)

_MODE_SETTINGS_BUCKETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "gameplay_setup",
        (
            "width",
            "height",
            "depth",
            "fourth",
            "explorer_width",
            "explorer_height",
            "explorer_depth",
            "explorer_fourth",
            "piece_set_index",
            "challenge_layers",
            "exploration_mode",
            "speed_level",
        ),
    ),
    (
        "gameplay",
        (
            "random_mode_index",
            "game_seed",
            "topology_mode",
            "topology_advanced",
            "topology_profile_index",
            "auto_speedup_enabled",
            "lines_per_level",
            "rotation_animation_mode",
            "rotation_animation_duration_ms_2d",
            "rotation_animation_duration_ms_nd",
            "translation_animation_duration_ms",
            "kick_level_index",
        ),
    ),
    (
        "bot",
        (
            "bot_mode_index",
            "bot_algorithm_index",
            "bot_profile_index",
            "bot_speed_level",
            "bot_budget_ms",
        ),
    ),
)


def _bucket_rows_by_path(
    rows: list[tuple[str, object]],
    *,
    bucket_defs: tuple[tuple[str, tuple[str, ...]], ...],
    scope_name: str,
) -> dict[str, list[tuple[str, object]]]:
    path_to_bucket: dict[str, str] = {}
    bucketed: dict[str, list[tuple[str, object]]] = {
        bucket_id: [] for bucket_id, _paths in bucket_defs
    }
    for bucket_id, paths in bucket_defs:
        for path in paths:
            if path in path_to_bucket:
                raise RuntimeError(f"duplicate bucket path assignment for {path}")
            path_to_bucket[path] = bucket_id
    for path, value in rows:
        bucket_id = path_to_bucket.get(path)
        if bucket_id is None:
            raise RuntimeError(f"unbucketed {scope_name} setting path: {path}")
        bucketed[bucket_id].append((path, value))
    return bucketed


def _category_doc(
    category_docs: dict[str, dict[str, str]],
    category_id: str,
) -> dict[str, str]:
    doc = category_docs.get(category_id)
    if doc is None:
        raise RuntimeError(f"missing category doc for {category_id}")
    return doc


def _user_settings_option_labels(
    keybindings_payload: dict[str, object],
    option_labels: dict[str, tuple[str, ...]],
) -> UserSettingsOptionLabelSet:
    return UserSettingsOptionLabelSet(
        active_profile_labels=tuple(sorted(keybindings_payload.get("profiles", {}))),
        random_mode_labels=option_labels.get("game_random_mode"),
        kick_level_labels=option_labels.get("game_kick_level"),
        topology_mode_labels=_topology_mode_labels(),
        bot_mode_labels=_bot_mode_labels(),
        bot_profile_labels=_bot_profile_labels(),
        bot_algorithm_labels=_bot_algorithm_labels(),
        piece_set_labels_by_dimension=_piece_set_labels_by_dimension(),
        topology_profile_labels_by_dimension=_topology_profile_labels_by_dimension(),
    )


def _user_settings_reference_preamble() -> list[str]:
    return [
        "# User Settings Reference",
        "",
        "Generated from repo config sources by "
        "`tools/governance/generate_configuration_reference.py`.",
        "Do not edit this file manually.",
        "",
        "Scope:",
        "- Covers the persisted user-facing settings surface rather than the "
        "entire `config/` tree.",
        "- Uses runtime defaults from "
        "`tet4d.engine.runtime.menu_config.default_settings_payload()` so "
        "runtime-derived settings like `bot_budget_ms` are included.",
        "- Uses `config/schema/menu_settings.schema.json` for documented "
        "bounds and enums.",
        "- Uses `config/keybindings/defaults.json` for built-in keybinding "
        "profile coverage.",
        "- Fails generation when a persisted setting is not assigned to a "
        "documented bucket.",
        "",
    ]


def _render_settings_bucket(
    *,
    category_doc: dict[str, str],
    ordered_keys: tuple[str, ...],
    row_values: dict[str, object],
    path_builder: Callable[[str], str],
    schema_payload: dict[str, object],
    option_labels: UserSettingsOptionLabelSet,
) -> list[str]:
    lines = [f"### {category_doc['label']}", category_doc["description"]]
    for key in ordered_keys:
        if key not in row_values:
            continue
        path = path_builder(key)
        lines.append(
            _render_user_setting_line(
                path,
                row_values[key],
                schema_node=_schema_node_for_path(
                    schema_payload, tuple(path.split("."))
                ),
                option_labels=_option_labels_for_path(path, option_labels),
            )
        )
    lines.append("")
    return lines


def _render_global_settings_section(
    defaults_payload: dict[str, object],
    *,
    category_docs: dict[str, dict[str, str]],
    schema_payload: dict[str, object],
    option_labels: UserSettingsOptionLabelSet,
) -> list[str]:
    global_rows = [
        path_value
        for path_value in _iter_leaf_paths(defaults_payload)
        if path_value[0] not in {"version", "last_mode"}
        and not path_value[0].startswith("settings.")
    ]
    global_bucket_rows = _bucket_rows_by_path(
        global_rows,
        bucket_defs=_GLOBAL_SETTINGS_BUCKETS,
        scope_name="global",
    )
    lines = ["## Global settings"]
    for bucket_id, ordered_paths in _GLOBAL_SETTINGS_BUCKETS:
        lines.extend(
            _render_settings_bucket(
                category_doc=_category_doc(category_docs, bucket_id),
                ordered_keys=ordered_paths,
                row_values=dict(global_bucket_rows[bucket_id]),
                path_builder=lambda key: key,
                schema_payload=schema_payload,
                option_labels=option_labels,
            )
        )
    lines.append("")
    return lines


def _render_mode_settings_section(
    *,
    mode_key: str,
    heading: str,
    mode_settings: dict[str, object],
    category_docs: dict[str, dict[str, str]],
    schema_payload: dict[str, object],
    option_labels: UserSettingsOptionLabelSet,
) -> list[str]:
    mode_bucket_rows = _bucket_rows_by_path(
        list(mode_settings.items()),
        bucket_defs=_MODE_SETTINGS_BUCKETS,
        scope_name=f"{mode_key} mode",
    )
    lines = [f"## {heading}"]
    for bucket_id, ordered_names in _MODE_SETTINGS_BUCKETS:
        lines.extend(
            _render_settings_bucket(
                category_doc=_category_doc(category_docs, bucket_id),
                ordered_keys=ordered_names,
                row_values=dict(mode_bucket_rows[bucket_id]),
                path_builder=lambda key, mk=mode_key: f"settings.{mk}.{key}",
                schema_payload=schema_payload,
                option_labels=option_labels,
            )
        )
    lines.append("")
    return lines


def _render_keybinding_profiles_section(
    *,
    active_profile: object,
    profile_names: tuple[str, ...],
    keybindings_payload: dict[str, object],
    category_docs_payload: dict[str, object],
) -> list[str]:
    lines = [
        "## Keybinding profiles",
        f"- Default active profile: `{_format_literal(active_profile)}`",
        "- Built-in profile sources: `config/keybindings/defaults.json`",
        f"- Built-in profiles: {', '.join(f'`{name}`' for name in profile_names)}",
        "",
    ]
    for profile_name, summaries in _keybinding_profile_rows(
        keybindings_payload,
        category_docs_payload=category_docs_payload,
    ):
        lines.append(f"### `{profile_name}`")
        for heading, description, scope_summaries in summaries:
            lines.append(f"#### {heading}")
            lines.append(description)
            for summary in scope_summaries:
                lines.append(f"- {summary}")
            lines.append("")
        lines.append("")
    return lines


def _keybinding_scope_label(scope_id: str) -> str:
    labels = {
        "general": "General",
        "2d": "2D",
        "3d": "3D",
        "4d": "4D",
        "all": "Shared",
    }
    label = labels.get(scope_id)
    if label is None:
        raise RuntimeError(f"unsupported keybinding scope label: {scope_id}")
    return label


def _keybinding_scope_id_for_bucket(*, group_name: str, bucket_name: str) -> str:
    if group_name == "system":
        return "general"
    scope_ids = {
        "d2": "2d",
        "d3": "3d",
        "d4": "4d",
        "all": "all",
    }
    scope_id = scope_ids.get(bucket_name)
    if scope_id is None:
        raise RuntimeError(
            f"unknown keybinding scope bucket for {group_name}: {bucket_name}"
        )
    return scope_id


def _keybinding_profile_group_counts(
    *,
    profile_name: str,
    profile_payload: dict[str, object],
    category_docs_payload: dict[str, object],
) -> dict[str, dict[str, int]]:
    raw_groups = category_docs_payload.get("groups")
    if not isinstance(raw_groups, dict):
        raise RuntimeError("keybinding category docs must include group metadata")
    scope_order = category_docs_payload.get("scope_order")
    if not isinstance(scope_order, tuple):
        scope_order = tuple(scope_order) if isinstance(scope_order, list) else ()
    counts: dict[str, dict[str, int]] = {}
    for group_name, raw_group in profile_payload.items():
        if group_name not in raw_groups:
            raise RuntimeError(
                f"unknown keybinding group in profile {profile_name}: {group_name}"
            )
        if not isinstance(raw_group, dict):
            raise RuntimeError(
                f"keybinding profile {profile_name} group {group_name} must be a mapping"
            )
        group_counts = counts.setdefault(group_name, {})
        if group_name == "system":
            group_counts["general"] = len(raw_group)
            continue
        for bucket_name, bucket in raw_group.items():
            if not isinstance(bucket, dict):
                raise RuntimeError(
                    "keybinding profile "
                    f"{profile_name} group {group_name}.{bucket_name} must be a mapping"
                )
            scope_id = _keybinding_scope_id_for_bucket(
                group_name=group_name,
                bucket_name=bucket_name,
            )
            if scope_id not in scope_order:
                raise RuntimeError(
                    f"keybinding scope order missing documented scope: {scope_id}"
                )
            group_counts[scope_id] = len(bucket)
    return counts


def _keybinding_profile_rows(
    payload: dict[str, object],
    *,
    category_docs_payload: dict[str, object],
) -> tuple[tuple[str, tuple[tuple[str, str, tuple[str, ...]], ...]], ...]:
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        return ()
    raw_groups = category_docs_payload.get("groups")
    if not isinstance(raw_groups, dict):
        raise RuntimeError("keybinding category docs must include group metadata")
    scope_order = category_docs_payload.get("scope_order")
    if not isinstance(scope_order, tuple):
        scope_order = tuple(scope_order) if isinstance(scope_order, list) else ()
    rows: list[tuple[str, tuple[tuple[str, str, tuple[str, ...]], ...]]] = []
    for profile_name in sorted(profiles):
        profile = profiles[profile_name]
        if not isinstance(profile, dict):
            continue
        group_counts = _keybinding_profile_group_counts(
            profile_name=profile_name,
            profile_payload=profile,
            category_docs_payload=category_docs_payload,
        )
        group_rows: list[tuple[str, str, tuple[str, ...]]] = []
        for group_name, group_doc in raw_groups.items():
            if not isinstance(group_doc, dict):
                raise RuntimeError(
                    f"keybinding category doc for {group_name} must be a mapping"
                )
            counts = group_counts.get(group_name, {})
            if not counts:
                continue
            scope_summaries = tuple(
                f"{_keybinding_scope_label(scope_id)}: {counts[scope_id]} actions"
                for scope_id in scope_order
                if scope_id in counts
            )
            group_rows.append(
                (
                    str(group_doc.get("label", group_name)),
                    str(group_doc.get("description", "")),
                    scope_summaries,
                )
            )
        rows.append((profile_name, tuple(group_rows)))
    return tuple(rows)


def render_user_settings_reference() -> str:
    defaults_payload = _user_settings_defaults_payload()
    schema_payload = _menu_settings_schema_payload()
    keybindings_payload = _keybindings_defaults_payload()
    category_docs = _settings_category_docs_payload()
    option_labels = _user_settings_option_labels(
        keybindings_payload,
        _settings_option_labels_payload(),
    )
    profile_names = option_labels.active_profile_labels

    lines = _user_settings_reference_preamble()
    lines.extend(
        _render_global_settings_section(
            defaults_payload,
            category_docs=category_docs,
            schema_payload=schema_payload,
            option_labels=option_labels,
        )
    )
    for mode_key, heading in (
        ("2d", "2D settings"),
        ("3d", "3D settings"),
        ("4d", "4D settings"),
    ):
        mode_settings = defaults_payload.get("settings", {}).get(mode_key, {})
        if not isinstance(mode_settings, dict):
            continue
        lines.extend(
            _render_mode_settings_section(
                mode_key=mode_key,
                heading=heading,
                mode_settings=mode_settings,
                category_docs=category_docs,
                schema_payload=schema_payload,
                option_labels=option_labels,
            )
        )
    lines.extend(
        _render_keybinding_profiles_section(
            active_profile=defaults_payload.get("active_profile"),
            profile_names=profile_names,
            keybindings_payload=keybindings_payload,
            category_docs_payload=_keybinding_category_docs_payload(),
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def _check_doc(path: Path, expected: str) -> int:
    if not path.exists():
        print(f"Missing generated documentation: {path}", file=sys.stderr)
        return 1
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        print(
            f"Generated documentation is out of date: {path.relative_to(PROJECT_ROOT).as_posix()}. "
            "Run tools/governance/generate_configuration_reference.py.",
            file=sys.stderr,
        )
        return 1
    return 0


def check_generated_docs() -> int:
    failures = 0
    failures |= _check_doc(CONFIG_DOC_PATH, render_configuration_reference())
    failures |= _check_doc(USER_SETTINGS_DOC_PATH, render_user_settings_reference())
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated configuration docs are stale",
    )
    args = parser.parse_args(argv)
    if args.check:
        return check_generated_docs()
    CONFIG_DOC_PATH.write_text(render_configuration_reference(), encoding="utf-8")
    USER_SETTINGS_DOC_PATH.write_text(
        render_user_settings_reference(),
        encoding="utf-8",
    )
    print(f"Wrote {CONFIG_DOC_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote {USER_SETTINGS_DOC_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
