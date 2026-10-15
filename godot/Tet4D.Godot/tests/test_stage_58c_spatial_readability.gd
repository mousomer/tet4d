extends RefCounted

# Stage 58C presentation hierarchy: active > settled > contextual > grid.
# Assertions compare roles, depths and slices against each other, so they fail
# when the hierarchy inverts rather than when a tuned constant moves.

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const SpatialReadability = preload("res://scripts/presentation/spatial_readability.gd")
const TraceSceneRendererScript = preload("res://scripts/rendering/trace_scene_renderer.gd")

const FACES := ["top", "front", "right", "left", "back", "bottom"]
const THEMES := ["plain", "diagnostic", "tron"]
# Material lightness (OKHSL) the active face must keep over the same face of a
# same-colour settled cell, for every palette colour, face and theme.
const ACTIVE_OVER_SETTLED_MIN_MARGIN := 0.08
const NEAR_3D := [5, 9, 5]
const FAR_3D := [0, 9, 0]


func run() -> Array:
	var failures: Array = []
	_test_active_over_settled(failures)
	_test_depth_weight_function(failures)
	await _test_rendered_depth_cue(failures)
	return failures


func _test_active_over_settled(failures: Array) -> void:
	for theme in THEMES:
		for color_id in range(ReplayVisuals.TRACE_COLOR_PALETTE.size()):
			var active: Dictionary = ReplayVisuals.live_3d_active_face_materials(theme, color_id, 1.0)
			var settled: Dictionary = ReplayVisuals.live_3d_locked_face_materials(theme, color_id, 1.0)
			for face in FACES:
				var margin := _lightness(active[face]) - _lightness(settled[face])
				if margin < ACTIVE_OVER_SETTLED_MIN_MARGIN:
					failures.append("%s colour %d %s: active face must stay lighter than settled (margin %.3f)" % [theme, color_id, face, margin])


func _test_depth_weight_function(failures: Array) -> void:
	if SpatialReadability.DEPTH_WEIGHT_REAR < 0.6 or SpatialReadability.DEPTH_WEIGHT_REAR >= 1.0:
		failures.append("rear depth weight must stay in [0.6, 1.0) so rear cells recede without vanishing")
	if not is_equal_approx(SpatialReadability.depth_weight(0.0), 1.0):
		failures.append("the near side of the board must keep full weight")
	if not is_equal_approx(SpatialReadability.depth_weight(1.0), SpatialReadability.DEPTH_WEIGHT_REAR):
		failures.append("the far side of the board must reach the rear weight")
	if not is_equal_approx(SpatialReadability.depth_weight(-0.5), 1.0) or not is_equal_approx(SpatialReadability.depth_weight(1.5), SpatialReadability.DEPTH_WEIGHT_REAR):
		failures.append("depth weight must be bounded outside the board box")
	var previous := INF
	for step in range(11):
		var weight := SpatialReadability.depth_weight(step / 10.0)
		if weight > previous:
			failures.append("depth weight must not increase with depth (step %d)" % step)
		previous = weight
	# Normalised depth is a property of the board, not of window size, zoom or
	# board placement: translating and uniformly scaling everything keeps it.
	var corners: Array = []
	for corner_index in range(8):
		corners.append(Vector3(4.0 if corner_index & 1 else -2.0, 3.0 if corner_index & 2 else -5.0, 1.0 if corner_index & 4 else -1.0))
	var forward := Vector3(0.3, -0.5, -0.8).normalized()
	var point := Vector3(1.0, -1.0, 0.25)
	var reference := SpatialReadability.normalized_depth(point, forward, SpatialReadability.depth_range(corners, forward))
	var moved: Array = corners.map(func(corner: Vector3) -> Vector3: return corner * 2.5 + Vector3(7.0, -3.0, 11.0))
	var moved_depth := SpatialReadability.normalized_depth(point * 2.5 + Vector3(7.0, -3.0, 11.0), forward, SpatialReadability.depth_range(moved, forward))
	if absf(reference - moved_depth) > 0.0001:
		failures.append("normalised depth must not depend on board placement or scale")
	var nearest := SpatialReadability.depth_range(corners, forward)
	if SpatialReadability.normalized_depth(forward * nearest.x, forward, nearest) > 0.0001:
		failures.append("the nearest board corner must have normalised depth 0")


