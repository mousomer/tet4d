extends RefCounted

const SettingSpecScript = preload("res://scripts/ui/settings/setting_spec.gd")


func build_control(spec, current_value, changed_callback: Callable) -> Control:
	match spec.control_type():
		"checkbox":
			return _checkbox(spec, bool(current_value), changed_callback)
		"slider":
			return _slider(spec, current_value, changed_callback)
		"dropdown":
			return _dropdown(spec, current_value, changed_callback)
		"text_field":
			return _text_field(spec, str(current_value), changed_callback)
		"button":
			return _button(spec, changed_callback)
		"label":
			return _label(str(current_value))
		_:
			return _label("Unsupported")


func _checkbox(spec, current_value: bool, changed_callback: Callable) -> Control:
	var control := CheckBox.new()
	control.name = _control_name(spec)
	control.button_pressed = current_value
	control.size_flags_horizontal = Control.SIZE_SHRINK_END
	control.toggled.connect(func(value: bool) -> void:
		changed_callback.call(spec.id(), value)
	)
	return control


func _slider(spec, current_value, changed_callback: Callable) -> Control:
	var group := HBoxContainer.new()
	group.name = _control_name(spec)
	group.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	group.add_theme_constant_override("separation", 8)
	var slider := HSlider.new()
	slider.name = "Slider"
	slider.min_value = float(spec.data.get("min", 0.0))
	slider.max_value = float(spec.data.get("max", 1.0))
	slider.step = float(spec.data.get("step", 1.0))
	slider.value = float(current_value)
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	group.add_child(slider)
	var value_label := Label.new()
	value_label.name = "ValueLabel"
	value_label.custom_minimum_size = Vector2(54, 0)
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value_label.text = format_numeric_value(spec, slider.value)
	group.add_child(value_label)
	slider.value_changed.connect(func(value: float) -> void:
		value_label.text = format_numeric_value(spec, value)
		var emitted_value = int(round(value)) if spec.value_type() == "int" else value
		changed_callback.call(spec.id(), emitted_value)
	)
	return group


func _dropdown(spec, current_value, changed_callback: Callable) -> Control:
	var control := OptionButton.new()
	control.name = _control_name(spec)
	var selected_index := 0
	var options: Array = spec.data.get("options", [])
	for index in range(options.size()):
		var option: Dictionary = options[index]
		var value := str(option.get("value", ""))
		control.add_item(str(option.get("label", value)))
		control.set_item_metadata(index, value)
		if value == str(current_value):
			selected_index = index
	control.select(selected_index)
	control.item_selected.connect(func(index: int) -> void:
		changed_callback.call(spec.id(), str(control.get_item_metadata(index)))
	)
	return control


func _text_field(spec, current_value: String, changed_callback: Callable) -> Control:
	var control := LineEdit.new()
	control.name = _control_name(spec)
	control.text = current_value
	control.text_submitted.connect(func(value: String) -> void:
		changed_callback.call(spec.id(), value)
	)
	control.focus_exited.connect(func() -> void:
		changed_callback.call(spec.id(), control.text)
	)
	return control


func _button(spec, changed_callback: Callable) -> Control:
	var control := Button.new()
	control.name = _control_name(spec)
	control.text = spec.label()
	control.pressed.connect(func() -> void:
		changed_callback.call(spec.id(), spec.data.get("action_id", spec.id()))
	)
	return control


func _label(text: String) -> Control:
	var control := Label.new()
	control.text = text
	control.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return control


func _control_name(spec) -> String:
	return "SettingControl__%s" % spec.id().replace(".", "__")


func format_numeric_value(spec, value: float) -> String:
	var unit := str(spec.data.get("unit", ""))
	if spec.value_type() == "int":
		return "%d%s" % [int(round(value)), unit]
	return "%.2f%s" % [value, unit]
