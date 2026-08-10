extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const CameraPresetScript = preload("res://scripts/presentation/camera_preset.gd")
const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")

const LIVE_4D_DIMENSIONS := [5, 7, 3, 2]
const LIVE_4D_INTERIOR_POINT := [2, 3, 1, 0]
const SCREEN_RIGHT_TOLERANCE_PX := 0.5
const AWAY_DEPTH_TOLERANCE := 0.0001
const ANALYTICAL_DEPTH_TOLERANCE := 0.000005
const REJECTED_COUNTEREXAMPLE_AWAY_DEPTH := -0.1826245
const EXPECTED_SAFE_PITCH_MIN_DEG := -42.479647
const EXPECTED_SAFE_PITCH_MAX_DEG := 86.240113


func run() -> Array:
	var failures: Array = []
	if CameraRigScript.LIVE_2D_FIT_MARGIN < 1.3 or CameraRigScript.LIVE_3D_FIT_MARGIN < 1.3 or CameraRigScript.LIVE_4D_FIT_MARGIN < 1.3:
		failures.append("live entry fit margins should preserve visible breathing room around the board")
	if CameraRigScript.LIVE_4D_FIT_MARGIN >= 1.4:
		failures.append("live 4D entry fit should keep the W-slice matrix close enough to inspect")
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["camera rig test requires SceneTree"]
	var viewport := SubViewport.new()
	viewport.size = Vector2i(960, 540)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	tree.root.add_child(viewport)
	var world_root := Node3D.new()
	viewport.add_child(world_root)
	var presentation_root := Node3D.new()
	presentation_root.name = "Live4DPresentationRoot"
	world_root.add_child(presentation_root)
	var rig := CameraRigScript.new()
	var camera := Camera3D.new()
	camera.name = "Camera3D"
	camera.current = true
	rig.add_child(camera)
	world_root.add_child(rig)
	rig.set_world_presentation_root(presentation_root)
	await tree.process_frame

	rig.fit_bounds({"ok": true, "min": Vector3(-2.0, -2.5, -1.5), "max": Vector3(8.0, 2.5, 1.5)}, 1.14)
	_assert_vector(failures, rig._current_focus, Vector3(3.0, 0.0, 0.0), "fit snaps current focus")
	_assert_float(failures, rig._current_yaw, CameraRigScript.PYTHON_DISPLAY_YAW_RAD, "fit uses Python display yaw")
	_assert_float(failures, rig._current_pitch, CameraRigScript.PYTHON_DISPLAY_PITCH_RAD, "fit uses Python display pitch")
	if camera.projection != Camera3D.PROJECTION_ORTHOGONAL:
		failures.append("camera should use orthographic projection")
	if camera.size <= 5.0 or camera.size >= 10.5:
		failures.append("camera fit should use projected bounds with margin, got size %.3f" % camera.size)
	if bool(rig.presentation_snapshot().get("horizontal_reflection_active", false)) or presentation_root.transform != Transform3D.IDENTITY:
		failures.append("generic replay fit must leave the world presentation unreflected")

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
	if not bool(rig.presentation_snapshot().get("horizontal_reflection_active", false)):
		failures.append("live 4D fixed far-side mount should activate the rendered-world reflection")
	if camera.scale != Vector3.ONE:
		failures.append("Camera3D scale must remain identity; reflection belongs to the rendered-world V path")
	if presentation_root.transform.basis.determinant() >= 0.0:
		failures.append("Live-4D presentation root must carry an actual orientation-reversing world transform")
	_assert_reflected_fit_enclosure(failures, rig, presentation_root, {"min": Vector3(-2.5, -5.0, -2.0), "max": Vector3(23.5, 6.72, 2.0)})
	_assert_rejected_pitch_only_counterexample(failures, rig, presentation_root)
	_assert_live_4d_fitted_view_contract(failures, rig, presentation_root)
	_assert_live_4d_signed_correspondence(failures, rig, presentation_root)
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
	_assert_pan_and_preset_reflection_contract(failures, rig, presentation_root)
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
	if bool(rig.presentation_snapshot().get("horizontal_reflection_active", false)) or presentation_root.transform != Transform3D.IDENTITY:
		failures.append("generic camera presets must not retain Live-4D presentation reflection")
	if rig.apply_preset("unknown"):
		failures.append("unknown camera preset should be rejected")
	if absf(yaw_before_preset - rig._current_yaw) < 0.001:
		failures.append("Back camera preset should be meaningfully distinct from the fitted view")
	rig.set_presentation_preferences(1.5, true, 0.0)
	rig.fit_bounds(
		{"ok": true, "min": Vector3(-2.5, -5.0, -2.0), "max": Vector3(23.5, 6.72, 2.0)},
		1.34,
		CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD,
		CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD,
		CameraPresetScript.ISO,
		"fitted W slices",
		true
	)
	rig.pan_focus(Vector3(2.0, -1.0, 0.0))
	rig.zoom(-1.0)
	rig.nudge_roll(0.25)
	rig.clear_presentation_state()
	var cleared := rig.presentation_snapshot()
	if bool(cleared.get("horizontal_reflection_active", true)) or presentation_root.transform != Transform3D.IDENTITY:
		failures.append("presentation teardown must remove reflection authority immediately")
	if cleared.get("target_focus") != Vector3.ZERO or not is_equal_approx(float(cleared.get("zoom_multiplier", 0.0)), 1.0) or not is_equal_approx(float(cleared.get("target_roll", 1.0)), 0.0):
		failures.append("presentation teardown must clear focus, zoom, and roll state")
	if camera.projection != Camera3D.PROJECTION_ORTHOGONAL or not is_equal_approx(camera.size, CameraRigScript.DEFAULT_ORTHOGRAPHIC_SIZE):
		failures.append("presentation teardown must restore the canonical orthographic projection")
	if not is_equal_approx(float(cleared.get("sensitivity_factor", 0.0)), 1.5) or not bool(cleared.get("invert_y", false)) or not is_equal_approx(float(cleared.get("interpolation_scale", 1.0)), 0.0):
		failures.append("presentation teardown must preserve camera and reduced-motion preferences")
	_assert_orientation_gizmo_visible_axes_only(failures, rig)

	viewport.queue_free()
	await tree.process_frame
	return failures


