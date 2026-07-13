extends RefCounted

class_name SettingsRegistry

const SettingSpecScript = preload("res://scripts/ui/settings/setting_spec.gd")
const REGISTRY_PATH := "res://config/shell_settings_registry.json"

var categories: Array = []
var settings: Array = []
var _settings_by_id: Dictionary = {}
var schema_version := 0

func load_from_path(path: String) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Failed to open settings registry at %s" % path)
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary):
		push_error("Settings registry at %s must be a JSON object" % path)
		return
	load_from_data(parsed)


func load_from_data(data: Dictionary) -> void:
	schema_version = int(data.get("schema_version", 0))
	categories = data.get("categories", []).duplicate(true)
	settings = []
	_settings_by_id.clear()
	for spec_data in data.get("settings", []):
		if spec_data is Dictionary:
			var spec := SettingSpecScript.new(spec_data)
			settings.append(spec)
			_settings_by_id[spec.id()] = spec


func validate() -> Array: # tet4d-semantic-boundary: allow diagnostic-presentation
	var failures: Array = []
	if schema_version != 1:
		failures.append("settings registry schema_version must be 1")
	var category_ids: Array = []
	for category_data in categories:
		if not (category_data is Dictionary):
			failures.append("category entries must be objects")
			continue
		var category_id := str(category_data.get("id", ""))
		if category_id.is_empty():
			failures.append("category id is required")
			continue
		if category_ids.has(category_id):
			failures.append("duplicate category id %s" % category_id)
		category_ids.append(category_id)
		if not SettingSpecScript.ALLOWED_CATEGORIES.has(category_id):
			failures.append("unknown Stage 29 category %s" % category_id)
		for token in SettingSpecScript.FORBIDDEN_CATEGORY_TOKENS:
			if category_id.find(token) >= 0:
				failures.append("forbidden semantic token %s in category %s" % [token, category_id])
	var setting_ids: Array = []
	for spec in settings:
		var setting_id: String = spec.id()
		if setting_ids.has(setting_id):
			failures.append("duplicate setting id %s" % setting_id)
		setting_ids.append(setting_id)
		failures.append_array(SettingSpecScript.validate(spec.data, category_ids))
	return failures


func settings_for_category(category_id: String) -> Array:
	var result: Array = []
	for spec in settings:
		if spec.category() == category_id:
			result.append(spec)
	return result


func category_label(category_id: String) -> String:
	for category_data in categories:
		if category_data is Dictionary and str(category_data.get("id", "")) == category_id:
			return str(category_data.get("label", category_id))
	return category_id


func get_spec(setting_id: String):
	return _settings_by_id.get(setting_id)


func default_values() -> Dictionary:
	var values: Dictionary = {}
	for spec in settings:
		values[spec.id()] = spec.default_value()
	return values


func persistent_specs() -> Array:
	var result: Array = []
	for spec in settings:
		if spec.is_persistent():
			result.append(spec)
	return result


func persistent_default_values() -> Dictionary:
	var values: Dictionary = {}
	for spec in persistent_specs():
		values[spec.id()] = spec.default_value()
	return values
