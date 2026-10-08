extends RefCounted

const HudScript = preload("res://scripts/ui/replay_hud.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	var original_content_scale_size := tree.root.content_scale_size
	var scene := load("res://scenes/game_bootstrap.tscn") as PackedScene
	var instance := scene.instantiate() as Control
	tree.root.add_child(instance)
	await _settle(tree)
	var hud = instance.get_node("ReplayHud")
	hud._set_onboarding_visible(false)
	hud._apply_ui_scale("standard")
	for screen in [HudScript.SCREEN_MAIN_MENU, HudScript.SCREEN_ADVANCED]:
		hud.show_screen(screen)
		var panel_name := "MainMenuScrollPanel" if screen == HudScript.SCREEN_MAIN_MENU else "AdvancedMenuScrollPanel"
		var panel := hud.find_child(panel_name, true, false) as PanelContainer
		var button_name := "CommandCard__Play" if screen == HudScript.SCREEN_MAIN_MENU else "CommandCard__Replay_Demos"
		var command := hud.find_child(button_name, true, false) as Button
		await _resize(tree, Vector2i(960, 720))
		var compact_width := panel.size.x
		await _resize(tree, Vector2i(1600, 1200))
		if panel.size.x <= compact_width:
			failures.append("%s menu panel must grow with the window width" % screen)
		# Compare height at the same width: larger text wraps more in the
		# compact window, so its natural content height can exceed a wider one.
		var standard_height := panel.size.y
		await _resize(tree, Vector2i(1600, 1600))
		if panel.size.y <= standard_height:
			failures.append("%s menu panel must use additional available window height" % screen)
		if command.get_theme_font_size("font_size") < 24:
			failures.append("%s command text must meet the 24px body target" % screen)
		await _resize(tree, Vector2i(720, 600))
		hud._apply_ui_scale("extra_large")
		await _settle(tree)
		var scroll := panel.get_parent().get_parent() as ScrollContainer
		var quit_or_back := hud.find_child("QuitApplicationButton" if screen == HudScript.SCREEN_MAIN_MENU else "CommandCard__Back_to_Main_Menu", true, false) as Button
		quit_or_back.grab_focus()
		await _settle(tree)
		var scroll_rect := scroll.get_global_rect()
		var button_rect := quit_or_back.get_global_rect()
		if not hud.get_viewport_rect().grow(1.0).encloses(scroll_rect):
			failures.append("%s compact menu scroll surface must fit the actual viewport at maximum UI scale: %s in %s" % [screen, scroll_rect, hud.get_viewport_rect()])
		if not scroll_rect.grow(1.0).encloses(button_rect):
			failures.append("%s compact menu must scroll the final focused action fully into view: %s in %s" % [screen, button_rect, scroll_rect])
		if panel.get_global_rect().end.x > scroll_rect.end.x + 1.0:
			failures.append("%s compact menu must wrap text without horizontal overflow" % screen)
		hud._apply_ui_scale("standard")
	for mode in ["plain", "tron", "diagnostic"]:
		hud.set_display_mode(mode)
		if hud.theme.default_font_size < 24:
			failures.append("%s theme must use readable default body text" % mode)
	instance.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	tree.root.content_scale_size = original_content_scale_size
	ThemeDB.fallback_base_scale = 1.0
	return failures


func _settle(tree: SceneTree) -> void:
	for frame in range(12):
		await tree.process_frame


func _resize(tree: SceneTree, points: Vector2i) -> void:
	if DisplayServer.get_name() == "headless":
		tree.root.size = points
		# Headless has no physical resize signal to synchronize the design canvas.
		tree.root.content_scale_size = points
	else:
		DisplayServer.window_set_size(Vector2i(Vector2(points) * DisplayServer.screen_get_scale()))
	await _settle(tree)
