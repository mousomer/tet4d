extends PanelContainer

class_name LivePieceControlStrip

signal rebuilt

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const PassiveControlComponentsScript = preload("res://scripts/ui/passive_control_components.gd")
const ShellDesignTokensScript = preload("res://scripts/ui/style/shell_design_tokens.gd")
const ControlLegendGlyphScript = preload("res://scripts/ui/control_legend_glyph.gd")

# "deck" is the legacy horizontal strip; "rail" is the vertical key-first
# legend beside a tall board (2D, 3D); "wide" lays the same legend sections
# side by side for the Live 4D deck under its wide slice row.
const LAYOUT_DECK := "deck"
const LAYOUT_RAIL := "rail"
const LAYOUT_WIDE := "wide"
# Under view-relative controls the plane letters name screen directions
# (x sideways, y up, z depth, w the slice row), so a turn is named by what it
# mixes, and its glyph lights those directions. The letters stay as a tag.
const ROTATION_WORDS := {"XY": "Spin", "XZ": "Turn", "YZ": "Tip", "XW": "Side↔W", "YW": "Up↔W", "ZW": "Depth↔W"}
const MOVE_INTENTS := {"horizontal": ["move_x_neg", "move_x_pos"], "depth": ["move_z_neg", "move_z_pos"], "slice": ["move_w_neg", "move_w_pos"]}
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
var _groups_box: Container
var _title: Label
var _scroll: ScrollContainer
var _margin: MarginContainer
var _layout := LAYOUT_DECK
var _source := "LiveInputContract"
var _screen_directions := {}
var _glyphs: Array = []
var _slice_keys_reversed := false


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
	_margin = margin
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
	var legend := layout in [LAYOUT_RAIL, LAYOUT_WIDE]
	var groups: Array = authority.play_legend_groups(mode, basis_snapshot, control_frame) if legend else authority.piece_control_groups(mode, basis_snapshot, control_frame)
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
	var compass_keys := {}
	for glyph in _glyphs:
		if (glyph as ControlLegendGlyph).kind == ControlLegendGlyphScript.KIND_COMPASS:
			for entry in (glyph as ControlLegendGlyph).compass_keys:
				compass_keys[str(entry["intent"])] = str(entry["key"])
	return {
		"source": _source,
		"mode": _mode,
		"density": _density,
		"layout": _layout,
		"spatial": _is_spatial(),
		"compass_keys": compass_keys,
		"screen_directions": _screen_directions.duplicate(),
		"slice_keys_reversed": _slice_keys_reversed,
		"plane_glyphs": _glyphs.filter(func(glyph): return (glyph as ControlLegendGlyph).kind == ControlLegendGlyphScript.KIND_PLANE).map(func(glyph): return (glyph as ControlLegendGlyph).plane_axes),
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
	_glyphs.clear()
	if _layout in [LAYOUT_RAIL, LAYOUT_WIDE]:
		_rebuild_rail()
		rebuilt.emit()
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

	rebuilt.emit()


# Measured on-screen directions from the app: movement intents and local
# rotation axes -> normalized screen vectors. Glyphs redraw in place.
func flash_plane(plane: String) -> bool:
	return ControlLegendGlyphScript.flash_matching(_glyphs, plane)


func set_screen_directions(directions: Dictionary) -> void:
	_screen_directions = directions.duplicate()
	if _is_spatial() and _slice_keys_reversed != _slice_positive_points_left():
		_rebuild()
		return
	for glyph in _glyphs:
		(glyph as ControlLegendGlyph).set_directions(_screen_directions)


func _is_spatial() -> bool:
	return _layout in [LAYOUT_RAIL, LAYOUT_WIDE] and _mode in ["live_3d", "live_4d"]


func _slice_positive_points_left() -> bool:
	return (_screen_directions.get("move_w_pos", Vector2.ZERO) as Vector2).x < 0.0


func _set_layout(layout: String) -> void:
	var next_layout := layout if layout in [LAYOUT_RAIL, LAYOUT_WIDE] else LAYOUT_DECK
	_title.visible = next_layout == LAYOUT_DECK
	if next_layout == _layout:
		return
	_layout = next_layout
	# The rail and the 4D deck both scroll as a whole, so the legend must report
	# its true height: a nested auto-scroll reports none, which left the deck
	# sizing to a guess and the legend scrolling even when it had room.
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED if _layout in [LAYOUT_RAIL, LAYOUT_WIDE] else ScrollContainer.SCROLL_MODE_AUTO
	for side in ["top", "bottom"]:
		_margin.add_theme_constant_override("margin_%s" % side, 2 if _layout == LAYOUT_RAIL else 6)
	var parent := _groups_box.get_parent()
	parent.remove_child(_groups_box)
	_groups_box.queue_free()
	_groups_box = _new_groups_box(_layout)
	parent.add_child(_groups_box)


func _new_groups_box(layout: String) -> Container:
	if layout == LAYOUT_WIDE:
		# Sections wrap onto another line in a narrow window rather than forcing
		# the deck wider than the window.
		var flow := HFlowContainer.new()
		flow.name = "PieceControlGroups"
		flow.mouse_filter = Control.MOUSE_FILTER_IGNORE
		flow.add_theme_constant_override("h_separation", ShellDesignTokensScript.SPACE_4)
		flow.add_theme_constant_override("v_separation", ShellDesignTokensScript.SPACE_2)
		return flow
	var box: BoxContainer = VBoxContainer.new() if layout == LAYOUT_RAIL else HBoxContainer.new()
	box.name = "PieceControlGroups"
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Section titles already separate the rail's groups; a wide gap only costs
	# the height a magnified window is short of.
	box.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_1 if layout == LAYOUT_RAIL else ShellDesignTokensScript.SPACE_2)
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
	if _is_spatial():
		_build_spatial_legend(rows_by_role)
		return
	for section_spec in RAIL_SECTIONS:
		var section_rows: Array = []
		for role in section_spec[1]:
			section_rows.append_array(rows_by_role.get(role, []))
		if section_rows.is_empty():
			continue
		var section := PassiveControlComponentsScript.section(str(section_spec[0]), str(section_spec[0]).to_lower(), _density)
		section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if str(section_spec[0]) == "GAME":
			section.add_child(_compact_rows(section_rows))
		else:
			for semantic in section_rows:
				section.add_child(PassiveControlComponentsScript.key_first_row(str(semantic["operation"]), str(semantic["binding"]), str(semantic["role"]), key_column))
		_groups_box.add_child(section)


