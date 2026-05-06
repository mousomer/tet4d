extends Node3D

class_name GridRenderer


func rebuild(board_shape: Array, dimension: int, slice_stride: float) -> void:
	for child in get_children():
		child.queue_free()

	if board_shape.is_empty():
		return

	var x_size := float(board_shape[0])
	var y_size := float(board_shape[1]) if board_shape.size() > 1 else 1.0
	var z_size := float(board_shape[2]) if board_shape.size() > 2 else 1.0
	var w_size := int(board_shape[3]) if dimension >= 4 and board_shape.size() > 3 else 1

	for w_index in range(w_size):
		var x_offset := float(w_index) * slice_stride
		_add_outline_box(Vector3(x_size, y_size, z_size), x_offset)
		if dimension >= 4:
			_add_w_label(w_index, x_offset, y_size)


func _add_outline_box(size: Vector3, x_offset: float) -> void:
	var line_color := Color(0.38, 0.41, 0.48, 1.0)
	var x0 := -0.5 + x_offset
	var x1 := size.x - 0.5 + x_offset
	var y0 := 0.5
	var y1 := -(size.y - 0.5)
	var z0 := -0.5
	var z1 := size.z - 0.5

	_add_line(Vector3((x0 + x1) * 0.5, y0, z0), Vector3(size.x, 0.03, 0.03), line_color)
	_add_line(Vector3((x0 + x1) * 0.5, y1, z0), Vector3(size.x, 0.03, 0.03), line_color)
	_add_line(Vector3((x0 + x1) * 0.5, y0, z1), Vector3(size.x, 0.03, 0.03), line_color)
	_add_line(Vector3((x0 + x1) * 0.5, y1, z1), Vector3(size.x, 0.03, 0.03), line_color)
	_add_line(Vector3(x0, (y0 + y1) * 0.5, z0), Vector3(0.03, size.y, 0.03), line_color)
	_add_line(Vector3(x1, (y0 + y1) * 0.5, z0), Vector3(0.03, size.y, 0.03), line_color)
	_add_line(Vector3(x0, (y0 + y1) * 0.5, z1), Vector3(0.03, size.y, 0.03), line_color)
	_add_line(Vector3(x1, (y0 + y1) * 0.5, z1), Vector3(0.03, size.y, 0.03), line_color)
	_add_line(Vector3(x0, y0, (z0 + z1) * 0.5), Vector3(0.03, 0.03, size.z), line_color)
	_add_line(Vector3(x1, y0, (z0 + z1) * 0.5), Vector3(0.03, 0.03, size.z), line_color)
	_add_line(Vector3(x0, y1, (z0 + z1) * 0.5), Vector3(0.03, 0.03, size.z), line_color)
	_add_line(Vector3(x1, y1, (z0 + z1) * 0.5), Vector3(0.03, 0.03, size.z), line_color)


func _add_line(position: Vector3, scale_value: Vector3, color: Color) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = scale_value
	mesh_instance.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.9
	mesh_instance.material_override = material
	mesh_instance.position = position
	add_child(mesh_instance)


func _add_w_label(w_index: int, x_offset: float, y_size: float) -> void:
	var label := Label3D.new()
	label.text = "W=%d" % w_index
	label.font_size = 36
	label.modulate = Color(0.86, 0.89, 0.94, 1.0)
	label.position = Vector3(x_offset, 1.2, 0.0)
	add_child(label)
