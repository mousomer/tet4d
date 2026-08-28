extends RefCounted

const ReplacementScript = preload("res://scripts/persistence/persistent_file_replacement.gd")

const TEST_DIRECTORY := "user://stage54f3r1_persistent_file_replacement"
const DESTINATION_PATH := TEST_DIRECTORY + "/destination.json"
const BACKUP_PATH := DESTINATION_PATH + ReplacementScript.BACKUP_SUFFIX
const TEMPORARY_PATH := DESTINATION_PATH + ReplacementScript.TEMPORARY_SUFFIX
const PREVIOUS_CONTENT := "previous destination content\n"
const REPLACEMENT_CONTENT := "replacement destination content\n"
const BACKUP_SENTINEL := "unrelated sibling backup sentinel\n"


class InjectedOperations:
	extends RefCounted

	var rename_failures: Dictionary = {}
	var remove_failures: Dictionary = {}
	var rename_count := 0
	var remove_count := 0
	var backup_observed_before_install := false
	var observed_backup_content := ""

	func file_exists(path: String) -> bool:
		return FileAccess.file_exists(path)

	func rename_absolute(from_path: String, to_path: String) -> Error:
		rename_count += 1
		if rename_failures.has(rename_count):
			return rename_failures.get(rename_count)
		if rename_count == 3:
			var backup_path := "%s.bak" % to_path
			backup_observed_before_install = FileAccess.file_exists(backup_path)
			observed_backup_content = _read_text(backup_path)
		return DirAccess.rename_absolute(from_path, to_path)

	func copy_absolute(from_path: String, to_path: String) -> Error:
		return DirAccess.copy_absolute(from_path, to_path)

	func remove_absolute(path: String) -> Error:
		remove_count += 1
		if remove_failures.has(remove_count):
			return remove_failures.get(remove_count)
		return DirAccess.remove_absolute(path)

	func _read_text(path: String) -> String:
		var file := FileAccess.open(path, FileAccess.READ)
		return file.get_as_text() if file != null else ""


func run() -> Array:
	var failures: Array = []
	_cleanup()
	var directory_error := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(TEST_DIRECTORY))
	if directory_error != OK:
		return ["persistent replacement tests require a writable temporary user-data directory"]
	failures.append_array(_test_fresh_install_preserves_unrelated_backup())
	failures.append_array(_test_absent_install_failure())
	failures.append_array(_test_backup_then_install_success())
	failures.append_array(_test_stale_backup_cleanup_warning())
	_cleanup()
	return failures


func _test_fresh_install_preserves_unrelated_backup() -> Array:
	var failures: Array = []
	_reset_files()
	_write_text(BACKUP_PATH, BACKUP_SENTINEL)
	var operations := InjectedOperations.new()
	var result: Dictionary = ReplacementScript.write_text(
		DESTINATION_PATH,
		REPLACEMENT_CONTENT,
		true,
		operations
	)
	if not bool(result.get("ok", false)) or _read_text(DESTINATION_PATH) != REPLACEMENT_CONTENT:
		failures.append("fresh direct replacement should install the requested destination")
	if _read_text(BACKUP_PATH) != BACKUP_SENTINEL:
		failures.append("fresh direct replacement must preserve an unrelated sibling backup byte-for-byte")
	if operations.remove_count != 0 or FileAccess.file_exists(TEMPORARY_PATH):
		failures.append("fresh direct replacement must not claim sibling backup cleanup ownership")
	return failures


func _test_absent_install_failure() -> Array:
	var failures: Array = []
	_reset_files()
	_write_text(BACKUP_PATH, BACKUP_SENTINEL)
	var operations := InjectedOperations.new()
	operations.rename_failures = {1: ERR_CANT_CREATE}
	var result: Dictionary = ReplacementScript.write_text(
		DESTINATION_PATH,
		REPLACEMENT_CONTENT,
		true,
		operations
	)
	if bool(result.get("ok", false)) or not bool(result.get("destination_untouched", false)):
		failures.append("absent-destination install failure should report bounded failure")
	if FileAccess.file_exists(DESTINATION_PATH) or FileAccess.file_exists(TEMPORARY_PATH):
		failures.append("absent-destination install failure must leave no destination or temporary phantom")
	if _read_text(BACKUP_PATH) != BACKUP_SENTINEL or operations.rename_count != 1:
		failures.append("absent-destination install failure must not touch an unrelated sibling backup")
	return failures


func _test_backup_then_install_success() -> Array:
	var failures: Array = []
	_reset_files()
	_write_text(DESTINATION_PATH, PREVIOUS_CONTENT)
	var operations := InjectedOperations.new()
	operations.rename_failures = {1: ERR_CANT_CREATE}
	var result: Dictionary = ReplacementScript.write_text(
		DESTINATION_PATH,
		REPLACEMENT_CONTENT,
		true,
		operations
	)
	if not bool(result.get("ok", false)) or result.get("replacement") != "backup_then_install":
		failures.append("existing-destination fallback should report backup-then-install success")
	if _read_text(DESTINATION_PATH) != REPLACEMENT_CONTENT:
		failures.append("backup-then-install success should leave the new destination readable")
	if not operations.backup_observed_before_install or operations.observed_backup_content != PREVIOUS_CONTENT:
		failures.append("backup-then-install must preserve the exact prior destination during transition")
	if FileAccess.file_exists(TEMPORARY_PATH) or FileAccess.file_exists(BACKUP_PATH):
		failures.append("backup-then-install success should clean owned temporary and backup state")
	if operations.rename_count != 3 or operations.remove_count != 1:
		failures.append("backup-then-install should execute each state transition exactly once")
	return failures


func _test_stale_backup_cleanup_warning() -> Array:
	var failures: Array = []
	_reset_files()
	_write_text(DESTINATION_PATH, PREVIOUS_CONTENT)
	_write_text(BACKUP_PATH, BACKUP_SENTINEL)
	var operations := InjectedOperations.new()
	operations.remove_failures = {1: ERR_CANT_CREATE}
	var result: Dictionary = ReplacementScript.write_text(
		DESTINATION_PATH,
		REPLACEMENT_CONTENT,
		true,
		operations
	)
	if not bool(result.get("ok", false)) or str(result.get("warning", "")).is_empty():
		failures.append("stale-backup cleanup failure should report successful installation with an explicit warning")
	if _read_text(DESTINATION_PATH) != REPLACEMENT_CONTENT or _read_text(BACKUP_PATH) != BACKUP_SENTINEL:
		failures.append("stale-backup cleanup failure must leave the new destination and retained backup intact")
	if FileAccess.file_exists(TEMPORARY_PATH) or operations.remove_count != 1:
		failures.append("stale-backup cleanup failure should be deterministic and leave no temporary artifact")
	return failures


func _reset_files() -> void:
	for path in [DESTINATION_PATH, TEMPORARY_PATH, BACKUP_PATH]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _write_text(path: String, contents: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(contents)
		file.close()


func _read_text(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	return file.get_as_text() if file != null else ""


func _cleanup() -> void:
	_reset_files()
	var absolute := ProjectSettings.globalize_path(TEST_DIRECTORY)
	if DirAccess.dir_exists_absolute(absolute):
		DirAccess.remove_absolute(absolute)
