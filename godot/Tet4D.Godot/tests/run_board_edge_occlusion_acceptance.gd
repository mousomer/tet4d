extends SceneTree

# Board edge occlusion acceptance (graphical language P1), pixel level.
#
#   godot --path godot/Tet4D.Godot --script tests/run_board_edge_occlusion_acceptance.gd
#
# Needs a windowed display server: headless Godot draws nothing, so the
# standard Godot lane cannot run it. Exits 0 on pass and 1 on failure.
#
# Live 3D under the Luminous theme draws the board's outer edges as bright
# glass lines. A piece behind the nearest vertical edge must stay behind it.
# The regression this guards: transparent edge lines that do not write depth
# are painted over by the active piece drawn after them. It renders an empty
# board, then the same board with an active slab packed in behind that edge,
# both through the production TraceSceneRenderer, CameraRig fit and lighting,
# and requires the pixels on the projected edge to be unchanged.

const Renderer = preload("res://scripts/rendering/trace_scene_renderer.gd")
const RigScript = preload("res://scripts/rendering/camera_rig.gd")
const Profile = preload("res://scripts/presentation/presentation_profile.gd")
const Visuals = preload("res://scripts/ui/replay_visuals.gd")

const VIEWPORT := Vector2i(906, 580)
const SHAPE := [6, 10, 6]
const SLAB_ROWS := [3, 4, 5, 6]
const SAMPLES := 40
# Edge pixels may shift this much (RGB distance) and still count as unchanged:
# MSAA blends at the line's own border, not across its centre.
const EDGE_TOLERANCE := 0.12
# Beside the edge, the slab must change the image at least this much, or the
# fixture no longer puts the piece behind the edge and the test proves nothing.
const COVER_THRESHOLD := 0.25
const COVER_OFFSET_PX := 6.0
const MIN_EDGE_KEPT := 0.9
const MIN_COVERED := 0.8

var _renderer
var _rig
var _camera: Camera3D
var _environment: Environment


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("run_board_edge_occlusion_acceptance.gd needs a windowed display server")
		quit(2)
		return
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.msaa_3d = Viewport.MSAA_4X
	root.size = VIEWPORT
	_build_world()
	await process_frame
	var profile = Profile.canonical_defaults().with_overrides({"theme.name": Visuals.DISPLAY_MODE_LUMINOUS})
	var empty := await _render(profile, [])
	var corner := _nearest_vertical_corner()
	var top: Vector3 = corner + _row_offset(SLAB_ROWS[0] + 0.5)
	var bottom: Vector3 = corner + _row_offset(SLAB_ROWS[-1] + 0.5)
	var slab := await _render(profile, _slab_cells(corner))
	var top_px := _camera.unproject_position(top)
	var bottom_px := _camera.unproject_position(bottom)
	var side := (bottom_px - top_px).orthogonal().normalized()
	var kept := 0
	var covered := 0
	for index in range(SAMPLES):
		var point := top_px.lerp(bottom_px, (index + 0.5) / SAMPLES)
		if _distance(empty, slab, point) <= EDGE_TOLERANCE:
			kept += 1
		if maxf(_distance(empty, slab, point + side * COVER_OFFSET_PX), _distance(empty, slab, point - side * COVER_OFFSET_PX)) >= COVER_THRESHOLD:
			covered += 1
	var debug_dir := OS.get_environment("TET4D_EDGE_OCCLUSION_DEBUG_DIR")
	if not debug_dir.is_empty():
		empty.save_png(debug_dir.path_join("empty.png"))
		slab.save_png(debug_dir.path_join("slab.png"))
		print("edge %s -> %s" % [top_px, bottom_px])
	var kept_share := float(kept) / SAMPLES
	var covered_share := float(covered) / SAMPLES
	print("board edge occlusion: edge kept %.2f (need %.2f), slab around edge %.2f (need %.2f)" % [kept_share, MIN_EDGE_KEPT, covered_share, MIN_COVERED])
	if covered_share < MIN_COVERED:
		print("BOARD EDGE OCCLUSION: FAIL - the slab no longer surrounds the edge on screen; fix the fixture")
		quit(1)
		return
	if kept_share < MIN_EDGE_KEPT:
		print("BOARD EDGE OCCLUSION: FAIL - the active piece behind the front edge is painted over it")
		quit(1)
		return
	print("BOARD EDGE OCCLUSION: PASS")
	quit(0)


