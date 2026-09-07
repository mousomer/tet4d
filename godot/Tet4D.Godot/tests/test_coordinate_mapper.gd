extends RefCounted

const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")
const BoardPresentationModelScript = preload("res://scripts/presentation/board_presentation_model.gd")
const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")


func run() -> Array:
	var failures: Array = []
	var mapper := TraceCoordinateMapperScript.new()
	mapper.configure([4, 5, 3, 2])
	_assert_vector(
		failures,
		mapper.unoriented_world_position([1, 2, 1, 1], 4),
		mapper.slice_anchor(1) + Vector3(-0.5, 0.0, 0.0),
		"4D centered coordinate mapping"
	)
	_assert_vector(
		failures,
		mapper.unoriented_world_position([0, 0, 0], 3),
		Vector3(-1.5, 2.0, -1.0),
		"3D cell center follows Python raw_to_world"
	)
	var bounds: Dictionary = mapper.board_bounds([4, 5, 3, 2], 4)
	if not bounds.get("ok", false):
		failures.append("bounds should be available")
		return failures
	var second_anchor := mapper.slice_anchor(1)
	_assert_vector(
		failures,
		bounds.get("min", Vector3.ZERO),
		Vector3(-4.1, minf(-4.25, second_anchor.y - 4.25), -3.6),
		"bounds min includes compensated outside-edge W label clearance"
	)
	_assert_vector(
		failures,
		bounds.get("max", Vector3.ZERO),
		Vector3(second_anchor.x + 4.1, maxf(3.5, second_anchor.y + 3.5), 3.6),
		"bounds max includes compensated active-spawn clearance"
	)
	_assert_vector(failures, mapper.slice_label_position(1), second_anchor + Vector3(-3.15, -3.7, -2.65), "W label position")
	_test_decomposed_asymmetric_mapping(failures)
	_test_layout_anchor_oracle(failures)
	_test_live_4d_row_correction_is_mode_scoped(failures)
	return failures


func _test_decomposed_asymmetric_mapping(failures: Array) -> void:
	var mapper := TraceCoordinateMapperScript.new()
	mapper.configure([5, 7, 3, 2])
	var decomposition: Dictionary = mapper.decompose_position([1, 2, 2, 1], 4)
	if not bool(decomposition.get("ok", false)):
		failures.append("asymmetric 4D point should decompose")
		return
	if int(decomposition.get("layer_index", -1)) != 1 or decomposition.get("visible_cell_3d", []) != [1, 2, 2]:
		failures.append("identity B must remain separately queryable in decomposition")
	_assert_vector(failures, decomposition.get("centered_local_point", Vector3.ZERO), Vector3(-1.0, 1.0, 1.0), "asymmetric G_D centred point")
	var expected_anchor := mapper.slice_anchor(1)
	_assert_vector(failures, decomposition.get("anchor", Vector3.ZERO), expected_anchor, "asymmetric anchor_1")
	_assert_vector(failures, decomposition.get("unoriented_world_point", Vector3.ZERO), expected_anchor + Vector3(-1.0, 1.0, 1.0), "compatibility composition is G_D plus anchor")
	_assert_vector(failures, mapper.unoriented_world_position([1, 2, 2, 1], 4), decomposition.get("unoriented_world_point", Vector3.ZERO), "explicit unoriented path uses decomposed compatibility composition")
	var mapped_origin: Dictionary = mapper.presentation_coordinate([2, 3, 1, 0])
	var mapped_destination: Dictionary = mapper.presentation_coordinate([3, 3, 1, 0])
	var point_difference: Vector3 = mapper.centered_local_point(mapped_destination["visible_cell_3d"]) - mapper.centered_local_point(mapped_origin["visible_cell_3d"])
	_assert_vector(failures, point_difference, Vector3(1.0, 0.0, 0.0), "G_D point difference cancels centring")


# This oracle repeats only the documented affine layout arithmetic. It does
# not call mapper layout/decomposition helpers, so a shared implementation bug
# cannot certify its own camera-compensated anchor result.
func _test_layout_anchor_oracle(failures: Array) -> void:
	var mapper := TraceCoordinateMapperScript.new()
	# The Live-4D row correction is supplied by the presentation owner, so this
	# oracle opts in explicitly rather than relying on board dimensionality.
	mapper.configure([5, 7, 3, 4], null, 1.0, _live_4d_screen_row_slope())
	var layout = mapper.layer_layout
	var expected_x: float = float(layout.tile_width) + float(layout.horizontal_gap)
	var expected_y: float = expected_x * _live_4d_screen_row_slope()
	_assert_vector(
		failures,
		mapper.slice_anchor(1),
		Vector3(expected_x, expected_y, 0.0),
		"independent Live-4D compensated second-column anchor"
	)


func _live_4d_screen_row_slope() -> float:
	var yaw := 3.5779249665883754
	var pitch := 0.3490658503988659
	var camera_up_x := -sin(yaw) * sin(pitch)
	var camera_up_y := cos(pitch)
	return -camera_up_x / maxf(camera_up_y, 0.001)


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


# The fixed-mount row correction belongs to Live 4D alone. A 4D replay shares
# the dimensionality but not the camera contract, so it must stay uncorrected.
func _test_live_4d_row_correction_is_mode_scoped(failures: Array) -> void:
	var board_shape := [5, 7, 3, 4]
	var expected_slope := CameraRigScript.live_4d_screen_row_y_per_world_x()
	if absf(expected_slope) < 0.001:
		failures.append("Live-4D row slope fixture must be non-zero to be discriminating")
		return

	var live := BoardPresentationModelScript.new()
	live.configure({"trace_type": "live_4d", "dimension": 4, "board_shape": board_shape})
	if not live.is_live_4d:
		failures.append("live_4d fixture must be recognised as Live 4D")
		return
	var live_anchor: Vector3 = live.projection.mapper.slice_anchor(1)
	var live_expected_y: float = live_anchor.x * expected_slope
	if absf(live_anchor.y - live_expected_y) > 0.001:
		failures.append(
			"Live 4D must receive the fitted-mount row correction: expected y %s, got %s"
			% [live_expected_y, live_anchor.y]
		)

	var replay := BoardPresentationModelScript.new()
	replay.configure({"trace_type": "replay", "dimension": 4, "board_shape": board_shape})
	if replay.is_live_4d:
		failures.append("replay fixture must not be recognised as Live 4D")
		return
	var replay_anchor: Vector3 = replay.projection.mapper.slice_anchor(1)
	if absf(replay_anchor.y) > 0.001:
		failures.append(
			"4D replay must not inherit the Live-4D fixed-mount correction: got y %s"
			% replay_anchor.y
		)
	if absf(replay_anchor.x - live_anchor.x) > 0.001:
		failures.append("only the row correction may differ between Live 4D and replay")

	# 2D/3D never had a slice grid to correct; they must stay untouched.
	for lower_case in [
		{"trace_type": "live_3d", "dimension": 3, "board_shape": [5, 7, 3]},
		{"trace_type": "replay", "dimension": 2, "board_shape": [10, 20]},
	]:
		var model := BoardPresentationModelScript.new()
		model.configure(lower_case)
		var anchor: Vector3 = model.projection.mapper.slice_anchor(0)
		if absf(anchor.y) > 0.001:
			failures.append(
				"%s anchors must remain uncorrected: got y %s"
				% [str(lower_case["trace_type"]), anchor.y]
			)
