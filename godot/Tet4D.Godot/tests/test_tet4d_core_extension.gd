extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures: Array = []
	var bridge := Tet4DCoreBridgeScript.new()
	if not bridge.is_available():
		failures.append("Tet4DCoreApi should be registered by the Stage 8 GDExtension")
		return failures
	_assert_equal(failures, bridge.get_core_version(), "0.3.0-stage10", "core version")
	_assert_equal(
		failures,
		bridge.get_core_status(),
		"native tet4d core loaded; plain 2D snapshot and hash parity available",
		"core status"
	)
	_assert_equal(failures, bridge.echo_text("oracle-check"), "oracle-check", "echo text")
	_assert_equal(failures, bridge.stable_hash_text("tet4d"), "49fb984865ccbc22", "stable hash")
	_assert_equal(failures, bridge.add_integers(40, 2), 42, "integer addition")
	_assert_equal(failures, bridge.run_builtin_plain_2d_smoke_case(), true, "plain 2D smoke")
	_assert_equal(
		failures,
		bridge.get_plain_2d_parity_status(),
		"plain_2d gameplay_plain_2d_short required fields and state_hash match",
		"plain 2D parity status"
	)
	_assert_equal(failures, bridge.get_plain_2d_required_field_parity(), true, "plain 2D required field parity")
	var trace = JSON.parse_string(bridge.export_plain_2d_trace_json())
	if typeof(trace) != TYPE_DICTIONARY:
		failures.append("plain 2D exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace.get("case_id"), "gameplay_plain_2d_short", "plain 2D trace case")
		_assert_equal(failures, trace.get("dimension"), 2, "plain 2D trace dimension")
		_assert_equal(failures, trace.get("final", {}).get("score"), 5, "plain 2D final score")
		_assert_equal(
			failures,
			trace.get("final", {}).get("state_hash"),
			"2d3a6eb2744d46bc147ae7d21855036e1ff241a99261ab5324b20958ec353139",
			"plain 2D final state hash"
		)
	return failures


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
