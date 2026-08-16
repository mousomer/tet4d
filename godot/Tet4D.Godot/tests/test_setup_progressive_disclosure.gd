extends RefCounted

# Stage 54E-3b evidence: the setup surface presents the accepted RDS section 4.4
# taxonomy as progressive disclosure without changing any setup semantics.

const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const GameSetupPanelScript = preload("res://scripts/ui/game_setup/game_setup_panel.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const GameSetupStoreScript = preload("res://scripts/ui/game_setup/game_setup_store.gd")

const AXIS_COUNT_BY_MODE := {
	"live_2d": 2,
	"live_3d": 3,
	"live_4d": 4,
}


func run() -> Array:
	var failures: Array = []
	await _check_ordinary_surface(failures)
	await _check_board_disclosure(failures)
	await _check_custom_board_state(failures)
	await _check_piece_set_disclosure(failures)
	await _check_advanced_game_disclosure(failures)
	await _check_controls_disclosure(failures)
	await _check_deterministic_isolation(failures)
	await _check_navigation(failures)
	return failures


# --- Ordinary setup -----------------------------------------------------------


func _check_ordinary_surface(failures: Array) -> void:
	for mode in GameSetupSpecScript.modes():
		var harness := await _make_panel(mode)
		var panel = harness["panel"]
		for section_id in panel.disclosure_section_ids():
			if panel.is_section_expanded(section_id):
				failures.append("%s: %s must start collapsed for a preset-backed setup" % [mode, section_id])
		if not panel._board_selector.is_visible_in_tree():
			failures.append("%s: the preset shortcut must stay in the ordinary surface" % mode)
		if not panel._speed_selector.is_visible_in_tree():
			failures.append("%s: Starting Speed must stay in the ordinary surface" % mode)
		if panel._validation_label.is_visible_in_tree():
			failures.append("%s: a valid ordinary setup must not carry a validation banner" % mode)
		if panel._start_button.disabled:
			failures.append("%s: valid defaults must leave Start immediately available" % mode)
		if not panel._start_button.is_visible_in_tree():
			failures.append("%s: Start must remain the visible primary action" % mode)
		for control in panel.hidden_focus_controls():
			if control.focus_mode != Control.FOCUS_NONE:
				failures.append("%s: undisclosed %s must not be a focus target" % [mode, control.name])
		var expected_ordinary := 3 if mode == GameSetupSpecScript.MODE_2D else 4
		var ordinary_count: int = panel.visible_focus_controls().size()
		if ordinary_count > expected_ordinary + 5:
			failures.append("%s: ordinary setup exposes too many controls: %d" % [mode, ordinary_count])
		await _free_panel(harness)


# --- Board --------------------------------------------------------------------


func _check_board_disclosure(failures: Array) -> void:
	for mode in GameSetupSpecScript.modes():
		var harness := await _make_panel(mode)
		var panel = harness["panel"]
		var model = harness["model"]
		var expected_axes: int = int(AXIS_COUNT_BY_MODE.get(mode, 0))
		if panel._axis_inputs.size() != expected_axes:
			failures.append("%s: board customization must build exactly the active axes" % mode)
		for axis_input in panel._axis_inputs:
			if axis_input.is_visible_in_tree():
				failures.append("%s: a preset-backed board must not permanently expose axis editors" % mode)
		panel.set_section_expanded(panel.SECTION_BOARD, true)
		await harness["tree"].process_frame
		var revealed := 0
		for axis_input in panel._axis_inputs:
			if axis_input.is_visible_in_tree():
				revealed += 1
			if axis_input.focus_mode != Control.FOCUS_ALL:
				failures.append("%s: revealed axis editor must be keyboard reachable" % mode)
		if revealed != expected_axes:
			failures.append("%s: Customize Board must expose exactly %d axes, exposed %d" % [
				mode, expected_axes, revealed,
			])
		var reset_sizes := panel.find_child("ResetSizesButton", true, false) as Button
		if reset_sizes == null or not reset_sizes.is_visible_in_tree():
			failures.append("%s: Reset Sizes belongs with board customization" % mode)

		# Dimension editing keeps the Stage 54B validation contract.
		var last_axis := expected_axes - 1
		var original: Array = model.selected_shape()
		panel._axis_inputs[last_axis].text = "not-a-number"
		panel._on_axis_text_changed(last_axis, "not-a-number")
		await harness["tree"].process_frame
		if not panel._start_button.disabled:
			failures.append("%s: malformed dimension text must block Start" % mode)
		if panel._validation_label.text.find("$.board_shape[%d]" % last_axis) == -1:
			failures.append("%s: malformed dimension text must stay visible and structured" % mode)
		panel._on_axis_adjusted(last_axis, 1)
		await harness["tree"].process_frame
		if panel._axis_inputs[last_axis].text != str(int(original[last_axis]) + 1):
			failures.append("%s: increment must recover from malformed text using the last-valid dimension" % mode)

		# Reset Sizes restores dimensions only.
		if mode != GameSetupSpecScript.MODE_2D:
			model.select_control_frame("rotation_frame", "absolute")
		model.select_speed_level(7)
		panel._on_reset_sizes_pressed()
		await harness["tree"].process_frame
		if model.selected_shape() != GameSetupSpecScript.canonical_default_shape(mode):
			failures.append("%s: Reset Sizes must restore the canonical dimensions" % mode)
		if model.selected_speed_level() != 7:
			failures.append("%s: Reset Sizes must not reset Starting Speed" % mode)
		if mode != GameSetupSpecScript.MODE_2D and model.selected_control_frames().get("rotation_frame") != "absolute":
			failures.append("%s: Reset Sizes must not reset control frames" % mode)
		await _free_panel(harness)


func _check_custom_board_state(failures: Array) -> void:
	for mode in GameSetupSpecScript.modes():
		var tree := Engine.get_main_loop() as SceneTree
		var model = GameSetupModelScript.new()
		model.set_mode(mode)
		var axis_count: int = int(AXIS_COUNT_BY_MODE.get(mode, 0))
		var custom_shape: Array = GameSetupSpecScript.canonical_default_shape(mode)
		custom_shape[0] = int(custom_shape[0]) + 1
		model.set_axis_text(0, str(custom_shape[0]))
		if not model.selected_preset_id().is_empty():
			failures.append("%s: the probe shape must not match a named preset" % mode)
		var panel = GameSetupPanelScript.new()
		tree.root.add_child(panel)
		panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		panel.configure(model)
		await tree.process_frame
		if not panel.is_section_expanded(panel.SECTION_BOARD):
			failures.append("%s: a rebuilt custom board must expose its dimensions without another step" % mode)
		for axis_index in range(axis_count):
			if not panel._axis_inputs[axis_index].is_visible_in_tree():
				failures.append("%s: custom board dimensions must be immediately visible" % mode)
		var selected_id := str(panel._board_selector.get_item_metadata(panel._board_selector.selected))
		if not selected_id.is_empty():
			failures.append("%s: a non-preset shape must read as Custom" % mode)
		if panel._board_selector.get_item_text(panel._board_selector.selected).find("Custom") == -1:
			failures.append("%s: the Custom identity must be labelled Custom" % mode)

		# Selecting `Custom` is an affordance, not a board mutation.
		var before: Array = model.selected_shape()
		panel.set_section_expanded(panel.SECTION_BOARD, false)
		await tree.process_frame
		panel._on_board_selected(panel._board_selector.item_count - 1)
		await tree.process_frame
		if model.selected_shape() != before:
			failures.append("%s: selecting Custom must preserve the current dimensions" % mode)
		if not panel.is_section_expanded(panel.SECTION_BOARD):
			failures.append("%s: selecting Custom must expose the dimension editors" % mode)
		panel.queue_free()
		await tree.process_frame


# --- Piece set ----------------------------------------------------------------


func _check_piece_set_disclosure(failures: Array) -> void:
	var harness := await _make_panel(GameSetupSpecScript.MODE_2D)
	var panel = harness["panel"]
	var model = harness["model"]
	if panel._piece_selector != null:
		failures.append("2D must not present a piece-set selector while only one set exists")
	if model.selected_piece_set_id() != "classic":
		failures.append("2D must still carry its piece set in the model")
	if str(model.canonical_session_setup().get("piece_set_id", "")) != "classic":
		failures.append("2D must still carry its piece set in the session payload")
	if panel._start_button.disabled:
		failures.append("2D setup must remain launchable without a piece-set selector")
	await _free_panel(harness)

	for mode in [GameSetupSpecScript.MODE_3D, GameSetupSpecScript.MODE_4D]:
		var choice_harness := await _make_panel(mode)
		var choice_panel = choice_harness["panel"]
		var choice_model = choice_harness["model"]
		if choice_panel._piece_selector == null or not choice_panel._piece_selector.is_visible_in_tree():
			failures.append("%s: the piece-set choice belongs in the ordinary surface" % mode)
			await _free_panel(choice_harness)
			continue
		if choice_panel._piece_selector.focus_mode != Control.FOCUS_ALL:
			failures.append("%s: the piece-set choice must be keyboard reachable" % mode)
		var expected_count: int = GameSetupSpecScript.piece_sets_for_mode(mode).size()
		if choice_panel._piece_selector.item_count != expected_count:
			failures.append("%s: every audited piece set must remain selectable" % mode)
		for index in range(choice_panel._piece_selector.item_count):
			var piece_id := str(choice_panel._piece_selector.get_item_metadata(index))
			var spec := GameSetupSpecScript.piece_set(mode, piece_id)
			if spec.is_empty():
				failures.append("%s: piece-set option %s must keep its audited identity" % [mode, piece_id])
			elif choice_panel._piece_selector.get_item_text(index) != str(spec.get("label", "")):
				failures.append("%s: piece-set option %s must keep its audited label" % [mode, piece_id])
		await _free_panel(choice_harness)

	# Compatibility validation is unchanged: W=1 with True 4D pieces stays invalid
	# while W=1 with Embedded 3D stays launchable.
	var w_harness := await _make_panel(GameSetupSpecScript.MODE_4D)
	var w_panel = w_harness["panel"]
	var w_model = w_harness["model"]
	w_panel.set_section_expanded(w_panel.SECTION_BOARD, true)
	w_panel._on_axis_text_changed(3, "1")
	await w_harness["tree"].process_frame
	if not w_panel._start_button.disabled:
		failures.append("W=1 with True 4D pieces must remain non-launchable")
	if w_panel._validation_label.text.find("$.piece_set_id") == -1:
		failures.append("W=1 piece-set incompatibility must stay visible in the summary")
	if not w_panel._validation_label.is_visible_in_tree():
		failures.append("W=1 piece-set incompatibility must leave the summary visible")
	w_model.select_piece_set("embedded_3d")
	w_panel._on_axis_text_changed(3, "1")
	await w_harness["tree"].process_frame
	if w_panel._start_button.disabled:
		failures.append("W=1 with Embedded 3D must remain launchable")
	await _free_panel(w_harness)


# --- Advanced game ------------------------------------------------------------


func _check_advanced_game_disclosure(failures: Array) -> void:
	var harness := await _make_panel(GameSetupSpecScript.MODE_4D)
	var panel = harness["panel"]
	var model = harness["model"]
	var tree: SceneTree = harness["tree"]
	if panel._random_selector.is_visible_in_tree():
		failures.append("randomness must not dominate the ordinary setup surface")
	if panel._random_selector.focus_mode != Control.FOCUS_NONE:
		failures.append("collapsed randomness must not be a focus target")
	panel.set_section_expanded(panel.SECTION_ADVANCED, true)
	await tree.process_frame
	if not panel._random_selector.is_visible_in_tree():
		failures.append("Advanced Game must expose randomness")
	if not panel._seed_input.is_visible_in_tree():
		failures.append("Fixed Seed must expose Seed inside Advanced Game")

	model.select_random_mode(GameSetupSpecScript.RANDOM_MODE_TRUE_RANDOM)
	panel._on_random_selected(_index_for_metadata(panel._random_selector, GameSetupSpecScript.RANDOM_MODE_TRUE_RANDOM))
	await tree.process_frame
	if panel._random_description.text.find("effective seed") == -1:
		failures.append("randomness copy must keep explaining effective-seed behavior")
	if panel._seed_input.is_visible_in_tree():
		failures.append("True Random must hide Seed")
	if panel._seed_input.focus_mode != Control.FOCUS_NONE:
		failures.append("hidden Seed must not be a focus target")
	panel._on_random_selected(_index_for_metadata(panel._random_selector, GameSetupSpecScript.RANDOM_MODE_FIXED_SEED))
	await tree.process_frame
	if not panel._seed_input.is_visible_in_tree():
		failures.append("returning to Fixed Seed must restore Seed")

	# Seed validation is unchanged.
	panel._seed_input.text = "1e3"
	panel._on_seed_changed(panel._seed_input.text)
	await tree.process_frame
	if panel._seed_error.text.is_empty() or not panel._start_button.disabled:
		failures.append("an invalid seed must show a structured error and block Start")
	panel._seed_input.text = "1337"
	panel._on_seed_changed(panel._seed_input.text)
	await tree.process_frame
	if not panel._seed_error.text.is_empty() or panel._start_button.disabled:
		failures.append("a valid seed must restore Start")

	# A seed failure inside a collapsed section stays explained and reachable.
	panel._seed_input.text = "1e3"
	panel._on_seed_changed(panel._seed_input.text)
	panel.set_section_expanded(panel.SECTION_ADVANCED, false)
	await tree.process_frame
	if panel._validation_label.text.find("invalid_seed @ $.seed") == -1:
		failures.append("a hidden seed failure must still be explained in the summary")
	if not panel._validation_label.is_visible_in_tree():
		failures.append("a hidden seed failure must leave the summary visible")
	panel._on_start_pressed()
	await tree.process_frame
	if not panel.is_section_expanded(panel.SECTION_ADVANCED):
		failures.append("blocked Start must expose the section owning the failure")
	await _free_panel(harness)


# --- Controls -----------------------------------------------------------------


func _check_controls_disclosure(failures: Array) -> void:
	var flat := await _make_panel(GameSetupSpecScript.MODE_2D)
	var flat_panel = flat["panel"]
	if flat_panel.disclosure_section_ids().has(flat_panel.SECTION_CONTROLS):
		failures.append("2D must not present the control-frame disclosure")
	if flat_panel._translation_frame_selector != null or flat_panel._rotation_frame_selector != null:
		failures.append("2D must not build control-frame selectors")
	await _free_panel(flat)

	for mode in [GameSetupSpecScript.MODE_3D, GameSetupSpecScript.MODE_4D]:
		var harness := await _make_panel(mode)
		var panel = harness["panel"]
		var model = harness["model"]
		var tree: SceneTree = harness["tree"]
		if not panel.disclosure_section_ids().has(panel.SECTION_CONTROLS):
			failures.append("%s: control frames must remain reachable" % mode)
			await _free_panel(harness)
			continue
		if panel.is_section_expanded(panel.SECTION_CONTROLS):
			failures.append("%s: control frames must be secondary by default" % mode)
		if panel._translation_frame_selector.is_visible_in_tree():
			failures.append("%s: control frames must not dominate ordinary setup" % mode)
		model.select_control_frame("translation_frame", "absolute")
		model.select_control_frame("rotation_frame", "absolute")
		var before: Dictionary = model.selected_control_frames()
		panel.set_section_expanded(panel.SECTION_CONTROLS, true)
		await tree.process_frame
		panel.set_section_expanded(panel.SECTION_CONTROLS, false)
		await tree.process_frame
		panel.set_section_expanded(panel.SECTION_CONTROLS, true)
		await tree.process_frame
		if model.selected_control_frames() != before:
			failures.append("%s: toggling disclosure must not change control-frame values" % mode)
		if not panel._translation_frame_selector.is_visible_in_tree():
			failures.append("%s: Controls must expose Translation" % mode)
		if not panel._rotation_frame_selector.is_visible_in_tree():
			failures.append("%s: Controls must expose Rotation" % mode)
		if panel._translation_frame_selector.focus_mode != Control.FOCUS_ALL:
			failures.append("%s: revealed Translation must be keyboard reachable" % mode)
		await _free_panel(harness)


# --- Deterministic and persistence isolation ----------------------------------


func _check_deterministic_isolation(failures: Array) -> void:
	for mode in GameSetupSpecScript.modes():
		var harness := await _make_panel(mode)
		var panel = harness["panel"]
		var model = harness["model"]
		var tree: SceneTree = harness["tree"]
		var before := JSON.stringify(model.canonical_session_setup())
		var persisted_before := JSON.stringify(model.last_valid_entries())
		for section_id in panel.disclosure_section_ids():
			panel.set_section_expanded(section_id, true)
			await tree.process_frame
			panel.toggle_section(section_id)
			await tree.process_frame
			panel.toggle_section(section_id)
			await tree.process_frame
		if JSON.stringify(model.canonical_session_setup()) != before:
			failures.append("%s: toggling disclosure must leave the session setup unchanged" % mode)
		if JSON.stringify(model.last_valid_entries()) != persisted_before:
			failures.append("%s: toggling disclosure must leave the persisted setup unchanged" % mode)
		var payload: Dictionary = model.canonical_session_setup()
		for forbidden in ["translation_frame", "rotation_frame", "board", "advanced_game", "controls", "disclosure"]:
			if payload.has(forbidden):
				failures.append("%s: %s must stay outside the session payload" % [mode, forbidden])
		await _free_panel(harness)

	# The persisted document keeps its established fields only.
	var store = GameSetupStoreScript.new()
	var model_for_store = GameSetupModelScript.new()
	var path := "user://test_setup_disclosure.json"
	if not store.save_last_validated(model_for_store, path):
		failures.append("the setup store must still persist a valid model")
	else:
		var file := FileAccess.open(path, FileAccess.READ)
		var document := file.get_as_text() if file != null else ""
		for forbidden in ["expanded", "disclosure", "section", "collapsed"]:
			if document.find(forbidden) != -1:
				failures.append("persisted setup must not record %s" % forbidden)
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


# --- Navigation ---------------------------------------------------------------


func _check_navigation(failures: Array) -> void:
	var harness := await _make_panel(GameSetupSpecScript.MODE_4D)
	var panel = harness["panel"]
	var tree: SceneTree = harness["tree"]

	# Disclosure controls are ordinary focusable buttons, so keyboard confirm and
	# pointer press reach the same semantic toggle.
	var board_button := panel.find_child("Disclosure__%s" % panel.SECTION_BOARD, true, false) as Button
	if board_button == null:
		failures.append("the board disclosure must be a real control")
		await _free_panel(harness)
		return
	if board_button.focus_mode != Control.FOCUS_ALL:
		failures.append("a disclosure control must be keyboard focusable")
	board_button.emit_signal("pressed")
	await tree.process_frame
	if not panel.is_section_expanded(panel.SECTION_BOARD):
		failures.append("activating the disclosure control must expand its section")
	board_button.emit_signal("pressed")
	await tree.process_frame
	if panel.is_section_expanded(panel.SECTION_BOARD):
		failures.append("activating the disclosure control again must collapse its section")

	# Collapsing a section while focus is inside it must land focus somewhere safe.
	panel.set_section_expanded(panel.SECTION_BOARD, true)
	await tree.process_frame
	panel._axis_inputs[0].grab_focus()
	await tree.process_frame
	if tree.root.gui_get_focus_owner() != panel._axis_inputs[0]:
		failures.append("a revealed axis editor must accept focus")
	panel.set_section_expanded(panel.SECTION_BOARD, false)
	await tree.process_frame
	var focus_owner := tree.root.gui_get_focus_owner()
	if focus_owner != board_button:
		failures.append("collapsing a section holding focus must move focus to its disclosure control, got %s" % (
			"none" if focus_owner == null else focus_owner.name
		))

	# Collapsing a section that does not hold focus must not steal it.
	panel._board_selector.grab_focus()
	await tree.process_frame
	panel.set_section_expanded(panel.SECTION_ADVANCED, true)
	await tree.process_frame
	panel.set_section_expanded(panel.SECTION_ADVANCED, false)
	await tree.process_frame
	if tree.root.gui_get_focus_owner() != panel._board_selector:
		failures.append("collapsing an unfocused section must not steal focus")

	# Ordinary Up/Down navigation stays a closed loop over revealed controls only.
	var revealed: Array = panel.visible_focus_controls()
	if revealed.is_empty():
		failures.append("setup must always expose focusable controls")
	else:
		var walker: Control = revealed[0]
		for step in range(revealed.size()):
			var next_path: NodePath = walker.focus_neighbor_bottom
			var next_control := walker.get_node_or_null(next_path) as Control
			if next_control == null:
				failures.append("focus order must stay connected at %s" % walker.name)
				break
			if not next_control.is_visible_in_tree():
				failures.append("focus order must not route through the hidden control %s" % next_control.name)
				break
			walker = next_control
		if walker != revealed[0]:
			failures.append("focus order must return to its origin over the revealed controls")

	# The setup surface stays scroll-safe at the supported compact viewport.
	var original_size: Vector2i = tree.root.size
	tree.root.size = Vector2i(960, 640)
	panel.set_section_expanded(panel.SECTION_BOARD, true)
	panel.set_section_expanded(panel.SECTION_ADVANCED, true)
	panel.set_section_expanded(panel.SECTION_CONTROLS, true)
	await tree.process_frame
	await tree.process_frame
	var scroll := panel.get_child(0) as ScrollContainer
	if scroll == null or scroll.horizontal_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		failures.append("setup must keep viewport-safe vertical scrolling")
	else:
		panel._start_button.grab_focus()
		await tree.process_frame
		await tree.process_frame
		if not _is_within_scroll(scroll, panel._start_button):
			failures.append("focusing Start must scroll it into view at the compact viewport")
	tree.root.size = original_size
	await _free_panel(harness)


# --- Helpers ------------------------------------------------------------------


func _make_panel(mode: String) -> Dictionary:
	var tree := Engine.get_main_loop() as SceneTree
	var panel = GameSetupPanelScript.new()
	tree.root.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var model = GameSetupModelScript.new()
	model.set_mode(mode)
	panel.configure(model)
	await tree.process_frame
	return {"tree": tree, "panel": panel, "model": model}


func _free_panel(harness: Dictionary) -> void:
	var tree: SceneTree = harness["tree"]
	harness["panel"].queue_free()
	await tree.process_frame


func _index_for_metadata(selector: OptionButton, value: String) -> int:
	for index in range(selector.item_count):
		if str(selector.get_item_metadata(index)) == value:
			selector.select(index)
			return index
	return -1


func _is_within_scroll(scroll: ScrollContainer, control: Control) -> bool:
	var viewport_rect := Rect2(scroll.global_position, scroll.size)
	var control_rect := control.get_global_rect()
	return viewport_rect.intersects(control_rect)
