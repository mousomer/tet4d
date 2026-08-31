extends RefCounted

class_name BuiltInStyleCatalog

# Read-only catalog of shipped presentation styles.
#
# It is deliberately a parallel source to the mutable `PresentationProfileLibrary`
# rather than a second library: entries are repository data, never live under
# `user://`, and the owner exposes no save, rename, delete, or overwrite API.
# Style values reuse the one authoritative `PresentationProfile` payload and the
# one settings registry; this owner adds only shipped catalog identity and
# descriptive metadata.

const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")

const CATALOG_TYPE := "tet4d.built_in_style_catalog"
const CATALOG_SCHEMA_VERSION := 1
const CATALOG_PATH := "res://config/built_in_style_catalog.json"
const MAX_STYLE_ID_LENGTH := 48
const MAX_DISPLAY_NAME_LENGTH := 80
const STYLE_CATEGORIES := [
	"baseline",
	"heritage",
	"vivid",
	"animated",
	"technical",
	"accessibility",
]

var _registry
var _catalog_path := CATALOG_PATH
var _entries: Array = []
var _entries_by_id: Dictionary = {}
var _diagnostics: Array = []
var _loaded := false


func _init(registry = null, catalog_path: String = CATALOG_PATH) -> void:
	_registry = registry
	_catalog_path = catalog_path


func list_styles() -> Array:
	_ensure_loaded()
	var records: Array = []
	for entry in _entries:
		records.append(_record_for_entry(entry))
	return records


func has_style(style_id: String) -> bool:
	_ensure_loaded()
	return _entries_by_id.has(style_id)


func style_profile(style_id: String) -> Dictionary:
	_ensure_loaded()
	if not _entries_by_id.has(style_id):
		return _failure("Unknown built-in style.")
	var entry: Dictionary = _entries_by_id.get(style_id)
	# Rebuilt per call so a caller can never reach the shipped source object.
	var profile = PresentationProfileScript.from_snapshot(_registry, {
		"schema_version": PresentationProfileScript.SCHEMA_VERSION,
		"values": entry.get("values", {}).duplicate(true),
	})
	if profile == null or not profile.contract_conforms():
		return _failure("Built-in style values failed authoritative validation.")
	return _success({
		"record": _record_for_entry(entry),
		"profile": profile.detached_copy(),
	})


func diagnostics() -> Array:
	_ensure_loaded()
	return _diagnostics.duplicate()


func animated_style_ids() -> Array:
	_ensure_loaded()
	var ids: Array = []
	for entry in _entries:
		if bool(entry.get("animated", false)):
			ids.append(str(entry.get("style_id", "")))
	return ids


func deterministic_snapshot() -> Dictionary:
	return {
		"catalog_type": CATALOG_TYPE,
		"catalog_schema_version": CATALOG_SCHEMA_VERSION,
		"catalog_path": _catalog_path,
		"read_only": true,
		"styles": list_styles(),
		"diagnostics": diagnostics(),
	}


func _ensure_loaded() -> void:
	if _loaded:
		return
	_loaded = true
	_entries = []
	_entries_by_id = {}
	_diagnostics = []
	if not FileAccess.file_exists(_catalog_path):
		_diagnostics.append("Built-in style catalog is missing: %s" % _catalog_path)
		return
	var file := FileAccess.open(_catalog_path, FileAccess.READ)
	if file == null:
		_diagnostics.append("Built-in style catalog could not be read.")
		return
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK or not (parser.data is Dictionary):
		_diagnostics.append("Built-in style catalog JSON is malformed.")
		return
	var document: Dictionary = parser.data
	if str(document.get("catalog_type", "")) != CATALOG_TYPE:
		_diagnostics.append("Built-in style catalog type is unsupported.")
		return
	if int(document.get("catalog_schema_version", 0)) != CATALOG_SCHEMA_VERSION:
		_diagnostics.append("Built-in style catalog uses an unsupported schema version.")
		return
	var declared = document.get("styles", [])
	if not (declared is Array):
		_diagnostics.append("Built-in style catalog styles must be an array.")
		return
	for raw_entry in declared:
		var checked := _validated_entry(raw_entry)
		if bool(checked.get("ok", false)):
			var entry: Dictionary = checked.get("entry", {})
			var style_id := str(entry.get("style_id", ""))
			if _entries_by_id.has(style_id):
				_diagnostics.append("Ignored duplicate built-in style id %s." % style_id)
				continue
			_entries.append(entry)
			_entries_by_id[style_id] = entry
		else:
			_diagnostics.append(str(checked.get("error", "Ignored an invalid built-in style.")))
	_entries.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		var left_order := int(left.get("ordering", 0))
		var right_order := int(right.get("ordering", 0))
		return left_order < right_order if left_order != right_order else str(left.get("style_id", "")) < str(right.get("style_id", ""))
	)


