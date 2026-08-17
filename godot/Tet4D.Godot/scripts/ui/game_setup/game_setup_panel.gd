extends Control

class_name GameSetupPanel

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const SetupFieldRegistryScript = preload("res://scripts/ui/game_setup/setup_field_registry.gd")
const SetupFieldSpecScript = preload("res://scripts/ui/game_setup/setup_field_spec.gd")
const ShellDesignTokensScript = preload("res://scripts/ui/style/shell_design_tokens.gd")

signal start_requested(setup: Dictionary)
signal back_requested()
signal setup_changed()
signal last_valid_changed()

# Disclosure sections are presentation state only. They are rebuilt from the
# model on every `configure()` and never enter the canonical session setup, the
# persisted setup document, or any deterministic payload.
const SECTION_BOARD := SetupFieldSpecScript.SECTION_BOARD
const SECTION_ADVANCED := SetupFieldSpecScript.SECTION_ADVANCED
const SECTION_CONTROLS := SetupFieldSpecScript.SECTION_CONTROLS

const SECTION_TITLES := {
	SECTION_BOARD: "Customize Board",
	SECTION_ADVANCED: "Advanced Game",
	SECTION_CONTROLS: "Controls",
}

var _model
var _title: Label
var _scroll: ScrollContainer
var _board_selector: OptionButton
var _axis_inputs: Array[LineEdit] = []
var _validation_label: Label
var _piece_selector: OptionButton
var _piece_description: Label
var _random_selector: OptionButton
var _random_description: Label
var _seed_row: Control
var _seed_input: LineEdit
var _seed_error: Label
var _speed_selector: OptionButton
var _controls_section: VBoxContainer
var _translation_frame_selector: OptionButton
var _rotation_frame_selector: OptionButton
var _start_button: Button
var _reveal_button: Button
var _focus_controls: Array[Control] = []
var _refreshing := false
var _expanded := {}
var _section_buttons := {}
var _section_bodies := {}
# Mode applicability and conditional visibility come from the declared taxonomy
# rather than a second copy of the same rules in this panel.
var _seed_spec


func configure(model) -> void:
	_model = model
	_rebuild()


func _ready() -> void:
	if _model != null:
		_rebuild()


func _rebuild() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
	_clear_build_state()
	_scroll = ScrollContainer.new()
	_scroll.name = "SetupScroll"
	_scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(_scroll)
	var center := CenterContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(720, 0)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(panel)
	var margin := MarginContainer.new()
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, ShellDesignTokensScript.SPACE_5)
	panel.add_child(margin)
	var layout := VBoxContainer.new()
	layout.name = "SetupLayout"
	layout.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_3)
	margin.add_child(layout)
	_title = Label.new()
	_title.text = GameSetupSpecScript.mode_label(_model.current_mode)
	_title.theme_type_variation = "AccentLabel"
	_title.add_theme_font_size_override("font_size", ShellDesignTokensScript.FONT_SCREEN_TITLE)
	layout.add_child(_title)
	var prompt := Label.new()
	prompt.text = "Choose a bounded board. Changes prepare the next game; a running game keeps its frozen setup."
	prompt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	layout.add_child(prompt)

	_build_board_group(layout)
	_build_piece_group(layout)
	_build_speed_group(layout)
	_build_advanced_section(layout)
	_build_controls_section(layout)
	_build_actions(layout)

	_refresh_from_model()
	_board_selector.call_deferred("grab_focus")


func _clear_build_state() -> void:
	_focus_controls.clear()
	_axis_inputs.clear()
	_expanded.clear()
	_section_buttons.clear()
	_section_bodies.clear()
	_title = null
	_scroll = null
	_board_selector = null
	_validation_label = null
	_piece_selector = null
	_piece_description = null
	_random_selector = null
	_random_description = null
	_seed_row = null
	_seed_input = null
	_seed_error = null
	_speed_selector = null
	_controls_section = null
	_translation_frame_selector = null
	_rotation_frame_selector = null
	_start_button = null
	_reveal_button = null
	_seed_spec = null


func first_focus_control() -> Control:
	return _board_selector


# --- Ordinary game definition -------------------------------------------------


