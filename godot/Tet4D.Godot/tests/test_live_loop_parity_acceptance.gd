extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures: Array = []
	var bridge := Tet4DCoreBridgeScript.new()
	if not bridge.is_available():
		failures.append("Stage 41 live-loop parity acceptance requires Tet4DCoreApi")
		return failures
	_assert_python_oracle_parity_exports(failures, bridge)
	_assert_live_case(failures, bridge, _case_2d())
	_assert_live_case(failures, bridge, _case_3d())
	_assert_live_case(failures, bridge, _case_4d())
	return failures


func _assert_python_oracle_parity_exports(failures: Array, bridge: RefCounted) -> void:
	for case_id in [
		"gameplay_plain_2d_short",
		"gameplay_plain_2d_rotation_short",
		"gameplay_plain_2d_hard_drop_lock",
		"gameplay_plain_3d_short",
		"gameplay_plain_3d_rotation_short",
		"gameplay_plain_4d_short",
		"gameplay_plain_4d_rotation_short",
	]:
		var parity_ok: bool = false
		if case_id.begins_with("gameplay_plain_2d"):
			parity_ok = bridge.get_plain_2d_required_field_parity(case_id)
		else:
			parity_ok = bridge.get_plain_nd_required_field_parity(case_id)
		if not parity_ok:
			failures.append("Stage 41 Python oracle parity export failed for %s" % case_id)


func _assert_live_case(failures: Array, bridge: RefCounted, case_def: Dictionary) -> void:
	var mode := str(case_def.get("mode", ""))
	_reset_mode(bridge, mode)
	_assert_step(failures, case_def, -1, "reset", _snapshot(bridge, mode))
	var commands: Array = case_def.get("commands", [])
	for index in range(commands.size()):
		var command := str(commands[index])
		_apply_command(bridge, mode, command)
		_assert_step(failures, case_def, index, command, _snapshot(bridge, mode))


func _assert_step(failures: Array, case_def: Dictionary, action_index: int, action_name: String, snapshot: Dictionary) -> void:
	if snapshot.is_empty():
		failures.append(
			_mismatch(case_def, action_index, action_name, "snapshot_parse", {}, {}, [], [])
		)
		return
	var step_key := "initial" if action_index < 0 else action_name
	var expected: Dictionary = case_def.get("expected", {}).get(step_key, {})
	for field in ["trace_type", "dimension", "current_piece", "next_piece", "last_command", "last_command_status", "score", "lines", "game_over", "last_rotation_plane", "active_w", "state_hash"]:
		if not expected.has(field):
			continue
		var actual_value = snapshot.get(field)
		var expected_value = expected.get(field)
		if actual_value != expected_value:
			failures.append(
				_mismatch(case_def, action_index, action_name, "field:%s" % field, snapshot, expected, _cell_positions(snapshot.get("active_cells", [])), expected.get("active_cells", []))
			)
	var active_cells := _cell_positions(snapshot.get("active_cells", []))
	if expected.has("active_cells") and active_cells != expected.get("active_cells"):
		failures.append(
			_mismatch(case_def, action_index, action_name, "active_cells", snapshot, expected, active_cells, expected.get("active_cells", []))
		)
	var locked_cells := _cell_positions(snapshot.get("locked_cells", []))
	if expected.has("locked_cells") and locked_cells != expected.get("locked_cells"):
		failures.append(
			_mismatch(case_def, action_index, action_name, "locked_cells", snapshot, expected, locked_cells, expected.get("locked_cells", []))
		)


func _mismatch(case_def: Dictionary, action_index: int, action_name: String, reason: String, snapshot: Dictionary, expected: Dictionary, godot_cells: Array, expected_cells: Array) -> String:
	return "mode=%s action_index=%d action=%s reason=%s godot_state=%s python_expected=%s godot_cells=%s python_expected_cells=%s" % [
		str(case_def.get("mode", "")),
		action_index,
		action_name,
		reason,
		_compact_state(snapshot),
		_compact_state(expected),
		str(godot_cells),
		str(expected_cells),
	]


func _compact_state(state: Dictionary) -> Dictionary:
	if state.is_empty():
		return {}
	var summary := {}
	for field in ["trace_type", "dimension", "current_piece", "next_piece", "last_command", "last_command_status", "score", "lines", "game_over", "last_rotation_plane", "active_w", "state_hash"]:
		if state.has(field):
			summary[field] = state.get(field)
	return summary


