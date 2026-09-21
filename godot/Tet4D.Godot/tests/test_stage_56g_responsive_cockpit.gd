extends RefCounted

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

const VIEWPORT_CASES := [
	{"name": "wide desktop", "size": Vector2i(1920, 1080), "profile": "wide"},
	{"name": "standard desktop", "size": Vector2i(1440, 900), "profile": "standard"},
	{"name": "narrow window", "size": Vector2i(960, 640), "profile": "narrow"},
	{"name": "small supported viewport", "size": Vector2i(634, 624), "profile": "small"},
]


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	var tree := Engine.get_main_loop() as SceneTree
	if scene == null or tree == null:
		return ["Stage 56G responsive acceptance requires the production scene and SceneTree"]
	for viewport_case in VIEWPORT_CASES:
		failures.append_array(await _check_viewport_case(tree, scene, viewport_case))
	return failures


func _check_viewport_case(tree: SceneTree, scene: PackedScene, viewport_case: Dictionary) -> Array:
	var failures: Array = []
	var requested_size: Vector2i = viewport_case["size"]
	var viewport := SubViewport.new()
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.size = requested_size
	tree.root.add_child(viewport)
	var root := scene.instantiate() as Control
	viewport.add_child(root)
	var hud = root.get_node("ReplayHud")
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node("App")
	hud._apply_ui_scale("standard")
	hud._apply_hud_density("standard")
	hud._set_onboarding_visible(false)
	hud._apply_responsive_layout()
	for mode in ["2D", "3D", "4D"]:
		match mode:
			"2D": app._enter_live_2d_mode()
			"3D": app._enter_live_3d_mode()
			"4D": app._enter_live_4d_mode()
		await tree.process_frame
		await tree.process_frame
		failures.append_array(_assert_live_geometry(hud, viewport_case, mode))
	viewport.queue_free()
	await tree.process_frame
	return failures


func _assert_live_geometry(hud: Node, viewport_case: Dictionary, mode: String) -> Array:
	var failures: Array = []
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = snapshot.get("live_cockpit", {})
	var label := "%s Live %s" % [viewport_case["name"], mode]
	var deck: Rect2 = snapshot.get("live_4d_deck", Rect2())
	var board: Rect2 = snapshot.get("game_area", Rect2())
	var game_viewport: Rect2 = snapshot.get("game_viewport", Rect2())
	var modules: Array[Rect2] = [
		snapshot.get("piece_module_rect", Rect2()),
		snapshot.get("view_module_rect", Rect2()),
		snapshot.get("piece_state_module_rect", Rect2()),
	]
	if cockpit.get("responsive_profile") != viewport_case["profile"]:
		failures.append("%s should select the %s cockpit profile, got %s for available=%s root=%s" % [label, viewport_case["profile"], cockpit.get("responsive_profile"), cockpit.get("available_size"), snapshot.get("root")])
	if cockpit.get("deck_modules") != ["PieceControls", "ViewControls", "PieceState"]:
		failures.append("%s must retain the shared PIECE / VIEW / PIECE STATE order" % label)
	if not bool(cockpit.get("deck_visible", false)):
		failures.append("%s must keep the shared control deck reachable" % label)
	if board.intersects(deck):
		failures.append("%s must keep the game surface and control deck separate" % label)
	if game_viewport.size.x < ReplayVisuals.GAME_AREA_MIN_WIDTH or game_viewport.size.y < 120.0:
		failures.append("%s must retain a legible game viewport, got %s" % [label, game_viewport])
	for module in modules:
		if not _contains_rect(deck, module):
			failures.append("%s must contain every semantic module in the reachable deck: %s in %s" % [label, module, deck])
	if modules[0].end.x > modules[1].position.x + 0.5 or modules[1].end.x > modules[2].position.x + 0.5:
		failures.append("%s must not overlap or reorder semantic deck modules" % label)
	var preview_row: Rect2 = snapshot.get("piece_preview_row_rect", Rect2())
	if not bool(snapshot.get("piece_preview_row_visible", false)) or not _contains_rect(modules[2], preview_row):
		failures.append("%s must keep HOLD and NEXT grouped inside PIECE STATE" % label)
	return failures


func _contains_rect(outer: Rect2, inner: Rect2) -> bool:
	return (
		inner.size.x > 0.0
		and inner.size.y > 0.0
		and inner.position.x >= outer.position.x - 0.5
		and inner.position.y >= outer.position.y - 0.5
		and inner.end.x <= outer.end.x + 0.5
		and inner.end.y <= outer.end.y + 0.5
	)
