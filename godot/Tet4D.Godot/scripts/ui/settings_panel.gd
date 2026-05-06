extends PanelContainer

class_name SettingsPanel

signal playback_speed_changed(value: float)
signal diagnostics_visibility_changed(visible: bool)

var _speed_slider: HSlider
var _speed_value: Label
var _diagnostics_toggle: CheckBox


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(320, 120)
	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(layout)
	var title := Label.new()
	title.text = "Replay Settings"
	layout.add_child(title)

	var speed_row := HBoxContainer.new()
	layout.add_child(speed_row)
	var speed_label := Label.new()
	speed_label.text = "Speed"
	speed_row.add_child(speed_label)
	_speed_slider = HSlider.new()
	_speed_slider.min_value = 1.0
	_speed_slider.max_value = 20.0
	_speed_slider.step = 1.0
	_speed_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_speed_slider.value_changed.connect(_on_speed_changed)
	speed_row.add_child(_speed_slider)
	_speed_value = Label.new()
	_speed_value.text = "1x"
	speed_row.add_child(_speed_value)

	_diagnostics_toggle = CheckBox.new()
	_diagnostics_toggle.text = "Show diagnostics"
	_diagnostics_toggle.button_pressed = true
	_diagnostics_toggle.toggled.connect(_on_diagnostics_toggled)
	layout.add_child(_diagnostics_toggle)


func set_speed(value: float) -> void:
	_speed_slider.set_value_no_signal(value)
	_speed_value.text = "%sx" % int(value)


func set_diagnostics_visible(visible: bool) -> void:
	_diagnostics_toggle.set_pressed_no_signal(visible)


func _on_speed_changed(value: float) -> void:
	_speed_value.text = "%sx" % int(value)
	playback_speed_changed.emit(value)


func _on_diagnostics_toggled(visible: bool) -> void:
	diagnostics_visibility_changed.emit(visible)
