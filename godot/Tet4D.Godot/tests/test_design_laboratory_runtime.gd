extends RefCounted

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const CatalogScript = preload("res://scripts/presentation/built_in_style_catalog.gd")
const ScenarioCatalogScript = preload("res://scripts/design_lab/design_scenario_catalog.gd")
const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Design Laboratory runtime test requires the canonical Godot scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	for _index in range(4):
		await tree.process_frame
	var app = root.get_node_or_null("App")
	var hud = root.get_node_or_null("ReplayHud")
	if app == null or hud == null:
		root.queue_free()
		return ["Design Laboratory runtime test requires TraceReplayApp and ReplayHud"]

	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var scenarios = ScenarioCatalogScript.new(registry)
	var catalog = CatalogScript.new(registry)
	failures.append_array(await _test_menu_entry(tree, app, hud))
	failures.append_array(await _test_runtime_matrix(tree, app, scenarios, catalog))
	failures.append_array(await _test_capture_readiness(tree, app, hud, scenarios, catalog))

	root.queue_free()
	await tree.process_frame
	return failures


func _test_menu_entry(tree: SceneTree, app, hud) -> Array:
	var failures: Array = []
	app._return_to_main_menu()
	await tree.process_frame
	var buttons: Array[Node] = hud.find_children("CommandCard__Design_Laboratory", "Button", true, false)
	if buttons.size() != 1 or not buttons[0].is_visible_in_tree():
		return ["main menu must expose one visible Design Laboratory command card"]
	buttons[0].pressed.emit()
	await tree.process_frame
	var snapshot: Dictionary = hud.design_laboratory_snapshot()
	if hud.current_screen() != hud.SCREEN_VIEWER or not bool(snapshot.get("visible", false)):
		failures.append("Design Laboratory command card must enter the isolated viewer overlay")
	if int(snapshot.get("scenario_count", 0)) < 7 or int(snapshot.get("preset_count", 0)) < 2:
		failures.append("Design Laboratory overlay must expose shipped scenarios and coherent presets")
	if not hud.live_interaction_owns_input():
		failures.append("visible Design Laboratory overlay must own gameplay/camera input")
	var panel = hud._design_laboratory
	var required_controls := {
		"PresetCatalogSelect": "catalogue preset selector",
		"ApplyLiveButton": "Apply Live",
		"SetArmAButton": "Set as A",
		"SetArmBButton": "Set as B",
		"ArmAAssignmentLabel": "visible A assignment",
		"ArmBAssignmentLabel": "visible B assignment",
		"ShowArmAButton": "Show A",
		"ShowArmBButton": "Show B",
		"ToggleArmButton": "Toggle",
	}
	for control_name in required_controls:
		if panel.find_child(control_name, true, false) == null:
			failures.append("Design Laboratory must expose %s" % required_controls.get(control_name))
	var start_button := panel.find_child("StartComparisonButton", true, false) as Button
	var show_b_button := panel.find_child("ShowArmBButton", true, false) as Button
	var set_a_button := panel.find_child("SetArmAButton", true, false) as Button
	var catalog_select := panel.find_child("PresetCatalogSelect", true, false) as OptionButton
	if start_button != null and show_b_button != null and set_a_button != null and catalog_select != null and catalog_select.item_count >= 3:
		start_button.pressed.emit()
		await tree.process_frame
		var started_comparison: Dictionary = panel.deterministic_snapshot().get("comparison", {})
		if started_comparison.is_empty():
			failures.append("runtime Start comparison must activate the prepared A/B slots: %s" % str(panel.deterministic_snapshot().get("status", "")))
		else:
			show_b_button.pressed.emit()
			await tree.process_frame
			var before_assignment: Dictionary = panel.deterministic_snapshot().get("comparison", {})
			catalog_select.select(2)
			set_a_button.pressed.emit()
			await tree.process_frame
			var after_assignment: Dictionary = panel.deterministic_snapshot().get("comparison", {})
			if (
				str(after_assignment.get("shown_arm", "")) != "B"
				or after_assignment.get("arms", {}).get("B", {}) != before_assignment.get("arms", {}).get("B", {})
				or after_assignment.get("arms", {}).get("A", {}) == before_assignment.get("arms", {}).get("A", {})
			):
				failures.append("Set as A while B is shown must replace only A and preserve shown_arm B: shown=%s b_same=%s a_changed=%s status=%s" % [
					str(after_assignment.get("shown_arm", "")),
					str(after_assignment.get("arms", {}).get("B", {}) == before_assignment.get("arms", {}).get("B", {})),
					str(after_assignment.get("arms", {}).get("A", {}) != before_assignment.get("arms", {}).get("A", {})),
					str(panel.deterministic_snapshot().get("status", "")),
				])
	hud._design_laboratory.close()
	return failures


