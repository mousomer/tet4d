extends RefCounted

const OperationResult = preload("res://scripts/operation_result.gd")


static func ensure(path: String, label: String) -> Dictionary:
	var absolute := ProjectSettings.globalize_path(path)
	if DirAccess.dir_exists_absolute(absolute):
		return OperationResult.success()
	var error := DirAccess.make_dir_recursive_absolute(absolute)
	if error != OK:
		return OperationResult.failure("%s directory could not be created (error %s)." % [label, error])
	return OperationResult.success()
