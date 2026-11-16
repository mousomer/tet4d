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
	"explorer_reject_hold": {"keys": [KEY_C], "display_key": KEY_C, "context": "explorer"},
	"explorer_reject_soft_drop": {"keys": [KEY_SHIFT, KEY_CTRL], "display_key": KEY_SHIFT, "context": "explorer"},
	"explorer_move_x_neg": {"keys": [KEY_LEFT, KEY_A], "display_key": KEY_A, "context": "explorer"},
	"explorer_move_x_pos": {"keys": [KEY_RIGHT, KEY_D], "display_key": KEY_D, "context": "explorer"},
	"explorer_move_z_neg": {"keys": [KEY_UP, KEY_W], "display_key": KEY_W, "context": "explorer"},
	"explorer_move_z_pos": {"keys": [KEY_DOWN, KEY_S], "display_key": KEY_S, "context": "explorer"},
	"explorer_2d_move_y_neg": {"keys": [KEY_UP, KEY_W], "display_key": KEY_W, "context": "explorer"},
	"explorer_2d_move_y_pos": {"keys": [KEY_DOWN, KEY_S], "display_key": KEY_S, "context": "explorer"},
	"explorer_move_w_neg": {"keys": [KEY_Q], "display_key": KEY_Q, "context": "explorer"},
	"explorer_move_w_pos": {"keys": [KEY_E], "display_key": KEY_E, "context": "explorer"},
	"explorer_move_y_neg": {"keys": [KEY_Z], "display_key": KEY_Z, "context": "explorer"},
	"explorer_move_y_pos": {"keys": [KEY_X], "display_key": KEY_X, "context": "explorer"},
	"explorer_retry": {"keys": [KEY_BACKSPACE], "display_key": KEY_BACKSPACE, "context": "explorer"},
	"explorer_reset_view": {"keys": [KEY_0], "display_key": KEY_0, "context": "explorer"},
	"explorer_camera_pitch_up": {"keys": [KEY_I], "display_key": KEY_I, "context": "explorer"},
	"explorer_camera_pitch_down": {"keys": [KEY_K], "display_key": KEY_K, "context": "explorer"},
	"explorer_camera_yaw_left": {"keys": [KEY_O], "display_key": KEY_O, "context": "explorer"},
	"explorer_camera_yaw_right": {"keys": [KEY_L], "display_key": KEY_L, "context": "explorer"},
	"explorer_camera_zoom_in": {"keys": [KEY_EQUAL, KEY_PLUS, KEY_KP_ADD], "display_key": KEY_EQUAL, "context": "explorer"},
	"explorer_camera_zoom_out": {"keys": [KEY_MINUS, KEY_KP_SUBTRACT], "display_key": KEY_MINUS, "context": "explorer"},
	"explorer_view_xz_neg": {"keys": [KEY_1], "display_key": KEY_1, "context": "explorer"},
	"explorer_view_xz_pos": {"keys": [KEY_2], "display_key": KEY_2, "context": "explorer"},
	"explorer_view_xw_neg": {"keys": [KEY_3], "display_key": KEY_3, "context": "explorer"},
	"explorer_view_xw_pos": {"keys": [KEY_4], "display_key": KEY_4, "context": "explorer"},
	"explorer_view_zw_neg": {"keys": [KEY_5], "display_key": KEY_5, "context": "explorer"},
	"explorer_view_zw_pos": {"keys": [KEY_6], "display_key": KEY_6, "context": "explorer"},
	"explorer_rotate_xy_neg": {"keys": [KEY_R], "display_key": KEY_R, "context": "explorer"},
	"explorer_rotate_xy_pos": {"keys": [KEY_T], "display_key": KEY_T, "context": "explorer"},
	"explorer_rotate_xz_neg": {"keys": [KEY_F], "display_key": KEY_F, "context": "explorer"},
	"explorer_rotate_xz_pos": {"keys": [KEY_G], "display_key": KEY_G, "context": "explorer"},
	"explorer_rotate_yz_neg": {"keys": [KEY_V], "display_key": KEY_V, "context": "explorer"},
	"explorer_rotate_yz_pos": {"keys": [KEY_B], "display_key": KEY_B, "context": "explorer"},
	"explorer_rotate_xw_neg": {"keys": [KEY_Y], "display_key": KEY_Y, "context": "explorer"},
	"explorer_rotate_xw_pos": {"keys": [KEY_U], "display_key": KEY_U, "context": "explorer"},
	"explorer_rotate_yw_neg": {"keys": [KEY_H], "display_key": KEY_H, "context": "explorer"},
	"explorer_rotate_yw_pos": {"keys": [KEY_J], "display_key": KEY_J, "context": "explorer"},
	"explorer_rotate_zw_neg": {"keys": [KEY_N], "display_key": KEY_N, "context": "explorer"},
	"explorer_rotate_zw_pos": {"keys": [KEY_M], "display_key": KEY_M, "context": "explorer"},
	"explorer_fit_view": {"keys": [KEY_9], "display_key": KEY_9, "context": "explorer"},
	"explorer_move_up": {"keys": [KEY_Z], "display_key": KEY_Z, "context": "explorer"},
	"explorer_move_down": {"keys": [KEY_X], "display_key": KEY_X, "context": "explorer"},
	"explorer_replace_piece": {"keys": [KEY_SPACE, KEY_P], "display_key": KEY_SPACE, "context": "explorer"},
	"explorer_view_xy_neg": {"keys": [KEY_1], "shift": true, "display_key": KEY_1, "context": "explorer"},
	"explorer_view_xy_pos": {"keys": [KEY_2], "shift": true, "display_key": KEY_2, "context": "explorer"},
	"explorer_view_yz_neg": {"keys": [KEY_3], "shift": true, "display_key": KEY_3, "context": "explorer"},
	"explorer_view_yz_pos": {"keys": [KEY_4], "shift": true, "display_key": KEY_4, "context": "explorer"},
	"explorer_view_yw_neg": {"keys": [KEY_5], "shift": true, "display_key": KEY_5, "context": "explorer"},
	"explorer_view_yw_pos": {"keys": [KEY_6], "shift": true, "display_key": KEY_6, "context": "explorer"},
	"explorer_slice_neg": {"keys": [KEY_BRACKETLEFT], "display_key": KEY_BRACKETLEFT, "context": "explorer"},
	"explorer_slice_pos": {"keys": [KEY_BRACKETRIGHT], "display_key": KEY_BRACKETRIGHT, "context": "explorer"},
	"shell_toggle_fullscreen": {"keys": [KEY_F11], "alt_keys": [KEY_ENTER], "display_key": KEY_F11},
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
	"live_3d_soft_drop": {"keys": [KEY_SHIFT, KEY_CTRL], "display_key": KEY_SHIFT},
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
	"live_4d_soft_drop": {"keys": [KEY_SHIFT, KEY_CTRL], "display_key": KEY_SHIFT},
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
	"view_zx_neg": {"keys": [KEY_1], "display_key": KEY_1},
	"view_zx_pos": {"keys": [KEY_2], "display_key": KEY_2},
	"view_xw_neg": {"keys": [KEY_3], "display_key": KEY_3},
	"view_xw_pos": {"keys": [KEY_4], "display_key": KEY_4},
	"view_zw_neg": {"keys": [KEY_5], "display_key": KEY_5},
	"view_zw_pos": {"keys": [KEY_6], "display_key": KEY_6},
	"reset": {"keys": [KEY_0], "display_key": KEY_0},
}

