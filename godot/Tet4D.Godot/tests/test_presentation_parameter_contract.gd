extends RefCounted

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const AdaptiveLayerLayoutScript = preload("res://scripts/presentation/adaptive_layer_layout.gd")
const BoardPresentationModelScript = preload("res://scripts/presentation/board_presentation_model.gd")
const TraceSceneRendererScript = preload("res://scripts/rendering/trace_scene_renderer.gd")


func run() -> Array:
	var failures: Array = []
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var defaults = PresentationProfileScript.canonical_defaults()
	if not defaults.contract_conforms():
		failures.append("canonical presentation defaults should validate: %s" % defaults.failures())
	if int(defaults.snapshot().get("schema_version", 0)) != PresentationProfileScript.SCHEMA_VERSION:
		failures.append("presentation profiles should carry their independent schema version")
	if defaults.values().size() != registry.settings.size():
		failures.append("presentation profile should cover every declared registry parameter")
	_assert_equal(failures, defaults.value("board.grid_opacity"), 0.31, "grid opacity default")
	_assert_equal(failures, defaults.value("board.boundary_opacity"), 0.90, "boundary opacity default")
	_assert_equal(failures, defaults.value("active_cells.opacity"), 1.0, "active-cell opacity default")
	_assert_equal(failures, defaults.value("ghost.opacity"), 1.0, "Ghost opacity multiplier default")
	_assert_equal(failures, defaults.value("slice_set.spacing"), 1.0, "slice spacing default")
	_assert_equal(failures, defaults.value("environment.background_intensity"), 1.0, "background intensity default")
	_assert_equal(failures, defaults.semantic_owner("board.grid_opacity"), "BOARD_PRESENTATION", "grid semantic owner")
	_assert_equal(failures, defaults.semantic_owner("active_cells.opacity"), "PIECE_PRESENTATION", "active-cell semantic owner")
	_assert_equal(failures, defaults.semantic_owner("ghost.opacity"), "GHOST_PRESENTATION", "Ghost semantic owner")
	_assert_equal(failures, defaults.semantic_owner("slice_set.spacing"), "SLICE_SET_PRESENTATION", "slice semantic owner")
	if not defaults.applies_at_runtime("slice_set.spacing", "live_4d") or defaults.applies_at_runtime("slice_set.spacing", "live_3d"):
		failures.append("slice-set spacing should apply only to the declared 4D runtime among live 3D/4D contexts")

	var variant = defaults.with_overrides({
		"board.grid_opacity": 0.55,
		"active_cells.opacity": 0.65,
		"ghost.opacity": 1.25,
		"slice_set.spacing": 1.4,
	})
	if not variant.contract_conforms():
		failures.append("valid A/B presentation overrides should produce a valid detached profile")
	_assert_equal(failures, defaults.value("board.grid_opacity"), 0.31, "copy-on-override source isolation")
	_assert_equal(failures, variant.value("board.grid_opacity"), 0.55, "copy-on-override variant")
	var round_trip = PresentationProfileScript.from_snapshot(registry, variant.snapshot())
	if not round_trip.contract_conforms() or round_trip.values() != variant.values():
		failures.append("presentation profile snapshot should round-trip without a global mutable singleton")
	if defaults.with_overrides({"gameplay.board_state": []}).contract_conforms():
		failures.append("unknown gameplay fields should be rejected by the presentation profile")
	if defaults.with_overrides({"board.grid_opacity": 4.0}).contract_conforms():
		failures.append("out-of-range presentation values should be rejected")
	for forbidden_key in ["score", "lines", "board_state", "rng_state", "setup", "state_hash", "replay_hash", "native_trace_state"]:
		if defaults.values().has(forbidden_key):
			failures.append("presentation profile must exclude deterministic field %s" % forbidden_key)

	_test_visual_material_consumers(failures)
	_test_spacing_and_mode_coverage(failures)
	_test_renderer_profile_application(failures, variant)
	return failures


