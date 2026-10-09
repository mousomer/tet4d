extends RefCounted

# Test support for the spatial 3D/4D legend: checks the legend against the
# board itself rather than against the legend's own computation.


# On-screen height of the fitted content boxes, in viewport pixels.
static func projected_content_height(app) -> float:
	var low := INF
	var high := -INF
	for box in app._renderer.current_content_boxes():
		var minimum: Vector3 = box.get("min", Vector3.ZERO)
		var maximum: Vector3 = box.get("max", Vector3.ZERO)
		for x in [minimum.x, maximum.x]:
			for y in [minimum.y, maximum.y]:
				for z in [minimum.z, maximum.z]:
					var point: Vector2 = app._camera_rig.project_world_point(Vector3(x, y, z))
					low = minf(low, point.y)
					high = maxf(high, point.y)
	return high - low if high > low else 0.0


static func active_centroid(app) -> Vector2:
	var cells: Array = app._current_snapshot.get("active_cells", [])
	if cells.is_empty():
		return Vector2.INF
	var total := Vector2.ZERO
	for cell in cells:
		var world: Vector3 = app._renderer.to_global(app._renderer._presentation.render_active_world_position(cell.get("position", [])))
		total += app._camera_rig.project_world_point(world)
	return total / float(cells.size())


# Dispatches every movement intent through the real control path and requires
# the active piece to move on screen the way the legend's arrow points. The
# move is measured synchronously after dispatch, so gravity cannot leak in.
static func check_compass_matches_moves(app, hud, tree: SceneTree, dimension: int, label: String) -> Array:
	var failures: Array = []
	var intents := ["move_x_neg", "move_x_pos", "move_z_neg", "move_z_pos"]
	if dimension >= 4:
		intents.append_array(["move_w_neg", "move_w_pos"])
	for intent in intents:
		app._live_tick_accumulator = 0.0
		await tree.process_frame
		var legend: Dictionary = hud._piece_control_strip.deterministic_snapshot().get("screen_directions", {})
		var expected: Vector2 = legend.get(intent, Vector2.ZERO)
		if expected == Vector2.ZERO:
			failures.append("%s legend has no on-screen direction for %s" % [label, intent])
			continue
		var before := active_centroid(app)
		if dimension >= 4:
			app._dispatch_live_4d_control_intent(intent)
		else:
			app._dispatch_live_3d_control_intent(intent)
		var moved := active_centroid(app) - before
		if moved.length() < 1.0:
			failures.append("%s piece did not move for %s, so its arrow could not be checked" % [label, intent])
			continue
		if moved.normalized().dot(expected) < 0.95:
			failures.append("%s arrow for %s points %s but the piece moved %s on screen" % [label, intent, expected, moved.normalized()])
	return failures
