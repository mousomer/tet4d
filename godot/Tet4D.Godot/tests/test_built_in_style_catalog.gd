extends RefCounted

const CatalogScript = preload("res://scripts/presentation/built_in_style_catalog.gd")
const DesignerScript = preload("res://scripts/ui/presentation_designer.gd")
const LibraryScript = preload("res://scripts/presentation/presentation_profile_library.gd")
const ProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const AnimatedBackgroundScript = preload("res://scripts/rendering/animated_background.gd")

const DESIGNER_DIRECTORY := "user://stage54f4_designer_profiles"
const INTEGRATION_DIRECTORY := "user://stage54f4_integration_profiles"
const MALFORMED_CATALOG_PATH := "user://stage54f4_malformed_catalog.json"
const UNSUPPORTED_CATALOG_PATH := "user://stage54f4_unsupported_catalog.json"
const REJECTED_CATALOG_PATH := "user://stage54f4_rejected_catalog.json"
const MINIMUM_SHIPPED_STYLES := 5
const ANIMATION_IDS := [
	"environment.background_animation_mode",
	"environment.background_animation_intensity",
	"environment.background_animation_speed",
]


func run() -> Array:
	var failures: Array = []
	_cleanup_all()
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	failures.append_array(_test_cache_independent_startup_contract())
	failures.append_array(_test_animation_parameters(registry))
	failures.append_array(_test_catalog_structure(registry))
	failures.append_array(_test_catalog_read_only(registry))
	failures.append_array(_test_catalog_rejection(registry))
	failures.append_array(_test_animated_background_component(registry))
	failures.append_array(await _test_designer_integration(registry))
	failures.append_array(await _test_live_integration(registry))
	_cleanup_all()
	return failures


func _test_cache_independent_startup_contract() -> Array:
	var failures: Array = []
	var app_source := FileAccess.get_file_as_string("res://scripts/app/trace_replay_app.gd")
	if app_source.is_empty():
		return ["cache-independent startup test must be able to read the application controller"]
	if app_source.find('const AnimatedBackgroundScript = preload("res://scripts/rendering/animated_background.gd")') == -1:
		failures.append("the application controller must explicitly preload AnimatedBackground")
	if app_source.find("AnimatedBackgroundScript.new()") == -1:
		failures.append("the application controller must construct the background through its explicit preload")
	if app_source.find(": AnimatedBackground") != -1 or app_source.find("as AnimatedBackground") != -1:
		failures.append("application startup must not depend on ignored global-script-class cache metadata for AnimatedBackground")
	return failures


func _test_animation_parameters(registry) -> Array:
	var failures: Array = []
	for setting_id in ANIMATION_IDS:
		var spec = registry.get_spec(setting_id)
		if spec == null:
			failures.append("background animation parameter %s must be declared in the one registry" % setting_id)
			continue
		if spec.semantic_owner() != "ENVIRONMENT_PRESENTATION":
			failures.append("%s must be owned by ENVIRONMENT_PRESENTATION" % setting_id)
		for context in ["live_2d", "live_3d", "live_4d"]:
			if not spec.applies_at_runtime(context):
				failures.append("%s must be applicable in %s" % [setting_id, context])
		if spec.persistence() != "local_shell" or not spec.is_persistent():
			failures.append("%s must follow the existing persistent presentation policy" % setting_id)

	var defaults = ProfileScript.canonical_defaults()
	if str(defaults.value("environment.background_animation_mode")) != AnimatedBackgroundScript.MODE_NONE:
		failures.append("background animation must default to the current static background")
	var mode_spec = registry.get_spec("environment.background_animation_mode")
	if mode_spec != null:
		var option_values: Array = []
		for option in mode_spec.data.get("options", []):
			option_values.append(str(option.get("value", "")))
		if option_values != AnimatedBackgroundScript.SUPPORTED_MODES:
			failures.append("registry animation modes must match the component's supported modes: %s" % [option_values])
		if bool(mode_spec.validated_value("unsupported_mode").get("ok", false)):
			failures.append("unsupported animation modes must be rejected by the registry")
	for bounded in [
		["environment.background_animation_intensity", 0.55, -0.1, 1.6],
		["environment.background_animation_speed", 1.0, -0.1, 2.6],
	]:
		var setting_id := str(bounded[0])
		if defaults.value(setting_id) != bounded[1]:
			failures.append("%s default should be %s" % [setting_id, bounded[1]])
		for out_of_range in [bounded[2], bounded[3]]:
			if defaults.with_overrides({setting_id: out_of_range}).contract_conforms():
				failures.append("%s must reject out-of-range value %s" % [setting_id, out_of_range])

	var animated_variant = defaults.with_overrides({
		"environment.background_animation_mode": AnimatedBackgroundScript.MODE_TRON_GRID_FLOW,
		"environment.background_animation_intensity": 0.6,
		"environment.background_animation_speed": 0.75,
	})
	if not animated_variant.contract_conforms():
		failures.append("animated background overrides should produce a conforming detached profile")
	var round_trip = ProfileScript.from_snapshot(registry, animated_variant.snapshot())
	if not round_trip.contract_conforms() or round_trip.values() != animated_variant.values():
		failures.append("animation parameters must survive profile snapshot round-trip")
	return failures


