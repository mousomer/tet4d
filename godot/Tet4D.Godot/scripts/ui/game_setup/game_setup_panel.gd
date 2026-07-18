extends Control

class_name GameSetupPanel

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")

signal start_requested(mode: String, board_shape: Array)
signal back_requested()
signal preset_selected(preset_id: String)

var _model
var _title: Label
var _shape_label: Label
var _description_label: Label
var _preset_buttons: Array[Button] = []
var _preset_ids: Array[String] = []


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
	_preset_buttons.clear()
	_preset_ids.clear()
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(720, 520)
	center.add_child(panel)
	var margin := MarginContainer.new()
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 36)
	panel.add_child(margin)
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 16)
	margin.add_child(layout)
	_title = Label.new()
	_title.text = GameSetupSpecScript.mode_label(_model.current_mode)
	_title.theme_type_variation = "AccentLabel"
	_title.add_theme_font_size_override("font_size", 30)
	layout.add_child(_title)
	var prompt := Label.new()
	prompt.text = "Board Size · choose a supported preset before constructing the native session"
	prompt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	layout.add_child(prompt)
	var group := VBoxContainer.new()
	group.add_theme_constant_override("separation", 10)
	layout.add_child(group)
	for spec in GameSetupSpecScript.presets_for_mode(_model.current_mode):
		var preset_id := str(spec.get("id", ""))
		var button := Button.new()
		button.name = "Preset_%s" % preset_id
		button.text = "%s    %s" % [str(spec.get("label", preset_id)), GameSetupSpecScript.format_shape(spec.get("shape", []))]
		button.toggle_mode = true
		button.pressed.connect(func() -> void:
			_select(preset_id)
		)
		group.add_child(button)
		_preset_buttons.append(button)
		_preset_ids.append(preset_id)
	_shape_label = Label.new()
	_shape_label.theme_type_variation = "AccentLabel"
	_shape_label.add_theme_font_size_override("font_size", 22)
	layout.add_child(_shape_label)
	_description_label = Label.new()
	_description_label.theme_type_variation = "SecondaryLabel"
	layout.add_child(_description_label)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 12)
	layout.add_child(actions)
	var start := Button.new()
	start.name = "StartGameButton"
	start.text = "Start Game"
	start.pressed.connect(func() -> void:
		start_requested.emit(_model.current_mode, _model.selected_shape())
	)
	actions.add_child(start)
	var back := Button.new()
	back.name = "BackButton"
	back.text = "Back"
	back.pressed.connect(func() -> void: back_requested.emit())
	actions.add_child(back)
	var focus_controls: Array[Control] = []
	focus_controls.append_array(_preset_buttons)
	focus_controls.append(start)
	focus_controls.append(back)
	for index in range(focus_controls.size()):
		var control := focus_controls[index]
		control.focus_neighbor_top = control.get_path_to(focus_controls[(index - 1 + focus_controls.size()) % focus_controls.size()])
		control.focus_neighbor_bottom = control.get_path_to(focus_controls[(index + 1) % focus_controls.size()])
	_refresh_selection()
	if not _preset_buttons.is_empty():
		_preset_buttons[_selected_index()].call_deferred("grab_focus")


func first_focus_control() -> Control:
	return _preset_buttons[_selected_index()] if not _preset_buttons.is_empty() else null


func _select(preset_id: String) -> void:
	if _model.select_preset(preset_id):
		preset_selected.emit(preset_id)
		_refresh_selection()


func _refresh_selection() -> void:
	var selected_id: String = _model.selected_preset_id()
	for index in range(_preset_buttons.size()):
		_preset_buttons[index].button_pressed = _preset_ids[index] == selected_id
	var spec: Dictionary = _model.selected_spec()
	_shape_label.text = "Selected board: %s" % GameSetupSpecScript.format_shape(spec.get("shape", []))
	_description_label.text = str(spec.get("description", ""))


func _selected_index() -> int:
	var index := _preset_ids.find(_model.selected_preset_id())
	return maxi(index, 0)
