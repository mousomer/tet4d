extends RefCounted


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		return ["trace replay scene should load for demo entry checks"]
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["demo entry checks require SceneTree"]
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
		"Inspect replay demos or play accepted plain 2D, 3D, and 4D modes.",
	]:
		if main_menu_text.find(required) == -1:
			failures.append("main menu should expose %s for first-run demo flow" % required)
	if main_menu_text.find("semantic authority") != -1:
		failures.append("main menu should avoid governance jargon")
	for card_label in [
		"Replay Demos",
		"Live Plain 2D",
		"Live Plain 3D",
		"Live Plain 4D",
		"About / Demo Path",
		"Controls",
		"Settings",
		"Quit",
	]:
		if _find_command_card(hud, card_label) == null:
			failures.append("main menu should expose %s for first-run demo flow" % card_label)
	var about_card := _find_command_card(hud, "About / Demo Path")
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
			"Python remains the rules reference implementation.",
			"Godot is the product shell and playable front end.",
		]:
			if about_text.find(required) == -1:
				failures.append("about screen should explain %s" % required)
	root.queue_free()
	await tree.process_frame
	return failures


func _find_command_card(root: Node, label_text: String) -> Button:
	for child in root.find_children("CommandCard__*", "Button", true, false):
		var button := child as Button
		if button != null and button.text.begins_with(label_text):
			return button
	return null
