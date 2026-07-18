extends RefCounted


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

	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _setup(mode: String, shape: Array) -> Dictionary:
	var piece_set := "classic" if mode == "live_2d" else ("native_3d" if mode == "live_3d" else "standard_4d_5")
	return {
		"schema_version": 2,
		"mode": mode,
		"board_preset_id": "standard",
		"board_shape": shape,
		"piece_set_id": piece_set,
		"random_mode": "fixed_seed",
		"seed": 1337,
		"initial_speed_level": 1,
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