# One semantic inventory owns every normal-game rotation pair. Consumers use
# this metadata for input routing and public labels instead of duplicating a
# camera-only list beside the piece-control list.
const ROTATION_CONTROL_SPECS := [
	{"owner": "piece", "plane": "XY", "negative_action": "live_4d_rotate_xy_neg", "positive_action": "live_4d_rotate_xy_pos"},
	{"owner": "piece", "plane": "XZ", "negative_action": "live_4d_rotate_xz_neg", "positive_action": "live_4d_rotate_xz_pos"},
	{"owner": "piece", "plane": "YZ", "negative_action": "live_4d_rotate_yz_neg", "positive_action": "live_4d_rotate_yz_pos"},
	{"owner": "piece", "plane": "XW", "negative_action": "live_4d_rotate_xw_neg", "positive_action": "live_4d_rotate_xw_pos"},
	{"owner": "piece", "plane": "YW", "negative_action": "live_4d_rotate_yw_neg", "positive_action": "live_4d_rotate_yw_pos"},
	{"owner": "piece", "plane": "ZW", "negative_action": "live_4d_rotate_zw_neg", "positive_action": "live_4d_rotate_zw_pos"},
	{"owner": "camera", "plane": "XZ", "negative_action": "view_zx_neg", "positive_action": "view_zx_pos", "re_slices": false},
	{"owner": "camera", "plane": "XW", "negative_action": "view_xw_neg", "positive_action": "view_xw_pos", "re_slices": true},
	{"owner": "camera", "plane": "ZW", "negative_action": "view_zw_neg", "positive_action": "view_zw_pos", "re_slices": true},
]


