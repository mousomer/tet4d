extends Node3D

class_name ParticleRenderer


func setup(position: Vector3, color: Color, radius: float, velocity: Array = []) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _make_material(color)
	add_child(mesh_instance)
	if velocity.size() >= 3:
		var tail := MeshInstance3D.new()
		var tail_mesh := CylinderMesh.new()
		tail_mesh.top_radius = radius * 0.2
		tail_mesh.bottom_radius = radius * 0.08
		tail_mesh.height = max(radius * 1.5, _velocity_length(velocity) * 0.08)
		tail.mesh = tail_mesh
		tail.material_override = _make_material(color.darkened(0.25))
		tail.rotation_degrees = Vector3(90.0, 0.0, 0.0)
		tail.position = Vector3(0.0, 0.0, -tail_mesh.height * 0.25)
		add_child(tail)
	self.position = position


func _make_material(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color * 0.35
	material.roughness = 0.18
	return material


func _velocity_length(velocity: Array) -> float:
	var sum := 0.0
	for value in velocity:
		sum += float(value) * float(value)
	return sqrt(sum)
