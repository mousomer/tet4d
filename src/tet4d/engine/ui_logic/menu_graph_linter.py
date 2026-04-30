from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .menu_action_contracts import (
    LAUNCHER_ACTION_IDS,
    PARITY_ACTION_IDS,
    PAUSE_ACTION_IDS,
)
from ..runtime.menu_config import (
    default_settings_payload,
    keybindings_menu_id,
    launcher_menu_id,
    menu_graph,
    pause_menu_id,
    reachable_action_ids,
    settings_menu_id,
)


@dataclass(frozen=True)
class MenuGraphIssue:
    kind: str
    message: str


def _reachable_menu_ids(
    menus: dict[str, dict[str, object]],
    *,
    start_ids: tuple[str, ...],
) -> set[str]:
    seen: set[str] = set()
    queue: deque[str] = deque(start_ids)
    while queue:
        menu_id = queue.popleft()
        if menu_id in seen:
            continue
        menu = menus.get(menu_id)
        if menu is None:
            continue
        seen.add(menu_id)
        raw_items = menu.get("items")
        if not isinstance(raw_items, tuple):
            continue
        for item in raw_items:
            if str(item.get("type", "")).lower() != "submenu":
                continue
            target = str(item.get("menu_id", "")).strip().lower()
            if target and target not in seen:
                queue.append(target)
    return seen


def lint_menu_graph() -> list[MenuGraphIssue]:
    menus = menu_graph()
    launch_root = launcher_menu_id()
    pause_root = pause_menu_id()
    issues: list[MenuGraphIssue] = []

    _validate_launcher_root_ia(menus, launch_root=launch_root, issues=issues)
    _validate_launcher_advanced_menu(menus, issues=issues)
    _validate_settings_ia(menus, issues=issues)
    _validate_explosion_defaults_settings_coverage(menus, issues=issues)

    reachable_menus = _reachable_menu_ids(
        menus,
        start_ids=(launch_root, pause_root, settings_menu_id(), keybindings_menu_id()),
    )
    unreachable = sorted(set(menus) - reachable_menus)
    if unreachable:
        issues.append(
            MenuGraphIssue(
                "reachability",
                "unreachable menus detected: " + ", ".join(unreachable),
            )
        )

    launcher_actions = set(reachable_action_ids(launch_root))
    pause_actions = set(reachable_action_ids(pause_root))

    launcher_missing_handlers = sorted(launcher_actions - set(LAUNCHER_ACTION_IDS))
    if launcher_missing_handlers:
        issues.append(
            MenuGraphIssue(
                "handlers",
                "launcher actions missing handlers: "
                + ", ".join(launcher_missing_handlers),
            )
        )

    pause_missing_handlers = sorted(pause_actions - set(PAUSE_ACTION_IDS))
    if pause_missing_handlers:
        issues.append(
            MenuGraphIssue(
                "handlers",
                "pause actions missing handlers: " + ", ".join(pause_missing_handlers),
            )
        )

    parity = set(PARITY_ACTION_IDS)
    launcher_parity_missing = sorted(parity - launcher_actions)
    pause_parity_missing = sorted(parity - pause_actions)
    if launcher_parity_missing:
        issues.append(
            MenuGraphIssue(
                "parity",
                "launcher parity actions missing: "
                + ", ".join(launcher_parity_missing),
            )
        )
    if pause_parity_missing:
        issues.append(
            MenuGraphIssue(
                "parity",
                "pause parity actions missing: " + ", ".join(pause_parity_missing),
            )
        )

    return issues


def _menu_items_for_id(
    menus: dict[str, dict[str, object]],
    *,
    menu_id: str,
    label: str,
    issues: list[MenuGraphIssue],
) -> tuple[dict[str, object], ...] | None:
    menu = menus.get(menu_id)
    if menu is None:
        issues.append(MenuGraphIssue("ia", f"{label} menu missing: {menu_id}"))
        return None
    raw_items = menu.get("items")
    if not isinstance(raw_items, tuple):
        issues.append(MenuGraphIssue("ia", f"{label} items missing: {menu_id}"))
        return None
    return raw_items


def _menu_labels(items: tuple[dict[str, object], ...]) -> list[str]:
    return [str(item.get("label", "")) for item in items]


