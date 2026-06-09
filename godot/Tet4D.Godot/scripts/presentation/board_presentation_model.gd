extends RefCounted

class_name BoardPresentationModel

const ProjectionLayoutScript = preload("res://scripts/presentation/projection_layout.gd")

var snapshot: Dictionary = {}
var projection := ProjectionLayoutScript.new()
var trace_type := ""
var dimension := 0
var is_live := false
var is_live_3d := false


func configure(source_snapshot: Dictionary) -> void:
	snapshot = source_snapshot
	trace_type = str(snapshot.get("trace_type", ""))
	dimension = int(snapshot.get("dimension", 0))
	is_live = trace_type.begins_with("live_")
	is_live_3d = trace_type == "live_3d" and dimension == 3
	projection.configure(snapshot)


func current_bounds() -> Dictionary:
	return projection.bounds


func world_position(coordinates: Array) -> Vector3:
	return projection.world_position(coordinates)


func board_shape() -> Array:
	return snapshot.get("board_shape", [])


func locked_cells() -> Array:
	return snapshot.get("locked_cells", [])


func active_cells() -> Array:
	return snapshot.get("active_cells", [])


func probe_markers() -> Array:
	return snapshot.get("probe_markers", [])


func event_markers() -> Array:
	return snapshot.get("event_markers", [])


func particles() -> Array:
	return snapshot.get("particles", [])
