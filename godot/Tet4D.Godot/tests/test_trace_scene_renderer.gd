extends RefCounted

const TraceSceneRendererScript = preload("res://scripts/rendering/trace_scene_renderer.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["trace scene renderer test requires SceneTree"]
	var renderer := TraceSceneRendererScript.new()
	tree.root.add_child(renderer)
	await tree.process_frame

	var snapshot := {
		"case_id": "gameplay_snap_policy",
		"frame_index": 0,
		"dimension": 2,
		"board_shape": [4, 4],
		"locked_cells": [],
		"active_cells": [{"position": [0, 0], "color_id": 1}],
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
	}
	var next_snapshot := snapshot.duplicate(true)
	next_snapshot["frame_index"] = 1
	next_snapshot["active_cells"] = [{"position": [3, 3], "color_id": 1}]

	renderer.render_interpolated_snapshot(snapshot, next_snapshot, 0.85)
	var cell_root := renderer.get_node_or_null("CellRoot")
	if cell_root == null or cell_root.get_child_count() != 1:
		failures.append("gameplay renderer should create one active cell")
	else:
		var cell := cell_root.get_child(0) as Node3D
		_assert_vector(failures, cell.position, Vector3(-1.5, 1.5, 0.0), "gameplay active cells snap to current frame")
		var mesh_instance := cell.get_child(0) as MeshInstance3D
		if mesh_instance == null:
			failures.append("gameplay active cell should contain a mesh")
		else:
			var material := mesh_instance.material_override as StandardMaterial3D
			if material == null:
				failures.append("gameplay active cell should have a StandardMaterial3D")
			else:
				_assert_color(failures, material.albedo_color, ReplayVisuals.color_for_role(ReplayVisuals.ROLE_ACTIVE_CELL), "gameplay active cells use role color")
			var box := mesh_instance.mesh as BoxMesh
			if box == null:
				failures.append("gameplay active cell should use a box mesh")
			elif absf(box.size.x - ReplayVisuals.ACTIVE_GAMEPLAY_CELL_SCALE) > 0.001:
				failures.append("gameplay active cell scale should keep adjacent cells separated")

	renderer.render_snapshot({
		"case_id": "live_plain_2d",
		"trace_type": "live_2d",
		"frame_index": 0,
		"dimension": 2,
		"board_shape": [4, 4],
		"locked_cells": [{"position": [1, 3], "color_id": 4}],
		"active_cells": [{"position": [1, 1], "color_id": 2}],
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
	})
	await tree.process_frame
	cell_root = renderer.get_node_or_null("CellRoot")
	if cell_root == null or cell_root.get_child_count() != 2:
		failures.append("live renderer should create active and locked cells")
	else:
		var locked_cell := cell_root.get_child(0) as Node3D
		var active_cell := cell_root.get_child(1) as Node3D
		_assert_cell_material(
			failures,
			locked_cell,
			ReplayVisuals.live_locked_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 4).albedo_color,
			"live locked cells use piece-aware secondary material"
		)
		_assert_cell_material(
			failures,
			active_cell,
			ReplayVisuals.live_active_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 2).albedo_color,
			"live active cells use bright piece-aware material"
		)
		_assert_box_size(failures, active_cell, ReplayVisuals.LIVE_ACTIVE_CELL_SCALE, "live active cell scale")
		_assert_box_size(failures, locked_cell, ReplayVisuals.LIVE_LOCKED_CELL_SCALE, "live locked cell scale")
		if active_cell.get_child_count() < 2:
			failures.append("live active cell should include a crisp border mesh")
		if locked_cell.get_child_count() < 2:
			failures.append("live locked cell should include a crisp border mesh")
	var grid_root := renderer.get_node_or_null("GridRoot")
	if grid_root == null or grid_root.get_child_count() != 1:
		failures.append("live renderer should keep one shared grid renderer")
	else:
		var live_grid := grid_root.get_child(0)
		if live_grid.get_child_count() <= 12:
			failures.append("live renderer should include board fill/grid lines beyond the outline")

	renderer.render_snapshot({
		"case_id": "live_plain_3d",
		"trace_type": "live_3d",
		"frame_index": 0,
		"dimension": 3,
		"board_shape": [4, 5, 4],
		"locked_cells": [{"position": [1, 4, 1], "color_id": 4}],
		"active_cells": [{"position": [1, 1, 2], "color_id": 6}],
		"last_command": "rotate_xz_pos",
		"last_command_status": "accepted",
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
	})
	await tree.process_frame
	cell_root = renderer.get_node_or_null("CellRoot")
	if cell_root == null or cell_root.get_child_count() != 2:
		failures.append("live 3D renderer should create active and locked cells through the shared renderer")
	else:
		var live_3d_locked_cell := cell_root.get_child(0) as Node3D
		var live_3d_active_cell := cell_root.get_child(1) as Node3D
		_assert_cell_material(
			failures,
			live_3d_locked_cell,
			ReplayVisuals.live_3d_locked_face_materials(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 4).get("top").albedo_color,
			"live 3D locked cells use piece-aware exterior face material"
		)
		_assert_cell_material(
			failures,
			live_3d_active_cell,
			ReplayVisuals.live_3d_active_face_materials(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 6).get("top").albedo_color,
			"live 3D active cells use bright exterior face material"
		)
		_assert_box_size(failures, live_3d_active_cell, ReplayVisuals.LIVE_3D_ACTIVE_CELL_SCALE, "live 3D active cell scale")
		_assert_box_depth(failures, live_3d_active_cell, ReplayVisuals.LIVE_3D_ACTIVE_CELL_SCALE, "live 3D active cell depth")
		_assert_lit_material(failures, live_3d_active_cell, "live 3D active cell material")
		_assert_live_3d_exterior_block(failures, live_3d_active_cell, "live 3D active cell")
		_assert_live_3d_exterior_block(failures, live_3d_locked_cell, "live 3D locked cell")
		_assert_rotation_pulse_outline(failures, live_3d_active_cell, "live 3D active rotation pulse")
		_assert_live_3d_active_priority(failures, live_3d_active_cell, live_3d_locked_cell)
		_assert_live_3d_origin_marker(failures, live_3d_active_cell)
		if ReplayVisuals.color_for_role(ReplayVisuals.ROLE_LIVE_3D_ACTIVE).a < 0.99:
			failures.append("live 3D active role should be opaque")
		if ReplayVisuals.color_for_role(ReplayVisuals.ROLE_LIVE_3D_LOCKED).a < 0.99:
			failures.append("live 3D locked role should be opaque")
	grid_root = renderer.get_node_or_null("GridRoot")
	if grid_root == null or grid_root.get_child_count() != 1:
		failures.append("live 3D renderer should keep one shared grid renderer")

	renderer.queue_free()
	await tree.process_frame
	return failures


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_color(failures: Array, actual: Color, expected: Color, label: String) -> void:
	var tolerance := 0.01
	if (
		absf(actual.r - expected.r) > tolerance
		or absf(actual.g - expected.g) > tolerance
		or absf(actual.b - expected.b) > tolerance
		or absf(actual.a - expected.a) > tolerance
	):
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_cell_material(failures: Array, cell: Node3D, expected: Color, label: String) -> void:
	var mesh_instance := cell.get_child(0) as MeshInstance3D
	if mesh_instance == null:
		failures.append("%s: missing mesh" % label)
		return
	var material := mesh_instance.material_override as StandardMaterial3D
	if material == null:
		failures.append("%s: missing StandardMaterial3D" % label)
		return
	_assert_color(failures, material.albedo_color, expected, label)


