extends RefCounted

const DirectionProbe = preload("res://tests/support/legend_direction_probe.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size if DisplayServer.get_name() == "headless" else DisplayServer.window_get_size()
	_resize_window(tree, Vector2i(1600, 960))
	var root := (load("res://scenes/game_bootstrap.tscn") as PackedScene).instantiate()
	tree.root.add_child(root)
	await _layout_frames(tree)
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	for mode in ["live_3d", "live_4d"]:
		hud._game_setup_model.set_mode(mode)
		hud._game_setup_model.reset_to_standard(mode)
		app._return_to_main_menu()
		await _layout_frames(tree)
		if hud.board_viewport_size() != Vector2.ZERO:
			failures.append("Hidden %s Main Menu render region must not supply fit geometry (screen=%s, size=%s)" % [mode, hud.current_screen(), hud.board_viewport_size()])
		var play := hud.find_child("CommandCard__Play", true, false) as Button
		play.pressed.emit()
		app._live_3d_paused = true
		app._live_4d_paused = true
		if DisplayServer.get_name() != "headless":
			# Observe the first actual draw as well as eventual settled geometry.
			await RenderingServer.frame_post_draw
			_check_fit(failures, app, hud, "%s first visible draw" % mode)
		await _layout_frames(tree)
		_check_fit(failures, app, hud, "%s Main Menu Play" % mode)
		var hash_before := _state_hash(app, mode)
		# Guide allocation can change the render region after entry.
		for visible in [false, true, false]:
			hud._set_onboarding_visible(visible)
			await _layout_frames(tree)
			_check_fit(failures, app, hud, "%s guide %s" % [mode, visible])
		for density in ["compact", "detailed", "standard"]:
			# Capture BEFORE each transition, never after applying density.
			var density_before := _state_hash(app, mode)
			hud._apply_hud_density(density)
			await _layout_frames(tree)
			if _state_hash(app, mode) != density_before:
				failures.append("%s density %s mutated gameplay" % [mode, density])
			_check_fit(failures, app, hud, "%s density %s" % [mode, density])
		for window_size in [Vector2i(1000, 720), Vector2i(1600, 960)]:
			_resize_window(tree, window_size)
			await _layout_frames(tree)
			_check_fit(failures, app, hud, "%s resize %s" % [mode, window_size])
		# Change the INNER render area without resizing the outer GameArea:
		# this was invisible to the old outer-panel resized connection.
		var outer_size: Vector2 = hud._game_area.size
		var region_before: Vector2 = hud.board_viewport_size()
		hud._game_viewport_container.custom_minimum_size.y = 0.0
		hud._viewport_hint.text = "Render-region lifecycle regression"
		hud._viewport_hint.visible = true
		await _layout_frames(tree)
		if hud._game_area.size != outer_size or hud.board_viewport_size() == region_before:
			failures.append("%s inner-region regression must change inner geometry only" % mode)
		_check_fit(failures, app, hud, "%s inner-only resize" % mode)
		hud._viewport_hint.visible = false
		await _layout_frames(tree)
		_check_fit(failures, app, hud, "%s inner-only restore" % mode)
		if _state_hash(app, mode) != hash_before:
			failures.append("%s layout/refit lifecycle mutated native state" % mode)
		# Restart reuses the running mode/view and still fits the actual region.
		hud._restart_game_button.pressed.emit()
		app._live_3d_paused = true
		app._live_4d_paused = true
		await _layout_frames(tree)
		_check_fit(failures, app, hud, "%s Restart" % mode)
		var fingerprint: Dictionary = app._design_laboratory_fingerprint()
		app._camera_rig.pan_focus(Vector3(0.25, 0.5, 0.0))
		if app._design_laboratory_fingerprint()["camera_pose"]["target_focus"] == fingerprint["camera_pose"]["target_focus"]:
			failures.append("%s comparison fingerprint must still detect authored pan" % mode)
		app._fit_view()
		if app._design_laboratory_fingerprint()["camera_pose"]["target_focus"] != fingerprint["camera_pose"]["target_focus"]:
			failures.append("%s refit must restore the comparison's unpanned pose" % mode)
	root.queue_free()
	await tree.process_frame
	if DisplayServer.get_name() == "headless":
		tree.root.size = original_size
	else:
		DisplayServer.window_set_size(original_size)
	return failures


func _resize_window(tree: SceneTree, points: Vector2i) -> void:
	if DisplayServer.get_name() == "headless":
		tree.root.size = points
	else:
		# Real-window acceptance must exercise the OS backing-pixel size and
		# shipped canvas stretch, rather than changing the logical root alone.
		var display_scale := maxf(DisplayServer.screen_get_scale(), 0.01)
		DisplayServer.window_set_size(Vector2i(Vector2(points) * display_scale))


func _layout_frames(tree: SceneTree) -> void:
	# Test observation budget only: production fitting is driven by actual
	# region validity/signals, with no frame-count correctness assumption.
	for frame in range(10):
		await tree.process_frame


func _state_hash(app, mode: String) -> String:
	return str(app._live_bridge.live_3d_state_hash() if mode == "live_3d" else app._live_bridge.live_4d_state_hash())


func _check_fit(failures: Array, app, hud, label: String) -> void:
	var region := Vector2(hud.game_viewport().size)
	if not hud._game_viewport_container.is_visible_in_tree() or region.x < 240.0 or region.y < 120.0:
		failures.append("%s requires visible resolved inner geometry" % label)
		return
	if region != hud.board_viewport_size():
		failures.append("%s layout must consume actual inner render geometry" % label)
	if not app._last_layout_viewport_size.is_equal_approx(region) or app._pending_fit_view:
		failures.append("%s must complete fitting/layout from the current inner render region" % label)
	var camera: Camera3D = app._camera_rig._camera
	var size_before := camera.size
	var height_before := DirectionProbe.projected_content_height(app)
	if height_before < region.y * 0.40:
		failures.append("%s must not enter with half-size initial framing" % label)
	for box in app._renderer.current_content_boxes():
		var low: Vector3 = box["min"]
		var high: Vector3 = box["max"]
		for x in [low.x, high.x]:
			for y in [low.y, high.y]:
				for z in [low.z, high.z]:
					var point: Vector2 = camera.unproject_position(Vector3(x, y, z))
					if point.x < -1.0 or point.y < -1.0 or point.x > region.x + 1.0 or point.y > region.y + 1.0:
						failures.append("%s clips content at %s in %s" % [label, point, region])

	# A subsequent explicit Fit must not repair stale automatic framing.
	app._fit_view()
	if not is_equal_approx(size_before, camera.size):
		failures.append("%s automatic fit is stale: %s -> %s" % [label, size_before, camera.size])