# 3D/4D: movement as a compass of where each key moves the piece on screen,
# rotations as glyph rows, then the game keys.
func _build_spatial_legend(rows_by_role: Dictionary) -> void:
	var cap_width := float(ShellDesignTokensScript.FONT_CONTROL_HINT) * 1.4 + 4.0
	_slice_keys_reversed = _slice_positive_points_left()
	var move := PassiveControlComponentsScript.section("MOVE", "move", _density)
	# Compass beside a column of the slice hop and the drops: no section grows
	# past three rows, which is what lets the 4D deck stay one unscrolled row.
	# In the rail the column wraps under the compass when the rail is narrow.
	# The wide deck wraps whole sections instead: a flow nested in a flow only
	# ever gets its minimum width, so it would always wrap.
	var wide := _layout == LAYOUT_WIDE
	var move_body: Container = HBoxContainer.new() if wide else HFlowContainer.new()
	move_body.name = "LegendMoveBody"
	move_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if wide:
		move_body.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_3)
	else:
		move_body.add_theme_constant_override("h_separation", ShellDesignTokensScript.SPACE_3)
		move_body.add_theme_constant_override("v_separation", ShellDesignTokensScript.SPACE_1)
	move.add_child(move_body)
	var compass_keys: Array = []
	var slice_labels: Array = []
	for semantic in rows_by_role.get("translate", []):
		var direction := str((semantic["semantic"] as Dictionary).get("cockpit_direction", ""))
		var labels := PassiveControlComponentsScript.binding_labels(str(semantic["binding"]))
		if labels.size() != 2 or not MOVE_INTENTS.has(direction):
			continue
		if direction == "slice":
			slice_labels = labels
			continue
		compass_keys.append({"intent": MOVE_INTENTS[direction][0], "key": labels[0]})
		compass_keys.append({"intent": MOVE_INTENTS[direction][1], "key": labels[1]})
	var compass := ControlLegendGlyphScript.compass(compass_keys, func(text: String) -> Label: return PassiveControlComponentsScript.keycap(PassiveControlComponentsScript.key_glyph(text)))
	_glyphs.append(compass)
	var compass_column := VBoxContainer.new()
	compass_column.name = "LegendCompassColumn"
	compass_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	compass_column.add_child(compass)
	move_body.add_child(compass_column)
	var move_column := VBoxContainer.new()
	move_column.name = "LegendMoveColumn"
	move_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	move_column.alignment = BoxContainer.ALIGNMENT_CENTER
	move_column.add_theme_constant_override("separation", 2)
	move_body.add_child(move_column)
	if slice_labels.size() == 2:
		move_column.add_child(_slice_row(slice_labels))
	for semantic in rows_by_role.get("drop", []):
		move_column.add_child(_legend_row(semantic, cap_width * 2.0))
	_groups_box.add_child(move)

	var rotate := PassiveControlComponentsScript.section("ROTATE", "rotate", _density)
	var rotation_rows: Array = rows_by_role.get("rotate", [])
	var in_view: Array = rotation_rows.filter(func(semantic): return not _rotation_plane(semantic).contains("W"))
	var with_w: Array = rotation_rows.filter(func(semantic): return _rotation_plane(semantic).contains("W"))
	var rotation_body: BoxContainer = HBoxContainer.new() if wide else VBoxContainer.new()
	rotation_body.name = "LegendRotationBody"
	rotation_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rotation_body.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_3 if wide else 2)
	rotate.add_child(rotation_body)
	for column_rows in [in_view, with_w]:
		if column_rows.is_empty():
			continue
		var column := VBoxContainer.new()
		column.mouse_filter = Control.MOUSE_FILTER_IGNORE
		column.add_theme_constant_override("separation", 2)
		rotation_body.add_child(column)
		for semantic in column_rows:
			column.add_child(_rotation_row(semantic, cap_width * 2.0))
	_groups_box.add_child(rotate)

	# Reset View belongs to the VIEW module, which Live 3D and 4D both show.
	var game_rows: Array = rows_by_role.get("hold", []) + rows_by_role.get("session", [])
	if not game_rows.is_empty():
		var game := PassiveControlComponentsScript.section("GAME", "game", _density)
		if _layout == LAYOUT_RAIL:
			game.add_child(_compact_rows(game_rows))
		else:
			for semantic in game_rows:
				game.add_child(_legend_row(semantic, cap_width * 2.0))
		_groups_box.add_child(game)
	for glyph in _glyphs:
		(glyph as ControlLegendGlyph).set_directions(_screen_directions)


