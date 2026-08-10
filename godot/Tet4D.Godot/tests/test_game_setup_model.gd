extends RefCounted

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const GameSetupStoreScript = preload("res://scripts/ui/game_setup/game_setup_store.gd")
const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures: Array = []
	var model = GameSetupModelScript.new()
	for mode in GameSetupSpecScript.modes():
		if not model.set_mode(mode):
			failures.append("supported mode should select: %s" % mode)
		if model.selected_preset_id() != "standard":
			failures.append("%s should default to the generated standard dimensions" % mode)
		if model.selected_shape().size() != int(mode.right(2).left(1)):
			failures.append("%s should expose one active value per axis" % mode)
		if not model.is_current_valid():
			failures.append("%s canonical default should pass native admission" % mode)

	model.set_mode(GameSetupSpecScript.MODE_4D)
	if not model.select_preset("wide_w") or model.selected_shape() != [8, 16, 5, 8]:
		failures.append("4D Wide W should populate editable dimensions")
	if not model.adjust_axis(3, -1) or model.selected_shape() != [8, 16, 5, 7]:
		failures.append("axis increment/decrement should update the draft without a preset lookup")
	if not model.selected_preset_id().is_empty():
		failures.append("an edited preset shape must derive Custom/no-preset identity")
	model.select_preset("standard")
	if not model.set_axis_text(3, "1") or model.is_current_valid():
		failures.append("W=1 + standard_4d_5 must remain an invalid visible draft")
	elif str((model.validation_errors()[0] as Dictionary).get("code", "")) != "spawn_not_viable":
		failures.append("W=1 standard_4d_5 must fail via spawn viability")
	if model.last_valid_shape() != [5, 10, 4, 4]:
		failures.append("invalid drafts must not replace the last valid dimensions")
	if not model.select_piece_set("embedded_3d") or not model.is_current_valid():
		failures.append("W=1 + embedded_3d must validate through the native contract")
	if not model.select_piece_set("embedded_2d") or not model.is_current_valid():
		failures.append("W=1 + embedded_2d must validate through the native contract")
	if not model.select_piece_set("standard_4d_5") or model.is_current_valid():
		failures.append("piece-set changes must re-evaluate the same dimensional draft")
	model.select_piece_set("embedded_3d")
	model.set_axis_text(3, "1e0")
	if model.is_current_valid() or model.selected_axis_text(3) != "1e0":
		failures.append("non-integer axis text must remain visible and block launch without clamping")
	elif str((model.validation_errors()[0] as Dictionary).get("code", "")) != "invalid_field_type":
		failures.append("raw malformed axis text must route to strict native validation")
	model.set_axis_text(3, "1")
	if not model.is_current_valid():
		failures.append("valid axis text should restore the native-valid draft")
	model.reset_sizes()
	if model.selected_shape() != [5, 10, 4, 4] or model.selected_piece_set_id() != "embedded_3d":
		failures.append("Reset Sizes must leave non-size setup fields unchanged")
	model.reset_to_standard()
	if model.selected_piece_set_id() != "standard_4d_5" or model.selected_shape() != [5, 10, 4, 4]:
		failures.append("Reset Setup must restore all canonical setup fields")

	model.set_mode(GameSetupSpecScript.MODE_2D)
	model.select_preset("large")
	model.set_mode(GameSetupSpecScript.MODE_4D)
	if model.selected_shape() != [5, 10, 4, 4]:
		failures.append("each mode must retain an independent draft")
	model.set_axis_text(3, "1")
	model.select_piece_set("embedded_3d")
	var canonical: Dictionary = model.canonical_session_setup()
	if canonical.get("board_preset_id", "unexpected") != "" or canonical.get("board_shape", []) != [5, 10, 4, 1]:
		failures.append("custom session setup must carry the actual shape, not a synthetic preset")
	for expected_key in ["schema_version", "contract_version", "mode", "board_preset_id", "board_shape", "piece_set_id", "random_mode", "seed", "initial_speed_level", "topology_profile"]:
		if not canonical.has(expected_key):
			failures.append("canonical setup missing %s" % expected_key)
	if not model.select_control_frame("translation_frame", "absolute") or not model.select_control_frame("rotation_frame", "absolute"):
		failures.append("3D/4D control-frame selectors should accept absolute mode")
	if model.selected_control_frames() != {"translation_frame": "absolute", "rotation_frame": "absolute"}:
		failures.append("control-frame selectors should remain independent")
	if canonical.has("translation_frame") or canonical.has("rotation_frame"):
		failures.append("control-frame preferences must not enter deterministic native setup")
	if canonical.get("topology_profile", {}).get("dimensions", []) != [5, 10, 4, 1]:
		failures.append("custom setup topology must derive from the exact editable shape")
	var bridge = Tet4DCoreBridgeScript.new()
	if not bool(bridge.live_4d_configure_checked(canonical).get("ok", false)):
		failures.append("a native-valid custom W=1 Embedded 3D draft must construct a live session")
	var live_shape: Array = []
	var live_snapshot = JSON.parse_string(bridge.live_4d_snapshot_json())
	if live_snapshot is Dictionary:
		for value in (live_snapshot as Dictionary).get("board_shape", []):
			live_shape.append(int(value))
	if live_shape != [5, 10, 4, 1]:
		failures.append("live custom setup must retain its exact W=1 shape")

	var path := "user://stage54b_game_setup_test.json"
	var store = GameSetupStoreScript.new()
	if not store.save_last_validated(model, path):
		failures.append("only the model's native-validated last-valid snapshot should persist")
	var loaded: Dictionary = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_4D, {}).get("board_shape", []) != [5, 10, 4, 1] or loaded.get(GameSetupSpecScript.MODE_4D, {}).get("translation_frame", "") != "absolute":
		failures.append("schema 4 should persist the full custom shape and control-frame preference")
	var persisted_4d: Dictionary = loaded.get(GameSetupSpecScript.MODE_4D, {})
	for ephemeral_field in ["basis", "basis_state", "local_yaw", "local_pitch", "target_focus", "zoom_multiplier", "projection", "horizontal_reflection_active", "fit_reference"]:
		if persisted_4d.has(ephemeral_field):
			failures.append("game setup persistence must exclude Live-4D presentation field %s" % ephemeral_field)
	model.set_axis_text(3, "1e0")
	store.save_last_validated(model, path)
	loaded = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_4D, {}).get("board_shape", []) != [5, 10, 4, 1]:
		failures.append("an invalid draft must never replace the persisted last-valid setup")

	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"schema_version": 1, "last_selected": {"live_2d": "large", "live_3d": "unknown", "live_4d": "wide_w"}}))
		file.close()
	loaded = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_2D, {}).get("board_shape", []) != [10, 20] or loaded.get(GameSetupSpecScript.MODE_3D, {}).get("board_shape", []) != [6, 10, 6]:
		failures.append("schema 1 preset IDs must migrate to concrete shapes with safe defaults")
	if file != null:
		file = FileAccess.open(path, FileAccess.WRITE)
		file.store_string(JSON.stringify({"schema_version": 2, "last_selected": {"live_4d": {"board_preset_id": "wide_w", "piece_set_id": "embedded_3d", "random_mode": "fixed_seed", "seed": 77, "initial_speed_level": 8}}}))
		file.close()
	loaded = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_4D, {}).get("board_shape", []) != [8, 16, 5, 8]:
		failures.append("schema 2 preset entries must migrate to concrete shapes")
	if file != null:
		file = FileAccess.open(path, FileAccess.WRITE)
		file.store_string(JSON.stringify({"schema_version": 3, "last_selected": {"live_4d": {"board_shape": [5, 10, 4, 1], "piece_set_id": "standard_4d_5", "random_mode": "fixed_seed", "seed": 1337, "initial_speed_level": 1}}}))
		file.close()
	loaded = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_4D, {}).get("translation_frame", "") != "relative" or loaded.get(GameSetupSpecScript.MODE_4D, {}).get("rotation_frame", "") != "relative":
		failures.append("schema 3 setup persistence must migrate control frames to relative defaults")
	model.apply_last_selected(store.load_last_selected(path))
	if model.selected_shape(GameSetupSpecScript.MODE_4D) != [5, 10, 4, 4] or not model.is_valid(GameSetupSpecScript.MODE_4D):
		failures.append("stale invalid persisted tuples must recover through native validation to canonical defaults")
	if file != null:
		file = FileAccess.open(path, FileAccess.WRITE)
		file.store_string("{malformed")
		file.close()
	if store.load_last_selected(path).get(GameSetupSpecScript.MODE_4D, {}).get("board_shape", []) != [5, 10, 4, 4]:
		failures.append("malformed persistence should recover to canonical defaults")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	return failures
