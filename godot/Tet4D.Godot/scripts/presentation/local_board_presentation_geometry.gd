extends RefCounted

class_name LocalBoardPresentationGeometry

const CELL_SIZE := 1.0
const PRESENTATION_DEGENERATE_AXIS := 0

var local_dimensions: Array = []
var axis_mapping: Array = []
var cell_size := CELL_SIZE
var local_extent := Vector3.ZERO
var center := Vector3.ZERO


func configure(dimensions: Array, authoritative_axis_mapping: Array) -> bool:
	local_dimensions.clear()
	axis_mapping.clear()
	local_extent = Vector3.ZERO
	center = Vector3.ZERO
	if dimensions.size() != 3 or authoritative_axis_mapping.size() != 3:
		return false
	for raw_extent in dimensions:
		if not _is_integral_number(raw_extent) or int(raw_extent) < 1:
			return false
		local_dimensions.append(int(raw_extent))
	for raw_axis in authoritative_axis_mapping:
		if typeof(raw_axis) != TYPE_INT:
			return false
		axis_mapping.append(int(raw_axis))
	local_extent = Vector3(
		float(local_dimensions[0]) * cell_size,
		float(local_dimensions[1]) * cell_size,
		float(local_dimensions[2]) * cell_size
	)
	return true


func is_configured() -> bool:
	return local_dimensions.size() == 3 and axis_mapping.size() == 3


func cell_count() -> int:
	if not is_configured():
		return 0
	return int(local_dimensions[0]) * int(local_dimensions[1]) * int(local_dimensions[2])


func cell_transform(local_coordinate: Array, allow_above_board_y: bool = false) -> Transform3D:
	return Transform3D(Basis.IDENTITY, cell_position(local_coordinate, allow_above_board_y))


func cell_position(local_coordinate: Array, allow_above_board_y: bool = false) -> Vector3:
	if not _valid_local_coordinate(local_coordinate, allow_above_board_y):
		return Vector3.ZERO
	return _affine_position(local_coordinate)


func point_position(local_point: Array) -> Vector3:
	if not accepts_point_input(local_point):
		return Vector3.ZERO
	return _affine_position(local_point)


func accepts_point_input(local_point: Array) -> bool:
	if not is_configured() or local_point.size() != 3:
		return false
	for value in local_point:
		if not _is_finite_number(value):
			return false
	return true


func accepts_cell_input(local_coordinate: Array, allow_above_board_y: bool = false) -> bool:
	return _valid_local_coordinate(local_coordinate, allow_above_board_y)


func _affine_position(local_point: Array) -> Vector3:
	return Vector3(
		float(local_point[0]) - (float(local_dimensions[0]) - 1.0) * 0.5,
		-(float(local_point[1]) - (float(local_dimensions[1]) - 1.0) * 0.5),
		float(local_point[2]) - (float(local_dimensions[2]) - 1.0) * 0.5
	) * cell_size


func cell_bounds(local_coordinate: Array, allow_above_board_y: bool = false) -> Dictionary:
	if not _valid_local_coordinate(local_coordinate, allow_above_board_y):
		return {"ok": false}
	var position := cell_position(local_coordinate, allow_above_board_y)
	var half_cell := Vector3.ONE * cell_size * 0.5
	return {"ok": true, "min": position - half_cell, "max": position + half_cell}


func local_bounds() -> Dictionary:
	if not is_configured():
		return {"ok": false}
	var half_extent := local_extent * 0.5
	return {"ok": true, "min": center - half_extent, "max": center + half_extent}


# The board is one rectangular lattice. For each lattice coordinate pair on two
# axes, emit one maximal line spanning the whole remaining axis; never per-cell
# edges. A line's class is the number of boundary planes it lies on: 2 marks the
# 12 outer edges, 1 a boundary-face line (tagged with its face), 0 a
# volume-interior line. Total count
# is (Ny+1)(Nz+1) + (Nx+1)(Nz+1) + (Nx+1)(Ny+1), independent of cell count.
func lattice_geometry() -> Array:
	var result: Array = []
	if not is_configured():
		return result
	for line_axis in range(3):
		var a := (line_axis + 1) % 3
		var b := (line_axis + 2) % 3
		for i in range(int(local_dimensions[a]) + 1):
			for j in range(int(local_dimensions[b]) + 1):
				var lattice_start := Vector3i.ZERO
				lattice_start[a] = i
				lattice_start[b] = j
				var lattice_end := lattice_start
				lattice_end[line_axis] = int(local_dimensions[line_axis])
				var line := {
					"start": _lattice_point_position(lattice_start),
					"end": _lattice_point_position(lattice_end),
					"line_axis": line_axis,
					"lattice_start": lattice_start,
					"lattice_end": lattice_end,
					"boundary_planes": int(i == 0 or i == int(local_dimensions[a])) + int(j == 0 or j == int(local_dimensions[b])),
				}
				if int(line.boundary_planes) == 1:
					# A face line lies on exactly one boundary plane: that face owns it.
					var face_axis := a if i == 0 or i == int(local_dimensions[a]) else b
					line["face_axis"] = face_axis
					line["face_sign"] = signf(line.start[face_axis] - center[face_axis])
				result.append(line)
	return result


func boundary_geometry() -> Array:
	return lattice_geometry().filter(func(line: Dictionary) -> bool: return int(line.boundary_planes) == 2)


# Lattice points sit on cell corners: board point p maps like cell center p - 0.5.
func _lattice_point_position(lattice_point: Vector3i) -> Vector3:
	return _affine_position([lattice_point.x - 0.5, lattice_point.y - 0.5, lattice_point.z - 0.5])


# Dimensions and cell size determine every generated line, so the cache key
# never regenerates geometry.
func structural_snapshot() -> Dictionary:
	return {
		"local_dimensions": local_dimensions.duplicate(),
		"cell_size": cell_size,
		"scaffold_cell_count": cell_count(),
		"local_extent": local_extent,
		"center": center,
	}


func snapshot() -> Dictionary:
	var result := structural_snapshot()
	result["axis_mapping"] = axis_mapping.duplicate()
	return result


func _valid_local_coordinate(local_coordinate: Array, allow_above_board_y: bool) -> bool:
	if not is_configured() or local_coordinate.size() != 3:
		return false
	for axis in range(3):
		var value = local_coordinate[axis]
		if not _is_integral_number(value):
			return false
		var coordinate := int(value)
		if coordinate >= int(local_dimensions[axis]):
			return false
		if coordinate < 0 and not (allow_above_board_y and axis == Vector3.AXIS_Y):
			return false
	return true


func _is_integral_number(value) -> bool:
	if typeof(value) == TYPE_INT:
		return true
	return typeof(value) == TYPE_FLOAT and is_finite(float(value)) and float(value) == float(int(value))


func _is_finite_number(value) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value))
