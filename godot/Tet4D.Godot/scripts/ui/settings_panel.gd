extends PanelContainer

class_name SettingsPanel

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

signal playback_speed_changed(value: float)
signal diagnostics_visibility_changed(visible: bool)
signal display_mode_changed(mode: String)

var _diagnostics_toggle: CheckBox
var _display_mode_select: OptionButton


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.SETTINGS_MIN_HEIGHT)
	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(layout)
	var title := Label.new()
	title.text = "Replay Settings"
	layout.add_child(title)

	var display_mode_label := Label.new()
	display_mode_label.text = "Display Mode"
	display_mode_label.theme_type_variation = "SecondaryLabel"
	layout.add_child(display_mode_label)

	_display_mode_select = OptionButton.new()
	for display_mode in ReplayVisuals.DISPLAY_MODES:
		_display_mode_select.add_item(ReplayVisuals.display_mode_label(display_mode))
	_display_mode_select.item_selected.connect(_on_display_mode_selected)
	layout.add_child(_display_mode_select)

	_diagnostics_toggle = CheckBox.new()
	_diagnostics_toggle.text = "Show diagnostics"
	_diagnostics_toggle.button_pressed = true
	_diagnostics_toggle.toggled.connect(_on_diagnostics_toggled)
	layout.add_child(_diagnostics_toggle)
	var note := Label.new()
	note.text = "Presentation controls only. Python remains authoritative. Diagnostic is the startup readability mode."
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.theme_type_variation = "DimLabel"
	layout.add_child(note)


func set_diagnostics_visible(visible: bool) -> void:
	_diagnostics_toggle.set_pressed_no_signal(visible)


func set_display_mode(mode: String) -> void:
	var normalized := ReplayVisuals.normalize_display_mode(mode)
	var index := ReplayVisuals.DISPLAY_MODES.find(normalized)
	if index >= 0:
		_display_mode_select.select(index)


func _on_diagnostics_toggled(visible: bool) -> void:
	diagnostics_visibility_changed.emit(visible)


func _on_display_mode_selected(index: int) -> void:
	if index < 0 or index >= ReplayVisuals.DISPLAY_MODES.size():
		return
	display_mode_changed.emit(ReplayVisuals.DISPLAY_MODES[index])