const EXPLORER_CAMERA_ROTATION_SPECS := [
	{"plane": "XY", "negative_action": "explorer_view_xy_neg", "positive_action": "explorer_view_xy_pos"},
	{"plane": "YZ", "negative_action": "explorer_view_yz_neg", "positive_action": "explorer_view_yz_pos"},
	{"plane": "YW", "negative_action": "explorer_view_yw_neg", "positive_action": "explorer_view_yw_pos"},
]


# Shared by Explorer's interactive VIEW helper and its keyboard dispatcher.
static func practice_view_control_groups(mode: String) -> Array:
	return explorer_profile(int(mode.trim_prefix("live_").trim_suffix("d"))).view_groups


static func _explorer_view_groups(mode: String) -> Array:
	var groups: Array = []
	if mode == "live_4d":
		var rotations: Array = []
		var camera_specs := EXPLORER_CAMERA_ROTATION_SPECS + [
			{"plane": "XZ", "negative_action": "explorer_view_xz_neg", "positive_action": "explorer_view_xz_pos"},
			{"plane": "XW", "negative_action": "explorer_view_xw_neg", "positive_action": "explorer_view_xw_pos"},
			{"plane": "ZW", "negative_action": "explorer_view_zw_neg", "positive_action": "explorer_view_zw_pos"},
		]
		for plane in ["XY", "XZ", "YZ", "XW", "YW", "ZW"]:
			for spec in camera_specs:
				if spec.plane == plane:
					rotations.append(_practice_view_pair(plane, spec.negative_action, spec.positive_action, "basis_%s_neg" % plane.to_lower(), "basis_%s_pos" % plane.to_lower()))
		groups.append({"cockpit_role": "view_exact", "items": rotations})
	var framing := {"cockpit_role": "view_framing", "items": [
		_practice_view_pair("Zoom", "explorer_camera_zoom_out", "explorer_camera_zoom_in", "zoom_out", "zoom_in"),
		[_display_key("explorer_fit_view"), "Fit", {"operation": "Fit", "command": "view_fit", "action": "explorer_fit_view"}],
		[_display_key("explorer_reset_view"), "Reset", {"operation": "Reset", "command": "view_reset", "action": "explorer_reset_view"}],
	]}
	if mode == "live_2d":
		return [framing]
	groups.append({"cockpit_role": "view_orient", "items": [
		_practice_view_pair("Yaw", "explorer_camera_yaw_left", "explorer_camera_yaw_right", "look_yaw_left", "look_yaw_right"),
		_practice_view_pair("Pitch", "explorer_camera_pitch_up", "explorer_camera_pitch_down", "look_pitch_up", "look_pitch_down"),
	]})
	groups.append(framing)
	if mode == "live_4d":
		groups.append({"cockpit_role": "view_slice", "items": [_practice_view_pair("Slice", "explorer_slice_neg", "explorer_slice_pos", "slice_neg", "slice_pos")]})
	groups.append({"cockpit_role": "view_pointer", "items": camera_helper_items()})
	return groups


