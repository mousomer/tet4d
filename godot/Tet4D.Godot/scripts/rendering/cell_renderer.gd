extends Node3D

class_name CellRenderer

# Unweighted albedo and emission per material, captured on first weighting.
var _base_colors: Dictionary = {}
var _presentation_weight := 1.0


func setup(
	position: Vector3,
	material: Material,
	size: float,
	depth: float = -1.0,
	border_material: Material = null,
	border_size: float = 0.0,
	bevel: Dictionary = {}
) -> void:
	var cell_depth := size if depth < 0.0 else depth
	# With a bevel the body shrinks to the inner square and the strips tile the
	# rim, so every pixel of the cell is one layer at the configured opacity.
	var body := size - 2.0 * size * float(bevel.get("width", 0.0)) if not bevel.is_empty() else size
	_add_box(Vector3.ZERO, Vector3(body, body, cell_depth), material)
	if border_material != null and border_size > size:
		_add_edge_outline(Vector3(border_size, border_size, cell_depth + (border_size - size)), border_size - size, border_material)
	if not bevel.is_empty():
		_add_bevel(size, cell_depth, bevel)
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


# Stage 58C: a cell recedes by scaling every material colour it draws with
# toward black; alpha, geometry and draw order are unchanged.
func set_presentation_weight(weight: float) -> void:
	if is_equal_approx(weight, _presentation_weight):
		return
	_presentation_weight = weight
	if _base_colors.is_empty():
		for child in get_children():
			if not child is GeometryInstance3D:
				continue
			var material := (child as GeometryInstance3D).material_override as StandardMaterial3D
			if material != null and not _base_colors.has(material):
				_base_colors[material] = [material.albedo_color, material.emission]
	for material in _base_colors:
		var albedo: Color = _base_colors[material][0]
		var emission: Color = _base_colors[material][1]
		material.albedo_color = Color(albedo.r * weight, albedo.g * weight, albedo.b * weight, albedo.a)
		material.emission = Color(emission.r * weight, emission.g * weight, emission.b * weight)


func presentation_weight() -> float:
	return _presentation_weight


func _add_box(local_position: Vector3, size: Vector3, material: Material) -> void:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	mesh_instance.position = local_position
	add_child(mesh_instance)


# A camera-facing quad centred on the cell; its material draws the halo.
func add_halo(material: Material, size: float) -> void:
	if material == null:
		return
	var mesh_instance := MeshInstance3D.new()
	mesh_instance.name = "Halo"
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	mesh_instance.mesh = quad
	mesh_instance.material_override = material
	mesh_instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mesh_instance)


# A flat cell's bevel: light strips on the top and left rims, dark strips on
# the bottom and right, laid on the camera-facing face. The four strips tile
# the rim without overlapping, so no two coplanar strips fight for depth.
func _add_bevel(size: float, depth: float, bevel: Dictionary) -> void:
	var width := size * float(bevel.get("width", 0.16))
	var thickness := maxf(0.002, size * 0.01)
	var z := depth * 0.5 - thickness * 0.5
	var half := size * 0.5
	var light: Material = bevel.get("light")
	var dark: Material = bevel.get("dark")
	_add_box(Vector3(0.0, half - width * 0.5, z), Vector3(size, width, thickness), light)
	_add_box(Vector3(-half + width * 0.5, -width * 0.5, z), Vector3(width, size - width, thickness), light)
	_add_box(Vector3(width * 0.5, -half + width * 0.5, z), Vector3(size - width, width, thickness), dark)
	_add_box(Vector3(half - width * 0.5, 0.0, z), Vector3(width, size - width * 2.0, thickness), dark)


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
