extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures: Array = []
	var bridge := Tet4DCoreBridgeScript.new()
	if not bridge.is_available():
		failures.append("Tet4DCoreApi should be registered by the Stage 8 GDExtension")
		return failures
	_assert_equal(failures, bridge.get_core_version(), "0.9.0-stage23", "core version")
	_assert_equal(
		failures,
		bridge.get_core_status(),
		"native tet4d core loaded; Stage 23 live plain 4D prototype available beside accepted live plain 2D/3D",
		"core status"
	)
	_assert_equal(failures, bridge.echo_text("oracle-check"), "oracle-check", "echo text")
	_assert_equal(failures, bridge.stable_hash_text("tet4d"), "49fb984865ccbc22", "stable hash")
	_assert_equal(failures, bridge.add_integers(40, 2), 42, "integer addition")
	_assert_geometry_helpers(failures, bridge)
	_assert_query_helpers(failures, bridge)
	_assert_equal(failures, bridge.run_builtin_plain_2d_smoke_case(), true, "plain 2D smoke")
	_assert_equal(
		failures,
		bridge.get_plain_2d_parity_status(),
		"plain_2d Stage 11 parity cases match required fields and state_hash",
		"plain 2D parity status"
	)
	var cases := bridge.list_plain_2d_parity_cases()
	_assert_equal(failures, cases.size(), 5, "plain 2D parity case count")
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
	_assert_plain_nd_parity_api(failures, bridge)
	_assert_live_2d_session(failures, bridge)
	_assert_live_3d_session(failures, bridge)
	_assert_live_4d_session(failures, bridge)
	return failures


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_geometry_helpers(failures: Array, bridge: RefCounted) -> void:
	var blocks_3d := [[2, -1, 0], [0, 0, 1], [1, 0, -1], [0, 1, 1]]
	_assert_equal(
		failures,
		bridge.geometry_normalize_blocks(blocks_3d),
		[[-1, 0, 1], [-1, 1, 1], [0, 0, -1], [1, -1, 0]],
		"geometry normalize"
	)
	_assert_equal(
		failures,
		bridge.geometry_translate_blocks(blocks_3d, [-2, 3, 1]),
		[[-2, 3, 2], [-2, 4, 2], [-1, 3, 0], [0, 2, 1]],
		"geometry translate"
	)
	_assert_equal(
		failures,
		bridge.geometry_rotate_blocks(blocks_3d, 0, 2, 1),
		[[1, -1, -1], [2, 0, 1], [0, 0, 0], [2, 1, 1]],
		"geometry rotate"
	)
	_assert_equal(failures, bridge.geometry_hash_blocks(blocks_3d), "bbec08d1ebde9192", "geometry hash")


func _assert_query_helpers(failures: Array, bridge: RefCounted) -> void:
	var legal: Dictionary = bridge.native_piece_pose_diagnostic([4, 5], [[1, 1], [2, 1]], [])
	_assert_equal(failures, legal.get("ok"), true, "query legality ok")
	_assert_equal(failures, legal.get("legal"), true, "query legality accepts bounded cells")
	var duplicate: Dictionary = bridge.native_piece_pose_diagnostic([4, 5], [[1, 1], [1, 1]], [])
	_assert_equal(failures, duplicate.get("legal"), false, "query legality rejects duplicates")
	_assert_equal(failures, duplicate.get("reason"), "duplicate_piece_cell", "query duplicate reason")
	var torus: Dictionary = bridge.query_topology_axis_wrap_cell_step([3, 4], [0, 1], [2, 2], 0, 1)
	_assert_equal(failures, torus.get("ok"), true, "query topology ok")
	_assert_equal(failures, torus.get("target"), [0, 2], "query topology torus target")
	_assert_equal(failures, torus.get("glue_id"), "wrap_0", "query topology glue")


