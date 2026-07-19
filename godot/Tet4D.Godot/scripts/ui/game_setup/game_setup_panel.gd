extends Control

class_name GameSetupPanel

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")

signal start_requested(setup: Dictionary)
signal back_requested()
signal setup_changed()

var _model
var _title: Label
var _board_selector: OptionButton
var _piece_selector: OptionButton
var _piece_description: Label
var _random_selector: OptionButton
var _random_description: Label
var _seed_row: Control
var _seed_input: LineEdit
var _seed_error: Label
var _speed_selector: OptionButton
var _start_button: Button
var _focus_controls: Array[Control] = []


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
	_focus_controls.clear()
	var scroll := ScrollContainer.new()
	scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	var center := CenterContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(720, 0)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(panel)
	var margin := MarginContainer.new()
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 30)
	panel.add_child(margin)
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 12)
	margin.add_child(layout)
	_title = Label.new()
	_title.text = GameSetupSpecScript.mode_label(_model.current_mode)
	_title.theme_type_variation = "AccentLabel"
	_title.add_theme_font_size_override("font_size", 30)
	layout.add_child(_title)
	var prompt := Label.new()
	prompt.text = "Choose the bounded game setup. These values are fixed for the session."
	prompt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	layout.add_child(prompt)

	_board_selector = _add_selector(layout, "Board Size")
	for spec in GameSetupSpecScript.presets_for_mode(_model.current_mode):
		_board_selector.add_item("%s · %s" % [
			str(spec.get("label", "")),
			GameSetupSpecScript.format_shape(spec.get("shape", [])),
		])
		_board_selector.set_item_metadata(_board_selector.item_count - 1, str(spec.get("id", "")))
	_board_selector.item_selected.connect(_on_board_selected)
	_board_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_board_selector, event))

	_piece_selector = _add_selector(layout, "Piece Set")
	_piece_selector.item_selected.connect(_on_piece_selected)
	_piece_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_piece_selector, event))
	_piece_description = _add_description(layout)

	_random_selector = _add_selector(layout, "Randomness")
	for spec in GameSetupSpecScript.random_modes():
		_random_selector.add_item(str(spec.get("label", "")))
		_random_selector.set_item_metadata(_random_selector.item_count - 1, str(spec.get("id", "")))
	_random_selector.item_selected.connect(_on_random_selected)
	_random_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_random_selector, event))
	_random_description = _add_description(layout)

	_seed_row = VBoxContainer.new()
	(_seed_row as VBoxContainer).add_theme_constant_override("separation", 4)
	layout.add_child(_seed_row)
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
	_seed_error = Label.new()
	_seed_error.theme_type_variation = "StatusErrorLabel"
	_seed_error.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_seed_row.add_child(_seed_error)

	_speed_selector = _add_selector(layout, "Starting Speed")
	for speed in GameSetupSpecScript.speed_levels():
		_speed_selector.add_item(str(int(speed)))
		_speed_selector.set_item_metadata(_speed_selector.item_count - 1, int(speed))
	_speed_selector.item_selected.connect(_on_speed_selected)
	_speed_selector.gui_input.connect(func(event: InputEvent) -> void: _on_selector_gui_input(_speed_selector, event))
	var speed_note := _add_description(layout)
	speed_note.text = "1 is relaxed; 10 is the fastest starting gravity cadence."

	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 12)
	layout.add_child(actions)
	_start_button = Button.new()
	_start_button.name = "StartGameButton"
	_start_button.text = "Start Game"
	_start_button.pressed.connect(_on_start_pressed)
	actions.add_child(_start_button)
	var reset := Button.new()
	reset.name = "ResetSetupButton"
	reset.text = "Reset to Standard"
	reset.pressed.connect(_on_reset_pressed)
	actions.add_child(reset)
	var back := Button.new()
	back.name = "BackButton"
	back.text = "Back"
	back.pressed.connect(func() -> void: back_requested.emit())
	actions.add_child(back)

	_focus_controls = [
		_board_selector,
		_piece_selector,
		_random_selector,
		_seed_input,
		_speed_selector,
		_start_button,
		reset,
		back,
	]
	_configure_focus()
	_refresh_from_model()
	_configure_focus()
	_board_selector.call_deferred("grab_focus")


func first_focus_control() -> Control:
	return _board_selector


func _add_selector(layout: VBoxContainer, label_text: String) -> OptionButton:
	var label := Label.new()
	label.text = label_text
	label.theme_type_variation = "SecondaryLabel"
	layout.add_child(label)
	var selector := OptionButton.new()
	selector.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.add_child(selector)
	return selector


