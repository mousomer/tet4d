extends Node3D

class_name TraceSceneRenderer

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const GridRendererScript = preload("res://scripts/rendering/grid_renderer.gd")
const CellRendererScript = preload("res://scripts/rendering/cell_renderer.gd")
const ParticleRendererScript = preload("res://scripts/rendering/particle_renderer.gd")
const EventMarkerRendererScript = preload("res://scripts/rendering/event_marker_renderer.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")

var current_slice_stride := 6.0
var _cell_scale := ReplayVisuals.CELL_SCALE
var _particle_scale := ReplayVisuals.PARTICLE_SCALE
var _event_scale := ReplayVisuals.EVENT_SCALE
var _display_mode := ReplayVisuals.default_display_mode()
var _last_case_id := ""
var _last_frame_index := -1
var _particle_trails: Dictionary = {}
var _mapper := TraceCoordinateMapperScript.new()
var _last_bounds: Dictionary = {"ok": false}

var _grid_root: Node3D
var _cell_root: Node3D
var _particle_root: Node3D
var _marker_root: Node3D


func _ready() -> void:
	_grid_root = _ensure_child("GridRoot")
	_cell_root = _ensure_child("CellRoot")
	_particle_root = _ensure_child("ParticleRoot")
	_marker_root = _ensure_child("MarkerRoot")


func set_display_mode(display_mode: String) -> void:
	_display_mode = ReplayVisuals.normalize_display_mode(display_mode)


func render_snapshot(snapshot: Dictionary) -> void:
	render_interpolated_snapshot(snapshot, {}, 0.0)


func render_interpolated_snapshot(snapshot: Dictionary, next_snapshot: Dictionary = {}, alpha: float = 0.0) -> void:
	if snapshot.is_empty():
		return
	var case_id := str(snapshot.get("case_id", ""))
	var frame_index := int(snapshot.get("frame_index", 0))
	if case_id != _last_case_id or frame_index < _last_frame_index:
		_particle_trails.clear()
	_last_case_id = case_id
	_last_frame_index = frame_index

	_mapper.configure(snapshot.get("board_shape", []))
	current_slice_stride = _mapper.slice_stride
	_last_bounds = _mapper.board_bounds(snapshot.get("board_shape", []), int(snapshot.get("dimension", 0)))
	_clear_root(_grid_root)
	_clear_root(_cell_root)
	_clear_root(_particle_root)
	_clear_root(_marker_root)

	var trace_type := str(snapshot.get("trace_type", ""))
	var is_live_snapshot := trace_type.begins_with("live_")
	var is_live_3d_snapshot := trace_type == "live_3d" and int(snapshot.get("dimension", 0)) == 3
	var grid := GridRendererScript.new()
	_grid_root.add_child(grid)
	grid.rebuild(
		snapshot.get("board_shape", []),
		int(snapshot.get("dimension", 0)),
		_mapper,
		_display_mode,
		is_live_snapshot
	)

	var locked_material := ReplayVisuals.locked_cell_material(_display_mode)
	var probe_before_material := ReplayVisuals.probe_before_material(_display_mode)
	var probe_after_material := ReplayVisuals.probe_after_material(_display_mode)
	var event_material := ReplayVisuals.event_marker_material(_display_mode)

	for cell in snapshot.get("locked_cells", []):
		var node := CellRendererScript.new()
		_cell_root.add_child(node)
		var locked_color_id := int(cell.get("color_id", 0))
		var locked_size := ReplayVisuals.LIVE_3D_LOCKED_CELL_SCALE if is_live_3d_snapshot else ReplayVisuals.LIVE_LOCKED_CELL_SCALE
		var locked_position := _mapper.world_position(cell.get("position", []), int(snapshot.get("dimension", 0)))
		if is_live_3d_snapshot:
			node.setup_exterior_block(
				locked_position,
				ReplayVisuals.live_3d_locked_face_materials(_display_mode, locked_color_id),
				ReplayVisuals.live_3d_locked_cell_border_material(_display_mode),
				locked_size,
				locked_size + ReplayVisuals.LIVE_3D_CELL_BORDER_DELTA
			)
		else:
			node.setup(
				locked_position,
				_live_locked_material(locked_color_id, is_live_3d_snapshot, is_live_snapshot, locked_material),
				locked_size if is_live_snapshot else _cell_scale * 0.95,
				ReplayVisuals.LIVE_CELL_DEPTH if is_live_snapshot else -1.0,
				_live_locked_border_material(is_live_3d_snapshot, is_live_snapshot),
				(locked_size + ReplayVisuals.LIVE_CELL_BORDER_DELTA) if is_live_snapshot else 0.0
			)

	for cell in snapshot.get("active_cells", []):
		var node := CellRendererScript.new()
		_cell_root.add_child(node)
		# Gameplay cells do not carry stable per-cell IDs in the exported traces.
		# Keep them on the current discrete frame instead of inventing a path.
		var position := _mapper.world_position(cell.get("position", []), int(snapshot.get("dimension", 0)))
		var active_color_id := int(cell.get("color_id", 1))
		var active_size := ReplayVisuals.LIVE_3D_ACTIVE_CELL_SCALE if is_live_3d_snapshot else ReplayVisuals.LIVE_ACTIVE_CELL_SCALE
		if is_live_3d_snapshot:
			node.setup_exterior_block(
				position,
				ReplayVisuals.live_3d_active_face_materials(_display_mode, active_color_id),
				ReplayVisuals.live_3d_active_cell_border_material(_display_mode),
				active_size,
				active_size + ReplayVisuals.LIVE_3D_CELL_BORDER_DELTA,
				_live_3d_rotation_pulse(snapshot)
			)
		else:
			node.setup(
				position,
				_live_active_material(active_color_id, is_live_3d_snapshot, is_live_snapshot),
				active_size if is_live_snapshot else ReplayVisuals.ACTIVE_GAMEPLAY_CELL_SCALE,
				ReplayVisuals.LIVE_CELL_DEPTH if is_live_snapshot else -1.0,
				_live_active_border_material(is_live_3d_snapshot, is_live_snapshot),
				(active_size + ReplayVisuals.LIVE_CELL_BORDER_DELTA) if is_live_snapshot else 0.0
			)

	for marker in snapshot.get("probe_markers", []):
		var marker_node := EventMarkerRendererScript.new()
		_marker_root.add_child(marker_node)
		var probe_material := probe_after_material if str(marker.get("kind", "")) == "probe_after" else probe_before_material
		marker_node.setup(
			_mapper.world_position(marker.get("position", []), int(snapshot.get("dimension", 0))) + Vector3.UP * ReplayVisuals.PROBE_MARKER_HEIGHT,
			probe_material,
			_event_scale * 1.05
		)

	for marker in snapshot.get("event_markers", []):
		var marker_node := EventMarkerRendererScript.new()
		_marker_root.add_child(marker_node)
		marker_node.setup(
			_mapper.world_position(marker.get("position", []), int(snapshot.get("dimension", 0))) + Vector3.UP * ReplayVisuals.EVENT_MARKER_HEIGHT,
			event_material,
			_event_scale,
			1.0 - (alpha * 0.65)
		)

	for particle in snapshot.get("particles", []):
		var particle_node := ParticleRendererScript.new()
		_particle_root.add_child(particle_node)
		var radius := maxf(_particle_scale, float(particle.get("radius", _particle_scale)))
		var escaped := bool(particle.get("escaped", false))
		var color_id := int(particle.get("color_id", 0))
		var particle_id := int(particle.get("particle_id", -1))
		var particle_position := _mapper.world_position(particle.get("position", []), int(snapshot.get("dimension", 0)))
		var next_particle := _matching_particle(particle_id, next_snapshot.get("particles", []))
		if not next_particle.is_empty():
			# Endgame particles have stable trace IDs, so this is visual-only
			# interpolation between exported frames, not simulation.
			particle_position = particle_position.lerp(
				_mapper.world_position(next_particle.get("position", []), int(snapshot.get("dimension", 0))),
				alpha
			)
		var trail_positions := _trail_positions_for_particle(particle_id, particle_position)
		particle_node.setup(
			particle_position,
			ReplayVisuals.particle_material(_display_mode, escaped, color_id),
			ReplayVisuals.particle_core_material(_display_mode, escaped, color_id),
			radius,
			particle.get("velocity", []),
			ReplayVisuals.particle_trail_material(_display_mode, escaped, color_id),
			trail_positions
		)