func _test_rendered_depth_cue(failures: Array) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var viewport := SubViewport.new()
	viewport.size = Vector2i(320, 240)
	viewport.own_world_3d = true
	tree.root.add_child(viewport)
	var renderer := TraceSceneRendererScript.new()
	viewport.add_child(renderer)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 16.0
	viewport.add_child(camera)
	camera.current = true
	await tree.process_frame
	renderer.render_snapshot({
		"case_id": "stage58c_depth", "trace_type": "live_3d", "dimension": 3, "board_shape": [6, 10, 6],
		"frame_index": 0, "locked_cells": [{"position": NEAR_3D, "color_id": 3}, {"position": FAR_3D, "color_id": 3}],
		"active_cells": [{"position": [2, 1, 2], "color_id": 3}], "ghost_cells": [], "probe_markers": [],
		"event_markers": [], "particles": [],
	})
	# The live 3D outer view looks from the +X/+Z side, above the board.
	_look(camera, renderer, 32.0, 26.0, 30.0)
	await tree.process_frame
	var near := _weight(renderer, NEAR_3D)
	var far := _weight(renderer, FAR_3D)
	if not (near > far):
		failures.append("the settled cell nearer the camera must keep more weight (near %.3f, far %.3f)" % [near, far])
	if far < SpatialReadability.DEPTH_WEIGHT_REAR - SpatialReadability.WEIGHT_QUANTUM:
		failures.append("rear settled cells must not drop below the rear weight")
	if not is_equal_approx(_weight(renderer, [2, 1, 2], "active"), 1.0):
		failures.append("active cells must never be depth weighted")
	if _lightness(_top_face(renderer, NEAR_3D)) <= _lightness(_top_face(renderer, FAR_3D)):
		failures.append("the nearer settled cell must render lighter than the same-colour rear cell")
	# Zoom, window size and camera distance leave the weights unchanged.
	camera.size = 37.0
	viewport.size = Vector2i(900, 300)
	_look(camera, renderer, 32.0, 26.0, 55.0)
	await tree.process_frame
	if not is_equal_approx(_weight(renderer, NEAR_3D), near) or not is_equal_approx(_weight(renderer, FAR_3D), far):
		failures.append("depth weights must not depend on zoom, viewport size or camera distance")
	# Orbiting to the opposite side swaps which cell is near: no orientation special cases.
	var grid = renderer.get_node("GridRoot").get_child(0)
	var topology: Array = grid.grid_topology()
	_look(camera, renderer, 212.0, 26.0, 30.0)
	await tree.process_frame
	if not (_weight(renderer, FAR_3D) > _weight(renderer, NEAR_3D)):
		failures.append("depth weights must follow the camera to the opposite side of the board")
	if grid.grid_topology() != topology:
		failures.append("camera orbit must not change grid topology")
	viewport.queue_free()
	await tree.process_frame


static func _look(camera: Camera3D, renderer: Node3D, yaw_degrees: float, pitch_degrees: float, distance: float) -> void:
	var yaw := deg_to_rad(yaw_degrees)
	var pitch := deg_to_rad(pitch_degrees)
	var center := renderer.to_global((renderer.current_bounds()["min"] + renderer.current_bounds()["max"]) * 0.5)
	var offset := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch)) * distance
	camera.look_at_from_position(center + offset, center, Vector3.UP)


static func _cell(renderer: Node, position: Array, role: String = "locked") -> Node:
	for node in renderer.get_node("CellRoot").get_children():
		if str(node.get_meta("presentation_role", "")) == role and node.get_meta("canonical_position", []) == position:
			return node
	return null


static func _weight(renderer: Node, position: Array, role: String = "locked") -> float:
	var node := _cell(renderer, position, role)
	return node.presentation_weight() if node != null else -1.0


static func _top_face(renderer: Node, position: Array) -> StandardMaterial3D:
	var node := _cell(renderer, position)
	return (node.get_child(0) as MeshInstance3D).material_override as StandardMaterial3D


static func _lightness(material: StandardMaterial3D) -> float:
	return material.albedo_color.ok_hsl_l