func _test_catalog_structure(registry) -> Array:
	var failures: Array = []
	var catalog = CatalogScript.new(registry)
	var records: Array = catalog.list_styles()
	if records.size() < MINIMUM_SHIPPED_STYLES:
		return ["built-in catalog must ship at least %d styles, got %d: %s" % [MINIMUM_SHIPPED_STYLES, records.size(), catalog.diagnostics()]]
	if not catalog.diagnostics().is_empty():
		failures.append("shipped catalog should load without diagnostics: %s" % [catalog.diagnostics()])
	if CatalogScript.CATALOG_PATH.begins_with("user://") or not CatalogScript.CATALOG_PATH.begins_with("res://"):
		failures.append("built-in catalog must be repository-shipped rather than user-data storage")

	var seen_ids: Array = []
	var values_by_id: Dictionary = {}
	var animated_ids: Array = []
	for record in records:
		var style_id := str(record.get("style_id", ""))
		if style_id.is_empty() or seen_ids.has(style_id):
			failures.append("built-in style identities must be present and unique: %s" % style_id)
		seen_ids.append(style_id)
		if not bool(record.get("read_only", false)):
			failures.append("built-in style %s must be marked read-only" % style_id)
		if str(record.get("display_name", "")).is_empty() or str(record.get("short_description", "")).is_empty():
			failures.append("built-in style %s must carry a display name and short description" % style_id)
		if int(record.get("presentation_profile_schema_version", 0)) != ProfileScript.SCHEMA_VERSION:
			failures.append("built-in style %s must reuse the authoritative profile schema" % style_id)
		var loaded: Dictionary = catalog.style_profile(style_id)
		if not bool(loaded.get("ok", false)):
			failures.append("built-in style %s must resolve: %s" % [style_id, loaded.get("error", "")])
			continue
		var profile = loaded.get("profile")
		if profile == null or not profile.contract_conforms():
			failures.append("built-in style %s must validate through the single PresentationProfile contract" % style_id)
			continue
		if profile.values().size() != registry.settings.size():
			failures.append("built-in style %s must resolve to a complete registry-covering value set" % style_id)
		values_by_id[style_id] = profile.values()
		if bool(record.get("animated", false)):
			animated_ids.append(style_id)
			if str(profile.value("environment.background_animation_mode")) == AnimatedBackgroundScript.MODE_NONE:
				failures.append("animated built-in style %s must select a real animation mode" % style_id)
			if float(profile.value("environment.background_animation_intensity")) <= 0.0:
				failures.append("animated built-in style %s must use a visible animation strength" % style_id)
			if float(profile.value("environment.background_animation_speed")) <= 0.0:
				failures.append("animated built-in style %s must actually move" % style_id)
		elif str(profile.value("environment.background_animation_mode")) != AnimatedBackgroundScript.MODE_NONE:
			failures.append("non-animated built-in style %s must set the static background mode" % style_id)

	if animated_ids != catalog.animated_style_ids():
		failures.append("catalog animated-style reporting must match its own records")
	if animated_ids.size() != 1 or not animated_ids.has("tron_grid_flow"):
		failures.append("exactly one shipped Tron-like animated style is expected, got %s" % [animated_ids])
	if not seen_ids.has("high_contrast_access"):
		failures.append("an accessibility-oriented built-in style is expected")
	else:
		var accessibility_values: Dictionary = values_by_id.get("high_contrast_access", {})
		if not bool(accessibility_values.get("accessibility.reduced_motion", false)):
			failures.append("the accessibility style must keep motion off")
		if str(accessibility_values.get("environment.background_animation_mode", "")) != AnimatedBackgroundScript.MODE_NONE:
			failures.append("the accessibility style must not animate its background")

	for left_id in values_by_id.keys():
		for right_id in values_by_id.keys():
			if str(left_id) >= str(right_id):
				continue
			if _difference_count(values_by_id.get(left_id), values_by_id.get(right_id)) < 3:
				failures.append("built-in styles %s and %s are not meaningfully distinct" % [left_id, right_id])

	if catalog.deterministic_snapshot() != catalog.deterministic_snapshot():
		failures.append("catalog snapshots must be deterministic across repeated reads")
	if not bool(catalog.deterministic_snapshot().get("read_only", false)):
		failures.append("catalog snapshot must report read-only ownership")
	return failures


