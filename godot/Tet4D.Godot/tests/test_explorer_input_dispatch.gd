extends RefCounted

const Contract = preload("res://scripts/input/live_input_contract.gd")
const Probe = preload("res://tests/fixtures/explorer_dispatch_probe.gd")
var failures: Array = []
var completed := false

func check(condition: bool, message: String) -> void:
	if not condition: failures.append("Explorer dispatch: " + message)

func key(code: int, pressed: bool = true) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = pressed
	return event

func bind(action: String, code: int) -> void:
	InputMap.action_erase_events(action)
	InputMap.action_add_event(action, key(code, false))

func send(app, event: InputEvent) -> void:
	var before: int = app.observed.size()
	app._input(event)
	if app.observed.size() == before and (not event is InputEventKey or event.keycode != KEY_SPACE):
		app._unhandled_input(event)

func run() -> Array:
	var tree := Engine.get_main_loop() as SceneTree
	var previous_size := tree.root.size
	var scene = load("res://scenes/game_bootstrap.tscn").instantiate()
	var app = scene.get_node("App")
	app.set_script(Probe)
	tree.root.add_child(scene)
	app.set_process(false)
	for frame in 10: await tree.process_frame
	var hud = scene.get_node("ReplayHud")
	var saved := {}
	for action in ["live_3d_move_x_neg", "live_4d_move_x_neg", "explorer_move_x_neg", "live_4d_camera_yaw_left", "explorer_camera_yaw_left", "view_zx_neg", "explorer_view_xz_neg", "explorer_replace_piece"]:
		saved[action] = InputMap.action_get_events(action)
	for dimension in [2, 3, 4]:
		app._start_practice(dimension)
		app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_IN)
		for frame in 3: await tree.process_frame
		await _check_focused_arrows(tree, app, hud, dimension)
		var native_before: String = app._live_bridge.call("live_%dd_snapshot_json" % dimension)
		var owned: Dictionary = Contract.explorer_profile(dimension)
		for spec in owned.input_actions:
			check(str(spec.action).begins_with("explorer_"), "every dispatched action belongs to Explorer")
		var live_action := "live_4d_move_x_neg" if dimension == 4 else "live_3d_move_x_neg"
		var helper_before := JSON.stringify(hud._piece_control_strip._groups)
		bind(live_action, KEY_F8)
		hud._refresh_configured_control_reference()
		check(JSON.stringify(hud._piece_control_strip._groups) == helper_before, "Live rebind leaves Explorer helper bindings unchanged")
		var before: Array = app._practice.cells.duplicate(true)
		send(app, key(KEY_F8))
		check(app._practice.cells == before, "%dD rebound Live movement cannot move Explorer" % dimension)
		app.observed.clear()
		send(app, key(KEY_A))
		check(app.observed.size() == 1 and app.observed[0].begins_with("move_"), "%dD Explorer keeps its A default after Live rebind" % dimension)
		app._practice_action("retry")
		bind("explorer_move_x_neg", KEY_F9)
		hud._refresh_configured_control_reference()
		check("F9" in JSON.stringify(hud._piece_control_strip._groups), "Explorer rebind updates the same helper inventory")
		app.observed.clear()
		send(app, key(KEY_A))
		check(app.observed.is_empty(), "%dD clearing Explorer's default cannot fall through to a Live alias" % dimension)
		send(app, key(KEY_F9))
		check(app.observed.size() == 1 and app.observed[0].begins_with("move_"), "%dD Explorer rebound key dispatches once" % dimension)
		var held := key(KEY_F9)
		held.echo = true
		send(app, held)
		check(app.observed.size() == 1, "OS key echo does not dispatch twice")
		app._practice_action("retry")
		Input.action_press("explorer_move_x_neg")
		app.observed.clear()
		send(app, key(KEY_F9))
		app._process_explorer_input_repeat(0.0)
		app._process_explorer_input_repeat(app.LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS + 0.01)
		check(app.observed.size() == 2 and app.observed[0] == app.observed[1], "%dD held Explorer key repeats the same intent after delay, including at a wall" % dimension)
		Input.action_press("explorer_move_x_pos")
		send(app, key(KEY_D))
		var opposed: Array = app._practice.cells.duplicate(true)
		app._process_explorer_input_repeat(1.0)
		check(app._practice.cells == opposed, "%dD opposite held keys cancel repeats" % dimension)
		Input.action_release("explorer_move_x_pos")
		app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
		app._process_explorer_input_repeat(1.0)
		check(app._practice.cells == opposed and app._explorer_repeat_state.is_empty(), "focus loss disarms repeats without moving the object")
		app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_IN)
		app._process_explorer_input_repeat(1.0)
		check(app._practice.cells == opposed, "focus return cannot replay a stale held key")
		Input.action_release("explorer_move_x_neg")
		app._practice_action("retry")
		# The old 3D/4D Y pair is deliberately still one-shot in this refactor.
		if dimension > 2:
			Input.action_press("explorer_move_y_neg")
			send(app, key(KEY_Z))
			var y_once: Array = app._practice.cells.duplicate(true)
			app._process_explorer_input_repeat(1.0)
			check(app._practice.cells == y_once, "Phase 2 preserves one-shot 3D/4D Y movement")
			Input.action_release("explorer_move_y_neg")
		# Modal ownership and navigation disarm existing movement, including held Input state.
		Input.action_press("explorer_move_x_neg")
		send(app, key(KEY_F9))
		hud._live_interaction_owns_input = true
		var modal_pose: Array = app._practice.cells.duplicate(true)
		send(app, key(KEY_F9))
		app._process_explorer_input_repeat(1.0)
		hud._live_interaction_owns_input = false
		app._process_explorer_input_repeat(1.0)
		check(app._practice.cells == modal_pose and app._explorer_repeat_state.is_empty(), "modal UI disarms held Explorer input")
		var navigation_pose: Array = app._practice.cells.duplicate(true)
		app._return_to_main_menu()
		app._process_explorer_input_repeat(1.0)
		app._practice_action("dimension_%d" % dimension)
		app._process_explorer_input_repeat(1.0)
		check(app._practice.cells == navigation_pose and app._explorer_repeat_state.is_empty(), "menu return cannot replay held Explorer input")
		Input.action_release("explorer_move_x_neg")
		app._practice_action("retry")
		app.observed.clear()
		var physical := key(KEY_F12)
		physical.physical_keycode = KEY_D
		send(app, physical)
		check(app.observed.size() == 1 and app.observed[0].begins_with("move_"), "unclaimed printed key resolves its physical Explorer position")
		physical.pressed = false
		send(app, physical)
		app._process_explorer_input_repeat(1.0)
		check(app._physical_fallback_held.is_empty(), "physical release clears held state")
		if dimension > 2:
			bind("live_4d_camera_yaw_left", KEY_F8)
			app.observed.clear()
			send(app, key(KEY_O))
			check(app.observed == ["look_yaw_left"], "Live camera rebind cannot change Explorer look")
			for action in ["live_4d_camera_yaw_left"]:
				InputMap.action_erase_events(action)
				for event in saved[action]: InputMap.action_add_event(action, event)
		if dimension == 4:
			bind("view_zx_neg", KEY_F8)
			app.observed.clear()
			send(app, key(KEY_1))
			check(app.observed == ["basis_xz_neg"], "ordinary Play basis rebind cannot change Explorer view turns")
			app._practice_action("view_reset")
			bind("explorer_view_xz_neg", KEY_F10)
			app.observed.clear()
			send(app, key(KEY_1))
			check(app.observed.is_empty(), "Explorer view rebind cannot fall through to a shared basis alias")
			send(app, key(KEY_F10))
			check(app.observed == ["basis_xz_neg"], "Explorer view uses its rebound action")
			for action in ["view_zx_neg", "explorer_view_xz_neg"]:
				InputMap.action_erase_events(action)
				for event in saved[action]: InputMap.action_add_event(action, event)
			app._practice_action("view_reset")
		app._practice_action("retry")
		check(app._live_bridge.call("live_%dd_snapshot_json" % dimension) == native_before, "%dD all Explorer key/repeat paths leave native gameplay unchanged" % dimension)
		check(app.live_handler_calls == 0, "Explorer never invokes any Live keyboard handler")
		# Explorer rebinding cannot change ordinary Play's action defaults.
		InputMap.action_erase_events(live_action)
		for event in saved[live_action]: InputMap.action_add_event(live_action, event)
		app._practice_action("play")
		var live_before: String = app._live_bridge.call("live_%dd_snapshot_json" % dimension)
		send(app, key(KEY_F9))
		check(app._live_bridge.call("live_%dd_snapshot_json" % dimension) == live_before, "Explorer-only rebind is inert during ordinary Play")
		app.live_handler_calls = 0
		InputMap.action_erase_events("explorer_move_x_neg")
		for event in saved.explorer_move_x_neg: InputMap.action_add_event("explorer_move_x_neg", event)
	app._start_practice(4)
	app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_IN)
	var button := Button.new()
	button.text = "GUI focus trap"
	var pressed := {"count": 0}
	button.pressed.connect(func(): pressed.count += 1)
	tree.root.add_child(button)
	button.grab_focus()
	app.observed.clear()
	Input.parse_input_event(key(KEY_SPACE))
	await tree.process_frame
	Input.parse_input_event(key(KEY_SPACE, false))
	await tree.process_frame
	check(app.observed.count("replace") == 1 and pressed.count == 0, "early Space replaces once without activating focused GUI button")
	bind("explorer_replace_piece", KEY_F8)
	app.observed.clear()
	Input.parse_input_event(key(KEY_SPACE))
	await tree.process_frame
	Input.parse_input_event(key(KEY_SPACE, false))
	await tree.process_frame
	check(app.observed.is_empty() and pressed.count == 0, "unbound Space stays claimed without resurrecting Replace or activating GUI")
	button.queue_free()
	for action in saved:
		InputMap.action_erase_events(action)
		for event in saved[action]: InputMap.action_add_event(action, event)
	scene.queue_free()
	await tree.process_frame
	tree.root.size = previous_size
	completed = true
	return failures


