extends RefCounted


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	var tree := Engine.get_main_loop() as SceneTree
	if scene == null or tree == null:
		return ["settings navigation test requires the replay scene and SceneTree"]
	var original_viewport_size := tree.root.size
	tree.root.size = Vector2i(960, 640)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	if hud == null:
		root.queue_free()
		return ["settings navigation test requires ReplayHud"]
	hud.show_screen("settings")
	await tree.process_frame
	var panel = hud._settings_screen_panel
	var scroll := panel.get_node_or_null("SettingsScroll") as ScrollContainer
	if scroll == null or not scroll.is_visible_in_tree():
		failures.append("Settings screen should expose a visible viewport-safe scroll container")
	elif scroll.size.y <= 0 or scroll.size.y > root.size.y:
		failures.append("Settings scroll container should fit the supported minimum viewport")
	var first := panel.first_focus_control() as Control
	if first == null or tree.root.gui_get_focus_owner() != first:
		failures.append("Settings screen should focus its first preference")
	var visited: Dictionary = {}
	var current := first
	for _index in range(25):
		if current == null or visited.has(current):
			break
		visited[current] = true
		current = current.get_node_or_null(current.focus_neighbor_bottom) as Control
	var reset := panel.get_node_or_null("SettingsScroll/SettingsContent/ResetSettingsToDefaultsButton") as Button
	if reset == null or not visited.has(reset):
		failures.append("deterministic arrow-key focus order should reach Reset Settings to Defaults")
	if visited.size() != 18:
		failures.append("focus order should include all visible Stage 51 setting controls and reset")
	var down := InputEventKey.new()
	down.keycode = KEY_DOWN
	down.pressed = true
	tree.root.push_input(down)
	await tree.process_frame
	if first != null and tree.root.gui_get_focus_owner() == first:
		failures.append("Down arrow should move focus to the next setting")
	hud.show_screen("main_menu")
	await tree.process_frame
	if str(hud.layout_contract_snapshot().get("current_screen", "")) != "main_menu":
		failures.append("Settings navigation should return to Main Menu")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_viewport_size
	return failures
