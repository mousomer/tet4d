extends PanelContainer

class_name EventListPanel

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

var _list: ItemList
var _title: Label


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.EVENTS_MIN_HEIGHT)
	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(layout)
	_title = Label.new()
	_title.text = "Frame Events"
	layout.add_child(_title)
	_list = ItemList.new()
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(_list)


func set_events(event_lines: Array) -> void:
	_list.clear()
	_title.text = "Frame Events  •  %d" % event_lines.size()
	if event_lines.is_empty():
		_list.add_item("No events in this frame.")
		return
	for line in event_lines:
		_list.add_item(str(line))
