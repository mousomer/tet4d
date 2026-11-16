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
var topology := "bounded"
var domains: Array = []
var frames: Array = []
var _display_cells: Array = []
var _display_shape: Array = []
var _pristine := true
var _chart_origins: Array = []
var _seams: Array = []


func _init(bridge) -> void:
	_bridge = bridge


# tet4d-semantic-boundary: allow adapter-routing
func begin(snapshot: Dictionary) -> bool:
	# JSON snapshots carry numbers as floats; the native typed boundary requires
	# integer lattice coordinates. Conversion supplies no geometry semantics.
	var shape: Array = snapshot.get("board_shape", []).map(func(value): return int(value))
	if shape.size() not in [2, 3, 4]:
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
	var catalog: Array = _bridge.live_2d_production_piece_catalog() if shape.size() == 2 else _bridge.live_nd_production_piece_catalog()
	_catalog = catalog.filter(func(piece): return int(piece.get("dimension", 0)) == shape.size() and str(piece.get("piece_set_id", "")) == str(snapshot.get("piece_set_id", "")))
	topology = "bounded"
	_seams = []
	domains = []
	frames = []
	_display_cells = []
	_display_shape = []
	_pristine = true
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
	if topology != "bounded":
		var admitted: Dictionary = _bridge.explorer_begin(_template.board_shape, candidate, candidate, topology)
		if not admitted.get("ok", false):
			feedback = "Object unchanged: " + str(admitted.get("reason", "unavailable"))
			return false
		_accept_transport(admitted)
		candidate = admitted.cells
	cells = candidate.duplicate(true)
	_initial = candidate.duplicate(true)
	_pristine = true
	selected_cell = 0
	selected_piece = index
	_template["current_piece"] = piece.piece_name
	_template["current_piece_color_id"] = piece.color_id
	revision += 1
	feedback = "Replaced piece: %s. View unchanged." % piece.piece_name
	return true


func square_surface() -> bool:
	return dimension() == 2 and topology in ["sphere_adjacent_positive", "projective"]


func board_shape() -> Array:
	return _template.get("board_shape", []).duplicate()


static func _shape_text(shape: Array) -> String:
	return "×".join(PackedStringArray(shape.map(func(value): return str(int(value)))))


# Restarts the piece on an admitted board; rejected requests preserve the space.
# tet4d-semantic-boundary: allow adapter-routing
func resize_board(shape: Array) -> bool:
	shape = shape.map(func(value): return int(value))
	if shape.size() != dimension() or (square_surface() and shape[0] != shape[1]):
		return false
	var candidate: Array = _centered_cells(_initial, shape)
	if candidate.is_empty() or not _bridge.native_piece_pose_diagnostic(shape, candidate).get("legal", false):
		feedback = "The piece does not fit a %s board. Board unchanged." % _shape_text(shape)
		return false
	if topology != "bounded":
		var admitted: Dictionary = _bridge.explorer_begin(shape, candidate, candidate, topology)
		if admitted.get("ok", false):
			_accept_transport(admitted)
			candidate = admitted.cells
		else:
			feedback = "Object unchanged: this board is unavailable for the selected space."
			return false
	_template["board_shape"] = shape
	cells = candidate.duplicate(true)
	_initial = candidate.duplicate(true)
	_pristine = true
	selected_cell = 0
	target = []
	revision += 1
	feedback = "Board %s. Piece restarted at the centre." % _shape_text(shape)
	return true


func replace_next_piece() -> bool:
	return replace_piece(posmod(selected_piece + 1, _catalog.size())) if not _catalog.is_empty() else replace_piece(-1)


