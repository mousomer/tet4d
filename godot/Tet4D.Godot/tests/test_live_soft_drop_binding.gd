extends RefCounted

const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["soft-drop binding test requires SceneTree and replay scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	if app == null:
		root.queue_free()
		return ["soft-drop binding test requires TraceReplayApp"]
	for mode in [TraceReplayAppScript.MODE_LIVE_3D, TraceReplayAppScript.MODE_LIVE_4D]:
		for location in [KEY_LOCATION_LEFT, KEY_LOCATION_RIGHT]:
			await _assert_soft_drop_event(failures, tree, app, mode, _shift_event(location), "physical %s Shift" % ["left" if location == KEY_LOCATION_LEFT else "right"])
		await _assert_soft_drop_event(failures, tree, app, mode, _ctrl_event(), "Ctrl compatibility")
	root.queue_free()
	await tree.process_frame
	return failures


func _assert_soft_drop_event(failures: Array, tree: SceneTree, app, mode: String, event: InputEventKey, label: String) -> void:
	app._start_ordinary_live_mode(mode)
	await tree.process_frame
	app._hud._set_onboarding_visible(false)
	app._hud._live_interaction_owns_input = false
	var before := str(app._current_snapshot.get("state_hash", ""))
	app._unhandled_input(event)
	var after := str(app._current_snapshot.get("state_hash", ""))
	if str(app._current_snapshot.get("last_command", "")) != "soft_drop" or str(app._current_snapshot.get("last_command_status", "")) != "accepted":
		failures.append("%s %s must dispatch exactly one accepted soft drop" % [mode, label])
	if after == before:
		failures.append("%s %s must mutate the native state through soft drop" % [mode, label])


func _shift_event(location: KeyLocation) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = KEY_SHIFT
	event.physical_keycode = KEY_SHIFT
	event.location = location
	event.pressed = true
	return event


func _ctrl_event() -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = KEY_CTRL
	event.pressed = true
	return event