func _cell_positions(cells: Array) -> Array:
	var positions: Array = []
	for cell in cells:
		if typeof(cell) != TYPE_DICTIONARY:
			continue
		var position: Array = cell.get("position", [])
		var normalized: Array = []
		for value in position:
			normalized.append(int(value))
		positions.append(normalized)
	return positions


func _snapshot(bridge: RefCounted, mode: String) -> Dictionary:
	var raw := ""
	match mode:
		"live_2d":
			raw = bridge.live_2d_snapshot_json()
		"live_3d":
			raw = bridge.live_3d_snapshot_json()
		"live_4d":
			raw = bridge.live_4d_snapshot_json()
	var parsed = JSON.parse_string(raw)
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func _reset_mode(bridge: RefCounted, mode: String) -> void:
	match mode:
		"live_2d":
			bridge.live_2d_reset()
		"live_3d":
			bridge.live_3d_reset()
		"live_4d":
			bridge.live_4d_reset()


func _apply_command(bridge: RefCounted, mode: String, command: String) -> void:
	match mode:
		"live_2d":
			bridge.live_2d_apply_command(command)
		"live_3d":
			bridge.live_3d_apply_command(command)
		"live_4d":
			bridge.live_4d_apply_command(command)


func _case_2d() -> Dictionary:
	return {
		"mode": "live_2d",
		"commands": ["move_right", "rotate_cw", "soft_drop", "hard_drop"],
		"expected": {
			"initial": {
				"trace_type": "live_2d",
				"dimension": 2.0,
				"current_piece": "I",
				"next_piece": "O",
				"last_command": "reset",
				"last_command_status": "reset",
				"score": 0.0,
				"lines": 0.0,
				"game_over": false,
				"state_hash": "b64c640d1210416e5dad64cdea3c164ee9b742b2a34bcd1728d88d090aeaa8eb",
				"active_cells": [[1, -2], [2, -2], [3, -2], [4, -2]],
				"locked_cells": [],
			},
			"move_right": {
				"last_command": "move_right",
				"last_command_status": "accepted",
				"state_hash": "58743aecf6487bb3b4f985e92e3a374f8f4c9c7f037003667e0f17a61a2cbd35",
				"active_cells": [[2, -2], [3, -2], [4, -2], [5, -2]],
			},
			"rotate_cw": {
				"last_command": "rotate_cw",
				"last_command_status": "accepted",
				"state_hash": "e6ecc93921631e9ffb6ef0f8657b80580411e0d543642279a6c6080e868e830b",
				"active_cells": [[3, -4], [3, -3], [3, -2], [3, -1]],
			},
			"soft_drop": {
				"last_command": "soft_drop",
				"last_command_status": "accepted",
				"state_hash": "3895562a30f48cc42038abe24061991850484f3eaf5db27cb1ed9c35ef5e41c6",
				"active_cells": [[3, -3], [3, -2], [3, -1], [3, 0]],
			},
			"hard_drop": {
				"current_piece": "O",
				"next_piece": "T",
				"last_command": "hard_drop",
				"last_command_status": "accepted",
				"score": 5.0,
				"lines": 0.0,
				"game_over": false,
				"state_hash": "4f50c9a5ca23e778bc8b16be09a4e0054d9e528be8aca5b7c59307bfa335dba9",
				"active_cells": [[2, -2], [2, -1], [3, -2], [3, -1]],
				"locked_cells": [[3, 2], [3, 3], [3, 4], [3, 5]],
			},
		},
	}