func _test_catalog_read_only(registry) -> Array:
	var failures: Array = []
	var catalog = CatalogScript.new(registry)
	for forbidden_method in [
		"save_new",
		"save_existing",
		"rename_profile",
		"delete_profile",
		"duplicate_profile",
		"import_profile",
		"import_artifact",
		"export_profile",
	]:
		if catalog.has_method(forbidden_method):
			failures.append("read-only catalog must not expose mutation method %s" % forbidden_method)

	var first: Dictionary = catalog.style_profile("tron_grid_flow")
	if not bool(first.get("ok", false)):
		return failures + ["the shipped Tron style must resolve"]
	var mutated = first.get("profile").with_overrides({"board.grid_opacity": 0.09})
	var second: Dictionary = catalog.style_profile("tron_grid_flow")
	if second.get("profile").values() != first.get("profile").values():
		failures.append("editing a resolved built-in profile must not mutate the shipped source")
	if mutated.values() == second.get("profile").values():
		failures.append("resolved built-in profiles must be detached copies")
	if first.get("profile") == second.get("profile"):
		failures.append("each built-in resolution must produce an independent profile object")
	if bool(catalog.style_profile("no_such_style").get("ok", true)):
		failures.append("unknown built-in style identities must fail cleanly")

	# The shipped catalog file must never be read from or written to user data.
	var user_catalog := "user://built_in_style_catalog.json"
	if FileAccess.file_exists(user_catalog):
		failures.append("built-in catalog must not be mirrored into mutable user storage")
	return failures


