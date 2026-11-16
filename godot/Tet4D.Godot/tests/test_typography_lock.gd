extends RefCounted

# Phase 0 of docs/plans/typography_cleanup.md: locks the typography a player
# actually sees. Fingerprints are measured from the running shell, because the
# style applier overrides several coded sizes before they render. Changing the
# baseline is an owner-approved product decision, never a refactor side effect.
#
# Regenerate (owner-approved only):
#   TET4D_WRITE_TYPOGRAPHY_BASELINE=1 "$GODOT_BIN" --headless \
#     --path godot/Tet4D.Godot --script tests/run_typography_lock.gd

const BASELINE_PATH := "res://tests/fixtures/typography_baseline.json"
const WRITE_ENV := "TET4D_WRITE_TYPOGRAPHY_BASELINE"
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const SIZES := [Vector2i(1280, 800), Vector2i(1280, 720)]
const MAX_REPORTED_DIFFS := 40
var completed := false


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	var original_scale := tree.root.content_scale_size
	var original_minimum := tree.root.min_size
	var instance := (load("res://scenes/designer_bootstrap.tscn") as PackedScene).instantiate() as Control
	tree.root.add_child(instance)
	await _frames(tree, 10)
	var hud = instance.get_node("ReplayHud")
	var app = instance.get_node("App")
	app.set_process(false)
	# Pin every persisted input: earlier suite tests share this HOME.
	var settings_directory := DirAccess.create_temp("tet4d-typography-lock")
	hud._settings_store._storage_path = settings_directory.get_current_dir().path_join("settings.json")
	hud._set_onboarding_visible(false)
	hud._apply_ui_scale("standard")
	hud._apply_hud_density("standard")
	var setups := _default_setups()
	tree.root.min_size = Vector2i.ZERO
	var screens := {}
	for size in SIZES:
		tree.root.size = size
		tree.root.content_scale_size = size
		await _frames(tree, 10)
		var prefix := "%dx%d/" % [size.x, size.y]
		hud.show_screen("main_menu")
		await _frames(tree, 6)
		screens[prefix + "main_menu"] = _fingerprint(hud)
		for screen in ["settings", "controls", "about", "advanced"]:
			hud.show_screen(screen)
			await _frames(tree, 6)
			screens[prefix + screen] = _fingerprint(hud)
		for mode in ["live_2d", "live_3d", "live_4d"]:
			hud.open_game_setup(mode)
			await _frames(tree, 6)
			screens[prefix + "setup_" + mode] = _fingerprint(hud)
		for mode in ["live_2d", "live_3d", "live_4d"]:
			if setups.get(mode, {}).is_empty():
				failures.append("Typography lock: default %s setup is invalid" % mode)
				continue
			app._start_configured_live_game(setups[mode].duplicate(true))
			await _frames(tree, 10)
			await _settle_cockpit(tree, hud._live_cockpit)
			screens[prefix + mode] = _fingerprint(hud, instance)
		hud._set_onboarding_visible(true)
		await _frames(tree, 6)
		screens[prefix + "live_4d_onboarding"] = _fingerprint(hud)
		hud._set_onboarding_visible(false)
		await _frames(tree, 4)
		hud._open_presentation_designer()
		await _frames(tree, 10)
		screens[prefix + "live_4d_designer"] = _fingerprint(hud)
		hud._presentation_designer.revert_and_hide()
		await _frames(tree, 6)
		for dimension in [3, 4]:
			app._practice_action("dimension_%d" % dimension)
			await _frames(tree, 10)
			await _settle_cockpit(tree, hud._live_cockpit)
			screens[prefix + "explorer_%dd" % dimension] = _fingerprint(hud, instance)
		app._start_configured_live_game(setups.get("live_4d", {}).duplicate(true))
		await _frames(tree, 4)
		hud.show_screen("main_menu")
		await _frames(tree, 4)
	var actual := {
		"face": _face_snapshot(),
		"themes": _theme_snapshot(),
		"glyphs": _glyph_snapshot(),
		"screens": screens,
	}
	instance.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	tree.root.content_scale_size = original_scale
	tree.root.min_size = original_minimum
	if OS.get_environment(WRITE_ENV) == "1":
		var file := FileAccess.open(ProjectSettings.globalize_path(BASELINE_PATH), FileAccess.WRITE)
		file.store_string(JSON.stringify(actual, "\t", true) + "\n")
		file.close()
		# A write run never counts as a pass: review the diff, then rerun.
		failures.append("Typography lock: baseline written to %s; review it and rerun without %s" % [BASELINE_PATH, WRITE_ENV])
	else:
		failures.append_array(_compare(actual))
	completed = true
	return failures


