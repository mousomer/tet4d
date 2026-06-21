extends RefCounted

const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")


func run() -> Array:
	var failures: Array = []
	var manager = ShellStyleManagerScript.new()
	_assert_equal(failures, manager.get_theme_id(), "tron", "active theme should default to tron")
	_assert_color(failures, manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY), "default accent")
	manager.set_theme("plain")
	_assert_equal(failures, manager.get_theme_id(), "plain", "set_theme plain")
	manager.set_theme("diagnostic")
	_assert_equal(failures, manager.get_theme_id(), "diagnostic", "set_theme diagnostic")
	var emissions := []
	manager.theme_changed.connect(func(theme_id: String) -> void:
		emissions.append(theme_id)
	)
	manager.set_theme("tron")
	_assert_equal(failures, manager.get_theme_id(), "tron", "set_theme tron")
	if emissions != ["tron"]:
		failures.append("theme_changed should emit once for valid change, got %s" % emissions)
	manager.set_theme("missing")
	_assert_equal(failures, manager.get_theme_id(), "tron", "unknown theme should fall back to tron")
	_assert_color(failures, manager.get_color("not.a.role"), "unknown role fallback")
	return failures


func _assert_color(failures: Array, color: Color, label: String) -> void:
	if color.a <= 0.0:
		failures.append("%s should return a visible Color" % label)


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
