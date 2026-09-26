extends RefCounted

# Pause is owned by the app's _live_*_paused flags, but the HUD badge and the
# status word are rebuilt from _current_snapshot["paused"] on every refresh.
# A pause toggle must therefore reach that copy too, or the next HUD refresh
# repaints "[ RUNNING ]" over a frozen game.


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["live pause status test requires SceneTree and replay scene"]
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
		return ["live pause status test requires ReplayHud and TraceReplayApp"]

	var mode_shapes := {
		"live_2d": [6, 6],
		"live_3d": [6, 10, 6],
		"live_4d": [5, 10, 4, 4],
	}
	for mode in mode_shapes:
		app._start_configured_live_game(_setup(mode, mode_shapes[mode]))
		await tree.process_frame
		# Toggle and assert inside one frame so a wall-clock gravity tick cannot
		# change the native hash between capture and comparison.
		var hash_before := _live_state_hash(app, mode)
		app._unhandled_input(_pause_event())
		_assert_status(failures, mode, "paused", app, hud, true)
		if _live_state_hash(app, mode) != hash_before:
			failures.append("%s pausing must not change native gameplay state" % mode)
		app._unhandled_input(_pause_event())
		_assert_status(failures, mode, "resumed", app, hud, false)

	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _assert_status(failures: Array, mode: String, phase: String, app, hud, paused: bool) -> void:
	if bool(app._current_snapshot.get("paused", not paused)) != paused:
		failures.append("%s %s: snapshot paused flag must follow the app pause state" % [mode, phase])
	var badge := str(hud._top_state_badge_label.text)
	var expected_badge := "[ PAUSED ]" if paused else "[ RUNNING ]"
	if badge != expected_badge:
		failures.append("%s %s: status badge must read %s, got %s" % [mode, phase, expected_badge, badge])
	var summary := str(hud._summary_label.text)
	if (summary.find("PAUSED") != -1) != paused:
		failures.append("%s %s: status line PAUSED word must match the pause state, got %s" % [mode, phase, summary])


func _pause_event() -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = KEY_P
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
