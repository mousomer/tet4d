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
		var definition := CameraPresetScript.definition(str(id))
		if definition.has("zoom") or definition.has("pan"):
			failures.append("view action %s must not own framing fields" % id)
		seen[id] = true
	if not CameraPresetScript.definition("custom").is_empty() or CameraPresetScript.is_known("custom"):
		failures.append("Custom must not survive as a public or fallback view identity")
	if ControlFrameMappingScript.for_3d(PI).translation_command("move_z_neg", "relative") != "move_z_pos":
		failures.append("Back preset yaw must map Forward to canonical +Z so it recedes")
	if ControlFrameMappingScript.for_3d(PI).translation_command("move_z_neg", "absolute") != "move_z_neg":
		failures.append("absolute translation must remain canonical under Back yaw")
	if ReplayVisuals.DEFAULT_LOCKED_CELL_OPACITY != 0.75 or ReplayVisuals.MIN_LOCKED_CELL_OPACITY != 0.35 or ReplayVisuals.MAX_LOCKED_CELL_OPACITY != 1.0:
		failures.append("locked-cell opacity authority must retain its documented default and range")
	var normal_grid := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_PLAIN, false)
	var contrast_grid := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_PLAIN, true)
	if normal_grid.transparency != BaseMaterial3D.TRANSPARENCY_ALPHA:
		failures.append("normal internal-grid alpha must be an operational material property")
	if normal_grid.albedo_color.a >= 0.5 or contrast_grid.albedo_color.a <= normal_grid.albedo_color.a:
		failures.append("internal grid should remain weak normally and strengthen in High Contrast")
	var outline_thickness := ReplayVisuals.slice_outline_thickness()
	if ReplayVisuals.grid_internal_thickness() >= outline_thickness:
		failures.append("internal grid must remain thinner than the inactive outer wireframe")
	var active_thickness := outline_thickness * ReplayVisuals.ACTIVE_SLICE_FRAME_MULTIPLIER
	if active_thickness <= outline_thickness or active_thickness >= ReplayVisuals.LIVE_3D_ACTIVE_CELL_SCALE * 0.2:
		failures.append("active frame should beat the inactive frame without competing with piece volume")
	return failures
