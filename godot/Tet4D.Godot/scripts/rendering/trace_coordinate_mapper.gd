extends RefCounted

class_name TraceCoordinateMapper

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const AdaptiveLayerLayoutScript = preload("res://scripts/presentation/adaptive_layer_layout.gd")
const LocalBoardPresentationGeometryScript = preload("res://scripts/presentation/local_board_presentation_geometry.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")

var slice_stride := 6.0
var _board_shape: Array = []
var _visible_board_shape: Array = []
var _basis = SliceBasis4DScript.identity()
var layer_layout = AdaptiveLayerLayoutScript.new()
var _local_geometry = LocalBoardPresentationGeometryScript.new()


func configure(board_shape: Array, basis = null, spacing_scale: float = 1.0) -> void:
	_board_shape = board_shape.duplicate()
	_basis = basis if basis != null else SliceBasis4DScript.identity()
	var axis_mapping := []
	if _board_shape.size() == 4:
		_visible_board_shape = _basis.visible_dimensions(_board_shape)
		axis_mapping = _basis.slots().slice(0, 3)
	elif _board_shape.size() >= 3:
		_visible_board_shape = _board_shape.slice(0, 3)
		axis_mapping = [SliceBasis4DScript.AXIS_X + 1, SliceBasis4DScript.AXIS_Y + 1, SliceBasis4DScript.AXIS_Z + 1]
	elif _board_shape.size() == 2:
		_visible_board_shape = [_board_shape[0], _board_shape[1], 1]
		axis_mapping = [SliceBasis4DScript.AXIS_X + 1, SliceBasis4DScript.AXIS_Y + 1, LocalBoardPresentationGeometryScript.PRESENTATION_DEGENERATE_AXIS]
	else:
		_visible_board_shape = []
	_local_geometry.configure(_visible_board_shape, axis_mapping)
	var width: float = _local_geometry.local_extent.x if _local_geometry.is_configured() else 4.0
	var height: float = _local_geometry.local_extent.y if _local_geometry.is_configured() else 4.0
	layer_layout.configure(current_layer_count(), width, height, 1.7777778, spacing_scale)
	slice_stride = width + layer_layout.horizontal_gap


func unoriented_world_position(coordinates: Array, dimension: int) -> Vector3:
	# Explicit Stage 54E-2a compatibility composition: G_D(p) + anchor_i.
	# Live-4D renderer consumers use ProjectionLayout.oriented_world_position().
	var decomposition := decompose_position(coordinates, dimension)
	return decomposition.get("unoriented_world_point", Vector3.ZERO) if bool(decomposition.get("ok", false)) else Vector3.ZERO


func decompose_position(coordinates: Array, dimension: int, allow_above_board_y: bool = false) -> Dictionary:
	return _decompose_position(coordinates, dimension, allow_above_board_y, false)


func decompose_cell_position(coordinates: Array, dimension: int, allow_above_board_y: bool = false) -> Dictionary:
	return _decompose_position(coordinates, dimension, allow_above_board_y, true)


func _decompose_position(coordinates: Array, dimension: int, allow_above_board_y: bool, strict_cell: bool) -> Dictionary:
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
	var local_coordinate := _local_coordinate_3d(visible_coordinates)
	var accepted_local_coordinate := (
		_local_geometry.accepts_cell_input(local_coordinate, allow_above_board_y)
		if strict_cell
		else _local_geometry.accepts_point_input(local_coordinate)
	)
	if not accepted_local_coordinate:
		return {"ok": false}
	var local_point := (
		_local_geometry.cell_position(local_coordinate, allow_above_board_y)
		if strict_cell
		else _local_geometry.point_position(local_coordinate)
	)
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
	if visible_coordinates.is_empty() or not _local_geometry.is_configured():
		return Vector3.ZERO
	return _local_geometry.point_position(_local_coordinate_3d(visible_coordinates))


func centered_local_cell(visible_coordinates: Array, allow_above_board_y: bool = false) -> Vector3:
	return _local_geometry.cell_position(_local_coordinate_3d(visible_coordinates), allow_above_board_y)


func _local_coordinate_3d(visible_coordinates: Array) -> Array:
	var local_coordinate := visible_coordinates.duplicate()
	while local_coordinate.size() < 3:
		local_coordinate.append(0)
	return local_coordinate


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
	return _local_geometry.local_bounds()


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


func visible_board_shape() -> Array:
	return _visible_board_shape.duplicate()


func local_geometry():
	return _local_geometry


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
