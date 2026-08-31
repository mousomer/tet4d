extends RefCounted

const DesignerScript = preload("res://scripts/ui/presentation_designer.gd")
const LibraryScript = preload("res://scripts/presentation/presentation_profile_library.gd")
const ProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")

const TEST_DIRECTORY := "user://stage54f3_presentation_profiles"
const DESIGNER_DIRECTORY := "user://stage54f3_designer_profiles"
const INTEGRATION_DIRECTORY := "user://stage54f3_integration_profiles"
const WRITE_FAILURE_DIRECTORY := "user://stage54f3r_write_failure_profiles"
const DESIGNER_FAILURE_DIRECTORY := "user://stage54f3r_designer_failure_profiles"
const RESTORE_RENAME_DIRECTORY := "user://stage54f3r_restore_rename_profiles"
const RESTORE_COPY_DIRECTORY := "user://stage54f3r_restore_copy_profiles"
const RESTORE_TOTAL_FAILURE_DIRECTORY := "user://stage54f3r_restore_total_failure_profiles"
const DIAGNOSTIC_DIRECTORY := "user://stage54f3r_diagnostic_profiles"
const WARNING_DIRECTORY := "user://stage54f3r1_warning_profiles"
const EXPORT_PATH := "user://stage54f3_exported_profile.json"
const ABSENT_INSTALL_EXPORT_PATH := "user://stage54f3r1_absent_install_export.json"
const INVALID_PATH := "user://stage54f3_invalid_profile.json"
const UNRELATED_BACKUP_SENTINEL := "unrelated sibling backup sentinel\n"


class FailingStorageOps:
	extends RefCounted

	func ensure_directory(_path: String) -> Dictionary:
		return {"ok": true, "error": ""}

	func write_json_file(_path: String, _payload: Dictionary, _allow_overwrite: bool) -> Dictionary:
		return {"ok": false, "error": "Injected storage write failure."}


class InjectedPersistenceOps:
	extends RefCounted

	var write_failures: Dictionary = {}
	var rename_failures: Dictionary = {}
	var copy_failures: Dictionary = {}
	var remove_failures: Dictionary = {}
	var write_count := 0
	var rename_count := 0
	var copy_count := 0
	var remove_count := 0

	func ensure_directory(path: String) -> Dictionary:
		var absolute := ProjectSettings.globalize_path(path)
		if DirAccess.dir_exists_absolute(absolute):
			return {"ok": true, "error": ""}
		var error := DirAccess.make_dir_recursive_absolute(absolute)
		return {"ok": error == OK, "error": "" if error == OK else "Injected directory creation failed."}

	func write_text_file(path: String, contents: String) -> Error:
		write_count += 1
		var file := FileAccess.open(path, FileAccess.WRITE)
		if file == null:
			return FileAccess.get_open_error()
		if write_failures.has(write_count):
			file.store_string(contents.left(maxi(1, contents.length() / 4)))
			file.flush()
			file.close()
			return write_failures.get(write_count)
		file.store_string(contents)
		file.flush()
		var error := file.get_error()
		file.close()
		return error

	func file_exists(path: String) -> bool:
		return FileAccess.file_exists(path)

	func rename_absolute(from_path: String, to_path: String) -> Error:
		rename_count += 1
		if rename_failures.has(rename_count):
			return rename_failures.get(rename_count)
		return DirAccess.rename_absolute(from_path, to_path)

	func copy_absolute(from_path: String, to_path: String) -> Error:
		copy_count += 1
		if copy_failures.has(copy_count):
			return copy_failures.get(copy_count)
		return DirAccess.copy_absolute(from_path, to_path)

	func remove_absolute(path: String) -> Error:
		remove_count += 1
		if remove_failures.has(remove_count):
			return remove_failures.get(remove_count)
		return DirAccess.remove_absolute(path)


