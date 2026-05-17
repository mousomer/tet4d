extends RefCounted

const TraceSceneRendererScript = preload("res://scripts/rendering/trace_scene_renderer.gd")


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

	renderer.queue_free()
	await tree.process_frame
	return failures


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