func _build_board_group(layout: VBoxContainer) -> void:
	var header := Label.new()
	header.name = "BoardGroupHeader"
	header.text = "Board"
	header.theme_type_variation = "AccentLabel"
	layout.add_child(header)
	_board_selector = _add_selector(layout, "Preset Shortcut")
	for spec in GameSetupSpecScript.presets_for_mode(_model.current_mode):
		_board_selector.add_item("%s · %s" % [
			str(spec.get("label", "")),
			GameSetupSpecScript.format_shape(spec.get("shape", [])),
		])
		_board_selector.set_item_metadata(_board_selector.item_count - 1, str(spec.get("id", "")))
	_board_selector.add_item("Custom · editable dimensions")
	_board_selector.set_item_metadata(_board_selector.item_count - 1, "")
	_board_selector.item_selected.connect(_on_board_selected)
	_board_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_board_selector, event))

	var body := _add_disclosure_section(layout, SECTION_BOARD)
	for axis_index in range(GameSetupSpecScript.board_axis_ranges(_model.current_mode).size()):
		_add_axis_editor(_container_for("board_axis_%d" % axis_index, layout), axis_index)
	var reset_sizes := Button.new()
	reset_sizes.name = "ResetSizesButton"
	reset_sizes.text = "Reset Sizes"
	reset_sizes.tooltip_text = "Restore the canonical dimensions without changing any other setup choice"
	reset_sizes.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	reset_sizes.pressed.connect(_on_reset_sizes_pressed)
	body.add_child(reset_sizes)
	_register_focus_control(reset_sizes)

	# The validation summary stays in the ordinary surface so a failure inside a
	# collapsed section is never silent.
	_validation_label = Label.new()
	_validation_label.name = "BoardValidationLabel"
	_validation_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	layout.add_child(_validation_label)
	# `Start Game` is disabled while the setup is invalid and a disabled Godot
	# button emits no `pressed`, so the reveal path needs its own enabled,
	# focusable control. It appears only alongside a failure.
	_reveal_button = Button.new()
	_reveal_button.name = "RevealProblemButton"
	_reveal_button.text = "Show Problem"
	_reveal_button.tooltip_text = "Open the section holding the first setup problem and focus that field"
	_reveal_button.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_reveal_button.pressed.connect(_reveal_first_blocking_field)
	layout.add_child(_reveal_button)
	_register_focus_control(_reveal_button)


func _build_piece_group(layout: VBoxContainer) -> void:
	if not _field_applies("piece_set"):
		return
	var group := VBoxContainer.new()
	group.name = "PieceSetGroup"
	group.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_1)
	layout.add_child(group)
	_piece_selector = _add_selector(group, "Piece Set")
	_piece_selector.item_selected.connect(_on_piece_selected)
	_piece_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_piece_selector, event))
	_piece_description = _add_description(group)


func _build_speed_group(layout: VBoxContainer) -> void:
	_speed_selector = _add_selector(layout, "Starting Speed")
	for speed in GameSetupSpecScript.speed_levels():
		_speed_selector.add_item(str(int(speed)))
		_speed_selector.set_item_metadata(_speed_selector.item_count - 1, int(speed))
	_speed_selector.item_selected.connect(_on_speed_selected)
	_speed_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_speed_selector, event))
	var speed_note := _add_description(layout)
	speed_note.text = "1 is relaxed; 10 is the fastest starting gravity cadence."


# --- Secondary disclosure -----------------------------------------------------