func _validated_entry(raw_entry) -> Dictionary: # tet4d-semantic-boundary: allow diagnostic-presentation
	if not (raw_entry is Dictionary):
		return _failure("Built-in style entries must be objects.")
	var entry: Dictionary = raw_entry
	var style_id := str(entry.get("style_id", ""))
	if not _safe_style_id(style_id):
		return _failure("Built-in style identity is invalid or unsafe.")
	var display_name := str(entry.get("display_name", "")).strip_edges()
	if display_name.is_empty() or display_name.length() > MAX_DISPLAY_NAME_LENGTH:
		return _failure("Built-in style %s has an unusable display name." % style_id)
	var category := str(entry.get("category", ""))
	if not STYLE_CATEGORIES.has(category):
		return _failure("Built-in style %s declares unknown category %s." % [style_id, category])
	var snapshot = entry.get("presentation_profile")
	if not (snapshot is Dictionary):
		return _failure("Built-in style %s must embed a presentation_profile object." % style_id)
	if int(snapshot.get("schema_version", 0)) != PresentationProfileScript.SCHEMA_VERSION:
		return _failure("Built-in style %s uses an unsupported presentation-profile schema." % style_id)
	var values = snapshot.get("values", {})
	if not (values is Dictionary):
		return _failure("Built-in style %s presentation_profile values must be an object." % style_id)
	var profile = PresentationProfileScript.from_snapshot(_registry, {
		"schema_version": PresentationProfileScript.SCHEMA_VERSION,
		"values": values.duplicate(true),
	})
	if profile == null or not profile.contract_conforms():
		var detail := "; ".join(profile.failures()) if profile != null and profile.has_method("failures") else "invalid profile"
		return _failure("Built-in style %s failed authoritative validation: %s." % [style_id, detail])
	return _success({"entry": {
		"style_id": style_id,
		"display_name": display_name,
		"short_description": str(entry.get("short_description", "")),
		"category": category,
		"ordering": int(entry.get("ordering", 0)),
		"animated": bool(entry.get("animated", false)),
		"accent_summary": str(entry.get("accent_summary", "")),
		"recommended_modes": _string_array(entry.get("recommended_modes", [])),
		"values": values.duplicate(true),
	}})


func _record_for_entry(entry: Dictionary) -> Dictionary:
	return {
		"style_id": str(entry.get("style_id", "")),
		"display_name": str(entry.get("display_name", "")),
		"short_description": str(entry.get("short_description", "")),
		"category": str(entry.get("category", "")),
		"ordering": int(entry.get("ordering", 0)),
		"animated": bool(entry.get("animated", false)),
		"accent_summary": str(entry.get("accent_summary", "")),
		"recommended_modes": _string_array(entry.get("recommended_modes", [])),
		"read_only": true,
		"presentation_profile_schema_version": PresentationProfileScript.SCHEMA_VERSION,
	}


func _safe_style_id(style_id: String) -> bool:
	if style_id.is_empty() or style_id.length() > MAX_STYLE_ID_LENGTH:
		return false
	for index in range(style_id.length()):
		if "abcdefghijklmnopqrstuvwxyz0123456789_".find(style_id[index]) == -1:
			return false
	return true


static func _string_array(source) -> Array:
	var result: Array = []
	if source is Array:
		for item in source:
			result.append(str(item))
	return result


func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


func _failure(message: String) -> Dictionary:
	return {"ok": false, "error": message}
