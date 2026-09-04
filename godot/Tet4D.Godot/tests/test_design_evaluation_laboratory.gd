extends RefCounted

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const CatalogScript = preload("res://scripts/presentation/built_in_style_catalog.gd")
const LibraryScript = preload("res://scripts/presentation/presentation_profile_library.gd")
const ScenarioCatalogScript = preload("res://scripts/design_lab/design_scenario_catalog.gd")
const PresetResolverScript = preload("res://scripts/design_lab/design_preset_resolver.gd")
const ComparisonSessionScript = preload("res://scripts/design_lab/design_comparison_session.gd")
const EvaluationStoreScript = preload("res://scripts/design_lab/design_evaluation_store.gd")
const CaptureStoreScript = preload("res://scripts/design_lab/design_capture_store.gd")
const ExportBundleScript = preload("res://scripts/design_lab/design_export_bundle.gd")

const ROOT := "user://test_design_evaluation_laboratory"
const PROFILE_DIRECTORY := ROOT + "/profiles"
const EVALUATION_DIRECTORY := ROOT + "/evaluations"
const CAPTURE_DIRECTORY := ROOT + "/captures"
const EXPORT_DIRECTORY := ROOT + "/exports"


func run() -> Array:
	_cleanup()
	var failures: Array = []
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var catalog = CatalogScript.new(registry)
	var library = LibraryScript.new(registry, PROFILE_DIRECTORY)
	var scenarios = ScenarioCatalogScript.new(registry)
	var resolver = PresetResolverScript.new(catalog, library)
	failures.append_array(_test_scenarios(scenarios))
	failures.append_array(_test_candidate_and_comparison(catalog, library, scenarios, resolver))
	_cleanup()
	return failures


func _test_scenarios(scenarios) -> Array:
	var failures: Array = []
	var first: Dictionary = scenarios.deterministic_snapshot()
	var second: Dictionary = scenarios.deterministic_snapshot()
	if first != second or not scenarios.diagnostics().is_empty():
		failures.append("design scenario catalog should load deterministically without diagnostics: %s" % str(scenarios.diagnostics()))
	var records: Array = scenarios.list_scenarios()
	if records.size() < 7:
		failures.append("design scenario catalog should cover dimensional, density, and topology evaluation")
	var dimensions: Array = []
	var densities: Array = []
	var has_topology := false
	var has_preview_features := false
	for record in records:
		if not dimensions.has(record.get("dimension")):
			dimensions.append(record.get("dimension"))
		if not densities.has(record.get("density")):
			densities.append(record.get("density"))
		has_topology = has_topology or record.get("feature_tags", []).has("topology")
		has_preview_features = has_preview_features or (
			record.get("feature_tags", []).has("ghost")
			and record.get("feature_tags", []).has("next")
			and record.get("feature_tags", []).has("hold")
		)
		var again: Dictionary = scenarios.scenario(str(record.get("scenario_id")))
		if again != record or str(record.get("trace_identity_digest", "")).is_empty():
			failures.append("scenario repeat-load must preserve canonical replay identity")
	if not dimensions.has(2) or not dimensions.has(3) or not dimensions.has(4):
		failures.append("design scenarios must cover 2D, 3D, and 4D")
	if not densities.has("sparse") or not densities.has("dense") or not has_topology or not has_preview_features:
		failures.append("design scenarios must cover sparse/dense, topology, and NEXT/HOLD/Ghost evaluation")
	return failures


