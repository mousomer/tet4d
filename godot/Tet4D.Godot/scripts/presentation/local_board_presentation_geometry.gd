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
	return Vector3(
		float(local_coordinate[0]) - (float(local_dimensions[0]) - 1.0) * 0.5,
		-(float(local_coordinate[1]) - (float(local_dimensions[1]) - 1.0) * 0.5),
		float(local_coordinate[2]) - (float(local_dimensions[2]) - 1.0) * 0.5
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


func boundary_geometry() -> Array:
	if not is_configured():
		return []
	var bounds := local_bounds()
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	var result := []
	for line_axis in range(3):
		var fixed_axes := []
		for axis in range(3):
			if axis != line_axis:
				fixed_axes.append(axis)
		for first_sign in [-1.0, 1.0]:
			for second_sign in [-1.0, 1.0]:
				var start := center
				var finish := center
				start[line_axis] = min_pos[line_axis]
				finish[line_axis] = max_pos[line_axis]
				start[int(fixed_axes[0])] = min_pos[int(fixed_axes[0])] if first_sign < 0.0 else max_pos[int(fixed_axes[0])]
				finish[int(fixed_axes[0])] = start[int(fixed_axes[0])]
				start[int(fixed_axes[1])] = min_pos[int(fixed_axes[1])] if second_sign < 0.0 else max_pos[int(fixed_axes[1])]
				finish[int(fixed_axes[1])] = start[int(fixed_axes[1])]
				result.append({"start": start, "end": finish, "line_axis": line_axis})
	return result


func grid_geometry() -> Array:
	var result := []
	for face_axis in range(3):
		for face_sign in [-1.0, 1.0]:
			result.append({
				"face_axis": face_axis,
				"face_sign": face_sign,
				"normal": _axis_vector(face_axis) * face_sign,
				"segments": face_grid_geometry(face_axis, face_sign),
			})
	return result


func face_grid_geometry(face_axis: int, face_sign: float) -> Array:
	if not is_configured() or face_axis < 0 or face_axis > 2 or face_sign == 0.0:
		return []
	var bounds := local_bounds()
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	var face_coordinate := min_pos[face_axis] if face_sign < 0.0 else max_pos[face_axis]
	var result := []
	for division_axis in range(3):
		if division_axis == face_axis:
			continue
		var line_axis := 3 - face_axis - division_axis
		for division_index in range(1, int(local_dimensions[division_axis])):
			var start := center
			var finish := center
			start[face_axis] = face_coordinate
			finish[face_axis] = face_coordinate
			var division_coordinate := min_pos[division_axis] + float(division_index) * cell_size
			start[division_axis] = division_coordinate
			finish[division_axis] = division_coordinate
			start[line_axis] = min_pos[line_axis]
			finish[line_axis] = max_pos[line_axis]
			result.append({
				"start": start,
				"end": finish,
				"face_axis": face_axis,
				"face_sign": -1.0 if face_sign < 0.0 else 1.0,
				"division_axis": division_axis,
				"line_axis": line_axis,
			})
	return result


func structural_snapshot() -> Dictionary:
	return {
		"local_dimensions": local_dimensions.duplicate(),
		"cell_size": cell_size,
		"local_extent": local_extent,
		"center": center,
		"grid_geometry": grid_geometry(),
		"boundary_geometry": boundary_geometry(),
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


func _axis_vector(axis: int) -> Vector3:
	if axis == Vector3.AXIS_X:
		return Vector3.RIGHT
	if axis == Vector3.AXIS_Y:
		return Vector3.UP
	return Vector3.BACK


func _is_integral_number(value) -> bool:
	if typeof(value) == TYPE_INT:
		return true
	return typeof(value) == TYPE_FLOAT and is_finite(float(value)) and float(value) == float(int(value))
