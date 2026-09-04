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
	designer_root.queue_free()
	await tree.process_frame
	return failures
