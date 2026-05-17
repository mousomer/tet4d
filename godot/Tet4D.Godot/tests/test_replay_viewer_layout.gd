extends RefCounted


const VIEWPORT_SIZES := [
	Vector2i(1600, 960),
	Vector2i(1180, 760),
	Vector2i(960, 640),
]


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		return ["trace replay scene should load for layout contract"]
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["layout contract test requires SceneTree"]
	for viewport_size in VIEWPORT_SIZES:
		var root := scene.instantiate() as Control
		if root == null:
			failures.append("trace replay root should instantiate for %s" % str(viewport_size))
			continue
		tree.root.add_child(root)
		root.set_anchors_preset(Control.PRESET_TOP_LEFT)
		root.size = Vector2(viewport_size)
		var hud := root.get_node_or_null("ReplayHud")
		if hud == null:
			failures.append("ReplayHud should exist for layout contract")
			root.queue_free()
			continue
		hud.show_replay_viewer()
		await tree.process_frame
		await tree.process_frame
		failures.append_array(_check_layout(hud, viewport_size))
		root.queue_free()
		await tree.process_frame
	return failures


func _check_layout(hud: Node, viewport_size: Vector2i) -> Array:
	var failures: Array = []
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var root_rect: Rect2 = snapshot.get("root", Rect2())
	var body_rect: Rect2 = snapshot.get("body", Rect2())
	var game_rect: Rect2 = snapshot.get("game_area", Rect2())
	var game_viewport_rect: Rect2 = snapshot.get("game_viewport", Rect2())
	var inspector_rect: Rect2 = snapshot.get("right_inspector", Rect2())
	var bottom_rect: Rect2 = snapshot.get("bottom_bar", Rect2())
	var label := "viewport %s" % str(viewport_size)
	if root_rect.size.x <= 0.0 or root_rect.size.y <= 0.0:
		failures.append("%s: root rect should be nonzero" % label)
	if body_rect.size.x <= 0.0 or body_rect.size.y <= 0.0:
		failures.append("%s: body rect should be nonzero" % label)
	if game_rect.size.x <= 0.0 or game_rect.size.y <= 0.0:
		failures.append("%s: game area rect should be nonzero" % label)
	if game_viewport_rect.size.x <= 0.0 or game_viewport_rect.size.y <= 0.0:
		failures.append("%s: game viewport rect should be nonzero" % label)
	if inspector_rect.size.x <= 0.0 or inspector_rect.size.y <= 0.0:
		failures.append("%s: right inspector rect should be nonzero" % label)
	if bottom_rect.size.x <= 0.0 or bottom_rect.size.y <= 0.0:
		failures.append("%s: bottom bar rect should be nonzero" % label)
	if not _contains_rect(root_rect, body_rect):
		failures.append("%s: body should be inside root, root=%s body=%s" % [label, root_rect, body_rect])
	if not _contains_rect(body_rect, game_rect):
		failures.append("%s: game area should be inside body, body=%s game=%s" % [label, body_rect, game_rect])
	if not _contains_rect(body_rect, inspector_rect):
		failures.append("%s: inspector should be inside body, body=%s inspector=%s" % [label, body_rect, inspector_rect])
	if not _contains_rect(game_rect, game_viewport_rect):
		failures.append("%s: game viewport should be inside game area, game=%s viewport=%s" % [label, game_rect, game_viewport_rect])
	if inspector_rect.end.x > root_rect.end.x + 0.5:
		failures.append("%s: inspector right edge should stay inside root, root=%s inspector=%s" % [label, root_rect, inspector_rect])
	if game_rect.end.x > inspector_rect.position.x + 0.5:
		failures.append("%s: game area should not overlap inspector, game=%s inspector=%s" % [label, game_rect, inspector_rect])
	var game_viewport: SubViewport = hud.game_viewport()
	if game_viewport == null:
		failures.append("%s: HUD should expose a game SubViewport" % label)
	elif game_viewport.get_node_or_null("WorldRoot") == null:
		failures.append("%s: WorldRoot should live inside HUD game SubViewport" % label)
	return failures


func _contains_rect(container: Rect2, child: Rect2) -> bool:
	return (
		child.position.x >= container.position.x - 0.5
		and child.position.y >= container.position.y - 0.5
		and child.end.x <= container.end.x + 0.5
		and child.end.y <= container.end.y + 0.5
	)
