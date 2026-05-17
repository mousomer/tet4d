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
	var bounds: Dictionary = mapper.board_bounds([4, 5, 3, 2], 4)
	if not bounds.get("ok", false):
		failures.append("bounds should be available")
		return failures
	_assert_vector(failures, bounds.get("min", Vector3.ZERO), Vector3(-2.0, -2.5, -1.5), "bounds min")
	_assert_vector(failures, bounds.get("max", Vector3.ZERO), Vector3(8.0, 2.5, 1.5), "bounds max")
	return failures


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