func run() -> Array:
	var failures: Array = []
	_cleanup_all()
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	failures.append_array(_test_store_lifecycle(registry))
	failures.append_array(_test_write_and_restore_robustness(registry))
	failures.append_array(_test_deterministic_diagnostics(registry))
	failures.append_array(_test_import_validation(registry))
	failures.append_array(await _test_designer_boundary(registry))
	failures.append_array(await _test_designer_failed_save(registry))
	failures.append_array(await _test_designer_cleanup_warning(registry))
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

	_write_text("%s.bak" % EXPORT_PATH, UNRELATED_BACKUP_SENTINEL)
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
	if _read_text("%s.bak" % EXPORT_PATH) != UNRELATED_BACKUP_SENTINEL:
		failures.append("fresh profile export must preserve an unrelated sibling backup byte-for-byte")

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


func _test_write_and_restore_robustness(registry) -> Array:
	var failures: Array = []
	var source = _asymmetric_profile(registry)
	var edited = source.with_overrides({"ghost.opacity": 0.45})

	var write_library = LibraryScript.new(registry, WRITE_FAILURE_DIRECTORY)
	var original: Dictionary = write_library.save_new("Write Failure Original", source)
	write_library.save_new("Write Failure Healthy", source)
	var original_id := str(original.get("record", {}).get("profile_id", ""))
	var original_path := WRITE_FAILURE_DIRECTORY.path_join("%s%s" % [original_id, LibraryScript.FILE_SUFFIX])
	var original_text := _read_text(original_path)
	var write_ops := InjectedPersistenceOps.new()
	write_ops.write_failures = {1: ERR_FILE_CANT_WRITE, 2: ERR_FILE_CANT_WRITE}
	var blocked = LibraryScript.new(registry, WRITE_FAILURE_DIRECTORY, write_ops)
	var overwrite_result: Dictionary = blocked.save_existing(original_id, edited)
	if bool(overwrite_result.get("ok", false)) or not bool(overwrite_result.get("destination_untouched", false)):
		failures.append("incomplete overwrite must fail explicitly before modifying the destination")
	var preserved_load: Dictionary = blocked.load_profile(original_id)
	if not bool(preserved_load.get("ok", false)):
		failures.append("incomplete overwrite must leave the previous profile loadable: %s" % preserved_load.get("error", ""))
		return failures
	var preserved_profile = preserved_load.get("profile")
	if preserved_profile == null:
		failures.append("successful load after incomplete overwrite must return a detached profile")
		return failures
	if _read_text(original_path) != original_text or preserved_profile.values() != source.values():
		failures.append("incomplete overwrite must preserve the exact readable previous profile")
	if int(blocked.deterministic_snapshot().get("write_count", -1)) != 0 or int(blocked.deterministic_snapshot().get("mutation_count", -1)) != 0:
		failures.append("incomplete overwrite must not increment successful write or mutation counters")
	if FileAccess.file_exists("%s.tmp" % original_path):
		failures.append("incomplete overwrite should remove its invalid temporary artifact")
	var before_save_as: Array = blocked.list_profiles()
	var save_as_result: Dictionary = blocked.save_new("Write Failure Phantom", edited)
	var after_save_as: Array = blocked.list_profiles()
	if bool(save_as_result.get("ok", false)) or after_save_as != before_save_as:
		failures.append("incomplete Save As must fail without creating a phantom profile")
	if _records_contain_name(after_save_as, "Write Failure Phantom") or _directory_has_suffix(WRITE_FAILURE_DIRECTORY, ".tmp"):
		failures.append("failed Save As must leave neither a listed record nor a stale temporary artifact")

	_write_text("%s.bak" % ABSENT_INSTALL_EXPORT_PATH, UNRELATED_BACKUP_SENTINEL)
	var install_ops := InjectedPersistenceOps.new()
	install_ops.rename_failures = {1: ERR_CANT_CREATE}
	var install_library = LibraryScript.new(registry, WRITE_FAILURE_DIRECTORY, install_ops)
	var install_before: Dictionary = install_library.deterministic_snapshot()
	var install_result: Dictionary = install_library.export_profile(original_id, ABSENT_INSTALL_EXPORT_PATH)
	var install_after: Dictionary = install_library.deterministic_snapshot()
	if bool(install_result.get("ok", false)) or not bool(install_result.get("destination_untouched", false)):
		failures.append("fresh export install failure must report bounded failure before creating a destination")
	if FileAccess.file_exists(ABSENT_INSTALL_EXPORT_PATH) or FileAccess.file_exists("%s.tmp" % ABSENT_INSTALL_EXPORT_PATH):
		failures.append("fresh export install failure must leave no destination or temporary phantom")
	if _read_text("%s.bak" % ABSENT_INSTALL_EXPORT_PATH) != UNRELATED_BACKUP_SENTINEL:
		failures.append("fresh export install failure must not touch an unrelated sibling backup")
	if (
		install_after.get("write_count") != install_before.get("write_count")
		or install_after.get("mutation_count") != install_before.get("mutation_count")
	):
		failures.append("fresh export install failure must not increment profile-library success counters")

	failures.append_array(_test_restore_case(
		registry,
		RESTORE_RENAME_DIRECTORY,
		{1: ERR_CANT_CREATE, 3: ERR_CANT_CREATE},
		{},
		"rename"
	))
	failures.append_array(_test_restore_case(
		registry,
		RESTORE_COPY_DIRECTORY,
		{1: ERR_CANT_CREATE, 3: ERR_CANT_CREATE, 4: ERR_CANT_CREATE},
		{},
		"copy"
	))
	failures.append_array(_test_restore_case(
		registry,
		RESTORE_TOTAL_FAILURE_DIRECTORY,
		{1: ERR_CANT_CREATE, 3: ERR_CANT_CREATE, 4: ERR_CANT_CREATE},
		{1: ERR_FILE_CANT_WRITE},
		"failed"
	))
	return failures


