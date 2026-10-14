extends RefCounted

# The grid is one board lattice of maximal lines, never per-cell edges. These
# structural assertions sit underneath the renderer so that no implementation
# can reproduce the image from thousands of cell-edge fragments.

const GeometryScript = preload("res://scripts/presentation/local_board_presentation_geometry.gd")
const GridDisplayMode = preload("res://scripts/presentation/grid_display_mode.gd")

const SHAPES := [[1, 1, 1], [4, 4, 10], [3, 4, 2], [4, 6, 1], [4, 7, 11], [12, 16, 12]]


func run() -> Array:
	var failures: Array = []
	for shape in SHAPES:
		_test_shape(failures, shape)
	_test_worked_example(failures)
	_test_line_count_ignores_cell_count(failures)
	_test_mode_sequence(failures)
	return failures


# 12 outer edges plus every boundary-face line: 4(Nx+Ny+Nz).
static func expected_border_count(shape: Array) -> int:
	return 4 * (int(shape[0]) + int(shape[1]) + int(shape[2]))


static func expected_full_count(shape: Array) -> int:
	var nx := int(shape[0]) + 1
	var ny := int(shape[1]) + 1
	var nz := int(shape[2]) + 1
	return ny * nz + nx * nz + nx * ny


func _lines(shape: Array, mode: int) -> Array:
	var geometry := GeometryScript.new()
	geometry.configure(shape, [1, 2, 3])
	return GridDisplayMode.select_lines(geometry.lattice_geometry(), mode)


func _key(line: Dictionary) -> String:
	return "%d:%s:%s" % [int(line.line_axis), str(line.lattice_start), str(line.lattice_end)]


func _test_shape(failures: Array, shape: Array) -> void:
	var geometry := GeometryScript.new()
	geometry.configure(shape, [1, 2, 3])
	var label := str(shape)
	var border := _lines(shape, GridDisplayMode.Mode.BORDER)
	var full := _lines(shape, GridDisplayMode.Mode.FULL)
	if not _lines(shape, GridDisplayMode.Mode.NONE).is_empty():
		failures.append("%s NONE must emit no grid lines" % label)
	if border.size() != expected_border_count(shape):
		failures.append("%s BORDER must emit %d maximal lines, got %d" % [label, expected_border_count(shape), border.size()])
	if border.filter(func(line: Dictionary) -> bool: return int(line.boundary_planes) == 2).size() != 12:
		failures.append("%s BORDER must contain exactly the 12 outer box edges" % label)
	if full.size() != expected_full_count(shape):
		failures.append("%s FULL must emit %d maximal lines, got %d" % [label, expected_full_count(shape), full.size()])
	var full_keys: Dictionary = {}
	for line in full:
		var key := _key(line)
		if full_keys.has(key):
			failures.append("%s FULL duplicate segment %s" % [label, key])
		full_keys[key] = true
		_assert_maximal(failures, geometry, shape, line, label)
	var border_keys: Dictionary = {}
	for line in border:
		var key := _key(line)
		if border_keys.has(key):
			failures.append("%s BORDER duplicate segment %s" % [label, key])
		border_keys[key] = true
		_assert_maximal(failures, geometry, shape, line, label)
		var axis := int(line.line_axis)
		var on_boundary := 0
		for fixed_axis in range(3):
			if fixed_axis != axis and int(line.lattice_start[fixed_axis]) in [0, int(shape[fixed_axis])]:
				on_boundary += 1
		if on_boundary == 0 or on_boundary != int(line.boundary_planes):
			failures.append("%s BORDER line %s must lie on the board surface" % [label, key])
		if on_boundary == 1:
			var face_axis := int(line.get("face_axis", -1))
			var face_sign := float(line.get("face_sign", 0.0))
			var face_value := 0 if face_sign < 0.0 else int(shape[face_axis]) if face_axis >= 0 else -1
			# Board y grows downward, so local +Y is lattice y = 0.
			if face_axis == Vector3.AXIS_Y:
				face_value = int(shape[1]) - face_value
			if face_axis < 0 or face_axis == axis or face_sign == 0.0 or int(line.lattice_start[face_axis]) != face_value:
				failures.append("%s face line %s must name the one face it lies on" % [label, key])
		if not full_keys.has(key):
			failures.append("%s BORDER line %s must also belong to FULL" % [label, key])
	var nontrivial := int(shape[0]) > 1 or int(shape[1]) > 1 or int(shape[2]) > 1
	if nontrivial and full.size() <= border.size():
		failures.append("%s BORDER must be a strict subset of FULL" % label)
	if geometry.boundary_geometry().size() != 12:
		failures.append("%s boundary geometry must reuse the 12 lattice edges" % label)