func _test_catalog_rejection(registry) -> Array:
	var failures: Array = []
	_write_text(MALFORMED_CATALOG_PATH, "{not json")
	var malformed = CatalogScript.new(registry, MALFORMED_CATALOG_PATH)
	if not malformed.list_styles().is_empty() or not _contains_fragment(malformed.diagnostics(), "malformed"):
		failures.append("a malformed catalog must yield no styles and one clear diagnostic")

	_write_text(UNSUPPORTED_CATALOG_PATH, JSON.stringify({
		"catalog_type": CatalogScript.CATALOG_TYPE,
		"catalog_schema_version": CatalogScript.CATALOG_SCHEMA_VERSION + 1,
		"styles": [],
	}))
	var unsupported = CatalogScript.new(registry, UNSUPPORTED_CATALOG_PATH)
	if not unsupported.list_styles().is_empty() or not _contains_fragment(unsupported.diagnostics(), "schema version"):
		failures.append("an unsupported catalog schema must be rejected before use")

	_write_text(REJECTED_CATALOG_PATH, JSON.stringify({
		"catalog_type": CatalogScript.CATALOG_TYPE,
		"catalog_schema_version": CatalogScript.CATALOG_SCHEMA_VERSION,
		"styles": [
			{
				"style_id": "../escape",
				"display_name": "Unsafe",
				"category": "baseline",
				"presentation_profile": {"schema_version": 1, "values": {}},
			},
			{
				"style_id": "unknown_parameter",
				"display_name": "Unknown Parameter",
				"category": "baseline",
				"presentation_profile": {"schema_version": 1, "values": {"gameplay.board_state": []}},
			},
			{
				"style_id": "out_of_range",
				"display_name": "Out Of Range",
				"category": "baseline",
				"presentation_profile": {"schema_version": 1, "values": {"board.grid_opacity": 9.0}},
			},
			{
				"style_id": "unknown_category",
				"display_name": "Unknown Category",
				"category": "marketplace",
				"presentation_profile": {"schema_version": 1, "values": {}},
			},
			{
				"style_id": "healthy_entry",
				"display_name": "Healthy Entry",
				"category": "baseline",
				"presentation_profile": {"schema_version": 1, "values": {"board.grid_opacity": 0.4}},
			},
		],
	}))
	var rejected = CatalogScript.new(registry, REJECTED_CATALOG_PATH)
	var surviving: Array = rejected.list_styles()
	if surviving.size() != 1 or str(surviving[0].get("style_id", "")) != "healthy_entry":
		failures.append("invalid catalog entries must be isolated without hiding healthy ones: %s" % [surviving])
	if rejected.diagnostics().size() != 4:
		failures.append("each rejected catalog entry must produce one diagnostic: %s" % [rejected.diagnostics()])
	return failures


func _test_animated_background_component(registry) -> Array:
	var failures: Array = []
	var shader_source := FileAccess.get_file_as_string("res://assets/shaders/animated_background.gdshader")
	var shader_code := _without_comments(shader_source)
	if shader_code.find("depth_draw_never") == -1:
		failures.append("the backdrop material must never write depth")
	if shader_code.find("depth_test_disabled") != -1:
		failures.append("the backdrop must keep ordinary depth testing so gameplay always wins")
	if shader_code.find("TIME") != -1:
		failures.append("background motion must consume the shell-owned phase, not the engine clock")
	if shader_code.find("animation_phase") == -1:
		failures.append("the backdrop must consume the shell-owned animation phase uniform")

	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return failures + ["animated background component test requires a scene tree"]
	var background = AnimatedBackgroundScript.new()
	tree.root.add_child(background)
	var defaults = ProfileScript.canonical_defaults()

	background.apply_presentation_profile(defaults)
	var static_snapshot: Dictionary = background.deterministic_snapshot()
	if bool(static_snapshot.get("animated", true)) or bool(static_snapshot.get("visible", true)):
		failures.append("mode none must leave the current static background untouched")
	if bool(static_snapshot.get("processing", true)):
		failures.append("mode none must not consume per-frame work")
	background.advance_phase(2.0)
	if float(background.phase()) != 0.0:
		failures.append("mode none must never advance the animation phase")

	var animated = defaults.with_overrides({
		"environment.background_animation_mode": AnimatedBackgroundScript.MODE_TRON_GRID_FLOW,
		"environment.background_animation_intensity": 0.6,
		"environment.background_animation_speed": 0.75,
	})
	background.apply_presentation_profile(animated)
	var animated_snapshot: Dictionary = background.deterministic_snapshot()
	if not bool(animated_snapshot.get("animated", false)) or not bool(animated_snapshot.get("visible", false)):
		failures.append("the Tron mode must activate the animated background surface")
	if not bool(animated_snapshot.get("running", false)) or not bool(animated_snapshot.get("processing", false)):
		failures.append("an animated background with positive speed must actually run")
	if not bool(animated_snapshot.get("shader_ready", false)):
		failures.append("the backdrop must own the shipped background shader")
	if float(animated_snapshot.get("intensity", 0.0)) != 0.6 or float(animated_snapshot.get("speed", 0.0)) != 0.75:
		failures.append("animation parameters must propagate from the profile to the runtime component")
	background.advance_phase(1.0)
	var moved := float(background.phase())
	if moved <= 0.0:
		failures.append("time advancement must move the animated background phase")
	background.advance_phase(1.0)
	if float(background.phase()) <= moved:
		failures.append("the animated background phase must keep advancing")
	background.reset_phase()
	if float(background.phase()) != 0.0:
		failures.append("A/B comparison requires a resettable initial animation phase")

	var reduced = animated.with_overrides({"accessibility.reduced_motion": true})
	background.apply_presentation_profile(reduced)
	background.advance_phase(3.0)
	if float(background.phase()) != 0.0 or bool(background.deterministic_snapshot().get("running", true)):
		failures.append("reduced motion must freeze the animated background without a second motion preference")

	var still = animated.with_overrides({"environment.background_animation_speed": 0.0})
	background.apply_presentation_profile(still)
	background.advance_phase(3.0)
	if float(background.phase()) != 0.0 or not bool(background.deterministic_snapshot().get("animated", false)):
		failures.append("zero speed must hold a still frame while keeping the treatment visible")

	var faded = animated.with_overrides({"environment.background_animation_intensity": 0.0})
	background.apply_presentation_profile(faded)
	if bool(background.deterministic_snapshot().get("animated", true)):
		failures.append("zero strength must fall back to the static background")

	for display_mode in ["plain", "tron", "diagnostic"]:
		background.set_display_mode(display_mode)
		var themed: Dictionary = background.deterministic_snapshot()
		if themed.get("line_color") == null or str(themed.get("display_mode", "")) != display_mode:
			failures.append("the backdrop must resolve line colour from the semantic palette for %s" % display_mode)
	var background_source := FileAccess.get_file_as_string("res://scripts/rendering/animated_background.gd")
	if background_source.find("Color(") != -1:
		failures.append("the backdrop must resolve colour from palette roles, never from constructed literals")
	background.queue_free()
	return failures


