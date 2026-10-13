extends RefCounted

# Style controls appearance; grid mode controls lattice/boundary topology.
# Every style import must preserve the grid selection, and every grid change
# must preserve the active style, as observed in the renderer itself.

const CatalogScript = preload("res://scripts/presentation/built_in_style_catalog.gd")
const GridDisplayMode = preload("res://scripts/presentation/grid_display_mode.gd")
const ProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

const GRID_MODES := ["full", "border", "none"]
const INTERNAL_ROLES := ["board.grid_edge"]
const BOUNDARY_ROLES := ["board.enclosure", "board.floor"]

# Grid topology signature per board/slices/mode; no style may change it.
var _topology_signatures: Dictionary = {}


func run() -> Array:
	var failures: Array = []
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var catalog = CatalogScript.new(registry)
	# Derived from the shipped catalog so a new style cannot escape the contract.
	var style_ids: Array = []
	for record in catalog.list_styles():
		style_ids.append(str(record.get("style_id", "")))
	if style_ids.size() < 4 or not catalog.diagnostics().is_empty():
		return ["style × grid matrix requires a healthy catalog with at least four styles"]
	_test_composition_rule(failures, catalog, style_ids)

	var tree := Engine.get_main_loop() as SceneTree
	var root := (load("res://scenes/designer_bootstrap.tscn") as PackedScene).instantiate()
	tree.root.add_child(root)
	await _frames(tree, 10)
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	hud._settings_store._storage_path = "user://test_style_grid_settings_%s.json" % OS.get_process_id()
	await _test_design_laboratory(failures, tree, app, hud, catalog, style_ids)
	await _test_settings_theme(failures, tree, app, hud)
	for mode_name in ["live_2d", "live_3d", "live_4d"]:
		await _enter(tree, app, mode_name)
		await _test_mode_sequence(failures, tree, app, hud, mode_name)
		await _test_designer_matrix(failures, tree, app, hud, catalog, style_ids, mode_name)
	await _test_designer_transitions(failures, tree, app, hud, catalog, style_ids)
	await _test_library_and_slots(failures, tree, app, hud, catalog, style_ids)
	await _test_native_refresh_cache(failures, tree, app, hud)
	hud._presentation_designer.end_session()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(hud._settings_store._storage_path))
	root.queue_free()
	await tree.process_frame
	return failures


func _test_composition_rule(failures: Array, catalog, style_ids: Array) -> void:
	for style_id in style_ids:
		var style = catalog.style_profile(style_id).get("profile")
		for grid_mode in GRID_MODES:
			var current = ProfileScript.canonical_defaults().with_overrides({"display.grid_mode": grid_mode})
			var composed = current.with_style_of(style)
			var expected: Dictionary = style.values()
			for setting_id in ProfileScript.STYLE_INDEPENDENT_IDS:
				expected[setting_id] = current.value(setting_id)
			if not composed.contract_conforms() or composed.values() != expected:
				failures.append("%s over %s must keep the grid selection and every style value" % [style_id, grid_mode])


# Design Laboratory "Apply Live" previously adopted each preset's stored FULL.
func _test_design_laboratory(failures: Array, tree: SceneTree, app, hud, catalog, style_ids: Array) -> void:
	await _enter(tree, app, "live_3d")
	var lab = hud._design_laboratory
	lab.open()
	await _frames(tree, 3)
	var select: OptionButton = lab._catalog_select
	for grid_mode in GRID_MODES:
		await _select_grid(tree, hud, grid_mode)
		for index in range(select.item_count):
			var descriptor: Dictionary = select.get_item_metadata(index)
			var style_id := str(descriptor.get("preset_id", ""))
			if str(descriptor.get("source_kind", "")) != "built_in" or not style_ids.has(style_id):
				continue
			select.select(index)
			lab._apply_selected()
			await _frames(tree, 2)
			_assert_rendered(failures, app, catalog, style_id, grid_mode, "Design Laboratory %s over %s" % [style_id, grid_mode])
			if str(hud._settings_store.value("display.grid_mode")) != grid_mode:
				failures.append("Design Laboratory %s must not desynchronize persisted grid mode" % style_id)
	lab.close()
	await _frames(tree, 3)


