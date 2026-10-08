extends PanelContainer

class_name LivePieceControlStrip

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const PassiveControlComponentsScript = preload("res://scripts/ui/passive_control_components.gd")
const ShellDesignTokensScript = preload("res://scripts/ui/style/shell_design_tokens.gd")

# "deck" is the horizontal strip under the board; "rail" is the vertical,
# key-first legend beside a tall Live 2D board.
const LAYOUT_DECK := "deck"
const LAYOUT_RAIL := "rail"
# Rail sections follow what the player is trying to do, not one header per
# contract role: a single-row HOLD section would spend a header on one key.
const RAIL_SECTIONS := [
	["MOVE", ["translate", "drop"]],
	["ROTATE", ["rotate"]],
	["GAME", ["hold", "session"]],
]

var _mode := ""
var _density := "normal"
var _groups: Array = []
var _signature := ""
var _groups_box: BoxContainer
var _title: Label
var _scroll: ScrollContainer
var _layout := LAYOUT_DECK
var _source := "LiveInputContract"


func _init() -> void:
	name = "LivePieceControlStrip"
	theme_type_variation = "ViewportFrame"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	set_meta("semantic_role", "passive_primary_gameplay_guidance")
	var scroll := ScrollContainer.new()
	_scroll = scroll
	scroll.name = "PieceHelpScroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(scroll)
	var margin := MarginContainer.new()
	margin.name = "PieceControlMargin"
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_%s" % side, ShellDesignTokensScript.SPACE_1)
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 6)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(margin)
	var content := VBoxContainer.new()
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_theme_constant_override("separation", 4)
	margin.add_child(content)
	_title = Label.new()
	_title.name = "PieceControlTitle"
	_title.text = "PIECE"
	_title.theme_type_variation = "AccentLabel"
	_title.add_theme_font_size_override("font_size", ShellDesignTokensScript.FONT_SECTION)
	_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(_title)
	_groups_box = _new_groups_box(LAYOUT_DECK)
	content.add_child(_groups_box)


func configure(mode: String, basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}, density: String = "normal", authority = LiveInputContractScript, layout: String = LAYOUT_DECK) -> void:
	var rail := layout == LAYOUT_RAIL
	var groups: Array = authority.play_legend_groups(mode, basis_snapshot, control_frame) if rail else authority.piece_control_groups(mode, basis_snapshot, control_frame)
	var source := "LiveInputContract" if authority == LiveInputContractScript else "injected_fixture"
	# Provenance is part of the cached identity: an injected fixture that happens
	# to yield identical groups must not keep reporting contract provenance.
	var next_signature := JSON.stringify([mode, density, source, layout, groups])
	if next_signature == _signature:
		return
	_mode = mode
	_density = density
	_set_layout(layout)
	_groups = groups.duplicate(true)
	_source = source
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
		"layout": _layout,
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
	if _layout == LAYOUT_RAIL:
		_rebuild_rail()
		return
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		var section := PassiveControlComponentsScript.section(_section_title(role), role, _density)
		section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		# Reserve enough width for the full-size keycaps; wrapped operation text
		# and internal vertical scrolling keep the three deck modules together.
		section.custom_minimum_size.x = 115.0 if role == "drop" else (160.0 if role == "translate" else 248.0)
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


func _set_layout(layout: String) -> void:
	var next_layout := LAYOUT_RAIL if layout == LAYOUT_RAIL else LAYOUT_DECK
	_title.visible = next_layout == LAYOUT_DECK
	if next_layout == _layout:
		return
	_layout = next_layout
	# The rail scrolls as a whole. A nested auto-scroll reports no minimum
	# height, which would collapse the legend to nothing inside the rail.
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED if _layout == LAYOUT_RAIL else ScrollContainer.SCROLL_MODE_AUTO
	var parent := _groups_box.get_parent()
	parent.remove_child(_groups_box)
	_groups_box.queue_free()
	_groups_box = _new_groups_box(_layout)
	parent.add_child(_groups_box)


func _new_groups_box(layout: String) -> BoxContainer:
	var box: BoxContainer = VBoxContainer.new() if layout == LAYOUT_RAIL else HBoxContainer.new()
	box.name = "PieceControlGroups"
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_2)
	return box


func _rebuild_rail() -> void:
	var rows_by_role := {}
	var widest_cap_count := 1
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		var role_rows: Array = rows_by_role.get(role, [])
		for item in _merged_items(group.get("items", [])):
			role_rows.append(_semantic_row(role, item))
			widest_cap_count = maxi(widest_cap_count, PassiveControlComponentsScript.binding_labels(str(item[0])).size())
		rows_by_role[role] = role_rows
	# One shared key column across every section keeps all operations aligned.
	var key_column := float(widest_cap_count) * (float(ShellDesignTokensScript.FONT_CONTROL_HINT) * 1.4 + 4.0)
	for section_spec in RAIL_SECTIONS:
		var section_rows: Array = []
		for role in section_spec[1]:
			section_rows.append_array(rows_by_role.get(role, []))
		if section_rows.is_empty():
			continue
		var section := PassiveControlComponentsScript.section(str(section_spec[0]), str(section_spec[0]).to_lower(), _density)
		section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		for semantic in section_rows:
			section.add_child(PassiveControlComponentsScript.key_first_row(str(semantic["operation"]), str(semantic["binding"]), str(semantic["role"]), key_column))
		_groups_box.add_child(section)


func _section_title(role: String) -> String:
	return str({"translate": "MOVE", "drop": "DROP", "rotate": "ROTATE PIECE"}.get(role, role.to_upper()))


func _semantic_row(role: String, item: Array) -> Dictionary:
	var metadata := _item_metadata(item)
	return {
		"role": role,
		"operation": _operation_label(item, role) if _layout == LAYOUT_RAIL else str(metadata.get("operation", _operation_label(item, role))),
		"binding": str(item[0]),
		"source_label": str(item[1]),
		"semantic": metadata,
	}


func _operation_label(item: Array, role: String) -> String:
	var label := str(item[1])
	if _layout == LAYOUT_RAIL:
		return _rail_operation_label(label, role)
	if role == "translate":
		var signed_axis := str(_item_metadata(item).get("signed_axis", ""))
		if not signed_axis.is_empty():
			return signed_axis.trim_prefix("+")
	if role == "rotate" and label.begins_with("Rotate "):
		return label.trim_prefix("Rotate ")
	if role == "drop":
		return label.trim_suffix(" Drop")
	return label


# Plain verbs for the rail. Axis names are an implementation frame; a player
# choosing a key needs only the direction or the action.
func _rail_operation_label(label: String, role: String) -> String:
	match role:
		"translate":
			return "Move"
		"rotate":
			return {"Rotate clockwise": "Right (CW)", "Rotate counter-clockwise": "Left (CCW)"}.get(label, label.trim_prefix("Rotate "))
		"drop":
			return label.left(1) + label.substr(1).to_lower()
		"session":
			return "Restart" if label == "Restart Game" else label
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
