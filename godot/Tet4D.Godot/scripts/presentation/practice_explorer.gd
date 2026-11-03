extends RefCounted

# Detached native-query results. This adapter never implements geometry or
# topology rules and never advances the configured gameplay session.
const AXES := "xyzw"
var _bridge
var _template: Dictionary = {}
var _initial: Array = []
var cells: Array = []
var selected_cell := 0
var target: Array = []
var feedback := "Object ready. No gravity."
var revision := 0
var _catalog: Array = []
var selected_piece := -1
var _target_count := 0


func _init(bridge) -> void:
	_bridge = bridge


# tet4d-semantic-boundary: allow adapter-routing
func begin(snapshot: Dictionary) -> bool:
	# JSON snapshots carry numbers as floats; the native typed boundary requires
	# integer lattice coordinates. Conversion supplies no geometry semantics.
	var shape: Array = snapshot.get("board_shape", []).map(func(value): return int(value))
	if shape.size() not in [3, 4]:
		return false
	var source: Array = []
	for cell in snapshot.get("active_cells", []):
		source.append(cell.get("position", []).map(func(value): return int(value)))
	if source.is_empty():
		return false
	var candidate: Array = _centered_cells(source, shape)
	if not _bridge.native_piece_pose_diagnostic(shape, candidate).get("legal", false):
		return false
	_template = snapshot.duplicate(true)
	_template["board_shape"] = shape
	_initial = candidate.duplicate(true)
	cells = candidate.duplicate(true)
	selected_cell = 0
	target = []
	_target_count = 0
	feedback = "Object ready · no gravity."
	revision = 0
	_catalog = _bridge.live_nd_production_piece_catalog().filter(func(piece): return int(piece.get("dimension", 0)) == shape.size() and str(piece.get("piece_set_id", "")) == str(snapshot.get("piece_set_id", "")))
	selected_piece = -1
	for index in _catalog.size():
		if str(_catalog[index].get("piece_name", "")) == str(snapshot.get("current_piece", "")):
			selected_piece = index
	return true


func _centered_cells(source: Array, shape: Array) -> Array:
	var center: Array = []
	for extent in shape:
		# Request the lower central cell, matching native normalization's
		# integer pivot so an even-width piece can fit an exact-width board.
		center.append((int(extent) - 1) / 2)
	return _bridge.geometry_translate_blocks(_bridge.geometry_normalize_blocks(source), center)


func piece_names() -> Array:
	return _catalog.map(func(piece): return str(piece.get("piece_name", "")))


# tet4d-semantic-boundary: allow adapter-routing
func replace_piece(index: int) -> bool:
	if index < 0 or index >= _catalog.size():
		feedback = "Piece choice unavailable. Object unchanged."
		return false
	var piece: Dictionary = _catalog[index]
	var candidate := _centered_cells(piece.cells, _template.board_shape)
	var result: Dictionary = _bridge.native_piece_pose_diagnostic(_template.board_shape, candidate)
	if candidate.is_empty() or not result.get("legal", false):
		feedback = "This piece does not fit the board. Object unchanged."
		return false
	cells = candidate.duplicate(true)
	_initial = candidate.duplicate(true)
	selected_cell = 0
	selected_piece = index
	_template["current_piece"] = piece.piece_name
	_template["current_piece_color_id"] = piece.color_id
	revision += 1
	feedback = "Replaced piece: %s. View unchanged." % piece.piece_name
	return true


func replace_next_piece() -> bool:
	return replace_piece(posmod(selected_piece + 1, _catalog.size())) if not _catalog.is_empty() else replace_piece(-1)


func dimension() -> int:
	return _template.get("board_shape", []).size()


