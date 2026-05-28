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
			ReplayVisuals.live_locked_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 4).albedo_color,
			"live 3D locked cells use piece-aware secondary material"
		)
		_assert_cell_material(
			failures,
			live_3d_active_cell,
			ReplayVisuals.live_active_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 6).albedo_color,
			"live 3D active cells use bright piece-aware material"
		)
		_assert_box_size(failures, live_3d_active_cell, ReplayVisuals.LIVE_ACTIVE_CELL_SCALE, "live 3D active cell scale")
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