func _test_candidate_and_comparison(catalog, library, scenarios, resolver) -> Array:
	var failures: Array = []
	var built_ins: Array = catalog.list_styles()
	if built_ins.size() < 5:
		return ["design laboratory requires at least five built-in presets for explicit assignment coverage"]
	var built_in_snapshot: Dictionary = catalog.deterministic_snapshot()
	var first_id := str(built_ins[0].get("style_id"))
	var second_id := str(built_ins[1].get("style_id"))
	var duplicate: Dictionary = resolver.duplicate_as_candidate(PresetResolverScript.SOURCE_BUILT_IN, first_id, "Laboratory Candidate")
	if not bool(duplicate.get("ok", false)) or library.list_profiles().size() != 1:
		failures.append("built-in preset should duplicate into the existing mutable user profile library")
		return failures
	if catalog.deterministic_snapshot() != built_in_snapshot:
		failures.append("candidate creation must not mutate the shipped built-in catalog")
	var candidate_id := str(duplicate.get("record", {}).get("profile_id", ""))
	var resolved_a: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_BUILT_IN, second_id)
	var resolved_b: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_USER, candidate_id)
	var scenario: Dictionary = scenarios.scenario("plain_4d_dense_v1")
	var non_style := {
		"scenario_id": scenario.get("scenario_id"),
		"trace_identity_digest": scenario.get("trace_identity_digest"),
		"frame_index": scenario.get("frame_index"),
		"gameplay_state_hash": scenario.get("trace_final_state_hash"),
		"rng_state": "fixture-owned",
		"basis": "identity",
	}
	var session = ComparisonSessionScript.new()
	var started := session.start(scenario, resolved_a, resolved_b, non_style, true)
	if not bool(started.get("ok", false)):
		return ["comparison session should start from two detached presets: %s" % started.get("error", "")]
	var initial_a := session.arm_profile_snapshot("A")
	var initial_b := session.frozen_arm("B")
	var switched_b := session.activate("B", non_style)
	var restored_a := session.activate("A", non_style)
	if not bool(switched_b.get("ok", false)) or not bool(restored_a.get("ok", false)) or session.arm_profile_snapshot("A") != initial_a:
		failures.append("A -> B -> A must restore the exact frozen A snapshot")
	for index in range(8):
		var toggled := session.toggle(non_style)
		if not bool(toggled.get("ok", false)):
			failures.append("repeated A/B toggles must preserve the frozen non-style fingerprint")
	if session.snapshot().get("non_style_fingerprint") != non_style:
		failures.append("A/B switching must not mutate gameplay, replay, RNG, basis, or scenario identity")

	var resolved_3: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_BUILT_IN, str(built_ins[2].get("style_id")))
	var resolved_4: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_BUILT_IN, str(built_ins[3].get("style_id")))
	var resolved_5: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_BUILT_IN, str(built_ins[4].get("style_id")))
	var assigned_3 := session.assign("A", resolved_3, non_style)
	if not bool(assigned_3.get("ok", false)) or session.frozen_arm("B") != initial_b:
		failures.append("Set preset_3 as A must replace only A")
	session.activate("B", non_style)
	var b_before_hidden_a_assignment := session.frozen_arm("B")
	var assigned_4 := session.assign("A", resolved_4, non_style)
	if (
		not bool(assigned_4.get("ok", false))
		or session.frozen_arm("B") != b_before_hidden_a_assignment
		or session.shown_arm() != "B"
		or bool(assigned_4.get("refresh_shown", true))
	):
		failures.append("assigning A while B is shown must preserve B and shown_arm B")
	var a_before_b_assignment := session.frozen_arm("A")
	var assigned_5 := session.assign("B", resolved_5, non_style)
	if not bool(assigned_5.get("ok", false)) or session.frozen_arm("A") != a_before_b_assignment or session.shown_arm() != "B":
		failures.append("Set preset_5 as B must replace only B without changing shown_arm")
	var assignments_before_display_actions: Dictionary = session.snapshot().get("arms", {}).duplicate(true)
	for arm in ["A", "B", "A"]:
		session.activate(arm, non_style)
	for index in range(8):
		session.toggle(non_style)
	if session.snapshot().get("arms", {}) != assignments_before_display_actions:
		failures.append("show and repeated toggle operations must never mutate A/B assignments")
	var reset := session.reset_request(non_style)
	if not bool(reset.get("ok", false)) or session.snapshot().get("arms", {}) != assignments_before_display_actions:
		failures.append("scenario reset must preserve A/B assignments")
	var before_blind: Dictionary = session.snapshot().get("arms", {}).duplicate(true)
	session.set_blind(true)
	if session.arm_label("A").contains(str(session.frozen_arm("A").get("display_name", ""))):
		failures.append("blind labels must hide the current true arm identities")
	session.set_blind(false)
	if session.snapshot().get("arms", {}) != before_blind:
		failures.append("entering and exiting blind mode must preserve A/B assignments")
	var persisted: Dictionary = session.snapshot()
	var restored_session = ComparisonSessionScript.new()
	var restored := restored_session.restore(persisted)
	if not bool(restored.get("ok", false)) or restored_session.snapshot().get("arms", {}) != persisted.get("arms", {}) or restored_session.shown_arm() != persisted.get("shown_arm"):
		failures.append("comparison session persistence must retain A/B assignments and shown_arm")
	var drifted := non_style.duplicate(true)
	drifted["rng_state"] = "advanced"
	if bool(session.toggle(drifted).get("ok", false)):
		failures.append("A/B switching must fail closed when non-style state drifts")
	var assignments_before_edit: Dictionary = session.snapshot().get("arms", {}).duplicate(true)
	var user_profile = library.load_profile(candidate_id).get("profile")
	library.save_existing(candidate_id, user_profile.with_overrides({"ghost.opacity": 0.4}))
	if session.snapshot().get("arms", {}) != assignments_before_edit:
		failures.append("editing and saving a candidate must not mutate either frozen arm")
	var edited_candidate: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_USER, candidate_id)
	var b_before_explicit_candidate_assignment := session.frozen_arm("B")
	var assigned_candidate := session.assign("A", edited_candidate, non_style)
	if (
		not bool(assigned_candidate.get("ok", false))
		or session.frozen_arm("B") != b_before_explicit_candidate_assignment
		or session.arm_profile_snapshot("A") != edited_candidate.get("snapshot", {})
	):
		failures.append("explicit Set edited candidate as A must replace only A")
	failures.append_array(_test_evaluation_capture_export(session, resolved_b, resolved_a))
	return failures


