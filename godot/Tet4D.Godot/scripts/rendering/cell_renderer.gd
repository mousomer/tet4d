extends Node3D

class_name CellRenderer


func setup(
	position: Vector3,
	material: Material,
	size: float,
	depth: float = -1.0,
	border_material: Material = null,
	border_size: float = 0.0
) -> void:
	var cell_depth := size if depth < 0.0 else depth
	_add_box(Vector3.ZERO, Vector3(size, size, cell_depth), material)
	if border_material != null and border_size > size:
		_add_edge_outline(Vector3(border_size, border_size, cell_depth + (border_size - size)), border_size - size, border_material)
	self.position = position


func setup_exterior_block(
	position: Vector3,
	face_materials: Dictionary,
	outline_material: Material,
	size: float,
	outline_size: float,
	outline_pulse: float = 0.0,
	origin_marker_material: Material = null,
	origin_marker_size: float = 0.0
) -> void:
	_add_exterior_faces(size, face_materials)
	if outline_material != null and outline_size > size:
		_add_edge_outline(
			Vector3(outline_size, outline_size, outline_size),
			outline_size - size,
			outline_material,
			outline_pulse
		)
	if origin_marker_material != null and origin_marker_size > 0.0:
		_add_origin_marker(size, origin_marker_size, origin_marker_material)
	self.position = position


func _add_box(local_position: Vector3, size: Vector3, material: Material) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	mesh_instance.position = local_position
	add_child(mesh_instance)


func _add_exterior_faces(size: float, face_materials: Dictionary) -> void:
	var panel_depth := maxf(0.012, size * 0.028)
	var half := size * 0.5
	_add_box(
		Vector3(0.0, half + (panel_depth * 0.5), 0.0),
		Vector3(size, panel_depth, size),
		face_materials.get("top", face_materials.get("base"))
	)
	_add_box(
		Vector3(0.0, -half - (panel_depth * 0.5), 0.0),
		Vector3(size, panel_depth, size),
		face_materials.get("bottom", face_materials.get("base"))
	)
	_add_box(
		Vector3(0.0, 0.0, half + (panel_depth * 0.5)),
		Vector3(size, size, panel_depth),
		face_materials.get("front", face_materials.get("base"))
	)
	_add_box(
		Vector3(0.0, 0.0, -half - (panel_depth * 0.5)),
		Vector3(size, size, panel_depth),
		face_materials.get("back", face_materials.get("base"))
	)
	_add_box(
		Vector3(half + (panel_depth * 0.5), 0.0, 0.0),
		Vector3(panel_depth, size, size),
		face_materials.get("right", face_materials.get("base"))
	)
	_add_box(
		Vector3(-half - (panel_depth * 0.5), 0.0, 0.0),
		Vector3(panel_depth, size, size),
		face_materials.get("left", face_materials.get("base"))
	)


func _add_edge_outline(size: Vector3, border_delta: float, material: Material, outline_pulse: float = 0.0) -> void:
	var thickness := maxf(0.014, border_delta * (0.24 + (0.22 * clampf(outline_pulse, 0.0, 1.0))))
	var half := size * 0.5
	for y_sign in [-1.0, 1.0]:
		for z_sign in [-1.0, 1.0]:
			_add_box(
				Vector3(0.0, y_sign * half.y, z_sign * half.z),
				Vector3(size.x, thickness, thickness),
				material
			)
	for x_sign in [-1.0, 1.0]:
		for z_sign in [-1.0, 1.0]:
			_add_box(
				Vector3(x_sign * half.x, 0.0, z_sign * half.z),
				Vector3(thickness, size.y, thickness),
				material
			)
	for x_sign in [-1.0, 1.0]:
		for y_sign in [-1.0, 1.0]:
			_add_box(
				Vector3(x_sign * half.x, y_sign * half.y, 0.0),
				Vector3(thickness, thickness, size.z),
				material
			)


func _add_origin_marker(size: float, marker_size: float, material: Material) -> void:
	var half := size * 0.5
	var marker_half := marker_size * 0.5
	_add_box(
		Vector3(
			-half + marker_half * 1.15,
			half + marker_half * 0.65,
			half - marker_half * 1.15
		),
		Vector3(marker_size, marker_size, marker_size),
		material
	)
