extends RefCounted

class_name TraceCoordinateMapper

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const AdaptiveLayerLayoutScript = preload("res://scripts/presentation/adaptive_layer_layout.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")

var slice_stride := 6.0
var _board_shape: Array = []
var _visible_board_shape: Array = []
var _basis = SliceBasis4DScript.identity()
var layer_layout = AdaptiveLayerLayoutScript.new()


func configure(board_shape: Array, basis = null) -> void:
	_board_shape = board_shape.duplicate()
	_basis = basis if basis != null else SliceBasis4DScript.identity()
	_visible_board_shape = _basis.visible_dimensions(_board_shape) if _board_shape.size() == 4 else _board_shape.duplicate()
	var width := float(_visible_board_shape[0]) if not _visible_board_shape.is_empty() else 4.0
	slice_stride = width + ReplayVisuals.SLICE_PADDING
	var height := float(_visible_board_shape[1]) if _visible_board_shape.size() > 1 else 4.0
	layer_layout.configure(current_layer_count(), width, height)


func world_position(coordinates: Array, dimension: int) -> Vector3:
	if coordinates.is_empty():
		return Vector3.ZERO
	var visible_coordinates := coordinates
	var layer_index := 0
	if dimension >= 4 and coordinates.size() > 3:
		var mapped: Dictionary = _basis.presentation_coordinate(coordinates, _board_shape)
		if not bool(mapped.get("ok", false)):
			return Vector3.ZERO
		visible_coordinates = mapped.get("visible_cell_3d", [])
		layer_index = int(mapped.get("layer_index", 0))
	# Mirrors the Python/Pygame raw_to_world display convention: center each
	# board axis around zero and invert Y for screen/world-up rendering.
	var x_size := _axis_size(0)
	var y_size := _axis_size(1)
	var z_size := _axis_size(2)
	var x := float(visible_coordinates[0]) - (x_size - 1.0) * 0.5
	var y := -(float(visible_coordinates[1]) - (y_size - 1.0) * 0.5) if visible_coordinates.size() > 1 else 0.0
	var z := float(visible_coordinates[2]) - (z_size - 1.0) * 0.5 if visible_coordinates.size() > 2 else 0.0
	if dimension >= 4 and coordinates.size() > 3:
		return Vector3(x, y, z) + slice_offset(layer_index)
	return Vector3(x, y, z)


func w_offset(w_index: float) -> float:
	return slice_offset(int(round(w_index))).x


func slice_offset(w_index: int) -> Vector3:
	return layer_layout.offset_for_layer(w_index)


func slice_bounds(w_index: int = 0) -> Dictionary:
	if _board_shape.is_empty():
		return {"ok": false}
	var x_size := _axis_size(0)
	var y_size := _axis_size(1)
	var z_size := _axis_size(2)
	var offset := slice_offset(w_index)
	var min_pos := Vector3(-x_size * 0.5, -y_size * 0.5, -z_size * 0.5) + offset
	var max_pos := Vector3(x_size * 0.5, y_size * 0.5, z_size * 0.5) + offset
	return {"ok": true, "min": min_pos, "max": max_pos}


func slice_label_position(w_index: int = 0) -> Vector3:
	var bounds := slice_bounds(w_index)
	if not bounds.get("ok", false):
		return Vector3.ZERO
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	return Vector3(
		min_pos.x + ReplayVisuals.W_SLICE_LABEL_EDGE_OFFSET,
		max_pos.y + ReplayVisuals.W_SLICE_LABEL_VERTICAL_OFFSET,
		min_pos.z + ReplayVisuals.W_SLICE_LABEL_EDGE_OFFSET
	)


func board_bounds(board_shape: Array, dimension: int, basis = null) -> Dictionary:
	configure(board_shape, basis)
	if _board_shape.is_empty():
		return {"ok": false}
	var w_size := current_layer_count() if dimension >= 4 else 1
	var first_bounds := slice_bounds(0)
	var min_pos: Vector3 = first_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = first_bounds.get("max", Vector3.ZERO)
	for layer_index in range(1, w_size):
		var layer_bounds := slice_bounds(layer_index)
		var layer_min: Vector3 = layer_bounds.get("min", min_pos)
		var layer_max: Vector3 = layer_bounds.get("max", max_pos)
		min_pos = Vector3(minf(min_pos.x, layer_min.x), minf(min_pos.y, layer_min.y), minf(min_pos.z, layer_min.z))
		max_pos = Vector3(maxf(max_pos.x, layer_max.x), maxf(max_pos.y, layer_max.y), maxf(max_pos.z, layer_max.z))
	if dimension >= 4:
		max_pos.y += ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
	return {"ok": true, "min": min_pos, "max": max_pos}


func _axis_size(axis: int) -> float:
	if _visible_board_shape.size() > axis:
		return maxf(1.0, float(_visible_board_shape[axis]))
	return 1.0


func visible_board_shape() -> Array:
	return _visible_board_shape.duplicate()


func current_layer_count() -> int:
	return _basis.layer_count(_board_shape) if _board_shape.size() == 4 else 1


func slice_axis_label() -> String:
	return _basis.slice_axis_label() if _board_shape.size() == 4 else "+W"


func semantic_slice_coordinate(layer_index: int) -> int:
	return _basis.semantic_slice_coordinate(layer_index, _board_shape) if _board_shape.size() == 4 else layer_index


func basis_key() -> String:
	return _basis.key()


func presentation_coordinate(canonical_coordinate: Array) -> Dictionary:
	return _basis.presentation_coordinate(canonical_coordinate, _board_shape)
