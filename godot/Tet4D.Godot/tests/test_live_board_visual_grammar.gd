extends RefCounted

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const CameraPresetScript = preload("res://scripts/presentation/camera_preset.gd")
const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")


func run() -> Array:
	var failures: Array = []
	if CameraPresetScript.ids().size() != 6:
		failures.append("camera preset authority should expose the compact six-preset family")
	var seen := {}
	for id in CameraPresetScript.ids():
		if seen.has(id) or not CameraPresetScript.is_known(str(id)):
			failures.append("camera preset IDs must be unique and authority-owned")
		seen[id] = true
	if ControlFrameMappingScript.for_3d(PI).translation_command("move_z_neg", "relative") != "move_z_neg":
		failures.append("Back preset yaw must preserve viewer-relative forward mapping")
	if ControlFrameMappingScript.for_3d(PI).translation_command("move_z_neg", "absolute") != "move_z_neg":
		failures.append("absolute translation must remain canonical under Back yaw")
	if ReplayVisuals.DEFAULT_LOCKED_CELL_OPACITY != 0.75 or ReplayVisuals.MIN_LOCKED_CELL_OPACITY != 0.35 or ReplayVisuals.MAX_LOCKED_CELL_OPACITY != 1.0:
		failures.append("locked-cell opacity authority must retain its documented default and range")
	return failures
