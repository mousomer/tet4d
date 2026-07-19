extends RefCounted

class_name SettingsStore

const SCHEMA_VERSION := 2
const MIGRATABLE_SCHEMA_VERSIONS := [1, SCHEMA_VERSION]
const DEFAULT_PATH := "user://shell_settings.json"
const BACKUP_SUFFIX := ".bak"

var _registry
var _storage_path := DEFAULT_PATH
var _replacement_ops
var _session_values: Dictionary = {}
var _persistent_values: Dictionary = {}
var _diagnostics: Array = []
var _load_state := "not_loaded"
var _save_count := 0


func _init(registry = null, storage_path: String = DEFAULT_PATH, replacement_ops = null) -> void:
	_registry = registry
	_storage_path = storage_path
	_replacement_ops = replacement_ops
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
	if not _is_supported_schema_version(schema_value):
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
	_load_state = "migrated_v1" if int(schema_value) == 1 else "loaded"
	_diagnostics.push_front("Stage 48 shell settings migrated in memory." if int(schema_value) == 1 else "Shell settings loaded.")


func value(setting_id: String):
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	if spec == null:
		return null
	if spec.persistence() == "session" and _session_values.has(setting_id):
		return _safe_copy(_session_values.get(setting_id))
	if spec.is_persistent() and _persistent_values.has(setting_id):
		return _safe_copy(_persistent_values.get(setting_id))
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
	var canonical_value = _safe_copy(validated.get("value"))
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


func _is_supported_schema_version(value) -> bool:
	if typeof(value) not in [TYPE_INT, TYPE_FLOAT]:
		return false
	var integer_value := int(value)
	return float(value) == float(integer_value) and MIGRATABLE_SCHEMA_VERSIONS.has(integer_value)


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
	var replacement := _replace_temporary_file(temporary_absolute, destination_absolute)
	if not bool(replacement.get("ok", false)):
		_report_save_failure(str(replacement.get("detail", "replacement failed")))
		return false
	_save_count += 1
	_diagnostics.append("Shell settings saved automatically.")
	var warning := str(replacement.get("warning", ""))
	if not warning.is_empty():
		_diagnostics.append(warning)
	return true


func _replace_temporary_file(temporary_path: String, destination_path: String) -> Dictionary:
	var backup_path := "%s%s" % [destination_path, BACKUP_SUFFIX]
	var replace_error := _rename_absolute(temporary_path, destination_path)
	if replace_error == OK:
		var stale_cleanup := _remove_if_present(backup_path)
		return {
			"ok": true,
			"warning": _cleanup_warning("stale backup", stale_cleanup),
		}
	if not _file_exists(destination_path):
		var temporary_cleanup := _remove_if_present(temporary_path)
		return {
			"ok": false,
			"detail": "replacement failed with error %s before an existing settings file was modified%s" % [
				replace_error,
				_cleanup_detail(temporary_cleanup),
			],
		}
	var stale_backup_cleanup := _remove_if_present(backup_path)
	if stale_backup_cleanup != OK:
		_remove_if_present(temporary_path)
		return {
			"ok": false,
			"detail": "stale backup cleanup failed with error %s; previous settings were not modified" % stale_backup_cleanup,
		}
	var backup_error := _rename_absolute(destination_path, backup_path)
	if backup_error != OK:
		var temporary_cleanup := _remove_if_present(temporary_path)
		return {
			"ok": false,
			"detail": "previous settings could not be backed up (error %s) and were not modified%s" % [
				backup_error,
				_cleanup_detail(temporary_cleanup),
			],
		}
	var install_error := _rename_absolute(temporary_path, destination_path)
	if install_error == OK:
		var backup_cleanup := _remove_if_present(backup_path)
		return {
			"ok": true,
			"warning": _cleanup_warning("backup", backup_cleanup),
		}
	var restore_error := _rename_absolute(backup_path, destination_path)
	if restore_error != OK:
		restore_error = _copy_absolute(backup_path, destination_path)
	var temporary_cleanup := _remove_if_present(temporary_path)
	if restore_error != OK:
		return {
			"ok": false,
			"detail": "installation failed with error %s; previous settings remain at %s because restoration failed with error %s%s" % [
				install_error,
				backup_path,
				restore_error,
				_cleanup_detail(temporary_cleanup),
			],
		}
	var backup_cleanup := _remove_if_present(backup_path)
	return {
		"ok": false,
		"detail": "installation failed with error %s; previous settings were restored%s%s" % [
			install_error,
			_cleanup_detail(temporary_cleanup),
			_cleanup_detail(backup_cleanup, "backup"),
		],
	}


func _file_exists(path: String) -> bool:
	if _replacement_ops != null:
		return bool(_replacement_ops.file_exists(path))
	return FileAccess.file_exists(path)


func _rename_absolute(from_path: String, to_path: String) -> Error:
	if _replacement_ops != null:
		return _replacement_ops.rename_absolute(from_path, to_path)
	return DirAccess.rename_absolute(from_path, to_path)


func _copy_absolute(from_path: String, to_path: String) -> Error:
	if _replacement_ops != null:
		return _replacement_ops.copy_absolute(from_path, to_path)
	return DirAccess.copy_absolute(from_path, to_path)


func _remove_absolute(path: String) -> Error:
	if _replacement_ops != null:
		return _replacement_ops.remove_absolute(path)
	return DirAccess.remove_absolute(path)


func _remove_if_present(path: String) -> Error:
	return _remove_absolute(path) if _file_exists(path) else OK


func _cleanup_detail(error: Error, label: String = "temporary file") -> String:
	return "" if error == OK else "; %s cleanup also failed with error %s" % [label, error]


func _cleanup_warning(label: String, error: Error) -> String:
	return "" if error == OK else "Shell settings saved, but %s cleanup failed with error %s." % [label, error]


func _report_save_failure(detail: String) -> void:
	var message := "Shell settings could not be saved: %s." % detail
	_diagnostics.append(message)
	push_error(message)


func _safe_copy(value):
	return value.duplicate(true) if value is Array or value is Dictionary else value
