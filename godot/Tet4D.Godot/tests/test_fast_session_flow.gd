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
