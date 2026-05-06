extends Control

class_name ReplayHud

signal trace_family_selected(trace_type: String)
signal case_selected(case_id: String)
signal previous_frame_requested()
signal next_frame_requested()
signal play_pause_requested()
signal reset_requested()
signal frame_scrub_requested(frame_index: int)
signal playback_speed_changed(value: float)
signal diagnostics_visibility_changed(visible: bool)

var _bundle_status_label: Label
var _summary_label: Label
var _authority_label: Label
var _case_browser: CaseBrowser
var _diagnostics_panel: DiagnosticsPanel
var _event_panel: EventListPanel
var _settings_panel: SettingsPanel
var _play_button: Button
var _frame_slider: HSlider
var _frame_label: Label


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_PASS
	_build_layout()


func set_bundle_status(text: String) -> void:
	_bundle_status_label.text = text


func set_trace_families(families: Array, selected: String) -> void:
	_case_browser.set_trace_families(families, selected)


func set_cases(cases: Array, selected_case_id: String) -> void:
	_case_browser.set_cases(cases, selected_case_id)


func set_summary(trace_type: String, case_id: String, dimension: int, frame_index: int, frame_count: int, state_hash: String) -> void:
	_summary_label.text = "trace_type: %s\ncase_id: %s\ndimension: %d\nstate_hash: %s" % [
		trace_type,
		case_id,
		dimension,
		state_hash,
	]
	_frame_label.text = "Frame %d / %d" % [frame_index, max(frame_count - 1, 0)]
	_frame_slider.max_value = max(frame_count - 1, 0)
	_frame_slider.set_value_no_signal(frame_index)


func set_snapshot(snapshot: Dictionary, diagnostics_visible: bool) -> void:
	_diagnostics_panel.visible = diagnostics_visible
	_diagnostics_panel.set_content(
		snapshot.get("metadata_lines", []),
		snapshot.get("diagnostics_lines", []),
		snapshot.get("energy_lines", [])
	)
	_event_panel.set_events(snapshot.get("event_lines", []))


func set_playback_state(is_playing: bool, speed: float, diagnostics_visible: bool) -> void:
	_play_button.text = "Pause" if is_playing else "Play"
	_settings_panel.set_speed(speed)
	_settings_panel.set_diagnostics_visible(diagnostics_visible)


func _build_layout() -> void:
	var root := MarginContainer.new()
	root.anchors_preset = Control.PRESET_FULL_RECT
	root.anchor_right = 1.0
	root.anchor_bottom = 1.0
	root.add_theme_constant_override("margin_left", 16)
	root.add_theme_constant_override("margin_top", 16)
	root.add_theme_constant_override("margin_right", 16)
	root.add_theme_constant_override("margin_bottom", 16)
	add_child(root)

	var outer := VBoxContainer.new()
	outer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	outer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(outer)

	var top_bar := HBoxContainer.new()
	top_bar.custom_minimum_size = Vector2(0, 72)
	outer.add_child(top_bar)

	_bundle_status_label = Label.new()
	_bundle_status_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_bundle_status_label.text = "Bundle status: loading"
	top_bar.add_child(_bundle_status_label)

	_summary_label = Label.new()
	_summary_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_summary_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	top_bar.add_child(_summary_label)

	_authority_label = Label.new()
	_authority_label.text = "Python oracle / Godot replay-only"
	_authority_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	top_bar.add_child(_authority_label)

	var body := HBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 12)
	outer.add_child(body)

	_case_browser = CaseBrowser.new()
	_case_browser.trace_family_selected.connect(func(trace_type: String) -> void:
		trace_family_selected.emit(trace_type)
	)
	_case_browser.case_selected.connect(func(case_id: String) -> void:
		case_selected.emit(case_id)
	)
	body.add_child(_case_browser)

	var center_spacer := Control.new()
	center_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center_spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	body.add_child(center_spacer)

	var right_column := VBoxContainer.new()
	right_column.size_flags_horizontal = Control.SIZE_FILL
	right_column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right_column.custom_minimum_size = Vector2(360, 0)
	right_column.add_theme_constant_override("separation", 12)
	body.add_child(right_column)

	_diagnostics_panel = DiagnosticsPanel.new()
	right_column.add_child(_diagnostics_panel)
	_event_panel = EventListPanel.new()
	right_column.add_child(_event_panel)
	_settings_panel = SettingsPanel.new()
	_settings_panel.playback_speed_changed.connect(func(value: float) -> void:
		playback_speed_changed.emit(value)
	)
	_settings_panel.diagnostics_visibility_changed.connect(func(visible: bool) -> void:
		diagnostics_visibility_changed.emit(visible)
	)
	right_column.add_child(_settings_panel)

	var bottom := HBoxContainer.new()
	bottom.custom_minimum_size = Vector2(0, 52)
	bottom.add_theme_constant_override("separation", 10)
	outer.add_child(bottom)

	var prev_button := Button.new()
	prev_button.text = "Prev"
	prev_button.pressed.connect(func() -> void:
		previous_frame_requested.emit()
	)
	bottom.add_child(prev_button)

	_play_button = Button.new()
	_play_button.text = "Play"
	_play_button.pressed.connect(func() -> void:
		play_pause_requested.emit()
	)
	bottom.add_child(_play_button)

	var next_button := Button.new()
	next_button.text = "Next"
	next_button.pressed.connect(func() -> void:
		next_frame_requested.emit()
	)
	bottom.add_child(next_button)

	var reset_button := Button.new()
	reset_button.text = "Reset"
	reset_button.pressed.connect(func() -> void:
		reset_requested.emit()
	)
	bottom.add_child(reset_button)

	_frame_slider = HSlider.new()
	_frame_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_frame_slider.step = 1.0
	_frame_slider.value_changed.connect(func(value: float) -> void:
		frame_scrub_requested.emit(int(value))
	)
	bottom.add_child(_frame_slider)

	_frame_label = Label.new()
	_frame_label.text = "Frame 0 / 0"
	bottom.add_child(_frame_label)
