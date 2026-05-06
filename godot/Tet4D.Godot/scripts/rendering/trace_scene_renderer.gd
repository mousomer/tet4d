extends Node3D

class_name TraceSceneRenderer

@export var cell_scale := 0.9
@export var particle_scale := 0.24
@export var event_scale := 0.5
@export var slice_padding := 2.0

var current_slice_stride := 6.0

var _grid_root: Node3D
var _cell_root: Node3D
var _particle_root: Node3D
var _marker_root: Node3D


func _ready() -> void:
	_grid_root = _ensure_child("GridRoot")
	_cell_root = _ensure_child("CellRoot")
	_particle_root = _ensure_child("ParticleRoot")
	_marker_root = _ensure_child("MarkerRoot")


func render_snapshot(snapshot: Dictionary) -> void:
	if snapshot.is_empty():
		return
	current_slice_stride = _compute_slice_stride(snapshot.get("board_shape", []))
	_clear_root(_grid_root)
	_clear_root(_cell_root)
	_clear_root(_particle_root)
	_clear_root(_marker_root)

	var grid := GridRenderer.new()
	_grid_root.add_child(grid)
	grid.rebuild(snapshot.get("board_shape", []), int(snapshot.get("dimension", 0)), current_slice_stride)

	for cell in snapshot.get("locked_cells", []):
		var node := CellRenderer.new()
		_cell_root.add_child(node)
		node.setup(_project_position(cell.get("position", []), int(snapshot.get("dimension", 0))), Color(0.36, 0.39, 0.45), cell_scale * 0.95)

	for cell in snapshot.get("active_cells", []):
		var node := CellRenderer.new()
		_cell_root.add_child(node)
		node.setup(_project_position(cell.get("position", []), int(snapshot.get("dimension", 0))), _color_for_id(int(cell.get("color_id", 1)), false), cell_scale)

	for marker in snapshot.get("probe_markers", []):
		var marker_node := EventMarkerRenderer.new()
		_marker_root.add_child(marker_node)
		marker_node.setup(_project_position(marker.get("position", []), int(snapshot.get("dimension", 0))) + Vector3.UP * 0.35, Color(0.22, 0.94, 0.95, 1.0), event_scale)

	for marker in snapshot.get("event_markers", []):
		var marker_node := EventMarkerRenderer.new()
		_marker_root.add_child(marker_node)
		marker_node.setup(_project_position(marker.get("position", []), int(snapshot.get("dimension", 0))) + Vector3.UP * 0.7, Color(1.0, 0.82, 0.28, 1.0), event_scale)

	for particle in snapshot.get("particles", []):
		var particle_node := ParticleRenderer.new()
		_particle_root.add_child(particle_node)
		var radius := maxf(particle_scale, float(particle.get("radius", particle_scale)))
		particle_node.setup(
			_project_position(particle.get("position", []), int(snapshot.get("dimension", 0))),
			_color_for_id(int(particle.get("color_id", 0)), bool(particle.get("escaped", false))),
			radius,
			particle.get("velocity", [])
		)


func _compute_slice_stride(board_shape: Array) -> float:
	var width := float(board_shape[0]) if not board_shape.is_empty() else 4.0
	return width + slice_padding


func _project_position(coordinates: Array, dimension: int) -> Vector3:
	if coordinates.is_empty():
		return Vector3.ZERO
	var x := float(coordinates[0])
	var y := -float(coordinates[1]) if coordinates.size() > 1 else 0.0
	var z := float(coordinates[2]) if coordinates.size() > 2 else 0.0
	if dimension >= 4 and coordinates.size() > 3:
		x += float(coordinates[3]) * current_slice_stride
	return Vector3(x, y, z)


func _color_for_id(color_id: int, escaped: bool) -> Color:
	var palette := [
		Color(0.85, 0.85, 0.85),
		Color(0.95, 0.42, 0.32),
		Color(0.24, 0.75, 0.92),
		Color(0.44, 0.82, 0.36),
		Color(0.96, 0.75, 0.26),
		Color(0.74, 0.45, 0.96),
		Color(0.96, 0.54, 0.22),
		Color(0.93, 0.30, 0.62),
		Color(0.32, 0.92, 0.65),
	]
	var base: Color = palette[absi(color_id) % palette.size()]
	return base.lerp(Color.WHITE, 0.35) if escaped else base


func _ensure_child(node_name: String) -> Node3D:
	var existing := get_node_or_null(node_name)
	if existing != null:
		return existing
	var node := Node3D.new()
	node.name = node_name
	add_child(node)
	return node


func _clear_root(root: Node) -> void:
	for child in root.get_children():
		child.queue_free()
