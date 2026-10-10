extends RefCounted

const FitProbe = preload("res://tests/test_render_region_fit_lifecycle.gd")

func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size if DisplayServer.get_name() == "headless" else DisplayServer.window_get_size()
	var probe = FitProbe.new()
	probe._resize_window(tree, Vector2i(1600, 960))
	var root := (load("res://scenes/designer_bootstrap.tscn") as PackedScene).instantiate()
	tree.root.add_child(root)
	await probe._layout_frames(tree)
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	var test_settings_path := "user://test_designer_geometry_%s.json" % OS.get_process_id()
	hud._settings_store._storage_path = test_settings_path
	for mode in ["live_3d", "live_4d"]:
		if mode == "live_3d": app._enter_live_3d_mode()
		else: app._enter_live_4d_mode()
		app._live_3d_paused = true
		app._live_4d_paused = true
		await probe._layout_frames(tree)
		var hash_before := probe._state_hash(app, mode)
		hud._open_presentation_designer()
		await probe._layout_frames(tree)
		var designer = hud._presentation_designer
		var records: Array = designer.built_in_style_records()
		designer.apply_built_in_style(str(records[1]["style_id"]))
		await probe._layout_frames(tree)
		designer.set_parameter_value("display.grid_mode", "full")
		var style_values: Dictionary = hud.presentation_profile().values()
		var style_id: String = designer.deterministic_snapshot()["applied_style_id"]
		for expected in ["border", "none", "full"]:
			hud._toggle_grid_visibility()
			await probe._layout_frames(tree)
			var values: Dictionary = hud.presentation_profile().values()
			if values["display.grid_mode"] != expected:
				failures.append("Grid must cycle FULL → BORDER → NONE → FULL")
			values.erase("display.grid_mode")
			var expected_style := style_values.duplicate(true)
			expected_style.erase("display.grid_mode")
			if values != expected_style or designer.deterministic_snapshot()["applied_style_id"] != style_id:
				failures.append("Grid cycling must preserve detached style and identity")
		var density_before: Dictionary = hud.presentation_profile().values()
		var next_density := "standard" if hud._hud_density == "detailed" else "detailed"
		# The persisted value may already match while detached runtime B differs.
		hud._settings_store.set_value("display.hud_density", next_density)
		hud._toggle_quick_settings()
		await probe._layout_frames(tree)
		var density_after: Dictionary = hud.presentation_profile().values()
		if density_after["display.hud_density"] != next_density:
			failures.append("Quick density must update detached runtime even when saved value already matches")
		density_before.erase("display.hud_density")
		density_after.erase("display.hud_density")
		if density_before != density_after or probe._state_hash(app, mode) != hash_before:
			failures.append("Density changes must preserve style/grid and native state")
		# Grid cycling over reference A must not silently select B's style.
		designer.capture_reference()
		designer.set_parameter_value("theme.name", "diagnostic")
		designer.show_slot("A")
		var a_values: Dictionary = hud.presentation_profile().values()
		hud._toggle_grid_visibility()
		var a_after: Dictionary = hud.presentation_profile().values()
		a_values.erase("display.grid_mode")
		a_after.erase("display.grid_mode")
		if a_values != a_after or designer.deterministic_snapshot()["displayed_slot"] != "A":
			failures.append("Grid cycling must preserve displayed reference A and its style")
		designer.show_slot("B")
		designer.set_parameter_value("display.grid_mode", "none")
		designer.apply_built_in_style(str(records[0]["style_id"]))
		if hud.presentation_profile().value("display.grid_mode") != "none":
			failures.append("Applying a style must preserve selected grid mode")
		await probe._layout_frames(tree)
		app._fit_view() # Establish framing after explicit style changes before geometry edits.
		var profile_before: Dictionary = hud.presentation_profile().snapshot()
		var orientation_before: Dictionary = app._camera_rig.presentation_snapshot()
		var basis_before: Dictionary = app._live_4d_basis.indicator_snapshot()
		var local_before: Dictionary = app._live_4d_local_orientation.snapshot()
		var panels: Dictionary = hud._live_cockpit.designer_panels()
		if panels.size() != 4:
			failures.append("Full Designer must expose four movable/resizable panels")
		for key in panels:
			var frame = panels[key]
			var choice := designer.find_child("DesignerPanelChoice", true, false) as OptionButton
			for index in range(choice.item_count):
				if choice.get_item_metadata(index) == key: choice.select(index)
			(designer.find_child("DesignerRaisePanel", true, false) as Button).pressed.emit()
			if frame.get_index() != frame.get_parent().get_child_count() - 1:
				failures.append("Panel selector must recover the selected panel above overlaps")
			if frame.move_handle.text.find("Move") < 0 or frame.resize_handle.text.find("Resize") < 0:
				failures.append("Panel geometry must have explicit handles")
			var start := Rect2(frame.position, frame.size)
			_drag_handle(frame.move_handle, Vector2(-20 if start.position.x > 20 else 20, 0))
			await probe._layout_frames(tree)
			if frame.position == start.position:
				failures.append("Move handle must change panel position")
			var region_before: Vector2 = hud.board_viewport_size()
			_drag_handle(frame.resize_handle, Vector2(25, 15))
			await probe._layout_frames(tree)
			if frame.size == start.size:
				failures.append("Resize handle must change panel dimensions")
			if key == "GameArea" and hud.board_viewport_size() == region_before:
				failures.append("Board resize must change actual inner render geometry")
			frame.set_geometry(Rect2(frame.position + Vector2(35, 12), frame.size))
			await probe._layout_frames(tree)
			probe._check_fit(failures, app, hud, "%s panel move %s" % [mode, key])
			frame.set_geometry(Rect2(frame.position, frame.size * 0.85))
			await probe._layout_frames(tree)
			probe._check_fit(failures, app, hud, "%s panel resize %s" % [mode, key])
			frame.set_geometry(Rect2(Vector2(-10000, 10000), Vector2.ZERO))
			await probe._layout_frames(tree)
			var bounds := Rect2(Vector2.ZERO, frame.get_parent().size)
			if not bounds.encloses(Rect2(frame.position, frame.size)) or frame.size.x < 300 or frame.size.y < 160:
				failures.append("Designer panel %s must stay accessible and usable: panel=%s bounds=%s" % [key, Rect2(frame.position, frame.size), bounds])
			if hud.presentation_profile().snapshot() != profile_before or probe._state_hash(app, mode) != hash_before:
				failures.append("Panel geometry must preserve profile/grid/style and native state")
		var orientation_after: Dictionary = app._camera_rig.presentation_snapshot()
		for field in ["target_yaw", "target_pitch", "target_roll"]:
			if orientation_after[field] != orientation_before[field]:
				failures.append("Panel geometry must preserve view orientation")
		if app._live_4d_basis.indicator_snapshot() != basis_before or app._live_4d_local_orientation.snapshot() != local_before:
			failures.append("Panel geometry must preserve exact basis and local orientation")
		designer.hide_preserving_preview()
		await probe._layout_frames(tree)
		if not hud._live_cockpit.designer_panels().is_empty():
			failures.append("Normal gameplay must not retain drag/resize handles")
		probe._check_fit(failures, app, hud, "%s Designer exit" % mode)
	root.queue_free()
	await tree.process_frame
	if DisplayServer.get_name() == "headless": tree.root.size = original_size
	else: DisplayServer.window_set_size(original_size)
	for suffix in ["", ".bak"]:
		var path: String = test_settings_path + str(suffix)
		if FileAccess.file_exists(path): DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	return failures


func _drag_handle(handle: Control, delta: Vector2) -> void:
	var start := handle.get_global_rect().get_center()
	var down := InputEventMouseButton.new()
	down.button_index = MOUSE_BUTTON_LEFT
	down.pressed = true
	down.global_position = start
	handle.gui_input.emit(down)
	var motion := InputEventMouseMotion.new()
	motion.global_position = start + delta
	motion.button_mask = MOUSE_BUTTON_MASK_LEFT
	handle.gui_input.emit(motion)
	var up := InputEventMouseButton.new()
	up.button_index = MOUSE_BUTTON_LEFT
	up.global_position = motion.global_position
	handle.gui_input.emit(up)
