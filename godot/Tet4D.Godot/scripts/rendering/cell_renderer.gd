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
	_add_box(Vector3(0.0, 0.0, 0.018 if border_material != null else 0.0), Vector3(size, size, cell_depth), material)
	if border_material != null and border_size > size:
		_add_box(
			Vector3.ZERO,
			Vector3(border_size, border_size, maxf(depth, 0.02) * 0.65),
			border_material
		)
	self.position = position


func _add_box(local_position: Vector3, size: Vector3, material: Material) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	mesh_instance.position = local_position
	add_child(mesh_instance)
