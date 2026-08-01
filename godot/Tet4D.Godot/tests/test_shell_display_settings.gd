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
		"camera.sensitivity": "standard",
		"camera.invert_y": false,
	}
	for setting_id in expected_defaults:
		if store.value(setting_id) != expected_defaults[setting_id]:
			failures.append("%s should use its bounded Stage 51 default" % setting_id)
	if PreferencesScript.window_mode_value(Window.MODE_WINDOWED) != PreferencesScript.WINDOWED:
		failures.append("windowed OS state should canonicalize to the persistent windowed preference")
	if PreferencesScript.window_mode_value(Window.MODE_FULLSCREEN) != PreferencesScript.FULLSCREEN or PreferencesScript.window_mode_value(Window.MODE_EXCLUSIVE_FULLSCREEN) != PreferencesScript.FULLSCREEN:
		failures.append("fullscreen OS states should canonicalize to the persistent fullscreen preference")
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
		["camera.sensitivity", "high"],
		["camera.invert_y", true],
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
		["camera.sensitivity", "high"],
		["camera.invert_y", true],
	]:
		if fresh.value(str(setting_change[0])) != setting_change[1]:
			failures.append("%s should survive a schema-v2 reopen" % setting_change[0])
	if not fresh.set_value("display.window_mode", "windowed"):
		failures.append("returning from fullscreen should persist windowed mode")
	var reopened_windowed = StoreScript.new(registry, TEST_PATH)
	if reopened_windowed.value("display.window_mode") != "windowed":
		failures.append("windowed mode should survive a settings-store restart")
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
			"accessibility.high_contrast": true,
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
	if partial.value("accessibility.high_contrast") != true:
		failures.append("valid accessibility fields should survive invalid display fields")
	partial.set_value("theme.name", "plain")
	partial.set_value("accessibility.show_help_hints", false)
	partial.set_value("replay.playback_speed", 2.0)
	if not partial.reset_categories_to_defaults(["display", "theme", "camera"]):
		failures.append("display reset should persist canonical category defaults")
	var reset = StoreScript.new(registry, TEST_PATH)
	if reset.value("theme.name") != "plain" or reset.value("display.hud_density") != "standard" or reset.value("camera.invert_y") != false:
		failures.append("display reset should restore display, theme, and camera defaults")
	if reset.value("accessibility.show_help_hints") != false or reset.value("accessibility.high_contrast") != true or reset.value("interface.show_onboarding") != false or reset.value("replay.playback_speed") != 2.0:
		failures.append("display reset must preserve help, onboarding, and replay preferences")
	_write_json(TEST_PATH, {
		"schema_version": 3,
		"settings": {
			"display.ui_scale": "large",
			"camera.invert_y": true,
			"accessibility.high_contrast": "yes",
			"accessibility.reduced_motion": 1,
			"accessibility.show_help_hints": false,
			"interface.show_onboarding": false,
			"replay.loop_enabled": false,
		},
	})
	var accessibility_partial = StoreScript.new(registry, TEST_PATH)
	if accessibility_partial.value("display.ui_scale") != "large" or accessibility_partial.value("camera.invert_y") != true:
		failures.append("valid display fields should survive invalid accessibility fields")
	if accessibility_partial.value("accessibility.high_contrast") != false or accessibility_partial.value("accessibility.reduced_motion") != false:
		failures.append("string and numeric accessibility booleans should fall back independently")
	if accessibility_partial.value("accessibility.show_help_hints") != false:
		failures.append("valid accessibility siblings should survive invalid accessibility fields")
	accessibility_partial.set_value("accessibility.high_contrast", true)
	if not accessibility_partial.reset_categories_to_defaults(["accessibility"], "Accessibility settings"):
		failures.append("accessibility reset should persist canonical accessibility defaults")
	var accessibility_reset = StoreScript.new(registry, TEST_PATH)
	if accessibility_reset.value("accessibility.high_contrast") != false or accessibility_reset.value("accessibility.reduced_motion") != false or accessibility_reset.value("accessibility.show_help_hints") != true:
		failures.append("accessibility reset should restore only accessibility defaults")
	if accessibility_reset.value("display.ui_scale") != "large" or accessibility_reset.value("camera.invert_y") != true or accessibility_reset.value("interface.show_onboarding") != false or accessibility_reset.value("replay.loop_enabled") != false:
		failures.append("accessibility reset must preserve display, camera, onboarding, and replay preferences")

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
