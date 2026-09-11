extends RefCounted

class_name PassiveControlComponents


static func section(title_text: String, role: String, density: String = "normal") -> VBoxContainer:
	var box := VBoxContainer.new()
	box.name = "ControlSection__%s" % role
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_theme_constant_override("separation", 1 if density == "compact" else 2)
	var title := Label.new()
	title.name = "ControlSectionTitle"
	title.text = title_text
	title.theme_type_variation = "SecondaryLabel"
	title.add_theme_font_size_override("font_size", 10 if density == "compact" else 11)
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(title)
	return box


static func row(operation: String, binding: String, role: String, density: String = "normal", pointer := false) -> HBoxContainer:
	var result := HBoxContainer.new()
	result.name = "ControlRow__%s" % role
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	result.add_theme_constant_override("separation", 4 if density == "compact" else 6)
	var operation_label := Label.new()
	operation_label.name = "ControlRowOperation"
	operation_label.text = operation
	operation_label.theme_type_variation = "DimLabel" if density == "compact" else "SecondaryLabel"
	operation_label.add_theme_font_size_override("font_size", 10 if density == "compact" else 11)
	operation_label.custom_minimum_size.x = 50.0 if density == "compact" else 64.0
	operation_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	operation_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	operation_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result.add_child(operation_label)
	result.add_child(binding_pair(binding, density, pointer))
	return result


static func binding_pair(binding: String, density: String = "normal", pointer := false) -> HBoxContainer:
	var pair := HBoxContainer.new()
	pair.name = "PointerGesture" if pointer else "BindingPair"
	pair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pair.add_theme_constant_override("separation", 3)
	for label in binding_labels(binding):
		pair.add_child(keycap(label, density, pointer))
	return pair


static func keycap(binding: String, density: String = "normal", pointer := false) -> Label:
	var result := Label.new()
	result.name = "PointerGestureKeycap" if pointer else "Keycap"
	result.text = binding
	result.theme_type_variation = "KeycapLabel"
	result.add_theme_font_size_override("font_size", 10 if density == "compact" else 11)
	result.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	result.custom_minimum_size = Vector2(maxf(24.0, 8.0 + binding.length() * (5.2 if density == "compact" else 5.8)), 18.0)
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result.set_meta("semantic_role", "pointer_gesture" if pointer else "passive_keycap")
	return result


static func binding_labels(binding: String) -> Array[String]:
	if binding.contains(" · "):
		# Merged alternatives still split on their own separator, so a keycap
		# never renders an embedded "A / D" where an unmerged row would show
		# two caps.
		var alternatives: Array[String] = []
		for alternative in binding.split(" · ", false):
			alternatives.append_array(binding_labels(alternative.strip_edges()))
		return alternatives
	var separator := " / " if binding.contains(" / ") else ("/" if binding.contains("/") else "")
	if separator.is_empty():
		return [binding]
	var result: Array[String] = []
	for part in binding.split(separator, false):
		result.append(part.strip_edges())
	return result
