from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from tet4d.engine.runtime.project_config import project_root_path
from tet4d.engine.runtime.settings_schema import read_json_value_or_raise


_CATALOG_PATH = project_root_path() / "config" / "keybindings" / "catalog.json"
_GAMEPLAY_FALLBACK_BUCKET = "other"


def _require_object(value: object, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must be an object")
    return value


def _require_string(value: object, *, path: str, non_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{path} must be a string")
    if non_empty and not value.strip():
        raise RuntimeError(f"{path} must be non-empty")
    return value.strip() if non_empty else value


def _require_int(value: object, *, path: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"{path} must be an integer")
    if value < minimum:
        raise RuntimeError(f"{path} must be >= {minimum}")
    return value


def _require_string_list(
    value: object,
    *,
    path: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise RuntimeError(f"{path} must be a list")
    out = tuple(
        _require_string(item, path=f"{path}[{idx}]", non_empty=True)
        for idx, item in enumerate(value)
    )
    if not allow_empty and not out:
        raise RuntimeError(f"{path} must be non-empty")
    return out


def _require_dimension_list(value: object, *, path: str) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise RuntimeError(f"{path} must be a list")
    dims = tuple(_require_int(item, path=f"{path}[{idx}]", minimum=2) for idx, item in enumerate(value))
    invalid = tuple(dim for dim in dims if dim not in {2, 3, 4})
    if invalid:
        raise RuntimeError(f"{path} has unsupported dimensions: {invalid}")
    return dims


def _read_catalog_payload() -> dict[str, Any]:
    payload = read_json_value_or_raise(_CATALOG_PATH)
    if not isinstance(payload, dict):
        raise RuntimeError("keybinding catalog must be a JSON object")
    return payload


def _validate_helper_line(
    raw_line: object,
    *,
    panel_idx: int,
    line_idx: int,
    action_ids: set[str],
) -> dict[str, Any]:
    path = f"keybindings.catalog.helper_layout.panels[{panel_idx}].lines[{line_idx}]"
    line = _require_object(raw_line, path=path)
    key_actions = _require_string_list(
        line.get("key_actions", []),
        path=f"{path}.key_actions",
        allow_empty=True,
    )
    unknown = tuple(action for action in key_actions if action not in action_ids)
    if unknown:
        raise RuntimeError(f"{path}.key_actions has unknown actions: {', '.join(unknown)}")
    icon_action_raw = line.get("icon_action")
    icon_action = None
    if icon_action_raw is not None:
        icon_action = _require_string(
            icon_action_raw,
            path=f"{path}.icon_action",
            non_empty=True,
        )
        if icon_action not in action_ids:
            raise RuntimeError(f"{path}.icon_action has unknown action: {icon_action}")
    return {
        "id": _require_string(line.get("id"), path=f"{path}.id", non_empty=True),
        "order": _require_int(line.get("order"), path=f"{path}.order", minimum=0),
        "modes": _require_string_list(line.get("modes"), path=f"{path}.modes"),
        "requires": _require_string_list(
            line.get("requires", []),
            path=f"{path}.requires",
            allow_empty=True,
        ),
        "key_actions": key_actions,
        "icon_action": icon_action,
        "template": _require_string(
            line.get("template"),
            path=f"{path}.template",
            non_empty=True,
        ),
    }


def _validate_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    version = _require_int(payload.get("version"), path="keybindings.catalog.version", minimum=1)
    scopes_obj = _require_object(payload.get("scopes"), path="keybindings.catalog.scopes")
    groups_obj = _require_object(payload.get("groups"), path="keybindings.catalog.groups")
    editor_obj = _require_object(payload.get("editor"), path="keybindings.catalog.editor")
    reference_obj = _require_object(
        payload.get("reference_groups"),
        path="keybindings.catalog.reference_groups",
    )
    actions_obj = _require_object(payload.get("actions"), path="keybindings.catalog.actions")
    helper_obj = _require_object(
        payload.get("helper_layout"),
        path="keybindings.catalog.helper_layout",
    )

    scopes = _require_string_list(
        scopes_obj.get("order"),
        path="keybindings.catalog.scopes.order",
    )

    groups: dict[str, dict[str, Any]] = {}
    for group_name, raw_group in groups_obj.items():
        clean_name = _require_string(
            group_name,
            path="keybindings.catalog.groups keys",
            non_empty=True,
        ).lower()
        group = _require_object(raw_group, path=f"keybindings.catalog.groups.{clean_name}")
        groups[clean_name] = {
            "order": _require_int(
                group.get("order"),
                path=f"keybindings.catalog.groups.{clean_name}.order",
                minimum=0,
            ),
            "label": _require_string(
                group.get("label"),
                path=f"keybindings.catalog.groups.{clean_name}.label",
                non_empty=True,
            ),
            "description": _require_string(
                group.get("description"),
                path=f"keybindings.catalog.groups.{clean_name}.description",
                non_empty=True,
            ),
        }

    gameplay_buckets_obj = _require_object(
        editor_obj.get("gameplay_buckets"),
        path="keybindings.catalog.editor.gameplay_buckets",
    )
    gameplay_buckets: dict[str, dict[str, Any]] = {}
    for bucket_name, raw_bucket in gameplay_buckets_obj.items():
        clean_bucket = _require_string(
            bucket_name,
            path="keybindings.catalog.editor.gameplay_buckets keys",
            non_empty=True,
        ).lower()
        bucket = _require_object(
            raw_bucket,
            path=f"keybindings.catalog.editor.gameplay_buckets.{clean_bucket}",
        )
        gameplay_buckets[clean_bucket] = {
            "order": _require_int(
                bucket.get("order"),
                path=(
                    "keybindings.catalog.editor.gameplay_buckets."
                    f"{clean_bucket}.order"
                ),
                minimum=0,
            ),
            "label": _require_string(
                bucket.get("label"),
                path=(
                    "keybindings.catalog.editor.gameplay_buckets."
                    f"{clean_bucket}.label"
                ),
                non_empty=True,
            ),
            "description": _require_string(
                bucket.get("description"),
                path=(
                    "keybindings.catalog.editor.gameplay_buckets."
                    f"{clean_bucket}.description"
                ),
                non_empty=True,
            ),
        }

    runtime_order = _require_string_list(
        reference_obj.get("runtime_order"),
        path="keybindings.catalog.reference_groups.runtime_order",
    )
    live_order = _require_string_list(
        reference_obj.get("live_order"),
        path="keybindings.catalog.reference_groups.live_order",
    )
    headings_obj = _require_object(
        reference_obj.get("headings"),
        path="keybindings.catalog.reference_groups.headings",
    )
    reference_headings = {
        _require_string(key, path="keybindings.catalog.reference_groups.headings keys", non_empty=True): _require_string(
            value,
            path=f"keybindings.catalog.reference_groups.headings.{key}",
            non_empty=True,
        )
        for key, value in headings_obj.items()
    }

    actions: dict[str, dict[str, Any]] = {}
    for action_name, raw_action in actions_obj.items():
        clean_action = _require_string(
            action_name,
            path="keybindings.catalog.actions keys",
            non_empty=True,
        )
        action = _require_object(raw_action, path=f"keybindings.catalog.actions.{clean_action}")
        group_name = _require_string(
            action.get("group"),
            path=f"keybindings.catalog.actions.{clean_action}.group",
            non_empty=True,
        ).lower()
        if group_name not in groups:
            raise RuntimeError(
                f"keybindings.catalog.actions.{clean_action}.group references unknown group: {group_name}"
            )
        gameplay_bucket = action.get("gameplay_bucket")
        clean_bucket: str | None = None
        if gameplay_bucket is not None:
            clean_bucket = _require_string(
                gameplay_bucket,
                path=f"keybindings.catalog.actions.{clean_action}.gameplay_bucket",
                non_empty=True,
            ).lower()
            if clean_bucket not in gameplay_buckets:
                raise RuntimeError(
                    "keybindings.catalog.actions."
                    f"{clean_action}.gameplay_bucket references unknown bucket: {clean_bucket}"
                )
        actions[clean_action] = {
            "group": group_name,
            "order": _require_int(
                action.get("order"),
                path=f"keybindings.catalog.actions.{clean_action}.order",
                minimum=0,
            ),
            "label": _require_string(
                action.get("label"),
                path=f"keybindings.catalog.actions.{clean_action}.label",
                non_empty=True,
            ),
            "description": _require_string(
                action.get("description"),
                path=f"keybindings.catalog.actions.{clean_action}.description",
                non_empty=True,
            ),
            "dimensions": _require_dimension_list(
                action.get("dimensions"),
                path=f"keybindings.catalog.actions.{clean_action}.dimensions",
            ),
            "gameplay_bucket": clean_bucket,
        }

    meta_obj = _require_object(
        helper_obj.get("meta"),
        path="keybindings.catalog.helper_layout.meta",
    )
    helper_panels_raw = helper_obj.get("panels")
    if not isinstance(helper_panels_raw, list) or not helper_panels_raw:
        raise RuntimeError("keybindings.catalog.helper_layout.panels must be a non-empty list")
    helper_layout = {
        "meta": {
            "schema_version": _require_int(
                meta_obj.get("schema_version"),
                path="keybindings.catalog.helper_layout.meta.schema_version",
                minimum=1,
            )
        },
        "tokens": {
            str(key): _require_string(
                value,
                path=f"keybindings.catalog.helper_layout.tokens.{key}",
            )
            for key, value in _require_object(
                helper_obj.get("tokens", {}),
                path="keybindings.catalog.helper_layout.tokens",
            ).items()
        },
        "panels": tuple(
            {
                "id": _require_string(
                    _require_object(
                        raw_panel,
                        path=f"keybindings.catalog.helper_layout.panels[{panel_idx}]",
                    ).get("id"),
                    path=f"keybindings.catalog.helper_layout.panels[{panel_idx}].id",
                    non_empty=True,
                ),
                "order": _require_int(
                    _require_object(
                        raw_panel,
                        path=f"keybindings.catalog.helper_layout.panels[{panel_idx}]",
                    ).get("order"),
                    path=f"keybindings.catalog.helper_layout.panels[{panel_idx}].order",
                    minimum=0,
                ),
                "title": _require_string(
                    _require_object(
                        raw_panel,
                        path=f"keybindings.catalog.helper_layout.panels[{panel_idx}]",
                    ).get("title"),
                    path=f"keybindings.catalog.helper_layout.panels[{panel_idx}].title",
                    non_empty=True,
                ),
                "modes": _require_string_list(
                    _require_object(
                        raw_panel,
                        path=f"keybindings.catalog.helper_layout.panels[{panel_idx}]",
                    ).get("modes"),
                    path=f"keybindings.catalog.helper_layout.panels[{panel_idx}].modes",
                ),
                "requires": _require_string_list(
                    _require_object(
                        raw_panel,
                        path=f"keybindings.catalog.helper_layout.panels[{panel_idx}]",
                    ).get("requires", []),
                    path=f"keybindings.catalog.helper_layout.panels[{panel_idx}].requires",
                    allow_empty=True,
                ),
                "lines": tuple(
                    _validate_helper_line(
                        raw_line,
                        panel_idx=panel_idx,
                        line_idx=line_idx,
                        action_ids=set(actions.keys()),
                    )
                    for line_idx, raw_line in enumerate(
                        _require_object(
                            raw_panel,
                            path=f"keybindings.catalog.helper_layout.panels[{panel_idx}]",
                        ).get("lines", [])
                    )
                ),
            }
            for panel_idx, raw_panel in enumerate(helper_panels_raw)
        ),
    }

    return {
        "version": version,
        "scopes": scopes,
        "groups": groups,
        "editor": {"gameplay_buckets": gameplay_buckets},
        "reference_groups": {
            "runtime_order": runtime_order,
            "live_order": live_order,
            "headings": reference_headings,
        },
        "actions": actions,
        "helper_layout": helper_layout,
    }


@lru_cache(maxsize=1)
def keybinding_catalog_payload() -> dict[str, Any]:
    return _validate_catalog(_read_catalog_payload())


def binding_scope_order() -> tuple[str, ...]:
    return tuple(keybinding_catalog_payload()["scopes"])


def binding_group_docs() -> dict[str, dict[str, str]]:
    groups = keybinding_catalog_payload()["groups"]
    return {
        group: {
            "label": str(entry["label"]),
            "description": str(entry["description"]),
        }
        for group, entry in groups.items()
    }


def binding_group_label(group: str) -> str:
    docs = binding_group_docs()
    entry = docs.get(group)
    if entry is None:
        return group.replace("_", " ").title()
    return entry["label"]


def binding_group_description(group: str) -> str:
    docs = binding_group_docs()
    entry = docs.get(group)
    if entry is None:
        return "Control category."
    return entry["description"]


def binding_action_ids() -> tuple[str, ...]:
    actions = keybinding_catalog_payload()["actions"]
    ordered = sorted(actions.items(), key=lambda item: _action_sort_key(item[0]))
    return tuple(action for action, _entry in ordered)


def binding_action_label(action: str) -> str:
    entry = keybinding_catalog_payload()["actions"].get(action)
    if entry is None:
        return action.replace("_", " ")
    return str(entry["label"])


def binding_action_description(action: str) -> str:
    entry = keybinding_catalog_payload()["actions"].get(action)
    if entry is None:
        return action.replace("_", " ")
    return str(entry["description"])


def binding_reference_runtime_order() -> tuple[str, ...]:
    reference = keybinding_catalog_payload()["reference_groups"]
    return tuple(reference["runtime_order"])


def binding_reference_live_order() -> tuple[str, ...]:
    reference = keybinding_catalog_payload()["reference_groups"]
    return tuple(reference["live_order"])


def binding_reference_group_heading(group: str) -> str:
    headings = keybinding_catalog_payload()["reference_groups"]["headings"]
    key = str(group).strip()
    if not key:
        return ""
    return str(headings.get(key, ""))


def gameplay_bucket_label(bucket: str) -> str:
    entry = keybinding_catalog_payload()["editor"]["gameplay_buckets"].get(bucket)
    if entry is None:
        return bucket.replace("_", " ").title()
    return str(entry["label"])


def gameplay_bucket_description(bucket: str) -> str:
    entry = keybinding_catalog_payload()["editor"]["gameplay_buckets"].get(bucket)
    if entry is None:
        return ""
    return str(entry["description"])


def _action_sort_key(action: str) -> tuple[int, int, str]:
    catalog = keybinding_catalog_payload()
    actions = catalog["actions"]
    groups = catalog["groups"]
    entry = actions.get(action)
    if entry is None:
        return (999, 999, action)
    group_name = str(entry["group"])
    group_order = int(groups.get(group_name, {}).get("order", 999))
    return (group_order, int(entry["order"]), action)


def gameplay_action_category(action: str) -> str:
    entry = keybinding_catalog_payload()["actions"].get(action)
    if entry is None:
        return _GAMEPLAY_FALLBACK_BUCKET
    bucket = entry.get("gameplay_bucket")
    if bucket is None:
        return _GAMEPLAY_FALLBACK_BUCKET
    return str(bucket)


def partition_gameplay_actions(
    actions: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    ordered = tuple(sorted(dict.fromkeys(actions), key=_action_sort_key))
    translation = tuple(
        action for action in ordered if gameplay_action_category(action) == "translation"
    )
    rotation = tuple(
        action for action in ordered if gameplay_action_category(action) == "rotation"
    )
    other = tuple(
        action for action in ordered if gameplay_action_category(action) == _GAMEPLAY_FALLBACK_BUCKET
    )
    return translation, rotation, other


def keybinding_helper_layout_payload() -> dict[str, Any]:
    helper = keybinding_catalog_payload()["helper_layout"]
    return {
        "meta": dict(helper["meta"]),
        "tokens": dict(helper["tokens"]),
        "panels": [
            {
                "id": panel["id"],
                "order": int(panel["order"]),
                "title": panel["title"],
                "modes": list(panel["modes"]),
                "requires": list(panel["requires"]),
                "lines": [
                    {
                        "id": line["id"],
                        "order": int(line["order"]),
                        "modes": list(line["modes"]),
                        "requires": list(line["requires"]),
                        "key_actions": list(line["key_actions"]),
                        "icon_action": line["icon_action"],
                        "template": line["template"],
                    }
                    for line in panel["lines"]
                ],
            }
            for panel in helper["panels"]
        ],
    }
