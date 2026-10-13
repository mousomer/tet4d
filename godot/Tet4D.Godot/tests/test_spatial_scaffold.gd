extends RefCounted

const Renderer = preload("res://scripts/rendering/trace_scene_renderer.gd")
const GridMode = preload("res://scripts/presentation/grid_display_mode.gd")
const Catalog = preload("res://scripts/presentation/built_in_style_catalog.gd")
const Registry = preload("res://scripts/ui/settings/settings_registry.gd")
const Visuals = preload("res://scripts/ui/replay_visuals.gd")
const Profile = preload("res://scripts/presentation/presentation_profile.gd")

func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var registry = Registry.new()
	registry.load_from_path(Registry.REGISTRY_PATH)
	var catalog = Catalog.new(registry)
	var raw_catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Catalog.CATALOG_PATH))
	for entry in raw_catalog.styles:
		for setting in ["board.enclosure_opacity", "board.back_scaffold_opacity", "board.cell_volume_opacity"]:
			if not entry.presentation_profile.values.has(setting):
				failures.append("every shipped style must explicitly own " + setting)
	var renderer = Renderer.new()
	tree.root.add_child(renderer)
	await tree.process_frame
	var background = preload("res://scripts/rendering/animated_background.gd").new()
	tree.root.add_child(background)
	if background.material_override.render_priority >= -30:
		failures.append("environment must render before every transparent scaffold role")
	background.queue_free()
	var role_sets: Array = []
	for mode in [GridMode.Mode.NONE, GridMode.Mode.BORDER, GridMode.Mode.FULL]:
		role_sets.append(GridMode.roles(mode))
	if role_sets[0].size() != 2 or role_sets[1].size() != 4 or role_sets[2].size() != 5:
		failures.append("scaffold hierarchy must be strictly cumulative")
	for index in range(2):
		for role in role_sets[index]:
			if not role_sets[index + 1].has(role): failures.append("cumulative scaffold lost " + role)
	# Topology signature per dimension/mode; every style must reproduce it.
	var signatures: Dictionary = {}
	for dimension in [2, 3, 4]:
		var source := _snapshot(dimension)
		var unchanged := source.duplicate(true)
		for style in catalog.list_styles():
			var profile = catalog.style_profile(style.style_id).profile
			for mode in [0, 1, 2, 0, 2, 1, 0]:
				renderer.apply_presentation_profile(profile.with_overrides({"display.grid_mode": GridMode.to_value(mode)}))
				renderer.render_snapshot(source)
				var grid = renderer.get_node("GridRoot").get_child(0)
				var expected := GridMode.roles(mode)
				for role in GridMode.roles(0):
					if not _nodes(grid, role).is_empty() != expected.has(role):
						failures.append("%dd %s %s role %s" % [dimension, style.style_id, GridMode.to_value(mode), role])
				var slices := 3 if dimension == 4 else 1
				for role in [GridMode.ENCLOSURE, GridMode.FLOOR]:
					if _nodes(grid, role).size() != slices: failures.append("duplicate/missing " + role)
				var geometry = renderer._presentation.projection.mapper.local_geometry()
				_test_topology(failures, grid, geometry, mode, slices, signatures, "%dd %s %s" % [dimension, style.style_id, GridMode.to_value(mode)])
				var cells := _nodes(grid, GridMode.GRID_INTERIOR)
				if mode == 0:
					var segments: Array = _interior_lines(geometry)
					if cells.size() != (slices if not segments.is_empty() else 0): failures.append("FULL must batch internal edges once per spatial slice")
					for cell in cells:
						if not cell is MultiMeshInstance3D or cell.multimesh.instance_count != segments.size():
							failures.append("FULL must contain canonical unique internal lines")
						for index in range(cell.multimesh.instance_count):
							# The headless dummy renderer returns identity for GPU readback.
							# Exercise the production transform builder there; real-window
							# runs additionally inspect the actual MultiMesh transforms.
							var basis: Basis = preload("res://scripts/rendering/grid_renderer.gd").segment_transform(segments[index], Visuals.grid_internal_thickness(bool(profile.value("accessibility.high_contrast")))).basis
							if DisplayServer.get_name() != "headless": basis = cell.multimesh.get_instance_transform(index).basis
							var thin_axes := int(basis.x.length() < 0.1) + int(basis.y.length() < 0.1) + int(basis.z.length() < 0.1)
							if thin_axes != 2: failures.append("internal batches must contain thin edges, never cell-volume boxes")
						var material: StandardMaterial3D = cell.material_override
						var expected_alpha := Visuals.board_internal_scaffold_material(str(profile.value("theme.name")), float(profile.value("board.cell_volume_opacity")), bool(profile.value("accessibility.high_contrast"))).albedo_color.a
						if material.get_meta("scaffold_setting") != "board.cell_volume_opacity" or not is_equal_approx(material.albedo_color.a, expected_alpha):
							failures.append("internal edges must use resolved style/accessibility alpha")
						if material.render_priority >= 0 or material.albedo_color.a * 3.0 >= Visuals.ghost_cell_material().albedo_color.a:
							failures.append("internal depth/order/alpha must remain subordinate to Ghost")
				if not _nodes(grid, "board.cell_volumes").is_empty(): failures.append("no filled cell-volume role may remain")
				var enclosure: StandardMaterial3D = _nodes(grid, GridMode.ENCLOSURE)[0].material_override
				if not is_equal_approx(enclosure.albedo_color.a, Visuals.board_enclosure_material(str(profile.value("theme.name")), float(profile.value("board.enclosure_opacity")), float(profile.value("board.boundary_opacity")), bool(profile.value("accessibility.high_contrast"))).albedo_color.a):
					failures.append("enclosure must use resolved style alpha")
				if mode != 2:
					var line: StandardMaterial3D = _nodes(grid, GridMode.GRID_EDGE).filter(func(n): return n is MultiMeshInstance3D)[0].material_override
					var expected_alpha := Visuals.board_scaffold_material(str(profile.value("theme.name")), Visuals.scaffold_alpha(float(profile.value("board.back_scaffold_opacity")), float(profile.value("board.grid_opacity"))), bool(profile.value("accessibility.high_contrast"))).albedo_color.a
					if not is_equal_approx(line.albedo_color.a, expected_alpha) or line.albedo_color.a > 0.6:
						failures.append("border lattice must use subordinate resolved style alpha")
				if dimension == 4:
					var frames := _nodes(grid, "board.frame_active").filter(func(n): return n.is_visible_in_tree())
					if frames.size() != 1 or grid._slice_labels.size() != 3: failures.append("active slice and labels must survive every mode")
				var generation: int = grid.scaffold_generation
				var moved := source.duplicate(true)
				moved.active_cells[0].position[0] = 1
				moved.frame_index = 1
				renderer.render_snapshot(moved)
				if grid.scaffold_generation != generation: failures.append("piece movement must not rebuild static scaffold")
				var replay := source.duplicate(true)
				replay.trace_type = "gameplay"
				renderer.render_snapshot(replay)
				for role in GridMode.roles(0):
					if not _nodes(grid, role).is_empty() != expected.has(role): failures.append("replay scaffold role parity: " + role)
				if dimension < 4 and grid.scaffold_generation != generation: failures.append("replay must reuse identical static geometry")
			if source != unchanged: failures.append("scaffold transitions mutated gameplay snapshot")
	await _test_opacity_authoring(failures, renderer, registry)
	_test_unique_edges(failures)
	_test_shallow_parity(failures, renderer)
	_test_invalidation(failures, renderer)
	_test_transition_refresh(failures, renderer)
	for shape in [[10,20], [6,10,6], [5,10,4,4], [12,40], [10,24,10], [12,16,12,12]]:
		var snapshot := _snapshot(shape.size())
		snapshot.board_shape = shape
		renderer.apply_presentation_profile(Profile.canonical_defaults().with_overrides({"display.grid_mode":"full"}))
		var start := Time.get_ticks_usec()
		renderer.render_snapshot(snapshot)
		var elapsed := Time.get_ticks_usec() - start
		var grid = renderer.get_node("GridRoot").get_child(0)
		var batches := _nodes(grid, GridMode.GRID_INTERIOR)
		var instances := 0
		for batch in batches: instances += batch.multimesh.instance_count
		var count := _node_count(grid)
		if batches.size() != (shape[3] if shape.size() == 4 else 1) or count > 35 * (shape[3] if shape.size() == 4 else 1):
			failures.append("FULL node budget must scale by slices/faces, never by cells")
		print("SCAFFOLD_BUDGET ", shape, " edges=", instances, " nodes=", count, " batches=", batches.size(), " rebuild_us=", elapsed)
	renderer.queue_free()
	await tree.process_frame
	return failures