func _build_advanced_section(layout: VBoxContainer) -> void:
	_seed_spec = _spec_for_field("seed")
	_add_disclosure_section(layout, SECTION_ADVANCED)
	var body := _container_for("random_mode", layout)
	_random_selector = _add_selector(body, "Randomness")
	for spec in GameSetupSpecScript.random_modes():
		_random_selector.add_item(str(spec.get("label", "")))
		_random_selector.set_item_metadata(_random_selector.item_count - 1, str(spec.get("id", "")))
	_random_selector.item_selected.connect(_on_random_selected)
	_random_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_random_selector, event))
	_random_description = _add_description(body)

	_seed_row = VBoxContainer.new()
	_seed_row.name = "SeedRow"
	(_seed_row as VBoxContainer).add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_1)
	_container_for("seed", layout).add_child(_seed_row)
	var seed_label := Label.new()
	seed_label.text = "Seed"
	seed_label.theme_type_variation = "SecondaryLabel"
	_seed_row.add_child(seed_label)
	_seed_input = LineEdit.new()
	_seed_input.name = "SeedInput"
	_seed_input.placeholder_text = "%d–%d" % [GameSetupSpecScript.MIN_SEED, GameSetupSpecScript.MAX_SEED]
	_seed_input.max_length = 9
	_seed_input.text_changed.connect(_on_seed_changed)
	_seed_row.add_child(_seed_input)
	_register_focus_control(_seed_input)
	_seed_error = Label.new()
	_seed_error.name = "SeedError"
	_seed_error.theme_type_variation = "StatusErrorLabel"
	_seed_error.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_seed_row.add_child(_seed_error)


func _build_controls_section(layout: VBoxContainer) -> void:
	if not _field_applies("translation_frame"):
		return
	_add_disclosure_section(layout, SECTION_CONTROLS)
	_controls_section = _container_for("translation_frame", layout)
	_translation_frame_selector = _add_selector(_controls_section, "Translation")
	_rotation_frame_selector = _add_selector(_container_for("rotation_frame", layout), "Rotation")
	for selector in [_translation_frame_selector, _rotation_frame_selector]:
		selector.add_item("Relative")
		selector.set_item_metadata(0, "relative")
		selector.add_item("Absolute")
		selector.set_item_metadata(1, "absolute")
	_translation_frame_selector.item_selected.connect(func(index: int) -> void: _on_control_frame_selected("translation_frame", _translation_frame_selector, index))
	_rotation_frame_selector.item_selected.connect(func(index: int) -> void: _on_control_frame_selected("rotation_frame", _rotation_frame_selector, index))
	var controls_note := _add_description(_controls_section)
	controls_note.text = "Relative controls follow the current view; Absolute controls use canonical axes and planes."


func _build_actions(layout: VBoxContainer) -> void:
	_start_button = Button.new()
	_start_button.name = "StartGameButton"
	_start_button.text = "Start Game"
	_start_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_start_button.custom_minimum_size = Vector2(0, 44)
	_start_button.add_theme_font_size_override("font_size", ShellDesignTokensScript.FONT_BODY)
	# Reuse the shell's established primary-action treatment rather than
	# inventing setup-local emphasis.
	_start_button.set_meta("semantic_role", "action_button")
	_start_button.pressed.connect(_on_start_pressed)
	layout.add_child(_start_button)
	_register_focus_control(_start_button)

	var secondary := HBoxContainer.new()
	secondary.name = "SecondaryActions"
	secondary.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_2)
	layout.add_child(secondary)
	var reset_setup := Button.new()
	reset_setup.name = "ResetSetupButton"
	reset_setup.text = "Reset Setup"
	reset_setup.tooltip_text = "Restore every default for this mode"
	reset_setup.pressed.connect(_on_reset_setup_pressed)
	secondary.add_child(reset_setup)
	_register_focus_control(reset_setup)
	var back := Button.new()
	back.name = "BackButton"
	back.text = "Back"
	back.pressed.connect(func() -> void: back_requested.emit())
	secondary.add_child(back)
	_register_focus_control(back)


# --- Disclosure ---------------------------------------------------------------


func _add_disclosure_section(layout: VBoxContainer, section_id: String) -> VBoxContainer:
	var button := Button.new()
	button.name = "Disclosure__%s" % section_id
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.pressed.connect(func() -> void: toggle_section(section_id))
	layout.add_child(button)
	_register_focus_control(button)
	var body := VBoxContainer.new()
	body.name = "Section__%s" % section_id
	body.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_2)
	layout.add_child(body)
	_section_buttons[section_id] = button
	_section_bodies[section_id] = body
	_expanded[section_id] = false
	_apply_section_state(section_id)
	return body


