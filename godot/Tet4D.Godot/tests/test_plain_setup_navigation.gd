extends RefCounted

const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const GameSetupPanelScript = preload("res://scripts/ui/game_setup/game_setup_panel.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var panel = GameSetupPanelScript.new()
	tree.root.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var model = GameSetupModelScript.new()
	model.set_mode(GameSetupSpecScript.MODE_4D)
	panel.configure(model)
	await tree.process_frame
	if panel._board_selector.item_count != 4:
		failures.append("setup preset selector should include the derived Custom identity")
	if panel._axis_inputs.size() != 4:
		failures.append("4D setup should render exactly X/Y/Z/W editable fields")
	if panel._piece_selector.item_count != 3:
		failures.append("4D setup should expose three audited production piece sets")
	if not panel._seed_row.visible:
		failures.append("fixed-seed setup should show the seed field")
	if panel.first_focus_control() != panel._board_selector:
		failures.append("setup should restore focus at the preset shortcut")
	for control in panel._focus_controls:
		if control.focus_mode == Control.FOCUS_NONE:
			failures.append("setup control should remain keyboard reachable: %s" % control.name)
	panel._axis_inputs[3].text = "1"
	panel._on_axis_text_changed(3, "1")
	await tree.process_frame
	if not panel._start_button.disabled or panel._validation_label.text.find("spawn_not_viable @ $.piece_set_id") == -1:
		failures.append("W=1 standard pieces must present a structured native spawn error and block Start")
	model.select_piece_set("embedded_3d")
	panel.configure(model)
	await tree.process_frame
	if panel._start_button.disabled:
		failures.append("W=1 Embedded 3D must remain launchable through the same editor")
	panel._axis_inputs[3].text = "1e0"
	panel._on_axis_text_changed(3, "1e0")
	await tree.process_frame
	if not panel._start_button.disabled or panel._axis_inputs[3].text != "1e0" or panel._validation_label.text.find("invalid_field_type @ $.board_shape[3]") == -1:
		failures.append("invalid typed axis text must remain visible, structured, and non-launchable")
	panel._on_axis_adjusted(3, 1)
	if panel._axis_inputs[3].text != "2" or panel._start_button.disabled:
		failures.append("axis increment should recover from invalid text using the last-valid dimension")
	model.select_piece_set("embedded_3d")
	panel.configure(model)
	await tree.process_frame
	panel._on_reset_sizes_pressed()
	if model.selected_shape() != [5, 10, 4, 4] or model.selected_piece_set_id() != "embedded_3d":
		failures.append("Reset Sizes should not reset piece selection")
	panel._on_reset_setup_pressed()
	if model.selected_piece_set_id() != "standard_4d_5":
		failures.append("Reset Setup should reset the complete mode setup")

	model.select_random_mode(GameSetupSpecScript.RANDOM_MODE_TRUE_RANDOM)
	panel.configure(model)
	await tree.process_frame
	if panel._seed_row.visible:
		failures.append("true-random setup should hide the configured-seed editor")
	if panel._random_description.text.find("effective seed") == -1:
		failures.append("true-random setup should explain generated effective seed behavior")
	model.select_random_mode(GameSetupSpecScript.RANDOM_MODE_FIXED_SEED)
	panel.configure(model)
	await tree.process_frame
	panel._seed_input.text = "1e3"
	panel._on_seed_changed(panel._seed_input.text)
	if panel._seed_error.text.is_empty() or not panel._start_button.disabled:
		failures.append("scientific-notation seed should show a structured error and disable Start")
	panel._seed_input.text = "1337"
	panel._on_seed_changed(panel._seed_input.text)
	if not panel._seed_error.text.is_empty() or panel._start_button.disabled:
		failures.append("valid decimal seed should restore Start")

	var started := []
	panel.start_requested.connect(func(setup: Dictionary) -> void: started.append(setup))
	panel._on_start_pressed()
	if started.size() != 1:
		failures.append("activation should emit one native-validated setup")
	elif started[0].has("last_selected") or started[0].has("random_mode_index"):
		failures.append("Start should not emit persistence or legacy-index fields")
	var scroll := panel.get_child(0) as ScrollContainer
	if scroll == null or scroll.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		failures.append("setup screen should use viewport-safe vertical scrolling")
	var app = TraceReplayAppScript.new()
	app._bundle = BundleLoader.load_bundle()
	var slow_2d := app._gravity_interval_for_setup({"mode": "live_2d", "initial_speed_level": 1})
	var fast_2d := app._gravity_interval_for_setup({"mode": "live_2d", "initial_speed_level": 10})
	var slow_3d := app._gravity_interval_for_setup({"mode": "live_3d", "initial_speed_level": 1})
	var slow_4d := app._gravity_interval_for_setup({"mode": "live_4d", "initial_speed_level": 1})
	if not is_equal_approx(slow_2d, 1.0) or not is_equal_approx(fast_2d, 0.1):
		failures.append("2D setup speed should use the Python-authoritative 1000ms curve without wall-clock tests")
	if not is_equal_approx(slow_3d, 1.35) or not is_equal_approx(slow_4d, 1.7):
		failures.append("3D/4D setup speed should use the bundled dimension curves")
	app.free()
	panel.queue_free()
	await tree.process_frame
	return failures
