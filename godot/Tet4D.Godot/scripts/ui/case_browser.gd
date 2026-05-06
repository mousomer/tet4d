extends PanelContainer

class_name CaseBrowser

signal trace_family_selected(trace_type: String)
signal case_selected(case_id: String)

var _family_select: OptionButton
var _search_input: LineEdit
var _case_list: ItemList
var _cases: Array = []


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(280, 320)

	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(layout)

	var title := Label.new()
	title.text = "Trace Cases"
	layout.add_child(title)

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
	_case_list.item_selected.connect(_on_case_selected)
	layout.add_child(_case_list)


func set_trace_families(families: Array, selected: String) -> void:
	_family_select.clear()
	for trace_type in families:
		_family_select.add_item(str(trace_type))
	var index := families.find(selected)
	if index >= 0:
		_family_select.select(index)


func set_cases(cases: Array, selected_case_id: String) -> void:
	_cases = cases.duplicate(true)
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
		var label := case_id
		var dimension := case_entry.get("dimension", null)
		if dimension != null:
			label += "  [%sD]" % str(dimension)
		_case_list.add_item(label)
		_case_list.set_item_metadata(_case_list.item_count - 1, case_id)


func _on_family_changed(index: int) -> void:
	trace_family_selected.emit(_family_select.get_item_text(index))


func _on_case_selected(index: int) -> void:
	case_selected.emit(str(_case_list.get_item_metadata(index)))
