extends RefCounted

const Contract = preload("res://scripts/input/live_input_contract.gd")
const Profile = preload("res://scripts/presentation/presentation_profile.gd")
const Hud = preload("res://scripts/ui/replay_hud.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var root = load("res://scenes/game_bootstrap.tscn").instantiate()
	tree.root.add_child(root)
	await tree.process_frame
	var app = root.get_node("App")
	# Exercise explicit actions without gravity racing the initial-state oracle.
	app.set_process(false)
	var hud = root.get_node("ReplayHud")
	for mode in ["live_2d", "live_3d", "live_4d"]:
		var setup: Dictionary = hud.configured_live_setup(mode)
		app._start_configured_live_game(setup)
		await tree.process_frame
		await _check_bindings(failures, app, hud, mode)
		for random_mode in ["fixed_seed", "true_random"]:
			setup["random_mode"] = random_mode
			app._start_configured_live_game(setup)
			app.apply_presentation_profile(Profile.canonical_defaults().with_overrides({"theme.name": "diagnostic", "display.grid_mode": "none"}).with_design_state({"panel_rects": {"GameArea": [10, 20, 500, 400]}}))
			var frozen: Dictionary = app._active_live_setup.duplicate(true)
			var visual: Dictionary = app._presentation_profile.snapshot()
			var initial: Dictionary = app._current_snapshot.duplicate(true)
			# A later draft must not replace the setup used by either direct action.
			hud._game_setup_model.set_axis_text(0, "invalid")
			for state in ["playing", "paused", "gameover"]:
				for path in ["button", "key"]:
					app.call("_live_%s_command" % mode.trim_prefix("live_"), "hard_drop")
					if state == "paused":
						app.call("_toggle_%s_pause" % mode)
					elif state == "gameover":
						for drop in range(128):
							if app._current_snapshot.get("game_over", false): break
							app.call("_%s_command" % mode, "hard_drop")
						if not app._current_snapshot.get("game_over", false):
							failures.append("%s fixture must reach actual native game over" % mode)
					if path == "button":
						hud._restart_game_button.pressed.emit()
					else:
						var action := "live_reset" if mode == "live_2d" else "%s_reset" % mode
						var key: InputEvent = Contract.binding_events(action)[0].duplicate()
						key.pressed = true
						app._unhandled_input(key)
					_check_running(failures, app, hud, frozen, visual, "%s %s restart %s" % [mode, state, path])
					if app._current_snapshot.get("state_hash") != initial.get("state_hash") or app._current_snapshot.get("effective_seed") != initial.get("effective_seed"):
						failures.append("%s restart must reproduce the initial state and effective seed under %s" % [mode, random_mode])
			var seed_before = app._current_snapshot.get("effective_seed")
			if not hud._new_random_game_button.visible:
				failures.append("%s must expose another game for %s" % [mode, random_mode])
			app.call("_toggle_%s_pause" % mode)
			hud._new_random_game_button.pressed.emit()
			_check_running(failures, app, hud, frozen, visual, "%s new game" % mode)
			var seed_after = app._current_snapshot.get("effective_seed")
			if (random_mode == "fixed_seed" and seed_before != seed_after) or (random_mode == "true_random" and seed_before == seed_after):
				failures.append("%s New Game must follow %s seed policy" % [mode, random_mode])
			hud._change_setup_button.pressed.emit()
			await tree.process_frame
			if hud.current_screen() != Hud.SCREEN_GAME_SETUP:
				failures.append("%s Change Setup must directly open setup" % mode)
			hud._game_setup_model.reset_to_standard(mode)
	root.queue_free()
	await tree.process_frame
	return failures


func _check_running(failures: Array, app, hud, setup: Dictionary, visual: Dictionary, context: String) -> void:
	if app._mode != setup["mode"] or app._active_live_setup != setup:
		failures.append("%s must preserve the frozen canonical setup" % context)
	if hud.current_screen() != Hud.SCREEN_VIEWER or app._current_snapshot.get("trace_type") != setup["mode"]:
		failures.append("%s must enter ordinary live play directly, without menus or replay/debug startup" % context)
	if app._live_mode_paused() or app._current_snapshot.get("game_over", true):
		failures.append("%s must return to playing without pause/game-over leakage" % context)
	if app._presentation_profile.snapshot() != visual:
		failures.append("%s must retain complete presentation/Designer configuration" % context)
	var shape: Array = app._current_snapshot.get("board_shape", [])
	if shape.map(func(value): return int(value)) != setup["board_shape"]:
		failures.append("%s must preserve dimensions" % context)


func _check_bindings(failures: Array, app, hud, mode: String) -> void:
	var move_action := "live_move_left" if mode == "live_2d" else "%s_move_x_neg" % mode
	var move_events := InputMap.action_get_events(move_action)
	InputMap.action_erase_events(move_action)
	var move_key := InputEventKey.new()
	move_key.keycode = KEY_F11
	InputMap.action_add_event(move_action, move_key)
	hud._process(0.21)
	var move_rows: Array = hud._piece_control_strip.deterministic_snapshot().get("rows", [])
	if not move_rows.any(func(row): return row.get("role") == "translate" and str(row.get("binding")).contains("F11")):
		failures.append("%s movement reference must use the runtime binding" % mode)
	move_key.shift_pressed = true
	InputMap.action_erase_events(move_action)
	InputMap.action_add_event(move_action, move_key)
	if Contract.display_key(move_action) != "Shift+F11":
		failures.append("The binding label must retain configured modifiers")
	InputMap.action_erase_events(move_action)
	for event in move_events: InputMap.action_add_event(move_action, event)
	var action := "live_reset" if mode == "live_2d" else "%s_reset" % mode
	var previous := InputMap.action_get_events(action)
	InputMap.action_erase_events(action)
	var rebound := InputEventKey.new()
	rebound.keycode = KEY_F10
	InputMap.action_add_event(action, rebound)
	# Re-entering/initializing an app must not append default keys to a binding.
	app._ensure_input_map()
	app.call("_toggle_%s_pause" % mode)
	# The same poll used during play must refresh guidance while paused too.
	hud._process(0.21)
	var strip: Dictionary = hud._piece_control_strip.deterministic_snapshot()
	var rows: Array = strip.get("rows", [])
	var restart := rows.filter(func(row): return row.get("source_label") == "Restart Game")
	if restart.size() != 1 or restart[0].get("binding") != "F10" or InputMap.action_get_events(action).size() != 1:
		failures.append("%s visible control reference must track configured/rebound restart without restoring defaults" % mode)
	for role in ["translate", "rotate", "drop", "hold", "session"]:
		if not strip.get("roles", []).has(role):
			failures.append("%s must retain %s controls during play" % [mode, role])
	var reference := str(Contract.control_hint_groups(mode))
	if mode == "live_2d" and (reference.contains("Slice") or reference.contains("Rotate XW") or reference.contains("Pitch")):
		failures.append("2D reference must exclude 3D/4D actions")
	if mode == "live_4d" and not reference.contains("Slice"):
		failures.append("4D reference must include slice movement")
	rebound.pressed = true
	app._unhandled_input(rebound)
	if app._live_mode_paused():
		failures.append("%s displayed rebound restart must execute its configured action" % mode)
	InputMap.action_erase_events(action)
	hud._process(0.21)
	if Contract.display_key(action) != "Unbound":
		failures.append("Cleared bindings must not display a stale default")
	for event in previous: InputMap.action_add_event(action, event)
	hud._process(0.21)
