extends PanelContainer

class_name LiveViewControlStrip

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const PassiveControlComponentsScript = preload("res://scripts/ui/passive_control_components.gd")
const ShellDesignTokensScript = preload("res://scripts/ui/style/shell_design_tokens.gd")
const ControlLegendGlyphScript = preload("res://scripts/ui/control_legend_glyph.gd")
const LivePieceControlStripScript = preload("res://scripts/ui/live_piece_control_strip.gd")

const LAYOUT_GRID := "grid"
# The Live 4D deck shows only what play needs: view turns, drawn with the same
# plane glyphs as piece rotation, and look. Zoom, Fit and pointer gestures stay
# in the full help and the header.
const LAYOUT_WIDE := "wide"
const WIDE_ROLES := ["view_exact", "view_orient"]

var _mode := "live_4d"
var _density := "normal"
var _groups: Array = []
var _groups_box: GridContainer
var _signature := ""
var _source := "LiveInputContract"
var _layout := LAYOUT_GRID
var _glyphs: Array = []
var _screen_directions := {}
var _wide_box: VBoxContainer
var _title: Label


func _init() -> void:
	name = "LiveViewControlStrip"
	theme_type_variation = "ViewportFrame"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	set_meta("semantic_role", "passive_view_guidance")
	var scroll := ScrollContainer.new()
	scroll.name = "ViewHelpScroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(scroll)
	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, ShellDesignTokensScript.SPACE_1)
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(margin)
	var content := VBoxContainer.new()
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_theme_constant_override("separation", 3)
	margin.add_child(content)
	var title := Label.new()
	_title = title
	title.name = "ViewControlTitle"
	title.text = "VIEW"
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", ShellDesignTokensScript.FONT_SECTION)
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(title)
	_groups_box = GridContainer.new()
	_groups_box.name = "ViewControlGroups"
	_groups_box.columns = 2
	_groups_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_groups_box.add_theme_constant_override("h_separation", ShellDesignTokensScript.SPACE_2)
	_groups_box.add_theme_constant_override("v_separation", 3)
	content.add_child(_groups_box)
	# Stacked: in Live 4D this module lives in the narrow side column.
	_wide_box = VBoxContainer.new()
	_wide_box.name = "ViewControlWideGroups"
	_wide_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_wide_box.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_2)
	_wide_box.visible = false
	content.add_child(_wide_box)


func configure(basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}, density: String = "normal", mode: String = "live_4d", authority = LiveInputContractScript, layout: String = LAYOUT_GRID) -> void:
	var groups: Array = authority.view_control_groups(mode, basis_snapshot, control_frame)
	if layout == LAYOUT_WIDE:
		groups = groups.filter(func(group): return str(group.get("cockpit_role", "")) in WIDE_ROLES)
	var source := "LiveInputContract" if authority == LiveInputContractScript else "injected_fixture"
	# Provenance is part of the cached identity: an injected fixture that happens
	# to yield identical groups must not keep reporting contract provenance.
	var next_signature := JSON.stringify([mode, density, source, layout, groups])
	if next_signature == _signature:
		return
	_layout = LAYOUT_WIDE if layout == LAYOUT_WIDE else LAYOUT_GRID
	# TURN VIEW and LOOK already name themselves; the module title would only
	# cost the 4D side column a row.
	_title.visible = _layout == LAYOUT_GRID
	var scroll := get_node("ViewHelpScroll") as ScrollContainer
	# The wide layout must report its true height so the deck can size to it.
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED if _layout == LAYOUT_WIDE else ScrollContainer.SCROLL_MODE_AUTO
	_mode = mode
	_density = density
	_groups = groups.duplicate(true)
	_source = source
	_signature = next_signature
	_rebuild()


func set_detached_layout(enabled: bool) -> void:
	_groups_box.columns = 1 if enabled else 2


func deterministic_snapshot() -> Dictionary:
	var rows: Array = []
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		for item in group.get("items", []):
			rows.append(_semantic_row(role, item))
	return {
		"source": _source,
		"mode": _mode,
		"density": _density,
		"roles": _groups.map(func(group): return str(group.get("cockpit_role", ""))),
		"groups": _groups.duplicate(true),
		"rows": rows,
		"row_ids": rows.map(func(row: Dictionary): return "%s:%s" % [row.get("role"), row.get("operation")]),
		"rect": get_global_rect(),
		"visible": visible,
		"layout": _layout,
		"plane_glyphs": _glyphs.map(func(glyph): return (glyph as ControlLegendGlyph).plane_axes),
	}