func _assert_box_size(failures: Array, cell: Node3D, expected: float, label: String) -> void:
	var mesh_instance := cell.get_child(0) as MeshInstance3D
	if mesh_instance == null:
		failures.append("%s: missing mesh" % label)
		return
	var box := mesh_instance.mesh as BoxMesh
	if box == null:
		failures.append("%s should use a box mesh" % label)
	elif absf(box.size.x - expected) > 0.001:
		failures.append("%s should be %.3f, got %.3f" % [label, expected, box.size.x])


func _assert_box_depth(failures: Array, cell: Node3D, expected: float, label: String) -> void:
	var mesh_instance := cell.get_child(0) as MeshInstance3D
	if mesh_instance == null:
		failures.append("%s: missing mesh" % label)
		return
	var box := mesh_instance.mesh as BoxMesh
	if box == null:
		failures.append("%s should use a box mesh" % label)
	elif absf(box.size.z - expected) > 0.001:
		failures.append("%s should be %.3f, got %.3f" % [label, expected, box.size.z])


func _assert_lit_material(failures: Array, cell: Node3D, label: String) -> void:
	var mesh_instance := cell.get_child(0) as MeshInstance3D
	if mesh_instance == null:
		failures.append("%s: missing mesh" % label)
		return
	var material := mesh_instance.material_override as StandardMaterial3D
	if material == null:
		failures.append("%s: missing StandardMaterial3D" % label)
	elif material.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED:
		failures.append("%s should use lit material shading for face-depth readability" % label)


