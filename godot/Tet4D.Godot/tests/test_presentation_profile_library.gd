extends RefCounted

const DesignerScript = preload("res://scripts/ui/presentation_designer.gd")
const LibraryScript = preload("res://scripts/presentation/presentation_profile_library.gd")
const ProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")

const TEST_DIRECTORY := "user://stage54f3_presentation_profiles"
const DESIGNER_DIRECTORY := "user://stage54f3_designer_profiles"
const INTEGRATION_DIRECTORY := "user://stage54f3_integration_profiles"
const EXPORT_PATH := "user://stage54f3_exported_profile.json"
const INVALID_PATH := "user://stage54f3_invalid_profile.json"


class FailingStorageOps:
	extends RefCounted

	func ensure_directory(_path: String) -> Dictionary:
		return {"ok": true, "error": ""}

	func write_json_file(_path: String, _payload: Dictionary, _allow_overwrite: bool) -> Dictionary:
		return {"ok": false, "error": "Injected storage write failure."}


func run() -> Array:
	var failures: Array = []
	_cleanup_all()
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	failures.append_array(_test_store_lifecycle(registry))
	failures.append_array(_test_import_validation(registry))
	failures.append_array(await _test_designer_boundary(registry))
	failures.append_array(await _test_live_integration(registry))
	_cleanup_all()
	return failures


func _test_store_lifecycle(registry) -> Array:
	var failures: Array = []
	var library = LibraryScript.new(registry, TEST_DIRECTORY)
	var source = _asymmetric_profile(registry)
	var created: Dictionary = library.save_new("Asymmetric Study", source)
	if not bool(created.get("ok", false)):
		return ["profile library should explicitly save a conforming working profile: %s" % created.get("error", "")]
	var source_record: Dictionary = created.get("record", {})
	var source_id := str(source_record.get("profile_id", ""))
	if source_id.length() != 32 or str(source_record.get("display_name")) != "Asymmetric Study":
		failures.append("saved profiles should use generated stable identity and the validated display name")
	var records := library.list_profiles()
	if records.size() != 1 or records[0] != source_record:
		failures.append("library listing should derive one deterministic validated record from storage")
	var saved_path := TEST_DIRECTORY.path_join("%s%s" % [source_id, LibraryScript.FILE_SUFFIX])
	if not FileAccess.file_exists(saved_path) or saved_path.find("Asymmetric Study") >= 0:
		failures.append("library filenames must derive only from stable IDs, never display names")
	var artifact = _read_json(saved_path)
	if not (artifact is Dictionary) or artifact.get("artifact_type") != LibraryScript.ARTIFACT_TYPE:
		failures.append("saved files should use the versioned portable artifact envelope")
	elif (
		artifact.get("presentation_profile", {}).get("schema_version") != ProfileScript.SCHEMA_VERSION
		or library.load_profile(source_id).get("profile").values() != source.values()
	):
		failures.append("saved artifact should deserialize to the exact authoritative PresentationProfile values")

	for invalid_name in ["", "   ", "../escape", "/absolute", "bad/name", "bad\\name", "bad:name", "x".repeat(81)]:
		if bool(library.save_new(invalid_name, source).get("ok", false)):
			failures.append("invalid or unsafe display name should be rejected: %s" % invalid_name)
	if bool(library.save_new("asymmetric study", source).get("ok", false)):
		failures.append("display-name uniqueness should be case-insensitive and never overwrite")

	var duplicate: Dictionary = library.duplicate_profile(source_id)
	if not bool(duplicate.get("ok", false)):
		failures.append("Duplicate should create an independent profile")
	else:
		var duplicate_record: Dictionary = duplicate.get("record", {})
		var duplicate_id := str(duplicate_record.get("profile_id", ""))
		if duplicate_id == source_id or duplicate.get("profile").values() != source.values():
			failures.append("duplicate should allocate a new identity with identical semantic values")
		var before_rename := library.load_profile(duplicate_id)
		var renamed: Dictionary = library.rename_profile(duplicate_id, "Independent Copy")
		var after_rename := library.load_profile(duplicate_id)
		if not bool(renamed.get("ok", false)) or renamed.get("record", {}).get("profile_id") != duplicate_id:
			failures.append("rename should preserve stable profile identity")
		if before_rename.get("profile").values() != after_rename.get("profile").values():
			failures.append("rename should preserve all presentation values")

		var edited_source = source.with_overrides({"ghost.opacity": 0.45})
		if not bool(library.save_existing(source_id, edited_source).get("ok", false)):
			failures.append("explicit Save should update an existing stable profile")
		if library.load_profile(duplicate_id).get("profile").values() != source.values():
			failures.append("saving the source should not mutate its independent duplicate")
		var detached = library.load_profile(source_id).get("profile")
		var detached_edit = detached.with_overrides({"board.grid_opacity": 0.2})
		if detached_edit.values() == detached.values() or library.load_profile(source_id).get("profile").values() != edited_source.values():
			failures.append("loaded profiles should be detached from their stored artifact")

	var export_result := library.export_profile(source_id, EXPORT_PATH)
	if not bool(export_result.get("ok", false)):
		failures.append("export should write a selected portable artifact")
	else:
		var exported = _read_json(EXPORT_PATH)
		if not (exported is Dictionary) or exported.has("settings") or exported.has("camera_pose") or exported.has("gameplay"):
			failures.append("export should contain only artifact metadata and the profile payload")
		var imported := library.import_profile(EXPORT_PATH)
		if not bool(imported.get("ok", false)):
			failures.append("a valid exported profile should import successfully: %s" % imported.get("error", ""))
		elif imported.get("record", {}).get("profile_id") == source_id or imported.get("profile").values() != library.load_profile(source_id).get("profile").values():
			failures.append("export/import should allocate a fresh local ID and preserve semantic values")

	var active_detached = library.load_profile(source_id).get("profile")
	var active_values: Dictionary = active_detached.values()
	if not bool(library.delete_profile(source_id).get("ok", false)):
		failures.append("explicit deletion should remove a stored profile")
	if active_detached.values() != active_values or bool(library.load_profile(source_id).get("ok", false)):
		failures.append("deleting storage should preserve the already-detached runtime profile")

	var corrupt_id := "b".repeat(32)
	_write_text(TEST_DIRECTORY.path_join("%s%s" % [corrupt_id, LibraryScript.FILE_SUFFIX]), "{damaged")
	var healthy_count := library.list_profiles().size()
	if healthy_count < 2 or not _contains_fragment(library.diagnostics(), "damaged"):
		failures.append("one corrupted profile should be isolated without making healthy library entries unavailable")

	var blocked_library = LibraryScript.new(registry, "user://unused_stage54f3_failure", FailingStorageOps.new())
	var before_failure := blocked_library.deterministic_snapshot()
	var failed_save := blocked_library.save_new("Cannot Write", source)
	if bool(failed_save.get("ok", false)) or blocked_library.deterministic_snapshot().get("write_count") != before_failure.get("write_count"):
		failures.append("storage failure should report cleanly without claiming a write")
	return failures


