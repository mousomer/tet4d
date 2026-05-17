extends Node3D

class_name EventMarkerRenderer

var _base_scale := 0.6


func setup(position: Vector3, material: Material, size: float, visibility: float = 1.0) -> void:
	_base_scale = size
	var mesh_instance := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = size * 0.35
	mesh.height = size * 0.7
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _material_with_visibility(material, visibility)
	add_child(mesh_instance)
	self.position = position


func _process(delta: float) -> void:
	var pulse := 1.0 + 0.16 * sin((Time.get_ticks_msec() / 1000.0) * 4.0)
	scale = Vector3.ONE * (_base_scale * pulse)


func _material_with_visibility(material: Material, visibility: float) -> Material:
	if not material is StandardMaterial3D:
		return material
	var copy := (material as StandardMaterial3D).duplicate() as StandardMaterial3D
	copy.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	copy.albedo_color.a = clampf(visibility, 0.25, 1.0)
	return copy
