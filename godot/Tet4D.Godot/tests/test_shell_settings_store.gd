extends RefCounted

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const StoreScript = preload("res://scripts/ui/settings/settings_store.gd")

const TEST_PATH := "user://stage48_shell_settings_store_test.json"


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
	if not (payload is Dictionary) or int(payload.get("schema_version", 0)) != 1:
		failures.append("saved settings should use schema version 1 JSON")
	else:
		var saved: Dictionary = payload.get("settings", {})
		if saved.size() != registry.persistent_specs().size():
			failures.append("canonical file should contain every and only persistent registry key")
		for forbidden in ["score", "lines", "board_state", "active_cells", "locked_cells", "paused", "game_over", "topology", "native_trace_state"]:
			if saved.has(forbidden): failures.append("settings file must exclude semantic state %s" % forbidden)
	_test_invalid_inputs(failures, registry)
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
		{"text": JSON.stringify({"schema_version": 1}), "diagnostic": "values"},
		{"text": JSON.stringify({"schema_version": 1, "settings": []}), "diagnostic": "values"},
		{"text": JSON.stringify({"schema_version": 99, "settings": {}}), "diagnostic": "schema"},
	]:
		_write_file(str(case.get("text")))
		var original := _read_file()
		var store = StoreScript.new(registry, TEST_PATH)
		if store.value("theme.name") != "tron" or not _diagnostics_contain(store, str(case.get("diagnostic"))):
			failures.append("invalid settings case should recover with readable %s diagnostic" % case.get("diagnostic"))
		if _read_file() != original:
			failures.append("recovery should not rewrite malformed or unsupported input automatically")


func _diagnostics_contain(store, fragment: String) -> bool:
	for diagnostic in store.diagnostics():
		if str(diagnostic).to_lower().find(fragment.to_lower()) >= 0:
			return true
	return false


func _write_file(text: String) -> void:
	var file := FileAccess.open(TEST_PATH, FileAccess.WRITE)
	file.store_string(text)
	file.close()


func _read_file() -> String:
	var file := FileAccess.open(TEST_PATH, FileAccess.READ)
	return file.get_as_text() if file != null else ""


func _cleanup() -> void:
	for path in [TEST_PATH, "%s.tmp" % TEST_PATH]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