func _test_import_validation(registry) -> Array:
	var failures: Array = []
	var library = LibraryScript.new(registry, TEST_DIRECTORY)
	var profile = _asymmetric_profile(registry)
	var base := {
		"artifact_type": LibraryScript.ARTIFACT_TYPE,
		"artifact_schema_version": LibraryScript.ARTIFACT_SCHEMA_VERSION,
		"profile_id": "a".repeat(32),
		"display_name": "Portable Source",
		"presentation_profile": profile.snapshot(),
	}
	_write_text(INVALID_PATH, "{malformed")
	if bool(library.import_profile(INVALID_PATH).get("ok", false)):
		failures.append("malformed JSON import should fail")
	_write_text(INVALID_PATH, "[]")
	if bool(library.import_profile(INVALID_PATH).get("ok", false)):
		failures.append("wrong-root-shape import should fail")

	var cases := []
	var future_artifact := base.duplicate(true)
	future_artifact["artifact_schema_version"] = 99
	cases.append(["unsupported artifact schema", future_artifact])
	var future_profile := base.duplicate(true)
	future_profile["presentation_profile"]["schema_version"] = 99
	cases.append(["unsupported profile schema", future_profile])
	var wrong_type := base.duplicate(true)
	wrong_type["presentation_profile"]["values"]["ghost.enabled"] = "yes"
	cases.append(["wrong parameter type", wrong_type])
	var out_of_range := base.duplicate(true)
	out_of_range["presentation_profile"]["values"]["ghost.opacity"] = 500.0
	cases.append(["out-of-range number", out_of_range])
	var invalid_enum := base.duplicate(true)
	invalid_enum["presentation_profile"]["values"]["display.hud_density"] = "enormous"
	cases.append(["invalid enum", invalid_enum])
	var non_finite := base.duplicate(true)
	non_finite["presentation_profile"]["values"]["ghost.opacity"] = INF
	cases.append(["non-finite number", non_finite])
	var unknown := base.duplicate(true)
	unknown["presentation_profile"]["values"]["future.unknown"] = true
	cases.append(["unknown parameter", unknown])
	var unsafe_name := base.duplicate(true)
	unsafe_name["display_name"] = "../../escape"
	cases.append(["unsafe imported display name", unsafe_name])
	var unsafe_id := base.duplicate(true)
	unsafe_id["profile_id"] = "../../escape"
	cases.append(["unsafe imported identity", unsafe_id])
	for case in cases:
		var before := library.deterministic_snapshot()
		var result: Dictionary = library.import_artifact(case[1], "Rejected %s" % case[0])
		var after := library.deterministic_snapshot()
		if bool(result.get("ok", false)):
			failures.append("%s import should fail authoritative validation" % case[0])
		if after.get("profiles") != before.get("profiles") or after.get("write_count") != before.get("write_count") or after.get("mutation_count") != before.get("mutation_count"):
			failures.append("failed %s import should be atomic" % case[0])

	var missing_current := base.duplicate(true)
	missing_current["display_name"] = "Older Additive Profile"
	missing_current["presentation_profile"]["values"].erase("ghost.opacity")
	var missing_result: Dictionary = library.import_artifact(missing_current)
	if not bool(missing_result.get("ok", false)):
		failures.append("same-schema missing parameters should follow PresentationProfile default-fill policy")
	elif missing_result.get("profile").value("ghost.opacity") != registry.get_spec("ghost.opacity").default_value():
		failures.append("same-schema missing parameters should receive authoritative registry defaults")
	return failures


