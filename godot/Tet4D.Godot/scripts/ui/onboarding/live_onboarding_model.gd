extends RefCounted

class_name LiveOnboardingModel

const MODE_STEPS := {
	"live_2d": [
		{"id": "move", "title": "Move the piece", "body": "Move with A/D or Left/Right.", "accepted_commands": ["move_left", "move_right"]},
		{"id": "rotate", "title": "Rotate", "body": "Rotate with W, Up, or X. Use Z for the opposite direction.", "accepted_commands": ["rotate_cw", "rotate_ccw"]},
		{"id": "drop", "title": "Drop", "body": "Use S/Down for Soft Drop. Space locks the piece immediately.", "accepted_commands": ["soft_drop", "hard_drop"]},
		{"id": "system", "title": "System controls", "body": "P pauses. R restarts. Esc returns to the Main Menu.", "accepted_commands": []},
	],
	"live_3d": [
		{"id": "move", "title": "Move across the board", "body": "Movement uses X and Z; falling is separate. Rotations happen in the XY, XZ, and YZ planes.", "accepted_commands": ["move_x_neg", "move_x_pos", "move_z_neg", "move_z_pos"]},
		{"id": "rotate", "title": "Rotate in planes", "body": "Rotate in the XY, XZ, and YZ planes. Start with one plane at a time.", "accepted_commands": ["rotate_xy_neg", "rotate_xy_pos", "rotate_xz_neg", "rotate_xz_pos", "rotate_yz_neg", "rotate_yz_pos"]},
		{"id": "camera", "title": "Move the view", "body": "Camera movement changes only the view, not the piece. Fit View restores orientation.", "accepted_commands": []},
	],
	"live_4d": [
		{"id": "slices", "title": "Read the W slices", "body": "The board is displayed as multiple W slices. Q/E move the piece between them.", "accepted_commands": ["move_w_neg", "move_w_pos"]},
		{"id": "rotate", "title": "Rotate in planes", "body": "Six rotation planes exist. Start with XY and XZ before exploring the others.", "accepted_commands": ["rotate_xy_neg", "rotate_xy_pos", "rotate_xz_neg", "rotate_xz_pos", "rotate_yz_neg", "rotate_yz_pos", "rotate_xw_neg", "rotate_xw_pos", "rotate_yw_neg", "rotate_yw_pos", "rotate_zw_neg", "rotate_zw_pos"]},
		{"id": "camera", "title": "Recover the view", "body": "Camera controls do not move the piece. Double-click or Fit View restores the canonical view.", "accepted_commands": []},
	],
}

var _mode := ""
var _indices := {}
var _dismissed := false
var _enabled := true

func select_mode(mode: String) -> void:
	_mode = mode if MODE_STEPS.has(mode) else ""

func consume_command_result(command: String, status: String) -> bool:
	if _dismissed or _mode.is_empty() or status != "accepted":
		return false
	var step := current_step()
	if step.is_empty() or not step.get("accepted_commands", []).has(command):
		return false
	_indices[_mode] = current_index() + 1
	return true

func dismiss() -> void:
	_dismissed = true

func set_enabled(enabled: bool) -> void:
	_enabled = enabled
	if enabled:
		_dismissed = false

func is_visible() -> bool:
	return _enabled and not _dismissed and not current_step().is_empty()

func current_index() -> int:
	return int(_indices.get(_mode, 0))

func current_step() -> Dictionary:
	var steps: Array = MODE_STEPS.get(_mode, [])
	var index := current_index()
	return steps[index] if index >= 0 and index < steps.size() else {}

func snapshot() -> Dictionary:
	var step := current_step()
	var steps: Array = MODE_STEPS.get(_mode, [])
	return {"mode": _mode, "visible": is_visible(), "enabled": _enabled, "dismissed": _dismissed, "step_index": current_index(), "step_count": steps.size(), "step_id": str(step.get("id", "")), "title": str(step.get("title", "")), "body": str(step.get("body", ""))}