func _test_designer_integration(registry) -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["Designer built-in integration requires a scene tree"]
	var designer = DesignerScript.new()
	tree.root.add_child(designer)
	await tree.process_frame
	var library = LibraryScript.new(registry, DESIGNER_DIRECTORY)
	var catalog = CatalogScript.new(registry)
	if not designer.configure(registry, library, catalog):
		designer.queue_free()
		return ["Designer should configure with the read-only built-in catalog"]
	var opening = ProfileScript.canonical_defaults()
	designer.open_with_profile(opening, "live_4d")
	await tree.process_frame

	var visible_records: Array = designer.built_in_style_records()
	if visible_records.size() < MINIMUM_SHIPPED_STYLES:
		failures.append("the Designer must expose the shipped built-in styles")
	var list_texts: Array = []
	for index in range(designer._built_in_list.item_count):
		list_texts.append(designer._built_in_list.get_item_text(index))
	if list_texts.size() != visible_records.size():
		failures.append("every built-in style must be listed in the Designer surface")
	for text in list_texts:
		if str(text).find("BUILT-IN") == -1:
			failures.append("built-in entries must be visibly distinguishable from user profiles: %s" % text)

	designer.capture_reference()
	var reference_values: Dictionary = designer.reference_profile().values()
	var catalog_before: Dictionary = catalog.deterministic_snapshot()
	var applied: Dictionary = designer.apply_built_in_style("tron_grid_flow")
	await tree.process_frame
	if not bool(applied.get("ok", false)):
		designer.queue_free()
		return failures + ["applying a built-in style should succeed: %s" % applied.get("error", "")]
	var style_values: Dictionary = catalog.style_profile("tron_grid_flow").get("profile").values()
	if designer.working_profile().values() != style_values:
		failures.append("applying a built-in style must replace detached working B with its values")
	if designer.reference_profile().values() != reference_values:
		failures.append("applying a built-in style must leave captured A unchanged")
	var applied_snapshot: Dictionary = designer.deterministic_snapshot()
	if str(applied_snapshot.get("applied_style_id", "")) != "tron_grid_flow":
		failures.append("the Designer must record which read-only style produced B")
	if not str(applied_snapshot.get("loaded_profile_id", "")).is_empty():
		failures.append("a built-in style must never become a user-profile save target")
	if not designer._save_profile_button.disabled:
		failures.append("explicit Save must stay disabled so a built-in style cannot be overwritten")
	if str(applied_snapshot.get("slot_text", "")).find("read-only") == -1:
		failures.append("the Designer must announce that B came from a read-only built-in style")
	if not library.list_profiles().is_empty():
		failures.append("applying a built-in style must not silently create a user profile")

	designer.set_parameter_value("board.grid_opacity", 0.11)
	await tree.process_frame
	if catalog.style_profile("tron_grid_flow").get("profile").values() != style_values:
		failures.append("editing B after applying a built-in style must not mutate the built-in source")
	if catalog.deterministic_snapshot() != catalog_before:
		failures.append("the shipped catalog must be immutable across Designer usage")
	if not designer.working_profile_dirty():
		failures.append("editing after applying a built-in style should read as modified")

	var saved: Dictionary = designer.save_working_as("Tron Study")
	if not bool(saved.get("ok", false)):
		failures.append("Save As after applying a built-in style should create an ordinary user profile")
	else:
		var saved_id := str(saved.get("record", {}).get("profile_id", ""))
		var stored = library.load_profile(saved_id).get("profile")
		if stored == null or stored.values() != designer.working_profile().values():
			failures.append("the saved user profile must contain the edited built-in-derived values")
		if str(designer.deterministic_snapshot().get("applied_style_id", "")) != "":
			failures.append("saving as a user profile should hand identity to the mutable library")

	var copied: Dictionary = designer.copy_built_in_style_to_library("blueprint_technical", "Blueprint Copy")
	if not bool(copied.get("ok", false)):
		failures.append("Copy to User Library should create a normal mutable user profile: %s" % copied.get("error", ""))
	else:
		var copy_id := str(copied.get("record", {}).get("profile_id", ""))
		if copy_id.length() != 32:
			failures.append("a copied built-in style must gain a normal generated user identity")
		if not bool(library.rename_profile(copy_id, "Blueprint Renamed").get("ok", false)):
			failures.append("a copied built-in style must be an ordinary editable user profile")
		if not bool(library.delete_profile(copy_id).get("ok", false)):
			failures.append("a copied built-in style must be deletable like any user profile")
	if catalog.deterministic_snapshot() != catalog_before:
		failures.append("copying a built-in style must not change the shipped catalog")

	designer.set_built_in_styles_expanded(true)
	designer.set_library_expanded(true)
	var disclosure: Dictionary = designer.deterministic_snapshot()
	if bool(disclosure.get("built_in_visible", true)) or not bool(disclosure.get("library_visible", false)):
		failures.append("the two disclosure sections must stay mutually exclusive")
	designer.set_built_in_styles_expanded(true)
	disclosure = designer.deterministic_snapshot()
	if not bool(disclosure.get("built_in_visible", false)) or bool(disclosure.get("library_visible", true)):
		failures.append("expanding built-in styles must collapse the user library")
	designer.end_session()
	if bool(designer.deterministic_snapshot().get("built_in_expanded", true)):
		failures.append("ending a Designer session must collapse the built-in section")

	designer.queue_free()
	await tree.process_frame
	return failures