func _assert_plain_nd_parity_api(failures: Array, bridge: RefCounted) -> void:
	_assert_equal(failures, bridge.run_builtin_plain_nd_smoke_case(), true, "plain ND smoke")
	_assert_equal(
		failures,
		bridge.get_plain_nd_parity_status(),
		"plain_nd Stage 20 3D/4D movement, rotation, clear/scoring, and spawn-blocked game-over traces export required fields and state_hash",
		"plain ND parity status"
	)
	var cases: PackedStringArray = bridge.list_plain_nd_parity_cases()
	_assert_equal(failures, cases.size(), 10, "plain ND parity case count")
	for case_id in cases:
		_assert_equal(failures, bridge.get_plain_nd_required_field_parity(case_id), true, "plain ND required field parity %s" % case_id)
	var trace_3d = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_3d_short"))
	if typeof(trace_3d) != TYPE_DICTIONARY:
		failures.append("plain 3D exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_3d.get("dimension"), 3, "plain 3D trace dimension")
		_assert_equal(
			failures,
			trace_3d.get("final", {}).get("state_hash"),
			"9e183b178d0badec86b59a833782702d581b13a72d75bddeeda7f88333826dd7",
			"plain 3D final state hash"
		)
	var trace_4d = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_4d_short"))
	if typeof(trace_4d) != TYPE_DICTIONARY:
		failures.append("plain 4D exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_4d.get("dimension"), 4, "plain 4D trace dimension")
		_assert_equal(
			failures,
			trace_4d.get("final", {}).get("state_hash"),
			"d34d21da0a1c4aa6e947230e68e8b16a3e212b40bb7da1ccaef24200e7f80449",
			"plain 4D final state hash"
		)
	var trace_3d_rotation = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_3d_rotation_short"))
	if typeof(trace_3d_rotation) != TYPE_DICTIONARY:
		failures.append("plain 3D rotation exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_3d_rotation.get("dimension"), 3, "plain 3D rotation trace dimension")
		_assert_equal(
			failures,
			trace_3d_rotation.get("final", {}).get("state_hash"),
			"2d2ada3b5b425bf649c66cd8e6b2c3c2e24a57c4f8a7dc8aab26ac72a33a7e4d",
			"plain 3D rotation final state hash"
		)
		var frame_3d_rotation = trace_3d_rotation.get("frames", [])[0]
		_assert_equal(failures, frame_3d_rotation.get("active_piece", {}).get("last_rotation_plane"), [0.0, 2.0], "plain 3D rotation plane")
		_assert_equal(failures, frame_3d_rotation.get("active_piece", {}).get("last_rotation_steps"), 1, "plain 3D rotation steps")
	var trace_4d_rotation = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_4d_rotation_short"))
	if typeof(trace_4d_rotation) != TYPE_DICTIONARY:
		failures.append("plain 4D rotation exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_4d_rotation.get("dimension"), 4, "plain 4D rotation trace dimension")
		_assert_equal(
			failures,
			trace_4d_rotation.get("final", {}).get("state_hash"),
			"c3ccf55ccbac1998e7973ba4dc5e163398f2e32a6999cc933a3e4065dd71d34c",
			"plain 4D rotation final state hash"
		)
		var frame_4d_rotation = trace_4d_rotation.get("frames", [])[0]
		_assert_equal(failures, frame_4d_rotation.get("active_piece", {}).get("last_rotation_plane"), [0.0, 3.0], "plain 4D rotation plane")
		_assert_equal(failures, frame_4d_rotation.get("active_piece", {}).get("last_rotation_steps"), 1, "plain 4D rotation steps")
	var trace_3d_clear = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_3d_plane_clear_short"))
	if typeof(trace_3d_clear) != TYPE_DICTIONARY:
		failures.append("plain 3D clear exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_3d_clear.get("dimension"), 3, "plain 3D clear trace dimension")
		_assert_equal(
			failures,
			trace_3d_clear.get("final", {}).get("state_hash"),
			"9c1737872582996818277166c9b8d900a2362868315f15d1a8f9338e7afa6d57",
			"plain 3D clear final state hash"
		)
		var frame_3d_clear = trace_3d_clear.get("frames", [])[0]
		_assert_equal(failures, frame_3d_clear.get("lines"), 1, "plain 3D clear lines")
		_assert_equal(failures, frame_3d_clear.get("score"), 45, "plain 3D clear score")
		_assert_equal(failures, frame_3d_clear.get("command_result", {}).get("locked_cell_delta"), -3, "plain 3D clear locked delta")
	var trace_4d_clear = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_4d_plane_clear_short"))
	if typeof(trace_4d_clear) != TYPE_DICTIONARY:
		failures.append("plain 4D clear exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_4d_clear.get("dimension"), 4, "plain 4D clear trace dimension")
		_assert_equal(
			failures,
			trace_4d_clear.get("final", {}).get("state_hash"),
			"7b18f81b698dd0638fc1a11db4a896273f6d3bf3e5e31ded6241af3b6d1bee1f",
			"plain 4D clear final state hash"
		)
		var frame_4d_clear = trace_4d_clear.get("frames", [])[0]
		_assert_equal(failures, frame_4d_clear.get("lines"), 1, "plain 4D clear lines")
		_assert_equal(failures, frame_4d_clear.get("score"), 45, "plain 4D clear score")
		_assert_equal(failures, frame_4d_clear.get("command_result", {}).get("locked_cell_delta"), -3, "plain 4D clear locked delta")
	var trace_3d_spawn_blocked = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_3d_spawn_blocked_game_over"))
	if typeof(trace_3d_spawn_blocked) != TYPE_DICTIONARY:
		failures.append("plain 3D spawn-blocked exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_3d_spawn_blocked.get("dimension"), 3, "plain 3D spawn-blocked trace dimension")
		_assert_equal(
			failures,
			trace_3d_spawn_blocked.get("final", {}).get("state_hash"),
			"a950c1badd7dd47dda27d140b7aef5097e9331a890c145419076f1e938317619",
			"plain 3D spawn-blocked final state hash"
		)
		var frame_3d_spawn_blocked = trace_3d_spawn_blocked.get("frames", [])[0]
		_assert_equal(failures, frame_3d_spawn_blocked.get("drop_lock_status", {}).get("game_over"), true, "plain 3D spawn-blocked game_over")
		_assert_equal(failures, frame_3d_spawn_blocked.get("active_piece", {}).get("shape"), "TRACE_3D_NEXT", "plain 3D spawn-blocked shape")
		_assert_equal(failures, frame_3d_spawn_blocked.get("active_piece", {}).get("pos"), [2.0, -2.0, 2.0], "plain 3D spawn-blocked position")
	var trace_4d_spawn_blocked = JSON.parse_string(bridge.export_plain_nd_trace_json("gameplay_plain_4d_spawn_blocked_game_over"))
	if typeof(trace_4d_spawn_blocked) != TYPE_DICTIONARY:
		failures.append("plain 4D spawn-blocked exported trace should parse as JSON dictionary")
	else:
		_assert_equal(failures, trace_4d_spawn_blocked.get("dimension"), 4, "plain 4D spawn-blocked trace dimension")
		_assert_equal(
			failures,
			trace_4d_spawn_blocked.get("final", {}).get("state_hash"),
			"ee8f825bce34feb8fa7f9bdd15157f699bba9c34a650a582de6a6a3ee81d8ad6",
			"plain 4D spawn-blocked final state hash"
		)
		var frame_4d_spawn_blocked = trace_4d_spawn_blocked.get("frames", [])[0]
		_assert_equal(failures, frame_4d_spawn_blocked.get("drop_lock_status", {}).get("game_over"), true, "plain 4D spawn-blocked game_over")
		_assert_equal(failures, frame_4d_spawn_blocked.get("active_piece", {}).get("shape"), "TRACE_4D_NEXT", "plain 4D spawn-blocked shape")
		_assert_equal(failures, frame_4d_spawn_blocked.get("active_piece", {}).get("pos"), [2.0, -2.0, 2.0, 2.0], "plain 4D spawn-blocked position")


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


func _assert_live_3d_session(failures: Array, bridge: RefCounted) -> void:
	bridge.live_3d_reset()
	var initial_hash: String = bridge.live_3d_state_hash()
	var snapshot = JSON.parse_string(bridge.live_3d_snapshot_json())
	if typeof(snapshot) != TYPE_DICTIONARY:
		failures.append("live 3D snapshot should parse as JSON dictionary")
		return
	_assert_equal(failures, snapshot.get("trace_type"), "live_3d", "live 3D trace type")
	_assert_equal(failures, snapshot.get("case_id"), "live_plain_3d", "live 3D case")
	_assert_equal(failures, snapshot.get("dimension"), 3, "live 3D dimension")
	_assert_equal(failures, snapshot.get("board_shape"), [6.0, 10.0, 6.0], "live 3D board shape")
	_assert_equal(failures, snapshot.get("current_piece", ""), "I3", "live 3D deterministic initial piece")
	_assert_equal(failures, snapshot.get("next_piece", ""), "O3", "live 3D deterministic next piece")
	_assert_equal(failures, snapshot.get("game_over", true), false, "live 3D initial game_over")
	if snapshot.get("active_cells", []).is_empty():
		failures.append("live 3D snapshot should include active cells")
	bridge.live_3d_apply_command("move_x_pos")
	if bridge.live_3d_state_hash() == initial_hash:
		failures.append("live 3D state hash should change after X movement")
	var moved_hash: String = bridge.live_3d_state_hash()
	bridge.live_3d_apply_command("move_z_pos")
	if bridge.live_3d_state_hash() == moved_hash:
		failures.append("live 3D state hash should change after Z movement")
	bridge.live_3d_apply_command("rotate_xy_pos")
	var rotated_xy = JSON.parse_string(bridge.live_3d_snapshot_json())
	if typeof(rotated_xy) == TYPE_DICTIONARY:
		_assert_equal(failures, rotated_xy.get("last_rotation_plane", ""), "XY", "live 3D XY rotation plane")
	else:
		failures.append("live 3D rotated snapshot should parse")
	bridge.live_3d_reset()
	bridge.live_3d_apply_command("rotate_xz_pos")
	var rotated_xz = JSON.parse_string(bridge.live_3d_snapshot_json())
	if typeof(rotated_xz) == TYPE_DICTIONARY:
		_assert_equal(failures, rotated_xz.get("last_rotation_plane", ""), "XZ", "live 3D XZ rotation plane")
	else:
		failures.append("live 3D XZ rotated snapshot should parse")
	bridge.live_3d_reset()
	bridge.live_3d_apply_command("rotate_yz_pos")
	var rotated_yz = JSON.parse_string(bridge.live_3d_snapshot_json())
	if typeof(rotated_yz) == TYPE_DICTIONARY:
		_assert_equal(failures, rotated_yz.get("last_rotation_plane", ""), "YZ", "live 3D YZ rotation plane")
	else:
		failures.append("live 3D YZ rotated snapshot should parse")
	bridge.live_3d_reset()
	bridge.live_3d_apply_command("soft_drop")
	if bridge.live_3d_state_hash() == initial_hash:
		failures.append("live 3D state hash should change after soft_drop")
	bridge.live_3d_apply_command("hard_drop")
	var after_drop = JSON.parse_string(bridge.live_3d_snapshot_json())
	if typeof(after_drop) != TYPE_DICTIONARY:
		failures.append("live 3D post-drop snapshot should parse as JSON dictionary")
		return
	_assert_equal(failures, after_drop.get("score"), 5, "live 3D hard drop score")
	_assert_equal(failures, after_drop.get("current_piece", ""), "O3", "live 3D first post-lock piece")
	_assert_equal(failures, after_drop.get("next_piece", ""), "L3", "live 3D first post-lock next piece")
	_assert_equal(failures, after_drop.get("last_command", ""), "hard_drop", "live 3D last command")
	_assert_equal(failures, after_drop.get("last_command_status", ""), "accepted", "live 3D last command status")
	if after_drop.get("locked_cells", []).is_empty():
		failures.append("live 3D hard drop should expose locked cells")
	bridge.live_3d_reset()
	_assert_equal(failures, bridge.live_3d_state_hash(), initial_hash, "live 3D reset hash")
	bridge.live_3d_tick()
	if bridge.live_3d_status().find("last_command=tick") < 0:
		failures.append("live_3d_tick should update native status")


func _assert_live_4d_session(failures: Array, bridge: RefCounted) -> void:
	bridge.live_4d_reset()
	var initial_hash: String = bridge.live_4d_state_hash()
	var snapshot = JSON.parse_string(bridge.live_4d_snapshot_json())
	if typeof(snapshot) != TYPE_DICTIONARY:
		failures.append("live 4D snapshot should parse as JSON dictionary")
		return
	_assert_equal(failures, snapshot.get("trace_type"), "live_4d", "live 4D trace type")
	_assert_equal(failures, snapshot.get("case_id"), "live_plain_4d", "live 4D case")
	_assert_equal(failures, snapshot.get("dimension"), 4, "live 4D dimension")
	_assert_equal(failures, snapshot.get("board_shape"), [5.0, 10.0, 4.0, 4.0], "live 4D board shape")
	_assert_equal(failures, snapshot.get("w_slice_count"), 4, "live 4D W slice count")
	_assert_equal(failures, snapshot.get("current_piece", ""), "TRACE_4D", "live 4D deterministic initial piece")
	_assert_equal(failures, snapshot.get("next_piece", ""), "STAIR4", "live 4D deterministic next piece")
	if snapshot.get("active_cells", []).is_empty():
		failures.append("live 4D snapshot should include active cells")
	bridge.live_4d_apply_command("move_w_pos")
	if bridge.live_4d_state_hash() == initial_hash:
		failures.append("live 4D state hash should change after W movement")
	var moved_w = JSON.parse_string(bridge.live_4d_snapshot_json())
	if typeof(moved_w) == TYPE_DICTIONARY:
		_assert_equal(failures, moved_w.get("last_command", ""), "move_w_pos", "live 4D W movement command")
		_assert_equal(failures, moved_w.get("active_w"), 2, "live 4D active W after W movement")
	else:
		failures.append("live 4D W movement snapshot should parse")
	bridge.live_4d_reset()
	bridge.live_4d_apply_command("rotate_xw_pos")
	var rotated_xw = JSON.parse_string(bridge.live_4d_snapshot_json())
	if typeof(rotated_xw) == TYPE_DICTIONARY:
		_assert_equal(failures, rotated_xw.get("last_rotation_plane", ""), "XW", "live 4D XW rotation plane")
	else:
		failures.append("live 4D XW rotated snapshot should parse")
	bridge.live_4d_reset()
	bridge.live_4d_apply_command("rotate_yw_pos")
	var rotated_yw = JSON.parse_string(bridge.live_4d_snapshot_json())
	if typeof(rotated_yw) == TYPE_DICTIONARY:
		_assert_equal(failures, rotated_yw.get("last_rotation_plane", ""), "YW", "live 4D YW rotation plane")
	else:
		failures.append("live 4D YW rotated snapshot should parse")
	bridge.live_4d_reset()
	bridge.live_4d_apply_command("rotate_zw_pos")
	var rotated_zw = JSON.parse_string(bridge.live_4d_snapshot_json())
	if typeof(rotated_zw) == TYPE_DICTIONARY:
		_assert_equal(failures, rotated_zw.get("last_rotation_plane", ""), "ZW", "live 4D ZW rotation plane")
	else:
		failures.append("live 4D ZW rotated snapshot should parse")
	bridge.live_4d_reset()
	bridge.live_4d_apply_command("hard_drop")
	var after_drop = JSON.parse_string(bridge.live_4d_snapshot_json())
	if typeof(after_drop) != TYPE_DICTIONARY:
		failures.append("live 4D post-drop snapshot should parse as JSON dictionary")
		return
	_assert_equal(failures, after_drop.get("score"), 5, "live 4D hard drop score")
	_assert_equal(failures, after_drop.get("current_piece", ""), "STAIR4", "live 4D first post-lock piece")
	_assert_equal(failures, after_drop.get("last_command", ""), "hard_drop", "live 4D last command")
	_assert_equal(failures, after_drop.get("last_command_status", ""), "accepted", "live 4D last command status")
	if after_drop.get("locked_cells", []).is_empty():
		failures.append("live 4D hard drop should expose locked cells")
	bridge.live_4d_reset()
	_assert_equal(failures, bridge.live_4d_state_hash(), initial_hash, "live 4D reset hash")
	bridge.live_4d_tick()
	if bridge.live_4d_status().find("last_command=tick") < 0:
		failures.append("live_4d_tick should update native status")
