extends RefCounted

class_name GameSetupStore

const SCHEMA_VERSION := 1
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
	if int(document.get("schema_version", -1)) != SCHEMA_VERSION or not (document.get("last_selected") is Dictionary):
		return defaults
	var result := defaults.duplicate()
	var stored := document.get("last_selected") as Dictionary
	for mode in GameSetupSpecScript.modes():
		var preset_id := str(stored.get(mode, GameSetupSpecScript.STANDARD_PRESET_ID))
		if GameSetupSpecScript.is_supported(mode, preset_id):
			result[mode] = preset_id
	return result


func save_last_selected(values: Dictionary, path: String = DEFAULT_PATH) -> bool:
	var validated := _defaults()
	for mode in GameSetupSpecScript.modes():
		var preset_id := str(values.get(mode, GameSetupSpecScript.STANDARD_PRESET_ID))
		if GameSetupSpecScript.is_supported(mode, preset_id):
			validated[mode] = preset_id
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"schema_version": SCHEMA_VERSION, "last_selected": validated}, "  ", true) + "\n")
	return file.get_error() == OK


func _defaults() -> Dictionary:
	var result := {}
	for mode in GameSetupSpecScript.modes():
		result[mode] = GameSetupSpecScript.STANDARD_PRESET_ID
	return result
