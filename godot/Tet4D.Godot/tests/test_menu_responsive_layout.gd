extends RefCounted

const HudScript = preload("res://scripts/ui/replay_hud.gd")


func run() -> Array:
	var failures: Array = []
	for sample in [
		[Vector2(720, 600), 1.0],
		[Vector2(1280, 720), 1.0],
		[Vector2(1600, 900), 1.25],
		[Vector2(1920, 1080), 1.5],
		[Vector2(1920, 720), 1.0],
		[Vector2(3840, 2160), 2.0],
	]:
		if not is_equal_approx(HudScript.menu_window_scale(sample[0]), sample[1]):
			failures.append("menu scale must follow the tighter axis, preserve compact text, and cap at 2x: %s" % sample[0])
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	var original_content_scale_size := tree.root.content_scale_size
	var scene := load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene
	var instance := scene.instantiate() as Control
	tree.root.add_child(instance)
	await _settle(tree)
	var hud = instance.get_node("ReplayHud")
	var play := hud.find_child("CommandCard__Play", true, false) as Button
	var title := hud.find_child("MainMenuTitle", true, false) as Label
	var main_scroll := hud.find_child("MainMenuScroll", true, false) as ScrollContainer
	if tree.root.gui_get_focus_owner() != play or main_scroll.scroll_vertical != 0:
		failures.append("default project startup must focus Play at the top of the menu")
	if not main_scroll.get_global_rect().encloses(play.get_global_rect()) or not main_scroll.get_global_rect().encloses(title.get_global_rect()):
		failures.append("startup must show the title and the complete focused Play action")
	hud._set_onboarding_visible(false)
	hud._apply_ui_scale("standard")
	for screen in [HudScript.SCREEN_MAIN_MENU, HudScript.SCREEN_ADVANCED]:
		hud.show_screen(screen)
		var panel_name := "MainMenuScrollPanel" if screen == HudScript.SCREEN_MAIN_MENU else "AdvancedMenuScrollPanel"
		var panel := hud.find_child(panel_name, true, false) as PanelContainer
		var button_name := "CommandCard__Play" if screen == HudScript.SCREEN_MAIN_MENU else "CommandCard__Replay_Demos"
		var command := hud.find_child(button_name, true, false) as Button
		await _resize(tree, Vector2i(1280, 720))
		var opening_text_scale := (tree.root.get_final_transform() * command.get_global_transform_with_canvas()).get_scale().x
		await _resize(tree, Vector2i(1600, 900))
		if DisplayServer.get_name() != "headless":
			var growth := (tree.root.get_final_transform() * command.get_global_transform_with_canvas()).get_scale().x / opening_text_scale
			if absf(growth - 1.25) > 0.02:
				failures.append("%s rendered text must grow 25%% on a same-aspect 1280x720 to 1600x900 resize, got %s" % [screen, growth])
		await _resize(tree, Vector2i(960, 720))
		var compact_width := panel.size.x
		await _resize(tree, Vector2i(1600, 1200))
		if panel.size.x <= compact_width:
			failures.append("%s menu panel must grow with the window width" % screen)
		# Stay inside a laptop display's usable height; the OS clamps oversized
		# real windows, so 1200-to-1600 heights would test the same window twice.
		await _resize(tree, Vector2i(960, 720))
		# A long menu's panel already exceeds the window; its visible scroll
		# surface must grow even when the content's minimum height stays fixed.
		var menu_surface := panel.get_parent().get_parent() as ScrollContainer
		var standard_height := menu_surface.size.y
		await _resize(tree, Vector2i(960, 900))
		if menu_surface.size.y <= standard_height:
			failures.append("%s menu scroll surface must use additional available window height" % screen)
		if command.get_theme_font_size("font_size") < 24:
			failures.append("%s command text must meet the 24px body target" % screen)
		await _resize(tree, Vector2i(720, 600))
		hud._apply_ui_scale("extra_large")
		await _settle(tree)
		var scroll := panel.get_parent().get_parent() as ScrollContainer
		var quit_or_back := hud.find_child("QuitApplicationButton" if screen == HudScript.SCREEN_MAIN_MENU else "CommandCard__Back_to_Main_Menu", true, false) as Button
		quit_or_back.grab_focus()
		await _settle(tree)
		# Resize with the last row focused: container sorting must retain reachability.
		await _resize(tree, Vector2i(760, 620))
		var scroll_rect := scroll.get_global_rect()
		var button_rect := quit_or_back.get_global_rect()
		if not hud.get_viewport_rect().grow(1.0).encloses(scroll_rect):
			failures.append("%s compact menu scroll surface must fit the actual viewport at maximum UI scale: %s in %s" % [screen, scroll_rect, hud.get_viewport_rect()])
		if not scroll_rect.grow(1.0).encloses(button_rect):
			failures.append("%s compact menu must scroll the final focused action fully into view: %s in %s" % [screen, button_rect, scroll_rect])
		if panel.get_global_rect().end.x > scroll_rect.end.x + 1.0:
			failures.append("%s compact menu must wrap text without horizontal overflow" % screen)
		# Layout repair must not continuously snap manual scrolling to focus.
		scroll.scroll_vertical = 0
		await _settle(tree)
		if scroll.scroll_vertical != 0:
			failures.append("%s menu must preserve manual scrolling when layout is stable" % screen)
		hud._apply_ui_scale("standard")
	await _resize(tree, Vector2i(1600, 900))
	hud.show_screen(HudScript.SCREEN_VIEWER)
	await _settle(tree)
	if DisplayServer.get_name() != "headless":
		var points := Vector2(DisplayServer.window_get_size()) / DisplayServer.screen_get_scale()
		if not Vector2(tree.root.content_scale_size).is_equal_approx(points):
			failures.append("returning to live/replay must restore the existing point-sized responsive canvas")
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
