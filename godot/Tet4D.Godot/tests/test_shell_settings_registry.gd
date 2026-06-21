extends RefCounted

const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const SettingSpecScript = preload("res://scripts/ui/settings/setting_spec.gd")


func run() -> Array:
	var failures: Array = []
	var registry = SettingsRegistryScript.new()
	registry.load_from_path(SettingsRegistryScript.REGISTRY_PATH)
	failures.append_array(registry.validate())
	_assert_equal(failures, registry.categories.size(), 5, "Stage 29 category count")
	_assert_equal(failures, registry.settings.size(), 7, "Stage 29 setting count")
	var setting_ids: Array = []
	for spec in registry.settings:
		var setting_id: String = spec.id()
		if setting_ids.has(setting_id):
			failures.append("duplicate setting id %s" % setting_id)
		setting_ids.append(setting_id)
		if not SettingSpecScript.ALLOWED_CATEGORIES.has(spec.category()):
			failures.append("%s should use a known Stage 29 category" % setting_id)
		if SettingSpecScript.CONTROL_TYPE_BY_VALUE_TYPE.get(spec.value_type(), "") != spec.control_type():
			failures.append("%s should use required value/control mapping" % setting_id)
		if spec.authority() != "godot_shell":
			failures.append("%s should be editable only by godot_shell authority" % setting_id)
		for token in SettingSpecScript.FORBIDDEN_CATEGORY_TOKENS:
			if setting_id.find(token) >= 0 or spec.category().find(token) >= 0:
				failures.append("%s should not expose forbidden semantic token %s" % [setting_id, token])
		_validate_shape(failures, spec)
	_assert_has_setting(failures, registry, "replay.playback_speed")
	_assert_has_setting(failures, registry, "replay.loop_enabled")
	_assert_has_setting(failures, registry, "display.show_w_labels")
	_assert_has_setting(failures, registry, "display.projection_strength")
	_assert_has_setting(failures, registry, "theme.name")
	_assert_has_setting(failures, registry, "diagnostics.show_layout_bounds")
	_assert_has_setting(failures, registry, "controls_help.show_keyboard_hints")
	return failures


func _validate_shape(failures: Array, spec) -> void: # tet4d-semantic-boundary: allow test-fixture
	if spec.value_type() == "float" or spec.value_type() == "int":
		for field in ["min", "max", "step"]:
			if not spec.data.has(field):
				failures.append("%s numeric setting should define %s" % [spec.id(), field])
		var default_value := float(spec.default_value())
		if default_value < float(spec.data.get("min", 0.0)) or default_value > float(spec.data.get("max", 0.0)):
			failures.append("%s numeric default should be inside range" % spec.id())
	elif spec.value_type() == "enum":
		var options: Array = spec.data.get("options", [])
		if options.is_empty():
			failures.append("%s enum should define options" % spec.id())
		var values: Array = []
		for option in options:
			values.append(str(option.get("value", "")))
		if not values.has(str(spec.default_value())):
			failures.append("%s enum default should be one of its options" % spec.id())
	elif spec.value_type() == "bool" and typeof(spec.default_value()) != TYPE_BOOL:
		failures.append("%s bool default should be bool" % spec.id())
	elif spec.value_type() == "string" and typeof(spec.default_value()) != TYPE_STRING:
		failures.append("%s string default should be string" % spec.id())


func _assert_has_setting(failures: Array, registry, setting_id: String) -> void:
	if registry.get_spec(setting_id) == null:
		failures.append("missing setting %s" % setting_id)


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
