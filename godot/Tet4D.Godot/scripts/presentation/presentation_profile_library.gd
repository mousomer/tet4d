extends RefCounted

class_name PresentationProfileLibrary

const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const PersistentFileReplacementScript = preload("res://scripts/persistence/persistent_file_replacement.gd")

const ARTIFACT_TYPE := "tet4d.presentation_profile"
const ARTIFACT_SCHEMA_VERSION := 1
const DEFAULT_DIRECTORY := "user://presentation_profiles"
const FILE_SUFFIX := ".tet4d-presentation-profile.json"
const MAX_DISPLAY_NAME_LENGTH := 80

var _registry
var _storage_directory := DEFAULT_DIRECTORY
var _storage_ops
var _diagnostics: Array = []
var _write_count := 0
var _mutation_count := 0


func _init(registry = null, storage_directory: String = DEFAULT_DIRECTORY, storage_ops = null) -> void:
	_registry = registry
	_storage_directory = storage_directory.trim_suffix("/")
	_storage_ops = storage_ops


func list_profiles() -> Array:
	var records: Array = []
	var scan_diagnostics: Array = []
	var directory := DirAccess.open(ProjectSettings.globalize_path(_storage_directory))
	if directory == null:
		_diagnostics = scan_diagnostics
		return records
	var file_names: Array = []
	directory.list_dir_begin()
	var file_name := directory.get_next()
	while not file_name.is_empty():
		if not directory.current_is_dir() and file_name.ends_with(FILE_SUFFIX):
			file_names.append(file_name)
		file_name = directory.get_next()
	directory.list_dir_end()
	file_names.sort()
	for candidate_name in file_names:
		var result := _read_artifact(_storage_directory.path_join(str(candidate_name)))
		if bool(result.get("ok", false)):
			var artifact: Dictionary = result.get("artifact", {})
			var expected_file := _file_name(str(artifact.get("profile_id", "")))
			if candidate_name == expected_file:
				records.append(_record_for_artifact(artifact))
			else:
				scan_diagnostics.append("Ignored profile artifact whose filename does not match its stable identity: %s" % candidate_name)
		else:
			scan_diagnostics.append("Ignored damaged profile %s: %s" % [candidate_name, result.get("error", "invalid artifact")])
	records.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		var left_name := str(left.get("display_name", "")).to_lower()
		var right_name := str(right.get("display_name", "")).to_lower()
		return left_name < right_name if left_name != right_name else str(left.get("profile_id", "")) < str(right.get("profile_id", ""))
	)
	_diagnostics = scan_diagnostics
	return records


func save_new(display_name: String, profile) -> Dictionary:
	var name_result := _validated_available_name(display_name)
	if not bool(name_result.get("ok", false)):
		return name_result
	var profile_result := _validated_profile(profile)
	if not bool(profile_result.get("ok", false)):
		return profile_result
	var profile_id := _new_profile_id()
	var artifact := _artifact(profile_id, str(name_result.get("display_name")), profile)
	var write_result := _write_artifact(_artifact_path(profile_id), artifact, false)
	if not bool(write_result.get("ok", false)):
		return write_result
	return _success({"record": _record_for_artifact(artifact), "profile": profile.detached_copy()})


func save_existing(profile_id: String, profile) -> Dictionary:
	var loaded := _load_artifact_by_id(profile_id)
	if not bool(loaded.get("ok", false)):
		return loaded
	var profile_result := _validated_profile(profile)
	if not bool(profile_result.get("ok", false)):
		return profile_result
	var existing: Dictionary = loaded.get("artifact", {})
	var artifact := _artifact(profile_id, str(existing.get("display_name", "")), profile)
	var write_result := _write_artifact(_artifact_path(profile_id), artifact, true)
	if not bool(write_result.get("ok", false)):
		return write_result
	return _success({"record": _record_for_artifact(artifact), "profile": profile.detached_copy()})


