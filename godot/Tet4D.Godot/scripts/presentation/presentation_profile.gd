extends RefCounted

class_name PresentationProfile

const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const SCHEMA_VERSION := 1

var _registry
var _values: Dictionary = {}
var _failures: Array = []


static func canonical_defaults():
	var registry = SettingsRegistryScript.new()
	registry.load_from_path(SettingsRegistryScript.REGISTRY_PATH)
	var profile = PresentationProfile.new()
	profile.configure(registry, registry.default_values())
	return profile


static func from_store(registry, store):
	var profile = PresentationProfile.new()
	profile.configure(registry, store.all_values() if store != null else {})
	return profile


static func from_snapshot(registry, snapshot: Dictionary):
	var profile = PresentationProfile.new()
	if int(snapshot.get("schema_version", 0)) != SCHEMA_VERSION:
		profile._registry = registry
		profile._failures.append("presentation profile schema_version must be %d" % SCHEMA_VERSION)
		return profile
	var source_values = snapshot.get("values", {})
	if not (source_values is Dictionary):
		profile._registry = registry
		profile._failures.append("presentation profile values must be an object")
		return profile
	profile.configure(registry, source_values)
	return profile


func configure(registry, source_values: Dictionary) -> Array:
	_registry = registry
	_values.clear()
	_failures.clear()
	if _registry == null:
		_failures.append("presentation profile registry is required")
		return failures()
	for setting_id in source_values.keys():
		if _registry.get_spec(str(setting_id)) == null:
			_failures.append("unknown presentation parameter %s" % str(setting_id))
	for spec in _registry.settings:
		var setting_id: String = spec.id()
		var candidate = source_values.get(setting_id, spec.default_value())
		var validated: Dictionary = spec.validated_value(candidate)
		if bool(validated.get("ok", false)):
			_values[setting_id] = _safe_copy(validated.get("value"))
		else:
			_values[setting_id] = _safe_copy(spec.default_value())
			_failures.append("invalid presentation parameter %s" % setting_id)
	return failures()


func contract_conforms() -> bool:
	return _registry != null and _failures.is_empty()


func failures() -> Array:
	return _failures.duplicate()


func value(setting_id: String):
	return _safe_copy(_values.get(setting_id))


func values() -> Dictionary:
	return _values.duplicate(true)


func semantic_owner(setting_id: String) -> String:
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	return spec.semantic_owner() if spec != null else ""


func values_for_owner(owner: String) -> Dictionary:
	var result: Dictionary = {}
	if _registry == null:
		return result
	for spec in _registry.settings_for_semantic_owner(owner):
		result[spec.id()] = value(spec.id())
	return result


func applies_at_runtime(setting_id: String, runtime_context: String) -> bool:
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	return spec != null and spec.applies_at_runtime(runtime_context)


func minimum(setting_id: String, fallback: float = 0.0) -> float:
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	return float(spec.data.get("min", fallback)) if spec != null else fallback


func maximum(setting_id: String, fallback: float = 1.0) -> float:
	var spec = _registry.get_spec(setting_id) if _registry != null else null
	return float(spec.data.get("max", fallback)) if spec != null else fallback


func snapshot() -> Dictionary:
	return {
		"schema_version": SCHEMA_VERSION,
		"values": values(),
	}


func with_overrides(overrides: Dictionary):
	var next_values := values()
	for setting_id in overrides.keys():
		next_values[str(setting_id)] = _safe_copy(overrides.get(setting_id))
	var profile = PresentationProfile.new()
	profile.configure(_registry, next_values)
	return profile


func detached_copy():
	var profile = PresentationProfile.new()
	profile.configure(_registry, _values)
	return profile


static func _safe_copy(value):
	return value.duplicate(true) if value is Array or value is Dictionary else value