# Native candidate owns transport and destination admission. Profile selection
# recovers the Retry baseline when frames/domains cannot carry across spaces.
# tet4d-semantic-boundary: allow adapter-routing
func select_topology(preset: String, board_minima: Array = [], board_maxima: Array = []) -> bool:
	if dimension() != 2 or preset not in ["bounded", "cylinder_x", "cylinder_y", "torus", "mobius", "klein", "projective", "sphere_adjacent_positive", "sphere_double_2d"]:
		feedback = "Object unchanged: topology unavailable."
		return false
	if preset == topology:
		return true
	var recover := not _pristine and not _plain_pose()
	var candidate: Array = _initial if recover else cells
	if preset in ["sphere_adjacent_positive", "projective"] and _template.board_shape[0] != _template.board_shape[1]:
		return _select_square_surface(preset, board_minima, board_maxima)
	var result: Dictionary = _bridge.explorer_begin(_template.board_shape, _initial, candidate, preset)
	if not result.get("ok", false):
		feedback = "Object unchanged: %s. This is a runtime limitation, not a topology verdict." % str(result.get("reason", "unavailable")).replace("_", " ")
		return false
	topology = preset
	_accept_transport(result)
	_initial = result.initial_cells.duplicate(true)
	revision += 1
	target = []
	feedback = "Space changed. Retry pose restored." if recover else "Topology selected."
	return true


# The single-square Sphere glues each edge to an adjacent one, so the two edges
# must be equally long. Square the board (as large as both axes allow) and
# restart the piece at its centre instead of refusing the space.
func _select_square_surface(preset: String, minima: Array, maxima: Array) -> bool:
	var shape: Array = _template.board_shape
	var side := mini(int(shape[0]), int(shape[1]))
	if minima.size() >= 2 and maxima.size() >= 2:
		side = clampi(side, maxi(int(minima[0]), int(minima[1])), mini(int(maxima[0]), int(maxima[1])))
	var square := [side, side]
	var candidate: Array = _centered_cells(_initial, square)
	if candidate.is_empty() or not _bridge.native_piece_pose_diagnostic(square, candidate).get("legal", false):
		feedback = "Object unchanged: This surface needs a square board and the piece does not fit %s." % _shape_text(square)
		return false
	var result: Dictionary = _bridge.explorer_begin(square, candidate, candidate, preset)
	if not result.get("ok", false):
		feedback = "Object unchanged: %s." % str(result.get("reason", "unavailable")).replace("_", " ")
		return false
	_template["board_shape"] = square
	topology = preset
	_accept_transport(result)
	_initial = result.initial_cells.duplicate(true)
	selected_cell = 0
	revision += 1
	target = []
	feedback = "This surface needs a square board: board set to %s, piece restarted at the centre." % _shape_text(square)
	return true


func _plain_pose() -> bool:
	if topology == "bounded":
		return true
	for domain in domains:
		if int(domain) != 0:
			return false
	for frame in frames:
		if frame.permutation != [0, 1] or frame.signs != [1, 1]:
			return false
	return true


func _accept_transport(result: Dictionary) -> void:
	cells = result.cells.duplicate(true)
	domains = result.domains.duplicate()
	frames = result.frames.duplicate(true)
	_display_cells = result.display_cells.duplicate(true)
	_display_shape = result.display_shape.duplicate()
	_pristine = result.pristine
	_chart_origins = result.chart_origins.duplicate(true)
	_seams = result.seams.duplicate(true)


func topology_note() -> String:
	match topology:
		"mobius": return "Möbius · left/right join with a flip; top/bottom stay open."
		"klein": return "Klein bottle · left/right wrap; top/bottom join with a flip."
		"projective": return "Projective plane · experimental · both edge pairs join with flips."
		"sphere_adjacent_positive": return "Sphere · left joins top, right joins bottom; both preserve tangent direction. A piece can block on itself at the corners."
		"sphere_double_2d": return "Sphere · chart A (left), chart B (right). Matching boundaries join."
	return ""


func dimension() -> int:
	return _template.get("board_shape", []).size()


