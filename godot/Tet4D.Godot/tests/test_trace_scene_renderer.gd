extends RefCounted

const TraceSceneRendererScript = preload("res://scripts/rendering/trace_scene_renderer.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["trace scene renderer test requires SceneTree"]
	var renderer := TraceSceneRendererScript.new()
	tree.root.add_child(renderer)
	await tree.process_frame
	renderer.set_display_mode(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)

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
				_assert_color(failures, material.albedo_color, ReplayVisuals.color_for_role(ReplayVisuals.ROLE_ACTIVE_CELL, ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC), "gameplay active cells use role color")
			var box := mesh_instance.mesh as BoxMesh
			if box == null:
				failures.append("gameplay active cell should use a box mesh")
			elif absf(box.size.x - ReplayVisuals.ACTIVE_GAMEPLAY_CELL_SCALE) > 0.001:
				failures.append("gameplay active cell scale should keep adjacent cells separated")

	var live_2d_snapshot := {
		"case_id": "live_plain_2d",
		"trace_type": "live_2d",
		"frame_index": 0,
		"dimension": 2,
		"board_shape": [4, 4],
		"locked_cells": [{"position": [1, 3], "color_id": 4}],
		"ghost_cells": [{"position": [1, 2], "color_id": 2}],
		"active_cells": [{"position": [1, 1], "color_id": 2}],
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
	}
	renderer.render_snapshot(live_2d_snapshot)
	await tree.process_frame
	cell_root = renderer.get_node_or_null("CellRoot")
	if cell_root == null or cell_root.get_child_count() != 3:
		failures.append("live renderer should create locked, ghost, and active cells")
	else:
		var locked_cell := cell_root.get_child(0) as Node3D
		var ghost_cell := cell_root.get_child(1) as Node3D
		var active_cell := cell_root.get_child(2) as Node3D
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
		_assert_box_size(failures, ghost_cell, ReplayVisuals.LIVE_GHOST_CELL_SCALE, "live ghost cell scale")
		if active_cell.get_child_count() < 2:
			failures.append("live active cell should include a crisp border mesh")
		if locked_cell.get_child_count() < 2:
			failures.append("live locked cell should include a crisp border mesh")
		if ghost_cell.get_child_count() < 2 or not bool(ghost_cell.get_meta("presentation_role", "") == "ghost"):
			failures.append("live ghost cell should retain a dedicated outlined presentation role")
		elif _cell_alpha(ghost_cell) < 0.45 or _cell_alpha(ghost_cell) >= _cell_alpha(active_cell):
			failures.append("ghost fill should be clearly visible while remaining weaker than active cells")
		renderer.set_locked_cell_opacity(0.60)
		renderer.render_snapshot(live_2d_snapshot)
		await tree.process_frame
		var translucent_locked := (renderer.get_node_or_null("CellRoot") as Node).get_child(0) as Node3D
		var unchanged_active := (renderer.get_node_or_null("CellRoot") as Node).get_child(2) as Node3D
		if absf(_cell_alpha(translucent_locked) - 0.60) > 0.001 or absf(_cell_alpha(unchanged_active) - 1.0) > 0.001:
			failures.append("locked-cell opacity must restyle only locked fill without weakening active cells")
		renderer.set_locked_cell_opacity(ReplayVisuals.DEFAULT_LOCKED_CELL_OPACITY)
	var grid_root := renderer.get_node_or_null("GridRoot")
	if grid_root == null or grid_root.get_child_count() != 1:
		failures.append("live renderer should keep one shared grid renderer")
	else:
		var live_grid := grid_root.get_child(0)
		if _count_presentation_role(live_grid, "board.wireframe") != 12:
			failures.append("live 2D renderer should build an explicit 12-edge ordinary wireframe")
		if _count_presentation_role(live_grid, "board.grid") != 6:
			failures.append("live 2D internal grid should exclude its six coincident outer-boundary lines")
		renderer.set_grid_visible(false)
		renderer.render_snapshot(renderer._presentation.snapshot)
		await tree.process_frame
		var hidden_grid := (renderer.get_node_or_null("GridRoot") as Node).get_child(0)
		if _count_presentation_role(hidden_grid, "board.wireframe") != 12 or _count_presentation_role(hidden_grid, "board.grid") != 0:
			failures.append("grid toggle should hide internal detail while retaining the 12-edge orientation cage")
		renderer.set_grid_visible(true)

	var live_3d_snapshot := {
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
	}
	renderer.render_snapshot(live_3d_snapshot)
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
	else:
		var live_3d_grid := grid_root.get_child(0)
		if _count_presentation_role(live_3d_grid, "board.wireframe") != 12:
			failures.append("live 3D renderer should retain an explicit ordinary wireframe")
		_assert_internal_face_grid_counts(failures, live_3d_grid, [4, 5, 4])

	var live_4d_snapshot := {
		"case_id": "live_plain_4d",
		"trace_type": "live_4d",
		"frame_index": 0,
		"dimension": 4,
		"board_shape": [5, 10, 3, 4],
		"locked_cells": [{"position": [1, 4, 1, 0], "color_id": 4}],
		"ghost_cells": [{"position": [2, 1, 2, 1], "color_id": 6}],
		"active_cells": [{"position": [1, 1, 2, 1], "color_id": 6}],
		"last_command": "rotate_xw_pos",
		"last_command_status": "accepted",
		"w_slice_count": 4,
		"active_w": 1,
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
	}
	renderer.render_snapshot(live_4d_snapshot)
	await tree.process_frame
	cell_root = renderer.get_node_or_null("CellRoot")
	if cell_root == null or cell_root.get_child_count() != 3:
		failures.append("live 4D renderer should create active, Ghost, and locked cells through the shared renderer")
	else:
		var live_4d_locked_cell := cell_root.get_child(0) as Node3D
		var live_4d_ghost_cell := cell_root.get_child(1) as Node3D
		var live_4d_active_cell := cell_root.get_child(2) as Node3D
		_assert_cell_material(
			failures,
			live_4d_locked_cell,
			ReplayVisuals.live_3d_locked_face_materials(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 4).get("top").albedo_color,
			"live 4D locked cells reuse piece-aware exterior face material"
		)
		_assert_cell_material(
			failures,
			live_4d_active_cell,
			ReplayVisuals.live_4d_active_face_materials(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 6).get("top").albedo_color,
			"live 4D active cells use restrained exterior face material"
		)
		_assert_live_3d_exterior_block(failures, live_4d_active_cell, "live 4D active cell")
		_assert_live_3d_exterior_block(failures, live_4d_locked_cell, "live 4D locked cell")
		_assert_box_size(failures, live_4d_ghost_cell, ReplayVisuals.LIVE_3D_GHOST_CELL_SCALE, "live 4D Ghost cell scale")
		_assert_rotation_pulse_outline(failures, live_4d_active_cell, "live 4D active rotation pulse")
		_assert_live_3d_origin_marker(failures, live_4d_active_cell)
		_assert_live_4d_active_restrained(failures, live_4d_active_cell, live_4d_locked_cell)
		if live_4d_active_cell.position.x <= live_4d_locked_cell.position.x:
			failures.append("live 4D renderer should position higher W slices to the right")
	grid_root = renderer.get_node_or_null("GridRoot")
	if grid_root == null or grid_root.get_child_count() != 1:
		failures.append("live 4D renderer should keep one shared grid renderer")
	else:
		var live_4d_grid := grid_root.get_child(0)
		if _count_presentation_role(live_4d_grid, "board.wireframe") != 48:
			failures.append("live 4D renderer should build one explicit ordinary wireframe per board")
		if _count_presentation_role(live_4d_grid, "board.frame_active") != 12:
			failures.append("live 4D renderer should keep one separately governed active frame")
		var stable_structural_count := _count_presentation_role(live_4d_grid, "board.wireframe") + _count_presentation_role(live_4d_grid, "board.grid") + _count_presentation_role(live_4d_grid, "board.grid.floor") + _count_presentation_role(live_4d_grid, "board.frame_active")
		live_4d_grid._process(0.016)
		var processed_structural_count := _count_presentation_role(live_4d_grid, "board.wireframe") + _count_presentation_role(live_4d_grid, "board.grid") + _count_presentation_role(live_4d_grid, "board.grid.floor") + _count_presentation_role(live_4d_grid, "board.frame_active")
		if processed_structural_count != stable_structural_count:
			failures.append("stable board processing must not rebuild or accumulate structural geometry")
		var floor_count := _count_meta_value(live_4d_grid, "boundary_role", "gravity_floor")
		if floor_count != 4:
			failures.append("live 4D should distinguish the bottom boundary on every W section")
		live_4d_grid._update_rear_grid_faces(Vector3(100.0, 100.0, 100.0))
		_assert_three_rear_grid_faces_per_slice(failures, live_4d_grid, 4, -1.0, "positive camera octant")
		live_4d_grid._update_rear_grid_faces(Vector3(-100.0, -100.0, -100.0))
		live_4d_grid._update_slice_labels(Vector3(-100.0, -100.0, -100.0))
		_assert_three_rear_grid_faces_per_slice(failures, live_4d_grid, 4, 1.0, "negative camera octant")
		var slice_label_count := 0
		for child in live_4d_grid.get_children():
			if child is Label3D and child.has_meta("slice_axis"):
				slice_label_count += 1
				var label := child as Label3D
				if label.text.find("ACTIVE") != -1:
					failures.append("slice labels should contain only signed semantic identity")
				var selected := bool(label.get_meta("selected_slice", false))
				var expected_font_size := ReplayVisuals.W_SLICE_LABEL_SELECTED_FONT_SIZE if selected else ReplayVisuals.W_SLICE_LABEL_FONT_SIZE
				if label.font_size != expected_font_size or absf(label.pixel_size - ReplayVisuals.W_SLICE_LABEL_PIXEL_SIZE) > 0.0001:
					failures.append("live 4D W labels should remain readable at fitted overview scale")
				var rear_axis := int(label.get_meta("rear_face_axis", -1))
				var rear_sign := float(label.get_meta("rear_face_sign", 0.0))
				var label_min: Vector3 = label.get_meta("slice_bounds_min", Vector3.ZERO)
				var label_max: Vector3 = label.get_meta("slice_bounds_max", Vector3.ZERO)
				if rear_axis not in [Vector3.AXIS_X, Vector3.AXIS_Z]:
					failures.append("W labels should attach to a camera-relative rear vertical face")
				else:
					var expected_face := label_min[rear_axis] if rear_sign < 0.0 else label_max[rear_axis]
					if absf(label.position[rear_axis] - expected_face) > 0.05:
						failures.append("W labels should attach to a camera-relative rear vertical face")
		if slice_label_count < 4:
			failures.append("live 4D renderer should label each basis-derived slice")

	# Requirement/invariant/regression coverage: cells, Ghost, grids, frames,
	# labels, anchors, and bounds consume one shared L exactly once.
	var anchors_before_orientation := []
	for layer_index in range(4):
		anchors_before_orientation.append(renderer._presentation.projection.slice_anchor(layer_index))
	var canonical_snapshot_before_orientation: Dictionary = live_4d_snapshot.duplicate(true)
	var oriented_identity_bounds: Dictionary = renderer.current_bounds().duplicate(true)
	var quarter_orientation = SliceLocalOrientationScript.new(PI * 0.5, 0.0)
	renderer.set_live_4d_local_orientation(quarter_orientation)
	renderer.render_snapshot(live_4d_snapshot)
	await tree.process_frame
	cell_root = renderer.get_node_or_null("CellRoot")
	if cell_root != null and cell_root.get_child_count() == 3:
		var quarter_ghost := cell_root.get_child(1) as Node3D
		var quarter_active := cell_root.get_child(2) as Node3D
		_assert_vector(failures, quarter_ghost.position - quarter_active.position, Vector3(0.0, 0.0, -1.0), "renderer consumes continuous L at pi/2")

	var shared_orientation = SliceLocalOrientationScript.new(PI / 6.0, PI / 8.0)
	renderer.set_live_4d_local_orientation(shared_orientation)
	renderer.render_snapshot(live_4d_snapshot)
	await tree.process_frame
	if renderer._presentation.projection.local_orientation != shared_orientation:
		failures.append("app/renderer/projection must share one SliceLocalOrientation object")
	if live_4d_snapshot != canonical_snapshot_before_orientation:
		failures.append("renderer orientation must not mutate canonical snapshot identity")
	cell_root = renderer.get_node_or_null("CellRoot")
	if cell_root == null or cell_root.get_child_count() != 3:
		failures.append("oriented Live-4D renderer must retain locked, Ghost, and active cells")
	else:
		var oriented_locked := cell_root.get_child(0) as Node3D
		var oriented_ghost := cell_root.get_child(1) as Node3D
		var oriented_active := cell_root.get_child(2) as Node3D
		var expected_render_basis: Basis = shared_orientation.passive_render_basis()
		_assert_basis(failures, oriented_locked.basis, expected_render_basis, "locked cell uses shared L")
		_assert_basis(failures, oriented_ghost.basis, expected_render_basis, "Ghost cell uses shared L")
		_assert_basis(failures, oriented_active.basis, expected_render_basis, "active cell uses shared L")
		_assert_vector(
			failures,
			oriented_ghost.position - oriented_active.position,
			expected_render_basis * Vector3.RIGHT,
			"Ghost and active cell canonical delta shares B plus L plus anchor"
		)
		if renderer._presentation.ghost_cells()[0].get("position", []) != live_4d_snapshot["ghost_cells"][0]["position"]:
			failures.append("presentation orientation must not change authoritative Ghost destination")
	var oriented_grid := (renderer.get_node_or_null("GridRoot") as Node).get_child(0) as Node3D
	var slice_roots := _nodes_with_meta(oriented_grid, "slice_anchor")
	if slice_roots.size() != 4:
		failures.append("oriented grid must keep one geometry root per slice")
	else:
		for layer_index in range(4):
			var slice_root := slice_roots[layer_index] as Node3D
			_assert_vector(failures, slice_root.position, anchors_before_orientation[layer_index], "L leaves anchor_%d unchanged" % layer_index)
			_assert_basis(failures, slice_root.basis, shared_orientation.passive_render_basis(), "grid/frame slice %d uses shared L once" % layer_index)
			_assert_vector(failures, slice_root.basis * Vector3.RIGHT, shared_orientation.passive_render_basis() * Vector3.RIGHT, "grid/frame local X follows L in slice %d" % layer_index)
	var oriented_bounds: Dictionary = renderer.current_bounds()
	var identity_size: Vector3 = oriented_identity_bounds.get("max", Vector3.ZERO) - oriented_identity_bounds.get("min", Vector3.ZERO)
	var oriented_size: Vector3 = oriented_bounds.get("max", Vector3.ZERO) - oriented_bounds.get("min", Vector3.ZERO)
	if identity_size.distance_to(oriented_size) <= 0.001:
		failures.append("non-quarter yaw/pitch must change renderer camera-fit bounds")
	for layer_index in range(4):
		if renderer._presentation.projection.slice_anchor(layer_index) != anchors_before_orientation[layer_index]:
			failures.append("shared L must not move renderer anchor_%d" % layer_index)
	var oriented_labels := 0
	for child in oriented_grid.get_children():
		if child is Label3D and child.has_meta("presentation_layer"):
			oriented_labels += 1
			if (child as Label3D).billboard != BaseMaterial3D.BILLBOARD_ENABLED:
				failures.append("slice identity labels must remain billboarded outside local physical rotation")
	if oriented_labels != 4:
		failures.append("orientation must preserve one semantic identity label per slice")

	renderer.set_live_4d_local_orientation(SliceLocalOrientationScript.new())
	renderer.render_snapshot(live_4d_snapshot)
	await tree.process_frame

	var xw_basis = SliceBasis4DScript.identity().turned("xw", 1)
	renderer.set_live_4d_basis(xw_basis, false)
	renderer.render_snapshot(live_4d_snapshot)
	await tree.process_frame
	grid_root = renderer.get_node_or_null("GridRoot")
	if grid_root == null or grid_root.get_child_count() != 1:
		failures.append("basis rebuild should remove the prior slice stack")
	else:
		var xw_grid := grid_root.get_child(0)
		var xw_labels := 0
		for child in xw_grid.get_children():
			if child is Label3D and child.has_meta("slice_axis"):
				xw_labels += 1
				if str(child.get_meta("slice_axis")) != "-X":
					failures.append("XW+ labels must expose the signed -X slice axis")
		if xw_labels != 5:
			failures.append("XW+ should rebuild five X slices for dimensions 5x10x4x4")
	if renderer._presentation.projection.mapper.visible_board_shape() != [4, 10, 3]:
		failures.append("XW+ should render W,Y,Z as visible board dimensions")
	var zw_basis = SliceBasis4DScript.identity().turned("zw", 1)
	var stable_grid_during_transition = grid_root.get_child(0) if grid_root != null and grid_root.get_child_count() == 1 else null
	renderer.set_live_4d_basis(zw_basis, true)
	renderer._process(0.08)
	if stable_grid_during_transition != null and grid_root.get_child(0) != stable_grid_during_transition:
		failures.append("basis settle frames must not rebuild stable layer geometry")
	renderer.render_snapshot(live_4d_snapshot)
	await tree.process_frame
	grid_root = renderer.get_node_or_null("GridRoot")
	if grid_root == null or grid_root.get_child_count() != 1:
		failures.append("smaller Z slice rebuild must remove stale X panels")
	elif renderer._presentation.projection.mapper.current_layer_count() != 3:
		failures.append("ZW+ should derive layer count from Z extent")
	if renderer._presentation.projection.mapper.visible_board_shape() != [5, 10, 4]:
		failures.append("ZW+ should render X,Y,W as visible board dimensions")
	var zx_basis = SliceBasis4DScript.identity().turned("zx", 1)
	renderer.set_live_4d_basis(zx_basis, false)
	renderer.render_snapshot(live_4d_snapshot)
	await tree.process_frame
	if renderer._presentation.projection.mapper.current_layer_count() != 4 or renderer._presentation.projection.mapper.visible_board_shape() != [3, 10, 5]:
		failures.append("ZX+ should rotate visible X/Z dimensions while preserving the W slice count")

	renderer.queue_free()
	await tree.process_frame
	return failures


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_basis(failures: Array, actual: Basis, expected: Basis, label: String) -> void:
	_assert_vector(failures, actual.x, expected.x, "%s X" % label)
	_assert_vector(failures, actual.y, expected.y, "%s Y" % label)
	_assert_vector(failures, actual.z, expected.z, "%s Z" % label)


func _assert_color(failures: Array, actual: Color, expected: Color, label: String) -> void:
	var tolerance := 0.01
	if (
		absf(actual.r - expected.r) > tolerance
		or absf(actual.g - expected.g) > tolerance
		or absf(actual.b - expected.b) > tolerance
		or absf(actual.a - expected.a) > tolerance
	):
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _cell_alpha(cell: Node3D) -> float:
	var mesh_instance := cell.get_child(0) as MeshInstance3D
	var material := mesh_instance.material_override as StandardMaterial3D if mesh_instance != null else null
	return material.albedo_color.a if material != null else 0.0


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
		elif label.contains("locked"):
			if material.transparency != BaseMaterial3D.TRANSPARENCY_ALPHA or absf(material.albedo_color.a - ReplayVisuals.DEFAULT_LOCKED_CELL_OPACITY) > 0.001:
				failures.append("%s face %d should use the configured translucent locked fill" % [label, index])
		elif material.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or material.albedo_color.a < 0.99:
			failures.append("%s face %d should be opaque" % [label, index])
	if label.contains("locked"):
		var outline := cell.get_child(6) as MeshInstance3D
		var outline_material := outline.material_override as StandardMaterial3D if outline != null else null
		if outline_material == null or outline_material.albedo_color.a < 0.99:
			failures.append("%s should retain an opaque outline over translucent faces" % label)


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


func _count_presentation_role(node: Node, role: String) -> int:
	var count := 1 if str(node.get_meta("presentation_role", "")) == role else 0
	for child in node.get_children():
		count += _count_presentation_role(child, role)
	return count


func _assert_internal_face_grid_counts(failures: Array, grid: Node3D, board_shape: Array) -> void:
	var face_count := 0
	for child in _nodes_with_meta(grid, "grid_axis"):
		face_count += 1
		var axis := int(child.get_meta("grid_axis", -1))
		var expected := 0
		for dimension_index in range(3):
			if dimension_index != axis:
				expected += maxi(0, int(board_shape[dimension_index]) - 1)
		if child.get_child_count() != expected:
			failures.append("rear grid faces must contain interior subdivisions only; axis %d expected %d, got %d" % [axis, expected, child.get_child_count()])
		if str(child.get_meta("presentation_role", "")) != "board.grid":
			failures.append("rear grid faces must consume the board.grid presentation role")
	if face_count != 6:
		failures.append("live 3D renderer should retain six cached rear-grid face candidates")


func _assert_three_rear_grid_faces_per_slice(
	failures: Array,
	grid: Node3D,
	slice_count: int,
	expected_sign: float,
	label: String
) -> void:
	var visible_faces := 0
	for child in _nodes_with_meta(grid, "grid_axis"):
		if not (child as Node3D).visible:
			continue
		visible_faces += 1
		if float(child.get_meta("grid_sign", 0.0)) != expected_sign:
			failures.append("%s should show only camera-relative rear grid faces" % label)
		if child.get_child_count() == 0:
			failures.append("%s rear grid face should contain boundary rectangles" % label)
	if visible_faces != slice_count * 3:
		failures.append("%s should show exactly three rear grid faces per section, got %d" % [label, visible_faces])


func _nodes_with_meta(root: Node, meta_name: String) -> Array:
	var result := []
	for child in root.get_children():
		if child.has_meta(meta_name):
			result.append(child)
		result.append_array(_nodes_with_meta(child, meta_name))
	return result


func _count_meta_value(root: Node, meta_name: String, expected_value: String) -> int:
	var count := 1 if root.has_meta(meta_name) and str(root.get_meta(meta_name)) == expected_value else 0
	for child in root.get_children():
		count += _count_meta_value(child, meta_name, expected_value)
	return count


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
	_assert_matching_cell_envelope(failures, active_cell, locked_cell)


func _assert_matching_cell_envelope(failures: Array, active_cell: Node3D, locked_cell: Node3D) -> void:
	var active_face := (active_cell.get_child(0) as MeshInstance3D).mesh as BoxMesh
	var locked_face := (locked_cell.get_child(0) as MeshInstance3D).mesh as BoxMesh
	var active_outline := (active_cell.get_child(6) as MeshInstance3D).mesh as BoxMesh
	var locked_outline := (locked_cell.get_child(6) as MeshInstance3D).mesh as BoxMesh
	if active_face == null or locked_face == null or active_outline == null or locked_outline == null:
		failures.append("live exterior cells need comparable face and outline meshes")
		return
	if absf(active_face.size.x - locked_face.size.x) > 0.001:
		failures.append("locked exterior cells should retain the active cell body scale")
	if absf(active_outline.size.x - locked_outline.size.x) > 0.001:
		failures.append("locked exterior cells should retain the active wireframe envelope")
	if active_outline.size.x - active_face.size.x > 0.051:
		failures.append("exterior cell bodies should nearly fill their wireframe envelope")


func _assert_live_4d_active_restrained(failures: Array, active_cell: Node3D, locked_cell: Node3D) -> void:
	var active_top := active_cell.get_child(0) as MeshInstance3D
	var locked_top := locked_cell.get_child(0) as MeshInstance3D
	if active_top == null or locked_top == null:
		failures.append("live 4D active restraint test needs top face meshes")
		return
	var active_material := active_top.material_override as StandardMaterial3D
	var locked_material := locked_top.material_override as StandardMaterial3D
	if active_material == null or locked_material == null:
		failures.append("live 4D active restraint test needs StandardMaterial3D faces")
		return
	if active_material.emission_energy_multiplier > 0.34:
		failures.append("live 4D active emission should stay below glare threshold")
	if _color_brightness(active_material.albedo_color) <= _color_brightness(locked_material.albedo_color) + 0.08:
		failures.append("live 4D active face should remain brighter than locked face")
	if _color_brightness(active_material.albedo_color) >= 0.82:
		failures.append("live 4D active face should not wash out toward white")


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
	elif material.albedo_color != ReplayVisuals.color_for_role(ReplayVisuals.ROLE_LIVE_3D_ORIGIN_MARKER, ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC):
		failures.append("live 3D active origin marker should use the origin marker role")


func _color_brightness(color: Color) -> float:
	return (color.r + color.g + color.b) / 3.0