func _check_focused_arrows(tree: SceneTree, app, hud, dimension: int) -> void:
	var tabs: TabContainer = hud._practice_panel._tabs
	var bar: TabBar = tabs.get_tab_bar()
	var previous_focus := bar.focus_mode
	bar.focus_mode = Control.FOCUS_ALL
	bar.grab_focus()
	var selected := tabs.current_tab
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
		app._practice_action("retry")
		var before: Array = app._practice.cells.duplicate(true)
		app.observed.clear()
		Input.parse_input_event(key(code))
		await tree.process_frame
		check(app.observed.size() == 1 and app.observed[0].begins_with("move_") and app._practice.cells != before, "%dD focused-tab arrow moves the piece exactly once" % dimension)
		var echo_event := key(code)
		echo_event.echo = true
		Input.parse_input_event(echo_event)
		await tree.process_frame
		Input.parse_input_event(key(code, false))
		await tree.process_frame
		check(tabs.current_tab == selected and app.observed.size() == 1, "%dD arrows and OS echo cannot navigate Explorer tabs" % dimension)
	# A genuine modal keeps keyboard ownership even with a movement key held.
	hud._live_interaction_owns_input = true
	app.observed.clear()
	Input.parse_input_event(key(KEY_RIGHT))
	await tree.process_frame
	Input.parse_input_event(key(KEY_RIGHT, false))
	await tree.process_frame
	check(app.observed.is_empty(), "modal input ownership still blocks Explorer movement")
	hud._live_interaction_owns_input = false
	bar.release_focus()
	bar.focus_mode = previous_focus
	app._practice_action("retry")
