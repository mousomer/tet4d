extends Node3D

class_name TraceSceneRenderer

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const GridRendererScript = preload("res://scripts/rendering/grid_renderer.gd")
const CellRendererScript = preload("res://scripts/rendering/cell_renderer.gd")
const ParticleRendererScript = preload("res://scripts/rendering/particle_renderer.gd")
const EventMarkerRendererScript = preload("res://scripts/rendering/event_marker_renderer.gd")
const BoardPresentationModelScript = preload("res://scripts/presentation/board_presentation_model.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")

var current_slice_stride := 6.0
var _cell_scale := ReplayVisuals.CELL_SCALE
var _particle_scale := ReplayVisuals.PARTICLE_SCALE
var _event_scale := ReplayVisuals.EVENT_SCALE
var _display_mode := ReplayVisuals.default_display_mode()
var _show_w_labels := true
var _projection_strength := 1.0
var _board_detail := "standard"
var _show_grid := true
var _locked_cell_opacity := ReplayVisuals.DEFAULT_LOCKED_CELL_OPACITY
var _high_contrast := false
var _reduced_motion := false
var _last_case_id := ""
var _last_frame_index := -1
var _particle_trails: Dictionary = {}
var _presentation := BoardPresentationModelScript.new()
var _last_bounds: Dictionary = {"ok": false}
var _live_4d_basis = SliceBasis4DScript.identity()
var _live_4d_local_orientation = SliceLocalOrientationScript.new()
var _basis_transition_progress := 1.0
var _basis_transition_duration := 0.16
var _live_4d_fit_reference: Dictionary = {}
var _live_4d_fit_reference_layer_count := 1
var _basis_fit_scale := 1.0
var _basis_fit_position := Vector3.ZERO

var _grid_root: Node3D
var _cell_root: Node3D
var _particle_root: Node3D
var _marker_root: Node3D


func _ready() -> void:
	_grid_root = _ensure_child("GridRoot")
	_cell_root = _ensure_child("CellRoot")
	_particle_root = _ensure_child("ParticleRoot")
	_marker_root = _ensure_child("MarkerRoot")


func _process(delta: float) -> void:
	if _basis_transition_progress >= 1.0:
		return
	_basis_transition_progress = minf(1.0, _basis_transition_progress + delta / maxf(_basis_transition_duration, 0.001))
	var eased := 1.0 - pow(1.0 - _basis_transition_progress, 3.0)
	_apply_basis_presentation_transform(lerpf(0.965, 1.0, eased))


func set_display_mode(display_mode: String) -> void:
	_display_mode = ReplayVisuals.normalize_display_mode(display_mode)


func set_show_w_labels(visible: bool) -> void:
	_show_w_labels = visible


func set_projection_strength(value: float) -> void:
	_projection_strength = clampf(value, 0.0, 2.0)
	_cell_scale = ReplayVisuals.CELL_SCALE * _projection_strength
	_particle_scale = ReplayVisuals.PARTICLE_SCALE * _projection_strength
	_event_scale = ReplayVisuals.EVENT_SCALE * _projection_strength


func set_board_detail(detail: String) -> void:
	_board_detail = detail if detail in ["minimal", "standard", "full"] else "standard"


func set_grid_visible(visible: bool) -> void:
	_show_grid = visible


func set_locked_cell_opacity(opacity: float) -> void:
	_locked_cell_opacity = ReplayVisuals.normalize_locked_cell_opacity(opacity)


func set_accessibility_policy(high_contrast: bool, reduced_motion: bool) -> void:
	_high_contrast = high_contrast
	_reduced_motion = reduced_motion


func set_live_4d_basis(basis, animate: bool = true) -> void:
	_live_4d_basis = basis
	_basis_transition_progress = 1.0 if _reduced_motion or not animate else 0.0
	_apply_basis_presentation_transform(1.0 if _basis_transition_progress >= 1.0 else 0.965)


func set_live_4d_local_orientation(orientation) -> void:
	if orientation != null:
		_live_4d_local_orientation = orientation


func live_4d_local_orientation_snapshot() -> Dictionary:
	return _live_4d_local_orientation.snapshot()