func load_profile(profile_id: String) -> Dictionary:
	var loaded := _load_artifact_by_id(profile_id)
	if not bool(loaded.get("ok", false)):
		return loaded
	var artifact: Dictionary = loaded.get("artifact", {})
	return _success({
		"record": _record_for_artifact(artifact),
		"profile": loaded.get("profile").detached_copy(),
	})


func duplicate_profile(profile_id: String, requested_name: String = "") -> Dictionary:
	var loaded := load_profile(profile_id)
	if not bool(loaded.get("ok", false)):
		return loaded
	var source_record: Dictionary = loaded.get("record", {})
	var display_name := requested_name.strip_edges()
	if display_name.is_empty():
		display_name = _next_available_copy_name(str(source_record.get("display_name", "Profile")))
	return save_new(display_name, loaded.get("profile"))


func rename_profile(profile_id: String, display_name: String) -> Dictionary:
	var loaded := _load_artifact_by_id(profile_id)
	if not bool(loaded.get("ok", false)):
		return loaded
	var name_result := _validated_available_name(display_name, profile_id)
	if not bool(name_result.get("ok", false)):
		return name_result
	var profile = loaded.get("profile")
	var artifact := _artifact(profile_id, str(name_result.get("display_name")), profile)
	var write_result := _write_artifact(_artifact_path(profile_id), artifact, true)
	if not bool(write_result.get("ok", false)):
		return write_result
	return _success({"record": _record_for_artifact(artifact), "profile": profile.detached_copy()})


func delete_profile(profile_id: String) -> Dictionary:
	var loaded := _load_artifact_by_id(profile_id)
	if not bool(loaded.get("ok", false)):
		return loaded
	var error := DirAccess.remove_absolute(ProjectSettings.globalize_path(_artifact_path(profile_id)))
	if error != OK:
		return _failure("Profile could not be deleted (error %s)." % error)
	_mutation_count += 1
	return _success({"record": _record_for_artifact(loaded.get("artifact", {}))})


func export_profile(profile_id: String, destination_path: String, allow_overwrite: bool = false) -> Dictionary:
	if destination_path.strip_edges().is_empty():
		return _failure("Choose an export destination.")
	var loaded := _load_artifact_by_id(profile_id)
	if not bool(loaded.get("ok", false)):
		return loaded
	var result := _write_json_file(destination_path, loaded.get("artifact", {}), allow_overwrite)
	if not bool(result.get("ok", false)):
		return result
	return _success({"path": destination_path, "record": _record_for_artifact(loaded.get("artifact", {}))})


func import_profile(source_path: String, requested_name: String = "") -> Dictionary:
	var parsed := _read_artifact(source_path)
	if not bool(parsed.get("ok", false)):
		return parsed
	return import_artifact(parsed.get("artifact", {}), requested_name)


func import_artifact(artifact: Dictionary, requested_name: String = "") -> Dictionary:
	var validated := validate_artifact(artifact)
	if not bool(validated.get("ok", false)):
		return validated
	var source: Dictionary = validated.get("artifact", {})
	var display_name := requested_name.strip_edges()
	if display_name.is_empty():
		display_name = _next_available_import_name(str(source.get("display_name", "Imported Profile")))
	return save_new(display_name, validated.get("profile"))


