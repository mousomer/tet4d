extends Node3D

class_name GridRenderer

const GridDisplayMode = preload("res://scripts/presentation/grid_display_mode.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const PRESENTATION_ROLE_ACTIVE_FRAME := "board.frame_active"

var _rear_faces: Array[Node3D] = []
var _slice_labels: Array[Label3D] = []
var _active_frames: Array[Node3D] = []
var _structural_key: Array = []
var scaffold_generation := 0
var _role_opacity_key: Array = []

func _process(_delta: float) -> void:
	var camera := get_viewport().get_camera_3d()
	if camera != null:
		var camera_position := to_local(camera.global_position)
		_update_rear_faces(camera_position)
		_update_slice_labels(camera_position)

# Geometry survives gameplay snapshots. Active navigation state and camera
# label placement update existing nodes and never recreate lattice batches.
func rebuild(
	dimension: int, projection, display_mode: String,
	_live_2d: bool = false, show_w_labels: bool = true,
	active_layers: Array = [], _board_detail: String = "standard",
	high_contrast: bool = false, grid_mode: int = GridDisplayMode.Mode.BORDER,
	grid_opacity: float = -1.0, boundary_opacity: float = -1.0,
	enclosure_opacity: float = -1.0, scaffold_opacity: float = -1.0,
	cell_opacity: float = -1.0
) -> void:
	var geometry = projection.mapper.local_geometry()
	if geometry == null or not geometry.is_configured():
		return
	var w_size: int = int(projection.mapper.current_layer_count()) if dimension >= 4 else 1
	var anchors: Array = []
	var slice_coordinates: Array = []
	for layer in range(w_size):
		anchors.append(projection.slice_anchor(layer))
		slice_coordinates.append(projection.mapper.semantic_slice_coordinate(layer))
	var key := [geometry.structural_snapshot(), dimension, anchors,
		projection.local_render_basis(), display_mode, high_contrast, grid_mode,
		grid_opacity, boundary_opacity,
		show_w_labels, projection.mapper.slice_axis_label(), slice_coordinates]
	var opacities := [enclosure_opacity, scaffold_opacity, cell_opacity]
	if key == _structural_key:
		if opacities != _role_opacity_key:
			_update_role_opacities(self, display_mode, high_contrast, enclosure_opacity, scaffold_opacity, cell_opacity, grid_opacity, boundary_opacity)
			_role_opacity_key = opacities
		_update_navigation(active_layers)
		return
	_role_opacity_key = opacities
	_structural_key = key.duplicate(true)
	scaffold_generation += 1
	for child in get_children():
		remove_child(child)
		child.queue_free()
	_rear_faces.clear()
	_slice_labels.clear()
	_active_frames.clear()
	var included := GridDisplayMode.roles(grid_mode)
	# Generated once per structural key; every slice receives the same topology.
	var grid_lines := GridDisplayMode.select_lines(geometry.lattice_geometry(), grid_mode)
	for w_index in range(w_size):
		var slice_root := Node3D.new()
		slice_root.name = "SliceGeometry_%d" % w_index
		slice_root.position = projection.slice_anchor(w_index)
		slice_root.basis = projection.local_render_basis()
		slice_root.set_meta("presentation_layer", w_index)
		slice_root.set_meta("slice_anchor", slice_root.position)
		slice_root.set_meta("presentation_role", "board.slice_geometry")
		add_child(slice_root)
		if included.has(GridDisplayMode.ENCLOSURE):
			_add_enclosure(geometry, display_mode, enclosure_opacity, boundary_opacity, high_contrast, slice_root)
		if included.has(GridDisplayMode.FLOOR):
			_add_floor_face(geometry, display_mode, slice_root)
		_add_lattice(grid_lines, GridDisplayMode.shows_rear_faces_only(grid_mode), display_mode, high_contrast,
			ReplayVisuals.scaffold_alpha(scaffold_opacity, grid_opacity), cell_opacity, slice_root)
		if dimension == 2:
			_add_spawn_entry_cue(geometry, display_mode, high_contrast, slice_root)
		if dimension >= 4:
			var frame := Node3D.new()
			frame.name = "ActiveSliceFrame"
			frame.set_meta("presentation_layer", w_index)
			slice_root.add_child(frame)
			_add_outline_box(geometry, display_mode,
				ReplayVisuals.board_active_frame_material(display_mode, high_contrast),
				ReplayVisuals.slice_outline_thickness(display_mode) * (ReplayVisuals.ACTIVE_SLICE_FRAME_HIGH_CONTRAST_MULTIPLIER if high_contrast else ReplayVisuals.ACTIVE_SLICE_FRAME_MULTIPLIER),
				PRESENTATION_ROLE_ACTIVE_FRAME, high_contrast, boundary_opacity, frame)
			_active_frames.append(frame)
			if show_w_labels:
				_add_slice_label(w_index, projection.oriented_slice_bounds(w_index), display_mode,
					active_layers.has(w_index), projection.mapper.slice_axis_label(),
					projection.mapper.semantic_slice_coordinate(w_index))
	_update_navigation(active_layers)
	_process(0.0)

func _update_navigation(active_layers: Array) -> void:
	for frame in _active_frames:
		frame.visible = active_layers.has(int(frame.get_meta("presentation_layer")))
	for label in _slice_labels:
		var selected := active_layers.has(int(label.get_meta("presentation_layer")))
		label.set_meta("selected_slice", selected)
		var mode: String = str(label.get_meta("display_mode"))
		label.modulate = ReplayVisuals.color_for_role(ReplayVisuals.ROLE_TEXT, mode) if selected else ReplayVisuals.slice_label_color(mode)
		label.font_size = ReplayVisuals.W_SLICE_LABEL_SELECTED_FONT_SIZE if selected else ReplayVisuals.W_SLICE_LABEL_FONT_SIZE
		label.outline_size = ReplayVisuals.W_SLICE_LABEL_OUTLINE_SIZE + (2 if selected else 0)

func _add_enclosure(geometry, display_mode: String, opacity: float, boundary_opacity: float, high_contrast: bool, parent: Node3D) -> void:
	var enclosure := MeshInstance3D.new()
	enclosure.name = "PlayableEnclosure"
	var mesh := BoxMesh.new()
	mesh.size = geometry.local_extent
	enclosure.mesh = mesh
	enclosure.material_override = ReplayVisuals.board_enclosure_material(display_mode, opacity, boundary_opacity, high_contrast)
	enclosure.set_meta("presentation_role", GridDisplayMode.ENCLOSURE)
	enclosure.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(enclosure)

# Edge and face lines keep the surface-scaffold material; interior lines keep
# the subordinate internal material. Topology never depends on material. Face
# lines batch per face so camera selection can hide whole front faces.
func _add_lattice(grid_lines: Array, rear_faces_only: bool, display_mode: String, high_contrast: bool, surface_opacity: float, interior_opacity: float, parent: Node3D) -> void:
	var thickness := ReplayVisuals.grid_internal_thickness(high_contrast)
	var batches: Dictionary = {}
	for line in grid_lines:
		var key := GridDisplayMode.lattice_role(line)
		if key == GridDisplayMode.GRID_FACE:
			key = "%d:%d" % [int(line.face_axis), int(line.face_sign)]
		if not batches.has(key):
			batches[key] = []
		batches[key].append(line)
	for key in batches:
		var lines: Array = batches[key]
		var role := GridDisplayMode.lattice_role(lines[0])
		var material := (
			ReplayVisuals.board_internal_scaffold_material(display_mode, interior_opacity, high_contrast)
			if role == GridDisplayMode.GRID_INTERIOR
			else ReplayVisuals.board_scaffold_material(display_mode, surface_opacity, high_contrast)
		)
		var batch_parent := parent
		if role == GridDisplayMode.GRID_FACE:
			var axis := int(lines[0].face_axis)
			var sign_value := float(lines[0].face_sign)
			var normal := Vector3.ZERO
			normal[axis] = sign_value
			var face := Node3D.new()
			face.name = "LatticeFace_%d_%s" % [axis, "Negative" if sign_value < 0.0 else "Positive"]
			face.set_meta("grid_axis", axis)
			face.set_meta("grid_sign", sign_value)
			face.set_meta("grid_center", parent.basis * (lines[0].start * normal.abs()) + parent.position)
			face.set_meta("grid_normal", parent.basis * normal)
			parent.add_child(face)
			if rear_faces_only:
				_rear_faces.append(face)
			batch_parent = face
		_add_geometry_segments(lines, thickness, material, batch_parent, role)


# Camera-relative rear faces stay visible; front and edge-on faces hide.
func _update_rear_faces(camera_position: Vector3) -> void:
	for face in _rear_faces:
		var center: Vector3 = face.get_meta("grid_center", Vector3.ZERO)
		var normal: Vector3 = face.get_meta("grid_normal", Vector3.BACK)
		face.visible = normal.dot(camera_position - center) < -0.0001


# Board-coordinate topology of every built lattice batch, per slice. Tests
# compare it across modes, styles and slices; it ignores material state and
# camera face visibility. visible_only reports what the camera currently shows.
func grid_topology(visible_only: bool = false) -> Array:
	var slices: Array = []
	for slice_root in get_children():
		if str(slice_root.get_meta("presentation_role", "")) != "board.slice_geometry":
			continue
		var lines: Array = []
		_collect_lattice_lines(slice_root, visible_only, lines)
		lines.sort_custom(func(left: Array, right: Array) -> bool: return str(left) < str(right))
		slices.append(lines)
	return slices


func _collect_lattice_lines(node: Node, visible_only: bool, lines: Array) -> void:
	for child in node.get_children():
		if visible_only and child is Node3D and not child.visible:
			continue
		if child.has_meta("lattice_lines"):
			lines.append_array(child.get_meta("lattice_lines"))
		_collect_lattice_lines(child, visible_only, lines)


func _add_outline_box(
	geometry,
	display_mode: String,
	material_override: Material = null,
	thickness_override: float = -1.0,
	presentation_role: String = GridDisplayMode.ENCLOSURE,
	high_contrast: bool = false,
	boundary_opacity: float = -1.0,
	parent: Node3D = null
) -> void:
	var board_material := ReplayVisuals.board_outline_material(display_mode, high_contrast, boundary_opacity) if material_override == null else material_override
	var thickness := ReplayVisuals.slice_outline_thickness(display_mode) if thickness_override < 0.0 else thickness_override
	_add_geometry_segments(geometry.boundary_geometry(), thickness, board_material, parent, presentation_role)


func _add_floor_face(geometry, display_mode: String, parent: Node3D) -> void:
	var bounds: Dictionary = geometry.local_bounds()
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var floor := MeshInstance3D.new()
	floor.name = "GravityFloor"
	floor.set_meta("boundary_role", "gravity_floor")
	floor.set_meta("presentation_role", GridDisplayMode.FLOOR)
	var mesh := BoxMesh.new()
	mesh.size = Vector3(geometry.local_extent.x, 0.025, geometry.local_extent.z)
	floor.mesh = mesh
	floor.material_override = ReplayVisuals.live_board_floor_material(display_mode)
	floor.position = geometry.center + Vector3(0.0, min_pos.y + 0.0125, 0.0)
	parent.add_child(floor)


func _add_spawn_entry_cue(
	geometry,
	display_mode: String,
	high_contrast: bool,
	parent: Node3D
) -> void:
	var bounds: Dictionary = geometry.local_bounds()
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	var label := Label3D.new()
	label.name = "SpawnEntryLabel"
	label.text = "SPAWN ENTRY  ↘"
	label.font_size = ReplayVisuals.SPAWN_ENTRY_LABEL_FONT_SIZE
	label.pixel_size = ReplayVisuals.SPAWN_ENTRY_LABEL_PIXEL_SIZE
	label.modulate = ReplayVisuals.color_for_role(
		ReplayVisuals.ROLE_TEXT if high_contrast else ReplayVisuals.ROLE_TEXT_DIM,
		display_mode
	)
	label.outline_modulate = ReplayVisuals.color_for_role(ReplayVisuals.ROLE_BACKGROUND, display_mode)
	label.outline_size = ReplayVisuals.SPAWN_ENTRY_LABEL_OUTLINE_SIZE
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	label.position = Vector3(
		min_pos.x - 0.18,
		max_pos.y + ReplayVisuals.SPAWN_ENTRY_LABEL_VERTICAL_OFFSET,
		min_pos.z - 0.03
	)
	label.set_meta("presentation_role", "board.spawn_entry_cue")
	parent.add_child(label)


func _add_geometry_segments(
	segments: Array,
	thickness: float,
	material: Material,
	parent: Node3D,
	presentation_role: String
) -> void:
	if segments.is_empty():
		return
	var lines := MultiMeshInstance3D.new()
	lines.set_meta("presentation_role", presentation_role)
	lines.set_meta("segment_count", segments.size())
	if GridDisplayMode.LATTICE_ROLE_BY_BOUNDARY_PLANES.has(presentation_role):
		lines.set_meta("lattice_lines", segments.map(func(line: Dictionary) -> Array:
			return [int(line.line_axis), line.lattice_start, line.lattice_end]))
	var batch := MultiMesh.new()
	batch.transform_format = MultiMesh.TRANSFORM_3D
	var unit := BoxMesh.new()
	unit.size = Vector3.ONE
	batch.mesh = unit
	batch.instance_count = segments.size()
	for index in range(segments.size()):
		batch.set_instance_transform(index, segment_transform(segments[index], thickness))
	lines.multimesh = batch
	lines.material_override = material
	lines.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(lines)


func _add_slice_label(
	layer_index: int,
	slice_bounds: Dictionary,
	display_mode: String,
	selected: bool,
	axis_label: String,
	semantic_coordinate: int
) -> void:
	var label := Label3D.new()
	label.name = "SliceLabel_%d" % layer_index
	label.text = "%s %d" % [axis_label, semantic_coordinate + 1]
	label.set_meta("display_mode", display_mode)
	label.set_meta("slice_axis", axis_label)
	label.set_meta("semantic_coordinate", semantic_coordinate)
	label.set_meta("presentation_layer", layer_index)
	label.font_size = ReplayVisuals.W_SLICE_LABEL_SELECTED_FONT_SIZE if selected else ReplayVisuals.W_SLICE_LABEL_FONT_SIZE
	label.pixel_size = ReplayVisuals.W_SLICE_LABEL_PIXEL_SIZE
	label.modulate = ReplayVisuals.color_for_role(ReplayVisuals.ROLE_TEXT, display_mode) if selected else ReplayVisuals.slice_label_color(display_mode)
	label.outline_modulate = ReplayVisuals.color_for_role(ReplayVisuals.ROLE_BACKGROUND, display_mode)
	label.outline_size = ReplayVisuals.W_SLICE_LABEL_OUTLINE_SIZE + (2 if selected else 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.set_meta("slice_bounds_min", slice_bounds.get("min", Vector3.ZERO))
	label.set_meta("slice_bounds_max", slice_bounds.get("max", Vector3.ZERO))
	label.set_meta("selected_slice", selected)
	add_child(label)
	_slice_labels.append(label)


func _update_slice_labels(camera_position: Vector3) -> void:
	for label in _slice_labels:
		var min_pos: Vector3 = label.get_meta("slice_bounds_min", Vector3.ZERO)
		var max_pos: Vector3 = label.get_meta("slice_bounds_max", Vector3.ZERO)
		var center := (min_pos + max_pos) * 0.5
		var camera_delta := camera_position - center
		var axis := Vector3.AXIS_X if absf(camera_delta.x) >= absf(camera_delta.z) else Vector3.AXIS_Z
		var camera_on_positive_side := camera_delta[axis] >= 0.0
		var position := Vector3(center.x, min_pos.y - ReplayVisuals.W_SLICE_LABEL_VERTICAL_OFFSET, center.z)
		position[axis] = (
			max_pos[axis] + ReplayVisuals.W_SLICE_LABEL_EDGE_OFFSET
			if camera_on_positive_side
			else min_pos[axis] - ReplayVisuals.W_SLICE_LABEL_EDGE_OFFSET
		)
		label.position = position
		label.set_meta("rear_face_axis", axis)
		label.set_meta("label_anchor_side", 1.0 if camera_on_positive_side else -1.0)


func _update_role_opacities(node: Node, mode: String, high_contrast: bool, enclosure: float, rear: float, internal: float, grid: float, boundary: float) -> void:
	if node is GeometryInstance3D:
		var material = node.material_override
		if material is StandardMaterial3D:
			match str(node.get_meta("presentation_role", "")):
				GridDisplayMode.ENCLOSURE:
					material.albedo_color.a = ReplayVisuals.board_enclosure_material(mode, enclosure, boundary, high_contrast).albedo_color.a
				GridDisplayMode.GRID_EDGE, GridDisplayMode.GRID_FACE:
					material.albedo_color.a = ReplayVisuals.board_scaffold_material(mode, ReplayVisuals.scaffold_alpha(rear, grid), high_contrast).albedo_color.a
				GridDisplayMode.GRID_INTERIOR:
					material.albedo_color.a = ReplayVisuals.board_internal_scaffold_material(mode, internal, high_contrast).albedo_color.a
	for child in node.get_children():
		_update_role_opacities(child, mode, high_contrast, enclosure, rear, internal, grid, boundary)


static func segment_transform(segment: Dictionary, thickness: float) -> Transform3D:
	var start: Vector3 = segment.get("start", Vector3.ZERO)
	var finish: Vector3 = segment.get("end", Vector3.ZERO)
	var delta := finish - start
	var size := Vector3(maxf(absf(delta.x), thickness), maxf(absf(delta.y), thickness), maxf(absf(delta.z), thickness))
	return Transform3D(Basis.from_scale(size), (start + finish) * 0.5)