func disclosure_section_ids() -> Array:
	var ids: Array = []
	for section_id in [SECTION_BOARD, SECTION_ADVANCED, SECTION_CONTROLS]:
		if _section_bodies.has(section_id):
			ids.append(section_id)
	return ids


func is_section_expanded(section_id: String) -> bool:
	return bool(_expanded.get(section_id, false))


func toggle_section(section_id: String) -> void:
	set_section_expanded(section_id, not is_section_expanded(section_id))


func set_section_expanded(section_id: String, expanded: bool) -> void:
	if not _section_bodies.has(section_id):
		return
	var collapsing := is_section_expanded(section_id) and not expanded
	var focus_was_inside := collapsing and _focus_is_inside_section(section_id)
	_expanded[section_id] = expanded
	_apply_section_state(section_id)
	if _validation_label != null:
		_refresh_validation_state()
	_configure_focus()
	var button := _section_buttons[section_id] as Button
	if focus_was_inside:
		button.grab_focus()
	elif expanded:
		_ensure_visible(button)


func _apply_section_state(section_id: String) -> void:
	var expanded := is_section_expanded(section_id)
	var body := _section_bodies.get(section_id) as Control
	if body != null:
		body.visible = expanded
	var button := _section_buttons.get(section_id) as Button
	if button != null:
		var title := str(SECTION_TITLES.get(section_id, section_id))
		button.text = "%s  %s" % ["▾" if expanded else "▸", title]
		button.tooltip_text = "%s %s" % ["Hide" if expanded else "Show", title]


func _focus_is_inside_section(section_id: String) -> bool:
	var body := _section_bodies.get(section_id) as Control
	if body == null or not is_inside_tree():
		return false
	var viewport := get_viewport()
	if viewport == null:
		return false
	var focused := viewport.gui_get_focus_owner()
	return focused != null and body.is_ancestor_of(focused)


# --- Control construction -----------------------------------------------------


# Placement comes from the declared section, so moving a field between the
# ordinary path and a disclosure is a registry edit rather than a panel edit.
func _container_for(field_id: String, layout: VBoxContainer) -> VBoxContainer:
	var section := SetupFieldRegistryScript.section_for_field(_model.current_mode, field_id)
	if section == SetupFieldSpecScript.SECTION_ORDINARY or not _section_bodies.has(section):
		return layout
	return _section_bodies[section] as VBoxContainer


func _spec_for_field(field_id: String):
	for spec in SetupFieldRegistryScript.specs_for_mode(_model.current_mode):
		if spec.id() == field_id:
			return spec
	return null


func _field_applies(field_id: String) -> bool:
	return _spec_for_field(field_id) != null


func _add_selector(layout: VBoxContainer, label_text: String) -> OptionButton:
	var label := Label.new()
	label.text = label_text
	label.theme_type_variation = "SecondaryLabel"
	layout.add_child(label)
	var selector := OptionButton.new()
	selector.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.add_child(selector)
	_register_focus_control(selector)
	return selector


func _add_axis_editor(layout: VBoxContainer, axis_index: int) -> void:
	var ranges: Array = GameSetupSpecScript.board_axis_ranges(_model.current_mode)
	var axis_range: Array = ranges[axis_index] as Array
	var axis_order: Array = (GameSetupSpecScript.BoardExtentContractScript.mode_spec(_model.current_mode).get("axis_order", []) as Array)
	var axis_name := str(axis_order[axis_index]) if axis_index < axis_order.size() else str(axis_index)
	var row := HBoxContainer.new()
	row.name = "Axis%sRow" % axis_name
	row.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_2)
	layout.add_child(row)
	var label := Label.new()
	label.text = "%s  %d–%d" % [axis_name, int(axis_range[0]), int(axis_range[1])]
	label.custom_minimum_size = Vector2(132, 0)
	row.add_child(label)
	var decrement := Button.new()
	decrement.name = "Axis%sDecrement" % axis_name
	decrement.text = "−"
	decrement.tooltip_text = "Decrease %s by one" % axis_name
	decrement.pressed.connect(func() -> void: _on_axis_adjusted(axis_index, -1))
	row.add_child(decrement)
	var input := LineEdit.new()
	input.name = "Axis%sInput" % axis_name
	input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	input.placeholder_text = "integer"
	input.text_changed.connect(func(text: String) -> void: _on_axis_text_changed(axis_index, text))
	row.add_child(input)
	var increment := Button.new()
	increment.name = "Axis%sIncrement" % axis_name
	increment.text = "+"
	increment.tooltip_text = "Increase %s by one" % axis_name
	increment.pressed.connect(func() -> void: _on_axis_adjusted(axis_index, 1))
	row.add_child(increment)
	_axis_inputs.append(input)
	for control in [decrement, input, increment]:
		_register_focus_control(control)


