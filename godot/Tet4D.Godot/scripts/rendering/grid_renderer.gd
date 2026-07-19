extends Node3D

class_name GridRenderer

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")


func rebuild(
	board_shape: Array,
	dimension: int,
	mapper,
	display_mode: String,
	live_2d: bool = false,
	show_w_labels: bool = true,
	active_layers: Array = [],
	board_detail: String = "standard",
	high_contrast: bool = false
) -> void:
	for child in get_children():
		child.queue_free()

	if board_shape.is_empty():
		return
	var w_size := int(board_shape[3]) if dimension >= 4 and board_shape.size() > 3 else 1

	for w_index in range(w_size):
		var slice_bounds: Dictionary = mapper.slice_bounds(w_index)
		if not slice_bounds.get("ok", false):
			continue
		if live_2d and (dimension == 2 or dimension >= 4) and board_detail != "minimal":
			_add_live_grid(slice_bounds, board_shape, display_mode)
		_add_outline_box(slice_bounds, display_mode)
		if board_detail == "full":
			_add_outline_box(
				slice_bounds,
				display_mode,
				ReplayVisuals.live_board_grid_material(display_mode),
				ReplayVisuals.slice_outline_thickness(display_mode) * 0.72
			)
		if live_2d and dimension >= 4:
			_add_outline_box(
				slice_bounds,
				display_mode,
				ReplayVisuals.board_outline_material(display_mode),
				ReplayVisuals.slice_outline_thickness(display_mode) * 1.55
			)
		if active_layers.has(w_index):
			_add_outline_box(
				slice_bounds,
				display_mode,
				ReplayVisuals.live_active_cell_border_material(display_mode),
				ReplayVisuals.slice_outline_thickness(display_mode) * (3.4 if high_contrast else 2.4)
			)
		if dimension >= 4 and show_w_labels:
			_add_w_label(w_index, w_size, mapper.slice_label_position(w_index), display_mode, active_layers.has(w_index), high_contrast)


func _add_outline_box(slice_bounds: Dictionary, display_mode: String, material_override: Material = null, thickness_override: float = -1.0) -> void:
	var board_material := ReplayVisuals.board_outline_material(display_mode) if material_override == null else material_override
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

	_add_line(Vector3((x0 + x1) * 0.5, y0, z0), Vector3(size.x, thickness, thickness), board_material)
	_add_line(Vector3((x0 + x1) * 0.5, y1, z0), Vector3(size.x, thickness, thickness), board_material)
	_add_line(Vector3((x0 + x1) * 0.5, y0, z1), Vector3(size.x, thickness, thickness), board_material)
	_add_line(Vector3((x0 + x1) * 0.5, y1, z1), Vector3(size.x, thickness, thickness), board_material)
	_add_line(Vector3(x0, (y0 + y1) * 0.5, z0), Vector3(thickness, size.y, thickness), board_material)
	_add_line(Vector3(x1, (y0 + y1) * 0.5, z0), Vector3(thickness, size.y, thickness), board_material)
	_add_line(Vector3(x0, (y0 + y1) * 0.5, z1), Vector3(thickness, size.y, thickness), board_material)
	_add_line(Vector3(x1, (y0 + y1) * 0.5, z1), Vector3(thickness, size.y, thickness), board_material)
	_add_line(Vector3(x0, y0, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material)
	_add_line(Vector3(x1, y0, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material)
	_add_line(Vector3(x0, y1, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material)
	_add_line(Vector3(x1, y1, (z0 + z1) * 0.5), Vector3(thickness, thickness, size.z), board_material)


func _add_line(position: Vector3, scale_value: Vector3, material: Material) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = scale_value
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	mesh_instance.position = position
	add_child(mesh_instance)


func _add_live_grid(slice_bounds: Dictionary, board_shape: Array, display_mode: String) -> void:
	if board_shape.size() < 2:
		return
	var width := int(board_shape[0])
	var height := int(board_shape[1])
	var min_pos: Vector3 = slice_bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = slice_bounds.get("max", Vector3.ZERO)
	var thickness := ReplayVisuals.GRID_LINE_THICKNESS * 0.55
	var material := ReplayVisuals.live_board_grid_material(display_mode)
	for x in range(width + 1):
		var x_pos := min_pos.x + float(x)
		_add_line(
			Vector3(x_pos, (min_pos.y + max_pos.y) * 0.5, -0.02),
			Vector3(thickness, max_pos.y - min_pos.y, thickness),
			material
		)
	for y in range(height + 1):
		var y_pos := min_pos.y + float(y)
		_add_line(
			Vector3((min_pos.x + max_pos.x) * 0.5, y_pos, -0.018),
			Vector3(max_pos.x - min_pos.x, thickness, thickness),
			material
		)


func _add_w_label(w_index: int, w_size: int, label_position: Vector3, display_mode: String, selected: bool, high_contrast: bool) -> void:
	var label := Label3D.new()
	label.text = "w%d ◀" % [w_index + 1] if selected else "w%d" % [w_index + 1]
	label.font_size = ReplayVisuals.W_SLICE_LABEL_FONT_SIZE
	label.modulate = ReplayVisuals.slice_label_color(display_mode)
	label.outline_modulate = ReplayVisuals.color_for_role(ReplayVisuals.ROLE_BACKGROUND, display_mode)
	label.outline_size = ReplayVisuals.W_SLICE_LABEL_OUTLINE_SIZE + (4 if selected and high_contrast else (2 if selected else 0))
	label.position = label_position + Vector3(0.0, 0.0, 0.015)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)


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
