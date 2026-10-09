extends RefCounted

class_name PassiveControlComponents

const Tokens = preload("res://scripts/ui/style/shell_design_tokens.gd")

static func section(title_text: String, role: String, density: String = "normal") -> VBoxContainer:
	var box := VBoxContainer.new()
	box.name = "ControlSection__%s" % role
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_theme_constant_override("separation", 1 if density == "compact" else 2)
	var title := Label.new()
	title.name = "ControlSectionTitle"
	title.text = title_text
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title.theme_type_variation = "SecondaryLabel"
	title.add_theme_font_size_override("font_size", Tokens.FONT_SECTION)
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
	operation_label.add_theme_font_size_override("font_size", Tokens.FONT_CONTROL_HINT)
	operation_label.custom_minimum_size.x = 50.0 if density == "compact" else 56.0
	operation_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	operation_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	operation_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result.add_child(operation_label)
	result.add_child(binding_pair(binding, density, pointer))
	return result


# Key-first row for the active-play legend. The keys sit in a fixed-width
# column so the eye can scan straight down them; the operation is secondary
# text and never wraps, because a wrapped "clock / wise" cannot be read at a
# glance.
static func key_first_row(operation: String, binding: String, role: String, key_column_width: float, tag := "") -> HBoxContainer:
	var result := HBoxContainer.new()
	result.name = "LegendRow__%s" % role
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	result.add_theme_constant_override("separation", Tokens.SPACE_3)
	var keys := HBoxContainer.new()
	keys.name = "LegendKeys"
	keys.mouse_filter = Control.MOUSE_FILTER_IGNORE
	keys.custom_minimum_size.x = key_column_width
	keys.add_theme_constant_override("separation", 4)
	var glyphs: Array[String] = []
	var letters: Array[String] = []
	for label in binding_labels(binding):
		var glyph := key_glyph(label)
		(letters if glyph == label else glyphs).append(glyph)
	# Arrows lead: they are the primary scheme and are read by shape.
	glyphs.append_array(letters)
	for label in glyphs:
		var cap := keycap(label)
		# A uniform minimum keeps single letters square-ish, so a row of caps
		# reads as keys rather than as a word.
		cap.custom_minimum_size.x = float(Tokens.FONT_CONTROL_HINT) * 1.4
		keys.add_child(cap)
	result.add_child(keys)
	var operation_label := Label.new()
	operation_label.name = "LegendOperation"
	operation_label.text = operation
	operation_label.theme_type_variation = "SecondaryLabel"
	operation_label.add_theme_font_size_override("font_size", Tokens.FONT_CONTROL_HINT)
	operation_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	operation_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	operation_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	operation_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result.add_child(operation_label)
	if not tag.is_empty():
		# Reference name for players who think in planes; never the only cue.
		var tag_label := Label.new()
		tag_label.name = "LegendTag"
		tag_label.text = tag
		tag_label.theme_type_variation = "SecondaryLabel"
		tag_label.add_theme_font_size_override("font_size", Tokens.FONT_CHROME_SUPPORTING)
		tag_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		tag_label.modulate = Color(1.0, 1.0, 1.0, 0.6)
		tag_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		result.add_child(tag_label)
	return result


# Arrow keys are recognised by shape faster than by name.
static func key_glyph(label: String) -> String:
	return str({"Left": "←", "Right": "→", "Up": "↑", "Down": "↓", "Backspace": "Bksp"}.get(label, label))


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
	result.add_theme_font_size_override("font_size", Tokens.FONT_CONTROL_HINT)
	result.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	# Text metrics own the chip size. Density may reduce gaps, never glyph size.
	result.custom_minimum_size = Vector2.ZERO
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
