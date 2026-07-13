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
		if model.selected_shape().size() != int(mode.right(2).left(1)):
			failures.append("%s preset dimension count mismatch" % mode)
	model.set_mode(GameSetupSpecScript.MODE_4D)
	if not model.select_preset("wide_w") or model.selected_shape() != [8, 16, 5, 8]:
		failures.append("4D Wide W should resolve to 8 × 16 × 5 × 8")
	if model.select_preset("unknown"):
		failures.append("unknown preset should reject")
	model.apply_last_selected({GameSetupSpecScript.MODE_4D: "unknown"})
	if model.selected_preset_id() != "standard":
		failures.append("invalid persisted preset should fall back to standard")
	var path := "user://stage49_game_setup_test.json"
	var store = GameSetupStoreScript.new()
	if not store.save_last_selected({GameSetupSpecScript.MODE_2D: "large", GameSetupSpecScript.MODE_4D: "wide_w"}, path):
		failures.append("game setup store should save validated selections")
	var loaded: Dictionary = store.load_last_selected(path)
	if loaded.get(GameSetupSpecScript.MODE_2D) != "large" or loaded.get(GameSetupSpecScript.MODE_4D) != "wide_w":
		failures.append("game setup store round trip mismatch")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string("{malformed")
	if store.load_last_selected(path).get(GameSetupSpecScript.MODE_4D) != "standard":
		failures.append("malformed game setup should recover to standard")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	return failures
