extends RefCounted

class_name SettingsStore

const PersistentFileReplacementScript = preload("res://scripts/persistence/persistent_file_replacement.gd")

const SCHEMA_VERSION := 3
const MIGRATABLE_SCHEMA_VERSIONS := [1, 2, SCHEMA_VERSION]
const DEFAULT_PATH := "user://shell_settings.json"
const LEGACY_HINT_SETTING_ID := "controls_help.show_keyboard_hints"
const HINT_SETTING_ID := "accessibility.show_help_hints"

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
	var schema_version := int(schema_value)
	if schema_version < SCHEMA_VERSION and stored.has(LEGACY_HINT_SETTING_ID):
		var hint_spec = _registry.get_spec(HINT_SETTING_ID)
		var hint_value: Dictionary = hint_spec.validated_value(stored.get(LEGACY_HINT_SETTING_ID)) if hint_spec != null else {}
		if bool(hint_value.get("ok", false)):
			_persistent_values[HINT_SETTING_ID] = hint_value.get("value")
		else:
			_diagnostics.append("Invalid legacy keyboard-hint setting replaced by its accessibility default.")
	for setting_id in stored.keys():
		if str(setting_id) == LEGACY_HINT_SETTING_ID and schema_version < SCHEMA_VERSION:
			continue
		var spec = _registry.get_spec(str(setting_id))
		if spec == null or not spec.is_persistent():
			_diagnostics.append("Unknown or non-persistent setting %s ignored." % str(setting_id))
			continue
		var validated: Dictionary = spec.validated_value(stored.get(setting_id))
		if bool(validated.get("ok", false)):
			_persistent_values[spec.id()] = validated.get("value")
		else:
			_diagnostics.append("Invalid setting %s replaced by its default." % spec.id())
	_load_state = "loaded" if schema_version == SCHEMA_VERSION else "migrated_v%s" % schema_version
	_diagnostics.push_front("Shell settings loaded." if schema_version == SCHEMA_VERSION else "Shell settings schema %s migrated to schema 3 in memory." % schema_version)


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


func reset_categories_to_defaults(category_ids: Array, reset_label: String = "Settings") -> bool:
	if _registry == null:
		return false
	for category_id in category_ids:
		for spec in _registry.settings_for_category(str(category_id)):
			if spec.persistence() == "session":
				_session_values.erase(spec.id())
			elif spec.is_persistent():
				_persistent_values[spec.id()] = _safe_copy(spec.default_value())
	var saved := _save_persistent_values()
	if saved:
		_diagnostics.append("%s reset to defaults." % reset_label)
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
	var replacement: Dictionary = PersistentFileReplacementScript.write_text(
		_storage_path,
		JSON.stringify(payload, "  ", true) + "\n",
		true,
		_replacement_ops
	)
	if not bool(replacement.get("ok", false)):
		_report_save_failure(str(replacement.get("detail", "replacement failed")))
		return false
	_save_count += 1
	_diagnostics.append("Shell settings saved automatically.")
	var warning := str(replacement.get("warning", ""))
	if not warning.is_empty():
		_diagnostics.append("Shell settings saved, but %s." % warning)
	return true


func _report_save_failure(detail: String) -> void:
	var message := "Shell settings could not be saved: %s." % detail
	_diagnostics.append(message)
	push_error(message)


func _safe_copy(value):
	return value.duplicate(true) if value is Array or value is Dictionary else value
