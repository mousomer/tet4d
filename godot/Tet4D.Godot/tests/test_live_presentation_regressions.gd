extends RefCounted

const AdaptiveLayerLayoutScript = preload("res://scripts/presentation/adaptive_layer_layout.gd")
const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")
const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")


func run() -> Array:
	var failures: Array = []
	_assert_structural_material_contract(failures)
	_assert_orientation_envelope_layout(failures)
	_assert_product_pitch_contract(failures)
	await _assert_screen_space_drag_and_fit(failures)
	return failures


func _assert_structural_material_contract(failures: Array) -> void:
	for role_case in [
		{"name": "locked", "materials": ReplayVisuals.live_3d_locked_face_materials(ReplayVisuals.DISPLAY_MODE_TRON, 3, 0.92), "alpha": 0.92},
		{"name": "locked alternate translucent style", "materials": ReplayVisuals.live_3d_locked_face_materials(ReplayVisuals.DISPLAY_MODE_PLAIN, 3, 0.78), "alpha": 0.78},
		{"name": "active", "materials": ReplayVisuals.live_4d_active_face_materials(ReplayVisuals.DISPLAY_MODE_PLAIN, 3, 0.70), "alpha": 0.70},
	]:
		for face_name in ["top", "front", "right", "left", "back", "bottom"]:
			var material := role_case["materials"].get(face_name) as StandardMaterial3D
			if material == null:
				failures.append("%s structural %s face material is missing" % [role_case["name"], face_name])
			elif material.transparency != BaseMaterial3D.TRANSPARENCY_ALPHA or absf(material.albedo_color.a - float(role_case["alpha"])) > 0.001:
				failures.append("%s structural %s face must retain requested translucency" % [role_case["name"], face_name])
			elif material.depth_draw_mode != BaseMaterial3D.DEPTH_DRAW_ALWAYS:
				failures.append("%s structural %s face must use the approved depth-writing path" % [role_case["name"], face_name])
	var ghost := ReplayVisuals.ghost_cell_material(ReplayVisuals.DISPLAY_MODE_TRON, 3, false)
	if ghost.depth_draw_mode == BaseMaterial3D.DEPTH_DRAW_ALWAYS:
		failures.append("Ghost must remain distinct from structural active/locked depth writing")
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://config/built_in_style_catalog.json"))
	var tron_opacity := -1.0
	var alternate_translucent_locked_style := false
	for style in catalog.get("styles", []):
		var settled_opacity := float(style.get("presentation_profile", {}).get("values", {}).get("settled_cells.opacity", 1.0))
		if str(style.get("style_id", "")) == "tron_grid_flow":
			tron_opacity = settled_opacity
		elif settled_opacity < 1.0:
			alternate_translucent_locked_style = true
	if absf(tron_opacity - 0.92) > 0.001:
		failures.append("Tron Grid Flow must retain visible 0.92 locked-cell translucency")
	if not alternate_translucent_locked_style:
		failures.append("the shipped catalog must retain a non-Tron translucent locked-cell style")


func _assert_orientation_envelope_layout(failures: Array) -> void:
	for shape_case in [
		{"extent": Vector3(5.0, 10.0, 4.0), "layers": 4, "aspect": 16.0 / 9.0},
		{"extent": Vector3(8.0, 16.0, 5.0), "layers": 8, "aspect": 4.0 / 3.0},
		{"extent": Vector3(4.0, 6.0, 10.0), "layers": 3, "aspect": 1.1},
	]:
		var local_extent: Vector3 = shape_case["extent"]
		var envelope := SliceLocalOrientationScript.normal_gameplay_extent_envelope(local_extent)
		if envelope.x < Vector2(local_extent.x, local_extent.z).length() - 0.001 or envelope.y <= local_extent.y:
			failures.append("supported orientation envelope must include yaw diagonal and pitched height for %s" % local_extent)
		var standard := AdaptiveLayerLayoutScript.new()
		standard.configure(shape_case["layers"], local_extent.x, local_extent.y, shape_case["aspect"], 1.0, local_extent.z)
		if standard.tile_width < envelope.x - 0.001 or standard.tile_height < envelope.y - 0.001:
			failures.append("4D layout tiles must reserve the complete supported local-orientation envelope for %s" % local_extent)
		var stable_snapshot: Dictionary = standard.snapshot()
		if standard.snapshot() != stable_snapshot:
			failures.append("orientation-envelope anchors must be deterministic for %s" % local_extent)
		for layer in range(1, shape_case["layers"]):
			var previous: Vector3 = standard.anchor_for_layer(layer - 1)
			var current: Vector3 = standard.anchor_for_layer(layer)
			if absf(current.y - previous.y) < 0.001 and current.x - previous.x < envelope.x + standard.horizontal_gap - 0.001:
				failures.append("same-row supported envelopes must retain their horizontal gutter for %s" % local_extent)
		for scale_case in [0.8, 1.0, 1.2]:
			var layout := AdaptiveLayerLayoutScript.new()
			layout.configure(shape_case["layers"], local_extent.x, local_extent.y, shape_case["aspect"], scale_case, local_extent.z)
			if absf(layout.horizontal_gap - standard.horizontal_gap * scale_case) > 0.001 or absf(layout.vertical_gap - standard.vertical_gap * scale_case) > 0.001:
				failures.append("slice_set.spacing %.1f must predictably multiply the governed gutter for %s" % [scale_case, local_extent])