func current_bounds() -> Dictionary:
	return _last_bounds


func _live_locked_material(color_id: int, is_live_3d_snapshot: bool, is_live_snapshot: bool, replay_material: Material) -> Material:
	if is_live_3d_snapshot:
		return ReplayVisuals.live_3d_locked_cell_material(_display_mode, color_id)
	if is_live_snapshot:
		return ReplayVisuals.live_locked_cell_material(_display_mode, color_id)
	return replay_material


func _live_active_material(color_id: int, is_live_3d_snapshot: bool, is_live_snapshot: bool) -> Material:
	if is_live_3d_snapshot:
		return ReplayVisuals.live_3d_active_cell_material(_display_mode, color_id)
	if is_live_snapshot:
		return ReplayVisuals.live_active_cell_material(_display_mode, color_id)
	return ReplayVisuals.gameplay_active_cell_material(_display_mode)


func _live_locked_border_material(is_live_3d_snapshot: bool, is_live_snapshot: bool) -> Material:
	if is_live_3d_snapshot:
		return ReplayVisuals.live_3d_locked_cell_border_material(_display_mode)
	if is_live_snapshot:
		return ReplayVisuals.live_locked_cell_border_material(_display_mode)
	return null


func _live_active_border_material(is_live_3d_snapshot: bool, is_live_snapshot: bool) -> Material:
	if is_live_3d_snapshot:
		return ReplayVisuals.live_3d_active_cell_border_material(_display_mode)
	if is_live_snapshot:
		return ReplayVisuals.live_active_cell_border_material(_display_mode)
	return null


func _live_3d_rotation_pulse(snapshot: Dictionary) -> float:
	var last_command := str(snapshot.get("last_command", ""))
	if not last_command.begins_with("rotate_"):
		return 0.0
	return 1.0 if str(snapshot.get("last_command_status", "")) == "accepted" else 0.55


func _matching_particle(particle_id: int, particles: Array) -> Dictionary:
	if particle_id < 0:
		return {}
	for particle in particles:
		if int(particle.get("particle_id", -1)) == particle_id:
			return particle
	return {}


func _trail_positions_for_particle(particle_id: int, position: Vector3) -> Array:
	if particle_id < 0:
		return []
	var key := str(particle_id)
	var trail: Array = _particle_trails.get(key, [])
	if trail.is_empty() or trail[trail.size() - 1].distance_to(position) > 0.02:
		trail.append(position)
	while trail.size() > ReplayVisuals.PARTICLE_TRAIL_HISTORY:
		trail.pop_front()
	_particle_trails[key] = trail
	return trail.duplicate()


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
