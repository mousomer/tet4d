extends RefCounted


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Stage 56B runtime tiling test requires SceneTree and live shell"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	var hud = root.get_node_or_null("ReplayHud")
	if app == null or hud == null:
		root.queue_free()
		tree.root.size = original_size
		return ["Stage 56B runtime tiling test requires app and HUD"]

	var expected_columns := {5: 3, 6: 3, 7: 4, 8: 4}
	for count in expected_columns:
		app._start_configured_live_game(_setup(count))
		await tree.process_frame
		await tree.process_frame
		var layout = app._renderer._presentation.projection.mapper.layer_layout
		var viewport_size: Vector2 = hud.board_viewport_size()
		if layout.viewport_size.distance_to(viewport_size) > 0.1:
			failures.append("%d-slice runtime layout must consume the displayed board viewport" % count)
		if layout.columns != int(expected_columns[count]) or layout.rows != 2:
			failures.append("%d-slice runtime cockpit must select %dx2, got %dx%d" % [count, expected_columns[count], layout.columns, layout.rows])
		var before: Dictionary = layout.snapshot()
		app._refresh_live_4d_snapshot()
		await tree.process_frame
		if app._renderer._presentation.projection.mapper.layer_layout.snapshot() != before:
			failures.append("%d-slice runtime layout must not depend on active-piece activity" % count)

	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _setup(slice_count: int) -> Dictionary:
	var shape := [8, 16, 5, slice_count]
	return {
		"schema_version": 2,
		"contract_version": 1,
		"mode": "live_4d",
		"board_preset_id": "stage56_tiling",
		"board_shape": shape,
		"piece_set_id": "standard_4d_5",
		"random_mode": "fixed_seed",
		"seed": 1337,
		"initial_speed_level": 1,
		"topology_profile": {"contract_version": 1, "rank": 4, "dimensions": shape, "seams": []},
	}
