extends RefCounted

func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Stage 47b acceptance checks require the replay scene and SceneTree"]
	var root := scene.instantiate() as Control
	root.set_anchors_preset(Control.PRESET_TOP_LEFT)
	root.size = Vector2(960, 640)
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node("ReplayHud")
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	_check_scroll(failures, snapshot.get("main_menu_scroll", {}), "main menu")
	if str(snapshot.get("focused_control", "")) != "CommandCard__Play_2D":
		failures.append("main menu should initially focus Play 2D")
	_send_key(KEY_DOWN)
	await tree.process_frame
	if tree.root.gui_get_focus_owner() == null or str(tree.root.gui_get_focus_owner().name) != "CommandCard__Play_3D":
		failures.append("Down should move main-menu focus from Play 2D to Play 3D")
	_send_key(KEY_ENTER)
	await tree.process_frame
	await tree.process_frame
	if str(hud.layout_contract_snapshot().get("current_screen", "")) != hud.SCREEN_VIEWER:
		failures.append("Enter should activate the focused Play 3D action")
	_send_key(KEY_ESCAPE)
	await tree.process_frame
	if str(hud.layout_contract_snapshot().get("current_screen", "")) != hud.SCREEN_MAIN_MENU:
		failures.append("Esc should return from live play to Main Menu")
	hud.show_screen(hud.SCREEN_CONTROLS)
	await tree.process_frame
	snapshot = hud.layout_contract_snapshot()
	_check_scroll(failures, snapshot.get("controls_scroll", {}), "controls help")
	if str(snapshot.get("focused_control", "")) != "ControlsHelpScroll":
		failures.append("controls help should focus its keyboard-scrollable content")
	hud.show_screen(hud.SCREEN_ABOUT)
	await tree.process_frame
	_check_scroll(failures, hud.layout_contract_snapshot().get("about_scroll", {}), "about")
	for mode in ["live_2d", "live_3d", "live_4d"]:
		if mode == "live_2d": hud.set_live_2d_mode(false, false, "none")
		elif mode == "live_3d": hud.set_live_3d_mode(false, false, "none")
		else: hud.set_live_4d_mode(false, false, "none")
		snapshot = hud.layout_contract_snapshot()
		var panel: Dictionary = snapshot.get("onboarding_panel", {})
		if not bool(panel.get("visible", false)):
			failures.append("%s onboarding should be visible before any command" % mode)
		if str(panel.get("title", "")).find("Getting Started") == -1 or str(panel.get("body", "")).is_empty():
			failures.append("%s onboarding should expose its initial title and instruction" % mode)
		if float(panel.get("minimum_height", 0.0)) < 170.0 or str(panel.get("hide_action", "")) != "Hide Guide":
			failures.append("%s onboarding should be prominent and expose an explicit Hide Guide action" % mode)
		var order: Array = snapshot.get("right_inspector_order", [])
		if order.is_empty() or str(order[0]) != "LiveOnboardingPanel":
			failures.append("%s onboarding should be first in the live inspector" % mode)
	root.queue_free()
	await tree.process_frame
	return failures

func _check_scroll(failures: Array, contract: Dictionary, label: String) -> void:
	if contract.is_empty() or not bool(contract.get("vertical_scroll_enabled", false)):
		failures.append("%s content should have a vertical scroll parent" % label)
	if float(contract.get("viewport_height", 0.0)) <= 0.0:
		failures.append("%s scroll viewport should be visible at minimum size" % label)

func _send_key(keycode: Key) -> void:
	var pressed := InputEventKey.new()
	pressed.keycode = keycode
	pressed.pressed = true
	Input.parse_input_event(pressed)
	var released := InputEventKey.new()
	released.keycode = keycode
	released.pressed = false
	Input.parse_input_event(released)
