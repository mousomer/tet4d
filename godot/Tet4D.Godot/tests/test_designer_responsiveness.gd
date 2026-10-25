extends RefCounted

const DesignerScript = preload("res://scripts/ui/presentation_designer.gd")
const LaboratoryScript = preload("res://scripts/ui/design_laboratory_panel.gd")
const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const ProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const Visuals = preload("res://scripts/ui/replay_visuals.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var profile = ProfileScript.from_snapshot(registry, {"schema_version": ProfileScript.SCHEMA_VERSION, "values": registry.default_values()})
	var designer = DesignerScript.new()
	designer.theme = Visuals.build_theme("plain")
	tree.root.add_child(designer)
	designer.configure(registry)
	for context in ["live_2d", "live_3d", "live_4d"]:
		designer.open_with_profile(profile, context)
		for viewport in [Vector2(1512, 982), Vector2(1440, 900), Vector2(1280, 720), Vector2(1024, 640), Vector2(800, 500)]:
			var envelope := Rect2(Vector2(16, 16), Vector2(minf(400.0, viewport.x - 32.0), viewport.y - 32.0))
			designer.position = envelope.position
			designer.size = envelope.size
			await _settle(tree)
			if not envelope.grow(1.0).encloses(designer.get_global_rect()):
				failures.append("%s Designer must honor its viewport envelope %s, got %s" % [context, envelope, designer.get_global_rect()])
			var scroll: ScrollContainer = designer._full_scroll
			if designer._full_root.size.x > scroll.size.x + 1.0:
				failures.append("%s Designer parameters must reflow within the scroll width" % context)
			var hide: Button
			for button in designer.find_children("*", "Button", true, false):
				if button.text == "Hide" and button.is_visible_in_tree():
					hide = button
					break
			if hide == null or not envelope.grow(1.0).encloses(hide.get_global_rect()):
				failures.append("%s Designer Hide action must remain pinned inside the viewport" % context)
			for control in designer._full_root.find_children("*", "Control", true, false):
				if control.is_visible_in_tree() and (control is Button or control is Range or control is LineEdit):
					var rect: Rect2 = control.get_global_rect()
					if rect.position.x < scroll.global_position.x - 1.0 or rect.end.x > scroll.get_global_rect().end.x + 1.0:
						failures.append("%s Designer control %s escapes horizontally at %s" % [context, control.name, viewport])
						break
			if designer._full_root.get_combined_minimum_size().y > scroll.size.y + 1.0 and not scroll.get_v_scroll_bar().visible:
				failures.append("%s Designer must scroll when measured readable parameters exceed its viewport" % context)
			scroll.scroll_vertical = int(scroll.get_v_scroll_bar().max_value)
			await _settle(tree)
			if hide != null and not envelope.grow(1.0).encloses(hide.get_global_rect()):
				failures.append("%s Designer must keep Hide accessible after scrolling to the final parameter" % context)
			scroll.scroll_vertical = 0
		designer.set_library_expanded(true)
		designer.set_built_in_styles_expanded(true)
		await _settle(tree)
		if designer._full_root.size.x > designer._full_scroll.size.x + 1.0:
			failures.append("Expanded Designer libraries must reflow without widening the panel")
		designer.set_library_expanded(false)
		designer.set_built_in_styles_expanded(false)
	designer.queue_free()
	await tree.process_frame
	var laboratory = LaboratoryScript.new()
	laboratory.theme = Visuals.build_theme("plain")
	tree.root.add_child(laboratory)
	var callback := func(_value = null): return {}
	laboratory.configure(registry, {
		"load_scenario": callback, "apply_profile": callback,
		"current_fingerprint": callback, "capture_image": callback,
		"build_identity": callback, "edit_candidate": callback,
	})
	laboratory.open()
	await _settle(tree)
	for extent in [Vector2(460, 950), Vector2(460, 868), Vector2(460, 688), Vector2(400, 608), Vector2(400, 468)]:
		laboratory.size = extent
		await _settle(tree)
		var envelope := Rect2(Vector2.ZERO, extent)
		if not envelope.grow(1.0).encloses(laboratory.get_global_rect()):
			failures.append("Laboratory must honor its viewport envelope %s, got %s" % [envelope, laboratory.get_global_rect()])
		var scroll := laboratory.find_child("LaboratoryContentScroll", true, false) as ScrollContainer
		if scroll != null and (scroll.get_child(0) as Control).size.x > scroll.size.x + 1.0:
			failures.append("Laboratory form must reflow within its scroll width at %s" % extent)
	laboratory.queue_free()
	await tree.process_frame
	return failures


func _settle(tree: SceneTree) -> void:
	for _frame in range(12):
		await tree.process_frame
