extends RefCounted

const GAME_SCENE := preload("res://scenes/game_bootstrap.tscn")
const DESIGNER_SCENE := preload("res://scenes/designer_bootstrap.tscn")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["product bootstrap test requires a SceneTree"]
	var game_root := GAME_SCENE.instantiate()
	tree.root.add_child(game_root)
	for _index in range(4):
		await tree.process_frame
	var game_app = game_root.get_node_or_null("App")
	if game_app == null:
		failures.append("game bootstrap must retain the shared application controller")
	elif game_app._is_designer_product() or game_app._mode != game_app.MODE_LIVE_2D:
		failures.append("game bootstrap must enter playable Live 2D without Designer initialization")
	var game_hud = game_root.get_node_or_null("ReplayHud")
	if game_hud != null:
		_assert_game_hides_design_affordances(game_hud, failures)
	game_root.queue_free()
	await tree.process_frame

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
