extends PanelContainer

class_name CaseBrowser

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

signal trace_family_selected(trace_type: String)
signal case_selected(case_id: String)

var _family_select: OptionButton
var _search_input: LineEdit
var _case_list: ItemList
var _cases: Array = []
var _summary_label: Label


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(ReplayVisuals.LEFT_PANEL_WIDTH, ReplayVisuals.CASE_BROWSER_MIN_HEIGHT)

	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(layout)

	var title := Label.new()
	title.text = "Replay Cases"
	layout.add_child(title)
	_summary_label = Label.new()
	_summary_label.theme_type_variation = "SecondaryLabel"
	_summary_label.text = "Replay case browser · selected state uses bright cyan fill"
	layout.add_child(_summary_label)

	_family_select = OptionButton.new()
	_family_select.item_selected.connect(_on_family_changed)
	layout.add_child(_family_select)

	_search_input = LineEdit.new()
	_search_input.placeholder_text = "Filter cases"
	_search_input.text_changed.connect(_refresh_case_list)
	layout.add_child(_search_input)

	_case_list = ItemList.new()
	_case_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_case_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_case_list.select_mode = ItemList.SELECT_SINGLE
	_case_list.item_selected.connect(_on_case_selected)
	layout.add_child(_case_list)


func set_trace_families(families: Array, selected: String) -> void:
	_family_select.clear()
	for trace_type in families:
		_family_select.add_item(str(trace_type))
	var index := families.find(selected)
	if index >= 0:
		_family_select.select(index)
	_summary_label.text = "%s traces" % selected.capitalize()


func set_cases(cases: Array, selected_case_id: String) -> void:
	_cases = cases.duplicate(true)
	_summary_label.text = "%s cases" % _cases.size()
	_refresh_case_list("")
	for index in range(_case_list.item_count):
		if _case_list.get_item_metadata(index) == selected_case_id:
			_case_list.select(index)
			break


func _refresh_case_list(_text: String) -> void:
	if _case_list == null:
		return
	_case_list.clear()
	var needle := _search_input.text.to_lower()
	for case_entry in _cases:
		var case_id := str(case_entry.get("case_id", ""))
		if not needle.is_empty() and needle not in case_id.to_lower():
			continue
		var label := _format_case_label(case_entry)
		_case_list.add_item(label)
		_case_list.set_item_metadata(_case_list.item_count - 1, case_id)


func _format_case_label(case_entry: Dictionary) -> String:
	var case_id := str(case_entry.get("case_id", ""))
	var parts: Array[String] = []
	var dimension: Variant = case_entry.get("dimension", null)
	if dimension != null:
		parts.append("%sD" % str(dimension))
	var topology_label: Variant = case_entry.get("topology_preset", case_entry.get("topology_id", ""))
	if topology_label != null and str(topology_label) != "":
		parts.append(str(topology_label))
	var badge := "  ".join(parts)
	return "[%s]  %s" % [badge, case_id] if badge != "" else case_id


func _on_family_changed(index: int) -> void:
	trace_family_selected.emit(_family_select.get_item_text(index))


func _on_case_selected(index: int) -> void:
	case_selected.emit(str(_case_list.get_item_metadata(index)))
