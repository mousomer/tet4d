extends RefCounted

class_name LiveInputContract

const CAMERA_ORBIT_BUTTON := MOUSE_BUTTON_LEFT
const CAMERA_PAN_BUTTON := MOUSE_BUTTON_RIGHT
const CAMERA_ZOOM_BUTTONS := [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]

# This is the public shell-control authority. Runtime input routing and every
# user-facing helper resolve bindings from these stable semantic IDs.
const CAMERA_CONTROL_SPECS := {
	"camera_orbit": {"button": CAMERA_ORBIT_BUTTON, "display": "Left Drag", "helper": "Rotate camera", "context": "live_camera", "public": true},
	"camera_pan": {"button": CAMERA_PAN_BUTTON, "display": "Right Drag", "helper": "Translate camera", "context": "live_camera", "public": true},
	"camera_zoom": {"buttons": CAMERA_ZOOM_BUTTONS, "display": "Wheel", "helper": "Zoom", "context": "live_camera", "public": true},
}

const ACTION_SPECS := {
	"live_move_left": {"keys": [KEY_LEFT, KEY_A], "display_key": KEY_A},
	"live_move_right": {"keys": [KEY_RIGHT, KEY_D], "display_key": KEY_D},
	"live_rotate_cw": {"keys": [KEY_UP, KEY_W, KEY_X], "display_key": KEY_W},
	"live_rotate_ccw": {"keys": [KEY_Z], "display_key": KEY_Z},
	"live_soft_drop": {"keys": [KEY_DOWN, KEY_S], "display_key": KEY_S},
	"live_hard_drop": {"keys": [KEY_SPACE], "display_key": KEY_SPACE},
	"live_hold": {"keys": [KEY_C], "display_key": KEY_C},
	"live_pause": {"keys": [KEY_P], "display_key": KEY_P},
	"live_reset": {"keys": [KEY_R], "display_key": KEY_R},
	"live_2d_move_left": {"keys": [KEY_LEFT], "display_key": KEY_LEFT},
	"live_2d_move_right": {"keys": [KEY_RIGHT], "display_key": KEY_RIGHT},
	"live_2d_rotate_cw": {"keys": [KEY_UP], "display_key": KEY_UP},
	"live_2d_rotate_ccw": {"keys": [KEY_Z], "display_key": KEY_Z},
	"live_2d_soft_drop": {"keys": [KEY_DOWN], "display_key": KEY_DOWN},
	"live_2d_hard_drop": {"keys": [KEY_SPACE], "display_key": KEY_SPACE},
	"live_2d_pause": {"keys": [KEY_P], "display_key": KEY_P},
	"live_3d_move_x_neg": {"keys": [KEY_LEFT, KEY_A], "display_key": KEY_A},
	"live_3d_move_x_pos": {"keys": [KEY_RIGHT, KEY_D], "display_key": KEY_D},
	"live_3d_move_z_neg": {"keys": [KEY_UP, KEY_W], "display_key": KEY_W},
	"live_3d_move_z_pos": {"keys": [KEY_DOWN, KEY_S], "display_key": KEY_S},
	"live_3d_soft_drop": {"keys": [KEY_CTRL], "display_key": KEY_CTRL, "forbidden_keys": [KEY_SHIFT]},
	"live_3d_hard_drop": {"keys": [KEY_SPACE], "display_key": KEY_SPACE},
	"live_3d_rotate_xy_neg": {"keys": [KEY_R], "display_key": KEY_R},
	"live_3d_rotate_xy_pos": {"keys": [KEY_T], "display_key": KEY_T},
	"live_3d_rotate_xz_neg": {"keys": [KEY_F], "display_key": KEY_F},
	"live_3d_rotate_xz_pos": {"keys": [KEY_G], "display_key": KEY_G},
	"live_3d_rotate_yz_neg": {"keys": [KEY_V], "display_key": KEY_V},
	"live_3d_rotate_yz_pos": {"keys": [KEY_B], "display_key": KEY_B},
	"live_3d_pause": {"keys": [KEY_P], "display_key": KEY_P},
	"live_3d_reset": {"keys": [KEY_BACKSPACE], "display_key": KEY_BACKSPACE},
	"live_4d_move_x_neg": {"keys": [KEY_LEFT, KEY_A], "display_key": KEY_A},
	"live_4d_move_x_pos": {"keys": [KEY_RIGHT, KEY_D], "display_key": KEY_D},
	"live_4d_move_z_neg": {"keys": [KEY_UP, KEY_W], "display_key": KEY_W},
	"live_4d_move_z_pos": {"keys": [KEY_DOWN, KEY_S], "display_key": KEY_S},
	"live_4d_move_w_neg": {"keys": [KEY_Q], "display_key": KEY_Q},
	"live_4d_move_w_pos": {"keys": [KEY_E], "display_key": KEY_E},
	"live_4d_soft_drop": {"keys": [KEY_CTRL], "display_key": KEY_CTRL, "forbidden_keys": [KEY_SHIFT]},
	"live_4d_hard_drop": {"keys": [KEY_SPACE], "display_key": KEY_SPACE},
	"live_4d_rotate_xy_neg": {"keys": [KEY_R], "display_key": KEY_R},
	"live_4d_rotate_xy_pos": {"keys": [KEY_T], "display_key": KEY_T},
	"live_4d_rotate_xz_neg": {"keys": [KEY_F], "display_key": KEY_F},
	"live_4d_rotate_xz_pos": {"keys": [KEY_G], "display_key": KEY_G},
	"live_4d_rotate_yz_neg": {"keys": [KEY_V], "display_key": KEY_V},
	"live_4d_rotate_yz_pos": {"keys": [KEY_B], "display_key": KEY_B},
	"live_4d_rotate_xw_neg": {"keys": [KEY_Y], "display_key": KEY_Y},
	"live_4d_rotate_xw_pos": {"keys": [KEY_U], "display_key": KEY_U},
	"live_4d_rotate_yw_neg": {"keys": [KEY_H], "display_key": KEY_H},
	"live_4d_rotate_yw_pos": {"keys": [KEY_J], "display_key": KEY_J},
	"live_4d_rotate_zw_neg": {"keys": [KEY_N], "display_key": KEY_N},
	"live_4d_rotate_zw_pos": {"keys": [KEY_M], "display_key": KEY_M},
	"live_4d_pause": {"keys": [KEY_P], "display_key": KEY_P},
	"live_4d_reset": {"keys": [KEY_BACKSPACE], "display_key": KEY_BACKSPACE},
	"live_4d_camera_pitch_up": {"keys": [KEY_I], "display_key": KEY_I},
	"live_4d_camera_pitch_down": {"keys": [KEY_K], "display_key": KEY_K},
	"live_4d_camera_yaw_left": {"keys": [KEY_O], "display_key": KEY_O},
	"live_4d_camera_yaw_right": {"keys": [KEY_L], "display_key": KEY_L},
	"live_4d_camera_zoom_in": {"keys": [KEY_EQUAL, KEY_PLUS, KEY_KP_ADD], "display_key": KEY_EQUAL},
	"live_4d_camera_zoom_out": {"keys": [KEY_MINUS, KEY_KP_SUBTRACT], "display_key": KEY_MINUS},
	# Existing repository-wide view action IDs are reused for exact Stage 54C
	# basis turns. Piece rotations retain their separate live_4d_rotate_* IDs.
	"view_xw_neg": {"keys": [KEY_1], "display_key": KEY_1},
	"view_xw_pos": {"keys": [KEY_2], "display_key": KEY_2},
	"view_zw_neg": {"keys": [KEY_SEMICOLON], "display_key": KEY_SEMICOLON},
	"view_zw_pos": {"keys": [KEY_APOSTROPHE], "display_key": KEY_APOSTROPHE},
	"view_zx_neg": {"keys": [KEY_BRACKETLEFT], "display_key": KEY_BRACKETLEFT},
	"view_zx_pos": {"keys": [KEY_BRACKETRIGHT], "display_key": KEY_BRACKETRIGHT},
	"reset": {"keys": [KEY_0], "display_key": KEY_0},
}


