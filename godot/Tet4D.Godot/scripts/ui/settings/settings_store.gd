extends RefCounted

class_name SettingsStore

const CONFIG_PATH := "user://tet4d_shell_settings.cfg"
const SECTION := "shell"

var _registry
var _session_values: Dictionary = {}
var _local_values: Dictionary = {}


func _init(registry = null) -> void:
	_registry = registry
	if _registry != null:
		_load_local_values()


func value(setting_id: String):
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	if spec == null:
		return null
	var persistence: String = spec.persistence()
	if persistence == "session" and _session_values.has(setting_id):
		return _session_values.get(setting_id)
	if persistence == "local_shell" and _local_values.has(setting_id):
		return _local_values.get(setting_id)
	return spec.default_value()


func set_value(setting_id: String, new_value) -> void:
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	if spec == null:
		return
	match spec.persistence():
		"session":
			_session_values[setting_id] = new_value
		"local_shell":
			_local_values[setting_id] = new_value
			_save_local_values()
		_:
			pass


func all_values() -> Dictionary:
	var values: Dictionary = {}
	if _registry == null:
		return values
	for spec in _registry.settings:
		values[spec.id()] = value(spec.id())
	return values


func _load_local_values() -> void:
	_local_values.clear()
	var config := ConfigFile.new()
	var error := config.load(CONFIG_PATH)
	if error != OK:
		return
	for spec in _registry.settings:
		if spec.persistence() == "local_shell" and config.has_section_key(SECTION, spec.id()):
			_local_values[spec.id()] = config.get_value(SECTION, spec.id(), spec.default_value())


func _save_local_values() -> void:
	var config := ConfigFile.new()
	for setting_id in _local_values.keys():
		config.set_value(SECTION, str(setting_id), _local_values.get(setting_id))
	var error := config.save(CONFIG_PATH)
	if error != OK:
		push_error("Failed to save shell settings to %s: %s" % [CONFIG_PATH, error])