func _add_description(layout: VBoxContainer) -> Label:
	var description := Label.new()
	description.theme_type_variation = "DimLabel"
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	layout.add_child(description)
	return description


# --- Model synchronisation ----------------------------------------------------


func _refresh_from_model() -> void:
	_refreshing = true
	_select_metadata(_board_selector, _model.selected_preset_id())
	_rebuild_piece_options()
	_select_metadata(_random_selector, _model.selected_random_mode())
	for axis_index in range(_axis_inputs.size()):
		_axis_inputs[axis_index].text = _model.selected_axis_text(axis_index)
	_seed_input.text = str(_model.selected_seed())
	_select_metadata(_speed_selector, _model.selected_speed_level())
	if _controls_section != null:
		var frames: Dictionary = _model.selected_control_frames()
		_select_metadata(_translation_frame_selector, frames.get("translation_frame", "relative"))
		_select_metadata(_rotation_frame_selector, frames.get("rotation_frame", "relative"))
	var random_spec := _spec_by_id(GameSetupSpecScript.random_modes(), _model.selected_random_mode())
	_random_description.text = str(random_spec.get("description", ""))
	_seed_row.visible = _seed_spec != null and _seed_spec.is_visible_for(
		_model.current_mode, {"random_mode": _model.selected_random_mode()}
	)
	# A board that matches no named preset must be immediately legible rather
	# than hidden behind another discovery step.
	_expanded[SECTION_BOARD] = is_section_expanded(SECTION_BOARD) or _model.selected_preset_id().is_empty()
	_apply_section_state(SECTION_BOARD)
	_refreshing = false
	_validate_seed_text()
	_refresh_validation_state()
	_configure_focus()


func _rebuild_piece_options() -> void:
	if _piece_selector == null:
		return
	_piece_selector.clear()
	for spec in GameSetupSpecScript.piece_sets_for_mode(_model.current_mode):
		_piece_selector.add_item(str(spec.get("label", "")))
		_piece_selector.set_item_metadata(_piece_selector.item_count - 1, str(spec.get("id", "")))
	_select_metadata(_piece_selector, _model.selected_piece_set_id())
	var piece_spec := GameSetupSpecScript.piece_set(_model.current_mode, _model.selected_piece_set_id())
	_piece_description.text = str(piece_spec.get("description", ""))


func _on_board_selected(index: int) -> void:
	var preset_id := str(_board_selector.get_item_metadata(index))
	if preset_id.is_empty():
		# `Custom` is an information-architecture affordance: it exposes the
		# dimension editors and leaves the current shape untouched.
		set_section_expanded(SECTION_BOARD, true)
		if not _axis_inputs.is_empty():
			_axis_inputs[0].grab_focus()
		return
	if _model.select_preset(preset_id):
		_refresh_from_model()
		_emit_changed()


func _on_axis_text_changed(axis_index: int, text: String) -> void:
	if _refreshing:
		return
	if _model.set_axis_text(axis_index, text):
		_select_metadata(_board_selector, _model.selected_preset_id())
		_refresh_validation_state()
		_emit_changed()


func _on_axis_adjusted(axis_index: int, delta: int) -> void:
	if _model.adjust_axis(axis_index, delta):
		_refresh_from_model()
		_emit_changed()


func _on_piece_selected(index: int) -> void:
	if _model.select_piece_set(str(_piece_selector.get_item_metadata(index))):
		var spec := GameSetupSpecScript.piece_set(_model.current_mode, _model.selected_piece_set_id())
		_piece_description.text = str(spec.get("description", ""))
		_refresh_validation_state()
		_emit_changed()


