extends RefCounted

class_name DesignCaptureStore

const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")
const PersistentFileReplacementScript = preload("res://scripts/persistence/persistent_file_replacement.gd")

const METADATA_TYPE := "tet4d.design_comparison_capture"
const METADATA_SCHEMA_VERSION := 1
const DEFAULT_DIRECTORY := "user://design_lab/captures"

var _directory := DEFAULT_DIRECTORY


func _init(directory: String = DEFAULT_DIRECTORY) -> void:
	_directory = directory.trim_suffix("/")


func capture_arm(image: Image, session: Dictionary, arm: String, build_identity: Dictionary, catalog_version: int) -> Dictionary:
	if image == null or image.is_empty():
		return _failure("A rendered comparison image is required.")
	if not ["A", "B"].has(arm) or not DesignValueScript.safe_id(str(session.get("session_id", ""))):
		return _failure("A valid comparison session and arm are required.")
	var directory := _session_directory(str(session.get("session_id")))
	var ensure := _ensure_directory(directory)
	if not bool(ensure.get("ok", false)):
		return ensure
	var image_path := directory.path_join("%s.png" % arm)
	var temporary_absolute := "%s.tmp" % ProjectSettings.globalize_path(image_path)
	var save_error := image.save_png(temporary_absolute)
	if save_error != OK:
		return _failure("Comparison PNG could not be encoded (error %s)." % save_error)
	var replacement := PersistentFileReplacementScript.replace_temporary_file(temporary_absolute, ProjectSettings.globalize_path(image_path))
	if not bool(replacement.get("ok", false)):
		return _failure("Comparison PNG could not be installed: %s" % replacement.get("detail", "replacement failed"))
	var metadata := _metadata(session, build_identity, catalog_version)
	metadata["captured_arms"][arm] = {
		"file": "%s.png" % arm,
		"captured_at_utc": DesignValueScript.timestamp_utc(),
		"snapshot_hash": str(session.get("arms", {}).get(arm, {}).get("snapshot_hash", "")),
	}
	var metadata_path := directory.path_join("metadata.json")
	if FileAccess.file_exists(metadata_path):
		var existing := _read_json(metadata_path)
		if existing.get("session_id") == session.get("session_id") and existing.get("captured_arms") is Dictionary:
			for captured_arm in existing.get("captured_arms", {}).keys():
				if not metadata["captured_arms"].has(captured_arm):
					metadata["captured_arms"][captured_arm] = existing["captured_arms"][captured_arm]
	var written := PersistentFileReplacementScript.write_text(metadata_path, JSON.stringify(metadata, "  ", true) + "\n", true)
	if not bool(written.get("ok", false)):
		return _failure("Capture metadata could not be saved: %s" % written.get("detail", "replacement failed"))
	return _success({"directory": directory, "image_path": image_path, "metadata_path": metadata_path, "metadata": metadata})


func metadata_for_session(session_id: String) -> Dictionary:
	return _read_json(_session_directory(session_id).path_join("metadata.json"))


func _metadata(session: Dictionary, build_identity: Dictionary, catalog_version: int) -> Dictionary:
	return {
		"metadata_type": METADATA_TYPE,
		"metadata_schema_version": METADATA_SCHEMA_VERSION,
		"session_id": str(session.get("session_id", "")),
		"scenario_id": str(session.get("scenario_id", "")),
		"preset_identities": {
			"A": _capture_preset_identity(session.get("arms", {}).get("A", {})),
			"B": _capture_preset_identity(session.get("arms", {}).get("B", {})),
		},
		"blind": bool(session.get("blind", false)),
		"blind_labels": session.get("blind_labels", {}).duplicate(true),
		"build_identity": build_identity.duplicate(true),
		"catalog_schema_version": catalog_version,
		"captured_arms": {},
	}


static func _capture_preset_identity(preset: Dictionary) -> Dictionary:
	return {
		"source_kind": str(preset.get("source_kind", "")),
		"preset_id": str(preset.get("preset_id", "")),
		"preset_version": int(preset.get("preset_version", 0)),
		"snapshot_hash": str(preset.get("snapshot_hash", "")),
	}


func _session_directory(session_id: String) -> String:
	return _directory.path_join("comparison_%s" % session_id)


static func _read_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}


static func _ensure_directory(path: String) -> Dictionary:
	var absolute := ProjectSettings.globalize_path(path)
	if DirAccess.dir_exists_absolute(absolute):
		return _success()
	var error := DirAccess.make_dir_recursive_absolute(absolute)
	return _success() if error == OK else _failure("Capture directory could not be created (error %s)." % error)


static func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


static func _failure(error: String) -> Dictionary:
	return {"ok": false, "error": error}
