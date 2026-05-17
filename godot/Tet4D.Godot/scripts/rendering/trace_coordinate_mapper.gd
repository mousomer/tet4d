extends RefCounted

class_name TraceCoordinateMapper

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

var slice_stride := 6.0
var _board_shape: Array = []


func configure(board_shape: Array) -> void:
	_board_shape = board_shape.duplicate()
	var width := float(board_shape[0]) if not board_shape.is_empty() else 4.0
	slice_stride = width + ReplayVisuals.SLICE_PADDING


func world_position(coordinates: Array, dimension: int) -> Vector3:
	if coordinates.is_empty():
		return Vector3.ZERO
	# Mirrors the Python/Pygame raw_to_world display convention: center each
	# board axis around zero and invert Y for screen/world-up rendering.
	var x_size := _axis_size(0)
	var y_size := _axis_size(1)
	var z_size := _axis_size(2)
	var x := float(coordinates[0]) - (x_size - 1.0) * 0.5
	var y := -(float(coordinates[1]) - (y_size - 1.0) * 0.5) if coordinates.size() > 1 else 0.0
	var z := float(coordinates[2]) - (z_size - 1.0) * 0.5 if coordinates.size() > 2 else 0.0
	if dimension >= 4 and coordinates.size() > 3:
		x += w_offset(float(coordinates[3]))
	return Vector3(x, y, z)


func w_offset(w_index: float) -> float:
	return w_index * slice_stride


func slice_bounds(w_index: int = 0) -> Dictionary:
	if _board_shape.is_empty():
		return {"ok": false}
	var x_size := _axis_size(0)
	var y_size := _axis_size(1)
	var z_size := _axis_size(2)
	var x_offset := w_offset(float(w_index))
	var min_pos := Vector3(-x_size * 0.5 + x_offset, -y_size * 0.5, -z_size * 0.5)
	var max_pos := Vector3(x_size * 0.5 + x_offset, y_size * 0.5, z_size * 0.5)
	return {"ok": true, "min": min_pos, "max": max_pos}


func slice_label_position(w_index: int = 0) -> Vector3:
	var bounds := slice_bounds(w_index)
	if not bounds.get("ok", false):
		return Vector3.ZERO
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	return Vector3((min_pos.x + max_pos.x) * 0.5, max_pos.y + 0.9, (min_pos.z + max_pos.z) * 0.5)


func board_bounds(board_shape: Array, dimension: int) -> Dictionary:
	configure(board_shape)
	if _board_shape.is_empty():
		return {"ok": false}
	var first_bounds := slice_bounds(0)
	var w_size := int(_board_shape[3]) if dimension >= 4 and _board_shape.size() > 3 else 1
	var last_bounds := slice_bounds(maxi(w_size - 1, 0))
	var min_pos: Vector3 = first_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = last_bounds.get("max", Vector3.ZERO)
	return {"ok": true, "min": min_pos, "max": max_pos}


func _axis_size(axis: int) -> float:
	if _board_shape.size() > axis:
		return maxf(1.0, float(_board_shape[axis]))
	return 1.0
