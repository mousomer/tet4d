extends PanelContainer

class_name DiagnosticsPanel

var _label: RichTextLabel


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(320, 220)
	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(layout)
	var title := Label.new()
	title.text = "Diagnostics"
	layout.add_child(title)
	_label = RichTextLabel.new()
	_label.fit_content = false
	_label.scroll_active = true
	_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(_label)


func set_content(metadata_lines: Array, diagnostics_lines: Array, energy_lines: Array) -> void:
	var sections: Array = []
	sections.append("[b]Metadata[/b]")
	for line in metadata_lines:
		sections.append(str(line))
	sections.append("")
	sections.append("[b]Diagnostics[/b]")
	for line in diagnostics_lines:
		sections.append(str(line))
	if not energy_lines.is_empty():
		sections.append("")
		sections.append("[b]Energy[/b]")
		for line in energy_lines:
			sections.append(str(line))
	_label.bbcode_enabled = true
	_label.text = "\n".join(sections)
