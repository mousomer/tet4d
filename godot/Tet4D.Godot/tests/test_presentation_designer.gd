extends RefCounted

const DesignerScript = preload("res://scripts/ui/presentation_designer.gd")
const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")


func run() -> Array:
	var failures: Array = []
	failures.append_array(await _test_registry_driven_component())
	failures.append_array(await _test_live_app_integration())
	return failures


func _test_registry_driven_component() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var registry = SettingsRegistryScript.new()
	registry.load_from_path(SettingsRegistryScript.REGISTRY_PATH)
	var opening = PresentationProfileScript.from_snapshot(registry, {
		"schema_version": PresentationProfileScript.SCHEMA_VERSION,
		"values": registry.default_values(),
	}).with_overrides({
		"ghost.opacity": 0.75,
		"theme.name": "tron",
	})
	var designer = DesignerScript.new()
	designer.size = Vector2(400, 650)
	tree.root.add_child(designer)
	await tree.process_frame
	if not designer.configure(registry) or not designer.open_with_profile(opening, "live_2d"):
		failures.append("Presentation Designer should configure from the canonical registry and open a detached live session")
		designer.queue_free()
		return failures
	var snapshot: Dictionary = designer.deterministic_snapshot()
	failures.append_array(_check_generated_controls(designer, registry, "live_2d"))
	if snapshot.get("applicable_ids", []).size() != 19:
		failures.append("live 2D Designer should generate exactly the registry's 19 applicable parameters")
	for hidden_id in [
		"display.window_mode",
		"display.windowed_size",
		"replay.playback_speed",
		"replay.loop_enabled",
		"display.projection_strength",
		"diagnostics.show_layout_bounds",
		"camera.sensitivity",
		"camera.invert_y",
		"slice_set.spacing",
		"display.show_w_labels",
	]:
		if snapshot.get("applicable_ids", []).has(hidden_id):
			failures.append("live 2D Designer must hide non-applicable parameter %s" % hidden_id)
	if not (designer.control_for_setting("ghost.enabled") is CheckBox):
		failures.append("boolean registry parameters should generate checkbox controls")
	if not (designer.control_for_setting("ghost.opacity") is HSlider):
		failures.append("numeric registry parameters should generate slider controls")
	var numeric_entry: Dictionary = designer._controls_by_id.get("ghost.opacity", {})
	if not (numeric_entry.get("exact") is SpinBox):
		failures.append("numeric registry parameters should pair sliders with exact SpinBox entry")
	if not (designer.control_for_setting("theme.name") is OptionButton):
		failures.append("enum registry parameters should generate option controls")
	var expected_owner_order: Array = []
	for spec in registry.settings:
		if spec.applies_at_runtime("live_2d") and not expected_owner_order.has(spec.semantic_owner()):
			expected_owner_order.append(spec.semantic_owner())
	if snapshot.get("owner_order", []) != expected_owner_order:
		failures.append("Designer groups should follow registry order and semantic_owner metadata")

	var previews: Array = []
	designer.profile_preview_requested.connect(func(profile) -> void: previews.append(profile.snapshot()))
	if not designer.capture_reference():
		failures.append("Designer should capture working B as immutable reference A")
	var reference_before: Dictionary = designer.reference_profile().snapshot()
	if not designer.set_parameter_value("ghost.opacity", 1.25):
		failures.append("Designer should accept in-range live numeric edits")
	if designer.reference_profile().snapshot() != reference_before:
		failures.append("editing B must never mutate captured reference A")
	if designer.working_profile().value("ghost.opacity") != 1.25:
		failures.append("numeric edits should update detached working B exactly")
	if not designer.show_slot(DesignerScript.SLOT_REFERENCE) or previews[-1].get("values", {}).get("ghost.opacity") != 0.75:
		failures.append("Show A should preview the exact captured reference profile")
	if not designer.show_slot(DesignerScript.SLOT_WORKING) or previews[-1].get("values", {}).get("ghost.opacity") != 1.25:
		failures.append("Show B should preview the exact detached working profile")
	if not designer.reset_parameter("ghost.opacity") or designer.working_profile().value("ghost.opacity") != 0.75:
		failures.append("parameter reset should restore the opening baseline, not factory defaults")
	designer.set_parameter_value("ghost.opacity", 1.1)
	designer.set_parameter_value("ghost.enabled", false)
	if not designer.reset_owner("GHOST_PRESENTATION"):
		failures.append("semantic-owner reset should be available for generated groups")
	if designer.working_profile().values_for_owner("GHOST_PRESENTATION") != opening.values_for_owner("GHOST_PRESENTATION"):
		failures.append("group reset should restore all applicable owner values to the opening baseline")
	if not designer.reset_working_to_factory_defaults() or designer.working_profile().value("theme.name") != registry.get_spec("theme.name").default_value():
		failures.append("Factory Defaults should be distinct from the non-default opening baseline")
	if not designer.reset_working_to_opening() or designer.working_profile().snapshot() != opening.snapshot():
		failures.append("Reset B should restore the complete opening profile")

	designer.set_runtime_context("live_3d")
	failures.append_array(_check_generated_controls(designer, registry, "live_3d"))
	if designer.deterministic_snapshot().get("applicable_ids", []).size() != 21:
		failures.append("live 3D Designer should generate exactly 21 registry-applicable controls")
	designer.set_runtime_context("live_4d")
	failures.append_array(_check_generated_controls(designer, registry, "live_4d"))
	var four_d_ids: Array = designer.deterministic_snapshot().get("applicable_ids", [])
	if four_d_ids.size() != 23 or not four_d_ids.has("slice_set.spacing") or not four_d_ids.has("display.show_w_labels"):
		failures.append("live 4D Designer should generate all 23 applicable controls including slice settings")

	var registry_data := {"schema_version": registry.schema_version, "categories": registry.categories.duplicate(true), "settings": []}
	for spec in registry.settings:
		var spec_data: Dictionary = spec.data.duplicate(true)
		if spec.id() == "interface.show_onboarding":
			spec_data["runtime_applicability"].erase("live_2d")
		registry_data["settings"].append(spec_data)
	var mutated_registry = SettingsRegistryScript.new()
	mutated_registry.load_from_data(registry_data)
	var mutation_designer = DesignerScript.new()
	mutation_designer.size = Vector2(400, 650)
	tree.root.add_child(mutation_designer)
	await tree.process_frame
	var mutation_profile = PresentationProfileScript.from_snapshot(mutated_registry, {
		"schema_version": PresentationProfileScript.SCHEMA_VERSION,
		"values": mutated_registry.default_values(),
	})
	if not mutation_designer.configure(mutated_registry) or not mutation_designer.open_with_profile(mutation_profile, "live_2d"):
		failures.append("Designer should accept a valid test registry mutation")
	elif mutation_designer.deterministic_snapshot().get("applicable_ids", []).has("interface.show_onboarding"):
		failures.append("Designer exposure must track registry applicability mutations without a hard-coded parameter list")
	designer.queue_free()
	mutation_designer.queue_free()
	await tree.process_frame
	return failures


