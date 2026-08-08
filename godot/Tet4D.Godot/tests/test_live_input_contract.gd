extends RefCounted

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const ReplayHudScript = preload("res://scripts/ui/replay_hud.gd")


func run() -> Array:
	var failures: Array = []
	var specs := LiveInputContractScript.action_specs()
	for action_id in ["live_3d_soft_drop", "live_4d_soft_drop"]:
		var spec: Dictionary = specs.get(action_id, {})
		if spec.is_empty() or int(spec.get("display_key", KEY_NONE)) != KEY_CTRL or KEY_SHIFT in spec.get("keys", []):
			failures.append("%s must derive Ctrl-only soft drop from the action authority" % action_id)
		if not KEY_SHIFT in spec.get("forbidden_keys", []):
			failures.append("%s must explicitly reject Shift" % action_id)
	var camera_specs := LiveInputContractScript.camera_control_specs()
	for control_id in ["camera_orbit", "camera_pan", "camera_zoom"]:
		if not camera_specs.has(control_id) or not bool(camera_specs[control_id].get("public", false)):
			failures.append("public camera control %s must have one descriptor" % control_id)
	if LiveInputContractScript.camera_control_for_button(MOUSE_BUTTON_LEFT) != "camera_orbit":
		failures.append("left drag must resolve to camera rotation")
	if LiveInputContractScript.camera_control_for_button(MOUSE_BUTTON_RIGHT) != "camera_pan":
		failures.append("right drag must resolve to camera translation")
	if LiveInputContractScript.camera_control_for_button(MOUSE_BUTTON_WHEEL_UP) != "camera_zoom":
		failures.append("ordinary wheel must resolve to zoom")
	if not LiveInputContractScript.camera_control_for_button(MOUSE_BUTTON_MIDDLE).is_empty():
		failures.append("middle drag must not retain an undocumented pan binding")
	var helper := ReplayHudScript.live_4d_hint_text()
	for required in ["Ctrl Soft Drop", "Left Drag Rotate camera", "Right Drag Translate camera", "Wheel Zoom"]:
		if not helper.contains(required):
			failures.append("helper must render the authoritative control: %s" % required)
	for obsolete in ["Shift +", "Middle / Right", "Shift-wheel"]:
		if helper.to_lower().contains(obsolete.to_lower()):
			failures.append("helper must not advertise obsolete control: %s" % obsolete)
	var expected_basis_keys := {
		"view_xw_neg": KEY_1,
		"view_xw_pos": KEY_2,
		"view_zw_neg": KEY_SEMICOLON,
		"view_zw_pos": KEY_APOSTROPHE,
		"view_zx_neg": KEY_BRACKETLEFT,
		"view_zx_pos": KEY_BRACKETRIGHT,
	}
	var reserved_keys := []
	for action_id in ["live_4d_rotate_xw_neg", "live_4d_rotate_xw_pos", "live_4d_rotate_zw_neg", "live_4d_rotate_zw_pos", "live_4d_soft_drop", "live_4d_hard_drop", "live_4d_camera_yaw_left", "live_4d_camera_yaw_right", "live_4d_camera_pitch_up", "live_4d_camera_pitch_down"]:
		reserved_keys.append_array(specs.get(action_id, {}).get("keys", []))
	for action_id in expected_basis_keys:
		var keycode := int(expected_basis_keys[action_id])
		if specs.get(action_id, {}).get("keys", []) != [keycode]:
			failures.append("%s must reuse the canonical repository basis binding" % action_id)
		if keycode in reserved_keys:
			failures.append("%s must not collide with piece rotation, drop, or camera actions" % action_id)
	return failures