func _default_setups() -> Dictionary:
	# Factory defaults, not the shared HOME's last-selected setup.
	var model = GameSetupModelScript.new()
	var result := {}
	for mode in ["live_2d", "live_3d", "live_4d"]:
		result[mode] = model.canonical_session_setup(mode).duplicate(true) if model.is_valid(mode) else {}
	return result


# One entry per visible text control: role, class, variation, rendered size,
# face, weight and the typography scope it inherits. Text content is excluded
# so copy edits do not trip the lock; counts catch added or removed controls.
func _fingerprint(hud: Control, scene: Node = null) -> Dictionary:
	var result := {}
	for node in hud.find_children("*", "Control", true, false):
		var control := node as Control
		if not control.is_visible_in_tree():
			continue
		var size_name := "font_size"
		var font_name := "font"
		var text := ""
		if control is RichTextLabel:
			size_name = "normal_font_size"
			font_name = "normal_font"
			text = (control as RichTextLabel).get_parsed_text()
		elif control is Label or control is Button or control is LineEdit:
			text = str(control.text)
		elif control is TabContainer:
			for tab in (control as TabContainer).get_tab_count():
				text += (control as TabContainer).get_tab_title(tab)
		elif control is ItemList:
			text = "items" if (control as ItemList).item_count > 0 else ""
		else:
			continue
		if text.strip_edges().is_empty():
			continue
		var font: Font = control.get_theme_font(font_name)
		_count(result, [
			control.get_class(), _role(control), _role(control.get_parent()), str(control.theme_type_variation),
			str(control.get_theme_font_size(size_name)), font.get_font_name() if font != null else "",
			str(font.get_font_weight()) if font != null else "", _scope(control),
		])
	if scene != null:
		for node in scene.find_children("*", "Label3D", true, false):
			var label := node as Label3D
			if not label.is_visible_in_tree() or label.text.strip_edges().is_empty():
				continue
			_count(result, [
				"Label3D", _role(label), _role(label.get_parent()), "", str(label.font_size),
				label.font.get_font_name() if label.font != null else "(fallback)", "outline=%d" % label.outline_size, "board",
			])
	return result


func _count(result: Dictionary, fields: Array) -> void:
	var key := "|".join(fields)
	result[key] = int(result.get(key, 0)) + 1


# Generated names collapse to their class and per-item suffixes (`__Play`) to
# their role, so the lock follows typography roles, not node identity.
func _role(node: Node) -> String:
	if node == null:
		return ""
	var name := str(node.name)
	if name.begins_with("@") or name.contains("@"):
		return node.get_class()
	return name.get_slice("__", 0)


func _scope(control: Control) -> String:
	var ancestor: Node = control
	while ancestor != null:
		if bool(ancestor.get_meta("readable_guidance", false)):
			return "readable"
		if bool(ancestor.get_meta("shell_chrome", false)):
			return "chrome"
		ancestor = ancestor.get_parent()
	return ""


func _face_snapshot() -> Dictionary:
	var font: Font = ThemeDB.fallback_font
	return {"name": font.get_font_name(), "style": font.get_font_style_name(), "weight": font.get_font_weight(), "fallbacks": font.fallbacks.size()}


func _theme_snapshot() -> Dictionary:
	var result := {}
	for mode in ["plain", "tron", "diagnostic"]:
		var theme: Theme = ReplayVisuals.build_theme(mode)
		result[mode] = {"default_font_size": theme.default_font_size, "default_font": theme.default_font.get_font_name() if theme.default_font != null else ""}
	return result