func _build_world() -> void:
	var world := Node3D.new()
	var presentation_root := Node3D.new()
	world.add_child(presentation_root)
	_renderer = Renderer.new()
	presentation_root.add_child(_renderer)
	_rig = RigScript.new()
	world.add_child(_rig)
	_camera = Camera3D.new()
	_camera.name = "Camera3D"
	_camera.current = true
	_camera.fov = 50.0
	_rig.add_child(_camera)
	var light := DirectionalLight3D.new()
	light.rotation = Vector3(-0.785398, 0.523599, 0.0)
	light.light_energy = 2.2
	world.add_child(light)
	_environment = Environment.new()
	_environment.background_mode = Environment.BG_COLOR
	_environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_environment.ambient_light_color = Color(0.95, 0.98, 1, 1)
	_environment.ambient_light_energy = 1.85
	var world_environment := WorldEnvironment.new()
	world_environment.environment = _environment
	world.add_child(world_environment)
	root.add_child(world)
	_rig.set_world_presentation_root(presentation_root)


func _render(profile, active: Array) -> Image:
	_environment.background_color = Visuals.color_for_role(Visuals.ROLE_BACKGROUND, Visuals.DISPLAY_MODE_LUMINOUS)
	_renderer.clear_presentation()
	_renderer.set_layout_viewport_size(Vector2(VIEWPORT))
	_renderer.apply_presentation_profile(profile)
	var cells: Array = []
	for position in active:
		cells.append({"position": position, "color_id": 3})
	_renderer.render_snapshot({"case_id": "board_edge_occlusion", "trace_type": "live_3d", "dimension": 3,
		"board_shape": SHAPE, "frame_index": 0, "locked_cells": [], "active_cells": cells,
		"ghost_cells": [], "probe_markers": [], "event_markers": [], "particles": []})
	_rig.establish_canonical_projection()
	_rig.establish_outer_view(RigScript.LIVE_3D_DISPLAY_YAW_RAD, RigScript.LIVE_3D_DISPLAY_PITCH_RAD, 0.0, false)
	for frame in range(2):
		await process_frame
	# TraceReplayApp._fit_view() for Live 3D. Both renders fit the same board,
	# so the empty and slab images line up pixel for pixel.
	var bounds: Dictionary = _renderer.current_bounds()
	var headroom := Vector3(0.0, RigScript.LIVE_2D_SPAWN_HEADROOM_ROWS, 0.0)
	bounds = {"ok": true, "min": bounds["min"], "max": (bounds["max"] as Vector3) + headroom}
	_rig.set_fit_horizontal_anchor(1.0)
	_rig.fit_current_bounds(bounds, RigScript.LIVE_3D_FIT_MARGIN, [{"min": bounds["min"], "max": bounds["max"]}])
	for frame in range(3):
		await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()


func _cell(position: Array) -> Vector3:
	return _renderer._presentation.render_cell_world_position(position)


# The outer vertical edge nearest the camera, at row 0's cell-centre height.
func _nearest_vertical_corner() -> Vector3:
	var best := Vector3.ZERO
	var best_distance := INF
	for x in [0, SHAPE[0] - 1]:
		for z in [0, SHAPE[2] - 1]:
			var inward_x := 1 if x == 0 else -1
			var inward_z := 1 if z == 0 else -1
			var centre := _cell([x, 0, z])
			var half_x := (centre - _cell([x + inward_x, 0, z])) * 0.5
			var half_z := (centre - _cell([x, 0, z + inward_z])) * 0.5
			var corner := centre + half_x + half_z
			var distance := corner.distance_to(_camera.global_position)
			if distance < best_distance:
				best_distance = distance
				best = corner
	return best


func _row_offset(rows: float) -> Vector3:
	return (_cell([0, 1, 0]) - _cell([0, 0, 0])) * rows


# Every cell in the slab rows except the column touching the edge, whose
# outer corner would tie with the edge in depth.
func _slab_cells(corner: Vector3) -> Array:
	var edge_column := Vector2i.ZERO
	var nearest := INF
	for x in [0, SHAPE[0] - 1]:
		for z in [0, SHAPE[2] - 1]:
			var distance := _cell([x, 0, z]).distance_to(corner)
			if distance < nearest:
				nearest = distance
				edge_column = Vector2i(x, z)
	var cells: Array = []
	for y in SLAB_ROWS:
		for x in range(SHAPE[0]):
			for z in range(SHAPE[2]):
				if Vector2i(x, z) != edge_column:
					cells.append([x, y, z])
	return cells


static func _distance(a: Image, b: Image, point: Vector2) -> float:
	var x := clampi(int(round(point.x)), 0, a.get_width() - 1)
	var y := clampi(int(round(point.y)), 0, a.get_height() - 1)
	var ca := a.get_pixel(x, y)
	var cb := b.get_pixel(x, y)
	return Vector3(ca.r - cb.r, ca.g - cb.g, ca.b - cb.b).length()
