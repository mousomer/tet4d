extends RefCounted

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const StoreScript = preload("res://scripts/ui/settings/settings_store.gd")

const TEST_PATH := "user://stage48_shell_settings_store_test.json"


class InjectedReplacementOps:
	extends RefCounted

	var rename_failures: Dictionary = {}
	var copy_failures: Dictionary = {}
	var remove_failures: Dictionary = {}
	var rename_count := 0
	var copy_count := 0
	var remove_count := 0

	func file_exists(path: String) -> bool:
		return FileAccess.file_exists(path)

	func rename_absolute(from_path: String, to_path: String) -> Error:
		rename_count += 1
		if rename_failures.has(rename_count):
			return rename_failures.get(rename_count)
		return DirAccess.rename_absolute(from_path, to_path)

	func copy_absolute(from_path: String, to_path: String) -> Error:
		copy_count += 1
		if copy_failures.has(copy_count):
			return copy_failures.get(copy_count)
		return DirAccess.copy_absolute(from_path, to_path)

	func remove_absolute(path: String) -> Error:
		remove_count += 1
		if remove_failures.has(remove_count):
			return remove_failures.get(remove_count)
		return DirAccess.remove_absolute(path)


func run() -> Array:
	var failures: Array = []
	_cleanup()
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var store = StoreScript.new(registry, TEST_PATH)
	if store.deterministic_snapshot().get("load_state") != "defaults_missing_file":
		failures.append("missing settings file should load canonical defaults")
	if store.value("theme.name") != "tron" or store.value("interface.show_onboarding") != true:
		failures.append("registry defaults should seed a missing settings file")
	store.set_value("theme.name", "plain")
	store.set_value("controls_help.show_keyboard_hints", false)
	store.set_value("replay.playback_speed", 1.5)
	store.set_value("diagnostics.show_layout_bounds", true)
	var save_count := int(store.deterministic_snapshot().get("save_count", 0))
	store.set_value("theme.name", "plain")
	if int(store.deterministic_snapshot().get("save_count", 0)) != save_count:
		failures.append("unchanged values should not rewrite settings")
	var fresh = StoreScript.new(registry, TEST_PATH)
	if fresh.value("theme.name") != "plain" or fresh.value("controls_help.show_keyboard_hints") != false or absf(float(fresh.value("replay.playback_speed")) - 1.5) > 0.001:
		failures.append("persistent enum, bool, and numeric values should round-trip")
	if fresh.value("diagnostics.show_layout_bounds") != false:
		failures.append("session-only diagnostics should not round-trip")
	var payload = JSON.parse_string(_read_file())
	if not (payload is Dictionary) or int(payload.get("schema_version", 0)) != 2:
		failures.append("saved settings should use schema version 2 JSON")
	else:
		var saved: Dictionary = payload.get("settings", {})
		if saved.size() != registry.persistent_specs().size():
			failures.append("canonical file should contain every and only persistent registry key")
		for forbidden in ["score", "lines", "board_state", "active_cells", "locked_cells", "paused", "game_over", "topology", "native_trace_state"]:
			if saved.has(forbidden): failures.append("settings file must exclude semantic state %s" % forbidden)
	_test_invalid_inputs(failures, registry)
	_test_schema_representations(failures, registry)
	_test_failure_safe_replacement(failures, registry)
	_write_file(JSON.stringify({"schema_version": 1, "settings": {"theme.name": "plain", "interface.show_onboarding": false}}))
	var migrated = StoreScript.new(registry, TEST_PATH)
	if migrated.deterministic_snapshot().get("load_state") != "migrated_v1" or migrated.value("theme.name") != "plain":
		failures.append("Stage 48 schema should migrate valid preferences in memory")
	if migrated.value("display.ui_scale") != "standard" or migrated.value("interface.show_onboarding") != false:
		failures.append("Stage 48 migration should default new fields without resetting onboarding")
	_write_file(JSON.stringify({"schema_version": 1, "settings": {"theme.name": "plain", "controls_help.show_keyboard_hints": "wrong", "unknown.key": true}}))
	var partial = StoreScript.new(registry, TEST_PATH)
	if partial.value("theme.name") != "plain" or partial.value("controls_help.show_keyboard_hints") != true:
		failures.append("partially valid files should preserve valid values and default invalid values")
	if not _diagnostics_contain(partial, "unknown") or not _diagnostics_contain(partial, "Invalid setting"):
		failures.append("partial recovery should report unknown and invalid values")
	partial.set_value("theme.name", "diagnostic")
	partial.set_value("interface.show_onboarding", false)
	if not partial.reset_to_defaults():
		failures.append("reset should save registry defaults")
	var reset_store = StoreScript.new(registry, TEST_PATH)
	if reset_store.value("theme.name") != "tron" or reset_store.value("interface.show_onboarding") != true:
		failures.append("reset defaults should survive reopening")
	_cleanup()
	return failures


