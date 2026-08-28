extends RefCounted

class_name PersistentFileReplacement

const TEMPORARY_SUFFIX := ".tmp"
const BACKUP_SUFFIX := ".bak"


static func write_text(
	destination_path: String,
	contents: String,
	allow_overwrite: bool = true,
	operations = null
) -> Dictionary:
	var destination_absolute := ProjectSettings.globalize_path(destination_path)
	if _file_exists(destination_absolute, operations) and not allow_overwrite:
		return _failure("destination already exists; overwrite was not requested", {
			"destination_untouched": true,
		})
	var temporary_absolute := "%s%s" % [destination_absolute, TEMPORARY_SUFFIX]
	var write_error := _write_text_file(temporary_absolute, contents, operations)
	if write_error != OK:
		var temporary_cleanup := _remove_if_present(temporary_absolute, operations)
		return _failure(
			"temporary write failed with error %s before the destination was modified%s" % [
				write_error,
				_cleanup_detail(temporary_cleanup),
			],
			{
				"destination_untouched": true,
				"write_error": write_error,
			}
		)
	return replace_temporary_file(temporary_absolute, destination_absolute, operations)


static func replace_temporary_file(
	temporary_path: String,
	destination_path: String,
	operations = null
) -> Dictionary:
	var backup_path := "%s%s" % [destination_path, BACKUP_SUFFIX]
	var destination_existed := _file_exists(destination_path, operations)
	var replace_error := _rename_absolute(temporary_path, destination_path, operations)
	if replace_error == OK:
		var stale_cleanup := _remove_if_present(backup_path, operations) if destination_existed else OK
		return _success({
			"warning": _cleanup_warning("stale backup", stale_cleanup),
			"replacement": "direct",
		})
	if not _file_exists(destination_path, operations):
		var temporary_cleanup := _remove_if_present(temporary_path, operations)
		return _failure(
			"installation failed with error %s before an existing destination was modified%s" % [
				replace_error,
				_cleanup_detail(temporary_cleanup),
			],
			{
				"destination_untouched": true,
				"install_error": replace_error,
			}
		)
	var stale_backup_cleanup := _remove_if_present(backup_path, operations)
	if stale_backup_cleanup != OK:
		_remove_if_present(temporary_path, operations)
		return _failure(
			"stale backup cleanup failed with error %s; the previous destination was not modified" % stale_backup_cleanup,
			{
				"destination_untouched": true,
				"backup_recoverable": _file_exists(backup_path, operations),
				"backup_path": backup_path,
			}
		)
	var backup_error := _rename_absolute(destination_path, backup_path, operations)
	if backup_error != OK:
		var temporary_cleanup := _remove_if_present(temporary_path, operations)
		return _failure(
			"the previous destination could not be backed up (error %s) and was not modified%s" % [
				backup_error,
				_cleanup_detail(temporary_cleanup),
			],
			{
				"destination_untouched": true,
				"backup_error": backup_error,
			}
		)
	var install_error := _rename_absolute(temporary_path, destination_path, operations)
	if install_error == OK:
		var backup_cleanup := _remove_if_present(backup_path, operations)
		return _success({
			"warning": _cleanup_warning("backup", backup_cleanup),
			"replacement": "backup_then_install",
			"backup_recoverable": _file_exists(backup_path, operations),
			"backup_path": backup_path,
		})
	var restore_error := _rename_absolute(backup_path, destination_path, operations)
	var restoration := "rename"
	if restore_error != OK:
		restore_error = _copy_absolute(backup_path, destination_path, operations)
		restoration = "copy"
	var temporary_cleanup := _remove_if_present(temporary_path, operations)
	if restore_error != OK:
		return _failure(
			"installation failed with error %s; restoration by rename and copy failed with error %s; the previous content remains%s at %s%s" % [
				install_error,
				restore_error,
				" recoverable" if _file_exists(backup_path, operations) else "",
				backup_path,
				_cleanup_detail(temporary_cleanup),
			],
			{
				"previous_restored": false,
				"backup_recoverable": _file_exists(backup_path, operations),
				"backup_path": backup_path,
				"install_error": install_error,
				"restore_error": restore_error,
				"restoration": "failed",
			}
		)
	var backup_cleanup := _remove_if_present(backup_path, operations)
	return _failure(
		"installation failed with error %s; the previous content was restored by %s%s%s" % [
			install_error,
			restoration,
			_cleanup_detail(temporary_cleanup),
			_cleanup_detail(backup_cleanup, "backup"),
		],
		{
			"previous_restored": true,
			"backup_recoverable": _file_exists(backup_path, operations),
			"backup_path": backup_path,
			"install_error": install_error,
			"restoration": restoration,
		}
	)


static func _write_text_file(path: String, contents: String, operations) -> Error:
	if operations != null and operations.has_method("write_text_file"):
		return operations.write_text_file(path, contents)
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(contents)
	file.flush()
	var write_error := file.get_error()
	file.close()
	return write_error


static func _file_exists(path: String, operations) -> bool:
	if operations != null and operations.has_method("file_exists"):
		return bool(operations.file_exists(path))
	return FileAccess.file_exists(path)


static func _rename_absolute(from_path: String, to_path: String, operations) -> Error:
	if operations != null and operations.has_method("rename_absolute"):
		return operations.rename_absolute(from_path, to_path)
	return DirAccess.rename_absolute(from_path, to_path)


static func _copy_absolute(from_path: String, to_path: String, operations) -> Error:
	if operations != null and operations.has_method("copy_absolute"):
		return operations.copy_absolute(from_path, to_path)
	return DirAccess.copy_absolute(from_path, to_path)


static func _remove_absolute(path: String, operations) -> Error:
	if operations != null and operations.has_method("remove_absolute"):
		return operations.remove_absolute(path)
	return DirAccess.remove_absolute(path)


static func _remove_if_present(path: String, operations) -> Error:
	return _remove_absolute(path, operations) if _file_exists(path, operations) else OK


static func _cleanup_detail(error: Error, label: String = "temporary file") -> String:
	return "" if error == OK else "; %s cleanup also failed with error %s" % [label, error]


static func _cleanup_warning(label: String, error: Error) -> String:
	return "" if error == OK else "%s cleanup failed with error %s" % [label, error]


static func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {
		"ok": true,
		"detail": "",
		"previous_restored": false,
		"backup_recoverable": false,
		"backup_path": "",
		"restoration": "not_required",
	}
	result.merge(extra, true)
	return result


static func _failure(detail: String, extra: Dictionary = {}) -> Dictionary:
	var result := {
		"ok": false,
		"detail": detail,
		"previous_restored": false,
		"backup_recoverable": false,
		"backup_path": "",
		"restoration": "not_required",
	}
	result.merge(extra, true)
	return result