# Every emitted line spans one complete board axis. This invariant alone rules
# out per-cell rendering, whatever image it would produce.
func _assert_maximal(failures: Array, geometry, shape: Array, line: Dictionary, label: String) -> void:
	var axis := int(line.line_axis)
	var lattice_start: Vector3i = line.lattice_start
	var lattice_end: Vector3i = line.lattice_end
	for other in range(3):
		if other != axis and lattice_start[other] != lattice_end[other]:
			failures.append("%s line %s is not axis-aligned in board coordinates" % [label, _key(line)])
	if lattice_start[axis] != 0 or lattice_end[axis] != int(shape[axis]):
		failures.append("%s line %s must span the entire board axis" % [label, _key(line)])
	var delta: Vector3 = line.end - line.start
	if delta.length() <= 0.0:
		failures.append("%s line %s has zero length" % [label, _key(line)])
	for other in range(3):
		var expected: float = geometry.local_extent[axis] if other == axis else 0.0
		if not is_equal_approx(absf(delta[other]), expected):
			failures.append("%s line %s local extent must match the whole board axis" % [label, _key(line)])
	var bounds: Dictionary = geometry.local_bounds()
	for point in [line.start, line.end]:
		for other in range(3):
			if point[other] < bounds.min[other] - 0.0001 or point[other] > bounds.max[other] + 0.0001:
				failures.append("%s line %s leaves the board volume" % [label, _key(line)])


func _test_worked_example(failures: Array) -> void:
	if _lines([4, 4, 10], GridDisplayMode.Mode.FULL).size() != 135:
		failures.append("a 4x4x10 board FULL lattice must be exactly 135 maximal lines")


# Grid generation must not scale with the number of cell edges.
func _test_line_count_ignores_cell_count(failures: Array) -> void:
	var short := [4, 4, 10]
	var tall := [4, 4, 20]
	var short_lines := _lines(short, GridDisplayMode.Mode.FULL).size()
	var tall_lines := _lines(tall, GridDisplayMode.Mode.FULL).size()
	# Only the (Nx+1)(Nz+1) + (Ny+1)(Nz+1) families grow with height: 2 * 5 * 10.
	if tall_lines - short_lines != 100:
		failures.append("doubling height must add exactly 100 maximal lines, added %d" % (tall_lines - short_lines))
	if _lines(tall, GridDisplayMode.Mode.BORDER).size() - _lines(short, GridDisplayMode.Mode.BORDER).size() != 40:
		failures.append("doubling height must add exactly 4 * 10 BORDER face lines")
	var unit_edges := 4 * 5 * 21 + 4 * 5 * 21 + 20 * 5 * 5
	if tall_lines * 4 >= unit_edges:
		failures.append("FULL lattice must stay far below the %d per-cell unit edges" % unit_edges)


func _test_mode_sequence(failures: Array) -> void:
	var shape := [4, 7, 11]
	var counts: Array = []
	for mode in [GridDisplayMode.Mode.NONE, GridDisplayMode.Mode.BORDER, GridDisplayMode.Mode.FULL, GridDisplayMode.Mode.NONE]:
		counts.append(_lines(shape, mode).size())
	if counts != [0, expected_border_count(shape), expected_full_count(shape), 0]:
		failures.append("None -> Border -> Full -> None must yield 0/border/full/0 lines, got %s" % str(counts))
