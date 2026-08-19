extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["live menu routing test requires SceneTree and replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	var app = root.get_node_or_null("App")
	if hud == null or app == null:
		root.queue_free()
		return ["live menu routing test requires ReplayHud and TraceReplayApp"]

	var mode_shapes := {
		"live_2d": [6, 6],
		"live_3d": [6, 10, 6],
		"live_4d": [5, 10, 4, 4],
	}
	for mode in mode_shapes:
		app._start_configured_live_game(_setup(mode, mode_shapes[mode]))
		await tree.process_frame
		app._return_to_main_menu()
		await tree.process_frame
		await tree.process_frame
		if hud.game_viewport_global_rect().has_area():
			failures.append("%s Main Menu transition should disable the hidden game viewport hit target" % mode)
		var play_button := _find_visible_button(hud, "CommandCard__Play_2D")
		if play_button == null:
			failures.append("%s Main Menu transition should expose Play 2D" % mode)
		else:
			await _click(tree, play_button)
			if hud.current_screen() != hud.SCREEN_GAME_SETUP:
				failures.append("%s Main Menu transition should leave Play 2D mouse-clickable" % mode)

		app._change_live_setup(mode)
		await tree.process_frame
		await tree.process_frame
		if hud.game_viewport_global_rect().has_area():
			failures.append("%s Change Setup should disable the hidden game viewport hit target" % mode)
		var start_button := _find_visible_button(hud, "StartGameButton")
		if start_button == null:
			failures.append("%s Change Setup should expose Start Game" % mode)
		else:
			start_button.grab_focus()
			_send_key(KEY_ENTER)
			await tree.process_frame
			await tree.process_frame
			if hud.current_screen() != hud.SCREEN_VIEWER:
				failures.append("%s Change Setup should activate Start Game with Enter" % mode)

		app._return_to_main_menu()
		await tree.process_frame
		var focused := tree.root.gui_get_focus_owner()
		if focused == null or focused.name != "CommandCard__Play_2D":
			failures.append("%s Main Menu transition should restore deterministic menu focus" % mode)
		else:
			_send_key(KEY_ENTER)
			await tree.process_frame
			if hud.current_screen() != hud.SCREEN_GAME_SETUP:
				failures.append("%s Main Menu transition should activate the focused card with Enter" % mode)

		app._return_to_main_menu()
		await tree.process_frame
		focused = tree.root.gui_get_focus_owner()
		if focused == null or focused.name != "CommandCard__Play_2D":
			failures.append("%s Main Menu transition should retain focus for Space activation" % mode)
		else:
			_send_key(KEY_SPACE)
			await tree.process_frame
			if hud.current_screen() != hud.SCREEN_GAME_SETUP:
				failures.append("%s Main Menu transition should activate the focused card with Space" % mode)

	var random_setup := _setup("live_2d", mode_shapes["live_2d"])
	random_setup["random_mode"] = "true_random"
	app._start_configured_live_game(random_setup)
	await tree.process_frame
	app._camera_rig.nudge_yaw(0.37)
	app._camera_rig.zoom(-1.0)
	var view_before_new_random: Dictionary = app._camera_rig.presentation_snapshot()
	var seed_before_new_random := int(app._current_snapshot.get("effective_seed", -1))
	app._start_new_random_game()
	await tree.process_frame
	if app._camera_rig.presentation_snapshot() != view_before_new_random:
		failures.append("same-context New Random Game must preserve the current view")
	if int(app._current_snapshot.get("effective_seed", -1)) == seed_before_new_random:
		failures.append("New Random Game should still reconstruct gameplay with a new effective seed")

	await _assert_reset_view_is_reachable_by_input(tree, app, mode_shapes, failures)

	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


# Reset View has to be reachable by the player in every live mode, not just
# Live 4D. The key event is pushed through the app's real input routing so the
# action contract, the per-mode handler, and the composite Reset View
# orchestration are all exercised rather than the reset helper being called
# directly.
func _assert_reset_view_is_reachable_by_input(
	tree: SceneTree,
	app,
	mode_shapes: Dictionary,
	failures: Array
) -> void:
	var canonical_orientation := {
		"live_2d": [0.0, 0.0, false],
		"live_3d": [CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD, CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD, false],
		"live_4d": [CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD, CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD, true],
	}
	for mode in ["live_2d", "live_3d", "live_4d"]:
		app._start_configured_live_game(_setup(mode, mode_shapes[mode]))
		await tree.process_frame
		await tree.process_frame
		var expected: Array = canonical_orientation[mode]
		var hash_before := _live_state_hash(app, mode)
		app._camera_rig.nudge_yaw(0.41)
		app._camera_rig.nudge_pitch(0.23)
		app._camera_rig.zoom(-1.0)
		if mode == "live_4d":
			app._set_live_4d_local_orientation(0.62, 0.31)
			app._apply_live_4d_basis_turn("xw", 1)
			await tree.process_frame
		if is_equal_approx(app._camera_rig._current_yaw, float(expected[0])):
			failures.append("%s Reset View routing test should start from an off-canonical view" % mode)

		app._unhandled_input(_reset_view_event())
		await tree.process_frame
		await tree.process_frame

		if not is_equal_approx(app._camera_rig._current_yaw, float(expected[0])) \
			or not is_equal_approx(app._camera_rig._current_pitch, float(expected[1])) \
			or not is_equal_approx(app._camera_rig._current_roll, 0.0):
			failures.append("%s must restore its canonical orientation from the player-facing Reset View input" % mode)
		var snapshot: Dictionary = app._camera_rig.presentation_snapshot()
		if bool(snapshot.get("horizontal_reflection_active", false)) != bool(expected[2]):
			failures.append("%s Reset View input must restore canonical reflection state" % mode)
		if int(snapshot.get("projection", -1)) != Camera3D.PROJECTION_ORTHOGONAL:
			failures.append("%s Reset View input must restore orthographic projection" % mode)
		if not is_equal_approx(float(snapshot.get("zoom_multiplier", 0.0)), 1.0):
			failures.append("%s Reset View input must restore canonical framing" % mode)
		if _live_state_hash(app, mode) != hash_before:
			failures.append("%s Reset View input must not restart gameplay" % mode)
		if mode == "live_4d":
			if not app._live_4d_basis.is_identity():
				failures.append("live_4d Reset View input must restore the identity presentation basis")
			var local: Dictionary = app._live_4d_local_orientation.snapshot()
			if not is_equal_approx(float(local.get("local_yaw", 1.0)), 0.0) or not is_equal_approx(float(local.get("local_pitch", 1.0)), 0.0):
				failures.append("live_4d Reset View input must restore default slice-local orientation")


func _reset_view_event() -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = int(LiveInputContractScript.ACTION_SPECS["reset"]["display_key"]) as Key
	event.pressed = true
	return event


func _live_state_hash(app, mode: String) -> String:
	match mode:
		"live_2d":
			return str(app._live_bridge.live_2d_state_hash())
		"live_3d":
			return str(app._live_bridge.live_3d_state_hash())
		_:
			return str(app._live_bridge.live_4d_state_hash())


func _setup(mode: String, shape: Array) -> Dictionary:
	var piece_set := "classic" if mode == "live_2d" else ("native_3d" if mode == "live_3d" else "standard_4d_5")
	return {
		"schema_version": 2,
		"contract_version": 1,
		"mode": mode,
		"board_preset_id": "standard",
		"board_shape": shape,
		"piece_set_id": piece_set,
		"random_mode": "fixed_seed",
		"seed": 1337,
		"initial_speed_level": 1,
		"topology_profile": {"contract_version": 1, "rank": shape.size(), "dimensions": shape.duplicate(), "seams": []},
	}


func _find_visible_button(root: Node, node_name: String) -> Button:
	for child in root.find_children(node_name, "Button", true, false):
		var button := child as Button
		if button != null and button.is_visible_in_tree():
			return button
	return null


func _click(tree: SceneTree, control: Control) -> void:
	var point := control.get_global_rect().get_center()
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.global_position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		tree.root.push_input(event)
		await tree.process_frame


func _send_key(keycode: Key) -> void:
	var pressed := InputEventKey.new()
	pressed.keycode = keycode
	pressed.pressed = true
	Input.parse_input_event(pressed)
	var released := InputEventKey.new()
	released.keycode = keycode
	released.pressed = false
	Input.parse_input_event(released)
