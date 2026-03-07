from __future__ import annotations

from typing import Any

from ...ui_logic.menu_action_contracts import PARITY_ACTION_IDS
from .graph import (
    collect_actions_for_menu_ids,
    collect_reachable_menu_ids,
    collect_route_ids_for_menu_ids,
)


def _entrypoint_reachability(
    menus: dict[str, dict[str, Any]],
    *,
    start_menu_id: str,
) -> tuple[set[str], set[str], set[str]]:
    reachable_menu_ids = collect_reachable_menu_ids(menus, start_menu_id=start_menu_id)
    actions = collect_actions_for_menu_ids(menus, menu_ids=reachable_menu_ids)
    route_ids = collect_route_ids_for_menu_ids(menus, menu_ids=reachable_menu_ids)
    return reachable_menu_ids, actions, route_ids


def validate_launcher_route_actions(
    *,
    launcher_route_actions: dict[str, str],
    launcher_route_ids: set[str],
    launcher_actions: set[str],
) -> None:
    unknown_route_mappings = sorted(set(launcher_route_actions) - launcher_route_ids)
    if unknown_route_mappings:
        raise RuntimeError(
            "structure.launcher_route_actions maps unknown route ids: "
            + ", ".join(unknown_route_mappings)
        )
    missing_route_mappings = sorted(launcher_route_ids - set(launcher_route_actions))
    if missing_route_mappings:
        raise RuntimeError(
            "structure.launcher_route_actions missing route mappings for: "
            + ", ".join(missing_route_mappings)
        )
    invalid_route_actions = sorted(
        {
            action_id
            for action_id in launcher_route_actions.values()
            if action_id not in launcher_actions
        }
    )
    if invalid_route_actions:
        raise RuntimeError(
            "structure.launcher_route_actions references unknown launcher actions: "
            + ", ".join(invalid_route_actions)
        )


def enforce_menu_entrypoint_parity(validated: dict[str, Any]) -> None:
    menus: dict[str, dict[str, Any]] = validated["menus"]
    entrypoints: dict[str, str] = validated["menu_entrypoints"]
    launcher_actions = _entrypoint_reachability(
        menus, start_menu_id=entrypoints["launcher"]
    )[1]
    pause_actions = _entrypoint_reachability(menus, start_menu_id=entrypoints["pause"])[1]
    required = set(PARITY_ACTION_IDS)
    launcher_missing = sorted(required - launcher_actions)
    pause_missing = sorted(required - pause_actions)
    if launcher_missing:
        raise RuntimeError(
            "launcher entrypoint missing required parity actions: "
            + ", ".join(launcher_missing)
        )
    if pause_missing:
        raise RuntimeError(
            "pause entrypoint missing required parity actions: "
            + ", ".join(pause_missing)
        )


def enforce_settings_split_policy(validated: dict[str, Any]) -> None:
    metrics: dict[str, dict[str, Any]] = validated["settings_category_metrics"]
    if not metrics:
        return

    rules = validated["settings_split_rules"]
    max_fields = int(rules["max_top_level_fields"])
    max_actions = int(rules["max_top_level_actions"])
    split_mode_specific = bool(rules["split_when_mode_specific"])
    docs = {entry["id"]: entry for entry in validated["settings_category_docs"]}

    required_top_labels: list[str] = []
    for category_id, entry in metrics.items():
        if not bool(entry.get("top_level")):
            continue
        if int(entry.get("field_count", 0)) > max_fields:
            raise RuntimeError(
                "settings split policy violation: "
                f"{category_id} exceeds max_top_level_fields"
            )
        if int(entry.get("action_count", 0)) > max_actions:
            raise RuntimeError(
                "settings split policy violation: "
                f"{category_id} exceeds max_top_level_actions"
            )
        if split_mode_specific and bool(entry.get("mode_specific")):
            raise RuntimeError(
                "settings split policy violation: "
                f"{category_id} is mode-specific and must not remain top-level"
            )
        required_top_labels.append(docs[category_id]["label"])

    hub_rows = set(validated["settings_hub_rows"])
    missing_rows = [label for label in required_top_labels if label not in hub_rows]
    if missing_rows:
        raise RuntimeError(
            "settings_hub_rows missing top-level categories required by split policy: "
            + ", ".join(missing_rows)
        )

    layout_headers = {
        row["label"]
        for row in validated["settings_hub_layout_rows"]
        if row["kind"] == "header"
    }
    missing_headers = [
        label for label in required_top_labels if label not in layout_headers
    ]
    if missing_headers:
        raise RuntimeError(
            "settings_hub_layout_rows missing required top-level headers: "
            + ", ".join(missing_headers)
        )