func _test_invalid_inputs(failures: Array, registry) -> void:
	for case in [
		{"text": "{broken", "diagnostic": "malformed"},
		{"text": "[]", "diagnostic": "root"},
		{"text": JSON.stringify({"schema_version": 2}), "diagnostic": "values"},
		{"text": JSON.stringify({"schema_version": 2, "settings": []}), "diagnostic": "values"},
		{"text": JSON.stringify({"schema_version": 99, "settings": {}}), "diagnostic": "schema"},
	]:
		_write_file(str(case.get("text")))
		var original := _read_file()
		var store = StoreScript.new(registry, TEST_PATH)
		if store.value("theme.name") != "tron" or not _diagnostics_contain(store, str(case.get("diagnostic"))):
			failures.append("invalid settings case should recover with readable %s diagnostic" % case.get("diagnostic"))
		if _read_file() != original:
			failures.append("recovery should not rewrite malformed or unsupported input automatically")


func _test_schema_representations(failures: Array, registry) -> void:
	for case in [
		{"label": "schema 1 integer", "value": 1, "load_state": "migrated_v1"},
		{"label": "schema 2 integer", "value": 2, "load_state": "loaded"},
		{"label": "schema 1 integral number", "value": 1.0, "load_state": "migrated_v1"},
		{"label": "schema 2 integral number", "value": 2.0, "load_state": "loaded"},
	]:
		_write_file(JSON.stringify({"schema_version": case.get("value"), "settings": {"theme.name": "plain"}}))
		var store = StoreScript.new(registry, TEST_PATH)
		if store.deterministic_snapshot().get("load_state") != case.get("load_state") or store.value("theme.name") != "plain":
			failures.append("%s should be accepted exactly" % case.get("label"))
	for case in [
		{"label": "fractional schema 1", "value": 1.5},
		{"label": "fractional schema 2", "value": 2.5},
		{"label": "numeric string", "value": "2"},
		{"label": "boolean", "value": true},
		{"label": "null", "value": null},
		{"label": "array", "value": [2]},
		{"label": "object", "value": {"value": 2}},
	]:
		_write_file(JSON.stringify({"schema_version": case.get("value"), "settings": {"theme.name": "plain"}}))
		var original := _read_file()
		var store = StoreScript.new(registry, TEST_PATH)
		if store.deterministic_snapshot().get("load_state") != "recovered_defaults" or store.value("theme.name") != "tron":
			failures.append("%s should be rejected" % case.get("label"))
		if _read_file() != original:
			failures.append("%s rejection should not rewrite input" % case.get("label"))


func _test_failure_safe_replacement(failures: Array, registry) -> void:
	_test_successful_existing_replacement(failures, registry)
	_test_failure_before_existing_file_changes(failures, registry)
	_test_failure_after_backup_restores_previous_file(failures, registry)
	_test_restore_copy_fallback(failures, registry)


func _test_successful_existing_replacement(failures: Array, registry) -> void:
	_write_valid_settings("tron")
	_write_file_at("%s.bak" % TEST_PATH, "stale backup")
	var store = StoreScript.new(registry, TEST_PATH)
	if not store.set_value("theme.name", "plain"):
		failures.append("existing settings file replacement should report a changed setting")
	if _saved_theme() != "plain":
		failures.append("successful replacement should install the new settings file")
	if int(store.deterministic_snapshot().get("save_count", 0)) != 1:
		failures.append("successful replacement should increment save count exactly once")
	if _path_exists("%s.tmp" % TEST_PATH) or _path_exists("%s.bak" % TEST_PATH):
		failures.append("successful replacement should clean temporary and backup files")