# tet4d-semantic-boundary: allow adapter-routing
func command(command_name: String) -> bool:
	var parts := command_name.split("_")
	if parts.size() != 3 or parts[2] not in ["neg", "pos"]:
		feedback = "Practice has no gravity, drop, lock or hold. Use deliberate moves."
		return false
	var direction := -1 if parts[2] == "neg" else 1
	var candidate: Array = []
	if parts[0] == "move" and parts[1].length() == 1:
		var axis := AXES.find(parts[1])
		if axis < 0 or axis >= dimension():
			return false
		var offset: Array = []
		offset.resize(dimension())
		offset.fill(0)
		offset[axis] = direction
		candidate = _bridge.geometry_translate_blocks(cells, offset)
	elif parts[0] == "rotate" and parts[1].length() == 2:
		var a := AXES.find(parts[1][0])
		var b := AXES.find(parts[1][1])
		if a < 0 or b < 0 or a == b or a >= dimension() or b >= dimension():
			return false
		candidate = _bridge.geometry_rotate_blocks(cells, a, b, direction)
	else:
		return false
	var check: Dictionary = _bridge.native_piece_pose_diagnostic(_template.board_shape, candidate)
	if candidate.is_empty() or not check.get("legal", false):
		feedback = "Object unchanged: %s." % str(check.get("reason", "blocked")).replace("_", " ")
		return false
	cells = candidate.duplicate(true)
	revision += 1
	feedback = "%s %s %s. View unchanged." % ["Moved" if parts[0] == "move" else "Rotated", parts[1].to_upper(), "−" if direction < 0 else "+"]
	return true


func retry() -> void:
	cells = _initial.duplicate(true)
	selected_cell = 0
	revision += 1
	feedback = "Object restored exactly. View unchanged."


func select_next_cell() -> void:
	selected_cell = posmod(selected_cell + 1, cells.size())


# tet4d-semantic-boundary: allow adapter-routing
func place_target() -> bool:
	# A target is the anchor cell of a native-legal translated pose, so the pose
	# query alone decides reachability. Each axis seeks up to a third of its
	# extent; successive targets flip direction so both signs, Y included, get
	# practiced.
	var shape: Array = _template.board_shape
	var offset: Array = []
	offset.resize(dimension())
	offset.fill(0)
	for axis in dimension():
		var preferred := 1 if (axis + _target_count) % 2 == 0 else -1
		var reach := maxi(1, int(shape[axis]) / 3)
		var found := false
		for direction in [preferred, -preferred]:
			for step in range(reach, 0, -1):
				offset[axis] = direction * step
				if _bridge.native_piece_pose_diagnostic(shape, _bridge.geometry_translate_blocks(cells, offset)).get("legal", false):
					found = true
					break
			if found:
				break
		if not found:
			offset[axis] = 0
	var candidate: Array = _bridge.geometry_translate_blocks(cells, offset)
	if candidate.is_empty() or candidate[0] in cells or not _bridge.native_piece_pose_diagnostic(shape, candidate).get("legal", false):
		feedback = "Target unavailable on this board. Object unchanged."
		return false
	target = candidate[0].duplicate()
	_target_count += 1
	feedback = "Target marked. Move the piece onto it."
	return true


# tet4d-semantic-boundary: allow adapter-routing
func neighbors() -> Array:
	var result: Array = []
	for axis in dimension():
		for direction in [-1, 1]:
			var step: Dictionary = _bridge.query_topology_axis_wrap_cell_step(_template.board_shape, [], cells[selected_cell], axis, direction)
			result.append({"label": "%s%s" % ["+" if direction > 0 else "−", AXES[axis].to_upper()], "target": step.get("target")})
	return result


func snapshot(show_neighbors: bool, hidden_axis: int, inspected_slice: int) -> Dictionary:
	var result := _template.duplicate(true)
	result["case_id"] = "practice_%dd" % dimension()
	result["state_hash"] = ""
	result["frame_index"] = revision
	result["last_command"] = feedback
	result["last_command_status"] = "practice"
	result["metadata_lines"] = ["Explorer Sandbox · native query results · no gameplay/replay identity", feedback]
	result["diagnostics_lines"] = []
	result["event_lines"] = []
	result["active_cells"] = []
	result["locked_cells"] = []
	result["ghost_cells"] = []
	result["probe_markers"] = []
	for coord in cells:
		result.active_cells.append({"position": coord.duplicate(), "color_id": _template.get("current_piece_color_id", 1)})
	if not target.is_empty():
		result.probe_markers.append({"position": target.duplicate(), "kind": "probe_after", "presentation_role": "lesson_target"})
	if show_neighbors:
		for neighbor in neighbors():
			if neighbor.target is Array:
				result.probe_markers.append({"position": neighbor.target.duplicate(), "kind": "probe_before"})
	# A negative slice follows the object like ordinary Play.
	if dimension() == 4 and inspected_slice >= 0:
		result["inspected_slice"] = {"axis": hidden_axis, "coordinate": inspected_slice}
	result["practice"] = true
	return result
