extends RefCounted

const Probe = preload("res://tests/support/panel_responsive_probe.gd")
const SIZES := [Vector2i(1512, 982), Vector2i(1440, 900), Vector2i(1280, 720), Vector2i(1024, 640), Vector2i(800, 500)]
var capture_dir := ""
var exercise_fullscreen := false
var observations: Array = []
var sizes: Array = SIZES
var scales: Array = ["standard", "extra_large"]
var completed := false


func run() -> Array:
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	var original_scale := tree.root.content_scale_size
	var original_minimum := tree.root.min_size
	var scene := load("res://scenes/designer_bootstrap.tscn") as PackedScene
	var instance := scene.instantiate() as Control
	tree.root.add_child(instance)
	var probe := Probe.new()
	probe.capture_dir = capture_dir
	await probe.settle(tree)
	var hud = instance.get_node("ReplayHud")
	var app = instance.get_node("App")
	app.set_process(false)
	var settings_directory := DirAccess.create_temp("tet4d-panel-responsiveness")
	var settings_path := settings_directory.get_current_dir().path_join("settings.json")
	hud._settings_store._storage_path = settings_path
	# User settings may start the product in fullscreen. Real-window resize
	# requests are ignored in that mode, so establish a windowed matrix first.
	if DisplayServer.get_name() != "headless":
		tree.root.mode = Window.MODE_WINDOWED
		await probe.settle(tree, 120)
	hud._set_onboarding_visible(false)
	var failures: Array = []
	# Exercise below the normal desktop window floor: that is the required
	# scroll-fallback stress case, including externally constrained viewports.
	tree.root.min_size = Vector2i.ZERO
	for size in sizes:
		print("Panel responsiveness matrix: %s" % size)
		await probe.resize(tree, size)
		observations.append({"requested_logical_size": str(size), "backing_pixels": str(tree.root.size), "display_scale": DisplayServer.screen_get_scale(), "actual_logical_size": str(Vector2(tree.root.size) / maxf(DisplayServer.screen_get_scale(), 1.0)), "usable_viewport": str(tree.root.get_visible_rect())})
		for scale_id in scales:
			hud._apply_ui_scale(scale_id)
			for screen in ["main_menu", "advanced", "settings", "controls", "about", "browser", "diagnostics"]:
				hud.show_screen(screen)
				await probe.settle(tree)
				if scale_id == "standard" and size.x >= 1280 and size.y >= 720 and screen in ["main_menu", "advanced"]:
					var scroll: ScrollContainer = hud._menu_scroll_for_current_screen()
					if scroll != null and scroll.get_v_scroll_bar().visible:
						failures.append("%s/%s must reflow and compact to fit without scrolling at standard UI scale" % [size, screen])
				failures.append_array(await probe.inspect(tree, hud._screens[screen], "%s/%s/%s" % [size, scale_id, screen]))
			for mode in ["live_2d", "live_3d", "live_4d"]:
				hud.open_game_setup(mode)
				await probe.settle(tree)
				failures.append_array(await probe.inspect(tree, hud._game_setup_screen, "%s/%s/setup/%s" % [size, scale_id, mode]))
			hud.open_design_laboratory()
			await probe.settle(tree)
			failures.append_array(await probe.inspect(tree, hud._design_laboratory, "%s/%s/design-laboratory" % [size, scale_id]))
			hud._design_laboratory.close()
			for mode in ["live_2d", "live_3d", "live_4d"]:
				app._start_configured_live_game(hud.configured_live_setup(mode))
				hud._set_onboarding_visible(true)
				await probe.settle(tree)
				failures.append_array(await probe.inspect(tree, hud._live_cockpit.header_slot, "%s/%s/guide/%s" % [size, scale_id, mode]))
				await probe.settle_cockpit(tree, hud._live_cockpit)
				failures.append_array(probe.inspect_cockpit(hud._live_cockpit, "%s/%s/cockpit+guide/%s" % [size, scale_id, mode]))
				hud._set_onboarding_visible(false)
				await probe.settle(tree)
				await probe.settle_cockpit(tree, hud._live_cockpit)
				# Normal play, guide closed: the helper allocation a player actually sees.
				await probe.capture(tree, "%s/%s/cockpit/%s" % [size, scale_id, mode])
				failures.append_array(probe.inspect_cockpit(hud._live_cockpit, "%s/%s/cockpit/%s" % [size, scale_id, mode]))
				var board_before: Vector2 = hud.board_viewport_size()
				var helper_before: Dictionary = hud._piece_control_strip.deterministic_snapshot()
				hud._open_presentation_designer()
				await probe.settle(tree)
				for checkbox in hud._presentation_designer.find_children("*", "CheckBox", true, false):
					if checkbox.get_theme_color("font_color") != hud.style_manager().get_color("text.primary"):
						failures.append("Rebuilt Designer controls must retain readable shell text colours")
				failures.append_array(await probe.inspect(tree, hud._presentation_designer, "%s/%s/designer/%s" % [size, scale_id, mode]))
				for frame in hud._live_cockpit.designer_panels().values():
					if frame.content.name == "GameArea":
						continue
					failures.append_array(await probe.inspect(tree, frame, "%s/%s/helper/%s/%s" % [size, scale_id, mode, frame.content.name]))
				if mode == "live_4d":
					for dialog in [hud._presentation_designer._delete_confirmation, hud._presentation_designer._overwrite_confirmation, hud._presentation_designer._import_dialog, hud._presentation_designer._export_dialog]:
						dialog.popup_centered()
						await probe.settle(tree)
						var bounds := Rect2(Vector2.ZERO, tree.root.get_visible_rect().size) if dialog.is_embedded() else Rect2(Vector2(tree.root.position), Vector2(tree.root.size))
						var context := "%s/%s/dialog/%s" % [size, scale_id, dialog.title]
						if not bounds.grow(1.0).encloses(Rect2(Vector2(dialog.position), Vector2(dialog.size))):
							failures.append("%s popup escapes application client area" % context)
						for child in dialog.get_children(true):
							if child is Control and child.is_visible_in_tree():
								failures.append_array(await probe.inspect(tree, child, context))
								break
						dialog.hide()
				hud._presentation_designer.hide_preserving_preview()
				await probe.settle(tree)
				await probe.settle_cockpit(tree, hud._live_cockpit)
				if hud.board_viewport_size().distance_to(board_before) > 1.0:
					failures.append("%s/%s/%s closing helper overlay must restore board allocation: %s -> %s" % [size, scale_id, mode, board_before, hud.board_viewport_size()])
				var helper_after: Dictionary = hud._piece_control_strip.deterministic_snapshot()
				if helper_after.layout != helper_before.layout or helper_after.row_ids != helper_before.row_ids:
					failures.append("%s/%s closing Designer must restore the normal legend layout and every action" % [size, mode])
	# A fixed width isolates vertical invalidation from width/profile changes.
	for height in [900, 500, 900]:
		await probe.resize(tree, Vector2i(1280, height))
		hud.show_screen("settings")
		await probe.settle(tree)
		failures.append_array(await probe.inspect(tree, hud._settings_screen, "height-only 1280x%s" % height))
	if exercise_fullscreen:
		for window_mode in [Window.MODE_WINDOWED, Window.MODE_FULLSCREEN, Window.MODE_WINDOWED]:
			tree.root.mode = window_mode
			# macOS fullscreen transitions animate asynchronously. Wait for actual
			# window bounds to stop changing, then observe the usable viewport.
			for _frame in range(120):
				await tree.process_frame
			for screen in ["settings", "controls", "main_menu"]:
				hud.show_screen(screen)
				await probe.settle(tree)
				var context := "actual-mode-%s/%s" % [window_mode, screen]
				failures.append_array(await probe.inspect(tree, hud._screens[screen], context))
			for mode in ["live_2d", "live_3d", "live_4d"]:
				hud.open_game_setup(mode)
				await probe.settle(tree)
				failures.append_array(await probe.inspect(tree, hud._game_setup_screen, "actual-mode-%s/setup/%s" % [window_mode, mode]))
				app._start_configured_live_game(hud.configured_live_setup(mode))
				hud._set_onboarding_visible(true)
				await probe.settle(tree)
				failures.append_array(await probe.inspect(tree, hud._live_cockpit.header_slot, "actual-mode-%s/guide/%s" % [window_mode, mode]))
				hud._set_onboarding_visible(false)
				hud._open_presentation_designer()
				await probe.settle(tree)
				failures.append_array(await probe.inspect(tree, hud._presentation_designer, "actual-mode-%s/designer/%s" % [window_mode, mode]))
				hud._presentation_designer.hide_preserving_preview()
			hud.open_design_laboratory()
			await probe.settle(tree)
			failures.append_array(await probe.inspect(tree, hud._design_laboratory, "actual-mode-%s/laboratory" % window_mode))
			hud._design_laboratory.close()
			observations.append({"window_mode": window_mode, "backing_pixels": str(DisplayServer.window_get_size()), "display_scale": DisplayServer.screen_get_scale(), "usable_viewport": str(tree.root.get_visible_rect()), "screen_usable_rect": str(DisplayServer.screen_get_usable_rect())})
	observations.append_array(probe.observations)
	instance.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	tree.root.content_scale_size = original_scale
	tree.root.min_size = original_minimum
	ThemeDB.fallback_base_scale = 1.0
	for suffix in ["", ".bak"]:
		if FileAccess.file_exists(settings_path + suffix):
			DirAccess.remove_absolute(settings_path + suffix)
	completed = true
	return failures