func _add_description(layout: VBoxContainer) -> Label:
	var description := Label.new()
	description.theme_type_variation = "DimLabel"
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	layout.add_child(description)
	return description


func _refresh_from_model() -> void:
	_select_metadata(_board_selector, _model.selected_preset_id())
	_rebuild_piece_options()
	_select_metadata(_random_selector, _model.selected_random_mode())
	_seed_input.text = str(_model.selected_seed())
	_select_metadata(_speed_selector, _model.selected_speed_level())
	var random_spec := _spec_by_id(GameSetupSpecScript.random_modes(), _model.selected_random_mode())
	_random_description.text = str(random_spec.get("description", ""))
	_seed_row.visible = _model.selected_random_mode() == GameSetupSpecScript.RANDOM_MODE_FIXED_SEED
	_validate_seed_text()
	_start_button.disabled = not _model.is_current_valid() or not _seed_error.text.is_empty()


func _rebuild_piece_options() -> void:
	_piece_selector.clear()
	for spec in GameSetupSpecScript.piece_sets_for_mode(_model.current_mode, _model.selected_preset_id()):
		_piece_selector.add_item(str(spec.get("label", "")))
		_piece_selector.set_item_metadata(_piece_selector.item_count - 1, str(spec.get("id", "")))
	_select_metadata(_piece_selector, _model.selected_piece_set_id())
	var piece_spec := GameSetupSpecScript.piece_set(_model.current_mode, _model.selected_piece_set_id())
	_piece_description.text = str(piece_spec.get("description", ""))


func _on_board_selected(index: int) -> void:
	if _model.select_preset(str(_board_selector.get_item_metadata(index))):
		_rebuild_piece_options()
		_emit_changed()


func _on_piece_selected(index: int) -> void:
	if _model.select_piece_set(str(_piece_selector.get_item_metadata(index))):
		var spec := GameSetupSpecScript.piece_set(_model.current_mode, _model.selected_piece_set_id())
		_piece_description.text = str(spec.get("description", ""))
		_emit_changed()


func _on_random_selected(index: int) -> void:
	if _model.select_random_mode(str(_random_selector.get_item_metadata(index))):
		_refresh_from_model()
		_emit_changed()


func _on_seed_changed(_text: String) -> void:
	if _validate_seed_text():
		_model.select_seed(int(_seed_input.text))
	_emit_changed()


func _on_speed_selected(index: int) -> void:
	if _model.select_speed_level(_speed_selector.get_item_metadata(index)):
		_emit_changed()


func _on_start_pressed() -> void:
	if _validate_seed_text() and _model.is_current_valid():
		start_requested.emit(_model.canonical_session_setup().duplicate(true))


func _on_reset_pressed() -> void:
	_model.reset_to_standard()
	_refresh_from_model()
	setup_changed.emit()


func _emit_changed() -> void:
	_start_button.disabled = not _model.is_current_valid() or not _seed_error.text.is_empty()
	setup_changed.emit()


# tet4d-semantic-boundary: allow adapter-routing
func _validate_seed_text() -> bool:
	if _model.selected_random_mode() == GameSetupSpecScript.RANDOM_MODE_TRUE_RANDOM:
		_seed_error.text = ""
		return true
	var text := _seed_input.text.strip_edges()
	if text.is_empty() or not text.is_valid_int():
		_seed_error.text = "Enter a whole number from %d to %d." % [GameSetupSpecScript.MIN_SEED, GameSetupSpecScript.MAX_SEED]
		return false
	var value := int(text)
	if not GameSetupSpecScript.is_valid_seed(value):
		_seed_error.text = "Seed must be from %d to %d." % [GameSetupSpecScript.MIN_SEED, GameSetupSpecScript.MAX_SEED]
		return false
	_seed_error.text = ""
	return true


func _select_metadata(selector: OptionButton, value) -> void:
	for index in range(selector.item_count):
		if selector.get_item_metadata(index) == value:
			selector.select(index)
			return


func _spec_by_id(specs: Array, value: String) -> Dictionary:
	for spec in specs:
		if str(spec.get("id", "")) == value:
			return spec
	return {}


func _configure_focus() -> void:
	var visible_controls: Array[Control] = []
	for control in _focus_controls:
		if control == _seed_input and not _seed_row.visible:
			continue
		visible_controls.append(control)
	for index in range(visible_controls.size()):
		var control := visible_controls[index]
		control.focus_neighbor_top = control.get_path_to(visible_controls[(index - 1 + visible_controls.size()) % visible_controls.size()])
		control.focus_neighbor_bottom = control.get_path_to(visible_controls[(index + 1) % visible_controls.size()])


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