func _test_designer_boundary(registry) -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var library = LibraryScript.new(registry, DESIGNER_DIRECTORY)
	var opening = ProfileScript.from_snapshot(registry, {
		"schema_version": ProfileScript.SCHEMA_VERSION,
		"values": registry.default_values(),
	})
	var designer = DesignerScript.new()
	designer.size = Vector2(420, 700)
	tree.root.add_child(designer)
	await tree.process_frame
	if not designer.configure(registry, library) or not designer.open_with_profile(opening, "live_4d"):
		designer.queue_free()
		return ["Designer should configure with an injected profile library"]
	if designer.deterministic_snapshot().get("library_expanded") or designer.deterministic_snapshot().get("library_visible"):
		failures.append("profile library should be collapsed by default and consume no permanent cockpit height")
	designer.capture_reference()
	var reference_before: Dictionary = designer.reference_profile().snapshot()
	var write_before := int(library.deterministic_snapshot().get("write_count", -1))
	designer.set_parameter_value("ghost.opacity", 1.25)
	designer.show_slot(DesignerScript.SLOT_REFERENCE)
	designer.show_slot(DesignerScript.SLOT_WORKING)
	designer.collapse_to_compact()
	designer.expand_to_full()
	designer.keep_working_and_hide()
	designer.open_with_profile(opening, "live_4d")
	if int(library.deterministic_snapshot().get("write_count", -1)) != write_before:
		failures.append("edit, A/B, compact, Keep B & Hide, hide, and reopen must perform zero library writes")

	designer.show_slot(DesignerScript.SLOT_REFERENCE)
	var working_at_save: Dictionary = designer.working_profile().values()
	var saved: Dictionary = designer.save_working_as("Designer Working B")
	if not bool(saved.get("ok", false)) or designer.working_profile_dirty():
		failures.append("explicit Save As should persist working B and establish a clean semantic baseline")
	var saved_id := str(saved.get("record", {}).get("profile_id", ""))
	if library.load_profile(saved_id).get("profile").values() != working_at_save:
		failures.append("Save As must persist working B even while immutable A is displayed")
	designer.show_slot(DesignerScript.SLOT_WORKING)
	var stored_before_edit: Dictionary = library.load_profile(saved_id).get("profile").values()
	designer.set_parameter_value("ghost.opacity", 0.5)
	if not designer.working_profile_dirty() or library.load_profile(saved_id).get("profile").values() != stored_before_edit:
		failures.append("editing loaded B should mark dirty without mutating its stored artifact")
	var writes_after_edit := int(library.deterministic_snapshot().get("write_count", -1))
	designer.show_slot(DesignerScript.SLOT_REFERENCE)
	designer.show_slot(DesignerScript.SLOT_WORKING)
	if int(library.deterministic_snapshot().get("write_count", -1)) != writes_after_edit or not designer.working_profile_dirty():
		failures.append("A/B display switching should neither save nor affect semantic dirty state")
	if not bool(designer.save_working().get("ok", false)) or designer.working_profile_dirty():
		failures.append("explicit Save should update only the stable profile and clear dirty state")

	var comparison = _asymmetric_profile(registry)
	var comparison_saved: Dictionary = library.save_new("Comparison Profile", comparison)
	var comparison_id := str(comparison_saved.get("record", {}).get("profile_id", ""))
	var previews: Array = []
	designer.profile_preview_requested.connect(func(profile) -> void: previews.append(profile.snapshot()))
	var reference_on_load: Dictionary = designer.reference_profile().snapshot()
	if not bool(designer.load_saved_profile(comparison_id).get("ok", false)):
		failures.append("Designer Load should replace working B from a valid artifact")
	elif designer.working_profile().values() != comparison.values() or designer.deterministic_snapshot().get("displayed_slot") != DesignerScript.SLOT_WORKING:
		failures.append("Load should create/display an exact detached working B")
	if designer.reference_profile().snapshot() != reference_on_load or designer.reference_profile().snapshot() != reference_before:
		failures.append("loading B must not recapture or mutate immutable A")
	if previews.is_empty() or previews[-1].get("values", {}) != comparison.values():
		failures.append("loading should apply detached B through the existing preview boundary")
	var loaded_stored: Dictionary = library.load_profile(comparison_id).get("profile").values()
	designer.set_parameter_value("board.grid_opacity", 0.2)
	if library.load_profile(comparison_id).get("profile").values() != loaded_stored:
		failures.append("editing a loaded working B must not alias stored profile values")

	var runtime_before_delete: Dictionary = designer.working_profile().snapshot()
	var reference_before_delete: Dictionary = designer.reference_profile().snapshot()
	var preview_count_before_delete := previews.size()
	if not bool(designer.delete_saved_profile(comparison_id).get("ok", false)):
		failures.append("Designer should support explicit deletion")
	if designer.working_profile().snapshot() != runtime_before_delete or designer.reference_profile().snapshot() != reference_before_delete or previews.size() != preview_count_before_delete:
		failures.append("deleting a stored source must leave detached B, A, and runtime preview unchanged")

	for mode in ["live_2d", "live_3d", "live_4d"]:
		designer.set_runtime_context(mode)
		designer.load_saved_profile(saved_id)
		var snapshot: Dictionary = designer.deterministic_snapshot()
		var expected_count := 16 if mode == "live_2d" else 18 if mode == "live_3d" else 20
		if snapshot.get("applicable_ids", []).size() != expected_count or designer.working_profile().values() != library.load_profile(saved_id).get("profile").values():
			failures.append("%s load should preserve the full payload while exposure remains registry-applicable" % mode)
	designer.set_library_expanded(true)
	if not designer.deterministic_snapshot().get("library_visible"):
		failures.append("full Designer should expose the bounded library on deliberate expansion")
	designer.collapse_to_compact()
	if designer.deterministic_snapshot().get("full_visible") or not designer.deterministic_snapshot().get("compact_visible"):
		failures.append("compact Designer should remain usable independently of expanded library disclosure")
	if not (designer._delete_confirmation is ConfirmationDialog) or not (designer._overwrite_confirmation is ConfirmationDialog):
		failures.append("delete and overwrite UI actions should use deliberate confirmation")
	designer.queue_free()
	await tree.process_frame
	return failures