# Grid mode alone fixes topology: exact maximal-line counts, one identical
# lattice per 4D slice, and a signature no style may change. Styles may only
# differ in material (colour, alpha, width, depth behaviour).
func _test_topology(failures: Array, grid, geometry, mode: int, slices: int, signatures: Dictionary, label: String) -> void:
	var dims: Array = geometry.local_dimensions
	var expected: int = [
		(dims[1] + 1) * (dims[2] + 1) + (dims[0] + 1) * (dims[2] + 1) + (dims[0] + 1) * (dims[1] + 1),
		4 * (dims[0] + dims[1] + dims[2]), 0][mode]
	var topology: Array = grid.grid_topology()
	if topology.size() != slices:
		failures.append("%s: expected %d slice lattices, got %d" % [label, slices, topology.size()])
		return
	for slice_lines in topology:
		if slice_lines.size() != expected:
			failures.append("%s: expected %d maximal lines per slice, got %d" % [label, expected, slice_lines.size()])
		if slice_lines != topology[0]:
			failures.append("%s: equal-dimension slices must share one grid topology" % label)
		for line in slice_lines:
			var axis: int = line[0]
			if line[1][axis] != 0 or line[2][axis] != int(dims[axis]):
				failures.append("%s: rendered line %s must span an entire board axis" % [label, str(line)])
				break
	_test_rear_faces(failures, grid, mode, label)
	var key := "%s:%d:%d" % [str(dims), slices, mode]
	var signature := hash(topology)
	if not signatures.has(key):
		signatures[key] = signature
	elif signatures[key] != signature:
		failures.append("%s: style changed grid topology signature" % label)


