extends RefCounted

const ParticleRendererScript = preload("res://scripts/rendering/particle_renderer.gd")


func run() -> Array:
	var failures: Array = []
	var renderer := ParticleRendererScript.new()
	var material := StandardMaterial3D.new()
	var particle_position := Vector3(10.0, 2.0, -1.0)
	var trail_positions := [
		Vector3(8.0, 2.0, -1.0),
		Vector3(9.0, 2.0, -1.0),
		particle_position,
	]
	renderer.setup(
		particle_position,
		material,
		material,
		0.25,
		[],
		material,
		trail_positions
	)
	_assert_vector(failures, renderer.position, particle_position, "particle node position")
	var trail_offsets := _trail_dot_offsets(renderer)
	if trail_offsets.size() != 2:
		failures.append("expected 2 trail dots, got %d" % trail_offsets.size())
		renderer.free()
		return failures
	_assert_vector(failures, trail_offsets[0], Vector3(-2.0, 0.0, 0.0), "oldest trail dot offset")
	_assert_vector(failures, trail_offsets[1], Vector3(-1.0, 0.0, 0.0), "newest trail dot offset")
	renderer.free()
	return failures


func _trail_dot_offsets(renderer: Node3D) -> Array:
	var offsets: Array = []
	for child in renderer.get_children():
		if child is MeshInstance3D and child.position.length() > 0.001:
			offsets.append(child.position)
	return offsets


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