func _test_live_integration(registry) -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["built-in style integration requires the production trace replay scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	for _frame in range(3):
		await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	var app = root.get_node_or_null("App")
	if hud == null or app == null:
		root.queue_free()
		return ["built-in style integration requires ReplayHud and TraceReplayApp"]
	var library = LibraryScript.new(registry, INTEGRATION_DIRECTORY)
	var catalog = CatalogScript.new(registry)
	hud._presentation_designer.configure(registry, library, catalog)

	for mode in ["live_2d", "live_3d", "live_4d"]:
		match mode:
			"live_2d": app._enter_live_2d_mode()
			"live_3d": app._enter_live_3d_mode()
			"live_4d": app._enter_live_4d_mode()
		await tree.process_frame
		hud._open_presentation_designer()
		await tree.process_frame
		var designer = hud._presentation_designer
		for record in catalog.list_styles():
			var style_id := str(record.get("style_id", ""))
			if not bool(designer.apply_built_in_style(style_id).get("ok", false)):
				failures.append("%s must apply in %s" % [style_id, mode])
				continue
			await tree.process_frame
			var applied_values: Dictionary = designer.working_profile().values()
			var expected: Dictionary = catalog.style_profile(style_id).get("profile").values()
			if applied_values != expected:
				failures.append("%s in %s must apply exactly its declared values" % [style_id, mode])
			var editable: Array = designer.deterministic_snapshot().get("applicable_ids", [])
			for setting_id in editable:
				if not registry.get_spec(str(setting_id)).applies_at_runtime(mode):
					failures.append("%s exposed non-applicable parameter %s in %s" % [style_id, setting_id, mode])
			if not hud._next_piece_panel.is_visible_in_tree() or not hud._hold_piece_panel.is_visible_in_tree():
				failures.append("%s in %s must preserve visible NEXT and HOLD" % [style_id, mode])
			if not hud._piece_control_strip.is_visible_in_tree():
				failures.append("%s in %s must preserve visible piece controls" % [style_id, mode])
		hud._presentation_designer.hide_preserving_preview()
		await tree.process_frame

	app._enter_live_4d_mode()
	await tree.process_frame
	hud._open_presentation_designer()
	await tree.process_frame
	var designer_4d = hud._presentation_designer
	var background = app._animated_background
	if background == null:
		root.queue_free()
		return failures + ["the production world must own one animated background component"]
	if background.get_parent() != app._camera_rig.get_node_or_null("Camera3D"):
		failures.append("the animated background must live in the camera-anchored environment layer")
	if background.position.z > -100.0:
		failures.append("the animated background must sit far behind the play volume, got %s" % background.position)
	if app._live_4d_presentation_root.is_ancestor_of(background):
		failures.append("the animated background must not join the gameplay presentation subtree")

	# Freeze the native clock before asserting presentation-only isolation. On a
	# slower CI runner an unpaused live gravity tick may legitimately advance the
	# game between awaited frames and would make this an animation timing test
	# instead of an isolation test.
	if not app._live_4d_paused:
		app._toggle_live_4d_pause()
	await tree.process_frame
	var hash_before := str(app._live_bridge.live_4d_state_hash())
	var snapshot_before: Dictionary = app._current_snapshot.duplicate(true)
	var settings_before: Dictionary = hud._settings_store.deterministic_snapshot()
	var basis_before: Array = app._live_4d_basis.slots()
	var camera_before: Dictionary = app._camera_rig.presentation_snapshot()

	designer_4d.apply_built_in_style("tet4d_balanced")
	await tree.process_frame
	var static_snapshot: Dictionary = background.deterministic_snapshot()
	if bool(static_snapshot.get("animated", true)) or bool(static_snapshot.get("visible", true)):
		failures.append("a non-animated built-in style must leave the static background in place")

	designer_4d.apply_built_in_style("tron_grid_flow")
	await tree.process_frame
	var tron_snapshot: Dictionary = background.deterministic_snapshot()
	if not bool(tron_snapshot.get("animated", false)) or not bool(tron_snapshot.get("running", false)):
		failures.append("the Tron built-in style must activate the animated background in production")
	if tron_snapshot.get("base_color") != app._world_environment.environment.background_color:
		failures.append("the backdrop base colour must track the resolved world background")
	if str(app._live_bridge.live_4d_state_hash()) != hash_before or app._current_snapshot != snapshot_before:
		failures.append("built-in style application must not touch deterministic gameplay state")
	if hud._settings_store.deterministic_snapshot() != settings_before:
		failures.append("applying a built-in style must not rewrite ordinary shell settings")
	if app._live_4d_basis.slots() != basis_before:
		failures.append("applying a built-in style must preserve exact basis and active slice")
	var camera_after: Dictionary = app._camera_rig.presentation_snapshot()
	for pose_key in ["target_yaw", "target_pitch", "current_yaw", "current_pitch", "target_focus", "current_focus", "zoom_multiplier"]:
		if camera_after.get(pose_key) != camera_before.get(pose_key):
			failures.append("built-in style application must preserve transient camera pose %s" % pose_key)

	# Animation-only isolation. Switching whole styles legitimately relayouts the
	# HUD through registry-owned density and contrast, so the layout claim is
	# proven by changing nothing except the three animation parameters.
	var animation_layout_before: Dictionary = hud.layout_contract_snapshot()
	var animation_hash_before := str(app._live_bridge.live_4d_state_hash())
	var animation_snapshot_before: Dictionary = app._current_snapshot.duplicate(true)
	var bounds_before: Dictionary = app._renderer.current_bounds()
	designer_4d.set_parameter_value("environment.background_animation_mode", "none")
	await tree.process_frame
	if bool(background.deterministic_snapshot().get("animated", true)):
		failures.append("clearing the animation mode must restore the static background")
	designer_4d.set_parameter_value("environment.background_animation_mode", "tron_grid_flow")
	designer_4d.set_parameter_value("environment.background_animation_speed", 1.4)
	await tree.process_frame
	if float(background.deterministic_snapshot().get("speed", 0.0)) != 1.4:
		failures.append("animation speed must propagate through the bounded apply seam")
	background.reset_phase()
	background.advance_phase(0.5)
	if float(background.phase()) <= 0.0:
		failures.append("advancing time must move the animated background")
	var animation_layout_after: Dictionary = hud.layout_contract_snapshot()
	for rect_key in ["body", "game_area", "game_viewport"]:
		if animation_layout_after.get(rect_key) != animation_layout_before.get(rect_key):
			failures.append("animation-only changes must not move cockpit rect %s" % rect_key)
	if str(app._live_bridge.live_4d_state_hash()) != animation_hash_before or app._current_snapshot != animation_snapshot_before:
		failures.append("animation-only changes and time advancement must not touch deterministic gameplay state")
	if app._renderer.current_bounds() != bounds_before:
		failures.append("animation-only changes must not move authoritative board bounds")
	if not hud._basis_panel.is_visible_in_tree() or str(animation_layout_after.get("basis_indicator_text", "")).find("Slice:") == -1:
		failures.append("the animated style must preserve visible Live 4D basis/slice state")
	if not hud._next_piece_panel.is_visible_in_tree() or not hud._hold_piece_panel.is_visible_in_tree() or not hud._piece_control_strip.is_visible_in_tree():
		failures.append("the animated style must preserve visible NEXT, HOLD, and piece controls")
	if not library.list_profiles().is_empty():
		failures.append("live built-in application must never write the user profile library")

	root.queue_free()
	await tree.process_frame
	return failures


func _without_comments(source: String) -> String:
	var kept: Array = []
	for line in source.split("\n"):
		var text := str(line)
		var comment := text.find("//")
		kept.append(text if comment == -1 else text.substr(0, comment))
	return "\n".join(kept)


func _difference_count(left, right) -> int:
	if not (left is Dictionary) or not (right is Dictionary):
		return 0
	var count := 0
	for key in left.keys():
		if left.get(key) != right.get(key):
			count += 1
	return count


func _contains_fragment(values: Array, fragment: String) -> bool:
	for value in values:
		if str(value).to_lower().find(fragment.to_lower()) >= 0:
			return true
	return false


func _write_text(path: String, contents: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(contents)
		file.close()


func _cleanup_all() -> void:
	for directory in [DESIGNER_DIRECTORY, INTEGRATION_DIRECTORY]:
		var absolute := ProjectSettings.globalize_path(directory)
		if not DirAccess.dir_exists_absolute(absolute):
			continue
		var handle := DirAccess.open(absolute)
		if handle == null:
			continue
		handle.list_dir_begin()
		var entry := handle.get_next()
		while not entry.is_empty():
			if not handle.current_is_dir():
				DirAccess.remove_absolute(absolute.path_join(entry))
			entry = handle.get_next()
		handle.list_dir_end()
		DirAccess.remove_absolute(absolute)
	for path in [MALFORMED_CATALOG_PATH, UNSUPPORTED_CATALOG_PATH, REJECTED_CATALOG_PATH]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