# BORDER shows its 12 edges always and face lines only on camera-relative rear
# faces; FULL never hides a face. Camera changes visibility, never topology.
func _test_rear_faces(failures: Array, grid, mode: int, label: String) -> void:
	var built: Array = grid.grid_topology()
	for camera in [Vector3(10,10,10), Vector3(-10,10,-10), Vector3(10,-10,-10), Vector3(-10,-10,10), Vector3(0,0,100)]:
		grid._update_rear_faces(camera * 10)
		if grid.grid_topology() != built:
			failures.append("%s: camera must not change built grid topology" % label)
		var faces := _nodes_with_meta(grid, "grid_axis")
		if mode != GridMode.Mode.NONE and faces.is_empty():
			failures.append("%s: boundary-face lines must batch per face" % label)
		for face in faces:
			var rear: bool = face.get_meta("grid_normal").dot(camera * 10 - face.get_meta("grid_center")) < -0.0001
			var expected_visible := rear if mode == GridMode.Mode.BORDER else true
			if face.visible != expected_visible:
				failures.append("%s: face %s visibility must be %s" % [label, face.name, expected_visible])
				return
		for edges in _nodes(grid, GridMode.GRID_EDGE):
			if not edges.is_visible_in_tree():
				failures.append("%s: outer edges must stay visible from every camera" % label)
				return
		if mode == GridMode.Mode.BORDER:
			var visible: Array = grid.grid_topology(true)
			var face_lines := 0
			for face in faces:
				if face.visible:
					face_lines += int(face.get_child(0).get_meta("segment_count"))
			var slices: int = visible.size()
			var shown := 0
			for slice_lines in visible: shown += slice_lines.size()
			if shown != 12 * slices + face_lines:
				failures.append("%s: visible Border must be 12 edges plus rear-face lines" % label)
				return


func _nodes_with_meta(node: Node, meta: String) -> Array:
	var result: Array = []
	for child in node.get_children():
		if child.has_meta(meta): result.append(child)
		result.append_array(_nodes_with_meta(child, meta))
	return result


func _interior_lines(geometry) -> Array:
	return geometry.lattice_geometry().filter(func(line: Dictionary) -> bool:
		return GridMode.lattice_role(line) == GridMode.GRID_INTERIOR)


func _test_invalidation(failures: Array, renderer) -> void:
	var snapshot := _snapshot(4)
	renderer.apply_presentation_profile(Profile.canonical_defaults().with_overrides({"display.grid_mode":"full"}))
	renderer.render_snapshot(snapshot)
	var grid = renderer.get_node("GridRoot").get_child(0)
	var generation: int = grid.scaffold_generation
	snapshot.active_cells[0].position[3] = 2
	renderer.render_snapshot(snapshot)
	if grid.scaffold_generation != generation or not grid._active_frames[2].visible or grid._active_frames[1].visible:
		failures.append("active slice changes only independent navigation")
	for change in [{"display.grid_mode":"border"}, {"board.grid_opacity":0.4}]:
		renderer.apply_presentation_profile(renderer._presentation_profile.with_overrides(change))
		renderer.render_snapshot(snapshot)
		if grid.scaffold_generation <= generation: failures.append("structural/material input must invalidate cache")
		generation = grid.scaffold_generation
	renderer.apply_presentation_profile(renderer._presentation_profile.with_overrides({"slice_set.spacing":1.2}))
	renderer.render_snapshot(snapshot)
	if grid.scaffold_generation != generation:
		failures.append("inert legacy spacing must not rebuild canonical geometry")
	snapshot.board_shape = [4,5,3,3]
	renderer.render_snapshot(snapshot)
	if grid.scaffold_generation <= generation: failures.append("dimensions must invalidate cache")

