extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const CameraPresetScript = preload("res://scripts/presentation/camera_preset.gd")
const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")

const LIVE_4D_DIMENSIONS := [5, 7, 3, 2]
const LIVE_4D_INTERIOR_POINT := [2, 3, 1, 0]


func run() -> Array:
	var failures: Array = []
	if CameraRigScript.LIVE_2D_FIT_MARGIN < 1.3 or CameraRigScript.LIVE_3D_FIT_MARGIN < 1.3 or CameraRigScript.LIVE_4D_FIT_MARGIN < 1.3:
		failures.append("live entry fit margins should preserve visible breathing room around the board")
	if CameraRigScript.LIVE_4D_FIT_MARGIN >= 1.4:
		failures.append("live 4D entry fit should keep the W-slice matrix close enough to inspect")
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["camera rig test requires SceneTree"]
	var rig := CameraRigScript.new()
	var camera := Camera3D.new()
	camera.name = "Camera3D"
	rig.add_child(camera)
	tree.root.add_child(rig)
	await tree.process_frame

	rig.fit_bounds({"ok": true, "min": Vector3(-2.0, -2.5, -1.5), "max": Vector3(8.0, 2.5, 1.5)}, 1.14)
	_assert_vector(failures, rig._current_focus, Vector3(3.0, 0.0, 0.0), "fit snaps current focus")
	_assert_float(failures, rig._current_yaw, CameraRigScript.PYTHON_DISPLAY_YAW_RAD, "fit uses Python display yaw")
	_assert_float(failures, rig._current_pitch, CameraRigScript.PYTHON_DISPLAY_PITCH_RAD, "fit uses Python display pitch")
	if camera.projection != Camera3D.PROJECTION_ORTHOGONAL:
		failures.append("camera should use orthographic projection")
	if camera.size <= 5.0 or camera.size >= 10.5:
		failures.append("camera fit should use projected bounds with margin, got size %.3f" % camera.size)

	rig.fit_bounds(
		{"ok": true, "min": Vector3(-2.0, -2.5, -1.5), "max": Vector3(8.0, 2.5, 1.5)},
		1.2,
		CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD,
		CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD,
		CameraPresetScript.ISO,
		"above exterior"
	)
	_assert_float(failures, rig._current_yaw, CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD, "live 3D fit uses canonical yaw")
	_assert_float(failures, rig._current_pitch, CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD, "live 3D fit uses above-board pitch")
	if rig._current_pitch <= 0.0:
		failures.append("live 3D canonical pitch should be above the board, got %.4f" % rig._current_pitch)
	if camera.global_position.y <= rig._current_focus.y:
		failures.append("live 3D camera should sit above the fit focus")
	var status := rig.view_status_text()
	if status.find("Iso") == -1:
		failures.append("live 3D camera status should name the canonical preset")
	if status.find("above") == -1 or status.find("fit OK") == -1 or status.find("ortho") == -1:
		failures.append("live 3D camera status should show orthographic above-board fit state: %s" % status)

	rig.fit_bounds(
		{"ok": true, "min": Vector3(-2.5, -5.0, -2.0), "max": Vector3(23.5, 6.72, 2.0)},
		1.34,
		CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD,
		CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD,
		CameraPresetScript.ISO,
		"fitted W slices",
		true
	)
	_assert_float(failures, rig._current_yaw, CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD, "live 4D fit uses W-slice yaw")
	_assert_float(failures, rig._current_pitch, CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD, "live 4D fit uses W-slice pitch")
	if camera.size <= 20.0:
		failures.append("live 4D camera fit should frame the full W-slice layout, got size %.3f" % camera.size)
	if not bool(rig.presentation_snapshot().get("horizontal_mirrored", false)):
		failures.append("live 4D fixed far-side mount should mirror screen X for board-frame Right")
	_assert_live_4d_fitted_view_contract(failures, rig)
	_assert_live_4d_signed_correspondence(failures, rig)
	status = rig.view_status_text()
	if status.find("Iso") == -1 or status.find("fitted W slices") == -1 or status.find("size") == -1 or status.find("zoom") == -1:
		failures.append("live 4D camera status should name the fitted W-slice preset and zoom diagnostics: %s" % status)
	var fitted_size := camera.size
	rig.zoom(-1.0)
	if camera.size >= fitted_size:
		failures.append("live 4D zoom in should reduce orthographic size, got %.3f from %.3f" % [camera.size, fitted_size])
	if rig.view_status_text().find("manual") == -1 or rig.view_status_text().find("zoom") == -1:
		failures.append("live 4D zoom should mark manual view and expose zoom status")
	var zoomed_in_size := camera.size
	rig.zoom(1.0)
	if camera.size <= zoomed_in_size:
		failures.append("live 4D zoom out should increase orthographic size, got %.3f from %.3f" % [camera.size, zoomed_in_size])
	var yaw_before := rig._current_yaw
	rig.nudge_yaw(CameraRigScript.LIVE_4D_CAMERA_YAW_STEP_RAD)
	if rig._current_yaw <= yaw_before:
		failures.append("generic camera yaw nudge should remain available for non-Live/free inspection")
	if rig.view_status_text().find("manual") == -1:
		failures.append("live 4D camera nudge should mark the view as manual")
	var roll_before := rig._current_roll
	rig.nudge_roll(CameraRigScript.LIVE_4D_CAMERA_ROLL_STEP_RAD)
	if rig._current_roll <= roll_before:
		failures.append("generic camera roll nudge should remain available for free inspection")
	if rig.view_status_text().find("roll") == -1:
		failures.append("live 4D camera status should expose roll diagnostics")
	rig.fit_bounds(
		{"ok": true, "min": Vector3(-2.5, -5.0, -2.0), "max": Vector3(23.5, 6.72, 2.0)},
		1.34,
		CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD,
		CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD,
		CameraPresetScript.ISO,
		"fitted W slices",
		true
	)
	if absf(camera.size - fitted_size) > 0.001:
		failures.append("live 4D Fit View should restore fitted orthographic size, got %.3f expected %.3f" % [camera.size, fitted_size])
	if absf(rig._current_roll) > 0.001:
		failures.append("live 4D Fit View should reset camera roll")
	if rig.view_status_text().find("fit OK") == -1:
		failures.append("live 4D Fit View should restore fitted state")
	var focus_before: Vector3 = rig._target_focus
	rig.pan_focus(Vector3.DOWN * CameraRigScript.LIVE_4D_MATRIX_SCROLL_STEP)
	if rig._target_focus == focus_before or rig.view_status_text().find("matrix scroll") == -1:
		failures.append("4D matrix scrolling should pan presentation focus and report its view state")
	var yaw_before_preset := rig._current_yaw
	if not rig.apply_preset(CameraPresetScript.BACK):
		failures.append("generic Back camera preset should be accepted")
	elif rig.current_preset_id() != CameraPresetScript.BACK or absf(rig._current_yaw - PI) > 0.001:
		failures.append("generic Back preset should retain reusable non-Live outer yaw")
	if rig.apply_preset("unknown"):
		failures.append("unknown camera preset should be rejected")
	if absf(yaw_before_preset - rig._current_yaw) < 0.001:
		failures.append("Back camera preset should be meaningfully distinct from the fitted view")
	_assert_orientation_gizmo_visible_axes_only(failures, rig)

	rig.queue_free()
	await tree.process_frame
	return failures


