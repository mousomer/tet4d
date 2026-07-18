extends RefCounted

class_name GameSetupStore

const SCHEMA_VERSION := 2
const LEGACY_SCHEMA_VERSION := 1
const DEFAULT_PATH := "user://game_setup.json"
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")


func load_last_selected(path: String = DEFAULT_PATH) -> Dictionary:
	var defaults := _defaults()
	if not FileAccess.file_exists(path):
		return defaults
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return defaults
	var json := JSON.new()
	if json.parse(file.get_as_text()) != OK:
		return defaults
	var parsed = json.data
	if not (parsed is Dictionary):
		return defaults
	var document := parsed as Dictionary
	var schema_version = document.get("schema_version", -1)
	if not GameSetupSpecScript.is_valid_speed(schema_version) or not (document.get("last_selected") is Dictionary):
		return defaults
	if int(schema_version) != SCHEMA_VERSION and int(schema_version) != LEGACY_SCHEMA_VERSION:
		return defaults
	var result := defaults.duplicate()
	var stored := document.get("last_selected") as Dictionary
	for mode in GameSetupSpecScript.modes():
		var raw = stored.get(mode, {})
		if int(schema_version) == LEGACY_SCHEMA_VERSION and typeof(raw) == TYPE_STRING:
			raw = {"board_preset_id": str(raw)}
		result[mode] = _validated_entry(mode, raw if raw is Dictionary else {})
	return result


func save_last_selected(values: Dictionary, path: String = DEFAULT_PATH) -> bool:
	var validated := _defaults()
	for mode in GameSetupSpecScript.modes():
		var raw = values.get(mode, {})
		if typeof(raw) == TYPE_STRING:
			raw = {"board_preset_id": str(raw)}
		validated[mode] = _validated_entry(mode, raw if raw is Dictionary else {})
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"schema_version": SCHEMA_VERSION, "last_selected": validated}, "  ", true) + "\n")
	return file.get_error() == OK


func _defaults() -> Dictionary:
	var result := {}
	for mode in GameSetupSpecScript.modes():
		result[mode] = _validated_entry(mode, {})
	return result


func _validated_entry(mode: String, raw: Dictionary) -> Dictionary:
	var result := {
		"board_preset_id": GameSetupSpecScript.STANDARD_PRESET_ID,
		"piece_set_id": GameSetupSpecScript.default_piece_set_id(mode),
		"random_mode": GameSetupSpecScript.RANDOM_MODE_FIXED_SEED,
		"seed": GameSetupSpecScript.DEFAULT_SEED,
		"initial_speed_level": GameSetupSpecScript.MIN_SPEED_LEVEL,
	}
	var preset_id = raw.get("board_preset_id", result["board_preset_id"])
	if typeof(preset_id) == TYPE_STRING and GameSetupSpecScript.is_supported(mode, str(preset_id)):
		result["board_preset_id"] = str(preset_id)
	var piece_set_id = raw.get("piece_set_id", result["piece_set_id"])
	if typeof(piece_set_id) == TYPE_STRING and GameSetupSpecScript.is_piece_set_supported(mode, str(result["board_preset_id"]), str(piece_set_id)):
		result["piece_set_id"] = str(piece_set_id)
	var random_mode = raw.get("random_mode", result["random_mode"])
	if typeof(random_mode) == TYPE_STRING and GameSetupSpecScript.is_random_mode_supported(str(random_mode)):
		result["random_mode"] = str(random_mode)
	var seed = raw.get("seed", result["seed"])
	if GameSetupSpecScript.is_valid_seed(seed):
		result["seed"] = int(seed)
	var speed = raw.get("initial_speed_level", result["initial_speed_level"])
	if GameSetupSpecScript.is_valid_speed(speed):
		result["initial_speed_level"] = int(speed)
	return result
