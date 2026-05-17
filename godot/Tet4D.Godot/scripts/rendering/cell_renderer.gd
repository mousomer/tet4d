extends Node3D

class_name CellRenderer


func setup(position: Vector3, material: Material, size: float) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE * size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	add_child(mesh_instance)
	self.position = position