func flash_plane(plane: String) -> bool:
	return ControlLegendGlyphScript.flash_matching(_glyphs, plane)


func set_screen_directions(directions: Dictionary) -> void:
	_screen_directions = directions.duplicate()
	for glyph in _glyphs:
		(glyph as ControlLegendGlyph).set_directions(_screen_directions)


func _rebuild() -> void:
	for box in [_groups_box, _wide_box]:
		for child in box.get_children():
			box.remove_child(child)
			child.queue_free()
	_glyphs.clear()
	_groups_box.visible = _layout == LAYOUT_GRID
	_wide_box.visible = _layout == LAYOUT_WIDE
	if _layout == LAYOUT_WIDE:
		_rebuild_wide()
		return
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		var section := PassiveControlComponentsScript.section(_section_title(role), role, _density)
		section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		# Two readable columns leave room for PIECE STATE at standard widths.
		section.custom_minimum_size.x = 205.0
		for item in group.get("items", []):
			var semantic := _semantic_row(role, item)
			section.add_child(PassiveControlComponentsScript.row(
				str(semantic["operation"]),
				str(semantic["binding"]),
				role,
				_density,
				role == "view_pointer"
			))
		_groups_box.add_child(section)


func _rebuild_wide() -> void:
	var key_column := 2.0 * (float(ShellDesignTokensScript.FONT_CONTROL_HINT) * 1.4 + 4.0)
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		var section := PassiveControlComponentsScript.section({"view_exact": "TURN VIEW", "view_orient": "LOOK"}.get(role, role.to_upper()), role, _density)
		# Look pairs stack inside the bounded side column; labels wrap at
		# its width while the module remains vertically scrollable.
		var row_parent: Container = section
		if role == "view_orient":
			row_parent = VBoxContainer.new()
			row_parent.name = "LookRow"
			row_parent.mouse_filter = Control.MOUSE_FILTER_IGNORE
			row_parent.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_3)
			section.add_child(row_parent)
		for item in group.get("items", []):
			var semantic := _semantic_row(role, item)
			var plane := str(semantic["operation"])
			var exact := role == "view_exact"
			var operation := str(LivePieceControlStripScript.ROTATION_WORDS.get(plane, plane)) if exact else plane
			var row := PassiveControlComponentsScript.key_first_row(operation, str(semantic["binding"]), role, key_column if exact else 0.0)
			(row.get_node("LegendOperation") as Label).text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
			(row.get_node("LegendOperation") as Label).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			if exact:
				var glyph := ControlLegendGlyphScript.plane(Array(plane.to_lower().split("")), row.get_node("LegendKeys").get_child(0) as Label)
				glyph.name = "LegendPlaneGlyph__%s" % plane
				glyph.set_directions(_screen_directions)
				row.add_child(glyph)
				row.move_child(glyph, 1)
				_glyphs.append(glyph)
			row_parent.add_child(row)
		_wide_box.add_child(section)


func _section_title(role: String) -> String:
	return str({
		"view_exact": "EXACT ROTATE VIEW",
		"view_orient": "LOOK",
		"view_framing": "FRAMING",
		"view_pointer": "POINTER",
	}.get(role, role.to_upper()))


func _semantic_row(role: String, item: Array) -> Dictionary:
	var metadata := _item_metadata(item)
	return {
		"role": role,
		"operation": str(metadata.get("operation", _operation_label(item))),
		"binding": str(item[0]),
		"source_label": str(item[1]),
		"semantic": metadata,
	}


func _operation_label(item: Array) -> String:
	var label := str(item[1])
	for suffix in [" - / + (re-slice)", " - / +", " up / down", " left / right", " out / in", " (framing only)"]:
		if label.ends_with(suffix):
			return label.trim_suffix(suffix)
	return label


func _item_metadata(item: Array) -> Dictionary:
	if item.size() < 3 or not (item[2] is Dictionary):
		return {}
	return item[2].duplicate(true)