func _assert_product_pitch_contract(failures: Array) -> void:
	if absf(rad_to_deg(SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD) + 40.0) > 0.001:
		failures.append("normal gameplay minimum pitch must retain the proven -40 degree limit")
	if absf(rad_to_deg(SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD) - 80.0) > 0.001:
		failures.append("normal gameplay maximum pitch must expand to +80 degrees")
	var safe := CameraRigScript.live_4d_all_yaw_safe_pitch_domain()
	if SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD <= safe.x or SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD >= safe.y:
		failures.append("product pitch limits must remain strictly inside the proven all-yaw interval")
	for pitch in [SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD, 0.0, deg_to_rad(60.0), SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD]:
		for yaw_degrees in range(-180, 181, 15):
			if CameraRigScript.live_4d_semantic_forward_away_depth(deg_to_rad(float(yaw_degrees)), pitch) <= 0.0:
				failures.append("semantic Forward inverted at yaw %d pitch %.0f" % [yaw_degrees, rad_to_deg(pitch)])
				return


func _assert_screen_space_drag_and_fit(failures: Array) -> void:
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	var tree := Engine.get_main_loop() as SceneTree
	if scene == null or tree == null:
		failures.append("live presentation regression test requires the production scene and SceneTree")
		return
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	if app == null:
		failures.append("production app is missing for Live-4D screen-space regression")
		root.queue_free()
		return
	app._enter_live_4d_mode()
	await tree.process_frame
	await tree.process_frame
	var basis_before: Array = app._live_4d_basis.slots()
	var native_before: String = app._live_bridge.live_4d_snapshot_json()
	var hash_before := str(app._live_bridge.live_4d_state_hash())
	app._camera_rig.set_presentation_preferences(1.0, false, 0.0)
	var right_delta := _drag_probe_delta(app, Vector2(8.0, 0.0))
	var left_delta := _drag_probe_delta(app, Vector2(-8.0, 0.0))
	var up_delta := _drag_probe_delta(app, Vector2(0.0, -8.0))
	var down_delta := _drag_probe_delta(app, Vector2(0.0, 8.0))
	if right_delta.x <= 0.5 or left_delta.x >= -0.5:
		failures.append("Live-4D right/left drag must move the canonical depth probe right/left on screen")
	if up_delta.y <= 0.5 or down_delta.y >= -0.5:
		failures.append("Live-4D up/down drag must match the Live-3D apparent vertical convention")
	app._camera_rig.set_presentation_preferences(1.0, true, 0.0)
	var inverted_right := _drag_probe_delta(app, Vector2(8.0, 0.0))
	var inverted_up := _drag_probe_delta(app, Vector2(0.0, -8.0))
	if inverted_right.x <= 0.5 or absf(inverted_right.x - right_delta.x) > 0.1:
		failures.append("invert-Y must not alter horizontal Live-4D drag")
	if inverted_up.y >= -0.5:
		failures.append("invert-Y must reverse vertical Live-4D drag only")
	app._set_live_4d_local_orientation(0.0, 0.0)
	app._fit_view()
	var first_fit: Dictionary = app._camera_rig.presentation_snapshot()
	app._fit_view()
	if app._camera_rig.presentation_snapshot() != first_fit:
		failures.append("repeated Live-4D Fit must be idempotent")
	if app._live_4d_basis.slots() != basis_before or app._live_bridge.live_4d_snapshot_json() != native_before or str(app._live_bridge.live_4d_state_hash()) != hash_before:
		failures.append("drag and Fit must not change exact B or deterministic gameplay identity")
	_assert_required_bounds_fit(failures, app)
	await _assert_fit_aspect_matrix(failures, app._renderer.current_bounds())
	root.queue_free()
	await tree.process_frame