func _test_runtime_matrix(tree: SceneTree, app, scenarios, catalog) -> Array:
	var failures: Array = []
	var records: Array = scenarios.list_scenarios()
	var styles: Array = catalog.list_styles()
	for scenario in records:
		var scenario_id := str(scenario.get("scenario_id", ""))
		var first: Dictionary = app._load_design_laboratory_scenario(scenario)
		if not bool(first.get("ok", false)):
			failures.append("runtime could not load design scenario %s: %s" % [scenario_id, first.get("error", "")])
			continue
		await tree.process_frame
		# Disturb view-only presentation state before exercising the canonical reset.
		app._camera_rig.nudge_yaw(0.27)
		app._camera_rig.zoom(-1.0)
		if str(scenario.get("scenario_kind", "replay_fixture")) == "live_session" and int(scenario.get("dimension", 0)) == 4:
			app._apply_live_4d_basis_turn("xw", 1)
		var second: Dictionary = app._load_design_laboratory_scenario(scenario)
		await tree.process_frame
		var settled_hash := DesignValueScript.canonical_hash(app._design_laboratory_fingerprint())
		if (
			not bool(second.get("ok", false))
			or str(first.get("fingerprint_hash", "")) != str(second.get("fingerprint_hash", ""))
			or str(second.get("fingerprint_hash", "")) != settled_hash
		):
			failures.append("scenario %s must reload to one canonical gameplay and presentation fingerprint" % scenario_id)
			continue

		for style in styles:
			var style_id := str(style.get("style_id", ""))
			var loaded: Dictionary = catalog.style_profile(style_id)
			var reset: Dictionary = app._load_design_laboratory_scenario(scenario)
			if not bool(loaded.get("ok", false)) or not bool(reset.get("ok", false)):
				failures.append("scenario/preset matrix could not resolve %s with %s" % [scenario_id, style_id])
				continue
			var before_hash := DesignValueScript.canonical_hash(app._design_laboratory_fingerprint())
			if not app.apply_presentation_profile(loaded.get("profile")):
				failures.append("scenario/preset matrix could not apply %s" % style_id)
				continue
			if DesignValueScript.canonical_hash(app._design_laboratory_fingerprint()) != before_hash:
				failures.append("applying %s changed non-style state in %s" % [style_id, scenario_id])
			await tree.process_frame
			if DesignValueScript.canonical_hash(app._design_laboratory_fingerprint()) != before_hash:
				failures.append("rendering %s accumulated hidden non-style state in %s" % [style_id, scenario_id])
	return failures


func _test_capture_readiness(tree: SceneTree, app, hud, scenarios, catalog) -> Array:
	var failures: Array = []
	var records: Array = scenarios.list_scenarios()
	var scenario: Dictionary = {}
	for record in records:
		if str(record.get("scenario_id", "")) == "live_4d_next_hold_ghost_v1":
			scenario = record
	var loaded: Dictionary = app._load_design_laboratory_scenario(scenario)
	var styles: Array = catalog.list_styles()
	var profile = catalog.style_profile(str(styles.back().get("style_id"))).get("profile")
	if not bool(loaded.get("ok", false)) or profile == null:
		return ["capture readiness requires an actual deterministic scenario and profile"]
	profile = profile.with_overrides({"display.ui_scale": "large"})
	if not app.restore_presentation_design(profile):
		return ["capture readiness must apply the complete production profile"]
	if bool(app._design_capture_readiness().get("ready", true)):
		failures.append("capture readiness must include the application's pending profile guard")
	var previous := ""
	var stable := false
	for _frame in range(int(ProjectSettings.get_setting("design_lab/capture/max_settle_frames", 0))):
		await tree.process_frame
		var observation: Dictionary = app._design_capture_readiness()
		var token := str(observation.get("token", ""))
		if bool(observation.get("ready", false)) and token == previous:
			stable = true
			break
		previous = token if bool(observation.get("ready", false)) else ""
	if not stable:
		failures.append("production layout and camera must reach a stable ready observation within the configured budget")
	hud.apply_shell_settings()
	await tree.process_frame
	# State is observational: reading it cannot mutate native scenario identity.
	if DesignValueScript.canonical_hash(app._design_laboratory_fingerprint()) != str(loaded.get("fingerprint_hash", "")):
		failures.append("capture readiness must preserve the native/non-style scenario fingerprint")
	# Replay owns no live helper fit. A hidden cockpit cannot keep capture busy.
	for record in records:
		if str(record.get("scenario_id", "")) == "plain_2d_sparse_v1":
			app._load_design_laboratory_scenario(record)
	app.restore_presentation_design(profile)
	stable = false
	previous = ""
	for _frame in range(int(ProjectSettings.get_setting("design_lab/capture/max_settle_frames", 0))):
		await tree.process_frame
		var replay_ready: Dictionary = app._design_capture_readiness()
		var replay_token := str(replay_ready.get("token", ""))
		if bool(replay_ready.get("ready", false)) and replay_token == previous:
			stable = true
			break
		previous = replay_token if bool(replay_ready.get("ready", false)) else ""
	if not stable:
		failures.append("replay capture must become ready without inactive live-helper probes")
	# A complete-profile round trip in 3D must invalidate the capture token too,
	# even though that mode does not use the 4D framing guard.
	for record in records:
		if str(record.get("scenario_id", "")) == "live_3d_next_hold_ghost_v1":
			app._load_design_laboratory_scenario(record)
	var token_before: String = str(app._design_capture_readiness().get("token", ""))
	app.restore_presentation_design(profile)
	var token_after: String = str(app._design_capture_readiness().get("token", ""))
	app.restore_presentation_design(profile)
	if token_after == token_before or str(app._design_capture_readiness().get("token", "")) == token_after:
		failures.append("every 3D profile application must invalidate capture readiness, including equal-snapshot round trips")
	return failures
