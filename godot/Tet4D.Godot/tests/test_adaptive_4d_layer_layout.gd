extends RefCounted

const AdaptiveLayerLayoutScript = preload("res://scripts/presentation/adaptive_layer_layout.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")
const BoardPresentationModelScript = preload("res://scripts/presentation/board_presentation_model.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")


func run() -> Array:
	var failures := []
	for count in [3, 4, 8, 12]:
		var layout = AdaptiveLayerLayoutScript.new()
		layout.configure(count, 8.0, 16.0)
		var snapshot: Dictionary = layout.snapshot()
		var assignments: Array = snapshot.get("assignments", [])
		if assignments.size() != count:
			failures.append("layout should represent all %d layers" % count)
		var seen := {}
		for assignment in assignments:
			seen[int(assignment.get("layer", -1))] = true
		if seen.size() != count:
			failures.append("layout should assign %d unique stable layers" % count)
		if int(snapshot.get("rows", 0)) * int(snapshot.get("columns", 0)) < count:
			failures.append("layout capacity should cover %d layers" % count)
	var mapper = TraceCoordinateMapperScript.new()
	var bounds: Dictionary = mapper.board_bounds([8, 16, 5, 8], 4)
	if not bounds.get("ok", false) or mapper.layer_layout.rows <= 1:
		failures.append("W=8 mapper should produce a bounded multi-row matrix")
	if mapper.slice_offset(7) == Vector3(7.0 * mapper.slice_stride, 0.0, 0.0):
		failures.append("W=8 should not remain a fixed horizontal strip")
	var presentation = BoardPresentationModelScript.new()
	presentation.configure({"trace_type": "live_4d", "dimension": 4, "board_shape": [8, 16, 5, 8], "active_cells": [{"position": [1, 1, 1, 2]}, {"position": [1, 1, 1, 3]}]})
	if presentation.active_layer_indices() != [2, 3]:
		failures.append("all active-piece layers should be highlighted")
	var asymmetric := TraceCoordinateMapperScript.new()
	asymmetric.configure([5, 4, 3, 2], SliceBasis4DScript.identity().turned("xw", 1))
	if asymmetric.current_layer_count() != 5 or asymmetric.visible_board_shape() != [2, 4, 3]:
		failures.append("XW basis layout must derive count and visible dimensions from asymmetric extents")
	var thin_w := TraceCoordinateMapperScript.new()
	thin_w.configure([4, 6, 2, 1], SliceBasis4DScript.identity().turned("zw", -1))
	if thin_w.current_layer_count() != 2 or thin_w.visible_board_shape() != [4, 6, 1]:
		failures.append("W=1 must remain a valid visible dimension after ZW re-slicing")
	_test_anchor_only_layout(failures)
	return failures


func _test_anchor_only_layout(failures: Array) -> void:
	var basis = SliceBasis4DScript.from_slots([-3, 2, 1, 4])
	var basis_before: Array = basis.slots()
	var orientation = SliceLocalOrientationScript.new(PI * 0.5, 0.0)
	var local_axes_before: Array = [
		orientation.passive_yaw_basis() * Vector3(1.0, 0.0, 0.0),
		orientation.passive_yaw_basis() * Vector3(0.0, 1.0, 0.0),
		orientation.passive_yaw_basis() * Vector3(0.0, 0.0, 1.0),
	]
	var layout = AdaptiveLayerLayoutScript.new()
	layout.configure(2, 5.0, 7.0)
	var first_anchor_before: Vector3 = layout.anchor_for_layer(1)
	if layout.offset_for_layer(1) != first_anchor_before:
		failures.append("legacy layout offset must be an alias of anchor lookup")
	layout.configure(2, 9.0, 7.0)
	var first_anchor_after: Vector3 = layout.anchor_for_layer(1)
	if first_anchor_after == first_anchor_before:
		failures.append("layout configuration must be able to change anchors")
	var local_axes_after: Array = [
		orientation.passive_yaw_basis() * Vector3(1.0, 0.0, 0.0),
		orientation.passive_yaw_basis() * Vector3(0.0, 1.0, 0.0),
		orientation.passive_yaw_basis() * Vector3(0.0, 0.0, 1.0),
	]
	if local_axes_after != local_axes_before:
		failures.append("layout changes must not rotate or scale local basis vectors")
	if basis.slots() != basis_before:
		failures.append("layout changes must not alter exact B")
	var anchors_before_orientation_change: Array = [layout.anchor_for_layer(0), layout.anchor_for_layer(1)]
	orientation.set_angles(-PI * 0.5, PI / 8.0)
	if [layout.anchor_for_layer(0), layout.anchor_for_layer(1)] != anchors_before_orientation_change:
		failures.append("local orientation state must not move anchors")

	var mapper = TraceCoordinateMapperScript.new()
	mapper.configure([5, 7, 3, 2])
	var layer_differences := []
	for layer_index in [0, 1]:
		var origin := [2, 3, 1, layer_index]
		var destination := [3, 3, 1, layer_index]
		layer_differences.append(mapper.world_position(destination, 4) - mapper.world_position(origin, 4))
	if layer_differences != [Vector3(1.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0)]:
		failures.append("anchor vectors must cancel from local gameplay point differences")
