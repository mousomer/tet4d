extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures: Array = []
	var bridge := Tet4DCoreBridgeScript.new()
	if not bridge.is_available():
		failures.append("Tet4DCoreApi should be registered by the Stage 8 GDExtension")
		return failures
	_assert_equal(failures, bridge.get_core_version(), "0.1.0-stage8", "core version")
	_assert_equal(
		failures,
		bridge.get_core_status(),
		"native tet4d core skeleton loaded; gameplay not implemented",
		"core status"
	)
	_assert_equal(failures, bridge.echo_text("oracle-check"), "oracle-check", "echo text")
	_assert_equal(failures, bridge.stable_hash_text("tet4d"), "49fb984865ccbc22", "stable hash")
	_assert_equal(failures, bridge.add_integers(40, 2), 42, "integer addition")
	return failures


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
