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


func configure(board_shape: Array, basis = null, spacing_scale: float = 1.0) -> void:
	_board_shape = board_shape.duplicate()
	_basis = basis if basis != null else SliceBasis4DScript.identity()
	_visible_board_shape = _basis.visible_dimensions(_board_shape) if _board_shape.size() == 4 else _board_shape.duplicate()
	var width := float(_visible_board_shape[0]) if not _visible_board_shape.is_empty() else 4.0
	var height := float(_visible_board_shape[1]) if _visible_board_shape.size() > 1 else 4.0
	layer_layout.configure(current_layer_count(), width, height, 1.7777778, spacing_scale)
	slice_stride = width + layer_layout.horizontal_gap


func unoriented_world_position(coordinates: Array, dimension: int) -> Vector3:
	# Explicit Stage 54E-2a compatibility composition: G_D(p) + anchor_i.
	# Live-4D renderer consumers use ProjectionLayout.oriented_world_position().
	var decomposition := decompose_position(coordinates, dimension)
	return decomposition.get("unoriented_world_point", Vector3.ZERO) if bool(decomposition.get("ok", false)) else Vector3.ZERO


func decompose_position(coordinates: Array, dimension: int, allow_above_board_y: bool = false) -> Dictionary:
	if coordinates.is_empty():
		return {"ok": false}
	var visible_coordinates := coordinates.duplicate()
	var layer_index := 0
	if dimension >= 4 and coordinates.size() > 3:
		var mapped: Dictionary = presentation_coordinate(coordinates, allow_above_board_y)
		if not bool(mapped.get("ok", false)):
			return {"ok": false}
		visible_coordinates = mapped.get("visible_cell_3d", [])
		layer_index = int(mapped.get("layer_index", 0))
	var local_point := centered_local_point(visible_coordinates)
	var anchor := slice_anchor(layer_index) if dimension >= 4 and coordinates.size() > 3 else Vector3.ZERO
	return {
		"ok": true,
		"layer_index": layer_index,
		"visible_cell_3d": visible_coordinates.duplicate(),
		"centered_local_point": local_point,
		"anchor": anchor,
		"unoriented_world_point": compose_anchored_point(local_point, anchor),
	}


func centered_local_point(visible_coordinates: Array) -> Vector3:
	# Mirrors the Python/Pygame raw_to_world display convention: center each
	# board axis around zero and invert Y for screen/world-up rendering. This is
	# the affine point mapping G_D; displacement vectors must use differences of
	# two mapped points rather than entering this function directly.
	if visible_coordinates.is_empty():
		return Vector3.ZERO
	var x_size := _axis_size(0)
	var y_size := _axis_size(1)
	var z_size := _axis_size(2)
	var x := float(visible_coordinates[0]) - (x_size - 1.0) * 0.5
	var y := -(float(visible_coordinates[1]) - (y_size - 1.0) * 0.5) if visible_coordinates.size() > 1 else 0.0
	var z := float(visible_coordinates[2]) - (z_size - 1.0) * 0.5 if visible_coordinates.size() > 2 else 0.0
	return Vector3(x, y, z)


func compose_anchored_point(centered_local_point_value: Vector3, anchor: Vector3) -> Vector3:
	return centered_local_point_value + anchor


func w_offset(w_index: float) -> float:
	return slice_anchor(int(round(w_index))).x


func slice_anchor(layer_index: int) -> Vector3:
	return layer_layout.anchor_for_layer(layer_index)


func slice_offset(w_index: int) -> Vector3:
	# Compatibility alias retained for renderer/layout consumers until 54E-2b.
	return slice_anchor(w_index)


func local_slice_bounds() -> Dictionary:
	if _board_shape.is_empty():
		return {"ok": false}
	var x_size := _axis_size(0)
	var y_size := _axis_size(1)
	var z_size := _axis_size(2)
	return {
		"ok": true,
		"min": Vector3(-x_size * 0.5, -y_size * 0.5, -z_size * 0.5),
		"max": Vector3(x_size * 0.5, y_size * 0.5, z_size * 0.5),
	}


func unoriented_slice_bounds(w_index: int = 0) -> Dictionary:
	var local_bounds := local_slice_bounds()
	if not local_bounds.get("ok", false):
		return {"ok": false}
	var anchor := slice_anchor(w_index)
	var min_pos: Vector3 = local_bounds.get("min", Vector3.ZERO) + anchor
	var max_pos: Vector3 = local_bounds.get("max", Vector3.ZERO) + anchor
	return {"ok": true, "min": min_pos, "max": max_pos}


func slice_label_position(w_index: int = 0) -> Vector3:
	var bounds := unoriented_slice_bounds(w_index)
	if not bounds.get("ok", false):
		return Vector3.ZERO
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	return Vector3(
		min_pos.x - ReplayVisuals.W_SLICE_LABEL_EDGE_OFFSET,
		min_pos.y - ReplayVisuals.W_SLICE_LABEL_VERTICAL_OFFSET,
		min_pos.z - ReplayVisuals.W_SLICE_LABEL_EDGE_OFFSET
	)


func board_bounds(board_shape: Array, dimension: int, basis = null) -> Dictionary:
	configure(board_shape, basis)
	if _board_shape.is_empty():
		return {"ok": false}
	var w_size := current_layer_count() if dimension >= 4 else 1
	var first_bounds := unoriented_slice_bounds(0)
	var min_pos: Vector3 = first_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = first_bounds.get("max", Vector3.ZERO)
	for layer_index in range(1, w_size):
		var layer_bounds := unoriented_slice_bounds(layer_index)
		var layer_min: Vector3 = layer_bounds.get("min", min_pos)
		var layer_max: Vector3 = layer_bounds.get("max", max_pos)
		min_pos = Vector3(minf(min_pos.x, layer_min.x), minf(min_pos.y, layer_min.y), minf(min_pos.z, layer_min.z))
		max_pos = Vector3(maxf(max_pos.x, layer_max.x), maxf(max_pos.y, layer_max.y), maxf(max_pos.z, layer_max.z))
	if dimension >= 4:
		min_pos.x -= ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
		min_pos.y -= ReplayVisuals.W_SLICE_LABEL_VERTICAL_BOUNDS_PAD
		min_pos.z -= ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
		max_pos.x += ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
		max_pos.y += ReplayVisuals.ABOVE_BOARD_ACTIVE_BOUNDS_PAD
		max_pos.z += ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
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


func presentation_coordinate(canonical_coordinate: Array, allow_above_board_y: bool = false) -> Dictionary:
	return _basis.presentation_coordinate(canonical_coordinate, _board_shape, allow_above_board_y)
