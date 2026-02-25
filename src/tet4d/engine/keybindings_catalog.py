from __future__ import annotations

from collections.abc import Sequence


_BINDING_GROUP_LABELS = {
    "system": "General / System",
    "game": "Gameplay",
    "camera": "Camera / View",
}

_BINDING_GROUP_DESCRIPTIONS = {
    "system": "Global actions available in all modes.",
    "game": "Piece translation, drop, and rotation actions.",
    "camera": "Board/view camera orbit, projection, and zoom controls.",
}

_COMMON_ACTION_DESCRIPTIONS = {
    "toggle_grid": "Cycle grid display mode.",
    "menu": "Open the in-game pause menu.",
    "restart": "Restart the current run.",
    "quit": "Quit the current game or application flow.",
    "help": "Open in-game help and explanations.",
    "move_x_neg": "Move active piece left on the x axis.",
    "move_x_pos": "Move active piece right on the x axis.",
    "move_z_neg": "Move active piece away from viewer (default view).",
    "move_z_pos": "Move active piece closer to viewer (default view).",
    "move_w_neg": "Move active piece to previous W-layer board.",
    "move_w_pos": "Move active piece to next W-layer board.",
    "move_y_neg": "Exploration mode: move active piece up along gravity axis.",
    "move_y_pos": "Exploration mode: move active piece down along gravity axis.",
    "soft_drop": "Move piece one gravity step down.",
    "hard_drop": "Drop piece immediately to lock position.",
    "rotate_xy_pos": "Rotate piece in x-y plane (+90).",
    "rotate_xy_neg": "Rotate piece in x-y plane (-90).",
    "rotate_xz_pos": "Rotate piece in x-z plane (+90).",
    "rotate_xz_neg": "Rotate piece in x-z plane (-90).",
    "rotate_yz_pos": "Rotate piece in y-z plane (+90).",
    "rotate_yz_neg": "Rotate piece in y-z plane (-90).",
    "rotate_xw_pos": "Rotate piece in x-w plane (+90).",
    "rotate_xw_neg": "Rotate piece in x-w plane (-90).",
    "rotate_yw_pos": "Rotate piece in y-w plane (+90).",
    "rotate_yw_neg": "Rotate piece in y-w plane (-90).",
    "rotate_zw_pos": "Rotate piece in z-w plane (+90).",
    "rotate_zw_neg": "Rotate piece in z-w plane (-90).",
    "yaw_fine_neg": "Yaw camera by -15 degrees.",
    "yaw_fine_pos": "Yaw camera by +15 degrees.",
    "yaw_neg": "Yaw camera by -90 degrees.",
    "yaw_pos": "Yaw camera by +90 degrees.",
    "pitch_neg": "Pitch camera by -90 degrees.",
    "pitch_pos": "Pitch camera by +90 degrees.",
    "view_xw_neg": "Turn view in x-w plane by -90 degrees (camera only).",
    "view_xw_pos": "Turn view in x-w plane by +90 degrees (camera only).",
    "view_zw_neg": "Turn view in z-w plane by -90 degrees (camera only).",
    "view_zw_pos": "Turn view in z-w plane by +90 degrees (camera only).",
    "zoom_in": "Zoom camera in.",
    "zoom_out": "Zoom camera out.",
    "cycle_projection": "Cycle projection mode.",
    "reset": "Reset camera/view transform.",
}


def binding_group_label(group: str) -> str:
    return _BINDING_GROUP_LABELS.get(group, group.replace("_", " ").title())


def binding_group_description(group: str) -> str:
    return _BINDING_GROUP_DESCRIPTIONS.get(group, "Control category.")


def binding_action_description(action: str) -> str:
    return _COMMON_ACTION_DESCRIPTIONS.get(action, action.replace("_", " "))


def binding_action_ids() -> tuple[str, ...]:
    return tuple(sorted(_COMMON_ACTION_DESCRIPTIONS.keys()))


_GAMEPLAY_TRANSLATION_ACTIONS = {"soft_drop", "hard_drop"}


def gameplay_action_category(action: str) -> str:
    if action.startswith("rotate_"):
        return "rotation"
    if action.startswith("move_") or action in _GAMEPLAY_TRANSLATION_ACTIONS:
        return "translation"
    return "other"


def partition_gameplay_actions(
    actions: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    ordered = sorted(actions)
    translation = tuple(
        action
        for action in ordered
        if gameplay_action_category(action) == "translation"
    )
    rotation = tuple(
        action for action in ordered if gameplay_action_category(action) == "rotation"
    )
    other = tuple(
        action for action in ordered if gameplay_action_category(action) == "other"
    )
    return translation, rotation, other
