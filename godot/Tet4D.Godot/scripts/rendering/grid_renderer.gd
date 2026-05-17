extends Node3D

class_name GridRenderer

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")


func rebuild(board_shape: Array, dimension: int, mapper, display_mode: String) -> void:
	for child in get_children():
		child.queue_free()

	if board_shape.is_empty():
		return
	var w_size := int(board_shape[3]) if dimension >= 4 and board_shape.size() > 3 else 1

	for w_index in range(w_size):
		var slice_bounds: Dictionary = mapper.slice_bounds(w_index)
		if not slice_bounds.get("ok", false):
			continue
		_add_outline_box(slice_bounds, display_mode)
		if dimension >= 4:
			_add_w_label(w_index, mapper.slice_label_position(w_index), display_mode)


func _add_outline_box(slice_bounds: Dictionary, display_mode: String) -> void:
	var board_material := ReplayVisuals.board_outline_material(display_mode)
	var thickness := ReplayVisuals.slice_outline_thickness(display_mode)
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


func _add_w_label(w_index: int, label_position: Vector3, display_mode: String) -> void:
	var label := Label3D.new()
	label.text = "W=%d" % w_index
	label.font_size = 42
	label.modulate = ReplayVisuals.slice_label_color(display_mode)
	label.outline_modulate = ReplayVisuals.color_for_role(ReplayVisuals.ROLE_BACKGROUND, display_mode)
	label.outline_size = 14
	label.position = label_position
	add_child(label)