def _validate_launcher_root_ia(
    menus: dict[str, dict[str, object]],
    *,
    launch_root: str,
    issues: list[MenuGraphIssue],
) -> None:
    expected_labels = [
        "2D",
        "3D",
        "4D",
        "Replay Last",
        "Leaderboard",
        "Help / Tutorials",
        "Advanced",
    ]
    banned_labels = {
        "Play",
        "Continue",
        "Tutorials",
        "Settings",
        "Topology Playground",
        "Explosion Simulator",
        "Bot",
        "Quit",
    }

    raw_items = _menu_items_for_id(
        menus,
        menu_id=launch_root,
        label="launcher root",
        issues=issues,
    )
    if raw_items is None:
        return
    _validate_launcher_root_labels(
        menus,
        raw_items,
        expected_labels=expected_labels,
        banned_labels=banned_labels,
        issues=issues,
    )
    _validate_launcher_root_rows(raw_items, issues=issues)

def _validate_launcher_root_labels(
    menus: dict[str, dict[str, object]],
    raw_items: tuple[dict[str, object], ...],
    *,
    expected_labels: list[str],
    banned_labels: set[str],
    issues: list[MenuGraphIssue],
) -> None:
    labels = _menu_labels(raw_items)
    if labels != expected_labels:
        issues.append(
            MenuGraphIssue(
                "ia",
                "launcher root labels must be exactly: "
                + ", ".join(expected_labels)
                + f" (got: {', '.join(labels)})",
            )
        )
    forbidden_present = sorted(banned_labels.intersection(labels))
    if forbidden_present:
        issues.append(
            MenuGraphIssue(
                "ia",
                "launcher root contains forbidden labels: " + ", ".join(forbidden_present),
            )
        )
    if "launcher_play" in menus:
        issues.append(
            MenuGraphIssue(
                "ia",
                "launcher_play menu id must not exist (no independent Play submenu)",
            )
        )
    if any(str(item.get("menu_id", "")) == "launcher_play" for item in raw_items):
        issues.append(MenuGraphIssue("ia", "launcher root must not route to launcher_play submenu"))
    if any(str(item.get("label", "")).strip().lower() == "quit" for item in raw_items):
        issues.append(MenuGraphIssue("ia", "launcher root must not include a Quit row"))