# Ordinary gameplay's style control is Settings → Theme, a one-parameter edit.
func _test_settings_theme(failures: Array, tree: SceneTree, app, hud) -> void:
	var panel = hud._settings_panel
	if panel == null:
		failures.append("Settings theme coverage requires the HUD settings panel")
		return
	for grid_mode in GRID_MODES:
		await _select_grid(tree, hud, grid_mode)
		for theme in ReplayVisuals.DISPLAY_MODES:
			panel._on_control_value_changed("theme.name", theme)
			await _frames(tree, 2)
			var label := "Settings theme %s over %s" % [theme, grid_mode]
			var internals := _assert_topology(failures, app, grid_mode, label)
			var profile = hud.presentation_profile()
			if app._renderer._display_mode != theme or str(profile.value("display.grid_mode")) != grid_mode:
				failures.append("%s: theme and grid selections must both survive" % label)
			var lattice := internals.filter(func(node: Node) -> bool: return node is MultiMeshInstance3D)
			if not lattice.is_empty():
				var expected := ReplayVisuals.board_scaffold_material(theme, ReplayVisuals.scaffold_alpha(float(profile.value("board.back_scaffold_opacity")), float(profile.value("board.grid_opacity")))).albedo_color
				if not (lattice[0] as MultiMeshInstance3D).material_override.albedo_color.is_equal_approx(expected):
					failures.append("%s: lattice must use the selected theme material" % label)


func _test_designer_matrix(failures: Array, tree: SceneTree, app, hud, catalog, style_ids: Array, mode_name: String) -> void:
	var designer = await _open_designer(tree, hud)
	# Test 1: grid selected first, then style applied.
	for grid_mode in GRID_MODES:
		for style_id in style_ids:
			await _select_grid(tree, hud, grid_mode)
			designer.apply_built_in_style(style_id)
			await _frames(tree, 2)
			_assert_rendered(failures, app, catalog, style_id, grid_mode, "%s Designer style %s after grid %s" % [mode_name, style_id, grid_mode])
	# Test 2: style applied first, then every grid mode through both controls.
	for style_id in style_ids:
		designer.apply_built_in_style(style_id)
		for grid_mode in GRID_MODES:
			await _select_grid(tree, hud, grid_mode)
			_assert_rendered(failures, app, catalog, style_id, grid_mode, "%s HUD grid %s under %s" % [mode_name, grid_mode, style_id])
			if designer.deterministic_snapshot()["applied_style_id"] != style_id:
				failures.append("%s HUD grid %s must keep Designer style identity %s" % [mode_name, grid_mode, style_id])
		for grid_mode in GRID_MODES:
			designer.set_parameter_value("display.grid_mode", grid_mode)
			await _frames(tree, 2)
			_assert_rendered(failures, app, catalog, style_id, grid_mode, "%s Designer grid %s under %s" % [mode_name, grid_mode, style_id])


func _test_designer_transitions(failures: Array, tree: SceneTree, app, hud, catalog, style_ids: Array) -> void:
	await _enter(tree, app, "live_3d")
	var designer = await _open_designer(tree, hud)
	var a: String = style_ids[1]
	var b: String = style_ids[2]
	var c: String = style_ids[3]
	designer.apply_built_in_style(style_ids[0])
	await _select_grid(tree, hud, "full")
	var expected_style := style_ids[0] as String
	var expected_grid := "full"
	var state_before: Dictionary = app._current_snapshot.duplicate(true)
	var setup_before: Dictionary = app._active_live_setup.duplicate(true)
	for step in [["style", a], ["grid", "none"], ["style", b], ["grid", "full"], ["style", c], ["grid", "border"], ["style", a]]:
		if step[0] == "style":
			designer.apply_built_in_style(step[1])
			expected_style = step[1]
		else:
			await _select_grid(tree, hud, step[1])
			expected_grid = step[1]
		await _frames(tree, 2)
		_assert_rendered(failures, app, catalog, expected_style, expected_grid, "transition %s %s" % step)
		if app._current_snapshot != state_before or app._active_live_setup != setup_before:
			failures.append("style/grid transitions must preserve authoritative gameplay and setup")


