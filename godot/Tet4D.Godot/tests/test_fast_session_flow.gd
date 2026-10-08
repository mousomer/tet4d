extends RefCounted

const ReplayHudScript = preload("res://scripts/ui/replay_hud.gd")
const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/game_bootstrap.tscn") as PackedScene
	if tree == null or scene == null:
		return ["fast-session-flow test requires the game bootstrap scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	if app == null:
		root.queue_free()
		return ["game bootstrap must contain TraceReplayApp"]

	await _assert_main_menu_play_and_setup(failures, app)
	await _assert_menu_shortcuts(failures, app)
	await _assert_restart_preserves_setup(failures, app, TraceReplayAppScript.MODE_LIVE_2D, [10, 20])
	await _assert_restart_preserves_setup(failures, app, TraceReplayAppScript.MODE_LIVE_3D, [4, 8, 4])
	await _assert_restart_preserves_setup(failures, app, TraceReplayAppScript.MODE_LIVE_4D, [4, 8, 3, 3])
	await _assert_game_over_play_again(failures, app)

	root.queue_free()
	await tree.process_frame
	return failures


func _assert_main_menu_play_and_setup(failures: Array, app) -> void:
	app._hud._game_setup_model.set_mode(GameSetupSpecScript.MODE_2D)
	app._hud._game_setup_model.reset_to_standard(GameSetupSpecScript.MODE_2D)
	app._return_to_main_menu()
	await (Engine.get_main_loop() as SceneTree).process_frame
	var starts := [0]
	app._hud.live_game_start_requested.connect(func(_setup: Dictionary) -> void: starts[0] += 1)
	var play_button := app._hud.find_child("CommandCard__Play", true, false) as Button
	if play_button == null:
		failures.append("Main Menu must expose a primary Play action")
		return
	play_button.pressed.emit()
	await (Engine.get_main_loop() as SceneTree).process_frame
	if starts[0] != 1 or app._mode != TraceReplayAppScript.MODE_LIVE_2D:
		failures.append("Main Menu Play must start the default/current setup in one action")
	if _snapshot_shape(app) != [10, 20]:
		failures.append("Main Menu Play must restore the canonical 2D 10x20 board")
	if app._hud.current_screen() != ReplayHudScript.SCREEN_VIEWER:
		failures.append("Main Menu Play must enter the running live viewer directly")

	app._return_to_main_menu()
	await (Engine.get_main_loop() as SceneTree).process_frame
	var change_setup := app._hud.find_child("CommandCard__Change_Setup", true, false) as Button
	if change_setup == null:
		failures.append("Main Menu must retain an explicit Change Setup action")
		return
	var starts_before_setup: int = starts[0]
	change_setup.pressed.emit()
	await (Engine.get_main_loop() as SceneTree).process_frame
	if app._hud.current_screen() != ReplayHudScript.SCREEN_GAME_SETUP:
		failures.append("Change Setup must open configuration UI")
	if starts[0] != starts_before_setup:
		failures.append("Change Setup must not start a game")


func _assert_menu_shortcuts(failures: Array, app) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var model = app._hud._game_setup_model
	var starts := [0]
	app._hud.live_game_start_requested.connect(func(_setup: Dictionary) -> void: starts[0] += 1)
	var cases := [
		{"key": KEY_2, "mode": GameSetupSpecScript.MODE_2D, "shape": [10, 20]},
		{"key": KEY_3, "mode": GameSetupSpecScript.MODE_3D, "shape": [4, 8, 4]},
		{"key": KEY_4, "mode": GameSetupSpecScript.MODE_4D, "shape": [4, 8, 3, 3]},
	]
	for case in cases:
		var mode: String = case["mode"]
		model.set_mode(mode)
		model.reset_to_standard(mode)
		for axis in case["shape"].size():
			model.set_axis_text(axis, str(case["shape"][axis]))
		var expected: Dictionary = app._hud.configured_live_setup(mode)
		if expected.is_empty():
			failures.append("%s shortcut fixture must be a valid setup" % mode)
			continue
		# Start from another menu mode to prove the digit selects its target.
		model.set_mode(GameSetupSpecScript.MODE_4D if mode == GameSetupSpecScript.MODE_2D else GameSetupSpecScript.MODE_2D)
		app._return_to_main_menu()
		await tree.process_frame
		var before: int = starts[0]
		app._input(_menu_key(case["key"]))
		await tree.process_frame
		if starts[0] != before + 1 or app._mode != mode or app._hud.current_screen() != ReplayHudScript.SCREEN_VIEWER:
			failures.append("%s digit shortcut must launch exactly once directly into its live viewer" % mode)
		_assert_frozen_setup(failures, app, expected, "%s digit shortcut" % mode)

		app._return_to_main_menu()
		await tree.process_frame
		before = starts[0]
		app._input(_menu_key(KEY_C))
		await tree.process_frame
		if starts[0] != before or app._hud.current_screen() != ReplayHudScript.SCREEN_GAME_SETUP or model.current_mode != mode:
			failures.append("%s C shortcut must open current-mode Setup without a session launch" % mode)
		var frozen: Dictionary = app._active_live_setup.duplicate(true)
		model.set_axis_text(0, "invalid")
		if model.is_valid(mode):
			failures.append("%s malformed draft must be invalid" % mode)
		app._return_to_main_menu()
		await tree.process_frame
		app._input(_menu_key(case["key"]))
		await tree.process_frame
		if starts[0] != before or app._hud.current_screen() != ReplayHudScript.SCREEN_MAIN_MENU:
			failures.append("%s digit shortcut must reject an invalid draft" % mode)
		if app._hud.start_current_validated_setup(mode):
			failures.append("%s button launch boundary must reject an invalid draft" % mode)
		_assert_frozen_setup(failures, app, frozen, "%s invalid draft" % mode)
		model.reset_to_standard(mode)

	app._return_to_main_menu()
	await tree.process_frame
	for key in [KEY_2, KEY_3, KEY_4, KEY_C]:
		for filter in ["release", "echo", "alt", "ctrl", "meta"]:
			var event := _menu_key(key)
			event.pressed = filter != "release"
			event.echo = filter == "echo"
			event.alt_pressed = filter == "alt"
			event.ctrl_pressed = filter == "ctrl"
			event.meta_pressed = filter == "meta"
			var before: int = starts[0]
			app._input(event)
			if starts[0] != before or app._hud.current_screen() != ReplayHudScript.SCREEN_MAIN_MENU:
				failures.append("menu shortcut %s must ignore %s events" % [str(key), filter])
	app._hud.open_game_setup(model.current_mode)
	var before: int = starts[0]
	app._input(_menu_key(KEY_3))
	if starts[0] != before or app._hud.current_screen() != ReplayHudScript.SCREEN_GAME_SETUP:
		failures.append("Main Menu digit shortcuts must not launch from Setup")


func _menu_key(key: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = key
	event.physical_keycode = key
	event.pressed = true
	return event


func _assert_restart_preserves_setup(failures: Array, app, mode: String, shape: Array) -> void:
	var setup: Dictionary = app._hud.configured_live_setup(mode)
	setup["board_shape"] = shape.duplicate()
	setup["board_preset_id"] = GameSetupSpecScript.preset_id_for_shape(mode, shape)
	setup["topology_profile"] = GameSetupSpecScript.bounded_topology_profile(shape)
	app._start_configured_live_game(setup)
	await (Engine.get_main_loop() as SceneTree).process_frame
	var frozen_setup: Dictionary = app._active_live_setup.duplicate(true)
	var start_count := [0]
	app._hud.live_game_start_requested.connect(func(_ignored: Dictionary) -> void: start_count[0] += 1)
	var restart_button := app._hud._restart_game_button as Button
	if restart_button == null:
		failures.append("%s must expose Restart Game" % mode)
		return
	restart_button.pressed.emit()
	await (Engine.get_main_loop() as SceneTree).process_frame
	if start_count[0] != 0:
		failures.append("%s Restart Game must not route through the setup-launch signal" % mode)
	if app._hud.current_screen() != ReplayHudScript.SCREEN_VIEWER:
		failures.append("%s Restart Game must not route through Setup or Main Menu" % mode)
	_assert_frozen_setup(failures, app, frozen_setup, "%s Restart Game" % mode)
	if bool(app._current_snapshot.get("game_over", true)):
		failures.append("%s Restart Game must return to a fresh running game" % mode)


func _assert_game_over_play_again(failures: Array, app) -> void:
	var setup: Dictionary = app._hud.configured_live_setup(TraceReplayAppScript.MODE_LIVE_2D)
	app._start_configured_live_game(setup)
	await (Engine.get_main_loop() as SceneTree).process_frame
	var frozen_setup: Dictionary = app._active_live_setup.duplicate(true)
	# This test controls only the terminal presentation branch; native reset remains
	# the same existing live-session boundary exercised by the button below.
	app._current_snapshot["game_over"] = true
	app._current_snapshot["game_over_reason"] = "spawn_blocked"
	app._refresh_hud()
	var play_again := app._hud._restart_game_button as Button
	if play_again == null or play_again.text != "Play Again":
		failures.append("GAME OVER must expose a prominent Play Again action")
		return
	var start_count := [0]
	app._hud.live_game_start_requested.connect(func(_ignored: Dictionary) -> void: start_count[0] += 1)
	play_again.pressed.emit()
	await (Engine.get_main_loop() as SceneTree).process_frame
	if start_count[0] != 0 or app._hud.current_screen() != ReplayHudScript.SCREEN_VIEWER:
		failures.append("Play Again must restart directly without Setup or Main Menu signals")
	_assert_frozen_setup(failures, app, frozen_setup, "Play Again")
	if bool(app._current_snapshot.get("game_over", true)):
		failures.append("Play Again must return to a fresh running game")


func _assert_frozen_setup(failures: Array, app, expected: Dictionary, context: String) -> void:
	var actual: Dictionary = app._active_live_setup
	for field in ["mode", "board_shape", "piece_set_id", "random_mode", "seed", "initial_speed_level", "topology_profile"]:
		if actual.get(field) != expected.get(field):
			failures.append("%s must preserve setup field %s" % [context, field])
	if _snapshot_shape(app) != expected.get("board_shape", []):
		failures.append("%s must restore the configured board shape" % context)


func _snapshot_shape(app) -> Array:
	var shape: Array = []
	for extent in (app._current_snapshot.get("board_shape", []) as Array):
		shape.append(int(extent))
	return shape
