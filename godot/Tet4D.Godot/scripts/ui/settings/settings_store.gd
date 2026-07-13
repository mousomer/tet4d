extends RefCounted

class_name SettingsStore

const SCHEMA_VERSION := 1
const DEFAULT_PATH := "user://shell_settings.json"

var _registry
var _storage_path := DEFAULT_PATH
var _session_values: Dictionary = {}
var _persistent_values: Dictionary = {}
var _diagnostics: Array = []
var _load_state := "not_loaded"
var _save_count := 0


func _init(registry = null, storage_path: String = DEFAULT_PATH) -> void:
	_registry = registry
	_storage_path = storage_path
	if _registry != null:
		load_settings()


func load_settings() -> void:
	_diagnostics.clear()
	_persistent_values = _registry.persistent_default_values() if _registry != null else {}
	if _registry == null:
		_load_state = "registry_missing"
		_diagnostics.append("Settings registry unavailable; defaults used.")
		return
	if not FileAccess.file_exists(_storage_path):
		_load_state = "defaults_missing_file"
		_diagnostics.append("Settings file missing; defaults used.")
		return
	var file := FileAccess.open(_storage_path, FileAccess.READ)
	if file == null:
		_recover_all("Settings file could not be read; defaults used.")
		return
	var raw_text := file.get_as_text()
	var json := JSON.new()
	if json.parse(raw_text) != OK:
		_recover_all("Settings file is malformed; defaults used.")
		return
	var parsed = json.data
	if not (parsed is Dictionary):
		_recover_all("Settings root must be an object; defaults used.")
		return
	var schema_value = parsed.get("schema_version")
	if typeof(schema_value) not in [TYPE_INT, TYPE_FLOAT] or int(schema_value) != SCHEMA_VERSION:
		_recover_all("Settings schema version is unsupported; defaults used.")
		return
	if not parsed.has("settings") or not (parsed.get("settings") is Dictionary):
		_recover_all("Settings values must be an object; defaults used.")
		return
	var stored: Dictionary = parsed.get("settings")
	for setting_id in stored.keys():
		var spec = _registry.get_spec(str(setting_id))
		if spec == null or not spec.is_persistent():
			_diagnostics.append("Unknown or non-persistent setting %s ignored." % str(setting_id))
			continue
		var validated: Dictionary = spec.validated_value(stored.get(setting_id))
		if bool(validated.get("ok", false)):
			_persistent_values[spec.id()] = validated.get("value")
		else:
			_diagnostics.append("Invalid setting %s replaced by its default." % spec.id())
	_load_state = "loaded"
	_diagnostics.push_front("Shell settings loaded.")


func value(setting_id: String):
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	if spec == null:
		return null
	if spec.persistence() == "session" and _session_values.has(setting_id):
		return _session_values.get(setting_id)
	if spec.is_persistent() and _persistent_values.has(setting_id):
		return _persistent_values.get(setting_id)
	return spec.default_value()


func set_value(setting_id: String, new_value) -> bool:
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	if spec == null:
		_diagnostics.append("Unknown setting %s was not changed." % setting_id)
		return false
	var validated: Dictionary = spec.validated_value(new_value)
	if not bool(validated.get("ok", false)):
		_diagnostics.append("Invalid setting %s was not saved." % setting_id)
		return false
	var canonical_value = validated.get("value")
	if value(setting_id) == canonical_value:
		return false
	if spec.persistence() == "session":
		_session_values[setting_id] = canonical_value
		return true
	if spec.is_persistent():
		_persistent_values[setting_id] = canonical_value
		_save_persistent_values()
		return true
	return false


func reset_to_defaults() -> bool:
	if _registry == null:
		return false
	_session_values.clear()
	_persistent_values = _registry.persistent_default_values()
	var saved := _save_persistent_values()
	if saved:
		_diagnostics.append("Shell settings reset to defaults.")
	return saved


func all_values() -> Dictionary:
	var values: Dictionary = {}
	if _registry == null:
		return values
	for spec in _registry.settings:
		values[spec.id()] = value(spec.id())
	return values


func persistent_values() -> Dictionary:
	var values: Dictionary = {}
	if _registry == null:
		return values
	for spec in _registry.persistent_specs():
		values[spec.id()] = value(spec.id())
	return values


func diagnostics() -> Array:
	return _diagnostics.duplicate()


func status_text() -> String:
	return str(_diagnostics[-1]) if not _diagnostics.is_empty() else "Shell settings ready."


func deterministic_snapshot() -> Dictionary:
	return {
		"schema_version": SCHEMA_VERSION,
		"storage_path": _storage_path,
		"load_state": _load_state,
		"values": all_values(),
		"persistent_values": persistent_values(),
		"diagnostics": diagnostics(),
		"save_count": _save_count,
	}


func _recover_all(message: String) -> void:
	_persistent_values = _registry.persistent_default_values() if _registry != null else {}
	_load_state = "recovered_defaults"
	_diagnostics.append(message)


func _save_persistent_values() -> bool:
	var payload := {
		"schema_version": SCHEMA_VERSION,
		"settings": persistent_values(),
	}
	var temporary_path := "%s.tmp" % _storage_path
	var file := FileAccess.open(temporary_path, FileAccess.WRITE)
	if file == null:
		_report_save_failure("temporary file could not be opened")
		return false
	file.store_string(JSON.stringify(payload, "  ", true) + "\n")
	file.close()
	var temporary_absolute := ProjectSettings.globalize_path(temporary_path)
	var destination_absolute := ProjectSettings.globalize_path(_storage_path)
	var rename_error := DirAccess.rename_absolute(temporary_absolute, destination_absolute)
	if rename_error != OK:
		if FileAccess.file_exists(_storage_path):
			DirAccess.remove_absolute(destination_absolute)
			rename_error = DirAccess.rename_absolute(temporary_absolute, destination_absolute)
	if rename_error != OK:
		DirAccess.remove_absolute(temporary_absolute)
		_report_save_failure("atomic replacement failed with error %s" % rename_error)
		return false
	_save_count += 1
	_diagnostics.append("Shell settings saved automatically.")
	return true


func _report_save_failure(detail: String) -> void:
	var message := "Shell settings could not be saved: %s." % detail
	_diagnostics.append(message)
	push_error(message)