func _snapshot(dimension: int) -> Dictionary:
	var shape := [3,4] if dimension == 2 else ([3,4,2] if dimension == 3 else [3,4,2,3])
	# Equal local cell count for all matrix modes, including the 2D slab.
	if dimension == 2: shape = [4,6]
	var coordinate := [0,1] if dimension == 2 else ([0,1,0] if dimension == 3 else [0,1,0,1])
	return {"case_id":"scaffold_regression", "trace_type":"live_%dd" % dimension, "dimension":dimension, "board_shape":shape, "frame_index":0,
		"active_cells":[{"position":coordinate,"color_id":1}], "locked_cells":[], "ghost_cells":[], "particles":[], "event_markers":[], "probe_markers":[],
		"state_hash":"unchanged_authoritative_state", "score":12, "seed":100, "topology":{"mode":"plain"}}

func _nodes(node: Node, role: String) -> Array:
	var result: Array = []
	if str(node.get_meta("presentation_role", "")) == role: result.append(node)
	for child in node.get_children(): result.append_array(_nodes(child, role))
	return result

func _node_count(node: Node) -> int:
	var count := 1
	for child in node.get_children(): count += _node_count(child)
	return count


func _test_shallow_parity(failures: Array, renderer) -> void:
	for mode in [0, 1, 2]:
		var reference: Array = []
		for dimension in [2, 3, 4]:
			var snapshot := _snapshot(dimension)
			snapshot.board_shape = [4,6] if dimension == 2 else ([4,6,1] if dimension == 3 else [4,6,1,1])
			if dimension == 4: snapshot.active_cells[0].position[3] = 0
			renderer.apply_presentation_profile(Profile.canonical_defaults().with_overrides({"display.grid_mode": GridMode.to_value(mode)}))
			renderer.render_snapshot(snapshot)
			var grid = renderer.get_node("GridRoot").get_child(0)
			var signature: Array = []
			for role in GridMode.roles(mode):
				for node in _nodes(grid, role):
					if node is MeshInstance3D:
						signature.append([role, node.mesh.size, node.position])
					elif node is MultiMeshInstance3D:
						var transforms: Array = []
						for index in range(node.multimesh.instance_count): transforms.append(node.multimesh.get_instance_transform(index))
						signature.append([role, node.multimesh.mesh.size, transforms])
			if dimension == 2: reference = signature
			elif signature != reference: failures.append("real renderer shallow dimensional scaffold parity")


func _test_transition_refresh(failures: Array, renderer) -> void:
	var source := _snapshot(4)
	renderer.set_live_4d_basis(preload("res://scripts/presentation/slice_basis_4d.gd").identity(), false)
	renderer.render_snapshot(source)
	renderer.set_live_4d_basis(preload("res://scripts/presentation/slice_basis_4d.gd").identity().turned("xz", 1), true)
	renderer.render_snapshot(source)
	renderer._process(0.08)
	var before: Transform3D = renderer.transform
	var grid = renderer.get_node("GridRoot").get_child(0)
	var generation: int = grid.scaffold_generation
	source.frame_index += 1
	source.active_cells[0].position[0] = 1
	renderer.render_snapshot(source)
	if not renderer.transform.is_equal_approx(before):
		failures.append("gameplay refresh must not restart an in-progress view settle pose")
	if grid.scaffold_generation != generation:
		failures.append("gameplay during view settle must retain scaffold generation")
	renderer.set_live_4d_basis(preload("res://scripts/presentation/slice_basis_4d.gd").identity(), false)


func _test_unique_edges(failures: Array) -> void:
	var geometry = preload("res://scripts/presentation/local_board_presentation_geometry.gd").new()
	for shape in [[1,1,1], [4,6,1], [3,4,2], [12,16,12]]:
		geometry.configure(shape, [1,2,3])
		var segments: Array = _interior_lines(geometry)
		var expected: int = (shape[1]-1)*(shape[2]-1) + (shape[0]-1)*(shape[2]-1) + (shape[0]-1)*(shape[1]-1)
		if segments.size() != expected: failures.append("internal line count must merge shared edges")
		var seen: Dictionary = {}
		for segment in segments:
			var key := str(segment.start) + str(segment.end)
			if seen.has(key): failures.append("duplicate shared internal edge")
			seen[key] = true
			var axis: int = segment.line_axis
			for perpendicular in range(3):
				if perpendicular != axis and absf(segment.start[perpendicular]) >= geometry.local_extent[perpendicular] * 0.5:
					failures.append("internal edges must exclude boundary-face subdivisions")