func _test_evaluation_capture_export(session, candidate: Dictionary, reference: Dictionary) -> Array:
	var failures: Array = []
	var build := {"application_version": "0.9.0", "build_id": "test-build"}
	var store = EvaluationStoreScript.new(EVALUATION_DIRECTORY)
	var created := store.create_record(session.snapshot(), "prefer_b", {
		"readability": 4,
		"spatial_comprehension": 5,
		"ui_clarity": 3,
	}, "B improves slice separation.", build, 1)
	if not bool(created.get("ok", false)):
		return ["evaluation record should validate: %s" % created.get("error", "")]
	var frozen_presets: Dictionary = created.get("record", {}).get("presets", {}).duplicate(true)
	var saved := store.save_record(created.get("record", {}))
	var records := store.list_records()
	if not bool(saved.get("ok", false)) or records.size() != 1:
		failures.append("preference, ratings, notes, and provenance should round-trip locally: save=%s count=%d" % [str(saved), records.size()])
	elif (
		records[0].get("presets", {}).get("A", {}).get("snapshot_hash") != frozen_presets.get("A", {}).get("snapshot_hash")
		or records[0].get("presets", {}).get("B", {}).get("snapshot_hash") != frozen_presets.get("B", {}).get("snapshot_hash")
		or records[0].get("notes") != "B improves slice separation."
	):
		failures.append("evaluation history must retain exact frozen preset provenance and notes")
	if bool(store.create_record(session.snapshot(), "prefer_b", {"readability": 6}, "", build, 1).get("ok", false)):
		failures.append("evaluation ratings outside the 1-5 ordinal scale must be rejected")

	var image := Image.create(16, 16, false, Image.FORMAT_RGBA8)
	image.fill(Color(0.1, 0.7, 0.8, 1.0))
	var captures = CaptureStoreScript.new(CAPTURE_DIRECTORY)
	var a_capture := captures.capture_arm(image, session.snapshot(), "A", build, 1)
	var b_capture := captures.capture_arm(image, session.snapshot(), "B", build, 1)
	var metadata := captures.metadata_for_session(session.session_id())
	if not bool(a_capture.get("ok", false)) or not bool(b_capture.get("ok", false)):
		failures.append("A and B comparison PNGs should be created")
	elif not FileAccess.file_exists(a_capture.get("image_path")) or not FileAccess.file_exists(b_capture.get("image_path")):
		failures.append("capture outputs must exist at the comparison-specific paths")
	elif metadata.get("scenario_id") != session.snapshot().get("scenario_id") or metadata.get("captured_arms", {}).size() != 2:
		failures.append("capture metadata should retain scenario and both true arm identities")

	var exporter = ExportBundleScript.new(_registry())
	var exported := exporter.export_candidate(candidate, reference, records, EXPORT_DIRECTORY, build, 1)
	if not bool(exported.get("ok", false)):
		failures.append("nominated candidate should export a portable bundle: %s" % exported.get("error", ""))
		return failures
	for key in ["preset_path", "summary_path", "proposal_path"]:
		if not FileAccess.file_exists(str(exported.get(key, ""))):
			failures.append("nomination export must create %s" % key)
	var preset: Dictionary = _read_json(str(exported.get("preset_path", "")))
	if not bool(exporter.conform_preset_document(preset).get("ok", false)):
		failures.append("exported preset.json must validate against the canonical registry and owner map")
	var bad_owner: Dictionary = preset.duplicate(true)
	bad_owner["semantic_owners"][bad_owner.get("properties", {}).keys()[0]] = "WRONG_OWNER"
	if bool(exporter.conform_preset_document(bad_owner).get("ok", false)):
		failures.append("repository portability contract must reject semantic-owner mismatch")
	var proposal := _read_text(str(exported.get("proposal_path", "")))
	if not proposal.contains("Review input only") or not proposal.contains("Canonical property changes"):
		failures.append("DESIGN_PROPOSAL.md must state the promotion boundary and exact canonical changes")
	return failures


func _registry():
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	return registry


static func _read_json(path: String):
	var file := FileAccess.open(path, FileAccess.READ)
	return JSON.parse_string(file.get_as_text()) if file != null else null


static func _read_text(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	return file.get_as_text() if file != null else ""


static func _cleanup() -> void:
	_remove_tree(ProjectSettings.globalize_path(ROOT))


static func _remove_tree(path: String) -> void:
	var directory := DirAccess.open(path)
	if directory == null:
		return
	directory.list_dir_begin()
	var name := directory.get_next()
	while not name.is_empty():
		var child := path.path_join(name)
		if directory.current_is_dir():
			_remove_tree(child)
		else:
			DirAccess.remove_absolute(child)
		name = directory.get_next()
	directory.list_dir_end()
	DirAccess.remove_absolute(path)
