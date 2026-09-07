extends RefCounted

const AdaptiveLayerLayoutScript = preload("res://scripts/presentation/adaptive_layer_layout.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")
const BoardPresentationModelScript = preload("res://scripts/presentation/board_presentation_model.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")


func run() -> Array:
	var failures := []
	_test_reference_viewport_policy(failures)
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
		if float(snapshot.get("horizontal_gap", 0.0)) < AdaptiveLayerLayoutScript.MIN_SLICE_GUTTER:
			failures.append("layout should reserve the minimum horizontal perceptual gutter")
		if float(snapshot.get("vertical_gap", 0.0)) < AdaptiveLayerLayoutScript.MIN_VERTICAL_SLICE_GUTTER:
			failures.append("layout should reserve the minimum vertical perceptual gutter")
		for first_index in range(count):
			for second_index in range(first_index + 1, count):
				if layout.tile_rect_for_layer(first_index).intersects(layout.tile_rect_for_layer(second_index)):
					failures.append("layout tiles %d and %d must not overlap" % [first_index, second_index])
		var repeated = AdaptiveLayerLayoutScript.new()
		repeated.configure(count, 8.0, 16.0)
		if repeated.snapshot() != snapshot:
			failures.append("layout output should be deterministic for the same presentation input")
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


func _test_reference_viewport_policy(failures: Array) -> void:
	var expected_columns := {5: 3, 6: 3, 7: 4, 8: 4}
	for count in expected_columns:
		var layout = AdaptiveLayerLayoutScript.new()
		layout.configure(count, 8.0, 16.0, 1600.0 / 960.0, 1.0, 5.0, 0.0, Vector2(1600.0, 960.0))
		var snapshot: Dictionary = layout.snapshot()
		if int(snapshot.get("columns", 0)) != int(expected_columns[count]) or int(snapshot.get("rows", 0)) != 2:
			failures.append("%d slices at 1600x960 must select %dx2, got %sx%s" % [count, expected_columns[count], snapshot.get("columns"), snapshot.get("rows")])
		if snapshot.get("viewport_size", Vector2.ZERO) != Vector2(1600.0, 960.0):
			failures.append("%d-slice evidence must retain the measured viewport" % count)
		if float(snapshot.get("projected_board_scale", 0.0)) <= 0.0 or float(snapshot.get("unused_viewport_area", -1.0)) < 0.0:
			failures.append("%d-slice evidence must report scale and unused area" % count)
		var content_rect: Rect2 = snapshot.get("content_rect", Rect2())
		var tile_rects: Array = snapshot.get("tile_rects", [])
		if tile_rects.size() != count:
			failures.append("%d-slice evidence must report every tile rectangle" % count)
		for index in range(tile_rects.size()):
			var tile_rect: Rect2 = tile_rects[index]
			if not _rect_contains(content_rect, tile_rect):
				failures.append("%d-slice tile %d must remain inside collection bounds" % [count, index])
			var assignment: Dictionary = snapshot.get("assignments", [])[index]
			if int(assignment.get("layer", -1)) != index or int(assignment.get("row", -1)) != index / int(expected_columns[count]) or int(assignment.get("column", -1)) != index % int(expected_columns[count]):
				failures.append("%d-slice assignment %d must remain monotonic row-major" % [count, index])
		if str(snapshot.get("partial_row_alignment", "")) != "left":
			failures.append("partial rows must retain the stable left-aligned column origin")
		var final_row_first := int(expected_columns[count])
		if count % int(expected_columns[count]) != 0 and int((snapshot.get("assignments", []) as Array)[final_row_first].get("column", -1)) != 0:
			failures.append("%d-slice partial final row must begin in column zero" % count)
		var fixed_four: Dictionary = layout.candidate_snapshot(4)
		var chosen_scale := float(snapshot.get("projected_board_scale", 0.0))
		if chosen_scale + AdaptiveLayerLayoutScript.SCALE_TIE_EPSILON < float(fixed_four.get("projected_board_scale", 0.0)):
			failures.append("%d-slice chosen grid must not reduce scale versus fixed four columns" % count)
		if count in [5, 6] and float(fixed_four.get("last_row_imbalance", 0.0)) <= float(layout.candidate_snapshot(int(expected_columns[count])).get("last_row_imbalance", 1.0)):
			failures.append("%d-slice 3-column choice must improve final-row balance versus fixed four" % count)

	var eight = AdaptiveLayerLayoutScript.new()
	eight.configure(8, 8.0, 16.0, 1600.0 / 960.0, 1.0, 5.0, 0.0, Vector2(1600.0, 960.0))
	var old_five_plus_three: Dictionary = eight.candidate_snapshot(5)
	var new_four_plus_four: Dictionary = eight.candidate_snapshot(4)
	if float(new_four_plus_four.get("last_row_imbalance", 1.0)) >= float(old_five_plus_three.get("last_row_imbalance", 0.0)):
		failures.append("8-slice 4+4 must improve balance over the old 5+3 grid")


func _rect_contains(outer: Rect2, inner: Rect2) -> bool:
	var epsilon := 0.0001
	return (
		inner.position.x >= outer.position.x - epsilon
		and inner.position.y >= outer.position.y - epsilon
		and inner.end.x <= outer.end.x + epsilon
		and inner.end.y <= outer.end.y + epsilon
	)


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
	if layout.horizontal_gap <= AdaptiveLayerLayoutScript.MIN_SLICE_GUTTER:
		failures.append("larger slices should receive responsive spacing above the minimum")
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
		layer_differences.append(mapper.unoriented_world_position(destination, 4) - mapper.unoriented_world_position(origin, 4))
	if layer_differences != [Vector3(1.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0)]:
		failures.append("anchor vectors must cancel from local gameplay point differences")