func _test_live_integration(registry) -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["profile-library integration requires the production trace replay scene"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	var app = root.get_node_or_null("App")
	if hud == null or app == null:
		root.queue_free()
		return ["profile-library integration requires ReplayHud and TraceReplayApp"]
	var library = LibraryScript.new(registry, INTEGRATION_DIRECTORY)
	hud._presentation_designer.configure(registry, library)
	app._enter_live_4d_mode()
	await tree.process_frame
	hud._open_presentation_designer()
	await tree.process_frame
	var designer = hud._presentation_designer
	var game_before: Dictionary = app._current_snapshot.duplicate(true)
	var setup_before: Dictionary = app._active_live_setup.duplicate(true)
	var state_hash_before := str(app._live_bridge.live_4d_state_hash())
	var settings_before: Dictionary = hud._settings_store.deterministic_snapshot()
	var basis_before: Array = app._live_4d_basis.slots()
	var orientation_before: Dictionary = app._live_4d_local_orientation.snapshot()
	var camera_before: Dictionary = app._camera_rig.presentation_snapshot()
	var next_before := _piece_semantic_snapshot(hud._next_piece_panel.deterministic_snapshot())
	var hold_before := _piece_semantic_snapshot(hud._hold_piece_panel.deterministic_snapshot())
	var stored: Dictionary = designer.save_working_as("Integrated Runtime")
	var stored_id := str(stored.get("record", {}).get("profile_id", ""))
	designer.set_parameter_value("environment.background_intensity", 1.35)
	await tree.process_frame
	if not bool(designer.load_saved_profile(stored_id).get("ok", false)):
		failures.append("production Designer should load a named profile through its bounded apply seam")
	await tree.process_frame
	if app._current_snapshot != game_before or app._active_live_setup != setup_before or str(app._live_bridge.live_4d_state_hash()) != state_hash_before:
		failures.append("profile save/edit/load must preserve deterministic game snapshot, setup, and state hash")
	if hud._settings_store.deterministic_snapshot() != settings_before:
		failures.append("named profile lifecycle must not rewrite ordinary shell settings")
	if app._live_4d_basis.slots() != basis_before or app._live_4d_local_orientation.snapshot() != orientation_before:
		failures.append("profile lifecycle must preserve exact basis, active slice, and local orientation")
	var camera_after: Dictionary = app._camera_rig.presentation_snapshot()
	for pose_key in ["target_yaw", "target_pitch", "target_roll", "current_yaw", "current_pitch", "current_roll", "target_focus", "current_focus", "zoom_multiplier"]:
		if camera_after.get(pose_key) != camera_before.get(pose_key):
			failures.append("profile load must preserve transient camera pose field %s" % pose_key)
	if _piece_semantic_snapshot(hud._next_piece_panel.deterministic_snapshot()) != next_before or _piece_semantic_snapshot(hud._hold_piece_panel.deterministic_snapshot()) != hold_before:
		failures.append("profile lifecycle must preserve authoritative NEXT and HOLD identity/availability")
	if not hud._next_piece_panel.is_visible_in_tree() or not hud._hold_piece_panel.is_visible_in_tree() or not hud._piece_control_strip.is_visible_in_tree() or not hud._basis_panel.is_visible_in_tree():
		failures.append("profile management must preserve NEXT, HOLD, piece controls, and 4D basis cockpit surfaces")
	root.queue_free()
	await tree.process_frame
	return failures


func _asymmetric_profile(registry):
	var profile = ProfileScript.from_snapshot(registry, {
		"schema_version": ProfileScript.SCHEMA_VERSION,
		"values": registry.default_values(),
	})
	return profile.with_overrides({
		"board.grid_opacity": 0.55,
		"active_cells.opacity": 0.65,
		"ghost.opacity": 1.25,
		"slice_set.spacing": 1.4,
		"display.hud_density": "compact",
		"environment.background_intensity": 1.3,
		"accessibility.high_contrast": true,
	})


func _piece_semantic_snapshot(snapshot: Dictionary) -> Dictionary:
	var result := snapshot.duplicate(true)
	var thumbnail: Dictionary = result.get("thumbnail", {})
	thumbnail.erase("style_revision")
	result["thumbnail"] = thumbnail
	return result


func _contains_fragment(values: Array, fragment: String) -> bool:
	for value in values:
		if str(value).to_lower().find(fragment.to_lower()) >= 0:
			return true
	return false


func _read_json(path: String):
	var file := FileAccess.open(path, FileAccess.READ)
	return JSON.parse_string(file.get_as_text()) if file != null else null


func _write_text(path: String, text: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(text)
		file.close()


func _cleanup_all() -> void:
	for directory in [TEST_DIRECTORY, DESIGNER_DIRECTORY, INTEGRATION_DIRECTORY]:
		_cleanup_directory(directory)
	for path in [EXPORT_PATH, "%s.tmp" % EXPORT_PATH, "%s.bak" % EXPORT_PATH, INVALID_PATH]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _cleanup_directory(path: String) -> void:
	var absolute := ProjectSettings.globalize_path(path)
	var directory := DirAccess.open(absolute)
	if directory == null:
		return
	directory.list_dir_begin()
	var entry := directory.get_next()
	while not entry.is_empty():
		if not directory.current_is_dir():
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path.path_join(entry)))
		entry = directory.get_next()
	directory.list_dir_end()
	DirAccess.remove_absolute(absolute)
