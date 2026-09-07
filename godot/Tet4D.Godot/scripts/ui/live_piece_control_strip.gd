extends PanelContainer

class_name LivePieceControlStrip

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const PassiveControlComponentsScript = preload("res://scripts/ui/passive_control_components.gd")

var _mode := ""
var _density := "normal"
var _groups: Array = []
var _signature := ""
var _groups_box: HBoxContainer
var _source := "LiveInputContract"


func _init() -> void:
	name = "LivePieceControlStrip"
	theme_type_variation = "ViewportFrame"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_meta("semantic_role", "passive_primary_gameplay_guidance")
	var margin := MarginContainer.new()
	margin.name = "PieceControlMargin"
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_%s" % side, 7)
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 6)
	add_child(margin)
	var content := VBoxContainer.new()
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_theme_constant_override("separation", 4)
	margin.add_child(content)
	var title := Label.new()
	title.name = "PieceControlTitle"
	title.text = "PIECE"
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", 13)
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(title)
	_groups_box = HBoxContainer.new()
	_groups_box.name = "PieceControlGroups"
	_groups_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_groups_box.add_theme_constant_override("separation", 10)
	content.add_child(_groups_box)


func configure(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}, density: String = "normal", authority = LiveInputContractScript) -> void:
	var groups: Array = authority.piece_control_groups(mode, basis_snapshot, control_frame)
	var next_signature := JSON.stringify([mode, density, groups])
	if next_signature == _signature:
		return
	_mode = mode
	_density = density
	_groups = groups.duplicate(true)
	_source = "LiveInputContract" if authority == LiveInputContractScript else "injected_fixture"
	_signature = next_signature
	_rebuild()


func deterministic_snapshot() -> Dictionary:
	var roles: Array = []
	var rows: Array = []
	var compact_items: Array = []
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		roles.append(role)
		for item in _merged_items(group.get("items", [])):
			rows.append(_semantic_row(role, item))
			compact_items.append({
				"role": role,
				"binding": str(item[0]),
				"source_label": str(item[1]),
				"compact_label": _legacy_compact_label(item, role),
				"semantic": _item_metadata(item),
			})
	return {
		"source": _source,
		"mode": _mode,
		"density": _density,
		"roles": roles,
		"rows": rows,
		"compact_items": compact_items,
		"row_ids": rows.map(func(row: Dictionary): return "%s:%s" % [row.get("role"), row.get("operation")]),
		"visible": visible,
		"rect": get_global_rect(),
	}


func _rebuild() -> void:
	for child in _groups_box.get_children():
		_groups_box.remove_child(child)
		child.queue_free()
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		var section := PassiveControlComponentsScript.section(_section_title(role), role, _density)
		section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		section.custom_minimum_size.x = 115.0 if role == "drop" else (190.0 if role == "translate" else 285.0)
		var row_parent: Container = section
		if role == "rotate":
			var rotation_grid := GridContainer.new()
			rotation_grid.name = "ControlRowGrid__rotate"
			rotation_grid.columns = 2
			rotation_grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
			rotation_grid.add_theme_constant_override("h_separation", 8)
			rotation_grid.add_theme_constant_override("v_separation", 1)
			section.add_child(rotation_grid)
			row_parent = rotation_grid
		for item in _merged_items(group.get("items", [])):
			var semantic := _semantic_row(role, item)
			row_parent.add_child(PassiveControlComponentsScript.row(str(semantic["operation"]), str(semantic["binding"]), role, _density))
		_groups_box.add_child(section)


func _section_title(role: String) -> String:
	return str({"translate": "MOVE", "drop": "DROP", "rotate": "ROTATE PIECE"}.get(role, role.to_upper()))


func _semantic_row(role: String, item: Array) -> Dictionary:
	var metadata := _item_metadata(item)
	return {
		"role": role,
		"operation": str(metadata.get("operation", _operation_label(item, role))),
		"binding": str(item[0]),
		"source_label": str(item[1]),
		"semantic": metadata,
	}


func _operation_label(item: Array, role: String) -> String:
	var label := str(item[1])
	if role == "translate":
		var signed_axis := str(_item_metadata(item).get("signed_axis", ""))
		if not signed_axis.is_empty():
			return signed_axis.trim_prefix("+")
	if role == "rotate" and label.begins_with("Rotate "):
		return label.trim_prefix("Rotate ")
	if role == "drop":
		return label.trim_suffix(" Drop")
	return label


func _legacy_compact_label(item: Array, role: String) -> String:
	var label := str(item[1])
	if role == "translate":
		var metadata := _item_metadata(item)
		var symbol := str({"horizontal": "← →", "depth": "↑ ↓", "slice": "W− W+"}.get(str(metadata.get("cockpit_direction", "")), ""))
		var signed_axis := str(metadata.get("signed_axis", ""))
		if not symbol.is_empty() and not signed_axis.is_empty():
			return "%s [%s]" % [symbol, signed_axis]
	if role == "rotate" and label.begins_with("Rotate "):
		return label.trim_prefix("Rotate ")
	return label


func _merged_items(source_items: Array) -> Array:
	var order: Array[String] = []
	var bindings_by_key := {}
	var label_by_key := {}
	var metadata_by_key := {}
	for item in source_items:
		if not (item is Array) or item.size() < 2:
			continue
		var label := str(item[1])
		var metadata := _item_metadata(item)
		var semantic_key := JSON.stringify([label, metadata])
		if not bindings_by_key.has(semantic_key):
			bindings_by_key[semantic_key] = []
			label_by_key[semantic_key] = label
			metadata_by_key[semantic_key] = metadata
			order.append(semantic_key)
		var binding := str(item[0])
		if not bindings_by_key[semantic_key].has(binding):
			bindings_by_key[semantic_key].append(binding)
	var result: Array = []
	for semantic_key in order:
		result.append([" · ".join(bindings_by_key[semantic_key]), label_by_key[semantic_key], metadata_by_key[semantic_key]])
	return result


func _item_metadata(item: Array) -> Dictionary:
	if item.size() < 3 or not (item[2] is Dictionary):
		return {}
	return item[2].duplicate(true)
