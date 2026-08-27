extends PanelContainer

class_name LivePieceControlStrip

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")

var _mode := ""
var _groups: Array = []
var _signature := ""
var _content: VBoxContainer
var _groups_box: VBoxContainer


func _init() -> void:
	name = "LivePieceControlStrip"
	theme_type_variation = "ViewportFrame"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_meta("semantic_role", "passive_primary_gameplay_guidance")
	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_%s" % side, 7)
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 6)
	add_child(margin)
	_content = VBoxContainer.new()
	_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_content.add_theme_constant_override("separation", 4)
	margin.add_child(_content)
	var title := Label.new()
	title.name = "PieceControlTitle"
	title.text = "PIECE CONTROLS"
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", 13)
	_content.add_child(title)
	_groups_box = VBoxContainer.new()
	_groups_box.name = "PieceControlGroups"
	_groups_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_groups_box.add_theme_constant_override("separation", 5)
	_content.add_child(_groups_box)


func configure(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> void:
	var groups := LiveInputContractScript.piece_control_groups(mode, basis_snapshot, control_frame)
	var next_signature := JSON.stringify(groups)
	if mode == _mode and next_signature == _signature:
		return
	_mode = mode
	_groups = groups.duplicate(true)
	_signature = next_signature
	_rebuild()


func deterministic_snapshot() -> Dictionary:
	var roles: Array = []
	var bindings: Array = []
	var action_labels: Array = []
	for group in _groups:
		roles.append(str(group.get("cockpit_role", "")))
		for item in group.get("items", []):
			bindings.append(str(item[0]))
			action_labels.append(str(item[1]))
	return {
		"source": "LiveInputContract",
		"mode": _mode,
		"roles": roles,
		"bindings": bindings,
		"action_labels": action_labels,
		"group_count": _groups.size(),
		"visible": visible,
		"rect": get_global_rect(),
	}


func _rebuild() -> void:
	for child in _groups_box.get_children():
		_groups_box.remove_child(child)
		child.queue_free()
	for group in _groups:
		_groups_box.add_child(_build_group(group))


func _build_group(group: Dictionary) -> Control:
	var role := str(group.get("cockpit_role", ""))
	var box := VBoxContainer.new()
	box.name = "PieceControlGroup__%s" % role
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_theme_constant_override("separation", 2)
	var heading := HBoxContainer.new()
	heading.mouse_filter = Control.MOUSE_FILTER_IGNORE
	heading.add_theme_constant_override("separation", 5)
	box.add_child(heading)
	var symbol := Label.new()
	symbol.name = "PieceControlSymbol"
	symbol.text = "↔" if role == "translate" else "⟳"
	symbol.theme_type_variation = "AccentLabel"
	symbol.custom_minimum_size = Vector2(22, 18)
	symbol.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	heading.add_child(symbol)
	var title := Label.new()
	title.name = "PieceControlCategory"
	title.text = "TRANSLATE" if role == "translate" else "ROTATE"
	title.theme_type_variation = "SecondaryLabel"
	title.add_theme_font_size_override("font_size", 12)
	heading.add_child(title)
	var flow := HFlowContainer.new()
	flow.name = "PieceControlItems__%s" % role
	flow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flow.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	flow.add_theme_constant_override("h_separation", 5)
	flow.add_theme_constant_override("v_separation", 3)
	box.add_child(flow)
	for item in _merged_items(group.get("items", [])):
		flow.add_child(_build_item(role, item))
	return box


func _build_item(role: String, item: Array) -> Control:
	var row := HBoxContainer.new()
	row.name = "PieceControlItem"
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 4)
	row.custom_minimum_size.x = 190.0 if role == "translate" else 90.0
	var action := Label.new()
	action.name = "PieceControlAction"
	action.text = _compact_action_label(str(item[1]), role)
	action.theme_type_variation = "SecondaryLabel"
	action.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	action.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(action)
	var keycap := Label.new()
	keycap.name = "PieceControlBinding"
	keycap.text = str(item[0])
	keycap.theme_type_variation = "KeycapLabel"
	keycap.add_theme_font_size_override("font_size", 11)
	keycap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	keycap.custom_minimum_size = Vector2(72 if role == "translate" else 50, 18)
	row.add_child(keycap)
	return row


func _merged_items(source_items: Array) -> Array:
	var order: Array[String] = []
	var bindings_by_label := {}
	for item in source_items:
		if not (item is Array) or item.size() < 2:
			continue
		var label := str(item[1])
		if not bindings_by_label.has(label):
			bindings_by_label[label] = []
			order.append(label)
		var binding := str(item[0])
		if not bindings_by_label[label].has(binding):
			bindings_by_label[label].append(binding)
	var result: Array = []
	for label in order:
		result.append([" · ".join(bindings_by_label[label]), label])
	return result


func _compact_action_label(label: String, role: String) -> String:
	if role == "translate":
		if label.begins_with("Left / Right"):
			return "← →%s" % _axis_suffix(label)
		if label.begins_with("Forward / Back"):
			return "↑ ↓%s" % _axis_suffix(label)
		if label.begins_with("Slice Down / Up"):
			return "W− W+%s" % _axis_suffix(label)
	if role == "rotate" and label.ends_with("counter-clockwise"):
		return "CCW"
	if role == "rotate" and label.ends_with("clockwise"):
		return "CW"
	if role == "rotate" and label.begins_with("Rotate "):
		return label.trim_prefix("Rotate ")
	return label


func _axis_suffix(label: String) -> String:
	var axis_start := label.rfind(" [")
	if axis_start < 0:
		return ""
	return label.substr(axis_start)