func _drag_probe_delta(app, delta: Vector2) -> Vector2:
	app._set_live_4d_local_orientation(0.0, 0.0)
	var probe := Vector3(0.0, 0.0, 2.0)
	var before: Vector2 = app._camera_rig.project_world_point(app._renderer.to_global(probe))
	app._apply_live_4d_orientation_drag(delta)
	var oriented_probe: Vector3 = app._live_4d_local_orientation.passive_render_basis() * probe
	var after: Vector2 = app._camera_rig.project_world_point(app._renderer.to_global(oriented_probe))
	return after - before


func _assert_required_bounds_fit(failures: Array, app) -> void:
	var bounds: Dictionary = app._renderer.current_bounds()
	var viewport_size: Vector2 = app._camera_rig._camera.get_viewport().get_visible_rect().size
	var screen_min := Vector2(INF, INF)
	var screen_max := Vector2(-INF, -INF)
	for x in [bounds["min"].x, bounds["max"].x]:
		for y in [bounds["min"].y, bounds["max"].y]:
			for z in [bounds["min"].z, bounds["max"].z]:
				var point: Vector2 = app._camera_rig.project_world_point(app._renderer.get_parent().to_global(Vector3(x, y, z)))
				screen_min.x = minf(screen_min.x, point.x)
				screen_min.y = minf(screen_min.y, point.y)
				screen_max.x = maxf(screen_max.x, point.x)
				screen_max.y = maxf(screen_max.y, point.y)
	if screen_min.x < -0.5 or screen_min.y < -0.5 or screen_max.x > viewport_size.x + 0.5 or screen_max.y > viewport_size.y + 0.5:
		failures.append("Live-4D Fit must contain every required projected bounds corner")
	var limiting_share := maxf((screen_max.x - screen_min.x) / viewport_size.x, (screen_max.y - screen_min.y) / viewport_size.y)
	if limiting_share < 0.94 or limiting_share > 0.96:
		failures.append("Live-4D required bounds should occupy about 95 percent after Fit, got %.4f" % limiting_share)


func _assert_fit_aspect_matrix(failures: Array, bounds: Dictionary) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var viewport := SubViewport.new()
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	tree.root.add_child(viewport)
	var world := Node3D.new()
	viewport.add_child(world)
	var presentation := Node3D.new()
	world.add_child(presentation)
	var rig = CameraRigScript.new()
	var camera := Camera3D.new()
	camera.name = "Camera3D"
	camera.current = true
	rig.add_child(camera)
	world.add_child(rig)
	rig.set_world_presentation_root(presentation)
	for size in [Vector2i(1600, 900), Vector2i(1040, 700), Vector2i(800, 720)]:
		viewport.size = size
		await tree.process_frame
		rig.establish_outer_view(CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD, CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD, 0.0, true)
		rig.fit_current_bounds(bounds, CameraRigScript.LIVE_4D_FIT_MARGIN)
		var screen_min := Vector2(INF, INF)
		var screen_max := Vector2(-INF, -INF)
		for x in [bounds["min"].x, bounds["max"].x]:
			for y in [bounds["min"].y, bounds["max"].y]:
				for z in [bounds["min"].z, bounds["max"].z]:
					var point: Vector2 = rig.project_world_point(presentation.to_global(Vector3(x, y, z)))
					screen_min.x = minf(screen_min.x, point.x)
					screen_min.y = minf(screen_min.y, point.y)
					screen_max.x = maxf(screen_max.x, point.x)
					screen_max.y = maxf(screen_max.y, point.y)
		if screen_min.x < 1.0 or screen_min.y < 1.0 or screen_max.x > size.x - 1.0 or screen_max.y > size.y - 1.0:
			failures.append("Live-4D Fit must retain safety clearance at viewport %s" % size)
		var limiting_share := maxf((screen_max.x - screen_min.x) / size.x, (screen_max.y - screen_min.y) / size.y)
		if limiting_share < 0.94 or limiting_share > 0.96:
			failures.append("Live-4D Fit must retain stable utilization at viewport %s, got %.4f" % [size, limiting_share])
	viewport.queue_free()
	await tree.process_frame