func _test_library_and_slots(failures: Array, tree: SceneTree, app, hud, catalog, style_ids: Array) -> void:
	var designer = await _open_designer(tree, hud)
	var x: String = style_ids[3]
	var y: String = style_ids[1]
	designer.apply_built_in_style(x)
	designer.set_parameter_value("display.grid_mode", "border")
	var expected_saved: Dictionary = designer.working_profile().values()
	var saved: Dictionary = designer.save_working_as("Grid Composition %s" % OS.get_process_id())
	var profile_id := str(saved.get("record", {}).get("profile_id", ""))
	var stored: Dictionary = designer._profile_library.load_profile(profile_id)
	if not bool(stored.get("ok", false)) or stored.get("profile").values() != expected_saved:
		failures.append("library must round-trip style %s with grid border exactly" % x)
	designer.apply_built_in_style(y)
	designer.set_parameter_value("display.grid_mode", "none")
	designer.load_saved_profile(profile_id)
	await _frames(tree, 2)
	_assert_rendered(failures, app, catalog, x, "border", "saved design restores border" )
	designer._profile_library.delete_profile(profile_id)

	# Comparison previews restore complete frozen designs independently of current.
	designer.apply_built_in_style(x)
	designer.capture_reference()
	designer.apply_built_in_style(y)
	designer.set_parameter_value("display.grid_mode", "full")
	designer.set_comparison_snapshot("B")
	designer.show_slot("A")
	await _frames(tree, 2)
	_assert_rendered(failures, app, catalog, x, "border", "A restores its frozen grid")
	await _select_grid(tree, hud, "none")
	_assert_rendered(failures, app, catalog, y, "none", "grid edits current and ends preview")
	designer.show_slot("B")
	await _frames(tree, 2)
	_assert_rendered(failures, app, catalog, y, "full", "B retains its frozen grid")


# Returns the rendered lattice nodes after checking FULL/BORDER/NONE topology.
func _assert_topology(failures: Array, app, grid_mode: String, label: String) -> Array:
	var grid_root: Node = app._renderer.get_node("GridRoot")
	var internals := _nodes_with_roles(grid_root, INTERNAL_ROLES)
	var boundaries := _nodes_with_roles(grid_root, BOUNDARY_ROLES)
	var mode := GridDisplayMode.from_value(grid_mode)
	var cells := _nodes_with_roles(grid_root, ["board.grid_interior"])
	if (not cells.is_empty()) != (mode == GridDisplayMode.Mode.FULL):
		failures.append("%s: interior lattice lines belong only to FULL" % label)
	var topology: Array = grid_root.get_child(0).grid_topology()
	var expected := _expected_line_count(app, mode)
	for slice_lines in topology:
		if slice_lines.size() != expected or slice_lines != topology[0]:
			failures.append("%s: each slice must render exactly %d maximal lines, got %d" % [label, expected, slice_lines.size()])
			break
	var key := "%s:%d:%d" % [str(_local_dimensions(app)), topology.size(), mode]
	if not _topology_signatures.has(key):
		_topology_signatures[key] = hash(topology)
	elif _topology_signatures[key] != hash(topology):
		failures.append("%s: style changed grid topology (line count or endpoints)" % label)
	var topology_ok := (
		(mode == GridDisplayMode.Mode.FULL and not internals.is_empty() and not boundaries.is_empty())
		or (mode == GridDisplayMode.Mode.BORDER and not internals.is_empty() and not boundaries.is_empty())
		or (mode == GridDisplayMode.Mode.NONE and internals.is_empty() and not boundaries.is_empty())
	)
	if not topology_ok:
		failures.append("%s: rendered %d lattice / %d boundary nodes, not %s" % [label, internals.size(), boundaries.size(), grid_mode])
	return internals


func _assert_rendered(failures: Array, app, catalog, style_id: String, grid_mode: String, label: String) -> void:
	var style = catalog.style_profile(style_id).get("profile")
	var renderer = app._renderer
	var internals := _assert_topology(failures, app, grid_mode, label)
	var boundaries := _nodes_with_roles(renderer.get_node("GridRoot"), BOUNDARY_ROLES)
	var theme := str(style.value("theme.name"))
	var high_contrast := bool(style.value("accessibility.high_contrast"))
	if renderer._display_mode != theme or renderer._high_contrast != high_contrast:
		failures.append("%s: renderer must keep style %s appearance" % [label, style_id])
	var lattice := internals.filter(func(node: Node) -> bool: return node is MultiMeshInstance3D)
	if not lattice.is_empty():
		var expected := ReplayVisuals.board_scaffold_material(theme, ReplayVisuals.scaffold_alpha(float(style.value("board.back_scaffold_opacity")), float(style.value("board.grid_opacity"))), high_contrast).albedo_color
		if not (lattice[0] as MultiMeshInstance3D).material_override.albedo_color.is_equal_approx(expected):
			failures.append("%s: lattice must use style %s material" % [label, style_id])
	for node in boundaries:
		if node is MeshInstance3D and str(node.get_meta("presentation_role", "")) == "board.enclosure":
			var expected := ReplayVisuals.board_enclosure_material(theme, float(style.value("board.enclosure_opacity")), float(style.value("board.boundary_opacity")), high_contrast).albedo_color
			if not (node as MeshInstance3D).material_override.albedo_color.is_equal_approx(expected):
				failures.append("%s: boundary must use style %s material" % [label, style_id])
			break