static func action_specs() -> Dictionary:
	return ACTION_SPECS.duplicate(true)


static func camera_control_specs() -> Dictionary:
	return CAMERA_CONTROL_SPECS.duplicate(true)


static func camera_control_for_button(button: MouseButton) -> String:
	for control_id in CAMERA_CONTROL_SPECS:
		var spec: Dictionary = CAMERA_CONTROL_SPECS[control_id]
		if int(spec.get("button", -1)) == button or button in spec.get("buttons", []):
			return control_id
	return ""


static func is_camera_button(button: MouseButton) -> bool:
	return not camera_control_for_button(button).is_empty()


static func camera_helper_items() -> Array:
	var items: Array = []
	for control_id in ["camera_orbit", "camera_pan", "camera_zoom"]:
		var spec: Dictionary = CAMERA_CONTROL_SPECS[control_id]
		items.append([str(spec["display"]), str(spec["helper"])])
	return items


static func live_4d_pointer_helper_items() -> Array:
	return [
		[str(CAMERA_CONTROL_SPECS["camera_orbit"]["display"]), "Orient slices"],
		[str(CAMERA_CONTROL_SPECS["camera_pan"]["display"]), "Translate framing"],
		[str(CAMERA_CONTROL_SPECS["camera_zoom"]["display"]), "Zoom"],
	]


