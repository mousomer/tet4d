extends RefCounted

class_name PresentationProfile

const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const SCRIPT_PATH := "res://scripts/presentation/presentation_profile.gd"
const SCHEMA_VERSION := 1
# Independent working selections outside built-in appearance ownership.
# Complete design restoration still replaces all of these values.
const STYLE_INDEPENDENT_IDS := [
	"display.grid_mode", "display.window_mode", "display.windowed_size",
	"display.ui_scale", "replay.playback_speed", "replay.loop_enabled",
	"display.projection_strength", "accessibility.show_help_hints",
	"camera.sensitivity", "camera.invert_y", "diagnostics.show_layout_bounds",
	"interface.show_onboarding",
]

var _registry
var _values: Dictionary = {}
var _failures: Array = []
var _design_state: Dictionary = {}


static func canonical_defaults():
	var registry = SettingsRegistryScript.new()
	registry.load_from_path(SettingsRegistryScript.REGISTRY_PATH)
	var profile = _new_profile()
	profile.configure(registry, registry.default_values())
	return profile


static func from_store(registry, store):
	var profile = _new_profile()
	profile.configure(registry, store.all_values() if store != null else {})
	return profile


static func from_snapshot(registry, snapshot: Dictionary):
	var profile = _new_profile()
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
	profile._read_design_state(snapshot.get("design_state", {}))
	return profile


func configure(registry, source_values: Dictionary) -> Array:
	# Compatibility for named profiles exported before tri-state grid display.
	source_values = source_values.duplicate(true)
	if source_values.has("display.grid_visible") and typeof(source_values["display.grid_visible"]) == TYPE_BOOL:
		if not source_values.has("display.grid_mode"):
			source_values["display.grid_mode"] = "full" if source_values["display.grid_visible"] == true else "none"
		source_values.erase("display.grid_visible")
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
	var result := {"schema_version": SCHEMA_VERSION, "values": values()}
	if not _design_state.is_empty():
		result["design_state"] = design_state()
	return result


func design_state() -> Dictionary:
	return _design_state.duplicate(true)


func with_design_state(metadata: Dictionary):
	var profile = detached_copy()
	profile._read_design_state(metadata)
	return profile


func _read_design_state(metadata) -> void:
	_design_state = {}
	if not (metadata is Dictionary):
		_failures.append("design_state must be an object")
		return
	var rects = metadata.get("panel_rects", {})
	if not (rects is Dictionary):
		_failures.append("panel_rects must be an object")
		return
	for key in rects:
		var rect = rects[key]
		if not ["GameArea", "PieceControls", "ViewControls", "PieceState"].has(str(key)) or not (rect is Array) or rect.size() != 4:
			_failures.append("invalid design panel rectangle")
			return
		for value in rect:
			if not typeof(value) in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(value)):
				_failures.append("invalid design panel coordinate")
				return
		if float(rect[2]) <= 0 or float(rect[3]) <= 0:
			_failures.append("design panel size must be positive")
			return
	var base = metadata.get("base_style_values", {})
	if not (base is Dictionary):
		_failures.append("base style values must be an object")
		return
	var normalized_base: Dictionary = {}
	if not base.is_empty():
		var validated = _new_profile()
		validated.configure(_registry, base)
		if not validated.contract_conforms():
			_failures.append("invalid base style values")
			return
		normalized_base = validated.values()
	for key in metadata:
		if not ["panel_rects", "base_style_id", "base_style_name", "base_style_values"].has(key):
			_failures.append("unknown design state property")
			return
	for key in ["base_style_id", "base_style_name"]:
		if metadata.has(key) and not metadata[key] is String:
			_failures.append("base style identity must be text")
			return
	_design_state = metadata.duplicate(true)
	if metadata.has("base_style_values"):
		_design_state["base_style_values"] = normalized_base
	for key in rects:
		var rect: Array = rects[key]
		_design_state["panel_rects"][key] = [float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])]


func with_overrides(overrides: Dictionary):
	var next_values := values()
	for setting_id in overrides.keys():
		next_values[str(setting_id)] = _safe_copy(overrides.get(setting_id))
	var profile = _new_profile()
	profile.configure(_registry, next_values)
	profile._design_state = design_state()
	return profile


# Named style composition: appearance comes from
# `style_profile`, style-independent selections stay with this profile.
func with_style_of(style_profile):
	var preserved: Dictionary = {}
	for setting_id in STYLE_INDEPENDENT_IDS:
		preserved[setting_id] = value(setting_id)
	var composed = style_profile.with_overrides(preserved)
	composed._design_state = design_state()
	return composed


func detached_copy():
	var profile = _new_profile()
	profile.configure(_registry, _values)
	profile._design_state = design_state()
	return profile


static func _new_profile():
	# The project-global class cache is generated, ignored editor state. Direct
	# exact-checkout scripts must be able to construct this type before import.
	return load(SCRIPT_PATH).new()


static func _safe_copy(value):
	return value.duplicate(true) if value is Array or value is Dictionary else value
