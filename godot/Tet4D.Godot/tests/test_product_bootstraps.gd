extends RefCounted

const GAME_SCENE := preload("res://scenes/game_bootstrap.tscn")
const DESIGNER_SCENE := preload("res://scenes/designer_bootstrap.tscn")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["product bootstrap test requires a SceneTree"]
	var launch_path := "user://test_product_bootstrap_launch_%d.cfg" % Time.get_ticks_usec()
	var game_root := GAME_SCENE.instantiate()
	game_root.get_node("App")._launch_view_path = launch_path
	tree.root.add_child(game_root)
	for _index in range(4):
		await tree.process_frame
	var game_app = game_root.get_node_or_null("App")
	if game_app == null:
		failures.append("game bootstrap must retain the shared application controller")
	elif game_app._is_designer_product() or game_app._mode != game_app.MODE_LIVE_2D:
		failures.append("game bootstrap must enter playable Live 2D without Designer initialization")
	var game_hud = game_root.get_node_or_null("ReplayHud")
	if game_app != null and game_hud != null:
		_assert_p3_cockpit(game_hud, 2, failures)
		var hash_before: String = game_app._live_bridge.live_state_hash(2)
		game_app._process(60.0)
		game_app._dispatch_live_command(game_app.MODE_LIVE_2D, "hard_drop")
		if not game_app._live_mode_paused() or game_hud._restart_game_button.text != "Start":
			failures.append("fresh Play must show Start on the ready board")
		if game_app._live_bridge.live_state_hash(2) != hash_before:
			failures.append("gravity and piece actions must wait for Start")
		if not game_hud._restart_game_button.is_visible_in_tree():
			failures.append("Start must be visible in the cockpit")
		game_hud._cockpit_dimensions[1].pressed.emit()
		_assert_p3_cockpit(game_hud, 3, failures)
		if not game_app._waiting_to_start or not game_app._live_mode_paused():
			failures.append("changing dimension must preserve the initial Start gate")
		game_hud._restart_game_button.pressed.emit()
		if game_app._live_mode_paused() or game_app._waiting_to_start:
			failures.append("Start must release the launch gate")
		_assert_game_hides_design_affordances(game_hud, failures)
	game_root.queue_free()
	await tree.process_frame

	game_root = GAME_SCENE.instantiate()
	game_root.get_node("App")._launch_view_path = launch_path
	tree.root.add_child(game_root)
	for _index in range(4):
		await tree.process_frame
	game_app = game_root.get_node("App")
	if game_app._mode != game_app.MODE_LIVE_3D or not game_app._waiting_to_start:
		failures.append("a returning Play profile must restore its dimension and wait for Start")
	var accept := InputEventAction.new()
	accept.action = "ui_accept"
	accept.pressed = true
	if not game_app._handle_live_input(accept) or game_app._waiting_to_start:
		failures.append("the standard keyboard/controller accept action must Start Play")
	game_hud = game_root.get_node("ReplayHud")
	game_hud._cockpit_dimensions[2].pressed.emit()
	_assert_p3_cockpit(game_hud, 4, failures)
	game_hud._cockpit_explore.pressed.emit()
	if not game_hud._cockpit_explore.button_pressed or game_hud._cockpit_stats.visible:
		failures.append("Explorer must reuse cockpit navigation and replace the Play stats")
	if not game_hud._cockpit_status.text.begins_with("Active: Explore 4D"):
		failures.append("Explorer must report the active view in the shared status footer")
	game_root.queue_free()
	await tree.process_frame

	game_root = GAME_SCENE.instantiate()
	game_root.get_node("App")._launch_view_path = launch_path
	tree.root.add_child(game_root)
	for _index in range(4):
		await tree.process_frame
	game_app = game_root.get_node("App")
	if game_app._practice == null or game_app._practice.dimension() != 4 or game_app._waiting_to_start:
		failures.append("a returning Explore profile must open its dimension ready to explore")
	game_root.queue_free()
	await tree.process_frame
	DirAccess.remove_absolute(ProjectSettings.globalize_path(launch_path))

	var designer_root := DESIGNER_SCENE.instantiate()
	tree.root.add_child(designer_root)
	for _index in range(4):
		await tree.process_frame
	var designer_app = designer_root.get_node_or_null("App")
	var designer_hud = designer_root.get_node_or_null("ReplayHud")
	if designer_app == null or designer_hud == null:
		failures.append("Designer bootstrap must retain the shared application and HUD")
	elif not designer_app._is_designer_product() or designer_hud._design_laboratory == null:
		failures.append("Designer bootstrap must configure the Design Laboratory")
	elif not designer_hud.design_affordances_enabled() or not designer_hud._design_lab_button.visible or not designer_hud._designer_button.visible:
		failures.append("Designer bootstrap must keep its Design Laboratory and Presentation Designer entries")
	designer_root.queue_free()
	await tree.process_frame
	return failures


func _assert_p3_cockpit(hud, dimension: int, failures: Array) -> void:
	if not hud._cockpit_nav.visible or hud._top_bar.visible:
		failures.append("%dD Play must use the P3 navigation" % dimension)
	if not hud._cockpit_dimensions[dimension - 2].button_pressed:
		failures.append("%dD Play must show its selected dimension" % dimension)
	if not hud._cockpit_stats.visible or hud._piece_preview_row.columns != 1:
		failures.append("%dD Play must share stacked previews and stats" % dimension)
	if not hud._cockpit_footer.visible or not hud._cockpit_status.text.begins_with("Active: Play %dD" % dimension):
		failures.append("%dD Play must publish status in the shared footer" % dimension)


# Stage 56H-R3.3: the game product exposes only connected player actions. Its
# Design Laboratory card and L shortcut were wired to nothing, and the live
# Designer button opened an authoring tool inside ordinary play.
func _assert_game_hides_design_affordances(hud, failures: Array) -> void:
	if hud.design_affordances_enabled():
		failures.append("game bootstrap must disable Designer affordances")
	for control_name in ["_design_menu_header", "_design_lab_button", "_designer_button"]:
		var control = hud.get(control_name)
		if control == null or control.visible:
			failures.append("game bootstrap must hide %s" % control_name)
	for control in hud._main_menu_focus_order:
		if control == hud._design_lab_button:
			continue
		for neighbor_path in [control.focus_neighbor_top, control.focus_neighbor_bottom]:
			if control.get_node_or_null(neighbor_path) == hud._design_lab_button:
				failures.append("game main-menu focus must skip the hidden Design Laboratory card")
	var requested := [false]
	hud.design_laboratory_requested.connect(func() -> void: requested[0] = true)
	hud.show_screen(hud.SCREEN_MAIN_MENU)
	var key := InputEventKey.new()
	key.keycode = KEY_L
	key.pressed = true
	if hud.handle_main_menu_shortcut(key) or requested[0]:
		failures.append("game main-menu L must not request the Design Laboratory")
	hud._open_presentation_designer()
	if hud._presentation_designer != null and hud._presentation_designer.state() != "hidden":
		failures.append("game bootstrap must not open the Presentation Designer")