# tet4d-semantic-boundary: allow adapter-routing
func command(command_name: String) -> bool:
	if command_name == "undo":
		if topology == "bounded":
			feedback = "Undo unavailable in bounded practice. Use Retry."
			return false
		var undone: Dictionary = _bridge.explorer_undo()
		if not undone.get("ok", false):
			feedback = "Object unchanged: Undo unavailable."
			return false
		_accept_transport(undone)
		revision += 1
		feedback = "Undid last object action. View unchanged."
		return true
	var parts := command_name.split("_")
	if parts.size() != 3 or parts[2] not in ["neg", "pos"]:
		feedback = "Practice has no gravity, drop, lock or hold. Use deliberate moves."
		return false
	var direction := -1 if parts[2] == "neg" else 1
	if topology != "bounded":
		var transported: Dictionary
		if parts[0] == "move" and parts[1] in ["x", "y"]:
			transported = _bridge.explorer_move(AXES.find(parts[1]), direction)
		elif parts[0] == "rotate" and parts[1] == "xy":
			transported = _bridge.explorer_rotate(direction)
		else:
			feedback = "Object unchanged: action unavailable."
			return false
		if not transported.get("ok", false):
			feedback = "Object unchanged: %s." % _blocked_reason(str(transported.get("reason", "")))
			return false
		_accept_transport(transported)
		revision += 1
		feedback = "Moved."
		return true
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
	_pristine = cells == _initial
	revision += 1
	feedback = "%s %s %s. View unchanged." % ["Moved" if parts[0] == "move" else "Rotated", parts[1].to_upper(), "−" if direction < 0 else "+"]
	return true


# Native refuses an action only for overlap or an open edge; name those plainly.
func _blocked_reason(reason: String) -> String:
	match reason:
		"destination_collision": return "two cells would land on one cell"
		"unconnected_boundary": return "an open edge blocks the piece"
		"": return "blocked"
	return reason.replace("_", " ")


func retry() -> void:
	if topology != "bounded":
		var result: Dictionary = _bridge.explorer_retry()
		if not result.get("ok", false):
			feedback = "Object unchanged: Retry unavailable."
			return
		_accept_transport(result)
	else:
		cells = _initial.duplicate(true)
		_pristine = true
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
	if topology != "bounded":
		feedback = "Target unavailable for surface practice. Use movement, rotation and Undo."
		return false
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
	if topology != "bounded":
		for neighbor in _bridge.explorer_neighbors(selected_cell).get("neighbors", []):
			result.append({"label": "%s%s" % ["+" if neighbor.direction > 0 else "−", AXES[neighbor.axis].to_upper()], "target": neighbor.get("target"), "domain": neighbor.get("domain"), "display_target": neighbor.get("display_target")})
		return result
	for axis in dimension():
		for direction in [-1, 1]:
			var step: Dictionary = _bridge.query_topology_axis_wrap_cell_step(_template.board_shape, ([0, 1] if topology == "torus" else ([0] if topology == "cylinder_x" else ([1] if topology == "cylinder_y" else []))), cells[selected_cell], axis, direction)
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
	if topology == "sphere_double_2d":
		result["board_shape"] = _display_shape.duplicate()
		result["explorer_charts"] = {"shape": _template.board_shape.duplicate(), "count": 2, "origins": _chart_origins.duplicate(true)}
	for coord in (_display_cells if topology == "sphere_double_2d" else cells):
		result.active_cells.append({"position": coord.duplicate(), "color_id": _template.get("current_piece_color_id", 1)})
	if not target.is_empty():
		result.probe_markers.append({"position": target.duplicate(), "kind": "probe_after", "presentation_role": "lesson_target"})
	if show_neighbors:
		for neighbor in neighbors():
			if neighbor.target is Array:
				result.probe_markers.append({"position": neighbor.get("display_target", neighbor.target).duplicate(), "kind": "probe_before"})
	# A negative slice follows the object like ordinary Play.
	if dimension() == 4 and inspected_slice >= 0:
		result["inspected_slice"] = {"axis": hidden_axis, "coordinate": inspected_slice}
	result["practice"] = true
	result["explorer_topology"] = topology
	result["explorer_seams"] = _seams.duplicate(true)
	result["explorer_topology_note"] = topology_note()
	result["explorer_domains"] = domains.duplicate()
	return result
