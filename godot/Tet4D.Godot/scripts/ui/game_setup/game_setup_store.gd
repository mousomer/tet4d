extends RefCounted

class_name GameSetupStore

const SCHEMA_VERSION := 3
const LEGACY_SCHEMA_VERSIONS := [1, 2]
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
	if json.parse(file.get_as_text()) != OK or not (json.data is Dictionary):
		return defaults
	var document := json.data as Dictionary
	var schema_version = _decoded_integer(document.get("schema_version", -1))
	if schema_version == null or not (document.get("last_selected") is Dictionary):
		return defaults
	if int(schema_version) != SCHEMA_VERSION and not LEGACY_SCHEMA_VERSIONS.has(int(schema_version)):
		return defaults
	var stored := document.get("last_selected") as Dictionary
	var result := {}
	for mode in GameSetupSpecScript.modes():
		result[mode] = _migrate_entry(mode, stored.get(mode, {}), int(schema_version))
	return result


# tet4d-semantic-boundary: allow adapter-routing
func save_last_validated(model, path: String = DEFAULT_PATH) -> bool:
	if model == null or not model.has_method("last_valid_entries"):
		return false
	var entries = model.last_valid_entries()
	if not (entries is Dictionary):
		return false
	return _write(entries as Dictionary, path)


func _write(entries: Dictionary, path: String) -> bool:
	for mode in GameSetupSpecScript.modes():
		if not _is_current_entry(entries.get(mode, {})):
			return false
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"schema_version": SCHEMA_VERSION, "last_selected": entries}, "  ", true) + "\n")
	return file.get_error() == OK


func _defaults() -> Dictionary:
	var result := {}
	for mode in GameSetupSpecScript.modes():
		result[mode] = _default_entry(mode)
	return result


func _default_entry(mode: String) -> Dictionary:
	var shape := GameSetupSpecScript.canonical_default_shape(mode)
	return {
		"board_preset_id": GameSetupSpecScript.preset_id_for_shape(mode, shape),
		"board_shape": shape,
		"piece_set_id": GameSetupSpecScript.default_piece_set_id(mode),
		"random_mode": GameSetupSpecScript.RANDOM_MODE_FIXED_SEED,
		"seed": GameSetupSpecScript.DEFAULT_SEED,
		"initial_speed_level": GameSetupSpecScript.MIN_SPEED_LEVEL,
	}


func _migrate_entry(mode: String, raw, schema_version: int) -> Dictionary:
	var result := _default_entry(mode)
	if schema_version == 1 and typeof(raw) == TYPE_STRING:
		raw = {"board_preset_id": raw}
	if not (raw is Dictionary):
		return result
	var entry := raw as Dictionary
	if schema_version == 3 and entry.has("board_shape"):
		result["board_shape"] = _decode_shape(entry.get("board_shape"))
	elif GameSetupSpecScript.is_supported(mode, str(entry.get("board_preset_id", ""))):
		result["board_shape"] = (GameSetupSpecScript.preset(mode, str(entry.get("board_preset_id", ""))).get("shape", []) as Array).duplicate()
	for key in ["piece_set_id", "random_mode", "seed", "initial_speed_level"]:
		if entry.has(key):
			result[key] = _decoded_integer(entry.get(key)) if key in ["seed", "initial_speed_level"] else entry.get(key)
	var shape = result.get("board_shape", [])
	result["board_preset_id"] = GameSetupSpecScript.preset_id_for_shape(mode, shape) if shape is Array else ""
	return result


func _is_current_entry(value) -> bool:
	if not (value is Dictionary):
		return false
	var entry := value as Dictionary
	if not (entry.get("board_shape") is Array):
		return false
	for extent in entry.get("board_shape", []):
		if typeof(extent) != TYPE_INT:
			return false
	return (
		typeof(entry.get("board_preset_id")) == TYPE_STRING
		and typeof(entry.get("piece_set_id")) == TYPE_STRING
		and typeof(entry.get("random_mode")) == TYPE_STRING
		and typeof(entry.get("seed")) == TYPE_INT
		and typeof(entry.get("initial_speed_level")) == TYPE_INT
	)


func _decode_shape(value):
	if not (value is Array):
		return value
	var result: Array = []
	for extent in value as Array:
		var decoded = _decoded_integer(extent)
		result.append(decoded if decoded != null else extent)
	return result


func _decoded_integer(value):
	if typeof(value) == TYPE_INT:
		return int(value)
	if typeof(value) == TYPE_FLOAT and is_finite(float(value)) and floor(float(value)) == float(value):
		return int(value)
	return null
