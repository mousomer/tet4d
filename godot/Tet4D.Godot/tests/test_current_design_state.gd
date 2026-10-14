extends RefCounted

const Designer = preload("res://scripts/ui/presentation_designer.gd")
const Registry = preload("res://scripts/ui/settings/settings_registry.gd")
const Profile = preload("res://scripts/presentation/presentation_profile.gd")
const Library = preload("res://scripts/presentation/presentation_profile_library.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var registry = Registry.new()
	registry.load_from_path(Registry.REGISTRY_PATH)
	var library = Library.new(registry, "user://current_design_%s" % OS.get_process_id())
	var designer = Designer.new()
	tree.root.add_child(designer)
	designer.configure(registry, library)
	var opening = Profile.canonical_defaults().with_overrides({"display.grid_mode": "border", "camera.invert_y": true})
	designer.open_with_profile(opening, "live_4d")
	var rectangles := {"GameArea": [20.0, 30.0, 500.0, 400.0], "PieceState": [600.0, 30.0, 320.0, 180.0]}
	designer.synchronize_panel_geometry(rectangles)
	designer.apply_built_in_style("tron_grid_flow")
	var current = designer.working_profile()
	if current.value("display.grid_mode") != "border" or not current.value("camera.invert_y") or current.design_state()["panel_rects"] != rectangles:
		failures.append("Apply Style must preserve independent grid, camera preference and geometry")
	var source: Dictionary = designer.save_working_as("Source")
	var source_id := str(source.get("record", {}).get("profile_id", ""))
	var baseline: Dictionary = designer.working_profile().snapshot()
	designer.set_comparison_snapshot("A")
	designer.set_parameter_value("display.grid_mode", "none")
	designer.synchronize_panel_geometry({"GameArea": [70.0, 80.0, 600.0, 500.0]})
	designer.set_parameter_value("ghost.opacity", 0.4)
	var copy: Dictionary = designer.save_working_as("Copy")
	var copy_id := str(copy.get("record", {}).get("profile_id", ""))
	var copy_snapshot: Dictionary = designer.working_profile().snapshot()
	if not bool(source.get("ok")) or not bool(copy.get("ok")) or source_id == copy_id:
		failures.append("Save As must create a new identity")
	if library.load_profile(source_id).get("profile").snapshot() != baseline or library.load_profile(copy_id).get("profile").snapshot() != copy_snapshot:
		failures.append("Save As must capture complete design without destroying or renaming its source")
	designer.load_saved_profile(source_id)
	if designer.working_profile().snapshot() != baseline:
		failures.append("Load must restore saved grid, geometry, appearance and provenance exactly")
	var records: Array = designer.built_in_style_records()
	designer.apply_built_in_style(str(records[0]["style_id"]))
	if designer.deterministic_snapshot()["loaded_profile_id"] != source_id:
		failures.append("Apply Style must retain the associated saved design")
	designer.set_parameter_value("display.grid_mode", "none")
	designer.revert_design()
	if designer.working_profile().snapshot() != baseline:
		failures.append("Revert restores the complete loaded/saved baseline after experimentation")
	designer.set_parameter_value("ghost.opacity", 0.3)
	designer.revert_style()
	if designer.working_profile().value("ghost.opacity") != baseline["design_state"]["base_style_values"]["ghost.opacity"] or designer.working_profile().design_state()["panel_rects"] != rectangles:
		failures.append("Internal Revert Style recovers base appearance and preserves geometry")
	designer.set_comparison_from_saved("B", copy_id)
	var editable_before: Dictionary = designer.working_profile().snapshot()
	var previews: Array = []
	designer.profile_preview_requested.connect(func(profile, _restore_geometry: bool) -> void: previews.append(profile.snapshot()))
	for index in range(10):
		designer.toggle_slots()
		var expected := baseline if designer.comparison.shown() == "A" else copy_snapshot
		if previews[-1] != expected or designer.working_profile().snapshot() != editable_before:
			failures.append("Repeated A/B toggles must preview frozen complete snapshots without mutating current")
	designer.adopt_comparison("B")
	if designer.working_profile().snapshot() != copy_snapshot or designer.comparison.shown() != "CURRENT":
		failures.append("Explicit Use B as Current must adopt the full snapshot")
	designer.adopt_comparison("A")
	if designer.working_profile().snapshot() != baseline:
		failures.append("Explicit Use A as Current must adopt the full snapshot")
	designer.set_parameter_value("display.grid_mode", "none")
	designer.save_working()
	if library.load_profile(source_id).get("profile").value("display.grid_mode") != "none" or designer.working_profile_dirty():
		failures.append("Save updates the associated complete design and baseline")
	var invalid := baseline.duplicate(true)
	invalid["design_state"]["panel_rects"] = {"GameArea": [0, 0, -10, 20]}
	if Profile.from_snapshot(registry, invalid).contract_conforms():
		failures.append("Saved design validation must reject malformed panel geometry")
	library.delete_profile(source_id)
	library.delete_profile(copy_id)
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://current_design_%s" % OS.get_process_id()))
	designer.queue_free()
	await tree.process_frame
	return failures
