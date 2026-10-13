extends RefCounted

const HudScript = preload("res://scripts/ui/replay_hud.gd")


func run() -> Array:
	var failures: Array = []
	# Expected factors are the contract written out by hand: the tighter of
	# width/1280 and height/720, floored at the 18/24 readable-body ratio.
	for sample in [
		[Vector2(1280, 720), 1.0],
		[Vector2(1600, 900), 1.25],
		[Vector2(1920, 1080), 1.5],
		[Vector2(1920, 720), 1.0],
		[Vector2(3840, 2160), 2.0],
		# Width-only and height-only reductions from the reference.
		[Vector2(1120, 720), 0.875],
		[Vector2(1280, 600), 600.0 / 720.0],
		# Wide but short is held by height; narrow but tall by width.
		[Vector2(1920, 600), 600.0 / 720.0],
		[Vector2(1700, 560), 560.0 / 720.0],
		[Vector2(1120, 1000), 0.875],
		# Compact windows stop at the 18 px readable-body floor and reflow.
		[Vector2(720, 600), 0.75],
		[Vector2(600, 400), 0.75],
	]:
		if not is_equal_approx(HudScript.menu_window_scale(sample[0]), sample[1]):
			failures.append("menu scale must follow the tighter axis in both directions, floor at 18 px body text, and cap at 2x: %s gave %s, want %s" % [sample[0], HudScript.menu_window_scale(sample[0]), sample[1]])
	var reference_scale := HudScript.menu_window_scale(Vector2(1280, 720))
	if HudScript.menu_window_scale(Vector2(1280, 560)) >= reference_scale:
		failures.append("reducing only the window height must shrink menu text")
	if HudScript.menu_window_scale(Vector2(1000, 720)) >= reference_scale:
		failures.append("reducing only the window width must shrink menu text")
	if HudScript.menu_window_scale(Vector2(2400, 560)) > HudScript.menu_window_scale(Vector2(1280, 560)):
		failures.append("extra width must not enlarge menu text in a height-limited window")
	if HudScript.menu_window_scale(Vector2(1000, 1400)) > HudScript.menu_window_scale(Vector2(1000, 720)):
		failures.append("extra height must not enlarge menu text in a width-limited window")
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
		var opening_text_scale := _rendered_scale(tree, command)
		await _resize(tree, Vector2i(1600, 900))
		if DisplayServer.get_name() != "headless":
			var growth := _rendered_scale(tree, command) / opening_text_scale
			if absf(growth - 1.25) > 0.02:
				failures.append("%s rendered text must grow 25%% on a same-aspect 1280x720 to 1600x900 resize, got %s" % [screen, growth])
			# Headless pins the canvas to the window, so rendered typography is
			# only observable with a real window. Each step compares the on-screen
			# command font against the reference measurement, not against the
			# policy function, so an inert resize path cannot satisfy it.
			for step in [
				[Vector2i(1280, 560), 560.0 / 720.0, "height-only reduction"],
				[Vector2i(1040, 720), 1040.0 / 1280.0, "width-only reduction"],
				[Vector2i(1700, 560), 560.0 / 720.0, "wide but short window"],
				[Vector2i(1040, 960), 1040.0 / 1280.0, "narrow but tall window"],
				[Vector2i(720, 600), 0.75, "compact window at the readable floor"],
				[Vector2i(1280, 720), 1.0, "restored reference window"],
			]:
				await _resize(tree, step[0])
				var ratio := _rendered_scale(tree, command) / opening_text_scale
				if absf(ratio - float(step[1])) > 0.02:
					failures.append("%s %s must render menu text at %.3fx the reference, got %.3fx" % [screen, step[2], step[1], ratio])
			var restored_scale := _rendered_scale(tree, command)
			hud._apply_responsive_layout()
			await _settle(tree)
			if not is_equal_approx(_rendered_scale(tree, command), restored_scale) or not is_equal_approx(restored_scale, opening_text_scale):
				failures.append("%s repeated layout at the reference size must reproduce the opening typography" % screen)
			await _resize(tree, Vector2i(720, 600))
			var body_points := command.get_theme_font_size("font_size") * _rendered_scale(tree, command) / DisplayServer.screen_get_scale()
			if body_points < 18.0 - 0.01:
				failures.append("%s compact menu body text must stay at or above 18 points, got %s" % [screen, body_points])
		await _resize(tree, Vector2i(960, 720))
		# Same-aspect windows share one logical canvas, so growth is measured in
		# rendered pixels: what the player sees, not the logical layout extent.
		var compact_width := panel.size.x * _rendered_scale(tree, panel)
		await _resize(tree, Vector2i(1600, 1200))
		if panel.size.x * _rendered_scale(tree, panel) <= compact_width:
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
		var logical := points / HudScript.window_ui_scale(points)
		var expected := Vector2(ceil(logical.x), ceil(logical.y))
		if not Vector2(tree.root.content_scale_size).is_equal_approx(expected):
			failures.append("returning to live/replay must restore its taller responsive reference canvas")
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


func _rendered_scale(tree: SceneTree, control: Control) -> float:
	return (tree.root.get_final_transform() * control.get_global_transform_with_canvas()).get_scale().x


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
