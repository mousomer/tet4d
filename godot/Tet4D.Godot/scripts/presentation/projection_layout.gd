extends RefCounted

class_name ProjectionLayout

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")

var mapper := TraceCoordinateMapperScript.new()
var local_orientation := SliceLocalOrientationScript.new()
var board_shape: Array = []
var dimension := 0
var bounds: Dictionary = {"ok": false}
var applies_local_orientation := false


func configure(snapshot: Dictionary, basis = null, orientation = null, spacing_scale: float = 1.0) -> void:
	board_shape = snapshot.get("board_shape", []).duplicate()
	dimension = int(snapshot.get("dimension", 0))
	if orientation != null:
		local_orientation = orientation
	applies_local_orientation = dimension == 4 and orientation != null
	mapper.configure(board_shape, basis, spacing_scale)
	bounds = _collection_bounds()


func oriented_world_position(coordinates: Array) -> Vector3:
	return oriented_world_position_with_local_offset(coordinates, Vector3.ZERO)


func oriented_cell_world_position(coordinates: Array) -> Vector3:
	var decomposition := mapper.decompose_cell_position(coordinates, dimension)
	return _oriented_world_position_from_decomposition(decomposition, Vector3.ZERO)


func oriented_active_world_position(coordinates: Array) -> Vector3:
	var decomposition := mapper.decompose_cell_position(coordinates, dimension, true)
	return _oriented_world_position_from_decomposition(decomposition, Vector3.ZERO)


func oriented_world_position_with_local_offset(coordinates: Array, local_offset: Vector3) -> Vector3:
	var decomposition := decompose_position(coordinates)
	return _oriented_world_position_from_decomposition(decomposition, local_offset)


func _oriented_world_position_from_decomposition(decomposition: Dictionary, local_offset: Vector3) -> Vector3:
	if not bool(decomposition.get("ok", false)):
		return Vector3.ZERO
	var local_point: Vector3 = decomposition.get("centered_local_point", Vector3.ZERO) + local_offset
	var anchor: Vector3 = decomposition.get("anchor", Vector3.ZERO)
	return oriented_local_point(local_point) + anchor


func unoriented_world_position(coordinates: Array) -> Vector3:
	return mapper.unoriented_world_position(coordinates, dimension)


func presentation_coordinate(canonical_coordinate: Array) -> Dictionary:
	return mapper.presentation_coordinate(canonical_coordinate)


func centered_local_point(visible_cell_3d: Array) -> Vector3:
	return mapper.centered_local_point(visible_cell_3d)


func slice_anchor(layer_index: int) -> Vector3:
	return mapper.slice_anchor(layer_index)


func decompose_position(coordinates: Array) -> Dictionary:
	return mapper.decompose_position(coordinates, dimension)


func oriented_local_point(centered_point: Vector3) -> Vector3:
	return local_render_basis() * centered_point


func oriented_local_vector(local_vector: Vector3) -> Vector3:
	return local_render_basis() * local_vector


func local_render_basis() -> Basis:
	return local_orientation.passive_render_basis() if applies_local_orientation else Basis.IDENTITY


func local_slice_bounds() -> Dictionary:
	return mapper.local_slice_bounds()


func oriented_slice_bounds(layer_index: int) -> Dictionary:
	var local_bounds := local_slice_bounds()
	if not bool(local_bounds.get("ok", false)):
		return {"ok": false}
	var min_local: Vector3 = local_bounds.get("min", Vector3.ZERO)
	var max_local: Vector3 = local_bounds.get("max", Vector3.ZERO)
	var anchor := slice_anchor(layer_index)
	var first := true
	var min_world := Vector3.ZERO
	var max_world := Vector3.ZERO
	for x in [min_local.x, max_local.x]:
		for y in [min_local.y, max_local.y]:
			for z in [min_local.z, max_local.z]:
				var corner := oriented_local_point(Vector3(x, y, z)) + anchor
				if first:
					min_world = corner
					max_world = corner
					first = false
				else:
					min_world = Vector3(
						minf(min_world.x, corner.x),
						minf(min_world.y, corner.y),
						minf(min_world.z, corner.z)
					)
					max_world = Vector3(
						maxf(max_world.x, corner.x),
						maxf(max_world.y, corner.y),
						maxf(max_world.z, corner.z)
					)
	return {"ok": not first, "min": min_world, "max": max_world}


func _collection_bounds() -> Dictionary:
	if board_shape.is_empty():
		return {"ok": false}
	var layer_count := mapper.current_layer_count() if dimension >= 4 else 1
	var first_bounds := oriented_slice_bounds(0)
	if not bool(first_bounds.get("ok", false)):
		return {"ok": false}
	var min_world: Vector3 = first_bounds.get("min", Vector3.ZERO)
	var max_world: Vector3 = first_bounds.get("max", Vector3.ZERO)
	for layer_index in range(1, layer_count):
		var layer_bounds := oriented_slice_bounds(layer_index)
		var layer_min: Vector3 = layer_bounds.get("min", min_world)
		var layer_max: Vector3 = layer_bounds.get("max", max_world)
		min_world = Vector3(
			minf(min_world.x, layer_min.x),
			minf(min_world.y, layer_min.y),
			minf(min_world.z, layer_min.z)
		)
		max_world = Vector3(
			maxf(max_world.x, layer_max.x),
			maxf(max_world.y, layer_max.y),
			maxf(max_world.z, layer_max.z)
		)
	if dimension >= 4:
		min_world.x -= ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
		min_world.y -= ReplayVisuals.W_SLICE_LABEL_VERTICAL_BOUNDS_PAD
		min_world.z -= ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
		max_world.x += ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
		max_world.y += ReplayVisuals.ABOVE_BOARD_ACTIVE_BOUNDS_PAD
		max_world.z += ReplayVisuals.W_SLICE_LABEL_BOUNDS_PAD
	return {"ok": true, "min": min_world, "max": max_world}