# The slice row is laid out across the screen, so W moves are drawn as the
# horizontal hop between boards, keyed to whichever side each key goes.
func _slice_row(labels: Array) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.name = "LegendSliceRow"
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_1)
	var left_key := str(labels[1] if _slice_keys_reversed else labels[0])
	var right_key := str(labels[0] if _slice_keys_reversed else labels[1])
	row.add_child(PassiveControlComponentsScript.keycap(left_key))
	var hop := Label.new()
	hop.name = "LegendSliceHop"
	hop.text = "← slice →"
	hop.theme_type_variation = "SecondaryLabel"
	hop.add_theme_font_size_override("font_size", ShellDesignTokensScript.FONT_CONTROL_HINT)
	hop.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(hop)
	row.add_child(PassiveControlComponentsScript.keycap(right_key))
	return row


# Hold, pause and restart are glanced at rarely, so in a rail they share one
# flowing line of key + verb pairs: a magnified window gives the rail the
# height of a ~1280x780 shell, where three full rows pushed the 3D legend
# into scrolling. The line still wraps into rows when the rail is narrow.
func _compact_rows(rows: Array) -> HFlowContainer:
	var flow := HFlowContainer.new()
	flow.name = "LegendCompactRows"
	flow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flow.add_theme_constant_override("h_separation", ShellDesignTokensScript.SPACE_4)
	flow.add_theme_constant_override("v_separation", 2)
	for semantic in rows:
		var row := _legend_row(semantic, 0.0)
		row.size_flags_horizontal = Control.SIZE_FILL
		(row.get_node("LegendOperation") as Label).size_flags_horizontal = Control.SIZE_FILL
		flow.add_child(row)
	return flow


# Spatial legends size to their words: a trimmed verb would leave only the key.
func _legend_row(semantic: Dictionary, key_column: float, tag := "") -> HBoxContainer:
	var row := PassiveControlComponentsScript.key_first_row(str(semantic["operation"]), str(semantic["binding"]), str(semantic["role"]), key_column, tag)
	(row.get_node("LegendOperation") as Label).text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
	return row


func _rotation_row(semantic: Dictionary, key_column: float) -> HBoxContainer:
	var plane := _rotation_plane(semantic)
	# Plane names stay as a reference tag where the rail has room for them.
	var row := _legend_row(semantic, key_column, "" if _layout == LAYOUT_WIDE else plane)
	var keys := row.get_node("LegendKeys")
	var glyph := ControlLegendGlyphScript.plane(Array(plane.to_lower().split("")), keys.get_child(0) as Label)
	glyph.name = "LegendPlaneGlyph__%s" % plane
	row.add_child(glyph)
	row.move_child(glyph, 1)
	_glyphs.append(glyph)
	return row


func _rotation_plane(semantic: Dictionary) -> String:
	return str(semantic["source_label"]).trim_prefix("Rotate ").strip_edges()


func _section_title(role: String) -> String:
	return str({"translate": "MOVE", "drop": "DROP", "rotate": "ROTATE PIECE"}.get(role, role.to_upper()))


func _semantic_row(role: String, item: Array) -> Dictionary:
	var metadata := _item_metadata(item)
	return {
		"role": role,
		"operation": _operation_label(item, role) if _layout != LAYOUT_DECK else str(metadata.get("operation", _operation_label(item, role))),
		"binding": str(item[0]),
		"source_label": str(item[1]),
		"semantic": metadata,
	}


func _operation_label(item: Array, role: String) -> String:
	var label := str(item[1])
	if _layout != LAYOUT_DECK:
		return _rail_operation_label(label, role, _item_metadata(item))
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
func _rail_operation_label(label: String, role: String, metadata: Dictionary = {}) -> String:
	match role:
		"translate":
			if _mode == "live_2d":
				return "Move"
			return str({"horizontal": "Sideways", "depth": "Near/far", "slice": "Slice"}.get(str(metadata.get("cockpit_direction", "")), "Move"))
		"rotate":
			var plane := label.trim_prefix("Rotate ").strip_edges()
			if ROTATION_WORDS.has(plane):
				return str(ROTATION_WORDS[plane])
			return {"Rotate clockwise": "Right (CW)", "Rotate counter-clockwise": "Left (CCW)"}.get(label, plane)
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