func _assert_live_4d_fitted_view_contract(failures: Array, rig) -> void:
	var focus_view: Vector3 = rig._camera.to_local(rig._current_focus)
	if focus_view.z >= 0.0:
		failures.append("actual fitted Live 4D collection must remain in front of the camera")
	var right_view: Vector3 = rig.view_space_direction(Vector3.RIGHT)
	if right_view.x <= 0.0:
		failures.append("actual fitted Live 4D view must project board-frame +X screen-right")
	var safe_domain := CameraRigScript.live_4d_pitch_safe_domain()
	var product_min := SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD
	var product_max := SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD
	if product_min <= safe_domain.x or product_max >= safe_domain.y:
		failures.append("normal gameplay pitch range must remain strictly inside theoretical fitted-view boundaries %s" % safe_domain)
	for pitch_case in [
		0.0,
		product_min,
		product_max,
		PI / 6.0,
		-PI / 6.0,
	]:
		var displayed_forward := Basis(Vector3.RIGHT, pitch_case) * Vector3.BACK
		var forward_view: Vector3 = rig.view_space_direction(displayed_forward)
		if -forward_view.z <= 0.0:
			failures.append("actual fitted view Forward must recede at pitch %.3f" % pitch_case)
		if CameraRigScript.live_4d_forward_away_depth(pitch_case) <= 0.0:
			failures.append("analytical fitted-view away depth must stay positive at pitch %.3f" % pitch_case)
	var epsilon := deg_to_rad(0.1)
	if CameraRigScript.live_4d_forward_away_depth(safe_domain.x + epsilon) <= 0.0:
		failures.append("pitch immediately inside the theoretical lower boundary should retain away depth")
	if CameraRigScript.live_4d_forward_away_depth(safe_domain.x - epsilon) >= 0.0:
		failures.append("pitch immediately outside the theoretical lower boundary should invert away depth")
	if CameraRigScript.live_4d_forward_away_depth(safe_domain.y - epsilon) <= 0.0:
		failures.append("pitch immediately inside the theoretical upper boundary should retain away depth")
	if CameraRigScript.live_4d_forward_away_depth(safe_domain.y + epsilon) >= 0.0:
		failures.append("pitch immediately outside the theoretical upper boundary should invert away depth")