func _on_random_selected(index: int) -> void:
	if _model.select_random_mode(str(_random_selector.get_item_metadata(index))):
		_refresh_from_model()
		_emit_changed()


func _on_seed_changed(_text: String) -> void:
	if _refreshing:
		return
	if _validate_seed_text():
		_model.select_seed(int(_seed_input.text))
	_refresh_validation_state()
	_emit_changed()


func _on_speed_selected(index: int) -> void:
	if _model.select_speed_level(_speed_selector.get_item_metadata(index)):
		_refresh_validation_state()
		_emit_changed()


func _on_control_frame_selected(kind: String, selector: OptionButton, index: int) -> void:
	if _refreshing:
		return
	if _model.select_control_frame(kind, str(selector.get_item_metadata(index))):
		_emit_changed()


func _on_start_pressed() -> void:
	if _validate_seed_text() and _model.validate_current_draft():
		start_requested.emit(_model.canonical_session_setup().duplicate(true))
	else:
		_refresh_validation_state()
		_reveal_first_blocking_field()


func reveal_problem_control() -> Button:
	return _reveal_button


func _on_reset_sizes_pressed() -> void:
	_model.reset_sizes()
	_refresh_from_model()
	_emit_changed()


func _on_reset_setup_pressed() -> void:
	_model.reset_to_standard()
	_refresh_from_model()
	_emit_changed()


func _emit_changed() -> void:
	_start_button.disabled = not _model.is_current_valid() or not _seed_error.text.is_empty()
	setup_changed.emit()
	if _model.is_current_valid() and _seed_error.text.is_empty():
		last_valid_changed.emit()


# --- Validation ---------------------------------------------------------------


func _refresh_validation_state() -> void:
	var errors: Array = _blocking_errors()
	if errors.is_empty():
		_validation_label.theme_type_variation = "StatusAccentLabel"
		_validation_label.text = "Dimensions accepted by the native board-extent contract."
	else:
		_validation_label.theme_type_variation = "StatusErrorLabel"
		_validation_label.text = "Not launchable: %s" % _format_validation_errors(errors)
	# A failure is always visible. The all-clear confirmation is feedback for
	# dimension editing, so it stays out of the ordinary path.
	_validation_label.visible = not errors.is_empty() or is_section_expanded(SECTION_BOARD)
	if _reveal_button != null:
		_reveal_button.visible = not errors.is_empty()
	for axis_index in range(_axis_inputs.size()):
		var path := "$.board_shape[%d]" % axis_index
		var has_axis_error := false
		for detail in errors:
			if str((detail as Dictionary).get("path", "")) == path:
				has_axis_error = true
				break
		_axis_inputs[axis_index].modulate = Color(1.0, 0.68, 0.68) if has_axis_error else Color.WHITE
	_start_button.disabled = not _model.is_current_valid() or not _seed_error.text.is_empty()
	# Showing or hiding the reveal action changes the focus ring.
	_configure_focus()


# Seed text that never reached the model would otherwise disable Start with no
# entry in the summary, so it is folded in here.
func _blocking_errors() -> Array:
	var errors: Array = _model.validation_errors()
	if _seed_error == null or _seed_error.text.is_empty():
		return errors
	for detail in errors:
		if str((detail as Dictionary).get("path", "")) == "$.seed":
			return errors
	errors.append({"code": "invalid_seed", "path": "$.seed"})
	return errors


func _format_validation_errors(errors: Array) -> String:
	var rows: Array = []
	for detail in errors:
		var value := detail as Dictionary
		rows.append("%s @ %s" % [str(value.get("code", "validation_error")), str(value.get("path", "$"))])
	return " · ".join(rows)


# A blocked setup must never leave the responsible field hidden.
func _reveal_first_blocking_field() -> void:
	for detail in _blocking_errors():
		var path := str((detail as Dictionary).get("path", ""))
		var section := _section_for_error_path(path)
		if not section.is_empty():
			set_section_expanded(section, true)
		var control := _control_for_error_path(path)
		if control != null and _is_revealed(control):
			control.grab_focus()
			return