func _local_dimensions(app) -> Array:
	return app._renderer._presentation.projection.mapper.local_geometry().local_dimensions


func _expected_line_count(app, mode: int) -> int:
	var d := _local_dimensions(app)
	return [(d[1] + 1) * (d[2] + 1) + (d[0] + 1) * (d[2] + 1) + (d[0] + 1) * (d[1] + 1), 4 * (d[0] + d[1] + d[2]), 0][mode]


# Both control routes must drive one canonical grid value into the renderer:
# None -> Border -> Full -> None yields 0 -> border -> full -> 0 built lines.
func _test_mode_sequence(failures: Array, tree: SceneTree, app, hud, mode_name: String) -> void:
	var designer = await _open_designer(tree, hud)
	var sequence := ["none", "border", "full", "none"]
	for route in ["quick_settings", "designer"]:
		var counts: Array = []
		var expected: Array = []
		for grid_mode in sequence:
			if route == "quick_settings":
				await _select_grid(tree, hud, grid_mode)
			else:
				designer.set_parameter_value("display.grid_mode", grid_mode)
				await _frames(tree, 2)
			var topology: Array = app._renderer.get_node("GridRoot").get_child(0).grid_topology()
			counts.append(topology.map(func(lines: Array) -> int: return lines.size()))
			var mode := GridDisplayMode.from_value(grid_mode)
			expected.append(topology.map(func(_lines: Array) -> int: return _expected_line_count(app, mode)))
			if str(hud.presentation_profile().value("display.grid_mode")) != grid_mode or hud._grid_mode != mode:
				failures.append("%s %s route: UI and renderer must share grid value %s" % [mode_name, route, grid_mode])
		if counts != expected or counts[0].is_empty():
			failures.append("%s %s route: None/Border/Full/None line counts %s, expected %s" % [mode_name, route, str(counts), str(expected)])


func _select_grid(tree: SceneTree, hud, grid_mode: String) -> void:
	# Real HUD control path: the Grid button cycles FULL → BORDER → NONE.
	var target := GridDisplayMode.from_value(grid_mode)
	for attempt in range(GridDisplayMode.VALUES.size()):
		if hud._grid_mode == target:
			break
		hud._grid_toggle_button.pressed.emit()
		await _frames(tree, 2)


func _open_designer(tree: SceneTree, hud):
	if hud._presentation_designer.state() == "hidden":
		hud._open_presentation_designer()
		await _frames(tree, 3)
	return hud._presentation_designer


func _enter(tree: SceneTree, app, mode_name: String) -> void:
	match mode_name:
		"live_2d": app._enter_live_2d_mode()
		"live_3d": app._enter_live_3d_mode()
		_: app._enter_live_4d_mode()
	app._live_2d_paused = true
	app._live_3d_paused = true
	app._live_4d_paused = true
	await _frames(tree, 6)


func _frames(tree: SceneTree, count: int) -> void:
	for frame in range(count):
		await tree.process_frame


func _nodes_with_roles(node: Node, roles: Array) -> Array:
	var found: Array = []
	if roles.has(str(node.get_meta("presentation_role", ""))):
		found.append(node)
	for child in node.get_children():
		found.append_array(_nodes_with_roles(child, roles))
	return found


func _test_native_refresh_cache(failures: Array, tree: SceneTree, app, hud) -> void:
	hud._presentation_designer.end_session()
	await _enter(tree, app, "live_3d")
	await _select_grid(tree, hud, "full")
	var grid = app._renderer.get_node("GridRoot").get_child(0)
	var generation: int = grid.scaffold_generation
	var state_hash := str(app._current_snapshot.get("state_hash", ""))
	app._live_3d_command("soft_drop")
	await _frames(tree, 2)
	if str(app._current_snapshot.get("state_hash", "")) == state_hash:
		failures.append("cache regression requires an actual authoritative piece move")
	if app._renderer.get_node("GridRoot").get_child(0) != grid or grid.scaffold_generation != generation:
		failures.append("native piece refresh must preserve scaffold generation and identity")
