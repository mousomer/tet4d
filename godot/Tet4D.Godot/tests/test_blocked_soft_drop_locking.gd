extends RefCounted

const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/game_bootstrap.tscn") as PackedScene
	if tree == null or scene == null:
		return ["blocked soft-drop regression requires the game bootstrap scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	if app == null:
		root.queue_free()
		return ["game bootstrap must contain TraceReplayApp"]

	for mode in [TraceReplayAppScript.MODE_LIVE_2D, TraceReplayAppScript.MODE_LIVE_3D, TraceReplayAppScript.MODE_LIVE_4D]:
		await _start_ordinary_live_game(tree, app, mode)
		_assert_successful_soft_drop_repeat(failures, app, mode)
		if _ground_active_piece(failures, app, mode):
			_assert_held_soft_drop_locks(failures, app, mode)
		await _start_ordinary_live_game(tree, app, mode)
		_assert_hard_drop_remains_immediate(failures, app, mode)

	root.queue_free()
	await tree.process_frame
	return failures


func _start_ordinary_live_game(tree: SceneTree, app, mode: String) -> void:
	app._start_ordinary_live_mode(mode)
	await tree.process_frame
	# The test is exercising keyboard gameplay, not an open HUD interaction.
	app._hud._live_interaction_owns_input = false


func _assert_successful_soft_drop_repeat(failures: Array, app, mode: String) -> void:
	var action := _soft_drop_action(mode)
	var before := _snapshot(app)
	Input.action_press(action)
	app._process(0.0)
	app._process(TraceReplayAppScript.LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS + 0.001)
	var after_first := _snapshot(app)
	app._process(TraceReplayAppScript.LIVE_SOFT_DROP_REPEAT_INTERVAL_SECONDS + 0.001)
	var after_second := _snapshot(app)
	Input.action_release(action)
	if str(after_first.get("last_command_status", "")) != "accepted":
		failures.append("%s successful held soft drop must report accepted" % mode)
	if str(after_second.get("last_command_status", "")) != "accepted":
		failures.append("%s repeated held soft drop must report accepted" % mode)
	if str(after_first.get("state_hash", "")) == str(before.get("state_hash", "")):
		failures.append("%s first held soft drop must advance authoritative state" % mode)
	if str(after_second.get("state_hash", "")) == str(after_first.get("state_hash", "")):
		failures.append("%s repeated held soft drop must continue advancing authoritative state" % mode)
	var expected_accumulator := TraceReplayAppScript.LIVE_SOFT_DROP_REPEAT_INTERVAL_SECONDS + 0.001
	if not is_equal_approx(app._live_tick_accumulator, expected_accumulator):
		failures.append("%s successful soft drop must retain the existing accumulator reset cadence" % mode)


func _ground_active_piece(failures: Array, app, mode: String) -> bool:
	for step in 64:
		_dispatch_command(app, mode, "soft_drop")
		if str(_snapshot(app).get("last_command_status", "")) == "rejected":
			return true
	failures.append("%s must report a blocked grounded soft drop through the native bridge" % mode)
	return false


func _assert_held_soft_drop_locks(failures: Array, app, mode: String) -> void:
	var action := _soft_drop_action(mode)
	var before := _snapshot(app)
	var locked_before := _locked_cell_count(before)
	Input.action_press(action)
	app._process(0.0)
	var elapsed := TraceReplayAppScript.LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS + 0.001
	app._process(elapsed)
	while elapsed <= app._live_gravity_interval_seconds + TraceReplayAppScript.LIVE_SOFT_DROP_REPEAT_INTERVAL_SECONDS:
		var repeat_delta := TraceReplayAppScript.LIVE_SOFT_DROP_REPEAT_INTERVAL_SECONDS + 0.001
		app._process(repeat_delta)
		elapsed += repeat_delta
	Input.action_release(action)
	var after := _snapshot(app)
	if _locked_cell_count(after) <= locked_before:
		failures.append("%s held blocked soft drop must lock within the normal gravity interval without release" % mode)


func _assert_hard_drop_remains_immediate(failures: Array, app, mode: String) -> void:
	var before := _snapshot(app)
	var locked_before := _locked_cell_count(before)
	var expected_spawn := str(before.get("next_piece", ""))
	_dispatch_command(app, mode, "hard_drop")
	var after := _snapshot(app)
	if str(after.get("last_command_status", "")) != "accepted":
		failures.append("%s hard drop must remain accepted" % mode)
	if _locked_cell_count(after) <= locked_before:
		failures.append("%s hard drop must lock immediately" % mode)
	if expected_spawn != "" and str(after.get("current_piece", "")) != expected_spawn:
		failures.append("%s hard drop must preserve the native next-piece spawn order" % mode)


func _dispatch_command(app, mode: String, command: String) -> void:
	match mode:
		TraceReplayAppScript.MODE_LIVE_2D:
			app._live_2d_command(command)
		TraceReplayAppScript.MODE_LIVE_3D:
			app._live_3d_command(command)
		TraceReplayAppScript.MODE_LIVE_4D:
			app._live_4d_command(command)


func _soft_drop_action(mode: String) -> String:
	if mode == TraceReplayAppScript.MODE_LIVE_3D:
		return "live_3d_soft_drop"
	if mode == TraceReplayAppScript.MODE_LIVE_4D:
		return "live_4d_soft_drop"
	return "live_soft_drop"


func _snapshot(app) -> Dictionary:
	return app._current_snapshot.duplicate(true)


func _locked_cell_count(snapshot: Dictionary) -> int:
	var locked_cells = snapshot.get("locked_cells", [])
	return locked_cells.size() if locked_cells is Array else 0
