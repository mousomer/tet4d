extends RefCounted

class_name DesignEvaluationStore

const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")
const PersistentFileReplacementScript = preload("res://scripts/persistence/persistent_file_replacement.gd")

const RECORD_TYPE := "tet4d.design_evaluation"
const RECORD_SCHEMA_VERSION := 1
const DEFAULT_DIRECTORY := "user://design_lab/evaluations"
const FILE_SUFFIX := ".tet4d-design-evaluation.json"
const PREFERENCES := ["prefer_a", "prefer_b", "no_preference"]
const RATING_IDS := [
	"readability",
	"spatial_comprehension",
	"depth_perception",
	"visual_hierarchy",
	"gameplay_focus",
	"aesthetic_quality",
	"motion_comfort",
	"ui_clarity",
]

var _directory := DEFAULT_DIRECTORY


func _init(directory: String = DEFAULT_DIRECTORY) -> void:
	_directory = directory.trim_suffix("/")


func create_record(session: Dictionary, preference: String, ratings: Dictionary, notes: String, build_identity: Dictionary, catalog_version: int) -> Dictionary:
	if int(session.get("session_schema_version", 0)) != 1 or not DesignValueScript.safe_id(str(session.get("session_id", ""))):
		return _failure("A valid frozen comparison session is required.")
	if not PREFERENCES.has(preference):
		return _failure("Evaluation preference is unsupported.")
	var normalized_ratings := _normalize_ratings(ratings)
	if not bool(normalized_ratings.get("ok", false)):
		return normalized_ratings
	var record_id := ("%s|%s|%s" % [str(session.get("session_id")), DesignValueScript.timestamp_utc(), str(Time.get_ticks_usec())]).sha256_text().substr(0, 32)
	var record := {
		"record_type": RECORD_TYPE,
		"record_schema_version": RECORD_SCHEMA_VERSION,
		"record_id": record_id,
		"session_id": str(session.get("session_id", "")),
		"scenario_id": str(session.get("scenario_id", "")),
		"preference": preference,
		"ratings": normalized_ratings.get("ratings", {}),
		"notes": notes.strip_edges(),
		"timestamp_utc": DesignValueScript.timestamp_utc(),
		"blind": bool(session.get("blind", false)),
		"build_identity": build_identity.duplicate(true),
		"catalog_schema_version": catalog_version,
		"non_style_hash": str(session.get("non_style_hash", "")),
		"presets": session.get("arms", {}).duplicate(true),
	}
	return _success({"record": record})


func save_record(record: Dictionary) -> Dictionary:
	var parsed_record := parse_record(record)
	if not bool(parsed_record.get("ok", false)):
		return parsed_record
	var directory_result := _ensure_directory()
	if not bool(directory_result.get("ok", false)):
		return directory_result
	var canonical: Dictionary = parsed_record.get("record", {})
	var path := _directory.path_join("%s%s" % [str(canonical.get("record_id")), FILE_SUFFIX])
	var write := PersistentFileReplacementScript.write_text(path, JSON.stringify(canonical, "  ", true) + "\n", false)
	if not bool(write.get("ok", false)):
		return _failure("Evaluation could not be saved: %s" % str(write.get("detail", "replacement failed")))
	return _success({"record": canonical.duplicate(true), "path": path, "warning": str(write.get("warning", ""))})


func list_records() -> Array:
	var result: Array = []
	var directory := DirAccess.open(ProjectSettings.globalize_path(_directory))
	if directory == null:
		return result
	directory.list_dir_begin()
	var file_name := directory.get_next()
	while not file_name.is_empty():
		if not directory.current_is_dir() and file_name.ends_with(FILE_SUFFIX):
			var loaded := load_path(_directory.path_join(file_name))
			if bool(loaded.get("ok", false)):
				result.append(loaded.get("record", {}))
		file_name = directory.get_next()
	directory.list_dir_end()
	result.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		return str(left.get("timestamp_utc", "")) < str(right.get("timestamp_utc", ""))
	)
	return result


func records_for_preset(source_kind: String, preset_id: String) -> Array:
	var result: Array = []
	for record in list_records():
		for arm in ["A", "B"]:
			var preset: Dictionary = record.get("presets", {}).get(arm, {})
			if str(preset.get("source_kind", "")) == source_kind and str(preset.get("preset_id", "")) == preset_id:
				result.append(record.duplicate(true))
				break
	return result


func load_path(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return _failure("Evaluation record could not be read.")
	var parsed = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary):
		return _failure("Evaluation record JSON is malformed.")
	return parse_record(parsed)


func parse_record(record: Dictionary) -> Dictionary:
	if str(record.get("record_type", "")) != RECORD_TYPE or int(record.get("record_schema_version", 0)) != RECORD_SCHEMA_VERSION:
		return _failure("Evaluation record envelope is unsupported.")
	for id_key in ["record_id", "session_id", "scenario_id"]:
		if not DesignValueScript.safe_id(str(record.get(id_key, ""))):
			return _failure("Evaluation %s is invalid." % id_key)
	if not PREFERENCES.has(str(record.get("preference", ""))):
		return _failure("Evaluation preference is unsupported.")
	var ratings := _normalize_ratings(record.get("ratings", {}))
	if not bool(ratings.get("ok", false)):
		return ratings
	var presets = record.get("presets")
	if not (presets is Dictionary) or not presets.has("A") or not presets.has("B"):
		return _failure("Evaluation must retain frozen A and B preset provenance.")
	for arm in ["A", "B"]:
		var preset = presets.get(arm)
		if not (preset is Dictionary) or not DesignValueScript.safe_id(str(preset.get("preset_id", ""))):
			return _failure("Evaluation preset %s identity is invalid." % arm)
		var snapshot = preset.get("presentation_profile")
		if not (snapshot is Dictionary) or DesignValueScript.canonical_hash(snapshot) != str(preset.get("snapshot_hash", "")):
			return _failure("Evaluation preset %s snapshot provenance is inconsistent." % arm)
	var canonical := record.duplicate(true)
	canonical["ratings"] = ratings.get("ratings", {})
	return _success({"record": canonical})


func _normalize_ratings(ratings) -> Dictionary:
	if not (ratings is Dictionary):
		return _failure("Evaluation ratings must be an object.")
	var result: Dictionary = {}
	for key in ratings.keys():
		var rating_id := str(key)
		if not RATING_IDS.has(rating_id):
			return _failure("Unknown evaluation rating %s." % rating_id)
		var value = ratings.get(key)
		if not (value is int or value is float) or float(value) != floorf(float(value)) or int(value) < 1 or int(value) > 5:
			return _failure("Evaluation rating %s must be an integer from 1 to 5." % rating_id)
		result[rating_id] = int(value)
	return _success({"ratings": result})


func _ensure_directory() -> Dictionary:
	var absolute := ProjectSettings.globalize_path(_directory)
	if DirAccess.dir_exists_absolute(absolute):
		return _success()
	var error := DirAccess.make_dir_recursive_absolute(absolute)
	return _success() if error == OK else _failure("Evaluation directory could not be created (error %s)." % error)


static func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


static func _failure(error: String) -> Dictionary:
	return {"ok": false, "error": error}