static func _practice_view_pair(label: String, negative_action: String, positive_action: String, negative_command: String, positive_command: String) -> Array:
	return [_pair(negative_action, positive_action), label, {
		"operation": label, "negative_action": negative_action, "positive_action": positive_action,
		"negative_command": negative_command, "positive_command": positive_command,
		"negative_binding": _display_key(negative_action), "positive_binding": _display_key(positive_action),
	}]


static func action_specs() -> Dictionary:
	return ACTION_SPECS.duplicate(true)


static func camera_control_specs() -> Dictionary:
	return CAMERA_CONTROL_SPECS.duplicate(true)


static func rotation_control_specs(owner: String = "") -> Array:
	var result: Array = []
	for raw_spec in ROTATION_CONTROL_SPECS:
		var spec: Dictionary = raw_spec
		if owner.is_empty() or str(spec.get("owner", "")) == owner:
			result.append(spec.duplicate(true))
	return result


static func exact_camera_rotation_specs() -> Array:
	return rotation_control_specs("camera")


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
		items.append([str(spec["display"]), str(spec["helper"]), {"operation": {"camera_orbit": "Orient", "camera_pan": "Translate", "camera_zoom": "Zoom"}[control_id]}])
	return items


static func live_4d_pointer_helper_items() -> Array:
	return [
		[str(CAMERA_CONTROL_SPECS["camera_orbit"]["display"]), "Orient slices", {"operation": "Orient"}],
		[str(CAMERA_CONTROL_SPECS["camera_pan"]["display"]), "Translate framing", {"operation": "Translate"}],
		[str(CAMERA_CONTROL_SPECS["camera_zoom"]["display"]), "Zoom", {"operation": "Zoom"}],
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


# The permanent cockpit strip selects gameplay and session groups through
# metadata on the existing authoritative help groups. It therefore consumes
# the same action identities, applicability, plane labels, and display bindings
# rather than maintaining a second inventory.
static func piece_control_groups(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Array:
	var result: Array = []
	var groups := control_hint_groups(mode, basis_snapshot, control_frame)
	for expected_role in ["translate", "drop", "rotate", "hold", "session"]:
		for source_group in groups:
			if str(source_group.get("cockpit_role", "")) == expected_role:
				result.append(source_group.duplicate(true))
	return result


# Rail, wide and compact deck layouts share one semantic inventory.
static func play_legend_groups(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Array:
	return piece_control_groups(mode, basis_snapshot, control_frame)


# Presentation/input inventory only; native providers retain geometry/topology truth.
# Each call returns detached data. Legacy bindings and labels are deliberately
# preserved until the separately approved visible-key phase.
static func explorer_profile(dimension: int, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Dictionary:
	assert(dimension in [2, 3, 4])
	var mode := "live_%dd" % dimension
	var axes: Array = []
	for label in "xyzw".substr(0, dimension):
		var prefix := "explorer_2d_move_y_" if dimension == 2 and label == "y" else "explorer_move_%s_" % label
		var axis := {"label": label, "negative_command": "move_%s_neg" % label, "positive_command": "move_%s_pos" % label, "negative_action": prefix + "neg", "positive_action": prefix + "pos", "alias_actions": [], "relative": dimension > 2 and label != "y", "repeat": dimension == 2 or label != "y"}
		if dimension == 2 and label == "y":
			axis.alias_actions = ["explorer_move_y_neg", "explorer_move_y_pos"]
		axes.append(axis)
	var planes: Array = []
	for spec in rotation_control_specs("piece"):
		var label: String = str(spec.plane).to_lower()
		if (dimension < 4 and "w" in label) or (dimension < 3 and "z" in label): continue
		planes.append({"label": label, "negative_command": "rotate_%s_neg" % label, "positive_command": "rotate_%s_pos" % label, "negative_action": "explorer_rotate_" + label + "_neg", "positive_action": "explorer_rotate_" + label + "_pos", "relative": dimension > 2})
	var session := {
		"replace": {"label": "Replace piece", "command": "replace", "action": "explorer_replace_piece"},
		"target": {"label": "New target", "command": "target", "action": ""},
		"retry": {"label": "Retry object", "command": "retry", "action": "explorer_retry"},
		"play": {"label": "Play", "command": "play", "action": ""},
	}
	var actions: Array = []
	for record in axes + planes:
		actions.append([record.negative_action, record.negative_command])
		actions.append([record.positive_action, record.positive_command])
	actions.append([session.retry.action, session.retry.command])
	var topologies: Array = []
	for record in [["Bounded", "bounded"], ["Cylinder · wrap X", "cylinder_x"], ["Cylinder · wrap Y", "cylinder_y"], ["Torus", "torus"], ["Möbius strip", "mobius"], ["Klein bottle", "klein"], ["Projective · experimental", "projective"], ["Sphere", "sphere_adjacent_positive"]]:
		topologies.append({"label": record[0], "id": record[1], "disabled": dimension != 2 and record[1] != "bounded"})
	var view_groups := _explorer_view_groups(mode)
	return {"input_actions": _explorer_input_actions(axes, planes, session, view_groups), "axes": axes, "rotation_planes": planes, "session": session, "piece_actions": actions, "topologies": topologies, "view_groups": view_groups, "piece_groups": _explorer_piece_groups(mode, axes, planes, session, basis_snapshot, control_frame), "capabilities": {"camera_orbit": dimension > 2, "basis_turns": dimension == 4, "slice": dimension == 4, "relative_frame": dimension > 2, "topology_selector": dimension == 2}}


static func _explorer_piece_groups(mode: String, axes: Array, planes: Array, session: Dictionary, basis_snapshot: Dictionary, control_frame: Dictionary) -> Array:
	# One structure for every dimension: planar moves (compass), the vertical
	# Up/Down pair, rotation planes and the practice session keys. 2D has no
	# camera, so its axes are always canonical.
	var groups: Array = []
	var flat := mode == "live_2d"
	var legacy := control_frame.is_empty()
	var relative := not flat and str(control_frame.get("translation_frame", "relative")) == "relative"
	var rotation_relative := not flat and str(control_frame.get("rotation_frame", "relative")) == "relative"
	var visible_axes: Array = basis_snapshot.get("visible_axes", ["X", "+Y", "Z"])
	var axis_values := {"x": str(control_frame.get("horizontal_axis", visible_axes[0] if mode == "live_4d" else "+X")), "z": str(control_frame.get("depth_axis", visible_axes[2] if mode == "live_4d" else "+Z")), "w": str(control_frame.get("slice_axis", basis_snapshot.get("slice_axis", "+W")))}
	var move_rows: Array = []
	var planar: Array = ["x"] if flat else (["x", "z", "w"] if mode == "live_4d" else ["x", "z"])
	for label in planar:
		var axis: Dictionary = axes.filter(func(record): return record.label == label)[0]
		var direction: String = {"x": "horizontal", "z": "depth", "w": "slice"}[label]
		var signed_axis: String = axis_values[label] if relative and not legacy else "+" + label.to_upper()
		var text: String = ("Visible X - / +" if label == "x" else ("Visible Z - / +" if label == "z" else "Slice W - / +")) if legacy and mode == "live_4d" else (({"x": "Left / Right", "z": "Forward / Back", "w": "Slice - / +"}[label] + " [%s]" % signed_axis) if relative and not legacy else label.to_upper() + "− / " + label.to_upper() + "+")
		move_rows.append([_pair(axis.negative_action, axis.positive_action, " / " if mode == "live_4d" else "/"), text, {"cockpit_direction": direction, "signed_axis": signed_axis}])
	var y: Dictionary = axes.filter(func(record): return record.label == "y")[0]
	if flat:
		# 2D's Y is already on the compass; Z/X remain keyboard aliases.
		move_rows.append([_pair(y.negative_action, y.positive_action, "/"), "Y− / Y+", {"cockpit_direction": "screen_vertical", "signed_axis": "+Y"}])
	else:
		move_rows.append([_pair(y.negative_action, y.positive_action), "Y− / Y+", {"cockpit_direction": "vertical", "signed_axis": "+Y"}])
	var rotation_rows: Array = []
	for plane in planes:
		var text: String = ("" if mode == "live_4d" else "Rotate ") + str(plane.label).to_upper()
		var row: Array = [_pair(plane.negative_action, plane.positive_action, " / " if mode == "live_4d" else "/"), text]
		if mode == "live_4d": row.append({"operation": str(plane.label).to_upper()})
		rotation_rows.append(row)
	var movement_note := "Canonical X/Y axes." if flat else (("Controls follow the current view; Forward recedes and Back approaches." if mode == "live_3d" else "Controls follow the current view.") if relative else ("Canonical X/Z axes." if mode == "live_3d" else "Canonical X/Z/W axes."))
	var rotation_note := "Canonical XY plane." if flat else (("Planes follow the current view." if rotation_relative else "Canonical XYZ planes.") if mode == "live_3d" else ("Left: CCW · Right: CW" if legacy else ("Left: CCW · Right: CW · Planes follow the current view." if rotation_relative else "Left: CCW · Right: CW · Canonical XY/XZ/YZ/XW/YW/ZW planes.")))
	groups.append({"group": "Piece movement", "cockpit_role": "translate", "note": movement_note, "items": move_rows})
	groups.append({"group": "Piece rotation", "cockpit_role": "rotate", "note": rotation_note, "items": rotation_rows})
	groups.append({"group": "Practice", "cockpit_role": "session", "items": [[_display_key(session.replace.action), session.replace.label], [_display_key(session.retry.action), session.retry.label]]})
	return groups


static func _explorer_input_actions(axes: Array, planes: Array, session: Dictionary, view_groups: Array) -> Array:
	var actions: Array = [{"action": session.replace.action, "command": session.replace.command, "kind": "session"}]
	for group in view_groups:
		for item in group.items:
			var metadata: Dictionary = item[2] if item.size() > 2 else {}
			for prefix in ["negative_", "positive_", ""]:
				var action := str(metadata.get(prefix + "action", ""))
				if not action.is_empty(): actions.append({"action": action, "command": metadata[prefix + "command"], "kind": "view", "exact": group.cockpit_role == "view_exact"})
	for collection in [axes, planes]:
		for record in collection:
			for prefix in ["negative_", "positive_"]:
				actions.append({"action": record[prefix + "action"], "command": record[prefix + "command"], "kind": "move" if collection == axes else "rotate", "relative": record.relative, "repeat": record.get("repeat", false)})
			# A 2D alias pair (Z/X for Y) dispatches the same command and shares
			# its axis's held-key repeat state.
			var aliases: Array = record.get("alias_actions", [])
			for index in aliases.size():
				var prefix := "negative_" if index == 0 else "positive_"
				actions.append({"action": aliases[index], "command": record[prefix + "command"], "kind": "move", "relative": record.relative, "repeat": record.get("repeat", false), "repeat_action": record[prefix + "action"]})
	if axes.size() > 2:
		# Preserve existing explicit rejection feedback for Play-only keys.
		actions.append({"action": "explorer_reject_hold", "command": "hold", "kind": "rejected"})
		actions.append({"action": "explorer_reject_soft_drop", "command": "soft_drop", "kind": "rejected"})
	actions.append({"action": session.retry.action, "command": session.retry.command, "kind": "session"})
	return actions


# Passive cockpit consumers select role metadata, never prose labels or a
# second action/binding inventory. Only Live 4D currently exposes this deck.
static func view_control_groups(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> Array:
	var result: Array = []
	for source_group in control_hint_groups(mode, basis_snapshot, control_frame):
		var role := str(source_group.get("cockpit_role", ""))
		if role.begins_with("view_"):
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
		if group_name == "Navigation" or (mode == "live_4d" and group_name == "Exact camera rotation"):
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
		{"group": "Drop", "cockpit_role": "drop", "items": [[_all_keys("live_soft_drop"), "Soft Drop", {"operation": "Soft"}], [_display_key("live_hard_drop"), "Hard Drop", {"operation": "Hard"}]]},
		{"group": "Piece management", "cockpit_role": "hold", "items": [[_display_key("live_hold"), "Hold"]]},
		{"group": "Framing", "cockpit_role": "view_framing", "items": [["F", "Fit View (framing only)", {"operation": "Fit"}], [_display_key("reset"), "Reset View (restore flat canonical view)", {"operation": "Reset"}]]},
		{"group": "Session", "cockpit_role": "session", "items": [[_display_key("live_pause"), "Pause"], [_display_key("live_reset"), "Restart Game"]]},
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
		{"group": "Drop", "cockpit_role": "drop", "items": [[_display_key("live_3d_soft_drop"), "Soft Drop", {"operation": "Soft"}], [_display_key("live_3d_hard_drop"), "Hard Drop", {"operation": "Hard"}]]},
		{"group": "Piece management", "cockpit_role": "hold", "items": [[_display_key("live_hold"), "Hold"]]},
		{"group": "Framing", "cockpit_role": "view_framing", "items": [["Double-click", "Fit View (framing only)", {"operation": "Fit"}], [_display_key("reset"), "Reset View (restore canonical view)", {"operation": "Reset"}]]},
		{"group": "Pointer", "cockpit_role": "view_pointer", "items": camera_helper_items()},
		{"group": "Session", "cockpit_role": "session", "items": [[_display_key("live_3d_pause"), "Pause"], [_display_key("live_3d_reset"), "Restart Game"]]},
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
		{"group": "Drop", "cockpit_role": "drop", "items": [[_display_key("live_4d_soft_drop"), "Soft Drop", {"operation": "Soft"}], [_display_key("live_4d_hard_drop"), "Hard Drop", {"operation": "Hard"}]]},
		{"group": "Piece rotation", "cockpit_role": "rotate", "note": "Left: CCW · Right: CW" if legacy else ("Left: CCW · Right: CW · Planes follow the current view." if rotation_relative else "Left: CCW · Right: CW · Canonical XY/XZ/YZ/XW/YW/ZW planes."), "items": _rotation_hint_items("piece")},
		{"group": "Exact camera rotation", "cockpit_role": "view_exact", "note": "Exact presentation basis; Y stays down", "items": _exact_camera_rotation_hint_items()},
		{"group": "Slice orientation", "cockpit_role": "view_orient", "items": [[_pair("live_4d_camera_pitch_up", "live_4d_camera_pitch_down", " / "), "Pitch up / down", {"operation": "Pitch"}], [_pair("live_4d_camera_yaw_left", "live_4d_camera_yaw_right", " / "), "Yaw left / right", {"operation": "Yaw"}]]},
		{"group": "Framing", "cockpit_role": "view_framing", "items": [["%s / %s" % [_all_keys("live_4d_camera_zoom_out", " / "), _all_keys("live_4d_camera_zoom_in", " / ")], "Zoom out / in", {"operation": "Zoom"}], ["Double-click", "Fit View (framing only)", {"operation": "Fit"}], [_display_key("reset"), "Reset View (basis, slice orientation, framing)", {"operation": "Reset"}]]},
		{"group": "Pointer", "cockpit_role": "view_pointer", "items": live_4d_pointer_helper_items()},
		{"group": "Piece management", "cockpit_role": "hold", "items": [[_display_key("live_hold"), "Hold"]]},
		{"group": "Session", "cockpit_role": "session", "items": [[_display_key("live_4d_pause"), "Pause"], [_display_key("live_4d_reset"), "Restart Game"]]},
		{"group": "Navigation", "items": [["Tab", "Replay Demos"], ["Esc", "Main Menu"]]},
	]


static func _rotation_hint_items(owner: String) -> Array:
	var items: Array = []
	for spec in rotation_control_specs(owner):
		items.append([
			_pair(str(spec["negative_action"]), str(spec["positive_action"]), " / "),
			str(spec["plane"]),
			{"operation": str(spec["plane"])},
		])
	return items


# One pass over one descriptor collection: labels and key pairs cannot drift
# apart by index because both are read from the same spec.
static func _exact_camera_rotation_hint_items() -> Array:
	var items: Array = []
	for spec in exact_camera_rotation_specs():
		var suffix := " (re-slice)" if bool(spec.get("re_slices", false)) else ""
		items.append([
			_pair(str(spec["negative_action"]), str(spec["positive_action"]), " / "),
			"%s - / +%s" % [str(spec["plane"]), suffix],
			{"operation": str(spec["plane"])},
		])
	return items


static func _pair(first_action: String, second_action: String, separator: String = "/") -> String:
	return "%s%s%s" % [_display_key(first_action), separator, _display_key(second_action)]


static func _display_key(action_name: String) -> String:
	var spec: Dictionary = ACTION_SPECS.get(action_name, {})
	var events := binding_events(action_name)
	for event in events:
		if event is InputEventKey and event.keycode == int(spec.get("display_key", KEY_NONE)) and not event.get_modifiers_mask():
			return _binding_label(event)
	return _binding_label(events[0]) if not events.is_empty() else "Unbound"


static func _all_keys(action_name: String, separator: String = "/") -> String:
	var labels: Array[String] = []
	for event in binding_events(action_name):
		var label := _binding_label(event)
		if not labels.has(label):
			labels.append(label)
	return separator.join(labels) if not labels.is_empty() else "Unbound"


# Defaults seed absent actions. Once registered, even an empty event list is
# authoritative: clearing/rebinding must never resurrect a printed default.
static func binding_events(action_name: String) -> Array:
	if InputMap.has_action(action_name):
		return InputMap.action_get_events(action_name)
	var events: Array = []
	for keycode in ACTION_SPECS.get(action_name, {}).get("keys", []):
		var event := InputEventKey.new()
		event.keycode = int(keycode)
		event.shift_pressed = bool(ACTION_SPECS.get(action_name, {}).get("shift", false))
		events.append(event)
	for keycode in ACTION_SPECS.get(action_name, {}).get("alt_keys", []):
		var event := InputEventKey.new()
		event.keycode = int(keycode)
		event.alt_pressed = true
		events.append(event)
	return events


static func binding_signature() -> String:
	var bindings: Array = []
	for action_name in ACTION_SPECS:
		bindings.append([action_name, binding_events(action_name).map(func(event): return event.as_text())])
	return JSON.stringify(bindings)


static func _binding_label(event: InputEvent) -> String:
	if not event is InputEventKey:
		return event.as_text()
	var key := event as InputEventKey
	var label := _key_label(key.keycode if key.keycode != KEY_NONE else key.physical_keycode)
	var modifiers: Array[String] = []
	if key.ctrl_pressed: modifiers.append("Ctrl")
	if key.alt_pressed: modifiers.append("Alt")
	if key.shift_pressed: modifiers.append("Shift")
	if key.meta_pressed: modifiers.append("Meta")
	modifiers.append(label)
	return "+".join(modifiers)


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
		KEY_PLUS, KEY_KP_ADD:
			return "+"
		KEY_MINUS, KEY_KP_SUBTRACT:
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