func _assert_rejected_pitch_only_counterexample(failures: Array, rig, presentation_root: Node3D) -> void:
	var basis = SliceBasis4DScript.identity()
	var mapper = TraceCoordinateMapperScript.new()
	mapper.configure(LIVE_4D_DIMENSIONS, basis)
	var yaw := deg_to_rad(46.0)
	var pitch := deg_to_rad(-60.0)
	var mapping = ControlFrameMappingScript.for_4d(basis, yaw)
	if mapping.yaw_quarter_turn != 1:
		failures.append("46-degree defect reproduction must resolve Forward through q=1")
		return
	var orientation = SliceLocalOrientationScript.new(yaw, pitch)
	var command: String = mapping.translation_command("move_z_neg", "relative")
	var displayed_points := _mapped_displayed_points(mapper, orientation, command)
	var origin_world: Vector3 = presentation_root.to_global(displayed_points[0])
	var destination_world: Vector3 = presentation_root.to_global(displayed_points[1])
	var origin_view: Vector3 = rig.camera_space_point(origin_world)
	var destination_view: Vector3 = rig.camera_space_point(destination_world)
	var away_depth := (origin_view.z - destination_view.z) / origin_world.distance_to(destination_world)
	if away_depth >= -0.000001:
		failures.append(
			"rejected pitch-only policy counterexample must have negative away depth: "
			+ "theta=46deg q=1 pitch=-60deg away_depth=%.9f" % away_depth
		)
	var analytical_depth := CameraRigScript.live_4d_semantic_forward_away_depth(yaw, pitch)
	if absf(away_depth - analytical_depth) > ANALYTICAL_DEPTH_TOLERANCE:
		failures.append(
			"counterexample production depth %.9f must match residual-yaw helper %.9f"
			% [away_depth, analytical_depth]
		)
	if absf(away_depth - REJECTED_COUNTEREXAMPLE_AWAY_DEPTH) > ANALYTICAL_DEPTH_TOLERANCE:
		failures.append(
			"counterexample corrected production depth %.9f must retain expected %.7f"
			% [away_depth, REJECTED_COUNTEREXAMPLE_AWAY_DEPTH]
		)


