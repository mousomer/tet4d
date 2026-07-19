extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures := []
	var bridge = Tet4DCoreBridgeScript.new()
	if not bridge.live_2d_configure(_setup("live_2d", "large", [10, 20], "classic", 1337, 1)):
		failures.append("native 2D alternate shape should configure")
	else:
		var snapshot_2d := _snapshot(bridge.live_2d_snapshot_json())
		if _shape(snapshot_2d) != [10, 20] or snapshot_2d.get("piece_set_id") != "classic":
			failures.append("native 2D snapshot should expose canonical setup")
	bridge.live_2d_reset()
	if _shape(_snapshot(bridge.live_2d_snapshot_json())) != [10, 20]:
		failures.append("native 2D restart should preserve alternate shape")
	var malformed := _setup("live_2d", "standard", [6, 6], "classic", 1337, 1)
	malformed.erase("seed")
	if bridge.live_2d_configure(malformed):
		failures.append("native fixed-seed setup must reject missing seed")
	malformed = _setup("live_2d", "standard", [6, 6], "classic", 1337, 1)
	malformed["seed"] = 13.37
	if bridge.live_2d_configure(malformed):
		failures.append("native setup must reject floating-point seed coercion")
	malformed = _setup("live_2d", "standard", [6, 6], "classic", 1337, 1)
	malformed["unexpected"] = true
	if bridge.live_2d_configure(malformed):
		failures.append("native setup must reject unsupported fields")
	if bridge.live_3d_configure(_setup("live_3d", "large", [3, 16, 8], "native_3d", 1337, 1)):
		failures.append("native 3D should reject unsupported width")
	if not bridge.live_3d_configure(_setup("live_3d", "large", [8, 16, 8], "embedded_2d", 2025, 6)):
		failures.append("native 3D alternate shape should configure")
	elif _snapshot(bridge.live_3d_snapshot_json()).get("piece_set_id") != "embedded_2d":
		failures.append("native 3D Embedded 2D identity missing")
	if not bridge.live_4d_configure(_setup("live_4d", "wide_w", [8, 16, 5, 8], "embedded_3d", 42, 8)):
		failures.append("native W=8 shape should configure")
	else:
		var snapshot := _snapshot(bridge.live_4d_snapshot_json())
		if _shape(snapshot) != [8, 16, 5, 8] or int(snapshot.get("w_slice_count", 0)) != 8 or snapshot.get("piece_set_id") != "embedded_3d":
			failures.append("native W=8 snapshot identity mismatch")
		bridge.live_4d_apply_command("move_w_pos")
		bridge.live_4d_reset()
		if _shape(_snapshot(bridge.live_4d_snapshot_json())) != [8, 16, 5, 8]:
			failures.append("native W=8 restart should preserve shape")
	var random_setup := _setup("live_2d", "standard", [6, 6], "classic", 1337, 3, "true_random")
	if not bridge.live_2d_configure(random_setup):
		failures.append("native true-random setup should configure through the Godot bridge")
	else:
		var first_random := _snapshot(bridge.live_2d_snapshot_json())
		var first_seed := int(first_random.get("effective_seed", -1))
		var first_hash := str(first_random.get("state_hash", ""))
		bridge.live_2d_apply_command("hard_drop")
		bridge.live_2d_reset()
		if str(_snapshot(bridge.live_2d_snapshot_json()).get("state_hash", "")) != first_hash:
			failures.append("Godot bridge restart should preserve true-random effective seed")
		if not bridge.live_2d_configure(random_setup):
			failures.append("explicit New Random construction should remain valid")
		elif int(_snapshot(bridge.live_2d_snapshot_json()).get("effective_seed", -1)) == first_seed:
			failures.append("explicit New Random construction should generate a different effective seed")
	return failures


func _setup(mode: String, preset_id: String, shape: Array, piece_set_id: String, seed: int, speed: int, random_mode: String = "fixed_seed") -> Dictionary:
	return {
		"schema_version": 2,
		"mode": mode,
		"board_preset_id": preset_id,
		"board_shape": shape,
		"piece_set_id": piece_set_id,
		"random_mode": random_mode,
		"seed": seed,
		"initial_speed_level": speed,
	}


func _snapshot(text: String) -> Dictionary:
	var parsed = JSON.parse_string(text)
	return parsed if parsed is Dictionary else {}


func _shape(snapshot: Dictionary) -> Array:
	var result := []
	for value in snapshot.get("board_shape", []):
		result.append(int(value))
	return result
