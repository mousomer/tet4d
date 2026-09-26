extends RefCounted

func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["onboarding suspension requires replay scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	var hud = root.get_node_or_null("ReplayHud")
	for mode in ["live_2d", "live_4d"]:
		app._start_configured_live_game(_setup(mode))
		await tree.process_frame
		hud._set_onboarding_visible(true)
		var before := str(app._current_snapshot.get("state_hash", ""))
		app._process(45.0)
		if str(app._current_snapshot.get("state_hash", "")) != before:
			failures.append("%s onboarding must suspend unattended gravity, lock, spawn, and game-over progression" % mode)
		hud._set_onboarding_visible(false)
		app._process(app._live_gravity_interval_seconds + 0.001)
		if str(app._current_snapshot.get("state_hash", "")) == before:
			failures.append("%s dismissal must restore running gameplay" % mode)
	app._start_configured_live_game(_setup("live_2d"))
	await tree.process_frame
	app._unhandled_input(_pause_event())
	hud._set_onboarding_visible(true)
	hud._set_onboarding_visible(false)
	if not app._live_mode_paused():
		failures.append("manual pause must survive onboarding visibility changes")
	app._unhandled_input(_pause_event())
	if app._live_mode_paused():
		failures.append("one ordinary resume must resume after onboarding dismissal")
	app._start_configured_live_game(_setup("live_2d"))
	await tree.process_frame
	hud._set_onboarding_visible(true)
	var step_before := str(hud.onboarding_snapshot().get("step_id", ""))
	app._live_2d_command("move_left")
	if step_before == str(hud.onboarding_snapshot().get("step_id", "")):
		failures.append("accepted tutorial command must still advance 2D onboarding")
	app._start_configured_live_game(_setup("live_4d"))
	await tree.process_frame
	hud._set_onboarding_visible(true)
	var hash_before_view := str(app._current_snapshot.get("state_hash", ""))
	var view_step_before := str(hud.onboarding_snapshot().get("step_id", ""))
	app._apply_live_4d_basis_turn("xw", 1)
	if str(app._current_snapshot.get("state_hash", "")) != hash_before_view:
		failures.append("4D onboarding view instruction must not mutate native gameplay")
	if view_step_before == str(hud.onboarding_snapshot().get("step_id", "")):
		failures.append("4D presentation-only instruction must advance onboarding")
	app._start_configured_live_game(_setup("live_2d"))
	await tree.process_frame
	hud._set_onboarding_visible(false)
	Input.action_press("live_move_right")
	app._process(0.0)
	app._process(app.LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS + 0.001)
	hud._set_onboarding_visible(true)
	app._process(app.LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS + 0.001)
	hud._set_onboarding_visible(false)
	var repeat_before := str(app._current_snapshot.get("state_hash", ""))
	app._process(0.0)
	app._process(0.1)
	if str(app._current_snapshot.get("state_hash", "")) != repeat_before:
		failures.append("onboarding suspension must reset an already-active held repeat")
	app._process(0.13)
	if str(app._current_snapshot.get("state_hash", "")) == repeat_before:
		failures.append("held movement must re-arm and repeat after the normal initial delay")
	Input.action_release("live_move_right")
	app._start_configured_live_game(_setup("live_2d"))
	hud._set_onboarding_visible(true)
	await tree.process_frame
	hud._set_onboarding_visible(false)
	var gravity_interval: float = app._live_gravity_interval_seconds
	app._process(gravity_interval * 0.60)
	var phase_hash := str(app._current_snapshot.get("state_hash", ""))
	hud._set_onboarding_visible(true)
	app._process(gravity_interval * 10.0)
	if str(app._current_snapshot.get("state_hash", "")) != phase_hash:
		failures.append("onboarding must not accumulate a latent gravity catch-up")
	hud._set_onboarding_visible(false)
	app._process(gravity_interval * 0.30)
	if str(app._current_snapshot.get("state_hash", "")) != phase_hash:
		failures.append("onboarding must preserve, not advance, the gravity phase")
	app._process(gravity_interval * 0.11)
	if str(app._current_snapshot.get("state_hash", "")) == phase_hash:
		failures.append("dismissal must resume from the preserved gravity phase")
	hud._set_onboarding_visible(true)
	if not hud.onboarding_suspends_live_gameplay():
		failures.append("visible guide step in an active live mode must suspend gameplay")
	hud._onboarding_panel.visible = false
	if hud.onboarding_suspends_live_gameplay():
		failures.append("hidden onboarding panel must not suspend live gameplay")
	hud._onboarding_panel.visible = true
	root.queue_free()
	await tree.process_frame
	return failures

func _setup(mode: String) -> Dictionary:
	var shape := [6, 6] if mode == "live_2d" else [5, 10, 4, 4]
	return {"schema_version": 2, "contract_version": 1, "mode": mode, "board_preset_id": "standard", "board_shape": shape, "piece_set_id": "classic" if mode == "live_2d" else "standard_4d_5", "random_mode": "fixed_seed", "seed": 1337, "initial_speed_level": 1, "topology_profile": {"contract_version": 1, "rank": shape.size(), "dimensions": shape.duplicate(), "seams": []}}

func _pause_event() -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = KEY_P
	event.pressed = true
	return event