func _assert_live_3d_exterior_block(failures: Array, cell: Node3D, label: String) -> void:
	if cell.get_child_count() < 18:
		failures.append("%s should include exterior face panels plus restrained outline edges" % label)
		return
	for index in range(6):
		var mesh_instance := cell.get_child(index) as MeshInstance3D
		if mesh_instance == null:
			failures.append("%s face %d should be a mesh" % [label, index])
			continue
		var material := mesh_instance.material_override as StandardMaterial3D
		if material == null:
			failures.append("%s face %d should have material" % [label, index])
		elif material.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or material.albedo_color.a < 0.99:
			failures.append("%s face %d should be opaque, not glass-like" % [label, index])


func _assert_rotation_pulse_outline(failures: Array, cell: Node3D, label: String) -> void:
	if cell.get_child_count() < 7:
		failures.append("%s should include outline edge meshes" % label)
		return
	var mesh_instance := cell.get_child(6) as MeshInstance3D
	if mesh_instance == null:
		failures.append("%s first outline edge should be a mesh" % label)
		return
	var box := mesh_instance.mesh as BoxMesh
	if box == null:
		failures.append("%s first outline edge should use box mesh" % label)
	elif minf(box.size.y, box.size.z) <= 0.016:
		failures.append("%s should thicken active outline briefly after rotation" % label)


func _assert_live_3d_active_priority(failures: Array, active_cell: Node3D, locked_cell: Node3D) -> void:
	var active_top := active_cell.get_child(0) as MeshInstance3D
	var locked_top := locked_cell.get_child(0) as MeshInstance3D
	if active_top == null or locked_top == null:
		failures.append("live 3D active priority test needs top face meshes")
		return
	var active_material := active_top.material_override as StandardMaterial3D
	var locked_material := locked_top.material_override as StandardMaterial3D
	if active_material == null or locked_material == null:
		failures.append("live 3D active priority test needs StandardMaterial3D faces")
		return
	if _color_brightness(active_material.albedo_color) <= _color_brightness(locked_material.albedo_color) + 0.18:
		failures.append("live 3D active face should be visibly brighter than locked face")
	var active_outline := active_cell.get_child(6) as MeshInstance3D
	var locked_outline := locked_cell.get_child(6) as MeshInstance3D
	if active_outline == null or locked_outline == null:
		failures.append("live 3D active priority test needs outline meshes")
		return
	var active_outline_material := active_outline.material_override as StandardMaterial3D
	var locked_outline_material := locked_outline.material_override as StandardMaterial3D
	if active_outline_material == null or locked_outline_material == null:
		failures.append("live 3D active priority test needs outline materials")
	elif active_outline_material.albedo_color == locked_outline_material.albedo_color:
		failures.append("live 3D active and locked outlines should not share the same visual role")


func _assert_live_3d_origin_marker(failures: Array, active_cell: Node3D) -> void:
	if active_cell.get_child_count() < 19:
		failures.append("live 3D active piece should include an origin/orientation marker")
		return
	var marker := active_cell.get_child(active_cell.get_child_count() - 1) as MeshInstance3D
	if marker == null:
		failures.append("live 3D active origin marker should be a mesh")
		return
	var material := marker.material_override as StandardMaterial3D
	if material == null:
		failures.append("live 3D active origin marker should have a material")
	elif material.albedo_color != ReplayVisuals.color_for_role(ReplayVisuals.ROLE_LIVE_3D_ORIGIN_MARKER):
		failures.append("live 3D active origin marker should use the origin marker role")


func _color_brightness(color: Color) -> float:
	return (color.r + color.g + color.b) / 3.0