func validate_artifact(artifact: Dictionary) -> Dictionary: # tet4d-semantic-boundary: allow diagnostic-presentation
	if artifact.is_empty():
		return _failure("Profile artifact root must be a non-empty object.")
	if str(artifact.get("artifact_type", "")) != ARTIFACT_TYPE:
		return _failure("Profile artifact type is unsupported.")
	if not _exact_version(artifact.get("artifact_schema_version"), ARTIFACT_SCHEMA_VERSION):
		return _failure("This profile was created by a newer or unsupported artifact format.")
	var profile_id := str(artifact.get("profile_id", ""))
	if not _valid_profile_id(profile_id):
		return _failure("Profile artifact identity is invalid or unsafe.")
	var name_result := _validate_display_name(str(artifact.get("display_name", "")))
	if not bool(name_result.get("ok", false)):
		return name_result
	var profile_snapshot = artifact.get("presentation_profile")
	if not (profile_snapshot is Dictionary):
		return _failure("Profile artifact presentation_profile must be an object.")
	if not _exact_version(profile_snapshot.get("schema_version"), PresentationProfileScript.SCHEMA_VERSION):
		return _failure("This profile was created by a newer or unsupported presentation-profile format.")
	var profile = PresentationProfileScript.from_snapshot(_registry, profile_snapshot)
	if not _valid_profile(profile):
		var detail := "; ".join(profile.failures()) if profile != null and profile.has_method("failures") else "invalid profile"
		return _failure("Profile values failed authoritative validation: %s." % detail)
	var canonical := _artifact(profile_id, str(name_result.get("display_name")), profile)
	return _success({"artifact": canonical, "profile": profile.detached_copy()})


func diagnostics() -> Array:
	return _diagnostics.duplicate()


func deterministic_snapshot() -> Dictionary:
	var profiles := list_profiles()
	return {
		"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
		"storage_directory": _storage_directory,
		"profiles": profiles,
		"write_count": _write_count,
		"mutation_count": _mutation_count,
		"diagnostics": diagnostics(),
	}


func _load_artifact_by_id(profile_id: String) -> Dictionary:
	if not _valid_profile_id(profile_id):
		return _failure("Profile identity is invalid or unsafe.")
	return _read_artifact(_artifact_path(profile_id))


func _read_artifact(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return _failure("Profile artifact does not exist.")
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return _failure("Profile artifact could not be read.")
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK:
		return _failure("Profile artifact JSON is malformed.")
	if not (parser.data is Dictionary):
		return _failure("Profile artifact root must be an object.")
	return validate_artifact(parser.data)


func _validated_profile(profile) -> Dictionary: # tet4d-semantic-boundary: allow diagnostic-presentation
	if not _valid_profile(profile):
		return _failure("A conforming PresentationProfile is required.")
	return _success({"profile": profile.detached_copy()})


func _validated_available_name(display_name: String, allowed_profile_id: String = "") -> Dictionary: # tet4d-semantic-boundary: allow diagnostic-presentation
	var result := _validate_display_name(display_name)
	if not bool(result.get("ok", false)):
		return result
	var canonical_name := str(result.get("display_name"))
	for record in list_profiles():
		if str(record.get("profile_id", "")) != allowed_profile_id and str(record.get("display_name", "")).to_lower() == canonical_name.to_lower():
			return _failure("A profile named '%s' already exists." % canonical_name)
	return result


func _validate_display_name(display_name: String) -> Dictionary: # tet4d-semantic-boundary: allow diagnostic-presentation
	var canonical := display_name.strip_edges()
	if canonical.is_empty():
		return _failure("Profile name cannot be empty.")
	if canonical.length() > MAX_DISPLAY_NAME_LENGTH:
		return _failure("Profile name must be at most %d characters." % MAX_DISPLAY_NAME_LENGTH)
	if canonical.find("..") >= 0 or canonical.find("/") >= 0 or canonical.find("\\") >= 0 or canonical.find(":") >= 0:
		return _failure("Profile name cannot contain path or traversal characters.")
	for index in range(canonical.length()):
		if canonical.unicode_at(index) < 32:
			return _failure("Profile name cannot contain control characters.")
	return _success({"display_name": canonical})


func _artifact(profile_id: String, display_name: String, profile) -> Dictionary:
	return {
		"artifact_type": ARTIFACT_TYPE,
		"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
		"profile_id": profile_id,
		"display_name": display_name,
		"presentation_profile": profile.snapshot(),
	}


func _record_for_artifact(artifact: Dictionary) -> Dictionary:
	var profile_snapshot: Dictionary = artifact.get("presentation_profile", {})
	return {
		"profile_id": str(artifact.get("profile_id", "")),
		"display_name": str(artifact.get("display_name", "")),
		"artifact_schema_version": int(artifact.get("artifact_schema_version", 0)),
		"presentation_profile_schema_version": int(profile_snapshot.get("schema_version", 0)),
	}


func _write_artifact(path: String, artifact: Dictionary, allow_overwrite: bool) -> Dictionary:
	var directory_result := _ensure_storage_directory()
	if not bool(directory_result.get("ok", false)):
		return directory_result
	var result := _write_json_file(path, artifact, allow_overwrite)
	if bool(result.get("ok", false)):
		_write_count += 1
		_mutation_count += 1
	return result


func _write_json_file(path: String, payload: Dictionary, allow_overwrite: bool) -> Dictionary:
	if _storage_ops != null and _storage_ops.has_method("write_json_file"):
		return _storage_ops.write_json_file(path, payload.duplicate(true), allow_overwrite)
	var replacement: Dictionary = PersistentFileReplacementScript.write_text(
		path,
		JSON.stringify(payload, "  ", true) + "\n",
		allow_overwrite,
		_storage_ops
	)
	if bool(replacement.get("ok", false)):
		return _success({"warning": replacement.get("warning", "")})
	var result := _failure("Profile file could not be saved: %s." % replacement.get("detail", "replacement failed"))
	for key in ["destination_untouched", "previous_restored", "backup_recoverable", "backup_path", "restoration", "write_error", "install_error", "restore_error"]:
		if replacement.has(key):
			result[key] = replacement.get(key)
	return result


func _ensure_storage_directory() -> Dictionary:
	if _storage_ops != null and _storage_ops.has_method("ensure_directory"):
		return _storage_ops.ensure_directory(_storage_directory)
	if DirAccess.dir_exists_absolute(ProjectSettings.globalize_path(_storage_directory)):
		return _success()
	var error := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(_storage_directory))
	return _success() if error == OK else _failure("Profile library directory could not be created (error %s)." % error)