func _test_restore_case(
	registry,
	directory: String,
	rename_failures: Dictionary,
	copy_failures: Dictionary,
	expected_restoration: String
) -> Array:
	var failures: Array = []
	var source = _asymmetric_profile(registry)
	var edited = source.with_overrides({"ghost.opacity": 0.45})
	var initial = LibraryScript.new(registry, directory)
	var original: Dictionary = initial.save_new("Restore Target", source)
	initial.save_new("Unrelated Healthy", source)
	var original_id := str(original.get("record", {}).get("profile_id", ""))
	var original_path := directory.path_join("%s%s" % [original_id, LibraryScript.FILE_SUFFIX])
	var original_text := _read_text(original_path)
	var ops := InjectedPersistenceOps.new()
	ops.rename_failures = rename_failures
	ops.copy_failures = copy_failures
	var library = LibraryScript.new(registry, directory, ops)
	var result: Dictionary = library.save_existing(original_id, edited)
	if bool(result.get("ok", false)) or str(result.get("restoration", "")) != expected_restoration:
		failures.append("%s restoration case must report explicit replacement failure metadata" % expected_restoration)
	if int(library.deterministic_snapshot().get("write_count", -1)) != 0 or int(library.deterministic_snapshot().get("mutation_count", -1)) != 0:
		failures.append("%s restoration failure must not increment successful counters" % expected_restoration)
	var backup_path := "%s.bak" % original_path
	if expected_restoration == "failed":
		if bool(result.get("previous_restored", true)) or not bool(result.get("backup_recoverable", false)):
			failures.append("total restoration failure must explicitly report a recoverable retained backup")
		if FileAccess.file_exists(original_path) or not FileAccess.file_exists(backup_path) or _read_text(backup_path) != original_text:
			failures.append("total restoration failure must retain the exact previous artifact only at its backup path")
		var visible: Array = library.list_profiles()
		if visible.size() != 1 or not _records_contain_name(visible, "Unrelated Healthy"):
			failures.append("total restoration failure must keep unrelated healthy profiles visible without exposing the backup")
		if not str(result.get("error", "")).to_lower().contains("recoverable"):
			failures.append("total restoration failure must explain recoverability in its public error")
	else:
		if not bool(result.get("previous_restored", false)) or _read_text(original_path) != original_text:
			failures.append("%s restoration must recover the exact previous destination" % expected_restoration)
		var restored_load: Dictionary = library.load_profile(original_id)
		if not bool(restored_load.get("ok", false)):
			failures.append("%s restoration must leave the previous profile loadable: %s" % [expected_restoration, restored_load.get("error", "")])
			return failures
		var restored_profile = restored_load.get("profile")
		if restored_profile == null:
			failures.append("successful load after %s restoration must return a detached profile" % expected_restoration)
			return failures
		if restored_profile.values() != source.values():
			failures.append("%s restoration must leave the previous profile readable through the library" % expected_restoration)
		if FileAccess.file_exists(backup_path):
			failures.append("%s restoration should remove the backup after confirming destination recovery" % expected_restoration)
		if expected_restoration == "copy" and ops.copy_count != 1:
			failures.append("restore rename failure must invoke the copy fallback exactly once")
	if _directory_has_suffix(directory, ".tmp"):
		failures.append("%s restoration case should clean the temporary artifact" % expected_restoration)
	return failures