def _validate_launcher_root_rows(
    raw_items: tuple[dict[str, object], ...],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    if len(raw_items) != 7:
        issues.append(MenuGraphIssue("ia", "launcher root must contain 7 rows"))
        return
    _validate_launcher_root_action_groups(raw_items, issues=issues)
    _validate_launcher_root_row(
        raw_items,
        index=3,
        expected_type="action",
        expected_label="Replay Last",
        expected_id_key="action_id",
        expected_id_value="continue",
        issues=issues,
    )
    _validate_launcher_root_row(
        raw_items,
        index=4,
        expected_type="action",
        expected_label="Leaderboard",
        expected_id_key="action_id",
        expected_id_value="leaderboard",
        issues=issues,
    )
    _validate_launcher_root_row(
        raw_items,
        index=5,
        expected_type="submenu",
        expected_label="Help / Tutorials",
        expected_id_key="menu_id",
        expected_id_value="launcher_tutorials",
        issues=issues,
    )
    _validate_launcher_root_row(
        raw_items,
        index=6,
        expected_type="submenu",
        expected_label="Advanced",
        expected_id_key="menu_id",
        expected_id_value="launcher_advanced",
        issues=issues,
    )


def _validate_launcher_root_action_groups(
    raw_items: tuple[dict[str, object], ...],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    for idx, expected in enumerate(("2D", "3D", "4D")):
        item = raw_items[idx]
        if str(item.get("type", "")).strip().lower() != "action_group":
            issues.append(MenuGraphIssue("ia", f"launcher root row {idx+1} must be action_group"))
            continue
        if str(item.get("label", "")) != expected:
            continue
        if str(item.get("default_action_id", "")) != "play":
            issues.append(MenuGraphIssue("ia", f"launcher root '{expected}' must default to Play"))
        actions = item.get("actions")
        if not isinstance(actions, tuple) or len(actions) != 2:
            issues.append(MenuGraphIssue("ia", f"launcher root '{expected}' must expose Play/Setup actions"))
            continue
        expected_action_ids = (
            f"play_{expected.lower()}",
            f"setup_{expected.lower()}",
        )
        action_ids = tuple(str(action.get("action_id", "")) for action in actions)
        if action_ids != expected_action_ids:
            issues.append(
                MenuGraphIssue(
                    "ia",
                    f"launcher root '{expected}' actions must be {expected_action_ids} (got {action_ids})",
                )
            )


def _validate_launcher_root_row(
    raw_items: tuple[dict[str, object], ...],
    *,
    index: int,
    expected_type: str,
    expected_label: str,
    expected_id_key: str,
    expected_id_value: str,
    issues: list[MenuGraphIssue],
) -> None:
    item = raw_items[index]
    if str(item.get("type", "")).strip().lower() != expected_type or str(item.get("label", "")) != expected_label:
        issues.append(
            MenuGraphIssue(
                "ia",
                f"launcher root row {index+1} must be '{expected_label}' {expected_type}",
            )
        )
        return
    if str(item.get(expected_id_key, "")) != expected_id_value:
        issues.append(
            MenuGraphIssue(
                "ia",
                f"launcher root '{expected_label}' must map to {expected_id_key} {expected_id_value!r}",
            )
        )


def _validate_launcher_advanced_menu(
    menus: dict[str, dict[str, object]],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    menu_id = "launcher_advanced"
    expected_labels = [
        "Settings",
        "Topology Playground",
        "Explosion Simulator",
        "Bot",
        "Last Custom Topology",
        "Back",
    ]
    expected_actions = {
        "Settings": "settings",
        "Topology Playground": "topology_lab",
        "Explosion Simulator": "locked_cell_explosion",
        "Bot": "bot_options",
        "Last Custom Topology": "play_last_custom_topology",
        "Back": "back",
    }
    menu = menus.get(menu_id)
    if menu is None:
        issues.append(MenuGraphIssue("ia", f"advanced menu missing: {menu_id}"))
        return
    raw_items = menu.get("items")
    if not isinstance(raw_items, tuple):
        issues.append(MenuGraphIssue("ia", f"advanced menu items missing: {menu_id}"))
        return
    labels = [str(item.get("label", "")) for item in raw_items]
    if labels != expected_labels:
        issues.append(
            MenuGraphIssue(
                "ia",
                "Advanced menu labels must be exactly: "
                + ", ".join(expected_labels)
                + f" (got: {', '.join(labels)})",
            )
        )
    for item in raw_items:
        if str(item.get("type", "")).strip().lower() != "action":
            issues.append(MenuGraphIssue("ia", f"{menu_id} must contain action items only"))
            continue
        label = str(item.get("label", ""))
        if label not in expected_actions:
            continue
        action_id = str(item.get("action_id", ""))
        if action_id != expected_actions[label]:
            issues.append(
                MenuGraphIssue(
                    "ia",
                    f"{menu_id}:{label} must map to action_id {expected_actions[label]!r} (got {action_id!r})",
                )
            )


def _validate_settings_ia(
    menus: dict[str, dict[str, object]],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    settings_root = settings_menu_id()
    raw_items = _menu_items_for_id(
        menus,
        menu_id=settings_root,
        label="settings root",
        issues=issues,
    )
    if raw_items is None:
        return
    _validate_settings_root_labels(raw_items, issues=issues)

    raw_controls_items = _menu_items_for_id(
        menus,
        menu_id="settings_controls",
        label="settings_controls",
        issues=issues,
    )
    if raw_controls_items is None:
        return
    _validate_settings_controls_keyboard_bindings(raw_controls_items, issues=issues)

    if "settings_endgame_explosion" not in menus:
        issues.append(MenuGraphIssue("ia", "settings_endgame_explosion menu missing"))

    board_items = _menu_items_for_id(
        menus,
        menu_id="settings_board_setup_defaults",
        label="settings_board_setup_defaults",
        issues=issues,
    )
    if board_items is None:
        return
    _validate_board_defaults_legacy_topology(board_items, issues=issues)


def _validate_settings_root_labels(
    raw_items: tuple[dict[str, object], ...],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    expected_labels = [
        "Gameplay",
        "Board / Setup Defaults",
        "Controls",
        "Display",
        "Audio",
        "Endgame / Explosion",
        "Back",
    ]
    labels = _menu_labels(raw_items)
    if labels != expected_labels:
        issues.append(
            MenuGraphIssue(
                "ia",
                "Settings root labels must be exactly: "
                + ", ".join(expected_labels)
                + f" (got: {', '.join(labels)})",
            )
        )
    if "Keyboard Bindings" in labels:
        issues.append(
            MenuGraphIssue(
                "ia",
                "Keyboard Bindings must live under Controls, not Settings root",
            )
        )


def _validate_settings_controls_keyboard_bindings(
    raw_controls_items: tuple[dict[str, object], ...],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    kb = [
        item
        for item in raw_controls_items
        if str(item.get("type", "")).strip().lower() == "action"
        and str(item.get("label", "")) == "Keyboard Bindings"
    ]
    if not kb:
        issues.append(
            MenuGraphIssue(
                "ia",
                "Settings -> Controls must include 'Keyboard Bindings'",
            )
        )
        return
    if str(kb[0].get("action_id", "")) != "keybindings":
        issues.append(
            MenuGraphIssue(
                "ia",
                "Settings -> Controls -> Keyboard Bindings must map to action_id 'keybindings'",
            )
        )


def _validate_board_defaults_legacy_topology(
    board_items: tuple[dict[str, object], ...],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    legacy = [
        item
        for item in board_items
        if str(item.get("type", "")).strip().lower() == "legacy_dispatch"
        and str(item.get("action_id", "")) == "settings_legacy_topology_editor"
    ]
    if not legacy:
        issues.append(
            MenuGraphIssue(
                "ia",
                "Legacy topology editor must remain reachable only from Board / Setup Defaults",
            )
        )
        return
    if "legacy" not in str(legacy[0].get("label", "")).strip().lower():
        issues.append(
            MenuGraphIssue(
                "ia",
                "Legacy topology editor row must be explicitly labeled as legacy",
            )
        )


def _validate_explosion_defaults_settings_coverage(
    menus: dict[str, dict[str, object]],
    *,
    issues: list[MenuGraphIssue],
) -> None:
    defaults = default_settings_payload()
    defaults_root = defaults.get("explosion_defaults")
    if not isinstance(defaults_root, dict):
        issues.append(MenuGraphIssue("schema", "defaults.explosion_defaults must be an object"))
        return

    for mode_key in ("2d", "3d", "4d"):
        _validate_explosion_defaults_menu_for_mode(
            menus,
            defaults_root=defaults_root,
            mode_key=mode_key,
            issues=issues,
        )


def _validate_explosion_defaults_menu_for_mode(
    menus: dict[str, dict[str, object]],
    *,
    defaults_root: dict[str, object],
    mode_key: str,
    issues: list[MenuGraphIssue],
) -> None:
    mode_defaults = defaults_root.get(mode_key)
    if not isinstance(mode_defaults, dict):
        issues.append(
            MenuGraphIssue(
                "schema",
                f"defaults.explosion_defaults.{mode_key} must be an object",
            )
        )
        return
    expected_fields = set(mode_defaults.keys())
    menu_id = f"settings_explosion_defaults_{mode_key}"
    raw_items = _menu_items_for_id(
        menus,
        menu_id=menu_id,
        label=menu_id,
        issues=issues,
    )
    if raw_items is None:
        return
    observed, invalid_prefix = _observed_explosion_defaults_fields(
        raw_items,
        mode_key=mode_key,
    )
    for item_id in invalid_prefix:
        issues.append(
            MenuGraphIssue(
                "ia",
                f"{menu_id}:{item_id} setting_id must start with explosion_defaults.{mode_key}.",
            )
        )
    if observed != expected_fields:
        issues.append(
            MenuGraphIssue(
                "ia",
                f"{menu_id} must cover every persisted explosion_defaults field ({_format_explosion_field_diff(expected_fields, observed)})",
            )
        )


def _observed_explosion_defaults_fields(
    raw_items: tuple[dict[str, object], ...],
    *,
    mode_key: str,
) -> tuple[set[str], list[str]]:
    observed: set[str] = set()
    invalid_prefix: list[str] = []
    prefix = f"explosion_defaults.{mode_key}."
    for item in raw_items:
        item_type = str(item.get("type", "")).strip().lower()
        if item_type not in {"toggle", "selector", "slider", "stepper"}:
            continue
        setting_id = str(item.get("setting_id", "")).strip().lower()
        if not setting_id.startswith(prefix):
            invalid_prefix.append(str(item.get("id", "")))
            continue
        remainder = setting_id[len(prefix) :]
        field = remainder.split("[", 1)[0]
        observed.add(field)
    return observed, invalid_prefix


def _format_explosion_field_diff(expected: set[str], observed: set[str]) -> str:
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    detail: list[str] = []
    if missing:
        detail.append("missing: " + ", ".join(missing))
    if extra:
        detail.append("extra: " + ", ".join(extra))
    return "; ".join(detail) if detail else "unknown mismatch"