func _assert_live_4d_fitted_view_contract(failures: Array, rig, presentation_root: Node3D) -> void:
	var focus_view: Vector3 = rig._camera.to_local(rig._current_focus)
	if focus_view.z >= 0.0:
		failures.append("actual fitted Live 4D collection must remain in front of the camera")
	var representative_origin := presentation_root.to_global(Vector3(3.0, 0.0, 0.0))
	var representative_right := presentation_root.to_global(Vector3(4.0, 0.0, 0.0))
	if rig.is_world_point_behind(representative_origin) or rig.is_world_point_behind(representative_right):
		failures.append("screen-right projection probes must be in front of the fitted camera")
	else:
		var origin_screen: Vector2 = rig.project_world_point(representative_origin)
		var right_screen: Vector2 = rig.project_world_point(representative_right)
		if right_screen.x - origin_screen.x <= SCREEN_RIGHT_TOLERANCE_PX:
			failures.append("actual fitted Camera3D projection must place reflected board-frame +X screen-right")
	var safe_domain := CameraRigScript.live_4d_all_yaw_safe_pitch_domain()
	var product_min := SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD
	var product_max := SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD
	if absf(rad_to_deg(safe_domain.x) - EXPECTED_SAFE_PITCH_MIN_DEG) > 0.0005 or absf(rad_to_deg(safe_domain.y) - EXPECTED_SAFE_PITCH_MAX_DEG) > 0.0005:
		failures.append("corrected production camera must retain the derived strict pitch interval, got %s" % safe_domain)
	if product_min <= safe_domain.x or product_max >= safe_domain.y:
		failures.append("normal gameplay pitch range must remain strictly inside all-yaw fitted-view boundaries %s" % safe_domain)
	for pitch_case in [
		0.0,
		product_min,
		product_max,
		PI / 6.0,
		-PI / 6.0,
	]:
		if CameraRigScript.live_4d_worst_case_semantic_forward_away_depth(pitch_case) <= 0.0:
			failures.append("all-yaw fitted-view away depth must stay positive at pitch %.3f" % pitch_case)
	var epsilon := deg_to_rad(0.1)
	if CameraRigScript.live_4d_worst_case_semantic_forward_away_depth(safe_domain.x + epsilon) <= 0.0:
		failures.append("pitch immediately inside the all-yaw lower boundary should retain away depth")
	if CameraRigScript.live_4d_worst_case_semantic_forward_away_depth(safe_domain.x - epsilon) >= 0.0:
		failures.append("pitch immediately outside the all-yaw lower boundary should invert away depth")
	if CameraRigScript.live_4d_worst_case_semantic_forward_away_depth(safe_domain.y - epsilon) <= 0.0:
		failures.append("pitch immediately inside the all-yaw upper boundary should retain away depth")
	if CameraRigScript.live_4d_worst_case_semantic_forward_away_depth(safe_domain.y + epsilon) >= 0.0:
		failures.append("pitch immediately outside the all-yaw upper boundary should invert away depth")
	if rad_to_deg(product_min - safe_domain.x) < 2.4:
		failures.append("selected lower pitch policy must retain its documented non-trivial angular margin")


func _assert_live_4d_signed_correspondence(failures: Array, rig, presentation_root: Node3D) -> void:
	var yaw_cases := [
		{"degrees": 0.0, "turn": 0},
		{"degrees": 44.0, "turn": 0},
		{"degrees": 45.0, "turn": 0},
		{"degrees": 46.0, "turn": 1},
		{"degrees": 90.0, "turn": 1},
		{"degrees": 134.0, "turn": 1},
		{"degrees": 135.0, "turn": 2},
		{"degrees": 136.0, "turn": 2},
		{"degrees": 180.0, "turn": 2},
		{"degrees": -44.0, "turn": 0},
		{"degrees": -45.0, "turn": 0},
		{"degrees": -46.0, "turn": 3},
		{"degrees": -90.0, "turn": 3},
		{"degrees": -134.0, "turn": 3},
		{"degrees": -135.0, "turn": 2},
		{"degrees": -136.0, "turn": 2},
	]
	var pitch_cases := [
		SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD,
		SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD,
		0.0,
		deg_to_rad(-20.0),
		deg_to_rad(30.0),
	]
	for basis in [
		SliceBasis4DScript.identity(),
		SliceBasis4DScript.from_slots([-3, 2, 1, 4]),
	]:
		var mapper = TraceCoordinateMapperScript.new()
		mapper.configure(LIVE_4D_DIMENSIONS, basis)
		for yaw_case in yaw_cases:
			var yaw := deg_to_rad(float(yaw_case["degrees"]))
			var mapping = ControlFrameMappingScript.for_4d(basis, yaw)
			if mapping.yaw_quarter_turn != int(yaw_case["turn"]):
				failures.append("yaw %.0f must retain ties-to-even q=%d" % [yaw_case["degrees"], yaw_case["turn"]])
			for pitch in pitch_cases:
				var orientation = SliceLocalOrientationScript.new(yaw, pitch)
				var right_points := _mapped_displayed_points(
					mapper,
					orientation,
					mapping.translation_command("move_x_pos", "relative")
				)
				var forward_points := _mapped_displayed_points(
					mapper,
					orientation,
					mapping.translation_command("move_z_neg", "relative")
				)
				var right_origin_world: Vector3 = presentation_root.to_global(right_points[0])
				var right_destination_world: Vector3 = presentation_root.to_global(right_points[1])
				var forward_origin_world: Vector3 = presentation_root.to_global(forward_points[0])
				var forward_destination_world: Vector3 = presentation_root.to_global(forward_points[1])
				var label := "signed B %s yaw %.0f pitch %.0f" % [basis.key(), yaw_case["degrees"], rad_to_deg(pitch)]
				if rig.is_world_point_behind(right_origin_world) or rig.is_world_point_behind(right_destination_world):
					failures.append("%s Right projection points must be in front of Camera3D" % label)
				else:
					var right_origin_screen: Vector2 = rig.project_world_point(right_origin_world)
					var right_destination_screen: Vector2 = rig.project_world_point(right_destination_world)
					if right_destination_screen.x - right_origin_screen.x <= SCREEN_RIGHT_TOLERANCE_PX:
						failures.append("%s Right must increase actual Camera3D screen X" % label)
				var forward_origin_view: Vector3 = rig.camera_space_point(forward_origin_world)
				var forward_destination_view: Vector3 = rig.camera_space_point(forward_destination_world)
				var forward_distance := forward_origin_world.distance_to(forward_destination_world)
				var away_depth := (forward_origin_view.z - forward_destination_view.z) / forward_distance
				if away_depth <= AWAY_DEPTH_TOLERANCE:
					failures.append("%s Forward must remain strictly receding in actual fitted view" % label)
				var analytical_depth := CameraRigScript.live_4d_semantic_forward_away_depth(yaw, pitch)
				if absf(away_depth - analytical_depth) > ANALYTICAL_DEPTH_TOLERANCE:
					failures.append("%s production away depth %.9f must match residual-yaw helper %.9f" % [label, away_depth, analytical_depth])