func _test_deterministic_diagnostics(registry) -> Array:
	var failures: Array = []
	var library = LibraryScript.new(registry, DIAGNOSTIC_DIRECTORY)
	var source = _asymmetric_profile(registry)
	var healthy: Dictionary = library.save_new("Diagnostic Healthy", source)
	var healthy_id := str(healthy.get("record", {}).get("profile_id", ""))
	var corrupt_id := "c".repeat(32)
	var corrupt_path := DIAGNOSTIC_DIRECTORY.path_join("%s%s" % [corrupt_id, LibraryScript.FILE_SUFFIX])
	_write_text(corrupt_path, "{damaged")
	_write_text("%s.tmp" % corrupt_path, "{partial")
	_write_text("%s.bak" % corrupt_path, "recoverable but not a listed artifact")
	var snapshot_1: Dictionary = library.deterministic_snapshot()
	var snapshot_2: Dictionary = library.deterministic_snapshot()
	var snapshot_3: Dictionary = library.deterministic_snapshot()
	if snapshot_1 != snapshot_2 or snapshot_2 != snapshot_3:
		failures.append("deterministic profile-library snapshots must be identical on unchanged storage")
	var profiles: Array = snapshot_1.get("profiles", [])
	var diagnostics: Array = snapshot_1.get("diagnostics", [])
	if profiles.size() != 1 or str(profiles[0].get("profile_id", "")) != healthy_id:
		failures.append("deterministic scanning must retain the healthy profile and reject corrupt/stale artifacts")
	if diagnostics.size() != 1 or not _contains_fragment(diagnostics, "damaged") or library.diagnostics() != diagnostics:
		failures.append("corrupt-artifact diagnostics must be one stable current-scan record without accumulation")
	if _records_contain_name(profiles, "recoverable but not a listed artifact"):
		failures.append("stale temporary and backup files must never become visible profiles")
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
		var expected_count := 19 if mode == "live_2d" else 21 if mode == "live_3d" else 23
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


func _test_designer_failed_save(registry) -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var ops := InjectedPersistenceOps.new()
	ops.write_failures = {1: ERR_FILE_CANT_WRITE}
	var library = LibraryScript.new(registry, DESIGNER_FAILURE_DIRECTORY, ops)
	var designer = DesignerScript.new()
	designer.size = Vector2(420, 700)
	tree.root.add_child(designer)
	await tree.process_frame
	var opening = _asymmetric_profile(registry)
	if not designer.configure(registry, library) or not designer.open_with_profile(opening, "live_4d"):
		designer.queue_free()
		return ["Designer write-failure regression requires a configured detached profile"]
	designer.set_parameter_value("ghost.opacity", 0.45)
	var working_before: Dictionary = designer.working_profile().snapshot()
	var result: Dictionary = designer.save_working_as("Designer Cannot Persist")
	var snapshot: Dictionary = designer.deterministic_snapshot()
	if bool(result.get("ok", false)) or not str(snapshot.get("loaded_profile_id", "")).is_empty():
		failures.append("failed Designer Save As must not establish loaded/saved profile state")
	if designer.working_profile().snapshot() != working_before or snapshot.get("displayed_slot") != DesignerScript.SLOT_WORKING:
		failures.append("failed Designer Save As must preserve detached working B and its displayed state")
	var library_snapshot: Dictionary = snapshot.get("profile_library", {})
	if not library_snapshot.get("profiles", []).is_empty() or int(library_snapshot.get("write_count", -1)) != 0:
		failures.append("failed Designer Save As must create no phantom profile or successful write")
	designer.queue_free()
	await tree.process_frame
	return failures


