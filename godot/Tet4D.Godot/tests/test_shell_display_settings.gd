extends RefCounted

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const StoreScript = preload("res://scripts/ui/settings/settings_store.gd")
const PreferencesScript = preload("res://scripts/ui/settings/shell_presentation_preferences.gd")

const TEST_PATH := "user://stage51_shell_display_settings_test.json"
const GAME_SETUP_SENTINEL_PATH := "user://stage51_game_setup_sentinel.json"


func run() -> Array:
	var failures: Array = []
	_cleanup()
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var store = StoreScript.new(registry, TEST_PATH)
	var expected_defaults := {
		"display.window_mode": "windowed",
		"display.windowed_size": [1280, 720],
		"display.ui_scale": "standard",
		"display.hud_density": "standard",
		"display.board_detail": "standard",
		"accessibility.contrast_mode": "standard",
		"accessibility.animation_mode": "standard",
		"camera.sensitivity": "standard",
		"camera.invert_y": false,
		"controls_help.contextual_help": "automatic",
	}
	for setting_id in expected_defaults:
		if store.value(setting_id) != expected_defaults[setting_id]:
			failures.append("%s should use its bounded Stage 51 default" % setting_id)
	var mutable_size: Array = store.value("display.windowed_size")
	mutable_size[0] = 1
	if store.value("display.windowed_size") != [1280, 720]:
		failures.append("settings values should return safe copies of mutable window sizes")

	_write_json(GAME_SETUP_SENTINEL_PATH, {"setup": "untouched"})
	for setting_change in [
		["display.window_mode", "fullscreen"],
		["display.windowed_size", [1440, 900]],
		["display.ui_scale", "extra_large"],
		["display.hud_density", "detailed"],
		["display.board_detail", "full"],
		["accessibility.contrast_mode", "high"],
		["accessibility.animation_mode", "reduced"],
		["camera.sensitivity", "high"],
		["camera.invert_y", true],
		["controls_help.contextual_help", "hidden"],
	]:
		if not store.set_value(str(setting_change[0]), setting_change[1]):
			failures.append("%s should accept its canonical Stage 51 value" % setting_change[0])
	var fresh = StoreScript.new(registry, TEST_PATH)
	for setting_change in [
		["display.window_mode", "fullscreen"],
		["display.windowed_size", [1440, 900]],
		["display.ui_scale", "extra_large"],
		["display.hud_density", "detailed"],
		["display.board_detail", "full"],
		["accessibility.contrast_mode", "high"],
		["accessibility.animation_mode", "reduced"],
		["camera.sensitivity", "high"],
		["camera.invert_y", true],
		["controls_help.contextual_help", "hidden"],
	]:
		if fresh.value(str(setting_change[0])) != setting_change[1]:
			failures.append("%s should survive a schema-v2 reopen" % setting_change[0])
	if _read_json(GAME_SETUP_SENTINEL_PATH) != {"setup": "untouched"}:
		failures.append("shell display persistence must not touch game_setup storage")

	_write_json(TEST_PATH, {
		"schema_version": 2,
		"settings": {
			"display.ui_scale": "huge",
			"display.windowed_size": [320, 200],
			"display.hud_density": "compact",
			"camera.sensitivity": "low",
			"camera.invert_y": true,
			"interface.show_onboarding": false,
			"unknown.stage51": "ignored",
		},
	})
	var partial = StoreScript.new(registry, TEST_PATH)
	if partial.value("display.ui_scale") != "standard" or partial.value("display.windowed_size") != [1280, 720]:
		failures.append("invalid scale and window size should fall back independently")
	if partial.value("display.hud_density") != "compact" or partial.value("camera.sensitivity") != "low" or partial.value("camera.invert_y") != true:
		failures.append("valid siblings should survive invalid Stage 51 fields")
	if partial.value("interface.show_onboarding") != false:
		failures.append("field recovery must preserve the separate onboarding preference")

	var clamped := PreferencesScript.clamp_windowed_size(
		Vector2i(3000, 2000),
		Vector2i(634, 660),
		Rect2i(40, 20, 1600, 900)
	)
	if clamped != Vector2i(1600, 900):
		failures.append("remembered window size should clamp to the current usable display")
	var minimum := PreferencesScript.clamp_windowed_size(
		Vector2i(100, 100),
		Vector2i(634, 660),
		Rect2i(0, 0, 1600, 900)
	)
	if minimum != Vector2i(634, 660):
		failures.append("remembered window size should enforce the supported minimum")
	_cleanup()
	return failures


func _write_json(path: String, value) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(value))
	file.close()


func _read_json(path: String):
	var file := FileAccess.open(path, FileAccess.READ)
	return JSON.parse_string(file.get_as_text()) if file != null else null


func _cleanup() -> void:
	for path in [TEST_PATH, "%s.tmp" % TEST_PATH, GAME_SETUP_SENTINEL_PATH]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
