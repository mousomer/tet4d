extends RefCounted


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		return ["trace replay scene should load for demo entry checks"]
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["demo entry checks require SceneTree"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	if hud == null:
		root.queue_free()
		return ["trace replay scene should include ReplayHud for demo entry checks"]
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	if str(snapshot.get("current_screen", "")) != "main_menu":
		failures.append("demo shell should start on the main menu")
	var main_menu_text := str(snapshot.get("main_menu_text", ""))
	for required in [
		"Tet4D Vector Arcade Cockpit",
		"Start with 2D",
	]:
		if main_menu_text.find(required) == -1:
			failures.append("main menu should expose %s for first-run demo flow" % required)
	if main_menu_text.find("semantic authority") != -1:
		failures.append("main menu should avoid governance jargon")
	for card_label in [
		"Play 2D",
		"Play 3D",
		"Play 4D",
		"About Tet4D",
		"How to Play",
		"Settings",
		"Advanced / Diagnostics",
		"Quit",
	]:
		if _find_visible_command_card(hud, card_label) == null:
			failures.append("main menu should expose %s for first-run demo flow" % card_label)
	if _find_visible_command_card(hud, "Replay Demos") != null:
		failures.append("Replay Demos should not compete with Play on the Main Menu")
	var advanced_card := _find_visible_command_card(hud, "Advanced / Diagnostics")
	if advanced_card != null:
		await _click(tree, advanced_card)
		if hud.current_screen() != hud.SCREEN_ADVANCED:
			failures.append("Advanced / Diagnostics should be mouse-accessible from Main Menu")
		var replay_card := _find_visible_command_card(hud, "Replay Demos")
		if replay_card == null:
			failures.append("Advanced / Diagnostics should retain Replay Demos")
		else:
			replay_card.grab_focus()
			_send_key(KEY_ENTER)
			await tree.process_frame
			if hud.current_screen() != hud.SCREEN_BROWSER:
				failures.append("Replay Demos should accept Enter from Advanced / Diagnostics")
		hud.show_screen(hud.SCREEN_ADVANCED)
		await tree.process_frame
		var diagnostics_card := _find_visible_command_card(hud, "Diagnostics")
		if diagnostics_card == null:
			failures.append("Advanced / Diagnostics should expose Diagnostics")
		else:
			await _click(tree, diagnostics_card)
			if hud.current_screen() != hud.SCREEN_DIAGNOSTICS:
				failures.append("Diagnostics should be mouse-accessible from the advanced screen")
		hud.show_screen(hud.SCREEN_MAIN_MENU)
		await tree.process_frame
	var about_card := _find_visible_command_card(hud, "About Tet4D")
	if about_card == null:
		failures.append("main menu should expose an About / Demo Path card")
	else:
		about_card.pressed.emit()
		await tree.process_frame
		var about_snapshot: Dictionary = hud.layout_contract_snapshot()
		if str(about_snapshot.get("current_screen", "")) != "about":
			failures.append("About / Demo Path card should open the about screen")
		var about_text := str(about_snapshot.get("about_text", ""))
		for required in [
			"Tet4D is a 2D/3D/4D Tetris project.",
			"Replay Demos",
			"Live Plain 2D",
			"Live Plain 3D",
			"Live Plain 4D",
			"Topology Playground",
			"The Python version currently contains the full topology tools.",
		]:
			if about_text.find(required) == -1:
				failures.append("about screen should explain %s" % required)
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _find_visible_command_card(root: Node, label_text: String) -> Button:
	for child in root.find_children("CommandCard__*", "Button", true, false):
		var button := child as Button
		if button != null and button.is_visible_in_tree() and button.text.begins_with(label_text):
			return button
	return null


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


func _send_key(keycode: Key) -> void:
	var pressed := InputEventKey.new()
	pressed.keycode = keycode
	pressed.pressed = true
	Input.parse_input_event(pressed)
	var released := InputEventKey.new()
	released.keycode = keycode
	released.pressed = false
	Input.parse_input_event(released)
