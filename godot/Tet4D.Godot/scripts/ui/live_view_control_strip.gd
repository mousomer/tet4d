extends PanelContainer

class_name LiveViewControlStrip

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")

var _groups: Array = []
var _groups_box: VBoxContainer


func _init() -> void:
	name = "LiveViewControlStrip"
	theme_type_variation = "ViewportFrame"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_meta("semantic_role", "passive_view_guidance")
	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 6)
	add_child(margin)
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 3)
	margin.add_child(content)
	var title := Label.new()
	title.text = "VIEW"
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", 13)
	content.add_child(title)
	_groups_box = VBoxContainer.new()
	_groups_box.add_theme_constant_override("separation", 3)
	content.add_child(_groups_box)


func configure(basis_snapshot: Dictionary = {}, control_frame: Dictionary = {}) -> void:
	var groups := LiveInputContractScript.view_control_groups("live_4d", basis_snapshot, control_frame)
	if JSON.stringify(groups) == JSON.stringify(_groups):
		return
	_groups = groups.duplicate(true)
	for child in _groups_box.get_children():
		child.queue_free()
	for group in _groups:
		_groups_box.add_child(_build_group(group))


func deterministic_snapshot() -> Dictionary:
	return {"source": "LiveInputContract", "roles": _groups.map(func(group): return str(group.get("cockpit_role", ""))), "groups": _groups.duplicate(true), "rect": get_global_rect(), "visible": visible}


func _build_group(group: Dictionary) -> Control:
	var box := VBoxContainer.new()
	box.name = "ViewControlGroup__%s" % str(group.get("cockpit_role", ""))
	var heading := Label.new()
	heading.text = str(group.get("group", ""))
	heading.theme_type_variation = "SecondaryLabel"
	heading.add_theme_font_size_override("font_size", 11)
	box.add_child(heading)
	var flow := HFlowContainer.new()
	flow.add_theme_constant_override("h_separation", 5)
	flow.add_theme_constant_override("v_separation", 2)
	box.add_child(flow)
	for item in group.get("items", []):
		var row := Label.new()
		row.text = "%s  %s" % [str(item[0]), str(item[1])]
		row.theme_type_variation = "DimLabel"
		row.add_theme_font_size_override("font_size", 11)
		flow.add_child(row)
	return box