func _next_available_copy_name(source_name: String) -> String:
	return _next_available_derived_name("%s Copy" % source_name)


func _next_available_import_name(source_name: String) -> String:
	return _next_available_derived_name("%s Imported" % source_name)


func _next_available_derived_name(base_name: String) -> String:
	var existing: Array = []
	for record in list_profiles():
		existing.append(str(record.get("display_name", "")).to_lower())
	var candidate := base_name.left(MAX_DISPLAY_NAME_LENGTH)
	var counter := 2
	while existing.has(candidate.to_lower()):
		var suffix := " %d" % counter
		candidate = "%s%s" % [base_name.left(MAX_DISPLAY_NAME_LENGTH - suffix.length()), suffix]
		counter += 1
	return candidate


func _new_profile_id() -> String:
	var crypto := Crypto.new()
	var candidate := crypto.generate_random_bytes(16).hex_encode()
	while FileAccess.file_exists(_artifact_path(candidate)):
		candidate = crypto.generate_random_bytes(16).hex_encode()
	return candidate


func _valid_profile_id(profile_id: String) -> bool:
	if profile_id.length() != 32:
		return false
	for index in range(profile_id.length()):
		if "0123456789abcdef".find(profile_id[index]) == -1:
			return false
	return true


func _exact_version(value, expected: int) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and float(value) == float(int(value)) and int(value) == expected


func _valid_profile(profile) -> bool:
	return profile != null and profile.has_method("contract_conforms") and profile.contract_conforms()


func _artifact_path(profile_id: String) -> String:
	return _storage_directory.path_join(_file_name(profile_id))


func _file_name(profile_id: String) -> String:
	return "%s%s" % [profile_id, FILE_SUFFIX]


func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


func _failure(message: String) -> Dictionary:
	return {"ok": false, "error": message}