func _test_opacity_authoring(failures: Array, renderer, registry) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var panel = preload("res://scripts/ui/settings_panel.gd").new()
	tree.root.add_child(panel)
	var designer = preload("res://scripts/ui/presentation_designer.gd").new()
	tree.root.add_child(designer)
	await tree.process_frame
	var path := "user://scaffold_authoring_test_%d" % Time.get_ticks_usec()
	var library = preload("res://scripts/presentation/presentation_profile_library.gd").new(registry, path)
	var profile = Profile.canonical_defaults().with_overrides({"display.grid_mode":"full"}).with_design_state({"panel_rects":{"GameArea":[10,20,400,500]}})
	designer.configure(registry, library)
	designer.open_with_profile(profile, "live_3d")
	await tree.process_frame
	var source := _snapshot(3)
	if Profile.canonical_defaults().value("display.grid_mode") != "border" or GridMode.from_value("invalid") != GridMode.Mode.BORDER:
		failures.append("fresh sessions and invalid grid fallback must default to Border")
	var advanced := designer.find_child("DesignerAdvancedSettings", true, false)
	var rows := advanced.get_node("AdvancedParameters") as Control
	if rows.visible: failures.append("Advanced Settings must initially collapse")
	(advanced.get_child(0) as Button).button_pressed = true
	for setting in ["board.enclosure_opacity", "board.back_scaffold_opacity", "board.cell_volume_opacity"]:
		for context in ["global_settings", "live_2d", "live_3d", "live_4d"]:
			panel.set_presentation_context(context)
			if panel.generated_control(setting) != null: failures.append("normal Settings must not construct " + setting)
		var slider = designer.control_for_setting(setting)
		if not slider is HSlider or not rows.is_ancestor_of(slider) or not slider.is_visible_in_tree():
			failures.append("Designer Advanced Settings must expose " + setting)
		renderer.apply_presentation_profile(designer.working_profile())
		renderer.render_snapshot(source)
		var grid = renderer.get_node("GridRoot").get_child(0)
		var generation: int = grid.scaffold_generation
		var before: Dictionary = designer.working_profile().snapshot()
		var materials: Dictionary = {}
		for role in [GridMode.ENCLOSURE, GridMode.GRID_EDGE, GridMode.GRID_FACE, GridMode.GRID_INTERIOR]:
			var nodes := _nodes(grid, role).filter(func(n): return n is GeometryInstance3D)
			materials[role] = nodes[0].material_override.albedo_color.a
		slider.value = {"board.enclosure_opacity":0.25,"board.back_scaffold_opacity":0.5,"board.cell_volume_opacity":0.06}[setting]
		var after: Dictionary = designer.working_profile().snapshot()
		before.values[setting] = after.values[setting]
		if before != after: failures.append("opacity edit changed unrelated design state")
		renderer.apply_presentation_profile(designer.working_profile())
		renderer.render_snapshot(source)
		if grid.scaffold_generation != generation: failures.append("opacity must only update cached material")
		for role in materials:
			var node = _nodes(grid, role).filter(func(n): return n is GeometryInstance3D)[0]
			var changed := not is_equal_approx(float(materials[role]), node.material_override.albedo_color.a)
			if changed != (node.material_override.get_meta("scaffold_setting") == setting):
				failures.append("slider must change only its corresponding material")
	var saved: Dictionary = designer.save_working_as("Scaffold regression")
	var saved_profile: Dictionary = designer.working_profile().snapshot()
	designer.reset_working_to_factory_defaults()
	if not saved.get("ok",false) or not designer.load_saved_profile(saved.record.profile_id).get("ok",false) or designer.working_profile().snapshot() != saved_profile:
		failures.append("Designer save/load must preserve scaffold values and design state")
	if saved.get("ok",false): library.delete_profile(saved.record.profile_id)
	DirAccess.remove_absolute(path)
	for material in [Visuals.board_enclosure_material("plain",0.005,0.1,true), Visuals.board_scaffold_material("plain",0.005,true), Visuals.board_internal_scaffold_material("plain",0.005,true)]:
		if material.albedo_color.a <= 0.005: failures.append("High Contrast must compose after stored opacity")
	designer.queue_free()
	panel.queue_free()
	await tree.process_frame
