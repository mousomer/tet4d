extends Node3D

class_name ParticleRenderer


func setup(
	position: Vector3,
	shell_material: Material,
	core_material: Material,
	radius: float,
	velocity: Array = [],
	trail_material: Material = null,
	trail_positions: Array = []
) -> void:
	self.position = position
	var mesh_instance := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh_instance.mesh = mesh
	mesh_instance.material_override = shell_material
	add_child(mesh_instance)
	var core := MeshInstance3D.new()
	var core_mesh := SphereMesh.new()
	core_mesh.radius = radius * 0.45
	core_mesh.height = radius * 0.9
	core.mesh = core_mesh
	core.material_override = core_material
	add_child(core)
	if velocity.size() >= 3 and trail_material != null:
		var tail := MeshInstance3D.new()
		var tail_mesh := CylinderMesh.new()
		tail_mesh.top_radius = radius * 0.2
		tail_mesh.bottom_radius = radius * 0.08
		tail_mesh.height = max(radius * 1.5, _velocity_length(velocity) * 0.08)
		tail.mesh = tail_mesh
		tail.material_override = trail_material
		tail.rotation_degrees = Vector3(90.0, 0.0, 0.0)
		tail.position = Vector3(0.0, 0.0, -tail_mesh.height * 0.25)
		add_child(tail)
	if trail_material != null:
		_add_history_trail(trail_positions, radius, trail_material)


func _add_history_trail(trail_positions: Array, radius: float, trail_material: Material) -> void:
	if trail_positions.size() < 2:
		return
	for index in range(trail_positions.size() - 1):
		var trail_world_position := trail_positions[index] as Vector3
		var dot := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		var age := float(index + 1) / float(trail_positions.size())
		mesh.radius = radius * lerpf(0.16, 0.32, age)
		mesh.height = mesh.radius * 2.0
		dot.mesh = mesh
		dot.material_override = trail_material
		dot.position = trail_world_position - self.position
		add_child(dot)


func _velocity_length(velocity: Array) -> float:
	var sum := 0.0
	for value in velocity:
		sum += float(value) * float(value)
	return sqrt(sum)
