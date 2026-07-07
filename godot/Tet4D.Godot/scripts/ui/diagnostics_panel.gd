extends PanelContainer

class_name DiagnosticsPanel

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

var _label: RichTextLabel
var _title: Label


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.DIAGNOSTICS_MIN_HEIGHT)
	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(layout)
	_title = Label.new()
	_title.text = "Replay Diagnostics"
	layout.add_child(_title)
	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(scroll)
	_label = RichTextLabel.new()
	_label.fit_content = false
	_label.scroll_active = true
	_label.bbcode_enabled = true
	_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.add_child(_label)


func set_snapshot(snapshot: Dictionary) -> void:
	var sections: Array = []
	sections.append("[b]Frame[/b]")
	for line in snapshot.get("metadata_lines", []):
		sections.append(str(line))
	var event_lines: Array = snapshot.get("event_lines", [])
	if not event_lines.is_empty():
		sections.append("")
		sections.append("[b]Events[/b]")
		for line in event_lines.slice(0, 4):
			sections.append(str(line))
	var diagnostics_lines: Array = snapshot.get("diagnostics_lines", [])
	if not diagnostics_lines.is_empty():
		sections.append("")
		sections.append("[b]Topology[/b]")
		for line in diagnostics_lines:
			sections.append(str(line))
	var energy_lines: Array = snapshot.get("energy_lines", [])
	if not energy_lines.is_empty():
		sections.append("")
		sections.append("[b]Energy[/b]")
		for line in energy_lines:
			sections.append(str(line))
	_label.text = "\n".join(sections)


func set_title(text: String) -> void:
	if _title != null:
		_title.text = text