func _test_live_app_integration() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Presentation Designer integration requires the trace replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1280, 800)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	var app = root.get_node_or_null("App")
	if hud == null or app == null:
		root.queue_free()
		tree.root.size = original_size
		return ["Presentation Designer integration requires ReplayHud and TraceReplayApp"]
	app._enter_live_2d_mode()
	await tree.process_frame
	var designer = hud._presentation_designer
	var store_before: Dictionary = hud._settings_store.deterministic_snapshot()
	var game_before: Dictionary = app._current_snapshot.duplicate(true)
	var setup_before: Dictionary = app._active_live_setup.duplicate(true)
	var basis_before: Array = app._live_4d_basis.slots()
	var orientation_before: Dictionary = app._live_4d_local_orientation.snapshot()
	var camera_before: Dictionary = app._camera_rig.presentation_snapshot()
	var bounds_before: Dictionary = app._renderer.current_bounds().duplicate(true)
	var background_before: Color = app._world_environment.environment.background_color
	var next_before: Dictionary = _piece_semantic_snapshot(hud._next_piece_panel.deterministic_snapshot())
	var hold_before: Dictionary = _piece_semantic_snapshot(hud._hold_piece_panel.deterministic_snapshot())
	hud._open_presentation_designer()
	await tree.process_frame
	if designer == null or designer.state() != DesignerScript.STATE_FULL or not hud.live_interaction_owns_input():
		failures.append("opening the live Designer should show the full editor and transfer gameplay input ownership")
	var layout: Dictionary = hud.layout_contract_snapshot()
	var game_rect: Rect2 = layout.get("game_area", Rect2())
	var designer_rect: Rect2 = designer.get_global_rect()
	if not _rect_contains_rect(game_rect, designer_rect) or designer_rect.size.x >= game_rect.size.x * 0.65:
		failures.append("full Designer should remain bounded inside the board area without obscuring the whole board")
	var inspector_rect: Rect2 = hud._right_scroll.get_global_rect()
	if (
		not hud._next_piece_panel.is_visible_in_tree()
		or not hud._hold_piece_panel.is_visible_in_tree()
		or not hud._piece_control_strip.is_visible_in_tree()
		or not _rect_contains_rect(inspector_rect, hud._next_piece_panel.get_global_rect())
		or not _rect_contains_rect(inspector_rect, hud._hold_piece_panel.get_global_rect())
		or not _rect_contains_rect(inspector_rect, hud._piece_control_strip.get_global_rect())
	):
		failures.append("NEXT, HOLD, and primary piece controls must remain simultaneously present while the full Designer is open")
	if not hud._right_scroll.is_visible_in_tree() or hud._right_scroll.vertical_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED:
		failures.append("helper/status content should remain immediately reachable through the existing inspector scroll surface")

	var full_owned_hash := str(app._live_bridge.live_2d_state_hash())
	var blocked_drop := InputEventAction.new()
	blocked_drop.action = "live_2d_hard_drop"
	blocked_drop.pressed = true
	app._unhandled_input(blocked_drop)
	if str(app._live_bridge.live_2d_state_hash()) != full_owned_hash:
		failures.append("full Designer keyboard focus must suppress gameplay commands")

	if not designer.capture_reference():
		failures.append("integrated Designer should capture reference A")
	var original_opacity := float(designer.working_profile().value("ghost.opacity"))
	var edited_opacity := 1.25 if absf(original_opacity - 1.25) > 0.001 else 0.75
	var original_grid_opacity := float(designer.working_profile().value("board.grid_opacity"))
	var edited_grid_opacity := 0.55 if absf(original_grid_opacity - 0.55) > 0.001 else 0.31
	var original_piece_opacity := float(designer.working_profile().value("active_cells.opacity"))
	var edited_piece_opacity := 0.65 if absf(original_piece_opacity - 0.65) > 0.001 else 0.85
	var original_background := float(designer.working_profile().value("environment.background_intensity"))
	var edited_background := 1.3 if absf(original_background - 1.3) > 0.001 else 0.7
	var original_density := str(designer.working_profile().value("display.hud_density"))
	var edited_density := "detailed" if original_density != "detailed" else "compact"
	if not designer.set_parameter_value("ghost.opacity", edited_opacity):
		failures.append("integrated Designer should route live edits through its detached B profile")
	designer.set_parameter_value("board.grid_opacity", edited_grid_opacity)
	designer.set_parameter_value("active_cells.opacity", edited_piece_opacity)
	designer.set_parameter_value("environment.background_intensity", edited_background)
	designer.set_parameter_value("display.hud_density", edited_density)
	await tree.process_frame
	if absf(float(app._presentation_profile.value("ghost.opacity")) - edited_opacity) > 0.001:
		failures.append("Designer edits should reach TraceReplayApp.apply_presentation_profile")
	var renderer_values: Dictionary = app._renderer.presentation_preferences_snapshot().get("profile", {}).get("values", {})
	var renderer_expectations := {
		"board.grid_opacity": edited_grid_opacity,
		"active_cells.opacity": edited_piece_opacity,
		"ghost.opacity": edited_opacity,
	}
	for setting_id in renderer_expectations:
		if absf(float(renderer_values.get(setting_id, -99.0)) - float(renderer_expectations.get(setting_id))) > 0.001:
			failures.append("Designer live apply should reach representative renderer owner %s" % setting_id)
	if hud.presentation_preferences_snapshot().get("hud_density") != edited_density:
		failures.append("Designer live apply should reach the HUD presentation owner")
	if app._world_environment.environment.background_color == background_before:
		failures.append("Designer live apply should reach the environment presentation owner")
	if not designer.show_slot(DesignerScript.SLOT_REFERENCE):
		failures.append("integrated A/B selection should expose the reference slot")
	await tree.process_frame
	if absf(float(app._presentation_profile.value("ghost.opacity")) - original_opacity) > 0.001:
		failures.append("integrated Show A should apply the exact captured profile")
	designer.show_slot(DesignerScript.SLOT_WORKING)
	await tree.process_frame
	if absf(float(app._presentation_profile.value("ghost.opacity")) - edited_opacity) > 0.001:
		failures.append("integrated Show B should restore the exact working profile")
	if hud._settings_store.deterministic_snapshot() != store_before:
		failures.append("Designer preview/edit/A-B operations must not mutate or save SettingsStore")
	if app._current_snapshot != game_before or app._active_live_setup != setup_before:
		failures.append("Designer presentation changes must preserve deterministic gameplay/session state")
	if app._live_4d_basis.slots() != basis_before or app._live_4d_local_orientation.snapshot() != orientation_before:
		failures.append("Designer presentation changes must preserve exact basis and slice-local orientation")
	if app._renderer.current_bounds() != bounds_before:
		failures.append("Designer presentation changes must preserve canonical board/fit geometry")
	if _piece_semantic_snapshot(hud._next_piece_panel.deterministic_snapshot()) != next_before or _piece_semantic_snapshot(hud._hold_piece_panel.deterministic_snapshot()) != hold_before:
		failures.append("Designer presentation changes must preserve NEXT and HOLD state")
	var camera_after: Dictionary = app._camera_rig.presentation_snapshot()
	for pose_key in ["target_yaw", "target_pitch", "target_roll", "current_yaw", "current_pitch", "current_roll", "target_focus", "current_focus", "zoom_multiplier"]:
		if camera_after.get(pose_key) != camera_before.get(pose_key):
			failures.append("Designer profile switching must preserve camera pose field %s" % pose_key)

	designer.collapse_to_compact()
	await tree.process_frame
	if designer.state() != DesignerScript.STATE_COMPACT or hud.live_interaction_owns_input():
		failures.append("compact Designer should preserve A/B while releasing ordinary gameplay keys")
	var compact_rect: Rect2 = designer.get_global_rect()
	var camera_compact_before: Dictionary = app._camera_rig.presentation_snapshot()
	var compact_wheel := InputEventMouseButton.new()
	compact_wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	compact_wheel.pressed = true
	compact_wheel.position = compact_rect.get_center()
	app._input(compact_wheel)
	if app._camera_rig.presentation_snapshot() != camera_compact_before:
		failures.append("pointer input over the compact Designer must not leak into camera controls")
	var compact_game_hash := str(app._live_bridge.live_2d_state_hash())
	var resumed_drop := InputEventAction.new()
	resumed_drop.action = "live_2d_hard_drop"
	resumed_drop.pressed = true
	app._unhandled_input(resumed_drop)
	if str(app._live_bridge.live_2d_state_hash()) == compact_game_hash:
		failures.append("ordinary gameplay commands should resume when the Designer is compact")
	designer.hide_preserving_preview()
	if designer.state() != DesignerScript.STATE_HIDDEN or hud.live_interaction_owns_input():
		failures.append("hidden Designer should release input while preserving the detached session")
	hud._open_presentation_designer()
	await tree.process_frame
	if designer.working_profile().value("ghost.opacity") != edited_opacity or not designer.deterministic_snapshot().get("has_reference", false):
		failures.append("hide/reopen should preserve working B and immutable A")

	for viewport_size in [Vector2i(960, 720), Vector2i(1440, 900)]:
		tree.root.size = viewport_size
		await tree.process_frame
		await tree.process_frame
		var responsive_game: Rect2 = hud.layout_contract_snapshot().get("game_area", Rect2())
		if not _rect_contains_rect(responsive_game, designer.get_global_rect()):
			failures.append("full Designer should remain inside the game area after resize to %s" % str(viewport_size))
		designer.collapse_to_compact()
		await tree.process_frame
		if not _rect_contains_rect(responsive_game, designer.get_global_rect()):
			failures.append("compact Designer should remain inside the game area after resize to %s" % str(viewport_size))
		designer.expand_to_full()
		await tree.process_frame

	app._enter_live_4d_mode()
	await tree.process_frame
	hud._open_presentation_designer()
	await tree.process_frame
	var four_d_designer: Dictionary = designer.deterministic_snapshot()
	if not four_d_designer.get("applicable_ids", []).has("slice_set.spacing") or not four_d_designer.get("applicable_ids", []).has("display.show_w_labels"):
		failures.append("integrated live 4D Designer should expose registry-authorized slice controls")
	var four_d_state_before: Dictionary = app._current_snapshot.duplicate(true)
	var four_d_basis_before: Array = app._live_4d_basis.slots()
	var four_d_orientation_before: Dictionary = app._live_4d_local_orientation.snapshot()
	var four_d_camera_before: Dictionary = app._camera_rig.presentation_snapshot()
	var original_spacing := float(designer.working_profile().value("slice_set.spacing"))
	var edited_spacing := 1.4 if absf(original_spacing - 1.4) > 0.001 else 0.8
	if not designer.set_parameter_value("slice_set.spacing", edited_spacing):
		failures.append("integrated 4D Designer should apply slice-set presentation values")
	await tree.process_frame
	var four_d_renderer_values: Dictionary = app._renderer.presentation_preferences_snapshot().get("profile", {}).get("values", {})
	if absf(float(four_d_renderer_values.get("slice_set.spacing", -99.0)) - edited_spacing) > 0.001:
		failures.append("Designer live apply should reach the slice-set presentation owner")
	if app._current_snapshot != four_d_state_before or app._live_4d_basis.slots() != four_d_basis_before or app._live_4d_local_orientation.snapshot() != four_d_orientation_before:
		failures.append("4D slice presentation editing must preserve game state, active slice, basis, and local orientation")
	var four_d_camera_after: Dictionary = app._camera_rig.presentation_snapshot()
	for pose_key in ["target_yaw", "target_pitch", "target_roll", "current_yaw", "current_pitch", "current_roll", "target_focus", "current_focus", "zoom_multiplier"]:
		if four_d_camera_after.get(pose_key) != four_d_camera_before.get(pose_key):
			failures.append("4D slice presentation editing must preserve camera pose field %s" % pose_key)
	if not hud._basis_panel.is_visible_in_tree() or str(hud.layout_contract_snapshot().get("basis_indicator_text", "")).find("Slice:") == -1:
		failures.append("4D basis/slice information should remain readable while tuning presentation")
	if not _rect_contains_rect(hud._right_scroll.get_global_rect(), hud._piece_control_strip.get_global_rect()):
		failures.append("4D primary piece controls should remain visible without scrolling while tuning presentation")
	if str(hud.layout_contract_snapshot().get("inspector_hint_text", "")).find("Slice") == -1:
		failures.append("4D helper guidance should remain present and scroll-reachable while tuning presentation")

	designer.revert_and_hide()
	await tree.process_frame
	if designer.state() != DesignerScript.STATE_HIDDEN or designer.working_profile().snapshot() != designer.opening_profile().snapshot():
		failures.append("Revert & Hide should restore the opening baseline and close the surface")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _rect_contains_rect(outer: Rect2, inner: Rect2) -> bool:
	return (
		outer.size.x > 0.0
		and outer.size.y > 0.0
		and outer.has_point(inner.position + Vector2(0.5, 0.5))
		and outer.has_point(inner.end - Vector2(0.5, 0.5))
	)


