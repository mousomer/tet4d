extends RefCounted

class_name ProjectionLayout

const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")

var mapper := TraceCoordinateMapperScript.new()
var local_orientation := SliceLocalOrientationScript.new()
var board_shape: Array = []
var dimension := 0
var bounds: Dictionary = {"ok": false}


func configure(snapshot: Dictionary, basis = null, orientation = null) -> void:
	board_shape = snapshot.get("board_shape", []).duplicate()
	dimension = int(snapshot.get("dimension", 0))
	if orientation != null:
		local_orientation = orientation
	mapper.configure(board_shape, basis)
	bounds = mapper.board_bounds(board_shape, dimension, basis)


func world_position(coordinates: Array) -> Vector3:
	# Stage 54E-2a compatibility path: G_D(p) + anchor_i. Slice-local L is
	# separately queryable but renderer consumers migrate through it in 54E-2b.
	return mapper.world_position(coordinates, dimension)


func presentation_coordinate(canonical_coordinate: Array) -> Dictionary:
	return mapper.presentation_coordinate(canonical_coordinate)


func centered_local_point(visible_cell_3d: Array) -> Vector3:
	return mapper.centered_local_point(visible_cell_3d)


func slice_anchor(layer_index: int) -> Vector3:
	return mapper.slice_anchor(layer_index)


func decompose_position(coordinates: Array) -> Dictionary:
	return mapper.decompose_position(coordinates, dimension)


func oriented_local_point(centered_point: Vector3) -> Vector3:
	return local_orientation.orient_local_point(centered_point)
