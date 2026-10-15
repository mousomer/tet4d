extends SceneTree

# Stage 58C spatial-readability reference matrix: presentation evidence only.
#
#   Godot --path godot/Tet4D.Godot --script tests/run_spatial_readability_capture.gd -- <absolute_output_dir> [key=value ...]
#
# Needs a windowed display server. Filters take comma lists: scenes= styles=
# grids= sizes= colors=. masks=0 writes composites only; scale=2 renders at
# twice the logical pixel density; save_masks=1 keeps the measurement passes.
#
# Uses the production TraceSceneRenderer, the CameraRig canonical outer views,
# the TraceReplayApp._fit_view() rules and the production light/environment.
# Every case renders a fixed board state from scenes(), so styles, grid modes
# and sizes compare identical content. Nothing simulates: ghost cells are
# fixture data placed where the fixture piece lands on the fixture stack.
#
# Measurement passes redraw the same frame with flat unshaded materials that
# keep each original material's transparency, depth-draw, priority and cull
# state, so draw order matches the composite:
#   ids             each cell one opaque id colour: which cell owns each pixel
#   active_alone    active footprint
#   active_visible  active white, all other geometry black at its own alpha:
#                   a pixel's value is the active piece's transmittance
#   active_lattice  as active_visible with lattice lines as the only occluders
#   lattice_alone   lattice lines white at their own alpha (grid ink)
# records.json holds screen-space observations: footprint, transmittance and
# mean composite CIELAB per cell, with summaries by role, depth and slice.
# They support manual review; they are not perceptual truth.

const Renderer = preload("res://scripts/rendering/trace_scene_renderer.gd")
const RigScript = preload("res://scripts/rendering/camera_rig.gd")
const Catalog = preload("res://scripts/presentation/built_in_style_catalog.gd")
const Profile = preload("res://scripts/presentation/presentation_profile.gd")
const Visuals = preload("res://scripts/ui/replay_visuals.gd")
const Background = preload("res://scripts/rendering/animated_background.gd")
const Registry = preload("res://scripts/ui/settings/settings_registry.gd")
const GridDisplayMode = preload("res://scripts/presentation/grid_display_mode.gd")

# Logical live-board regions. "ref" is the Stage 58B measurement in the
# 1280x720 shell; "large" and "compact" are the regions the live shell gives a
# 1728x1080 window and the 720x600 small profile.
const SIZES := {
	"ref": {3: Vector2i(906, 580), 4: Vector2i(970, 444)},
	"large": {3: Vector2i(1036, 660), 4: Vector2i(1085, 463)},
	"compact": {3: Vector2i(740, 418), 4: Vector2i(1010, 264)},
}
const GRIDS := ["none", "border", "full"]
const PROFILE_FIELDS := ["theme.name", "settled_cells.opacity", "active_cells.opacity", "ghost.opacity",
	"board.grid_opacity", "board.boundary_opacity", "board.enclosure_opacity", "board.back_scaffold_opacity",
	"board.cell_volume_opacity", "display.board_detail", "accessibility.high_contrast"]
const BAR_WIDTH := 24