func _assert_live_4d_signed_correspondence(failures: Array, rig) -> void:
	for basis in [
		SliceBasis4DScript.identity(),
		SliceBasis4DScript.from_slots([-3, 2, 1, 4]),
	]:
		var mapper = TraceCoordinateMapperScript.new()
		mapper.configure(LIVE_4D_DIMENSIONS, basis)
		for yaw in [0.0, PI * 0.5, PI, -PI * 0.5]:
			var mapping = ControlFrameMappingScript.for_4d(basis, yaw)
			var orientation = SliceLocalOrientationScript.new(yaw, PI / 6.0)
			var right := _mapped_displayed_difference(
				mapper,
				orientation,
				mapping.translation_command("move_x_pos", "relative")
			)
			var forward := _mapped_displayed_difference(
				mapper,
				orientation,
				mapping.translation_command("move_z_neg", "relative")
			)
			var right_view: Vector3 = rig.view_space_direction(right)
			var forward_view: Vector3 = rig.view_space_direction(forward)
			if right_view.x <= 0.0:
				failures.append("signed B %s yaw %.3f Right must remain screen-right in actual fitted view" % [basis.key(), yaw])
			if -forward_view.z <= 0.0:
				failures.append("signed B %s yaw %.3f Forward must remain receding in actual fitted view" % [basis.key(), yaw])


func _mapped_displayed_difference(mapper, orientation, command: String) -> Vector3:
	var delta := _canonical_delta(command)
	var destination := LIVE_4D_INTERIOR_POINT.duplicate()
	for axis in range(4):
		destination[axis] = int(destination[axis]) + int(delta[axis])
	var origin_mapping: Dictionary = mapper.presentation_coordinate(LIVE_4D_INTERIOR_POINT)
	var destination_mapping: Dictionary = mapper.presentation_coordinate(destination)
	var origin_local: Vector3 = mapper.centered_local_point(origin_mapping.get("visible_cell_3d", []))
	var destination_local: Vector3 = mapper.centered_local_point(destination_mapping.get("visible_cell_3d", []))
	return orientation.passive_render_basis() * (destination_local - origin_local)


func _canonical_delta(command: String) -> Array:
	match command:
		"move_x_neg": return [-1, 0, 0, 0]
		"move_x_pos": return [1, 0, 0, 0]
		"move_z_neg": return [0, 0, -1, 0]
		"move_z_pos": return [0, 0, 1, 0]
		_: return [0, 0, 0, 0]


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_float(failures: Array, actual: float, expected: float, label: String) -> void:
	if absf(actual - expected) > 0.001:
		failures.append("%s: expected %.4f, got %.4f" % [label, expected, actual])


func _assert_orientation_gizmo_visible_axes_only(failures: Array, rig) -> void:
	var bases := _reachable_bases()
	if bases.size() != 24:
		failures.append("4D orientation regression must cover all 24 reachable basis states")
		return
	for basis in bases:
		rig.set_orientation_basis(basis)
		var gizmo := rig.get_node_or_null("OrientationGizmo") as Node3D
		if gizmo == null:
			failures.append("orientation gizmo missing for basis %s" % basis.key())
			return
		var arrows := []
		for child in gizmo.get_children():
			if child.name.ends_with("Arrow"):
				arrows.append(child)
		if arrows.size() != 3 or gizmo.get_node_or_null("SliceArrow") != null:
			failures.append("basis %s must render exactly three visible-axis arrows and no slice arrow" % basis.key())
			return
		var visible_axes: Array = basis.indicator_snapshot().get("visible_axes", [])
		var labels := []
		for arrow in arrows:
			labels.append(str(arrow.get_meta("signed_axis", "")))
		for axis in visible_axes:
			if not labels.has(axis):
				failures.append("basis %s gizmo omitted visible axis %s" % [basis.key(), axis])
				return
		if labels.has(basis.slice_axis_label()):
			failures.append("basis %s gizmo must exclude slice axis %s" % [basis.key(), basis.slice_axis_label()])
			return


func _reachable_bases() -> Array:
	var result := []
	var queue := [SliceBasis4DScript.identity()]
	var seen := {}
	while not queue.is_empty():
		var basis = queue.pop_front()
		if seen.has(basis.key()):
			continue
		seen[basis.key()] = true
		result.append(basis)
		for plane in ["xw", "zw", "zx"]:
			for direction in [-1, 1]:
				queue.append(basis.turned(plane, direction))
	return result