func _section_for_error_path(path: String) -> String:
	if path.begins_with("$.board_shape"):
		return SECTION_BOARD
	if path == "$.seed" or path == "$.random_mode":
		return SECTION_ADVANCED
	return ""


func _control_for_error_path(path: String) -> Control:
	if path.begins_with("$.board_shape["):
		var axis_index := int(path.trim_prefix("$.board_shape[").trim_suffix("]"))
		if axis_index >= 0 and axis_index < _axis_inputs.size():
			return _axis_inputs[axis_index]
		return _axis_inputs[0] if not _axis_inputs.is_empty() else null
	match path:
		"$.seed":
			return _seed_input
		"$.random_mode":
			return _random_selector
		"$.piece_set_id":
			return _piece_selector
		"$.initial_speed_level":
			return _speed_selector
	return null


# tet4d-semantic-boundary: allow adapter-routing
func _validate_seed_text() -> bool:
	if _model.selected_random_mode() == GameSetupSpecScript.RANDOM_MODE_TRUE_RANDOM:
		_seed_error.text = ""
		return true
	var text := _seed_input.text.strip_edges()
	if text.is_empty() or not text.is_valid_int():
		_seed_error.text = "invalid_seed @ $.seed"
		return false
	var value := int(text)
	if not GameSetupSpecScript.is_valid_seed(value):
		_seed_error.text = "invalid_seed @ $.seed"
		return false
	_seed_error.text = ""
	return true


func _select_metadata(selector: OptionButton, value) -> void:
	if selector == null:
		return
	for index in range(selector.item_count):
		if selector.get_item_metadata(index) == value:
			selector.select(index)
			return


func _spec_by_id(specs: Array, value: String) -> Dictionary:
	for spec in specs:
		if str(spec.get("id", "")) == value:
			return spec
	return {}


# --- Focus and scrolling ------------------------------------------------------


func _register_focus_control(control: Control) -> void:
	_focus_controls.append(control)
	control.focus_entered.connect(func() -> void: _ensure_visible(control))


# Visibility is resolved against the panel's own subtree so focus stays correct
# while the setup screen is built off-screen in the shell's screen stack.
func _is_revealed(control: Control) -> bool:
	if not is_instance_valid(control):
		return false
	var node: Node = control
	while node != null and node != self:
		if node is CanvasItem and not (node as CanvasItem).visible:
			return false
		node = node.get_parent()
	return node == self


func visible_focus_controls() -> Array:
	var controls: Array = []
	for control in _focus_controls:
		if _is_revealed(control):
			controls.append(control)
	return controls


func hidden_focus_controls() -> Array:
	var controls: Array = []
	for control in _focus_controls:
		if is_instance_valid(control) and not _is_revealed(control):
			controls.append(control)
	return controls


func _configure_focus() -> void:
	var visible_controls: Array[Control] = []
	for control in _focus_controls:
		if not is_instance_valid(control):
			continue
		if _is_revealed(control):
			control.focus_mode = Control.FOCUS_ALL
			visible_controls.append(control)
		else:
			control.focus_mode = Control.FOCUS_NONE
	for index in range(visible_controls.size()):
		var control := visible_controls[index]
		control.focus_neighbor_top = control.get_path_to(visible_controls[(index - 1 + visible_controls.size()) % visible_controls.size()])
		control.focus_neighbor_bottom = control.get_path_to(visible_controls[(index + 1) % visible_controls.size()])


func _ensure_visible(control: Control) -> void:
	if _scroll == null or not is_instance_valid(control) or not control.is_inside_tree():
		return
	_scroll.ensure_control_visible(control)


func _on_selector_gui_input(selector: OptionButton, event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	var key := event as InputEventKey
	if key.keycode != KEY_LEFT and key.keycode != KEY_RIGHT:
		return
	var delta := -1 if key.keycode == KEY_LEFT else 1
	var index := posmod(selector.selected + delta, selector.item_count)
	selector.select(index)
	if selector == _board_selector:
		_on_board_selected(index)
	elif selector == _piece_selector:
		_on_piece_selected(index)
	elif selector == _random_selector:
		_on_random_selected(index)
	elif selector == _speed_selector:
		_on_speed_selected(index)
	accept_event()
