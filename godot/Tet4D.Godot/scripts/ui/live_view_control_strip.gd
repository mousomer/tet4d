extends PanelContainer

class_name LiveViewControlStrip

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const PassiveControlComponentsScript = preload("res://scripts/ui/passive_control_components.gd")

var _mode := "live_4d"
var _density := "normal"
var _groups: Array = []
var _groups_box: GridContainer
var _signature := ""
var _source := "LiveInputContract"


func _init() -> void:
	name = "LiveViewControlStrip"
	theme_type_variation = "ViewportFrame"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_meta("semantic_role", "passive_view_guidance")
	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 6)
	add_child(margin)
	var content := VBoxContainer.new()
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_theme_constant_override("separation", 3)
	margin.add_child(content)
	var title := Label.new()
	title.name = "ViewControlTitle"
	title.text = "VIEW"
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", 13)
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(title)
	_groups_box = GridContainer.new()
	_groups_box.name = "ViewControlGroups"
	_groups_box.columns = 2
	_groups_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_groups_box.add_theme_constant_override("h_separation", 10)
	_groups_box.add_theme_constant_override("v_separation", 3)
	content.add_child(_groups_box)


func configure(basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}, density: String = "normal", mode: String = "live_4d", authority = LiveInputContractScript) -> void:
	var groups: Array = authority.view_control_groups(mode, basis_snapshot, control_frame)
	var source := "LiveInputContract" if authority == LiveInputContractScript else "injected_fixture"
	# Provenance is part of the cached identity: an injected fixture that happens
	# to yield identical groups must not keep reporting contract provenance.
	var next_signature := JSON.stringify([mode, density, source, groups])
	if next_signature == _signature:
		return
	_mode = mode
	_density = density
	_groups = groups.duplicate(true)
	_source = source
	_signature = next_signature
	_rebuild()


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
	}


func _rebuild() -> void:
	for child in _groups_box.get_children():
		_groups_box.remove_child(child)
		child.queue_free()
	for group in _groups:
		var role := str(group.get("cockpit_role", ""))
		var section := PassiveControlComponentsScript.section(_section_title(role), role, _density)
		section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		section.custom_minimum_size.x = 225.0
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
