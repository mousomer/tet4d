extends Node3D

class_name GridRenderer

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const PRESENTATION_ROLE_GRID := "board.grid"
const PRESENTATION_ROLE_FLOOR_GRID := "board.grid.floor"
const PRESENTATION_ROLE_WIREFRAME := "board.wireframe"
const PRESENTATION_ROLE_ACTIVE_FRAME := "board.frame_active"

var _rear_grid_faces: Array[Node3D] = []
var _slice_labels: Array[Label3D] = []


func _process(_delta: float) -> void:
	if _rear_grid_faces.is_empty():
		return
	var camera := get_viewport().get_camera_3d()
	if camera != null:
		var camera_position := to_local(camera.global_position)
		_update_rear_grid_faces(camera_position)
		_update_slice_labels(camera_position)


func rebuild(
	board_shape: Array,
	dimension: int,
	mapper,
	display_mode: String,
	live_2d: bool = false,
	show_w_labels: bool = true,
	active_layers: Array = [],
	board_detail: String = "standard",
	high_contrast: bool = false,
	show_grid: bool = true
) -> void:
	for child in get_children():
		child.queue_free()
	_rear_grid_faces.clear()
	_slice_labels.clear()

	if board_shape.is_empty():
		return
	var visible_board_shape: Array = mapper.visible_board_shape()
	var w_size: int = int(mapper.current_layer_count()) if dimension >= 4 else 1

	for w_index in range(w_size):
		var slice_bounds: Dictionary = mapper.slice_bounds(w_index)
		if not slice_bounds.get("ok", false):
			continue
		# The Grid: On control is authoritative: detail may tune the presentation,
		# but it must never silently suppress the lattice.
		if show_grid and live_2d and dimension >= 2:
			if dimension == 2:
				_add_flat_grid(slice_bounds, visible_board_shape, display_mode, high_contrast)
			else:
				_add_volumetric_boundary_grids(slice_bounds, visible_board_shape, display_mode, high_contrast)
		if live_2d and dimension >= 3:
			_add_floor_face(slice_bounds, display_mode)
			_add_floor_lattice(slice_bounds, visible_board_shape, display_mode, high_contrast)
		_add_outline_box(
			slice_bounds,
			display_mode,
			null,
			ReplayVisuals.slice_outline_thickness(display_mode) * (1.20 if high_contrast else 1.0),
			PRESENTATION_ROLE_WIREFRAME,
			high_contrast
		)
		if active_layers.has(w_index):
			_add_outline_box(
				slice_bounds,
				display_mode,
				ReplayVisuals.board_active_frame_material(display_mode, high_contrast),
				ReplayVisuals.slice_outline_thickness(display_mode) * (ReplayVisuals.ACTIVE_SLICE_FRAME_HIGH_CONTRAST_MULTIPLIER if high_contrast else ReplayVisuals.ACTIVE_SLICE_FRAME_MULTIPLIER),
				PRESENTATION_ROLE_ACTIVE_FRAME,
				high_contrast
			)
		if dimension >= 4 and show_w_labels:
			_add_slice_label(
				w_index,
				slice_bounds,
				display_mode,
				active_layers.has(w_index),
				mapper.slice_axis_label(),
				mapper.semantic_slice_coordinate(w_index)
			)
	var camera := get_viewport().get_camera_3d()
	if camera != null:
		var camera_position := to_local(camera.global_position)
		_update_rear_grid_faces(camera_position)
		_update_slice_labels(camera_position)


