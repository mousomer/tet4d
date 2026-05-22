extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures: Array = []
	var bridge := Tet4DCoreBridgeScript.new()
	if not bridge.is_available():
		failures.append("Tet4DCoreApi should be registered by the Stage 8 GDExtension")
		return failures
	_assert_equal(failures, bridge.get_core_version(), "0.6.0-stage13", "core version")
	_assert_equal(
		failures,
		bridge.get_core_status(),
		"native tet4d core loaded; Stage 13 polished live plain 2D session available",
		"core status"
	)
	_assert_equal(failures, bridge.echo_text("oracle-check"), "oracle-check", "echo text")
	_assert_equal(failures, bridge.stable_hash_text("tet4d"), "49fb984865ccbc22", "stable hash")
	_assert_equal(failures, bridge.add_integers(40, 2), 42, "integer addition")
	_assert_equal(failures, bridge.run_builtin_plain_2d_smoke_case(), true, "plain 2D smoke")
	_assert_equal(
		failures,
		bridge.get_plain_2d_parity_status(),
		"plain_2d Stage 11 parity cases match required fields and state_hash",
		"plain 2D parity status"
	)
	var cases := bridge.list_plain_2d_parity_cases()
	_assert_equal(failures, cases.size(), 4, "plain 2D parity case count")
	for case_id in cases:
		_assert_equal(failures, bridge.get_plain_2d_required_field_parity(case_id), true, "plain 2D required field parity %s" % case_id)
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
	var line_clear_trace = JSON.parse_string(bridge.export_plain_2d_trace_json("gameplay_plain_2d_line_clear_short"))
	if typeof(line_clear_trace) != TYPE_DICTIONARY:
		failures.append("line-clear plain 2D exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, line_clear_trace.get("final", {}).get("score"), 45, "line-clear final score")
		_assert_equal(
			failures,
			line_clear_trace.get("final", {}).get("state_hash"),
			"b12eb245dc55563078b0342123f3bc519549b3eb75b40c5fd691e41536c95fc1",
			"line-clear final state hash"
		)
	_assert_live_2d_session(failures, bridge)
	return failures


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_live_2d_session(failures: Array, bridge: RefCounted) -> void:
	bridge.live_2d_reset()
	var initial_hash: String = bridge.live_2d_state_hash()
	var snapshot = JSON.parse_string(bridge.live_2d_snapshot_json())
	if typeof(snapshot) != TYPE_DICTIONARY:
		failures.append("live 2D snapshot should parse as JSON dictionary")
		return
	_assert_equal(failures, snapshot.get("trace_type"), "live_2d", "live 2D trace type")
	_assert_equal(failures, snapshot.get("case_id"), "live_plain_2d", "live 2D case")
	_assert_equal(failures, snapshot.get("current_piece", ""), "I", "live 2D deterministic initial piece")
	_assert_equal(failures, snapshot.get("next_piece", ""), "O", "live 2D deterministic next piece")
	_assert_equal(failures, snapshot.get("game_over", true), false, "live 2D initial game_over")
	_assert_equal(failures, snapshot.get("game_over_reason", "unexpected"), "", "live 2D initial game_over_reason")
	_assert_equal(failures, snapshot.get("paused", true), false, "live 2D initial paused")
	if snapshot.get("active_cells", []).is_empty():
		failures.append("live 2D snapshot should include active cells")
	bridge.live_2d_apply_command("soft_drop")
	if bridge.live_2d_state_hash() == initial_hash:
		failures.append("live 2D state hash should change after soft_drop")
	bridge.live_2d_apply_command("hard_drop")
	var after_drop = JSON.parse_string(bridge.live_2d_snapshot_json())
	if typeof(after_drop) != TYPE_DICTIONARY:
		failures.append("live 2D post-drop snapshot should parse as JSON dictionary")
		return
	var diagnostics: Array = after_drop.get("diagnostics_lines", [])
	if not diagnostics.has("score: 5"):
		failures.append("live 2D hard drop should update score diagnostics")
	if not after_drop.has("score"):
		failures.append("live snapshot exposes score")
	if not after_drop.has("lines"):
		failures.append("live snapshot exposes lines")
	_assert_equal(failures, after_drop.get("current_piece", ""), "O", "live 2D first post-lock piece")
	_assert_equal(failures, after_drop.get("next_piece", ""), "T", "live 2D first post-lock next piece")
	_assert_equal(failures, after_drop.get("last_command", ""), "hard_drop", "live snapshot exposes last command")
	_assert_equal(failures, after_drop.get("last_command_status", ""), "accepted", "live snapshot exposes last command status")
	bridge.live_2d_apply_command("hard_drop")
	var second_drop = JSON.parse_string(bridge.live_2d_snapshot_json())
	if typeof(second_drop) == TYPE_DICTIONARY:
		_assert_equal(failures, second_drop.get("current_piece", ""), "T", "live 2D second post-lock piece")
	else:
		failures.append("live 2D second post-drop snapshot should parse as JSON dictionary")
	bridge.live_2d_reset()
	_assert_equal(failures, bridge.live_2d_state_hash(), initial_hash, "live 2D reset hash")
	var game_over_seen := false
	for step in range(60):
		bridge.live_2d_apply_command("hard_drop")
		var game_over_snapshot = JSON.parse_string(bridge.live_2d_snapshot_json())
		if typeof(game_over_snapshot) == TYPE_DICTIONARY and bool(game_over_snapshot.get("game_over", false)):
			game_over_seen = true
			if str(game_over_snapshot.get("game_over_reason", "")).is_empty():
				failures.append("live 2D game_over should include a reason")
			var stopped_hash: String = bridge.live_2d_state_hash()
			bridge.live_2d_apply_command("move_left")
			_assert_equal(failures, bridge.live_2d_state_hash(), stopped_hash, "live 2D rejected command hash")
			if bridge.live_2d_status().find("last_command=rejected:move_left") < 0:
				failures.append("live 2D should reject commands after game_over")
			bridge.live_2d_reset()
			var reset_snapshot = JSON.parse_string(bridge.live_2d_snapshot_json())
			if typeof(reset_snapshot) == TYPE_DICTIONARY:
				_assert_equal(failures, reset_snapshot.get("game_over", true), false, "live 2D reset clears game_over")
				_assert_equal(failures, reset_snapshot.get("game_over_reason", "unexpected"), "", "live 2D reset clears reason")
			break
	if not game_over_seen:
		failures.append("live 2D repeated hard drops should eventually reach native game_over")
	bridge.live_2d_tick()
	if bridge.live_2d_status().find("last_command=tick") < 0:
		failures.append("live_2d_tick should update native status")
	if bridge.live_2d_status().find("next_piece=") < 0:
		failures.append("live_2d_status should expose next piece")