func reset_live_4d_fit_envelope() -> void:
	_live_4d_fit_reference = {}
	_live_4d_fit_reference_layer_count = 1
	_basis_fit_scale = 1.0
	_basis_fit_position = Vector3.ZERO
	_apply_basis_presentation_transform(1.0)


func live_4d_basis_snapshot() -> Dictionary:
	var snapshot: Dictionary = _live_4d_basis.indicator_snapshot()
	snapshot["transition_progress"] = _basis_transition_progress
	return snapshot


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

	var presentation_basis = _live_4d_basis if str(snapshot.get("trace_type", "")) == "live_4d" else null
	_presentation.configure(
		snapshot,
		presentation_basis,
		_live_4d_local_orientation if str(snapshot.get("trace_type", "")) == "live_4d" else null
	)
	current_slice_stride = _presentation.projection.mapper.slice_stride
	_last_bounds = _presentation.current_bounds()
	_update_live_4d_fit_envelope(str(snapshot.get("trace_type", "")))
	_clear_root(_grid_root)
	_clear_root(_cell_root)
	_clear_root(_particle_root)
	_clear_root(_marker_root)

	var grid := GridRendererScript.new()
	_grid_root.add_child(grid)
	grid.rebuild(
		_presentation.board_shape(),
		_presentation.dimension,
		_presentation.projection,
		_display_mode,
		_presentation.is_live,
		_show_w_labels,
		_presentation.active_layer_indices(),
		_board_detail,
		_high_contrast,
		_show_grid
	)

	var locked_material := ReplayVisuals.locked_cell_material(_display_mode, _locked_cell_opacity)
	var probe_before_material := ReplayVisuals.probe_before_material(_display_mode)
	var probe_after_material := ReplayVisuals.probe_after_material(_display_mode)
	var event_material := ReplayVisuals.event_marker_material(_display_mode)

	for cell in _presentation.locked_cells():
		var node := CellRendererScript.new()
		_cell_root.add_child(node)
		var locked_color_id := int(cell.get("color_id", 0))
		var locked_size := ReplayVisuals.LIVE_3D_LOCKED_CELL_SCALE if _presentation.uses_live_exterior_cells else ReplayVisuals.LIVE_LOCKED_CELL_SCALE
		var locked_position := _presentation.render_world_position(cell.get("position", []))
		if _presentation.uses_live_exterior_cells:
			node.setup_exterior_block(
				locked_position,
				ReplayVisuals.live_3d_locked_face_materials(_display_mode, locked_color_id, _locked_cell_opacity),
				ReplayVisuals.live_3d_locked_cell_border_material(_display_mode),
				locked_size,
				locked_size + ReplayVisuals.LIVE_3D_LOCKED_CELL_BORDER_DELTA * _edge_weight()
			)
		else:
			node.setup(
				locked_position,
				_live_locked_material(locked_color_id, _presentation.uses_live_exterior_cells, _presentation.is_live, locked_material),
				locked_size if _presentation.is_live else _cell_scale * 0.95,
				ReplayVisuals.LIVE_CELL_DEPTH if _presentation.is_live else -1.0,
				_live_locked_border_material(_presentation.uses_live_exterior_cells, _presentation.is_live),
				(locked_size + ReplayVisuals.LIVE_CELL_BORDER_DELTA * _edge_weight()) if _presentation.is_live else 0.0
			)
		node.basis = _presentation.local_render_basis()

	for cell in _presentation.ghost_cells():
		var ghost_node := CellRendererScript.new()
		ghost_node.name = "GhostCell"
		ghost_node.set_meta("presentation_role", "ghost")
		_cell_root.add_child(ghost_node)
		var ghost_size := ReplayVisuals.LIVE_3D_GHOST_CELL_SCALE if _presentation.uses_live_exterior_cells else ReplayVisuals.LIVE_GHOST_CELL_SCALE
		ghost_node.setup(
			_presentation.render_world_position(cell.get("position", [])),
			ReplayVisuals.ghost_cell_material(_display_mode, int(cell.get("color_id", 0)), _high_contrast),
			ghost_size,
			ghost_size if _presentation.uses_live_exterior_cells else ReplayVisuals.LIVE_CELL_DEPTH,
			ReplayVisuals.ghost_cell_border_material(_display_mode, _high_contrast),
			ghost_size + ReplayVisuals.LIVE_CELL_BORDER_DELTA * _edge_weight()
		)
		ghost_node.basis = _presentation.local_render_basis()

	var active_cells := _presentation.active_cells()
	for active_index in range(active_cells.size()):
		var cell = active_cells[active_index]
		var node := CellRendererScript.new()
		_cell_root.add_child(node)
		# Gameplay cells do not carry stable per-cell IDs in the exported traces.
		# Keep them on the current discrete frame instead of inventing a path.
		var position := _presentation.render_world_position(cell.get("position", []))
		var active_color_id := int(cell.get("color_id", 1))
		var active_size := ReplayVisuals.LIVE_3D_ACTIVE_CELL_SCALE if _presentation.uses_live_exterior_cells else ReplayVisuals.LIVE_ACTIVE_CELL_SCALE
		if _presentation.uses_live_exterior_cells:
			node.setup_exterior_block(
				position,
				_live_exterior_active_face_materials(active_color_id),
				ReplayVisuals.live_3d_active_cell_border_material(_display_mode),
				active_size,
				active_size + ReplayVisuals.LIVE_3D_ACTIVE_CELL_BORDER_DELTA * _edge_weight(),
				_live_3d_rotation_pulse(snapshot),
				ReplayVisuals.live_3d_origin_marker_material(_display_mode) if active_index == 0 else null,
				ReplayVisuals.LIVE_3D_ORIGIN_MARKER_SCALE if active_index == 0 else 0.0
			)
		else:
			node.setup(
				position,
				_live_active_material(active_color_id, _presentation.uses_live_exterior_cells, _presentation.is_live),
				active_size if _presentation.is_live else ReplayVisuals.ACTIVE_GAMEPLAY_CELL_SCALE,
				ReplayVisuals.LIVE_CELL_DEPTH if _presentation.is_live else -1.0,
				_live_active_border_material(_presentation.uses_live_exterior_cells, _presentation.is_live),
				(active_size + ReplayVisuals.LIVE_CELL_BORDER_DELTA * _edge_weight()) if _presentation.is_live else 0.0
			)
		node.basis = _presentation.local_render_basis()

	for marker in _presentation.probe_markers():
		var marker_node := EventMarkerRendererScript.new()
		_marker_root.add_child(marker_node)
		var probe_material := probe_after_material if str(marker.get("kind", "")) == "probe_after" else probe_before_material
		marker_node.setup(
			_presentation.render_world_position_with_local_offset(
				marker.get("position", []),
				Vector3.UP * ReplayVisuals.PROBE_MARKER_HEIGHT
			),
			probe_material,
			1.35 if str(marker.get("presentation_role", "")) == "lesson_target" else _event_scale * 1.05,
			1.0,
			not _reduced_motion
		)

	for marker in _presentation.event_markers():
		var marker_node := EventMarkerRendererScript.new()
		_marker_root.add_child(marker_node)
		marker_node.setup(
			_presentation.render_world_position_with_local_offset(
				marker.get("position", []),
				Vector3.UP * ReplayVisuals.EVENT_MARKER_HEIGHT
			),
			event_material,
			_event_scale,
			1.0 - ((0.0 if _reduced_motion else alpha) * 0.65),
			not _reduced_motion
		)

	for particle in _presentation.particles():
		var particle_node := ParticleRendererScript.new()
		_particle_root.add_child(particle_node)
		var radius := maxf(_particle_scale, float(particle.get("radius", _particle_scale)))
		var escaped := bool(particle.get("escaped", false))
		var color_id := int(particle.get("color_id", 0))
		var particle_id := int(particle.get("particle_id", -1))
		var particle_position := _presentation.render_world_position(particle.get("position", []))
		var next_particle := _matching_particle(particle_id, next_snapshot.get("particles", []))
		if not next_particle.is_empty():
			# Endgame particles have stable trace IDs, so this is visual-only
			# interpolation between exported frames, not simulation.
			particle_position = particle_position.lerp(
				_presentation.render_world_position(next_particle.get("position", [])),
				0.0 if _reduced_motion else alpha
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


func _update_live_4d_fit_envelope(trace_type: String) -> void:
	if trace_type != "live_4d" or not _last_bounds.get("ok", false):
		_basis_fit_scale = 1.0
		_basis_fit_position = Vector3.ZERO
		_apply_basis_presentation_transform(1.0)
		return
	if _live_4d_fit_reference.is_empty() or _live_4d_basis.is_identity():
		_live_4d_fit_reference = _last_bounds.duplicate(true)
		_live_4d_fit_reference_layer_count = _presentation.projection.mapper.current_layer_count()
	var reference_min: Vector3 = _live_4d_fit_reference.get("min", Vector3.ZERO)
	var reference_max: Vector3 = _live_4d_fit_reference.get("max", Vector3.ZERO)
	var current_min: Vector3 = _last_bounds.get("min", Vector3.ZERO)
	var current_max: Vector3 = _last_bounds.get("max", Vector3.ZERO)
	var reference_size := reference_max - reference_min
	var current_size := current_max - current_min
	_basis_fit_scale = 1.0
	for axis in range(3):
		if current_size[axis] > 0.001:
			_basis_fit_scale = minf(_basis_fit_scale, reference_size[axis] / current_size[axis])
	var minimum_legible_scale := 0.65 if _live_4d_fit_reference_layer_count >= 4 else (0.45 if _live_4d_fit_reference_layer_count >= 2 else 0.20)
	_basis_fit_scale = clampf(_basis_fit_scale, minimum_legible_scale, 1.0)
	var reference_center := (reference_min + reference_max) * 0.5
	var current_center := (current_min + current_max) * 0.5
	_basis_fit_position = reference_center - current_center * _basis_fit_scale
	_apply_basis_presentation_transform(1.0 if _basis_transition_progress >= 1.0 else 0.965)


func _apply_basis_presentation_transform(settle_scale: float) -> void:
	scale = Vector3.ONE * _basis_fit_scale * settle_scale
	position = _basis_fit_position


func _live_locked_material(color_id: int, is_live_3d_snapshot: bool, is_live_snapshot: bool, replay_material: Material) -> Material:
	if is_live_3d_snapshot:
		return ReplayVisuals.live_3d_locked_cell_material(_display_mode, color_id, _locked_cell_opacity)
	if is_live_snapshot:
		return ReplayVisuals.live_locked_cell_material(_display_mode, color_id, _locked_cell_opacity)
	return replay_material


func _live_active_material(color_id: int, is_live_3d_snapshot: bool, is_live_snapshot: bool) -> Material:
	if is_live_3d_snapshot:
		return ReplayVisuals.live_3d_active_cell_material(_display_mode, color_id)
	if is_live_snapshot:
		return ReplayVisuals.live_active_cell_material(_display_mode, color_id)
	return ReplayVisuals.gameplay_active_cell_material(_display_mode)


func _live_exterior_active_face_materials(color_id: int) -> Dictionary:
	if _presentation.is_live_4d:
		return ReplayVisuals.live_4d_active_face_materials(_display_mode, color_id)
	return ReplayVisuals.live_3d_active_face_materials(_display_mode, color_id)


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
	if _reduced_motion:
		return 0.0
	var last_command := str(snapshot.get("last_command", ""))
	if not last_command.begins_with("rotate_"):
		return 0.0
	return 1.0 if str(snapshot.get("last_command_status", "")) == "accepted" else 0.55


func presentation_preferences_snapshot() -> Dictionary:
	return {
		"board_detail": _board_detail,
		"high_contrast": _high_contrast,
		"reduced_motion": _reduced_motion,
	}


func _edge_weight() -> float:
	var detail_weight := 0.9 if _board_detail == "minimal" else (1.25 if _board_detail == "full" else 1.0)
	return detail_weight * (1.55 if _high_contrast else 1.0)


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
