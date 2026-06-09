extends RefCounted

class_name ProjectionLayout

const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")

var mapper := TraceCoordinateMapperScript.new()
var board_shape: Array = []
var dimension := 0
var bounds: Dictionary = {"ok": false}


func configure(snapshot: Dictionary) -> void:
	board_shape = snapshot.get("board_shape", []).duplicate()
	dimension = int(snapshot.get("dimension", 0))
	mapper.configure(board_shape)
	bounds = mapper.board_bounds(board_shape, dimension)


func world_position(coordinates: Array) -> Vector3:
	return mapper.world_position(coordinates, dimension)
