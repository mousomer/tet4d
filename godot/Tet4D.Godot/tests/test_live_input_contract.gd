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
	return failures