var _filters: Dictionary = {}
var _world: Node3D
var _presentation_root: Node3D
var _renderer
var _rig
var _camera: Camera3D
var _background
var _environment: Environment
var _backup: Array = []
var _scene: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty() or DisplayServer.get_name() == "headless":
		push_error("usage: windowed Godot ... -- <absolute_output_dir> [key=value ...]")
		quit(2)
		return
	var destination: String = args[0]
	for extra in args.slice(1):
		var pair := str(extra).split("=", false, 1)
		if pair.size() == 2:
			_filters[pair[0]] = pair[1]
	DirAccess.make_dir_recursive_absolute(destination)
	# The live board renders into a SubViewport without content scaling; match
	# that so viewport coordinates are pixels.
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.msaa_3d = Viewport.MSAA_4X
	_build_world()
	await process_frame
	var cases := _cases()
	var records: Array = []
	var started := Time.get_ticks_msec()
	for index in range(cases.size()):
		var case: Dictionary = cases[index]
		var case_started := Time.get_ticks_msec()
		await _render_case(case)
		var composite := root.get_texture().get_image()
		composite.save_png(destination.path_join(case.id + ".png"))
		var record := {"case": case.id, "scene": case.scene.id, "style": case.style, "grid": case.grid, "size": case.size,
			"scale": case.scale, "active_color": case.color, "dimension": case.scene.dim, "board_shape": case.scene.shape,
			"pixels": [composite.get_width(), composite.get_height()], "logical": [case.logical.x, case.logical.y],
			"active_layers": _renderer._presentation.active_layer_indices(), "profile": _profile_record(case.profile)}
		if str(_filters.get("masks", "1")) != "0":
			record["metrics"] = await _measure(composite, case, destination)
		records.append(record)
		_progress(index + 1, cases.size(), case.id, Time.get_ticks_msec() - case_started, Time.get_ticks_msec() - started)
	var file := FileAccess.open(destination.path_join("records.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(records, "\t"))
	file.close()
	print("Captured %d spatial-readability cases to %s" % [records.size(), destination])
	quit()


func _progress(done: int, total: int, label: String, case_ms: int, total_ms: int) -> void:
	var filled := int(round(float(BAR_WIDTH) * done / maxf(total, 1)))
	var eta := (float(total_ms) / done) * (total - done) / 1000.0
	print("[%s%s] %d/%d %-44s %5.1fs  eta %4.0fs" % ["#".repeat(filled), "-".repeat(BAR_WIDTH - filled), done, total, label, case_ms / 1000.0, eta])


func _selected(key: String, value: String) -> bool:
	return not _filters.has(key) or str(_filters[key]).split(",").has(value)


func _cases() -> Array:
	var registry = Registry.new()
	registry.load_from_path(Registry.REGISTRY_PATH)
	var catalog = Catalog.new(registry)
	var styles: Array = [["fresh", Profile.canonical_defaults()]]
	for record in catalog.list_styles():
		styles.append([str(record.style_id), catalog.style_profile(str(record.style_id)).profile])
	var scale := float(_filters.get("scale", "1"))
	var cases: Array = []
	for size_id in SIZES:
		if not _selected("sizes", size_id):
			continue
		for scene in scenes():
			if not _selected("scenes", scene.id):
				continue
			var colors: Array = [scene.color]
			if _filters.has("colors"):
				colors = Array(str(_filters["colors"]).split(",")).map(func(value: String) -> int: return int(value))
			for color in colors:
				for style in styles:
					if not _selected("styles", style[0]):
						continue
					for grid in GRIDS:
						if not _selected("grids", grid):
							continue
						var id := "%s__%s__%s__%s" % [scene.id, style[0], grid, size_id]
						if colors.size() > 1 or color != scene.color:
							id += "__c%d" % color
						if scale != 1.0:
							id += "__x%s" % str(scale)
						cases.append({"id": id, "scene": scene, "style": style[0], "grid": grid, "size": size_id,
							"color": color, "scale": scale, "logical": SIZES[size_id][scene.dim],
							"profile": style[1].with_overrides({"display.grid_mode": grid})})
	return cases


func _profile_record(profile) -> Dictionary:
	var result := {}
	for field in PROFILE_FIELDS:
		result[field] = profile.value(field)
	return result


func _build_world() -> void:
	_world = Node3D.new()
	_world.name = "WorldRoot"
	_presentation_root = Node3D.new()
	_presentation_root.name = "Live4DPresentationRoot"
	_world.add_child(_presentation_root)
	_renderer = Renderer.new()
	_renderer.name = "TraceSceneRenderer"
	_presentation_root.add_child(_renderer)
	_rig = RigScript.new()
	_rig.name = "CameraRig"
	_world.add_child(_rig)
	_camera = Camera3D.new()
	_camera.name = "Camera3D"
	_camera.current = true
	_camera.fov = 50.0
	_rig.add_child(_camera)
	_background = Background.new()
	_background.name = "AnimatedBackground"
	_camera.add_child(_background)
	var light := DirectionalLight3D.new()
	light.rotation = Vector3(-0.785398, 0.523599, 0.0)
	light.light_energy = 2.2
	_world.add_child(light)
	_environment = Environment.new()
	_environment.background_mode = Environment.BG_COLOR
	_environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_environment.ambient_light_color = Color(0.95, 0.98, 1, 1)
	_environment.ambient_light_energy = 1.85
	_environment.glow_enabled = false
	var world_environment := WorldEnvironment.new()
	world_environment.environment = _environment
	_world.add_child(world_environment)
	root.add_child(_world)
	_rig.set_world_presentation_root(_presentation_root)


func _render_case(case: Dictionary) -> void:
	_scene = case.scene
	var logical: Vector2i = case.logical
	root.size = Vector2i(int(round(logical.x * case.scale)), int(round(logical.y * case.scale)))
	var profile = case.profile
	var theme := str(profile.value("theme.name"))
	var background_color := _scaled_background(Visuals.color_for_role(Visuals.ROLE_BACKGROUND, theme), float(profile.value("environment.background_intensity")))
	_environment.background_color = background_color
	_background.visible = true
	_background.apply_presentation_profile(profile)
	_background.set_display_mode(theme)
	_background.set_base_color(background_color)
	_background.reset_phase()
	_background.set_process(false)
	_renderer.clear_presentation()
	_renderer.set_layout_viewport_size(Vector2(logical))
	_renderer.apply_presentation_profile(profile)
	_renderer.render_snapshot(snapshot_for(case.scene, case.color))
	_rig.establish_canonical_projection()
	if case.scene.dim == 3:
		_rig.establish_outer_view(RigScript.LIVE_3D_DISPLAY_YAW_RAD, RigScript.LIVE_3D_DISPLAY_PITCH_RAD, 0.0, false)
	else:
		_rig.establish_outer_view(RigScript.LIVE_4D_DISPLAY_YAW_RAD, RigScript.LIVE_4D_DISPLAY_PITCH_RAD, 0.0, true)
	for frame in range(2):
		await process_frame
	_fit(case.scene.dim)
	_rig.set_orientation_gizmo_visible(true)
	for frame in range(3):
		await process_frame
	await RenderingServer.frame_post_draw


# TraceReplayApp._fit_view() for live 3D/4D.
func _fit(dimension: int) -> void:
	var bounds: Dictionary = _renderer.current_bounds()
	var content_boxes: Array = _renderer.current_content_boxes()
	var margin := RigScript.LIVE_4D_FIT_MARGIN
	if dimension == 3:
		margin = RigScript.LIVE_3D_FIT_MARGIN
		var headroom := Vector3(0.0, RigScript.LIVE_2D_SPAWN_HEADROOM_ROWS, 0.0)
		bounds = {"ok": true, "min": bounds["min"], "max": (bounds["max"] as Vector3) + headroom}
		content_boxes = [{"min": bounds["min"], "max": bounds["max"]}]
	_rig.set_fit_horizontal_anchor(1.0 if dimension == 3 else 0.0)
	_rig.fit_current_bounds(bounds, margin, content_boxes)


static func _scaled_background(color: Color, intensity: float) -> Color:
	if intensity <= 1.0:
		return Color(color.r * intensity, color.g * intensity, color.b * intensity, color.a)
	return color.lerp(Color(1.0, 1.0, 1.0, color.a), minf((intensity - 1.0) * 0.35, 0.35))


# ---------------------------------------------------------------- measurement

func _measure(composite: Image, case: Dictionary, destination: String) -> Dictionary:
	var cells := _cell_table()
	_rig.set_orientation_gizmo_visible(false)
	_background.visible = false
	var saved_background := _environment.background_color
	_environment.background_color = Color.BLACK
	root.msaa_3d = Viewport.MSAA_DISABLED
	var passes := {
		"ids": await _pass({"active": "id", "locked": "id", "ghost": "id"}, cells),
		"active_alone": await _pass({"active": "solid_white"}),
		"active_visible": await _pass({"active": "solid_white", "locked": "black", "ghost": "black", "lattice": "black",
			"enclosure": "black", "floor": "black", "frame": "black"}),
		"active_lattice": await _pass({"active": "solid_white", "lattice": "black"}),
		"lattice_alone": await _pass({"lattice": "white"}),
	}
	root.msaa_3d = Viewport.MSAA_4X
	_environment.background_color = saved_background
	_background.visible = true
	_rig.set_orientation_gizmo_visible(true)
	if str(_filters.get("save_masks", "0")) == "1":
		for name in passes:
			(passes[name] as Image).save_png(destination.path_join("%s__%s.png" % [case.id, name]))
	return _analyse(composite, passes, cells, case)


# One row per rendered cell node: id is the 1-based index used by the id pass.
func _cell_table() -> Array:
	var forward := -_camera.global_transform.basis.z
	var colors := {}
	for entry in _scene.locked:
		colors[str(entry[0])] = int(entry[1])
	var cells: Array = []
	for node in _renderer.get_node("CellRoot").get_children():
		var role := str(node.get_meta("presentation_role", ""))
		var position: Array = node.get_meta("canonical_position", [])
		var color_id := int(colors.get(str(position), -1)) if role == "locked" else -1
		cells.append({"node": node, "role": role, "position": position, "color": color_id,
			"layer": _layer_of(position), "depth": ((node as Node3D).global_position - _camera.global_position).dot(forward)})
	return cells


func _layer_of(position: Array) -> int:
	if position.size() < 4:
		return 0
	return int(_renderer._presentation.projection.mapper.presentation_coordinate(position, true).get("layer_index", 0))


func _pass(spec: Dictionary, cells: Array = []) -> Image:
	var ids := {}
	for index in range(cells.size()):
		ids[(cells[index].node as Node).get_instance_id()] = index + 1
	_apply_spec(_renderer, spec, ids, 0)
	for frame in range(2):
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	for index in range(_backup.size() - 1, -1, -1):
		var entry: Array = _backup[index]
		(entry[0] as Object).set(entry[1], entry[2])
	_backup.clear()
	return image


# Categories come from the nearest presentation_role meta; anything a spec does
# not name is hidden. cell_id is the id of the enclosing cell node, if any.
func _apply_spec(node: Node, spec: Dictionary, ids: Dictionary, cell_id: int) -> void:
	if ids.has(node.get_instance_id()):
		cell_id = ids[node.get_instance_id()]
	if node is GeometryInstance3D:
		var category := _category(node)
		var mode := str(spec.get(category, "hide"))
		if node is Label3D or mode == "hide":
			_backup.append([node, "visible", node.visible])
			node.visible = false
		else:
			_backup.append([node, "material_override", node.material_override])
			node.material_override = _flat_material(node.material_override, mode, cell_id)
	for child in node.get_children():
		_apply_spec(child, spec, ids, cell_id)


func _category(node: Node) -> String:
	var cursor := node
	while cursor != null and cursor != _renderer:
		match str(cursor.get_meta("presentation_role", "")):
			"active", "locked", "ghost":
				return str(cursor.get_meta("presentation_role"))
			GridDisplayMode.GRID_EDGE, GridDisplayMode.GRID_FACE, GridDisplayMode.GRID_INTERIOR:
				return "lattice"
			GridDisplayMode.ENCLOSURE:
				return "enclosure"
			GridDisplayMode.FLOOR:
				return "floor"
			"board.frame_active":
				return "frame"
		cursor = cursor.get_parent()
	return "other"


func _flat_material(original, mode: String, cell_id: int) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var alpha := 1.0
	if original is BaseMaterial3D:
		material.transparency = original.transparency
		material.depth_draw_mode = original.depth_draw_mode
		material.render_priority = original.render_priority
		material.cull_mode = original.cull_mode
		material.no_depth_test = original.no_depth_test
		alpha = original.albedo_color.a
	match mode:
		"id":
			material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
			material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_OPAQUE_ONLY
			material.render_priority = 0
			material.albedo_color = _id_color(cell_id)
		"solid_white":
			material.albedo_color = Color(1, 1, 1, 1)
		"white":
			material.albedo_color = Color(1, 1, 1, alpha)
		_:
			material.albedo_color = Color(0, 0, 0, alpha)
	return material


# 5 bits per channel at 8-step spacing survive the sRGB round trip exactly.
static func _id_color(cell_id: int) -> Color:
	return Color8(((cell_id & 31) << 3) | 4, (((cell_id >> 5) & 31) << 3) | 4, (((cell_id >> 10) & 31) << 3) | 4)


func _analyse(composite: Image, passes: Dictionary, cells: Array, case: Dictionary) -> Dictionary:
	var comp := _bytes(composite, Image.FORMAT_RGB8)
	var ids := _bytes(passes.ids, Image.FORMAT_RGB8)
	var active_alone := _bytes(passes.active_alone, Image.FORMAT_R8)
	var active_visible := _bytes(passes.active_visible, Image.FORMAT_R8)
	var active_lattice := _bytes(passes.active_lattice, Image.FORMAT_R8)
	var lattice := _bytes(passes.lattice_alone, Image.FORMAT_R8)
	var count := cells.size() + 1
	var cell_px := PackedInt64Array()
	cell_px.resize(count)
	var cell_rgb := PackedFloat64Array()
	cell_rgb.resize(count * 3)
	var footprint := 0
	var visible := 0
	var transmittance := 0
	var lattice_transmittance := 0
	var lattice_on_active := 0
	var lattice_total := 0
	for i in range(active_alone.size()):
		var id := (ids[i * 3] >> 3) | ((ids[i * 3 + 1] >> 3) << 5) | ((ids[i * 3 + 2] >> 3) << 10)
		if id > 0 and id < count:
			cell_px[id] += 1
			cell_rgb[id * 3] += comp[i * 3]
			cell_rgb[id * 3 + 1] += comp[i * 3 + 1]
			cell_rgb[id * 3 + 2] += comp[i * 3 + 2]
		lattice_total += lattice[i]
		if active_alone[i] > 127:
			footprint += 1
			transmittance += active_visible[i]
			lattice_transmittance += active_lattice[i]
			lattice_on_active += lattice[i]
			if active_visible[i] > 127:
				visible += 1
	var rows: Array = []
	var depth_min := INF
	var depth_max := -INF
	for index in range(cells.size()):
		depth_min = minf(depth_min, cells[index].depth)
		depth_max = maxf(depth_max, cells[index].depth)
	for index in range(cells.size()):
		var id := index + 1
		var px := int(cell_px[id])
		var lab := _lab(Color8(int(round(cell_rgb[id * 3] / maxf(px, 1))), int(round(cell_rgb[id * 3 + 1] / maxf(px, 1))), int(round(cell_rgb[id * 3 + 2] / maxf(px, 1)))))
		var cell: Dictionary = cells[index]
		rows.append({"role": cell.role, "position": cell.position, "color": cell.color, "layer": cell.layer,
			"depth": snappedf(cell.depth, 0.001), "depth01": snappedf((cell.depth - depth_min) / maxf(depth_max - depth_min, 0.001), 0.001),
			"px": px, "lab": [snappedf(lab.x, 0.01), snappedf(lab.y, 0.01), snappedf(lab.z, 0.01)]})
	var pixels := float(active_alone.size())
	var result := {
		"active": {"footprint_px": footprint, "visible_fraction": float(visible) / maxf(footprint, 1),
			"transmittance_mean": transmittance / 255.0 / maxf(footprint, 1),
			"lattice_transmittance_mean": lattice_transmittance / 255.0 / maxf(footprint, 1)},
		"lattice": {"ink_per_kpx": 1000.0 * lattice_total / 255.0 / pixels,
			"ink_on_active_per_kpx": 1000.0 * lattice_on_active / 255.0 / maxf(footprint, 1)},
		"background_lab": _vector(_lab(_environment.background_color)),
		"roles": {
			"active": _group(rows, func(row: Dictionary) -> bool: return row.role == "active"),
			"ghost": _group(rows, func(row: Dictionary) -> bool: return row.role == "ghost"),
			"locked": _group(rows, func(row: Dictionary) -> bool: return row.role == "locked"),
			"locked_same_color": _group(rows, func(row: Dictionary) -> bool: return row.role == "locked" and row.color == case.color),
		},
		"locked_by_depth": [
			_group(rows, func(row: Dictionary) -> bool: return row.role == "locked" and row.depth01 < 1.0 / 3.0),
			_group(rows, func(row: Dictionary) -> bool: return row.role == "locked" and row.depth01 >= 1.0 / 3.0 and row.depth01 < 2.0 / 3.0),
			_group(rows, func(row: Dictionary) -> bool: return row.role == "locked" and row.depth01 >= 2.0 / 3.0),
		],
		"cells": rows,
	}
	if case.scene.dim == 4:
		var slices: Array = []
		var boxes: Array = _renderer.current_content_boxes()
		var active_layers: Array = _renderer._presentation.active_layer_indices()
		for layer in range(boxes.size()):
			var group := _group(rows, func(row: Dictionary) -> bool: return row.role == "locked" and row.layer == layer)
			group["layer"] = layer
			group["active"] = active_layers.has(layer)
			group["lattice_ink_per_kpx"] = _rect_ink(lattice, (passes.lattice_alone as Image).get_width(), _screen_rect(boxes[layer]))
			slices.append(group)
		result["slices"] = slices
	return result


# Pixel-weighted mean CIELAB of a group of cells, from per-cell mean colour.
static func _group(rows: Array, predicate: Callable) -> Dictionary:
	var px := 0
	var cells := 0
	var sum := Vector3.ZERO
	for row in rows:
		if not predicate.call(row) or int(row.px) <= 0:
			continue
		px += int(row.px)
		cells += 1
		sum += Vector3(row.lab[0], row.lab[1], row.lab[2]) * int(row.px)
	var mean := sum / maxf(px, 1)
	return {"cells": cells, "px": px, "lab": [snappedf(mean.x, 0.01), snappedf(mean.y, 0.01), snappedf(mean.z, 0.01)]}


func _bytes(image: Image, format: int) -> PackedByteArray:
	var copy: Image = image.duplicate()
	copy.convert(format)
	return copy.get_data()


func _screen_rect(box: Dictionary) -> Rect2i:
	var low: Vector3 = box.min
	var high: Vector3 = box.max
	var rect := Rect2()
	for corner_index in range(8):
		var corner := Vector3(high.x if corner_index & 1 else low.x, high.y if corner_index & 2 else low.y, high.z if corner_index & 4 else low.z)
		var screen := _camera.unproject_position(_presentation_root.global_transform * corner)
		rect = Rect2(screen, Vector2.ZERO) if corner_index == 0 else rect.expand(screen)
	return Rect2i(rect)


static func _rect_ink(values: PackedByteArray, width: int, rect: Rect2i) -> float:
	var height := values.size() / width
	var clipped := rect.intersection(Rect2i(0, 0, width, height))
	var total := 0
	for y in range(clipped.position.y, clipped.end.y):
		for x in range(clipped.position.x, clipped.end.x):
			total += values[y * width + x]
	return 1000.0 * total / 255.0 / maxf(clipped.get_area(), 1)


static func _vector(value: Vector3) -> Array:
	return [snappedf(value.x, 0.01), snappedf(value.y, 0.01), snappedf(value.z, 0.01)]


# sRGB (D65) to CIELAB.
static func _lab(color: Color) -> Vector3:
	var linear := color.srgb_to_linear()
	var x := (0.4124564 * linear.r + 0.3575761 * linear.g + 0.1804375 * linear.b) / 0.95047
	var y := 0.2126729 * linear.r + 0.7151522 * linear.g + 0.0721750 * linear.b
	var z := (0.0193339 * linear.r + 0.1191920 * linear.g + 0.9503041 * linear.b) / 1.08883
	return Vector3(116.0 * _lab_f(y) - 16.0, 500.0 * (_lab_f(x) - _lab_f(y)), 200.0 * (_lab_f(y) - _lab_f(z)))


static func _lab_f(t: float) -> float:
	return pow(t, 1.0 / 3.0) if t > 0.008856 else (7.787 * t + 16.0 / 116.0)


# ------------------------------------------------------------------- fixtures

func snapshot_for(scene: Dictionary, color: int) -> Dictionary:
	var locked: Array = []
	for entry in scene.locked:
		locked.append({"position": entry[0], "color_id": entry[1]})
	var active: Array = []
	for coord in scene.active:
		active.append({"position": coord, "color_id": color})
	var ghost: Array = []
	for coord in scene.active:
		var shifted: Array = coord.duplicate()
		shifted[1] += int(scene.ghost_rows)
		ghost.append({"position": shifted, "color_id": color})
	return {"case_id": "stage58c_" + scene.id, "trace_type": "live_%dd" % scene.dim, "dimension": scene.dim,
		"board_shape": scene.shape, "frame_index": 0, "locked_cells": locked, "active_cells": active,
		"ghost_cells": ghost, "probe_markers": [], "event_markers": [], "particles": []}


# Deterministic integer hash (no engine RNG), so fixtures are reproducible.
static func _hash(values: Array, seed: int) -> int:
	var h := (seed * 2654435761 + 97) & 0x7FFFFFFF
	for value in values:
		h = (h ^ (int(value) + 0x9E3779B9 + ((h << 6) & 0x7FFFFFFF) + (h >> 2))) & 0x7FFFFFFF
		h = (h * 1103515245 + 12345) & 0x7FFFFFFF
	return h


# Cells of rows [first_row, last_row] filled at density percent, colours 1..7,
# skipping excluded cells. Every W slice is filled when slices is empty.
static func _fill(shape: Array, first_row: int, last_row: int, density: int, seed: int, exclude: Array, slices: Array = []) -> Array:
	var excluded := {}
	for coord in exclude:
		excluded[str(coord)] = true
	var result: Array = []
	var w_values: Array = [0] if shape.size() == 3 else (slices if not slices.is_empty() else range(shape[3]))
	for w in w_values:
		for y in range(first_row, last_row + 1):
			for z in range(shape[2]):
				for x in range(shape[0]):
					var coord: Array = [x, y, z] if shape.size() == 3 else [x, y, z, w]
					if excluded.has(str(coord)):
						continue
					if _hash(coord, seed) % 100 < density:
						result.append([coord, 1 + _hash(coord, seed + 1) % 7])
	return result


static func _piece(offsets: Array, origin: Array) -> Array:
	var cells: Array = []
	for offset in offsets:
		var cell: Array = []
		for axis in range(origin.size()):
			cell.append(int(origin[axis]) + int(offset[axis]))
		cells.append(cell)
	return cells


static func _merge(parts: Array) -> Array:
	var seen := {}
	var result: Array = []
	for part in parts:
		for entry in part:
			if not seen.has(str(entry[0])):
				seen[str(entry[0])] = true
				result.append(entry)
	return result


static func _column(x: int, z: int, first_row: int, last_row: int, color: int) -> Array:
	var result: Array = []
	for y in range(first_row, last_row + 1):
		result.append([[x, y, z], color])
	return result


# 3D camera (yaw 32, pitch +26) sits on the +X/+Z side above the board, so
# x=5,z=5 is the front corner; along the view ray a cell overlaps the cell at
# (+2, -2, +3) in front of it. 4D (yaw 205, reflected) puts x=0,z=0 in front and
# tiles W slices left to right.
func scenes() -> Array:
	var s3 := [6, 10, 6]
	var tripod3 := [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
	var s4 := [5, 10, 4, 4]
	var s7 := [5, 10, 4, 7]
	var tripod4 := [[0, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]
	var spanning4 := [[0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1], [0, 1, 0, 1]]
	var result: Array = []
	var active: Array

	active = _piece(tripod3, [2, 1, 2])
	result.append({"id": "3d_fresh", "dim": 3, "shape": s3, "active": active, "locked": []})
	active = _piece(tripod3, [2, 3, 2])
	result.append({"id": "3d_sparse", "dim": 3, "shape": s3, "active": active, "locked": _fill(s3, 8, 9, 18, 11, active)})
	active = _piece(tripod3, [2, 2, 2])
	result.append({"id": "3d_moderate", "dim": 3, "shape": s3, "active": active,
		"locked": _merge([_fill(s3, 6, 9, 55, 23, active), _fill(s3, 5, 5, 15, 29, active)])})
	active = _piece(tripod3, [2, 0, 2])
	result.append({"id": "3d_dense", "dim": 3, "shape": s3, "active": active, "locked": _fill(s3, 3, 9, 72, 37, active)})
	# Active piece at the front with a settled back wall behind it on screen.
	active = _piece(tripod3, [3, 4, 4])
	var back_wall: Array = _fill(s3, 4, 9, 65, 41, active).filter(func(entry: Array) -> bool: return entry[0][2] <= 2)
	var front_floor: Array = _fill(s3, 8, 9, 40, 43, active).filter(func(entry: Array) -> bool: return entry[0][2] >= 3)
	result.append({"id": "3d_front", "dim": 3, "shape": s3, "active": active, "locked": _merge([back_wall, front_floor])})
	# Active piece behind a settled front wall that covers part of it.
	active = _piece(tripod3, [2, 4, 1])
	var front_wall: Array = _fill(s3, 3, 9, 70, 47, active).filter(func(entry: Array) -> bool: return entry[0][2] >= 4)
	var back_floor: Array = _fill(s3, 8, 9, 40, 53, active).filter(func(entry: Array) -> bool: return entry[0][2] < 4)
	result.append({"id": "3d_behind", "dim": 3, "shape": s3, "active": active, "locked": _merge([front_wall, back_floor])})
	# Projection overlap across a depth gap: the floating front piece covers a
	# distant settled column on screen with no contact between them.
	active = _piece(tripod3, [3, 3, 4])
	result.append({"id": "3d_overlap", "dim": 3, "shape": s3, "active": active,
		"locked": _merge([_column(1, 1, 5, 9, 1), _column(2, 1, 6, 9, 4), _fill(s3, 9, 9, 35, 59, active)])})

	active = _piece(tripod4, [2, 1, 1, 1])
	result.append({"id": "4d_fresh", "dim": 4, "shape": s4, "active": active, "locked": []})
	active = _piece(tripod4, [2, 3, 1, 1])
	result.append({"id": "4d_sparse", "dim": 4, "shape": s4, "active": active, "locked": _fill(s4, 8, 9, 15, 61, active)})
	active = _piece(tripod4, [2, 3, 1, 1])
	result.append({"id": "4d_populated", "dim": 4, "shape": s4, "active": active, "locked": _merge([
		_fill(s4, 6, 9, 50, 67, active, [0]), _fill(s4, 7, 9, 40, 71, active, [1]),
		_fill(s4, 5, 9, 60, 73, active, [2]), _fill(s4, 8, 9, 30, 79, active, [3])])})
	active = _piece(tripod4, [2, 1, 1, 2])
	result.append({"id": "4d_dense", "dim": 4, "shape": s4, "active": active, "locked": _fill(s4, 4, 9, 72, 83, active)})
	# Sparse active slice between dense neighbours.
	active = _piece(tripod4, [2, 4, 1, 1])
	result.append({"id": "4d_neighbours", "dim": 4, "shape": s4, "active": active, "locked": _merge([
		_fill(s4, 4, 9, 70, 89, active, [0, 2]), _fill(s4, 8, 9, 25, 97, active, [1]), _fill(s4, 7, 9, 45, 101, active, [3])])})
	active = _piece(spanning4, [2, 3, 1, 1])
	result.append({"id": "4d_spanning", "dim": 4, "shape": s4, "active": active, "locked": _fill(s4, 6, 9, 45, 103, active)})
	active = _piece(tripod4, [2, 3, 1, 3])
	result.append({"id": "4d_seven", "dim": 4, "shape": s7, "active": active, "locked": _merge([
		_fill(s7, 7, 9, 40, 107, active, [3]), _fill(s7, 5, 9, 60, 109, active, [2, 4]),
		_fill(s7, 7, 9, 35, 113, active, [1, 5]), _fill(s7, 8, 9, 20, 127, active, [0, 6])])})
	# Rows below the piece where the fixture ghost sits on the fixture stack.
	var ghost_rows := {"3d_fresh": 7, "3d_sparse": 3, "3d_moderate": 2, "3d_dense": 1, "3d_front": 2,
		"3d_behind": 2, "3d_overlap": 5, "4d_fresh": 7, "4d_sparse": 4, "4d_populated": 5, "4d_dense": 1,
		"4d_neighbours": 3, "4d_spanning": 3, "4d_seven": 3}
	for scene in result:
		scene["color"] = 3
		scene["ghost_rows"] = ghost_rows[scene.id]
	return result
