extends Node3D

class_name EventMarkerRenderer

var _base_scale := 0.6


func setup(position: Vector3, color: Color, size: float) -> void:
	_base_scale = size
	var mesh_instance := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = size * 0.35
	mesh.height = size * 0.7
	mesh_instance.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color * 0.8
	mesh_instance.material_override = material
	add_child(mesh_instance)
	self.position = position


func _process(delta: float) -> void:
	var pulse := 1.0 + 0.16 * sin((Time.get_ticks_msec() / 1000.0) * 4.0)
	scale = Vector3.ONE * (_base_scale * pulse)