func _mapped_displayed_points(mapper, orientation, command: String) -> Array:
	var delta := _canonical_delta(command)
	var destination := LIVE_4D_INTERIOR_POINT.duplicate()
	for axis in range(4):
		destination[axis] = int(destination[axis]) + int(delta[axis])
	var origin_decomposition: Dictionary = mapper.decompose_position(LIVE_4D_INTERIOR_POINT, 4)
	var destination_decomposition: Dictionary = mapper.decompose_position(destination, 4)
	var origin_local: Vector3 = orientation.passive_render_basis() * origin_decomposition.get("centered_local_point", Vector3.ZERO)
	var destination_local: Vector3 = orientation.passive_render_basis() * destination_decomposition.get("centered_local_point", Vector3.ZERO)
	return [
		origin_local + origin_decomposition.get("anchor", Vector3.ZERO),
		destination_local + destination_decomposition.get("anchor", Vector3.ZERO),
	]


func _assert_reflected_fit_enclosure(failures: Array, rig, presentation_root: Node3D, bounds: Dictionary) -> void:
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	var viewport_size: Vector2 = rig._camera.get_viewport().get_visible_rect().size
	for x in [min_pos.x, max_pos.x]:
		for y in [min_pos.y, max_pos.y]:
			for z in [min_pos.z, max_pos.z]:
				var reflected := presentation_root.to_global(Vector3(x, y, z))
				if rig.is_world_point_behind(reflected):
					failures.append("reflected fitted-bounds corner must remain in front of Camera3D")
					return
				var screen: Vector2 = rig.project_world_point(reflected)
				if screen.x < 0.0 or screen.x > viewport_size.x or screen.y < 0.0 or screen.y > viewport_size.y:
					failures.append("fixed presentation reflection must preserve projected fit enclosure")
					return


func _assert_pan_and_preset_reflection_contract(failures: Array, rig, presentation_root: Node3D) -> void:
	var probe_world := presentation_root.to_global(Vector3(3.0, 0.0, 0.0))
	var before_pan: Vector2 = rig.project_world_point(probe_world)
	rig.pan_screen(Vector2(12.0, 0.0))
	var after_pan: Vector2 = rig.project_world_point(probe_world)
	if after_pan.x - before_pan.x <= SCREEN_RIGHT_TOLERANCE_PX:
		failures.append("right-drag-right pan must continue translating the collection screen-right")
	for preset_id in [CameraPresetScript.ISO, CameraPresetScript.SIDE, CameraPresetScript.TOP]:
		if not rig.apply_framing_preset(preset_id):
			failures.append("Live-4D framing preset %s should remain accepted" % preset_id)
		elif not bool(rig.presentation_snapshot().get("horizontal_reflection_active", false)) or presentation_root.transform.basis.determinant() >= 0.0:
			failures.append("Live-4D framing preset %s must retain the fixed presentation reflection" % preset_id)


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