func _test_failure_before_existing_file_changes(failures: Array, registry) -> void:
	_write_valid_settings("tron")
	var original := _read_file()
	var ops := InjectedReplacementOps.new()
	ops.rename_failures = {1: ERR_CANT_CREATE, 2: ERR_CANT_CREATE}
	var store = StoreScript.new(registry, TEST_PATH, ops)
	store.set_value("theme.name", "plain")
	if _read_file() != original:
		failures.append("failure before backup should leave the existing settings file unchanged")
	if int(store.deterministic_snapshot().get("save_count", 0)) != 0:
		failures.append("failed replacement before backup must not increment save count")
	if not _diagnostics_contain(store, "not modified") or _diagnostics_contain(store, "saved automatically"):
		failures.append("failed replacement before backup should report failure without success")
	if _path_exists("%s.tmp" % TEST_PATH) or _path_exists("%s.bak" % TEST_PATH):
		failures.append("failure before backup should clean temporary artifacts")


func _test_failure_after_backup_restores_previous_file(failures: Array, registry) -> void:
	_write_valid_settings("tron")
	var original := _read_file()
	var ops := InjectedReplacementOps.new()
	ops.rename_failures = {1: ERR_CANT_CREATE, 3: ERR_CANT_CREATE}
	var store = StoreScript.new(registry, TEST_PATH, ops)
	store.set_value("theme.name", "plain")
	if _read_file() != original:
		failures.append("failed installation after backup should restore the previous settings file")
	if int(store.deterministic_snapshot().get("save_count", 0)) != 0:
		failures.append("failed installation after backup must not increment save count")
	if not _diagnostics_contain(store, "restored") or _diagnostics_contain(store, "saved automatically"):
		failures.append("restored replacement failure should report restoration without success")
	if _path_exists("%s.tmp" % TEST_PATH) or _path_exists("%s.bak" % TEST_PATH):
		failures.append("restored replacement failure should clean temporary and backup files")


func _test_restore_copy_fallback(failures: Array, registry) -> void:
	_write_valid_settings("tron")
	var original := _read_file()
	var ops := InjectedReplacementOps.new()
	ops.rename_failures = {1: ERR_CANT_CREATE, 3: ERR_CANT_CREATE, 4: ERR_CANT_CREATE}
	var store = StoreScript.new(registry, TEST_PATH, ops)
	store.set_value("theme.name", "plain")
	if ops.copy_count != 1 or _read_file() != original:
		failures.append("copy fallback should restore previous settings when restore rename fails")
	if int(store.deterministic_snapshot().get("save_count", 0)) != 0:
		failures.append("copy-restored replacement failure must not increment save count")
	if not _diagnostics_contain(store, "restored") or _diagnostics_contain(store, "saved automatically"):
		failures.append("copy-restored failure should report restoration without success")
	if _path_exists("%s.tmp" % TEST_PATH) or _path_exists("%s.bak" % TEST_PATH):
		failures.append("copy-restored failure should clean temporary and backup files")


func _write_valid_settings(theme_name: String) -> void:
	_write_file(JSON.stringify({"schema_version": 2, "settings": {"theme.name": theme_name}}))


func _saved_theme() -> String:
	var payload = JSON.parse_string(_read_file())
	return str(payload.get("settings", {}).get("theme.name", "")) if payload is Dictionary else ""


func _path_exists(path: String) -> bool:
	return FileAccess.file_exists(path)


func _diagnostics_contain(store, fragment: String) -> bool:
	for diagnostic in store.diagnostics():
		if str(diagnostic).to_lower().find(fragment.to_lower()) >= 0:
			return true
	return false


func _write_file(text: String) -> void:
	_write_file_at(TEST_PATH, text)


func _write_file_at(path: String, text: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(text)
	file.close()


func _read_file() -> String:
	var file := FileAccess.open(TEST_PATH, FileAccess.READ)
	return file.get_as_text() if file != null else ""


func _cleanup() -> void:
	for path in [TEST_PATH, "%s.tmp" % TEST_PATH, "%s.bak" % TEST_PATH]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
