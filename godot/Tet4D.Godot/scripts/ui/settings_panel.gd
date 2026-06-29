extends PanelContainer

class_name SettingsPanel

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const SettingsStoreScript = preload("res://scripts/ui/settings/settings_store.gd")
const SettingControlFactoryScript = preload("res://scripts/ui/settings/setting_control_factory.gd")
const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellControlStyleApplierScript = preload("res://scripts/ui/style/shell_control_style_applier.gd")

signal setting_changed(setting_id: String, value)
signal playback_speed_changed(value: float)
signal replay_loop_changed(enabled: bool)
signal display_w_labels_changed(visible: bool)
signal projection_strength_changed(value: float)
signal diagnostics_visibility_changed(visible: bool)
signal layout_bounds_visibility_changed(visible: bool)
signal keyboard_hints_visibility_changed(visible: bool)
signal display_mode_changed(mode: String)

var registry = SettingsRegistryScript.new()
var store
var _control_factory = SettingControlFactoryScript.new()
var _style_manager = null
var _style_applier = ShellControlStyleApplierScript.new()
var _controls_by_id: Dictionary = {}
var _updating_controls := false


func _ready() -> void:
	if registry.settings.is_empty():
		registry.load_from_path(SettingsRegistryScript.REGISTRY_PATH)
	if store == null:
		store = SettingsStoreScript.new(registry)
	if _style_manager == null:
		_style_manager = ShellStyleManagerScript.new()
		_style_manager.set_theme(ReplayVisuals.normalize_display_mode(str(store.value("theme.name"))))
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.SETTINGS_MIN_HEIGHT)
	_build_panel()
	apply_shell_style()


func setting_value(setting_id: String):
	return store.value(setting_id)


func set_setting_value(setting_id: String, value) -> void:
	store.set_value(setting_id, value)
	_update_control(setting_id, value)


func set_diagnostics_visible(visible: bool) -> void:
	pass


func set_display_mode(mode: String) -> void:
	set_setting_value("theme.name", ReplayVisuals.normalize_display_mode(mode))
	if _style_manager != null:
		_style_manager.set_theme(ReplayVisuals.normalize_display_mode(mode))
		apply_shell_style()


func set_playback_speed(speed: float) -> void:
	set_setting_value("replay.playback_speed", speed)


func apply_initial_settings() -> void:
	for spec in registry.settings:
		_emit_setting(spec.id(), store.value(spec.id()))


func generated_control(setting_id: String) -> Control:
	return _controls_by_id.get(setting_id)


func set_style_manager(style_manager) -> void:
	_style_manager = style_manager
	if _style_manager != null and is_inside_tree():
		apply_shell_style()


func style_manager():
	return _style_manager


func apply_shell_style() -> void:
	if _style_manager == null:
		return
	_style_applier.apply_to_tree(self, _style_manager)


func _build_panel() -> void:
	var validation_failures := registry.validate()
	if not validation_failures.is_empty():
		push_error("Shell settings registry validation failed: %s" % "; ".join(validation_failures))
	var scroll := ScrollContainer.new()
	scroll.name = "SettingsScroll"
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	var content := VBoxContainer.new()
	content.name = "SettingsContent"
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	scroll.add_child(content)
	content.add_child(_panel_intro())
	for category_data in registry.categories:
		var category_id := str(category_data.get("id", ""))
		var specs := registry.settings_for_category(category_id)
		if specs.is_empty():
			continue
		content.add_child(_section_header(registry.category_label(category_id)))
		for spec in specs:
			content.add_child(_setting_row(spec))


func _panel_intro() -> Control:
	var box := VBoxContainer.new()
	box.name = "SettingsIntro"
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", ReplayVisuals.SPEED_GROUP_GAP)
	var title := Label.new()
	title.name = "SettingsTitle"
	title.text = "Shell Settings"
	title.theme_type_variation = "AccentLabel"
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(title)
	var subtitle := Label.new()
	subtitle.name = "SettingsSubtitle"
	subtitle.text = "Visual replay-shell preferences. Python remains the gameplay oracle."
	subtitle.theme_type_variation = "DimLabel"
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(subtitle)
	return box


func _section_header(label_text: String) -> Control:
	var label := Label.new()
	label.name = "SectionHeader__%s" % label_text.replace(" ", "_")
	label.text = label_text
	label.theme_type_variation = "AccentLabel"
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label


func _setting_row(spec) -> Control:
	var row := PanelContainer.new()
	row.name = "SettingRow__%s" % spec.id().replace(".", "__")
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var row_content := HBoxContainer.new()
	row_content.name = "SettingRowContent"
	row_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row_content.add_theme_constant_override("separation", ReplayVisuals.CONTROL_GAP)
	row.add_child(row_content)
	var text_box := VBoxContainer.new()
	text_box.custom_minimum_size = Vector2(132, 0)
	text_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row_content.add_child(text_box)
	var label := Label.new()
	label.name = "SettingLabel__%s" % spec.id().replace(".", "__")
	label.text = spec.label()
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.theme_type_variation = "SecondaryLabel"
	text_box.add_child(label)
	var description := Label.new()
	description.name = "SettingDescription__%s" % spec.id().replace(".", "__")
	description.text = spec.description()
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.theme_type_variation = "DimLabel"
	text_box.add_child(description)
	var control := _control_factory.build_control(spec, store.value(spec.id()), _on_control_value_changed)
	control.custom_minimum_size = Vector2(96, 0)
	control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_controls_by_id[spec.id()] = control
	row_content.add_child(control)
	return row


func _on_control_value_changed(setting_id: String, value) -> void:
	if _updating_controls:
		return
	store.set_value(setting_id, value)
	_emit_setting(setting_id, value)


func _emit_setting(setting_id: String, value) -> void:
	setting_changed.emit(setting_id, value)
	match setting_id:
		"replay.playback_speed":
			playback_speed_changed.emit(float(value))
		"replay.loop_enabled":
			replay_loop_changed.emit(bool(value))
		"display.show_w_labels":
			display_w_labels_changed.emit(bool(value))
		"display.projection_strength":
			projection_strength_changed.emit(float(value))
		"theme.name":
			if _style_manager != null:
				_style_manager.set_theme(ReplayVisuals.normalize_display_mode(str(value)))
				apply_shell_style()
			display_mode_changed.emit(ReplayVisuals.normalize_display_mode(str(value)))
		"diagnostics.show_layout_bounds":
			layout_bounds_visibility_changed.emit(bool(value))
		"controls_help.show_keyboard_hints":
			keyboard_hints_visibility_changed.emit(bool(value))


func _update_control(setting_id: String, value) -> void:
	var control := _controls_by_id.get(setting_id) as Control
	if control == null:
		return
	_updating_controls = true
	if control is CheckBox:
		(control as CheckBox).set_pressed_no_signal(bool(value))
	elif control is OptionButton:
		var option_button := control as OptionButton
		for index in range(option_button.item_count):
			if str(option_button.get_item_metadata(index)) == str(value):
				option_button.select(index)
				break
	elif control is HBoxContainer:
		var slider := control.get_node_or_null("Slider") as HSlider
		var value_label := control.get_node_or_null("ValueLabel") as Label
		if slider != null:
			slider.set_value_no_signal(float(value))
		if value_label != null:
			var spec = registry.get_spec(setting_id)
			value_label.text = _control_factory.format_numeric_value(spec, float(value))
	elif control is LineEdit:
		(control as LineEdit).text = str(value)
	_updating_controls = false