func _test_designer_cleanup_warning(registry) -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var opening = _asymmetric_profile(registry)
	var initial_library = LibraryScript.new(registry, WARNING_DIRECTORY)
	var created: Dictionary = initial_library.save_new("Cleanup Warning Target", opening)
	if not bool(created.get("ok", false)):
		return ["cleanup-warning regression requires an existing managed profile"]
	var profile_id := str(created.get("record", {}).get("profile_id", ""))
	var artifact_path := WARNING_DIRECTORY.path_join("%s%s" % [profile_id, LibraryScript.FILE_SUFFIX])
	_write_text("%s.bak" % artifact_path, UNRELATED_BACKUP_SENTINEL)
	var ops := InjectedPersistenceOps.new()
	ops.remove_failures = {1: ERR_CANT_CREATE}
	var library = LibraryScript.new(registry, WARNING_DIRECTORY, ops)
	var designer = DesignerScript.new()
	designer.size = Vector2(420, 700)
	tree.root.add_child(designer)
	await tree.process_frame
	if not designer.configure(registry, library) or not designer.open_with_profile(opening, "live_4d"):
		designer.queue_free()
		return ["cleanup-warning regression requires a configured Designer"]
	var load_result: Dictionary = designer.load_saved_profile(profile_id)
	if not bool(load_result.get("ok", false)):
		designer.queue_free()
		return ["cleanup-warning regression requires the managed profile to load"]
	designer.set_parameter_value("ghost.opacity", 0.45)
	var result: Dictionary = designer.save_working()
	var snapshot: Dictionary = designer.deterministic_snapshot()
	if not bool(result.get("ok", false)) or str(result.get("warning", "")).is_empty():
		failures.append("successful profile replacement must propagate stale-backup cleanup warning metadata")
	if not str(snapshot.get("status_text", "")).contains("Warning: stale backup cleanup failed"):
		failures.append("Designer status must surface an actionable successful-write cleanup warning")
	if _read_text("%s.bak" % artifact_path) != UNRELATED_BACKUP_SENTINEL:
		failures.append("profile cleanup warning must leave the retained backup intact")
	if int(library.deterministic_snapshot().get("write_count", -1)) != 1:
		failures.append("profile replacement with a cleanup warning must increment its success counter exactly once")
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


func _records_contain_name(records: Array, display_name: String) -> bool:
	for record in records:
		if str(record.get("display_name", "")) == display_name:
			return true
	return false


func _directory_has_suffix(path: String, suffix: String) -> bool:
	var directory := DirAccess.open(ProjectSettings.globalize_path(path))
	if directory == null:
		return false
	directory.list_dir_begin()
	var entry := directory.get_next()
	while not entry.is_empty():
		if not directory.current_is_dir() and entry.ends_with(suffix):
			directory.list_dir_end()
			return true
		entry = directory.get_next()
	directory.list_dir_end()
	return false


func _read_json(path: String):
	var file := FileAccess.open(path, FileAccess.READ)
	return JSON.parse_string(file.get_as_text()) if file != null else null


func _read_text(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	return file.get_as_text() if file != null else ""


func _write_text(path: String, text: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(text)
		file.close()


func _cleanup_all() -> void:
	for directory in [
		TEST_DIRECTORY,
		DESIGNER_DIRECTORY,
		INTEGRATION_DIRECTORY,
		WRITE_FAILURE_DIRECTORY,
		DESIGNER_FAILURE_DIRECTORY,
		RESTORE_RENAME_DIRECTORY,
		RESTORE_COPY_DIRECTORY,
		RESTORE_TOTAL_FAILURE_DIRECTORY,
		DIAGNOSTIC_DIRECTORY,
		WARNING_DIRECTORY,
	]:
		_cleanup_directory(directory)
	for path in [
		EXPORT_PATH,
		"%s.tmp" % EXPORT_PATH,
		"%s.bak" % EXPORT_PATH,
		ABSENT_INSTALL_EXPORT_PATH,
		"%s.tmp" % ABSENT_INSTALL_EXPORT_PATH,
		"%s.bak" % ABSENT_INSTALL_EXPORT_PATH,
		INVALID_PATH,
	]:
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
