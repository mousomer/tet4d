extends RefCounted

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const GameSetupStoreScript = preload("res://scripts/ui/game_setup/game_setup_store.gd")


func run() -> Array:
	var failures := []
	var model = GameSetupModelScript.new()
	for mode in GameSetupSpecScript.modes():
		if not model.set_mode(mode):
			failures.append("supported mode should select: %s" % mode)
		if GameSetupSpecScript.presets_for_mode(mode).size() != 3:
			failures.append("%s should expose exactly three curated presets" % mode)
		if model.selected_preset_id() != "standard":
			failures.append("%s should default to standard" % mode)
		if model.selected_piece_set_id() != GameSetupSpecScript.default_piece_set_id(mode):
			failures.append("%s should use its canonical default piece-set ID" % mode)
		if model.selected_random_mode() != "fixed_seed" or model.selected_seed() != 1337:
			failures.append("%s deterministic defaults mismatch" % mode)
		if model.selected_speed_level() != 1:
			failures.append("%s speed default mismatch" % mode)
		if model.selected_shape().size() != int(mode.right(2).left(1)):
			failures.append("%s preset dimension count mismatch" % mode)
	model.set_mode(GameSetupSpecScript.MODE_4D)
	if not model.select_preset("wide_w") or model.selected_shape() != [8, 16, 5, 8]:
		failures.append("4D Wide W should resolve to 8 × 16 × 5 × 8")
	if model.select_preset("unknown"):
		failures.append("unknown preset should reject")
	model.apply_last_selected({GameSetupSpecScript.MODE_4D: {"board_preset_id": "unknown"}})
	if model.selected_preset_id() != "standard":
		failures.append("invalid persisted preset should fall back to standard")
	if not model.select_piece_set("embedded_3d"):
		failures.append("4D Embedded 3D should be supported")
	if model.select_piece_set("random_cells_4d"):
		failures.append("deferred random-cell piece set should reject")
	if not model.select_random_mode("true_random"):
		failures.append("true-random ID should select")
	if not model.select_seed(999999999) or model.select_seed(-1) or model.select_seed(1.5):
		failures.append("seed validation should accept only bounded integers")
	if not model.select_speed_level(10) or model.select_speed_level(11):
		failures.append("speed validation should enforce 1..10")
	var canonical: Dictionary = model.canonical_session_setup()
	for expected_key in ["schema_version", "mode", "board_preset_id", "board_shape", "piece_set_id", "random_mode", "seed", "initial_speed_level"]:
		if not canonical.has(expected_key):
			failures.append("canonical setup missing %s" % expected_key)
	for forbidden_key in ["piece_set_index", "random_mode_index", "preset_id"]:
		if canonical.has(forbidden_key):
			failures.append("canonical setup leaked legacy key %s" % forbidden_key)
	var path := "user://stage49_game_setup_test.json"
	var store = GameSetupStoreScript.new()
	var values := {
		GameSetupSpecScript.MODE_2D: {"board_preset_id": "large", "piece_set_id": "classic", "random_mode": "fixed_seed", "seed": 42, "initial_speed_level": 4},
		GameSetupSpecScript.MODE_4D: {"board_preset_id": "wide_w", "piece_set_id": "embedded_3d", "random_mode": "true_random", "seed": 77, "initial_speed_level": 8},
	}
	if not store.save_last_selected(values, path):
		failures.append("game setup store should save validated selections")
	var loaded: Dictionary = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_2D, {}).get("board_preset_id") != "large" or loaded.get(GameSetupSpecScript.MODE_4D, {}).get("piece_set_id") != "embedded_3d":
		failures.append("game setup store round trip mismatch")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"schema_version": 1, "last_selected": {"live_2d": "large", "live_3d": "unknown", "live_4d": "wide_w"}}))
		file.close()
	loaded = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_2D, {}).get("board_preset_id") != "large" or loaded.get(GameSetupSpecScript.MODE_3D, {}).get("board_preset_id") != "standard":
		failures.append("Stage 49 schema migration should preserve valid modes and isolate invalid modes")
	file = FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string("{malformed")
		file.close()
	if store.load_last_selected(path).get(GameSetupSpecScript.MODE_4D, {}).get("board_preset_id") != "standard":
		failures.append("malformed game setup should recover to standard")
	file = FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"schema_version": 3, "last_selected": values}))
		file.close()
	if store.load_last_selected(path).get(GameSetupSpecScript.MODE_2D, {}).get("board_preset_id") != "standard":
		failures.append("future game setup schema should recover safely")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	return failures
