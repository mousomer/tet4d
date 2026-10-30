extends Node

const PanelFrame = preload("res://scripts/ui/designer_panel_frame.gd")
signal geometry_changed(rects: Dictionary)

var _host: Control
var _frames: Dictionary = {}
var _origins: Dictionary = {}
var _rects: Dictionary = {}
var _active := false
var _revision := 0
var _stage: Control
var _deck: Control
var _stage_visible := false
var _deck_visible := false


func active() -> bool:
	return _active


func revision() -> int:
	return _revision


func surface_rect() -> Rect2:
	return _host.get_global_rect() if _active and is_instance_valid(_host) else Rect2()


func panels() -> Dictionary:
	return _frames.duplicate()


func set_restored_deck_visibility(enabled: bool) -> void:
	_deck_visible = enabled


func open(owner_surface: Control, stage: Control, deck: Control, entries: Array) -> void:
	if _active:
		return
	_revision += 1
	_active = true
	_stage = stage
	_deck = deck
	_stage_visible = stage.visible
	_deck_visible = deck.visible
	_host = Control.new()
	_host.name = "DesignerCockpitSurface"
	_host.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	owner_surface.add_child(_host)
	var generation := _revision
	_host.resized.connect(_constrain_generation.bind(generation))
	# Capture all original indices before removing any sibling.
	for entry in entries:
		var panel: Control = entry[1]
		_origins[str(panel.name)] = {"parent": panel.get_parent(), "index": panel.get_index(),
			"visible": panel.visible, "horizontal": panel.size_flags_horizontal,
			"vertical": panel.size_flags_vertical, "ratio": panel.size_flags_stretch_ratio}
	for entry in entries:
		var panel: Control = entry[1]
		var key := str(panel.name)
		var frame = PanelFrame.new()
		_host.add_child(frame)
		frame.configure(str(entry[0]), panel, bool(entry[2]))
		panel.show()
		frame.geometry_edited.connect(func(rect: Rect2) -> void:
			if _active and generation == _revision:
				_rects[key] = rect
				geometry_changed.emit(geometry_snapshot())
		)
		_frames[key] = frame
	stage.hide()
	deck.hide()
	_constrain_generation.call_deferred(generation)


func close() -> void:
	if not _active:
		return
	_active = false
	_revision += 1
	for key in _frames:
		var frame = _frames[key]
		_rects[key] = Rect2(frame.position, frame.size)
		# Restore layout modes synchronously. Queued destruction of an old
		# frame must not reset the controls of a newly opened session.
		frame.release_content()
		var origin: Dictionary = _origins[key]
		frame.content.reparent(origin["parent"], false)
		frame.content.visible = origin["visible"]
		frame.content.size_flags_horizontal = origin["horizontal"]
		frame.content.size_flags_vertical = origin["vertical"]
		frame.content.size_flags_stretch_ratio = origin["ratio"]
	var keys: Array = _origins.keys()
	keys.sort_custom(func(a, b) -> bool:
		var first: Dictionary = _origins[a]
		var second: Dictionary = _origins[b]
		if first["parent"] == second["parent"]:
			return int(first["index"]) < int(second["index"])
		return first["parent"].get_instance_id() < second["parent"].get_instance_id()
	)
	for key in keys:
		var origin: Dictionary = _origins[key]
		origin["parent"].move_child(_frames[key].content, mini(origin["index"], origin["parent"].get_child_count() - 1))
	var previous := _host
	_host = null
	_frames.clear()
	_origins.clear()
	_stage.visible = _stage_visible
	_deck.visible = _deck_visible
	previous.get_parent().remove_child(previous)
	previous.queue_free()


func geometry_snapshot() -> Dictionary:
	var result: Dictionary = {}
	for key in _rects:
		var rect: Rect2 = _rects[key]
		result[key] = [rect.position.x, rect.position.y, rect.size.x, rect.size.y]
	return result


func restore_geometry(rects: Dictionary) -> void:
	_rects.clear()
	for key in rects:
		var data: Array = rects[key]
		_rects[key] = Rect2(float(data[0]), float(data[1]), float(data[2]), float(data[3]))
	constrain()


func raise_panel(panel_name: String) -> void:
	if _active and _frames.has(panel_name):
		_host.move_child(_frames[panel_name], _host.get_child_count() - 1)


func _constrain_generation(generation: int) -> void:
	if generation == _revision:
		constrain()


func constrain() -> void:
	if not _active or _host == null or _host.size.x < 1:
		return
	var extent := _host.size
	var index := 0
	for key in _frames:
		var frame = _frames[key]
		var gap := 8.0
		var half_width := (extent.x - gap) * 0.65
		var right_origin := half_width + gap
		var column_width := extent.x - right_origin
		var row_height := (extent.y - gap * 2) / 3.0
		var initial := Rect2(Vector2.ZERO, Vector2(half_width, extent.y))
		if index > 0:
			initial = Rect2(Vector2(right_origin, (row_height + gap) * float(index - 1)), Vector2(column_width, row_height))
		frame.constrain(_rects.get(key, initial))
		_rects[key] = Rect2(frame.position, frame.size)
		index += 1
