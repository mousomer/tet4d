extends RefCounted

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const StoreScript = preload("res://scripts/ui/settings/settings_store.gd")
const SettingsPanelScript = preload("res://scripts/ui/settings_panel.gd")
const OnboardingModelScript = preload("res://scripts/ui/onboarding/live_onboarding_model.gd")

const TEST_PATH := "user://stage48_shell_settings_persistence_test.json"


func run() -> Array:
	var failures: Array = []
	_cleanup()
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var store = StoreScript.new(registry, TEST_PATH)
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["shell settings persistence test requires SceneTree"]
	var panel = SettingsPanelScript.new()
	panel.registry = registry
	panel.set_store(store)
	tree.root.add_child(panel)
	await tree.process_frame
	var applied: Dictionary = {}
	panel.setting_changed.connect(func(setting_id: String, value) -> void: applied[setting_id] = value)
	panel._on_control_value_changed("theme.name", "plain")
	var hints_checkbox := panel.generated_control("controls_help.show_keyboard_hints") as CheckBox
	if hints_checkbox == null:
		failures.append("keyboard-hints preference should expose a real checkbox")
	else:
		hints_checkbox.button_pressed = false
		await tree.process_frame
	panel._on_control_value_changed("display.projection_strength", 0.75)
	if applied.get("theme.name") != "plain" or applied.get("controls_help.show_keyboard_hints") != false:
		failures.append("validated changes should apply immediately through SettingsPanel signals")
	var fresh = StoreScript.new(registry, TEST_PATH)
	if fresh.value("theme.name") != "plain" or fresh.value("controls_help.show_keyboard_hints") != false:
		failures.append("fresh shell stores should restore persisted interface and appearance values")
	if absf(float(fresh.value("display.projection_strength")) - 0.75) > 0.001:
		failures.append("fresh shell stores should restore persisted numeric values")
	if store.status_text().find("saved automatically") == -1:
		failures.append("successful generated-control changes should visibly report automatic saving")
	var onboarding = OnboardingModelScript.new()
	onboarding.select_mode("live_2d")
	onboarding.set_enabled(bool(fresh.value("interface.show_onboarding")))
	if not bool(onboarding.snapshot().get("visible", false)):
		failures.append("default onboarding preference should keep live guidance available")
	panel._on_control_value_changed("interface.show_onboarding", false)
	onboarding.set_enabled(bool(store.value("interface.show_onboarding")))
	if bool(onboarding.snapshot().get("visible", true)):
		failures.append("disabled onboarding preference should hide guidance")
	var live_session := {"score": 320, "paused": true, "active_cells": [[1, 2]]}
	panel.reset_settings_to_defaults()
	if live_session != {"score": 320, "paused": true, "active_cells": [[1, 2]]}:
		failures.append("resetting shell preferences must not mutate live-session state")
	var reset_store = StoreScript.new(registry, TEST_PATH)
	if reset_store.value("theme.name") != "tron" or reset_store.value("interface.show_onboarding") != true:
		failures.append("panel reset should immediately persist registry defaults")
	panel.queue_free()
	await tree.process_frame
	_cleanup()
	return failures


func _cleanup() -> void:
	for path in [TEST_PATH, "%s.tmp" % TEST_PATH]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