func _test_visual_material_consumers(failures: Array) -> void:
	var grid := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_PLAIN, false, 0.55)
	_assert_near(failures, grid.albedo_color.a, 0.55, "grid material opacity")
	var boundary := ReplayVisuals.board_outline_material(ReplayVisuals.DISPLAY_MODE_PLAIN, false, 0.63)
	_assert_near(failures, boundary.albedo_color.a, 0.63, "boundary material opacity")
	var active := ReplayVisuals.live_3d_active_face_materials(ReplayVisuals.DISPLAY_MODE_PLAIN, 2, 0.65)
	_assert_near(failures, active.get("top").albedo_color.a, 0.65, "active-face opacity")
	var ghost_default := ReplayVisuals.ghost_cell_material(ReplayVisuals.DISPLAY_MODE_PLAIN, 2, false, 1.0)
	var ghost_variant := ReplayVisuals.ghost_cell_material(ReplayVisuals.DISPLAY_MODE_PLAIN, 2, false, 1.25)
	_assert_near(failures, ghost_variant.albedo_color.a, ghost_default.albedo_color.a * 1.25, "Ghost opacity multiplier")
	var contrast_ghost_default := ReplayVisuals.ghost_cell_material(ReplayVisuals.DISPLAY_MODE_PLAIN, 2, true, 1.0)
	var contrast_ghost_low := ReplayVisuals.ghost_cell_material(ReplayVisuals.DISPLAY_MODE_PLAIN, 2, true, 0.25)
	_assert_near(failures, contrast_ghost_low.albedo_color.a, contrast_ghost_default.albedo_color.a, "High Contrast Ghost minimum")
	var contrast_grid := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_PLAIN, true, 0.10)
	if contrast_grid.albedo_color.a < ReplayVisuals.GRID_HIGH_CONTRAST_ALPHA:
		failures.append("high contrast should compose with, and strengthen, low grid opacity")


func _test_spacing_and_mode_coverage(failures: Array) -> void:
	var standard_layout = AdaptiveLayerLayoutScript.new()
	standard_layout.configure(4, 5.0, 10.0, 1.7777778, 1.0)
	var expanded_layout = AdaptiveLayerLayoutScript.new()
	expanded_layout.configure(4, 5.0, 10.0, 1.7777778, 1.4)
	if expanded_layout.horizontal_gap <= standard_layout.horizontal_gap or expanded_layout.vertical_gap <= standard_layout.vertical_gap:
		failures.append("slice spacing profile should scale both adaptive 4D gutters")
	for fixture in [
		{"trace_type": "live_2d", "dimension": 2, "board_shape": [10, 20]},
		{"trace_type": "live_3d", "dimension": 3, "board_shape": [6, 10, 6]},
		{"trace_type": "live_4d", "dimension": 4, "board_shape": [5, 10, 4, 4]},
		{"trace_type": "live_4d", "dimension": 4, "board_shape": [7, 8, 3, 1]},
	]:
		var model = BoardPresentationModelScript.new()
		model.configure(fixture, null, null, 1.4)
		if not model.current_bounds().get("ok", false):
			failures.append("presentation profile layout should support %s custom shape %s" % [fixture.get("trace_type"), fixture.get("board_shape")])
		if int(fixture.get("dimension")) == 4 and model.projection.mapper.current_layer_count() != int(fixture.get("board_shape")[3]):
			failures.append("4D profile layout should preserve W=1 and multi-slice layer counts")


func _test_renderer_profile_application(failures: Array, profile) -> void:
	var renderer = TraceSceneRendererScript.new()
	if not renderer.apply_presentation_profile(profile):
		failures.append("renderer should accept a valid detached presentation profile")
	var snapshot: Dictionary = renderer.presentation_preferences_snapshot().get("profile", {})
	if snapshot.get("values", {}).get("slice_set.spacing") != 1.4:
		failures.append("renderer should expose the complete applied profile for structural verification")
	if renderer.apply_presentation_profile(profile.with_overrides({"ghost.opacity": 9.0})):
		failures.append("renderer should retain its active profile when a candidate profile is invalid")
	if renderer.presentation_preferences_snapshot().get("profile") != snapshot:
		failures.append("invalid renderer profile application should not mutate active presentation state")


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_near(failures: Array, actual: float, expected: float, label: String) -> void:
	if absf(actual - expected) > 0.001:
		failures.append("%s: expected %.3f, got %.3f" % [label, expected, actual])