func _check_generated_controls(designer, registry, runtime_context: String) -> Array:
	var failures: Array = []
	var expected_specs: Array = []
	for spec in registry.settings:
		if spec.applies_at_runtime(runtime_context):
			expected_specs.append(spec)
	if designer._controls_by_id.size() != expected_specs.size():
		failures.append("%s Designer should generate exactly one control entry for every applicable registry spec" % runtime_context)
	for spec in expected_specs:
		var entry: Dictionary = designer._controls_by_id.get(spec.id(), {})
		if entry.is_empty() or entry.get("spec") != spec:
			failures.append("%s Designer control %s should retain its exact registry spec and semantic owner" % [runtime_context, spec.id()])
			continue
		match spec.value_type():
			"bool":
				if not (entry.get("primary") is CheckBox):
					failures.append("%s bool %s should have exactly one CheckBox editor" % [runtime_context, spec.id()])
			"int", "float":
				var slider := entry.get("primary") as HSlider
				var exact := entry.get("exact") as SpinBox
				if slider == null or exact == null:
					failures.append("%s numeric %s should pair HSlider and exact SpinBox editors" % [runtime_context, spec.id()])
				else:
					for range_control in [slider, exact]:
						if (
							absf(range_control.min_value - float(spec.data.get("min"))) > 0.0001
							or absf(range_control.max_value - float(spec.data.get("max"))) > 0.0001
							or absf(range_control.step - float(spec.data.get("step"))) > 0.0001
						):
							failures.append("%s numeric %s bounds/step must match its registry spec exactly" % [runtime_context, spec.id()])
			"enum":
				var options := entry.get("primary") as OptionButton
				var spec_options: Array = spec.data.get("options", [])
				if options == null or options.item_count != spec_options.size():
					failures.append("%s enum %s should generate exactly the registered options" % [runtime_context, spec.id()])
				elif options != null:
					for index in range(spec_options.size()):
						if str(options.get_item_metadata(index)) != str(spec_options[index].get("value", "")):
							failures.append("%s enum %s option order/value must match registry metadata" % [runtime_context, spec.id()])
			_:
				failures.append("%s exposes unsupported current live type %s for %s" % [runtime_context, spec.value_type(), spec.id()])
	return failures


func _piece_semantic_snapshot(snapshot: Dictionary) -> Dictionary:
	var result := snapshot.duplicate(true)
	var thumbnail: Dictionary = result.get("thumbnail", {})
	thumbnail.erase("style_revision")
	result["thumbnail"] = thumbnail
	return result
