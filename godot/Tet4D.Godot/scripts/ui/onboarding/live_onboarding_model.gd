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
		{"id": "same_object", "title": "Same object, rotated view", "body": "Use one 90° View Rotation control. Watch the presentation change while the falling object stays the same.", "predicate": "basis_changed", "completion": "Same object. Exact view rotation."},
		{"id": "useful_slice", "title": "Choose a clearer slice", "body": "Re-slice once more. Choose X or Z as the slice direction so W becomes visible inside each board.", "predicate": "non_w_slice_used", "completion": "A different slicing direction can expose structure."},
		{"id": "find_coordinate", "title": "Find a stable coordinate", "body": "The marked coordinate is fixed in 4D. Use Q/E to navigate the current signed slice axis and follow its layer frame.", "predicate": "slice_navigation_used", "target_coordinate": [2, 7, 2, 0], "accepted_commands": ["move_x_neg", "move_x_pos", "move_z_neg", "move_z_pos", "move_w_neg", "move_w_pos"], "completion": "The coordinate stayed fixed; only its displayed layer changed."},
		{"id": "match_basis", "title": "Match the target basis", "body": "Reach View: +W · +Y · +Z / Slice: -X using exact quarter turns.", "predicate": "basis_equals_target", "target_basis": [4, 2, 3, -1], "completion": "Exact basis matched."},
		{"id": "inspect_placement", "title": "Inspect a difficult placement", "body": "Rotate the view once more to inspect the placement without rotating the piece. Y remains down.", "predicate": "basis_changed", "completion": "Inspection complete. The gameplay state did not rotate."},
	],
}

var _mode := ""
var _indices := {}
var _dismissed := false
var _enabled := true
var _last_basis_key := ""
var _step_entry_basis_key := ""
var _current_slice_axis := "w"

func select_mode(mode: String) -> void:
	_mode = mode if MODE_STEPS.has(mode) else ""

func consume_command_result(command: String, status: String) -> bool:
	if _dismissed or _mode.is_empty() or status != "accepted":
		return false
	var step := current_step()
	if step.is_empty() or not step.get("accepted_commands", []).has(command):
		return false
	if str(step.get("predicate", "")) == "slice_navigation_used":
		if not command.begins_with("move_%s_" % _current_slice_axis):
			return false
	_indices[_mode] = current_index() + 1
	_step_entry_basis_key = _last_basis_key
	return true


func consume_basis_state(basis_snapshot: Dictionary) -> bool:
	if _dismissed or _mode != "live_4d":
		return false
	var basis_key := str(basis_snapshot.get("key", ""))
	if basis_key.is_empty():
		return false
	_current_slice_axis = str(basis_snapshot.get("slice_axis", "+W")).replace("+", "").replace("-", "").to_lower()
	if _last_basis_key.is_empty():
		_last_basis_key = basis_key
		_step_entry_basis_key = basis_key
		return false
	if basis_key == _last_basis_key:
		return false
	_last_basis_key = basis_key
	var step := current_step()
	var predicate := str(step.get("predicate", ""))
	var complete := false
	match predicate:
		"basis_changed":
			complete = basis_key != _step_entry_basis_key
		"non_w_slice_used":
			complete = str(basis_snapshot.get("slice_axis", "+W")).replace("+", "").replace("-", "") != "W"
		"basis_equals_target":
			complete = basis_snapshot.get("slots", []) == step.get("target_basis", [])
	if not complete:
		return false
	_indices[_mode] = current_index() + 1
	_step_entry_basis_key = basis_key
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
	return {"mode": _mode, "visible": is_visible(), "enabled": _enabled, "dismissed": _dismissed, "step_index": current_index(), "step_count": steps.size(), "step_id": str(step.get("id", "")), "title": str(step.get("title", "")), "body": str(step.get("body", "")), "predicate": str(step.get("predicate", "")), "target_basis": step.get("target_basis", []).duplicate(), "target_coordinate": step.get("target_coordinate", []).duplicate(), "completion": str(step.get("completion", ""))}
