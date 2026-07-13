extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures := []
	var bridge = Tet4DCoreBridgeScript.new()
	if not bridge.live_2d_configure([10, 20]):
		failures.append("native 2D alternate shape should configure")
	elif _shape(_snapshot(bridge.live_2d_snapshot_json())) != [10, 20]:
		failures.append("native 2D snapshot should expose alternate shape")
	bridge.live_2d_reset()
	if _shape(_snapshot(bridge.live_2d_snapshot_json())) != [10, 20]:
		failures.append("native 2D restart should preserve alternate shape")
	if bridge.live_3d_configure([3, 16, 8]):
		failures.append("native 3D should reject unsupported width")
	if not bridge.live_3d_configure([8, 16, 8]):
		failures.append("native 3D alternate shape should configure")
	if not bridge.live_4d_configure([8, 16, 5, 8]):
		failures.append("native W=8 shape should configure")
	else:
		var snapshot := _snapshot(bridge.live_4d_snapshot_json())
		if _shape(snapshot) != [8, 16, 5, 8] or int(snapshot.get("w_slice_count", 0)) != 8:
			failures.append("native W=8 snapshot identity mismatch")
		bridge.live_4d_apply_command("move_w_pos")
		bridge.live_4d_reset()
		if _shape(_snapshot(bridge.live_4d_snapshot_json())) != [8, 16, 5, 8]:
			failures.append("native W=8 restart should preserve shape")
	return failures


func _snapshot(text: String) -> Dictionary:
	var parsed = JSON.parse_string(text)
	return parsed if parsed is Dictionary else {}


func _shape(snapshot: Dictionary) -> Array:
	var result := []
	for value in snapshot.get("board_shape", []):
		result.append(int(value))
	return result