# Every non-ASCII character in shipped scripts and whether the embedded face
# draws it; a glyph that leaves or joins the OS-fallback set changes the lock.
func _glyph_snapshot() -> Dictionary:
	var used := {}
	for path in _script_paths("res://scripts"):
		var source := FileAccess.get_file_as_string(path)
		for index in source.length():
			var code := source.unicode_at(index)
			if code > 127:
				used[code] = true
	var codes: Array = used.keys()
	codes.sort()
	var font: Font = ThemeDB.fallback_font
	var covered: Array = []
	var missing: Array = []
	for code in codes:
		var label := "U+%04X %s" % [code, String.chr(code)]
		if font.has_char(code):
			covered.append(label)
		else:
			missing.append(label)
	return {"covered": covered, "system_fallback": missing}


func _script_paths(directory_path: String) -> Array:
	var result: Array = []
	var directory := DirAccess.open(directory_path)
	if directory == null:
		return result
	for file_name in directory.get_files():
		if file_name.ends_with(".gd"):
			result.append(directory_path.path_join(file_name))
	for child in directory.get_directories():
		result.append_array(_script_paths(directory_path.path_join(child)))
	result.sort()
	return result


func _compare(actual: Dictionary) -> Array:
	if not FileAccess.file_exists(BASELINE_PATH):
		return ["Typography lock: missing %s" % BASELINE_PATH]
	var expected = JSON.parse_string(FileAccess.get_file_as_string(BASELINE_PATH))
	if typeof(expected) != TYPE_DICTIONARY:
		return ["Typography lock: %s is not valid JSON" % BASELINE_PATH]
	# JSON numbers come back as floats; compare through one canonical encoding.
	actual = JSON.parse_string(JSON.stringify(actual))
	var diffs: Array = []
	for section in ["face", "themes", "glyphs"]:
		if JSON.stringify(actual.get(section), "", true) != JSON.stringify(expected.get(section), "", true):
			diffs.append("%s changed: expected %s, got %s" % [section, JSON.stringify(expected.get(section)), JSON.stringify(actual.get(section))])
	var actual_screens: Dictionary = actual.get("screens", {})
	var expected_screens: Dictionary = expected.get("screens", {})
	var screen_names: Array = actual_screens.keys()
	for name in expected_screens:
		if not screen_names.has(name):
			screen_names.append(name)
	screen_names.sort()
	for screen in screen_names:
		if not actual_screens.has(screen) or not expected_screens.has(screen):
			diffs.append("%s: screen %s" % [screen, "missing" if not actual_screens.has(screen) else "not in baseline"])
			continue
		var got: Dictionary = actual_screens[screen]
		var want: Dictionary = expected_screens[screen]
		var keys: Array = got.keys()
		for key in want:
			if not keys.has(key):
				keys.append(key)
		keys.sort()
		for key in keys:
			var got_count := int(got.get(key, 0))
			var want_count := int(want.get(key, 0))
			if got_count != want_count:
				diffs.append("%s: %s expected %d, got %d" % [screen, key, want_count, got_count])
	if diffs.is_empty():
		return []
	var failures: Array = ["Typography lock: %d differences from the owner-approved baseline (class|role|parent|variation|size|face|weight|scope)" % diffs.size()]
	for diff in diffs.slice(0, MAX_REPORTED_DIFFS):
		failures.append("Typography lock: " + diff)
	if diffs.size() > MAX_REPORTED_DIFFS:
		failures.append("Typography lock: ... %d more" % (diffs.size() - MAX_REPORTED_DIFFS))
	return failures


func _settle_cockpit(tree: SceneTree, cockpit, limit: int = 120) -> void:
	for _frame in range(limit):
		if cockpit.fit_settled():
			return
		await tree.process_frame


func _frames(tree: SceneTree, count: int) -> void:
	for _frame in range(count):
		await tree.process_frame
