extends Node3D

# Draw only native-supplied pairings. Axis/side select a rectangle edge; the
# native tangent sign supplies the correspondence, never a preset-name map.
const Visuals = preload("res://scripts/ui/replay_visuals.gd")
var _key: Array = []
var generation := 0


func rebuild(snapshot: Dictionary, model, display_mode: String) -> void:
	var seams: Array = snapshot.get("explorer_seams", []) if model.dimension == 2 else []
	visible = not seams.is_empty()
	var key := [seams, snapshot.get("board_shape", []), display_mode]
	if key == _key: return
	_key = key.duplicate(true)
	generation += 1
	for child in get_children():
		remove_child(child)
		child.queue_free()
	if seams.is_empty(): return
	var origin: Vector3 = model.render_cell_world_position([0, 0])
	var dx: Vector3 = model.render_cell_world_position([1, 0]) - origin
	var dy: Vector3 = model.render_cell_world_position([0, 1]) - origin
	var shape: Array = snapshot.board_shape
	for index in seams.size():
		var seam: Dictionary = seams[index]
		var color := Visuals.axis_color("X" if index % 2 == 0 else "Z", false, display_mode)
		for end in ["source", "target"]:
			var axis := int(seam[end + "_axis"])
			var side := int(seam[end + "_side"])
			var sign_value := int(seam.tangent_sign) if end == "target" else 1
			var start := Vector2.ZERO
			var finish := Vector2.ZERO
			start[axis] = -0.5 if side < 0 else float(shape[axis]) - 0.5
			finish[axis] = start[axis]
			start[1 - axis] = -0.5
			finish[1 - axis] = float(shape[1 - axis]) - 0.5
			var edge := Node3D.new()
			edge.name = "Seam_%d_%s" % [index, end]
			edge.set_meta("seam_id", seam.id)
			edge.set_meta("tangent_sign", sign_value)
			edge.set_meta("boundary_axis", axis)
			edge.set_meta("boundary_side", side)
			add_child(edge)
			var offset := Vector2.ZERO
			offset[axis] = side * Visuals.SEAM_ARROW_EDGE_OFFSET
			var a := start.lerp(finish, 0.25) + offset
			var b := start.lerp(finish, 0.75) + offset
			if sign_value < 0:
				var swap := a
				a = b
				b = swap
			var direction := (b - a).normalized()
			var normal := Vector2(-direction.y, direction.x)
			var wing := b - direction * Visuals.SEAM_ARROW_HEAD_SIZE
			var segments := [start, finish, a, b, b, wing + normal * Visuals.SEAM_ARROW_HEAD_SIZE, b, wing - normal * Visuals.SEAM_ARROW_HEAD_SIZE]
			var mesh := ImmediateMesh.new()
			mesh.surface_begin(Mesh.PRIMITIVE_LINES)
			for point in segments:
				mesh.surface_add_vertex(origin + dx * point.x + dy * point.y + Vector3(0, 0, Visuals.SEAM_FRONT_OFFSET))
			mesh.surface_end()
			var line := MeshInstance3D.new()
			line.mesh = mesh
			var material := StandardMaterial3D.new()
			material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			material.albedo_color = color
			material.no_depth_test = true
			line.material_override = material
			edge.add_child(line)
			var label := Label3D.new()
			label.name = "PairLabel"
			label.text = String.chr(97 + index)
			label.font_size = Visuals.BOARD_LABEL_FONT_SIZE
			label.pixel_size = Visuals.BOARD_LABEL_PIXEL_SIZE
			label.outline_size = Visuals.BOARD_LABEL_OUTLINE_SIZE
			label.modulate = color
			label.outline_modulate = Visuals.color_for_role(Visuals.ROLE_BACKGROUND, display_mode)
			label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			label.no_depth_test = true
			var midpoint := (start + finish) / 2.0
			midpoint[axis] += side * Visuals.SEAM_LABEL_EDGE_OFFSET
			label.position = origin + dx * midpoint.x + dy * midpoint.y + Vector3(0, 0, Visuals.SEAM_FRONT_OFFSET)
			edge.add_child(label)