func _case_3d() -> Dictionary:
	return {
		"mode": "live_3d",
		"commands": ["move_z_pos", "rotate_xz_pos", "soft_drop", "hard_drop"],
		"expected": {
			"initial": {
				"trace_type": "live_3d",
				"dimension": 3.0,
				"current_piece": "I3",
				"next_piece": "O3",
				"last_command": "reset",
				"last_command_status": "reset",
				"last_rotation_plane": "none",
				"score": 0.0,
				"game_over": false,
				"state_hash": "ec6432100343b352c7933a2268db6f4ac127ce63376d02f4b3d11b8dc8084e17",
				"active_cells": [[1, -2, 2], [2, -2, 2], [3, -2, 2], [4, -2, 2]],
				"locked_cells": [],
			},
			"move_z_pos": {
				"last_command": "move_z_pos",
				"last_command_status": "accepted",
				"state_hash": "3f64087028ba5a73f142167cbe96dd135b03a19d334231270b27ff4b69987651",
				"active_cells": [[1, -2, 3], [2, -2, 3], [3, -2, 3], [4, -2, 3]],
			},
			"rotate_xz_pos": {
				"last_command": "rotate_xz_pos",
				"last_command_status": "accepted",
				"last_rotation_plane": "XZ",
				"state_hash": "a95ff064cc4dbe5e35ea0728142c594f98eebf5661a654df7a3c56e61ba28cc3",
				"active_cells": [[2, -2, 1], [2, -2, 2], [2, -2, 3], [2, -2, 4]],
			},
			"soft_drop": {
				"last_command": "soft_drop",
				"last_command_status": "accepted",
				"last_rotation_plane": "XZ",
				"state_hash": "7784ed5917e0d95e8612e22d55593695d16f21f4897bd86c647ab89cb8e81040",
				"active_cells": [[2, -1, 1], [2, -1, 2], [2, -1, 3], [2, -1, 4]],
			},
			"hard_drop": {
				"current_piece": "O3",
				"next_piece": "L3",
				"last_command": "hard_drop",
				"last_command_status": "accepted",
				"last_rotation_plane": "none",
				"score": 5.0,
				"game_over": false,
				"state_hash": "e48d956bc57d77448656c846b1add733820c1781b26768eb690902b1048f090c",
				"active_cells": [[2, -2, 2], [2, -1, 2], [3, -2, 2], [3, -1, 2]],
				"locked_cells": [[2, 9, 1], [2, 9, 2], [2, 9, 3], [2, 9, 4]],
			},
		},
	}


func _case_4d() -> Dictionary:
	return {
		"mode": "live_4d",
		"commands": ["move_w_pos", "rotate_xw_pos", "soft_drop", "hard_drop"],
		"expected": {
			"initial": {
				"trace_type": "live_4d",
				"dimension": 4.0,
				"current_piece": "TRACE_4D",
				"next_piece": "STAIR4",
				"last_command": "reset",
				"last_command_status": "reset",
				"last_rotation_plane": "none",
				"active_w": 1.0,
				"score": 0.0,
				"game_over": false,
				"state_hash": "daef26d673067f1cccf82085672ed1a0747e19bf0ba178ead3421bba2a0476c2",
				"active_cells": [[1, -2, 1, 1], [2, -2, 1, 1]],
				"locked_cells": [],
			},
			"move_w_pos": {
				"last_command": "move_w_pos",
				"last_command_status": "accepted",
				"active_w": 2.0,
				"state_hash": "fad67f35474bb7be413a4a22c22171ee7eb71c2787b9140533c1702e7b81a057",
				"active_cells": [[1, -2, 1, 2], [2, -2, 1, 2]],
			},
			"rotate_xw_pos": {
				"last_command": "rotate_xw_pos",
				"last_command_status": "accepted",
				"last_rotation_plane": "XW",
				"active_w": 2.0,
				"state_hash": "afac08f54c76ac58449424ae6f28a7841f4c1fbd56d9ea23295baf8a3031f5cf",
				"active_cells": [[1, -2, 1, 1], [1, -2, 1, 2]],
			},
			"soft_drop": {
				"last_command": "soft_drop",
				"last_command_status": "accepted",
				"last_rotation_plane": "XW",
				"active_w": 2.0,
				"state_hash": "f65cec3b94d5329ae76526154d634f25ef9bfaf1c341738c62ea3ddf192c29fa",
				"active_cells": [[1, -1, 1, 1], [1, -1, 1, 2]],
			},
			"hard_drop": {
				"current_piece": "STAIR4",
				"next_piece": "TRACE_4D",
				"last_command": "hard_drop",
				"last_command_status": "accepted",
				"last_rotation_plane": "none",
				"active_w": 1.0,
				"score": 5.0,
				"game_over": false,
				"state_hash": "60382ba2ca54b30596e64e7c9d87f9bec3f0d6726aa2c7fc46cfad053b39c26f",
				"active_cells": [[1, -2, 1, 1], [1, -1, 1, 1], [2, -1, 1, 1], [2, -1, 2, 1], [2, -1, 2, 2]],
				"locked_cells": [[1, 9, 1, 1], [1, 9, 1, 2]],
			},
		},
	}
