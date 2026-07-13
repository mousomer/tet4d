extends RefCounted


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Stage 48 regression checks require SceneTree and replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	if hud == null:
		root.queue_free()
		return ["Stage 48 regression checks require ReplayHud"]
	var settings_button := _find_command_card(hud, "Settings")
	if settings_button == null:
		failures.append("main menu should expose Settings for pointer activation")
	else:
		await _click(tree, settings_button)
		await tree.process_frame
		if hud.current_screen() != "settings":
			failures.append("mouse click should activate the Settings menu card; hovered %s; rect %s; viewport %s" % [_hovered_name(tree), settings_button.get_global_rect(), tree.root.size])
	hud.show_screen("main_menu")
	await tree.process_frame
	var quit_count := [0]
	for connection in hud.quit_requested.get_connections():
		hud.quit_requested.disconnect(connection.get("callable"))
	hud.quit_requested.connect(func() -> void: quit_count[0] += 1)
	var quit_button := _find_command_card(hud, "Quit")
	if quit_button == null:
		failures.append("main menu should expose Quit for pointer activation")
	else:
		if quit_button.get_global_rect().end.y > float(tree.root.size.y):
			failures.append("Quit card should fit fully inside the supported viewport")
		await _click(tree, quit_button)
		await tree.process_frame
		if quit_count[0] != 1:
			failures.append("mouse click should emit Quit exactly once; hovered %s; rect %s" % [_hovered_name(tree), quit_button.get_global_rect()])
	hud.show_screen("main_menu")
	if not hud.handle_main_menu_shortcut(_key_event(KEY_S)) or hud.current_screen() != "settings":
		failures.append("advertised S shortcut should activate Settings")
	hud.show_screen("main_menu")
	if not hud.handle_main_menu_shortcut(_key_event(KEY_H)) or hud.current_screen() != "controls":
		failures.append("advertised H shortcut should activate How to Play")
	hud.show_screen("main_menu")
	if not hud.handle_main_menu_shortcut(_key_event(KEY_A)) or hud.current_screen() != "about":
		failures.append("advertised A shortcut should activate About Tet4D")
	var live_2d_count := [0]
	hud.live_2d_requested.connect(func() -> void: live_2d_count[0] += 1)
	hud.show_screen("main_menu")
	if not hud.handle_main_menu_shortcut(_key_event(KEY_2)) or live_2d_count[0] != 1:
		failures.append("advertised 2 shortcut should activate Play 2D")
	hud.show_screen("main_menu")
	if not hud.handle_main_menu_shortcut(_key_event(KEY_ESCAPE)) or quit_count[0] != 2:
		failures.append("advertised Esc shortcut should emit Quit exactly once")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _click(tree: SceneTree, control: Control) -> void:
	var point := control.get_global_rect().get_center()
	var motion := InputEventMouseMotion.new()
	motion.position = point
	motion.global_position = point
	tree.root.push_input(motion)
	await tree.process_frame
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.global_position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		tree.root.push_input(event)
		await tree.process_frame


func _hovered_name(tree: SceneTree) -> String:
	var hovered := tree.root.gui_get_hovered_control()
	return "%s:%s" % [hovered.name, hovered.get_class()] if hovered != null else "none"


func _key_event(keycode: Key) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = keycode
	event.pressed = true
	return event


func _find_command_card(root: Node, label_text: String) -> Button:
	for child in root.find_children("CommandCard__*", "Button", true, false):
		var button := child as Button
		if button != null and button.text.begins_with(label_text):
			return button
	return null