static func display_key(action_name: String) -> String:
	return _display_key(action_name)


static func control_hint_groups(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Array:
	match mode:
		"live_2d":
			return _live_2d_groups(control_frame)
		"live_3d":
			return _live_3d_groups(control_frame)
		"live_4d":
			return _live_4d_groups(basis_snapshot, control_frame)
		_:
			return []


# The permanent cockpit strip selects the movement and rotation groups through
# metadata on the existing authoritative help groups. It therefore consumes
# the same action identities, applicability, plane labels, and display bindings
# rather than maintaining a second inventory.
static func piece_control_groups(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Array:
	var result: Array = []
	for source_group in control_hint_groups(mode, basis_snapshot, control_frame):
		var role := str(source_group.get("cockpit_role", ""))
		if role in ["translate", "rotate"]:
			result.append(source_group.duplicate(true))
	return result


# The live cockpit is a progressive-disclosure view of the same public action
# contract, not a second binding table. Visible action buttons own Fit, Reset,
# Restart, navigation, and exact 4D re-slicing, so passive cockpit help omits
# those conceptual duplicates while the full How to Play surface stays intact.
static func cockpit_hint_groups(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Array:
	var groups := control_hint_groups(mode, basis_snapshot, control_frame)
	var result: Array = []
	for source_group in groups:
		var group: Dictionary = source_group.duplicate(true)
		var group_name := str(group.get("group", ""))
		if group_name == "Navigation" or (mode == "live_4d" and group_name == "90° View Rotation"):
			continue
		var items: Array = []
		for item in group.get("items", []):
			var action_label := str(item[1]) if item.size() > 1 else ""
			if action_label.begins_with("Fit View") or action_label.begins_with("Reset View") or action_label == "Restart Game":
				continue
			items.append(item)
		if items.is_empty():
			continue
		group["items"] = items
		if group_name == "Camera":
			group["group"] = "View gestures"
		result.append(group)
	return result


static func _live_2d_groups(control_frame: Dictionary = {}) -> Array:
	var legacy := control_frame.is_empty()
	var relative := str(control_frame.get("translation_frame", "relative")) == "relative"
	var horizontal := str(control_frame.get("horizontal_axis", "+X"))
	var movement_label := "Move left / right" if legacy else ("Left / Right [%s]" % horizontal if relative else "X− / X+")
	var movement_meta := {"cockpit_direction": "horizontal", "signed_axis": horizontal if relative else "+X"}
	return [
		{"group": "Piece movement", "cockpit_role": "translate", "note": "Controls follow the current view." if relative else "Canonical X axis.", "items": [[_pair("live_move_left", "live_move_right"), movement_label, movement_meta], [_pair("live_2d_move_left", "live_2d_move_right"), movement_label, movement_meta]]},
		{"group": "Piece rotation", "cockpit_role": "rotate", "items": [[_all_keys("live_rotate_cw"), "Rotate clockwise"], [_display_key("live_rotate_ccw"), "Rotate counter-clockwise"]]},
		{"group": "Drop", "items": [[_all_keys("live_soft_drop"), "Soft Drop"], [_display_key("live_hard_drop"), "Hard Drop"]]},
		{"group": "Piece management", "items": [[_display_key("live_hold"), "Hold"]]},
		{"group": "Camera", "items": [["F", "Fit View (framing only)"], [_display_key("reset"), "Reset View (restore flat canonical view)"]]},
		{"group": "Session", "items": [[_display_key("live_pause"), "Pause"], [_display_key("live_reset"), "Restart Game"]]},
		{"group": "Navigation", "items": [["Tab", "Play 3D"], ["Esc", "Main Menu"]]},
	]


static func _live_3d_groups(control_frame: Dictionary = {}) -> Array:
	var legacy := control_frame.is_empty()
	var relative := str(control_frame.get("translation_frame", "relative")) == "relative"
	var rotation_relative := str(control_frame.get("rotation_frame", "relative")) == "relative"
	var horizontal := str(control_frame.get("horizontal_axis", "+X"))
	var depth := str(control_frame.get("depth_axis", "+Z"))
	var move_rows := [
		[_pair("live_3d_move_x_neg", "live_3d_move_x_pos"), "X− / X+", {"cockpit_direction": "horizontal", "signed_axis": "+X"}],
		[_pair("live_3d_move_z_neg", "live_3d_move_z_pos"), "Z− / Z+", {"cockpit_direction": "depth", "signed_axis": "+Z"}],
	] if legacy or not relative else [
		[_pair("live_3d_move_x_neg", "live_3d_move_x_pos"), "Left / Right [%s]" % horizontal, {"cockpit_direction": "horizontal", "signed_axis": horizontal}],
		[_pair("live_3d_move_z_neg", "live_3d_move_z_pos"), "Forward / Back [%s]" % depth, {"cockpit_direction": "depth", "signed_axis": depth}],
	]
	var rotation_note := "Planes follow the current view." if rotation_relative else "Canonical XYZ planes."
	return [
		{"group": "Piece movement", "cockpit_role": "translate", "note": "Controls follow the current view; Forward recedes and Back approaches." if relative else "Canonical X/Z axes.", "items": move_rows},
		{"group": "Piece rotation", "cockpit_role": "rotate", "note": rotation_note, "items": [[_pair("live_3d_rotate_xy_neg", "live_3d_rotate_xy_pos"), "Rotate XY"], [_pair("live_3d_rotate_xz_neg", "live_3d_rotate_xz_pos"), "Rotate XZ"], [_pair("live_3d_rotate_yz_neg", "live_3d_rotate_yz_pos"), "Rotate YZ"]]},
		{"group": "Drop", "items": [[_display_key("live_3d_soft_drop"), "Soft Drop"], [_display_key("live_3d_hard_drop"), "Hard Drop"]]},
		{"group": "Piece management", "items": [[_display_key("live_hold"), "Hold"]]},
		{"group": "Camera", "items": camera_helper_items() + [["Double-click", "Fit View (framing only)"], [_display_key("reset"), "Reset View (restore canonical view)"]]},
		{"group": "Session", "items": [[_display_key("live_3d_pause"), "Pause"], [_display_key("live_3d_reset"), "Restart Game"]]},
		{"group": "Navigation", "items": [["Tab", "Play 4D"], ["Esc", "Main Menu"]]},
	]


static func _live_4d_groups(basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Array:
	var legacy := control_frame.is_empty()
	var relative := str(control_frame.get("translation_frame", "relative")) == "relative"
	var rotation_relative := str(control_frame.get("rotation_frame", "relative")) == "relative"
	var visible_axes: Array = basis_snapshot.get("visible_axes", ["X", "+Y", "Z"])
	var horizontal_axis := str(control_frame.get("horizontal_axis", visible_axes[0] if visible_axes.size() > 0 else "+X"))
	var depth_axis := str(control_frame.get("depth_axis", visible_axes[2] if visible_axes.size() > 2 else "+Z"))
	var slice_axis := str(control_frame.get("slice_axis", basis_snapshot.get("slice_axis", "+W")))
	var move_rows := [
		[_pair("live_4d_move_x_neg", "live_4d_move_x_pos", " / "), "Visible X - / +", {"cockpit_direction": "horizontal", "signed_axis": "+X"}],
		[_pair("live_4d_move_z_neg", "live_4d_move_z_pos", " / "), "Visible Z - / +", {"cockpit_direction": "depth", "signed_axis": "+Z"}],
		[_pair("live_4d_move_w_neg", "live_4d_move_w_pos", " / "), "Slice W - / +", {"cockpit_direction": "slice", "signed_axis": "+W"}],
	] if legacy else ([
		[_pair("live_4d_move_x_neg", "live_4d_move_x_pos", " / "), "Left / Right [%s]" % horizontal_axis, {"cockpit_direction": "horizontal", "signed_axis": horizontal_axis}],
		[_pair("live_4d_move_z_neg", "live_4d_move_z_pos", " / "), "Forward / Back [%s]" % depth_axis, {"cockpit_direction": "depth", "signed_axis": depth_axis}],
		[_pair("live_4d_move_w_neg", "live_4d_move_w_pos", " / "), "Slice - / + [%s]" % slice_axis, {"cockpit_direction": "slice", "signed_axis": slice_axis}],
	] if relative else [
		[_pair("live_4d_move_x_neg", "live_4d_move_x_pos", " / "), "X− / X+", {"cockpit_direction": "horizontal", "signed_axis": "+X"}],
		[_pair("live_4d_move_z_neg", "live_4d_move_z_pos", " / "), "Z− / Z+", {"cockpit_direction": "depth", "signed_axis": "+Z"}],
		[_pair("live_4d_move_w_neg", "live_4d_move_w_pos", " / "), "W− / W+", {"cockpit_direction": "slice", "signed_axis": "+W"}],
	])
	return [
		{"group": "Piece movement", "cockpit_role": "translate", "note": "Controls follow the current view." if relative else "Canonical X/Z/W axes.", "items": move_rows},
		{"group": "Piece rotation", "cockpit_role": "rotate", "note": "Left: CCW · Right: CW" if legacy else ("Left: CCW · Right: CW · Planes follow the current view." if rotation_relative else "Left: CCW · Right: CW · Canonical XY/XZ/YZ/XW/YW/ZW planes."), "items": [[_pair("live_4d_rotate_xy_neg", "live_4d_rotate_xy_pos", " / "), "XY"], [_pair("live_4d_rotate_xz_neg", "live_4d_rotate_xz_pos", " / "), "XZ"], [_pair("live_4d_rotate_yz_neg", "live_4d_rotate_yz_pos", " / "), "YZ"], [_pair("live_4d_rotate_xw_neg", "live_4d_rotate_xw_pos", " / "), "XW"], [_pair("live_4d_rotate_yw_neg", "live_4d_rotate_yw_pos", " / "), "YW"], [_pair("live_4d_rotate_zw_neg", "live_4d_rotate_zw_pos", " / "), "ZW"]]},
		{"group": "90° View Rotation", "note": "Exact presentation basis; Y stays down", "items": [[_pair("view_xw_neg", "view_xw_pos", " / "), "XW - / + (re-slice)"], [_pair("view_zw_neg", "view_zw_pos", " / "), "ZW - / + (re-slice)"], [_pair("view_zx_neg", "view_zx_pos", " / "), "ZX - / +"], [_display_key("reset"), "Reset View (basis, slice orientation, framing)"]]},
		{"group": "Slice orientation", "items": [[_pair("live_4d_camera_pitch_up", "live_4d_camera_pitch_down", " / "), "Pitch up / down"], [_pair("live_4d_camera_yaw_left", "live_4d_camera_yaw_right", " / "), "Yaw left / right"]]},
		{"group": "Framing", "items": [["%s / = / +" % _display_key("live_4d_camera_zoom_out"), "Zoom out / in"], ["Double-click", "Fit View (framing only)"]]},
		{"group": "Pointer", "items": live_4d_pointer_helper_items()},
		{"group": "Drop", "items": [[_display_key("live_4d_soft_drop"), "Soft Drop"], [_display_key("live_4d_hard_drop"), "Hard Drop"]]},
		{"group": "Piece management", "items": [[_display_key("live_hold"), "Hold"]]},
		{"group": "Session", "items": [[_display_key("live_4d_pause"), "Pause"], [_display_key("live_4d_reset"), "Restart Game"]]},
		{"group": "Navigation", "items": [["Tab", "Replay Demos"], ["Esc", "Main Menu"]]},
	]


static func _pair(first_action: String, second_action: String, separator: String = "/") -> String:
	return "%s%s%s" % [_display_key(first_action), separator, _display_key(second_action)]


static func _display_key(action_name: String) -> String:
	var spec: Dictionary = ACTION_SPECS.get(action_name, {})
	return _key_label(int(spec.get("display_key", KEY_NONE)))


static func _all_keys(action_name: String) -> String:
	var spec: Dictionary = ACTION_SPECS.get(action_name, {})
	var labels: Array[String] = []
	for keycode in spec.get("keys", []):
		labels.append(_key_label(int(keycode)))
	return "/".join(labels)


static func _key_label(keycode: int) -> String:
	match keycode:
		KEY_LEFT:
			return "Left"
		KEY_RIGHT:
			return "Right"
		KEY_UP:
			return "Up"
		KEY_DOWN:
			return "Down"
		KEY_SPACE:
			return "Space"
		KEY_CTRL:
			return "Ctrl"
		KEY_SHIFT:
			return "Shift"
		KEY_BACKSPACE:
			return "Backspace"
		KEY_COMMA:
			return ","
		KEY_PERIOD:
			return "."
		KEY_EQUAL:
			return "="
		KEY_MINUS:
			return "-"
		KEY_SEMICOLON:
			return ";"
		KEY_APOSTROPHE:
			return "'"
		KEY_BRACKETLEFT:
			return "["
		KEY_BRACKETRIGHT:
			return "]"
		_:
			return OS.get_keycode_string(keycode)
