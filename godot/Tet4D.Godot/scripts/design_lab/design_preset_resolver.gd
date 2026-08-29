extends RefCounted

class_name DesignPresetResolver

const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")

const SOURCE_BUILT_IN := "built_in"
const SOURCE_USER := "user"

var _catalog
var _library


func _init(catalog = null, library = null) -> void:
	_catalog = catalog
	_library = library


func list_presets() -> Array:
	var result: Array = []
	if _catalog != null:
		for record in _catalog.list_styles():
			result.append(_built_in_descriptor(record))
	if _library != null:
		for record in _library.list_profiles():
			result.append(_user_descriptor(record))
	return result


func resolve(source_kind: String, preset_id: String) -> Dictionary:
	if source_kind == SOURCE_BUILT_IN and _catalog != null:
		var loaded: Dictionary = _catalog.style_profile(preset_id)
		if not bool(loaded.get("ok", false)):
			return _failure(str(loaded.get("error", "Built-in preset could not be resolved.")))
		var metadata: Dictionary = loaded.get("record", {})
		return _resolved(_built_in_descriptor(metadata), loaded.get("profile"))
	if source_kind == SOURCE_USER and _library != null:
		var loaded: Dictionary = _library.load_profile(preset_id)
		if not bool(loaded.get("ok", false)):
			return _failure(str(loaded.get("error", "User preset could not be resolved.")))
		return _resolved(_user_descriptor(loaded.get("record", {})), loaded.get("profile"))
	return _failure("Unknown preset source or identity.")


func duplicate_as_candidate(source_kind: String, preset_id: String, display_name: String = "") -> Dictionary:
	if _library == null:
		return _failure("User profile library is unavailable.")
	var resolved := resolve(source_kind, preset_id)
	if not bool(resolved.get("ok", false)):
		return resolved
	var descriptor: Dictionary = resolved.get("descriptor", {})
	var candidate_name := display_name.strip_edges()
	if candidate_name.is_empty():
		candidate_name = "%s Candidate" % str(descriptor.get("display_name", "Preset"))
	return _library.save_new(candidate_name, resolved.get("profile"))


func _resolved(descriptor: Dictionary, profile) -> Dictionary:
	if profile == null or not profile.has_method("contract_conforms") or not profile.contract_conforms():
		return _failure("Resolved preset does not conform to the canonical registry.")
	var snapshot: Dictionary = profile.snapshot()
	var version := int(snapshot.get("schema_version", 0))
	descriptor["preset_version"] = version
	descriptor["snapshot_hash"] = DesignValueScript.canonical_hash(snapshot)
	return {"ok": true, "error": "", "descriptor": descriptor, "profile": profile.detached_copy(), "snapshot": snapshot}


static func _built_in_descriptor(record: Dictionary) -> Dictionary:
	return {
		"source_kind": SOURCE_BUILT_IN,
		"preset_id": str(record.get("style_id", "")),
		"display_name": str(record.get("display_name", "")),
		"description": str(record.get("short_description", "")),
		"provenance": "Shipped built-in style",
		"category": str(record.get("category", "")),
		"status": "candidate",
		"read_only": true,
	}


static func _user_descriptor(record: Dictionary) -> Dictionary:
	return {
		"source_kind": SOURCE_USER,
		"preset_id": str(record.get("profile_id", "")),
		"display_name": str(record.get("display_name", "")),
		"description": "Mutable user presentation candidate",
		"provenance": "User profile library",
		"category": "user",
		"status": "candidate",
		"read_only": false,
	}


static func _failure(error: String) -> Dictionary:
	return {"ok": false, "error": error}