func _add_outline_box(
	slice_bounds: Dictionary,
	display_mode: String,
	material_override: Material = null,
	thickness_override: float = -1.0,
	presentation_role: String = PRESENTATION_ROLE_WIREFRAME,
	high_contrast: bool = false
) -> void:
	var board_material := ReplayVisuals.board_outline_material(display_mode, high_contrast) if material_override == null else material_override
	var thickness := ReplayVisuals.slice_outline_thickness(display_mode) if thickness_override < 0.0 else thickness_override
	var min_pos: Vector3 = slice_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = slice_bounds.get("max", Vector3.ZERO)
	var x0 := min_pos.x
	var x1 := max_pos.x
	var y0 := max_pos.y
	var y1 := min_pos.y
	var z0 := min_pos.z
	var z1 := max_pos.z
	var size := max_pos - min_pos

	_add_line(Vector3((x0 + x1) * 0.5, y0, z0), Vector3(size.x, thickness, thickness), board_material, null, presentation_role)
	_add_line(Vector3((x0 + x1) * 0.5, y1, z0), Vector3(size.x, thickness, thickness), board_material, null, presentation_role)
	_add_line(Vector3((x0 + x1) * 0.5, y0, z1), Vector3(size.x, thickness, thickness), board_material, null, presentation_role)
	_add_line(Vector3((x0 + x1) * 0.5, y1, z1), Vector3(size.x, thickness, thickness), board_material, null, presentation_role)
	_add_line(Vector3(x0, (y0 + y1) * 0.5, z0), Vector3(thickness, size.y, thickness), board_material, null, presentation_role)
	_add_line(Vector3(x1, (y0 + y1) * 0.5, z0), Vector3(thickness, size.y, thickness), board_material, null, presentation_role)
	_add_line(Vector3(x0, (y0 + y1) * 0.5, z1), Vector3(thickness, size.y, thickness), board_material, null, presentation_role)
	_add_line(Vector3(x1, (y0 + y1) * 0.5, z1), Vector3(thickness, size.y, thickness), board_material, null, presentation_role)
	_add_line(Vector3(x0, y0, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material, null, presentation_role)
	_add_line(Vector3(x1, y0, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material, null, presentation_role)
	_add_line(Vector3(x0, y1, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material, null, presentation_role)
	_add_line(Vector3(x1, y1, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material, null, presentation_role)


func _add_line(
	position: Vector3,
	scale_value: Vector3,
	material: Material,
	parent: Node3D = null,
	presentation_role: String = ""
) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = scale_value
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	mesh_instance.position = position
	if not presentation_role.is_empty():
		mesh_instance.set_meta("presentation_role", presentation_role)
	var target_parent: Node3D = self if parent == null else parent
	target_parent.add_child(mesh_instance)


func _add_floor_face(slice_bounds: Dictionary, display_mode: String) -> void:
	var min_pos: Vector3 = slice_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = slice_bounds.get("max", Vector3.ZERO)
	var floor := MeshInstance3D.new()
	floor.name = "GravityFloor"
	floor.set_meta("boundary_role", "gravity_floor")
	var mesh := BoxMesh.new()
	mesh.size = Vector3(max_pos.x - min_pos.x, 0.025, max_pos.z - min_pos.z)
	floor.mesh = mesh
	floor.material_override = ReplayVisuals.live_board_floor_material(display_mode)
	floor.position = Vector3((min_pos.x + max_pos.x) * 0.5, min_pos.y + 0.0125, (min_pos.z + max_pos.z) * 0.5)
	add_child(floor)


func _add_floor_lattice(slice_bounds: Dictionary, board_shape: Array, display_mode: String, high_contrast: bool) -> void:
	if board_shape.size() < 3:
		return
	var min_pos: Vector3 = slice_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = slice_bounds.get("max", Vector3.ZERO)
	var thickness := ReplayVisuals.grid_internal_thickness(high_contrast) * 0.86
	var material := ReplayVisuals.live_board_floor_grid_material(display_mode, high_contrast)
	var floor_y := min_pos.y + thickness * 0.70
	var lattice := Node3D.new()
	lattice.name = "GravityFloorLattice"
	lattice.set_meta("boundary_role", "gravity_floor_lattice")
	add_child(lattice)
	for x_index in range(1, int(board_shape[0])):
		var x_pos := min_pos.x + float(x_index)
		_add_line(Vector3(x_pos, floor_y, (min_pos.z + max_pos.z) * 0.5), Vector3(thickness, thickness, max_pos.z - min_pos.z), material, lattice, PRESENTATION_ROLE_FLOOR_GRID)
	for z_index in range(1, int(board_shape[2])):
		var z_pos := min_pos.z + float(z_index)
		_add_line(Vector3((min_pos.x + max_pos.x) * 0.5, floor_y, z_pos), Vector3(max_pos.x - min_pos.x, thickness, thickness), material, lattice, PRESENTATION_ROLE_FLOOR_GRID)


func _add_flat_grid(slice_bounds: Dictionary, board_shape: Array, display_mode: String, high_contrast: bool) -> void:
	if board_shape.size() < 2:
		return
	var width := int(board_shape[0])
	var height := int(board_shape[1])
	var min_pos: Vector3 = slice_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = slice_bounds.get("max", Vector3.ZERO)
	var thickness := ReplayVisuals.grid_internal_thickness(high_contrast)
	var material := ReplayVisuals.live_board_grid_material(display_mode, high_contrast)
	var grid_z := min_pos.z - 0.02
	for x in range(1, width):
		var x_pos := min_pos.x + float(x)
		_add_line(
			Vector3(x_pos, (min_pos.y + max_pos.y) * 0.5, grid_z),
			Vector3(thickness, max_pos.y - min_pos.y, thickness),
			material,
			null,
			PRESENTATION_ROLE_GRID
		)
	for y in range(1, height):
		var y_pos := min_pos.y + float(y)
		_add_line(
			Vector3((min_pos.x + max_pos.x) * 0.5, y_pos, grid_z + 0.002),
			Vector3(max_pos.x - min_pos.x, thickness, thickness),
			material,
			null,
			PRESENTATION_ROLE_GRID
		)


func _add_volumetric_boundary_grids(slice_bounds: Dictionary, board_shape: Array, display_mode: String, high_contrast: bool) -> void:
	if board_shape.size() < 3:
		return
	var min_pos: Vector3 = slice_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = slice_bounds.get("max", Vector3.ZERO)
	var center := (min_pos + max_pos) * 0.5
	var thickness := ReplayVisuals.grid_internal_thickness(high_contrast)
	var material := ReplayVisuals.live_board_grid_material(display_mode, high_contrast)
	for axis in range(3):
		for sign_value in [-1.0, 1.0]:
			var face := Node3D.new()
			face.name = "RearGridFace_%d_%s" % [axis, "Negative" if sign_value < 0.0 else "Positive"]
			face.set_meta("grid_axis", axis)
			face.set_meta("grid_sign", sign_value)
			face.set_meta("grid_center", center)
			face.set_meta("presentation_role", PRESENTATION_ROLE_GRID)
			add_child(face)
			_rear_grid_faces.append(face)
			_add_boundary_face_grid(face, axis, sign_value, min_pos, max_pos, board_shape, thickness, material)


func _add_boundary_face_grid(
	face: Node3D,
	axis: int,
	sign_value: float,
	min_pos: Vector3,
	max_pos: Vector3,
	board_shape: Array,
	thickness: float,
	material: Material
) -> void:
	var inward_offset := thickness * 0.55
	if axis == Vector3.AXIS_X:
		var x_pos := (min_pos.x if sign_value < 0.0 else max_pos.x) - sign_value * inward_offset
		for z_index in range(1, int(board_shape[2])):
			var z_pos := min_pos.z + float(z_index)
			_add_line(Vector3(x_pos, (min_pos.y + max_pos.y) * 0.5, z_pos), Vector3(thickness, max_pos.y - min_pos.y, thickness), material, face, PRESENTATION_ROLE_GRID)
		for y_index in range(1, int(board_shape[1])):
			var y_pos := min_pos.y + float(y_index)
			_add_line(Vector3(x_pos, y_pos, (min_pos.z + max_pos.z) * 0.5), Vector3(thickness, thickness, max_pos.z - min_pos.z), material, face, PRESENTATION_ROLE_GRID)
	elif axis == Vector3.AXIS_Y:
		var y_pos := (min_pos.y if sign_value < 0.0 else max_pos.y) - sign_value * inward_offset
		for x_index in range(1, int(board_shape[0])):
			var x_pos := min_pos.x + float(x_index)
			_add_line(Vector3(x_pos, y_pos, (min_pos.z + max_pos.z) * 0.5), Vector3(thickness, thickness, max_pos.z - min_pos.z), material, face, PRESENTATION_ROLE_GRID)
		for z_index in range(1, int(board_shape[2])):
			var z_pos := min_pos.z + float(z_index)
			_add_line(Vector3((min_pos.x + max_pos.x) * 0.5, y_pos, z_pos), Vector3(max_pos.x - min_pos.x, thickness, thickness), material, face, PRESENTATION_ROLE_GRID)
	else:
		var z_pos := (min_pos.z if sign_value < 0.0 else max_pos.z) - sign_value * inward_offset
		for x_index in range(1, int(board_shape[0])):
			var x_pos := min_pos.x + float(x_index)
			_add_line(Vector3(x_pos, (min_pos.y + max_pos.y) * 0.5, z_pos), Vector3(thickness, max_pos.y - min_pos.y, thickness), material, face, PRESENTATION_ROLE_GRID)
		for y_index in range(1, int(board_shape[1])):
			var y_pos := min_pos.y + float(y_index)
			_add_line(Vector3((min_pos.x + max_pos.x) * 0.5, y_pos, z_pos), Vector3(max_pos.x - min_pos.x, thickness, thickness), material, face, PRESENTATION_ROLE_GRID)


func _update_rear_grid_faces(camera_position: Vector3) -> void:
	for face in _rear_grid_faces:
		var axis := int(face.get_meta("grid_axis", 0))
		var sign_value := float(face.get_meta("grid_sign", -1.0))
		var center: Vector3 = face.get_meta("grid_center", Vector3.ZERO)
		var camera_delta := camera_position[axis] - center[axis]
		face.visible = sign_value * camera_delta <= 0.0


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
		var sign_value := -1.0 if camera_delta[axis] >= 0.0 else 1.0
		var inward_offset := 0.035
		var position := Vector3(center.x, max_pos.y - 0.55, center.z)
		position[axis] = (min_pos[axis] + inward_offset) if sign_value < 0.0 else (max_pos[axis] - inward_offset)
		label.position = position
		label.set_meta("rear_face_axis", axis)
		label.set_meta("rear_face_sign", sign_value)


func _add_w_label_chip(label_position: Vector3, display_mode: String) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3(
		ReplayVisuals.W_SLICE_LABEL_CHIP_WIDTH,
		ReplayVisuals.W_SLICE_LABEL_CHIP_HEIGHT,
		ReplayVisuals.W_SLICE_LABEL_CHIP_DEPTH
	)
	mesh_instance.mesh = mesh
	mesh_instance.material_override = ReplayVisuals.slice_label_chip_material(display_mode)
	mesh_instance.position = label_position + Vector3(0.0, 0.0, -0.02)
	add_child(mesh_instance)
