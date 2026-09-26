extends RefCounted

# Focus loss is dispatched through the same Node notification path Godot uses
# for the interactive window. The app handler owns pause flags; no native game
# state is changed merely because the application loses focus.


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["live focus-loss test requires SceneTree and replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	var hud = root.get_node_or_null("ReplayHud")
	if app == null or hud == null:
		root.queue_free()
		return ["live focus-loss test requires ReplayHud and TraceReplayApp"]

	for mode in ["live_2d", "live_3d", "live_4d"]:
		await _start_live_game(tree, app, mode)
		_assert_running_focus_loss(failures, app, hud, mode)
		await _start_live_game(tree, app, mode)
		_assert_manual_pause_survives_focus(failures, app, mode)

	await _start_live_game(tree, app, "live_3d")
	_assert_held_input_is_cleared(failures, app)
	_assert_game_over_is_not_reclassified(failures, app)
	_assert_non_live_surfaces_are_unchanged(failures, app, hud)

	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _start_live_game(tree: SceneTree, app, mode: String) -> void:
	app._start_configured_live_game(_setup(mode))
	await tree.process_frame
	app._hud._live_interaction_owns_input = false


func _assert_running_focus_loss(failures: Array, app, hud, mode: String) -> void:
	var hash_before := _state_hash(app, mode)
	var accumulator_before: float = app._live_tick_accumulator
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	if not app._live_mode_paused():
		failures.append("%s focus loss must ensure the authoritative pause flag is set" % mode)
	if _state_hash(app, mode) != hash_before:
		failures.append("%s focus loss must not mutate native gameplay state" % mode)
	if str(hud._top_state_badge_label.text) != "[ PAUSED ]":
		failures.append("%s focus loss must refresh the HUD to PAUSED" % mode)
	app._process(app._live_gravity_interval_seconds * 2.0)
	if _state_hash(app, mode) != hash_before:
		failures.append("%s must not advance gravity while focus-paused" % mode)
	if not is_equal_approx(app._live_tick_accumulator, accumulator_before):
		failures.append("%s must preserve its gravity accumulator while focus-paused" % mode)
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_IN)
	app._process(app._live_gravity_interval_seconds * 2.0)
	if not app._live_mode_paused() or _state_hash(app, mode) != hash_before:
		failures.append("%s focus regain must not auto-resume or advance gameplay" % mode)
	app._unhandled_input(_pause_event())
	if app._live_mode_paused():
		failures.append("%s one explicit pause action must resume after focus loss" % mode)
	app._process(app._live_gravity_interval_seconds + 0.001)
	if _state_hash(app, mode) == hash_before:
		failures.append("%s gravity must resume after explicit player resume" % mode)


func _assert_manual_pause_survives_focus(failures: Array, app, mode: String) -> void:
	app._unhandled_input(_pause_event())
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_IN)
	if not app._live_mode_paused():
		failures.append("%s manually paused game must remain paused across focus changes" % mode)
	app._unhandled_input(_pause_event())
	if app._live_mode_paused():
		failures.append("%s manually paused game must require exactly one resume action" % mode)


func _assert_held_input_is_cleared(failures: Array, app) -> void:
	var action := "live_3d_move_x_pos"
	Input.action_press(action)
	app._process(0.0)
	app._process(app.LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS + 0.001)
	var hash_after_first_repeat := _state_hash(app, "live_3d")
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	Input.action_release(action)
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_IN)
	app._unhandled_input(_pause_event())
	app._process(app.LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS + 0.001)
	if _state_hash(app, "live_3d") != hash_after_first_repeat:
		failures.append("held movement released while unfocused must not repeat after resume")


func _assert_game_over_is_not_reclassified(failures: Array, app) -> void:
	app._live_3d_paused = false
	app._current_snapshot["game_over"] = true
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	if app._live_3d_paused:
		failures.append("focus loss must not convert GAME OVER into PAUSED")


func _assert_non_live_surfaces_are_unchanged(failures: Array, app, hud) -> void:
	app._enter_replay_mode()
	app._state.is_playing = true
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	if not app._state.is_playing:
		failures.append("focus loss must not change replay playback state")
	app._start_ordinary_live_mode("live_2d")
	app._return_to_main_menu()
	var screen_before: String = str(hud.current_screen())
	app.notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	if hud.current_screen() != screen_before:
		failures.append("focus loss must not change the main-menu surface")


func _pause_event() -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = KEY_P
	event.pressed = true
	return event


func _state_hash(app, mode: String) -> String:
	match mode:
		"live_2d":
			return str(app._live_bridge.live_2d_state_hash())
		"live_3d":
			return str(app._live_bridge.live_3d_state_hash())
		_:
			return str(app._live_bridge.live_4d_state_hash())


func _setup(mode: String) -> Dictionary:
	var shape := [6, 6] if mode == "live_2d" else ([6, 10, 6] if mode == "live_3d" else [5, 10, 4, 4])
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
