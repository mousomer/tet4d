extends RefCounted

const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")


func run() -> Array:
	var failures: Array = []
	var mapper := TraceCoordinateMapperScript.new()
	mapper.configure([4, 5, 3, 2])
	_assert_vector(
		failures,
		mapper.world_position([1, 2, 1, 1], 4),
		Vector3(5.5, -0.0, 0.0),
		"4D centered coordinate mapping"
	)
	_assert_vector(
		failures,
		mapper.world_position([0, 0, 0], 3),
		Vector3(-1.5, 2.0, -1.0),
		"3D cell center follows Python raw_to_world"
	)
	var bounds: Dictionary = mapper.board_bounds([4, 5, 3, 2], 4)
	if not bounds.get("ok", false):
		failures.append("bounds should be available")
		return failures
	_assert_vector(failures, bounds.get("min", Vector3.ZERO), Vector3(-2.0, -2.5, -1.5), "bounds min")
	_assert_vector(failures, bounds.get("max", Vector3.ZERO), Vector3(8.0, 3.18, 1.5), "bounds max includes subtle W marker clearance")
	_assert_vector(failures, mapper.slice_label_position(1), Vector3(4.34, 2.92, -1.16), "W label position")
	_test_decomposed_asymmetric_mapping(failures)
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
	_assert_vector(failures, decomposition.get("anchor", Vector3.ZERO), Vector3(7.0, 0.0, 0.0), "asymmetric anchor_1")
	_assert_vector(failures, decomposition.get("composed_world_point", Vector3.ZERO), Vector3(6.0, 1.0, 1.0), "compatibility composition is G_D plus anchor")
	_assert_vector(failures, mapper.world_position([1, 2, 2, 1], 4), decomposition.get("composed_world_point", Vector3.ZERO), "world_position uses decomposed compatibility path")
	var mapped_origin: Dictionary = mapper.presentation_coordinate([2, 3, 1, 0])
	var mapped_destination: Dictionary = mapper.presentation_coordinate([3, 3, 1, 0])
	var point_difference: Vector3 = mapper.centered_local_point(mapped_destination["visible_cell_3d"]) - mapper.centered_local_point(mapped_origin["visible_cell_3d"])
	_assert_vector(failures, point_difference, Vector3(1.0, 0.0, 0.0), "G_D point difference cancels centring")


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
