extends RefCounted

class_name BoardPresentationModel

const ProjectionLayoutScript = preload("res://scripts/presentation/projection_layout.gd")

var snapshot: Dictionary = {}
var projection := ProjectionLayoutScript.new()
var trace_type := ""
var dimension := 0
var is_live := false
var is_live_3d := false
var is_live_4d := false
var uses_live_exterior_cells := false


func configure(source_snapshot: Dictionary, basis = null, orientation = null, spacing_scale: float = 1.0) -> void:
	snapshot = source_snapshot
	trace_type = str(snapshot.get("trace_type", ""))
	dimension = int(snapshot.get("dimension", 0))
	is_live = trace_type.begins_with("live_")
	is_live_3d = trace_type == "live_3d" and dimension == 3
	is_live_4d = trace_type == "live_4d" and dimension == 4
	uses_live_exterior_cells = is_live and dimension >= 3
	projection.configure(snapshot, basis, orientation if is_live_4d else null, spacing_scale)


func current_bounds() -> Dictionary:
	return projection.bounds


func render_world_position(coordinates: Array) -> Vector3:
	return projection.oriented_world_position(coordinates)


func render_cell_world_position(coordinates: Array) -> Vector3:
	return projection.oriented_cell_world_position(coordinates)


func render_active_world_position(coordinates: Array) -> Vector3:
	# Native spawn cells may legitimately sit above the board at negative Y.
	# Keep ordinary locked/Ghost mapping strict while preserving those active
	# coordinates through the same B -> G_D -> L -> anchor composition.
	return projection.oriented_active_world_position(coordinates)


func render_world_position_with_local_offset(coordinates: Array, local_offset: Vector3) -> Vector3:
	return projection.oriented_world_position_with_local_offset(coordinates, local_offset)


func local_render_basis() -> Basis:
	return projection.local_render_basis()


func board_shape() -> Array:
	return snapshot.get("board_shape", [])


func locked_cells() -> Array:
	return snapshot.get("locked_cells", [])


func active_cells() -> Array:
	return snapshot.get("active_cells", [])


func ghost_cells() -> Array:
	return snapshot.get("ghost_cells", [])


func active_layer_indices() -> Array:
	if dimension < 4:
		return []
	var result := []
	for cell in active_cells():
		var position: Array = cell.get("position", [])
		if position.size() > 3:
			var mapped: Dictionary = projection.mapper.presentation_coordinate(position, true)
			if not bool(mapped.get("ok", false)):
				continue
			var layer := int(mapped.get("layer_index", -1))
			if not result.has(layer):
				result.append(layer)
	result.sort()
	return result


func probe_markers() -> Array:
	return snapshot.get("probe_markers", [])


func event_markers() -> Array:
	return snapshot.get("event_markers", [])


func particles() -> Array:
	return snapshot.get("particles", [])
