extends RefCounted

const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/game_bootstrap.tscn") as PackedScene
	if tree == null or scene == null:
		return ["ordinary live entry test requires the game bootstrap scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	if app == null:
		root.queue_free()
		return ["game bootstrap must contain TraceReplayApp"]

	_assert_ordinary_live_session(failures, app, TraceReplayAppScript.MODE_LIVE_2D, "game bootstrap")
	await _toggle_mode(app)
	_assert_ordinary_live_session(failures, app, TraceReplayAppScript.MODE_LIVE_3D, "Tab from Live 2D")
	await _toggle_mode(app)
	_assert_ordinary_live_session(failures, app, TraceReplayAppScript.MODE_LIVE_4D, "Tab from Live 3D")

	var menu_setup: Dictionary = app._hud.configured_live_setup(TraceReplayAppScript.MODE_LIVE_3D)
	app._hud.live_game_start_requested.emit(menu_setup)
	await tree.process_frame
	_assert_ordinary_live_session(failures, app, TraceReplayAppScript.MODE_LIVE_3D, "menu Start")

	app._enter_replay_mode()
	await tree.process_frame
	if app._mode != TraceReplayAppScript.MODE_REPLAY or app._current_document == null:
		failures.append("explicit replay entry must remain available after ordinary live entry")

	root.queue_free()
	await tree.process_frame
	return failures


func _toggle_mode(app) -> void:
	var event := InputEventAction.new()
	event.action = "mode_toggle_replay_live"
	event.pressed = true
	app._unhandled_input(event)
	await (Engine.get_main_loop() as SceneTree).process_frame


func _assert_ordinary_live_session(failures: Array, app, mode: String, entry: String) -> void:
	if app._mode != mode:
		failures.append("%s must enter %s, got %s" % [entry, mode, str(app._mode)])
		return
	if str(app._active_live_setup.get("mode", "")) != mode:
		failures.append("%s must retain the configured %s setup" % [entry, mode])
	var snapshot: Dictionary = app._current_snapshot
	if str(snapshot.get("trace_type", "")) != mode:
		failures.append("%s must expose a %s snapshot, got %s" % [entry, mode, str(snapshot.get("trace_type", ""))])
	if str(snapshot).find("TRACE_") != -1 or str(app._hud._summary_label.text).find("TRACE_") != -1:
		failures.append("%s must not expose TRACE_* fixture content to ordinary players" % entry)
