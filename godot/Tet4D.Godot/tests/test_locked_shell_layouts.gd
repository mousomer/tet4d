extends RefCounted

# Owner-accepted layouts (2026-10-25), locked against drift:
# - Main Menu: one list of options in the original order and grouping, with
#   Play 2D/3D/4D always selectable; it keeps its font sizes and scales as a
#   whole to fit the window rather than reflowing into columns.
# - Live 2D/3D: the side rail beside a height-limited board shows every helper
#   without a scrollbar at the standard windows, with whole NEXT/HOLD names and,
#   in 3D, the MOVE compass beside its drop keys.
# - Live 4D: the split shows every helper without a scrollbar at the standard
#   windows (the side column shrinks to fit), and in a small window the deck
#   below the board leads with NEXT/HOLD and keeps that row on screen.
# A change to any of these is a product decision, not a layout fix.

const DirectionProbe = preload("res://tests/support/legend_direction_probe.gd")
const Tokens = preload("res://scripts/ui/style/shell_design_tokens.gd")
const SIZES := [Vector2i(1440, 900), Vector2i(1280, 720)]
const SMALL_4D := Vector2i(700, 480)
const MENU_ORDER := [
	"CommandCard__Play",
	"CommandCard__Play_2D",
	"CommandCard__Play_3D",
	"CommandCard__Play_4D",
	"CommandCard__Change_Setup",
	"CommandCard__Design_Laboratory",
	"CommandCard__Explorer",
	"CommandCard__How_to_Play",
	"CommandCard__About_Tet4D",
	"CommandCard__Settings",
	"CommandCard__Advanced___Diagnostics",
	"CommandCard__Quit",
]


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
	var settings_directory := DirAccess.create_temp("tet4d-locked-layouts")
	hud._settings_store._storage_path = settings_directory.get_current_dir().path_join("settings.json")
	hud._set_onboarding_visible(false)
	hud._apply_ui_scale("standard")
	tree.root.min_size = Vector2i.ZERO
	for size in SIZES:
		tree.root.size = size
		tree.root.content_scale_size = size
		await _frames(tree, 10)
		failures.append_array(await _check_menu(tree, hud, size))
		for mode in ["live_2d", "live_3d"]:
			app._start_configured_live_game(hud.configured_live_setup(mode))
			await _frames(tree, 10)
			await _settle_cockpit(tree, hud._live_cockpit)
			failures.append_array(_check_rail(hud, app, mode, size))
		app._start_configured_live_game(hud.configured_live_setup("live_4d"))
		await _frames(tree, 10)
		await _settle_cockpit(tree, hud._live_cockpit)
		failures.append_array(_check_4d_split(hud, size))
		hud.show_screen("main_menu")
	# A small window: the 4D deck moves below the board and must lead with
	# NEXT/HOLD on screen rather than collapse to a strip.
	tree.root.size = SMALL_4D
	tree.root.content_scale_size = SMALL_4D
	app._start_configured_live_game(hud.configured_live_setup("live_4d"))
	await _frames(tree, 10)
	await _settle_cockpit(tree, hud._live_cockpit)
	failures.append_array(_check_4d_small(hud))
	instance.queue_free()
	await tree.process_frame
	failures.append_array(await _check_p3_game(tree))
	tree.root.size = original_size
	tree.root.content_scale_size = original_scale
	tree.root.min_size = original_minimum
	return failures


# P3 game lock. The Designer checks above preserve its established authoring
# layout. The game shares the board, footer and controls across both choices.
func _check_p3_game(tree: SceneTree) -> Array:
	var failures: Array = []
	var instance := (load("res://scenes/game_bootstrap.tscn") as PackedScene).instantiate()
	var app = instance.get_node("App")
	var hud = instance.get_node("ReplayHud")
	var settings_directory := DirAccess.create_temp("tet4d-p3-layouts")
	app._launch_view_path = settings_directory.get_current_dir().path_join("launch.cfg")
	tree.root.add_child(instance)
	await _frames(tree, 10)
	app.set_process(false)
	hud._settings_store._storage_path = settings_directory.get_current_dir().path_join("settings.json")
	hud._set_onboarding_visible(false)
	hud._apply_ui_scale("standard")
	for size in SIZES + [SMALL_4D]:
		tree.root.size = size
		tree.root.content_scale_size = size
		for layout in ["concept_a", "concept_b"]:
			hud._settings_screen_panel._on_control_value_changed("display.cockpit_layout", layout)
			for mode in ["live_2d", "live_3d", "live_4d"]:
				app._start_configured_live_game(hud.configured_live_setup(mode))
				await _frames(tree, 10)
				await _settle_cockpit(tree, hud._live_cockpit)
				var name := "%s %s at %s" % [layout, mode, size]
				var board: Rect2 = hud._game_area.get_global_rect()
				var header: Rect2 = hud._cockpit_nav.get_global_rect()
				var footer: Rect2 = hud._cockpit_footer.get_global_rect()
				var legend: Rect2 = hud._live_cockpit.control_deck.get_global_rect()
				var viewport: Rect2 = hud.get_viewport_rect().grow(1.0)
				if not (viewport.encloses(board) and viewport.encloses(header) and viewport.encloses(footer) and viewport.encloses(legend)):
					failures.append("%s must keep the board, navigation, controls and status inside the window" % name)
				if header.end.y > board.position.y + 1.0 or footer.position.y < board.end.y - 1.0:
					failures.append("%s must keep navigation above the board and status below it" % name)
				var header_stats: bool = layout == "concept_b"
				if (hud._cockpit_stats.get_parent() == hud._live_cockpit.header_slot) != header_stats:
					failures.append("%s must keep stats in its chosen location" % name)
				if hud._cockpit_mode_title.is_visible_in_tree() != header_stats or (header_stats and not hud._cockpit_mode_title.text.begins_with("%sD" % mode[5])):
					failures.append("%s must title header stats with the mode, and only there" % name)
				if hud._cockpit_stat_dividers.size() != 2 or not hud._cockpit_stat_dividers.all(func(divider: ColorRect) -> bool: return divider.is_visible_in_tree() and hud._cockpit_stats.is_ancestor_of(divider)):
					failures.append("%s must divide the three stats" % name)
				if not hud._hold_piece_panel._thumbnail._show_empty_slot:
					failures.append("%s must keep the empty HOLD slot visible" % name)
				if header_stats:
					if legend.position.x < board.end.x - 1.0:
						failures.append("%s must keep controls beside the board" % name)
				elif legend.position.y < board.end.y - 1.0:
					failures.append("%s must keep controls below the board" % name)
				if size == SIZES[0]:
					# Outline floors at the reference window, excluding camera-fit padding.
					var minimums := {"live_2d": 0.65, "live_3d": 0.61, "live_4d": 0.42} if header_stats else {"live_2d": 0.70, "live_3d": 0.66, "live_4d": 0.44}
					var outline_height := DirectionProbe.projected_content_height(app, false)
					if outline_height < float(size.y) * float(minimums[mode]):
						failures.append("%s projected well outline is too short: %.1f px" % [name, outline_height])
					var deck: ScrollContainer = hud._live_cockpit.deck_scroll
					if deck.get_v_scroll_bar().visible or deck.get_h_scroll_bar().visible or hud._live_cockpit.deck_fit.fit_scale < 0.99:
						failures.append("%s must show the complete legend at its standard scale" % name)
					if header_stats and mode != "live_2d":
						for caption: Label in [hud._next_piece_panel._status_label, hud._hold_piece_panel._status_label]:
							var font := caption.get_theme_font("font")
							var required_width := font.get_string_size(caption.text, HORIZONTAL_ALIGNMENT_LEFT, -1, caption.get_theme_font_size("font_size")).x
							if caption.size.x + 1.0 < required_width:
								failures.append("%s clips the preview caption %s" % [name, caption.text])
					if not header_stats and mode in ["live_2d", "live_3d"]:
						var controls: HFlowContainer = hud._piece_control_strip._groups_box
						if controls.get_line_count() != 1:
							failures.append("%s must keep the controls on one row" % name)
				var preview_columns := 2 if header_stats and mode != "live_2d" else 1
				if hud._piece_preview_row.columns != preview_columns or not hud._piece_preview_row.is_visible_in_tree():
					failures.append("%s must keep NEXT and HOLD reachable in the preview row" % name)
				var controls: Control = hud._piece_control_strip
				var compass := controls.find_child("LegendCompass", true, false)
				var expected_planes := 6 if mode == "live_4d" else 3
				if header_stats and mode != "live_2d":
					if compass == null or controls.find_children("ControlSectionTitle", "Label", true, false).size() != 3:
						failures.append("%s must show the MOVE compass and all three group headings" % name)
					if controls.find_children("LegendPlaneGlyph__*", "Control", true, false).size() != expected_planes or controls.find_children("LegendTag", "Label", true, false).size() != expected_planes:
						failures.append("%s must show a glyph and plane label for every rotation pair" % name)
				elif not header_stats:
					if compass != null:
						failures.append("%s must retain the compact footer legend" % name)
					if mode != "live_2d":
						app._publish_legend_screen_directions()
						var arrow_count := 6 if mode == "live_4d" else 4
						var arrows := controls.find_children("LegendInlineArrow__*", "Control", true, false)
						if arrows.size() != arrow_count:
							failures.append("%s must show an arrow beside each spatial movement key" % name)
						for arrow in arrows:
							if arrow.directions().get(arrow.movement_intent, Vector2.ZERO) == Vector2.ZERO:
								failures.append("%s is missing a direction for %s" % [name, arrow.movement_intent])
						var rotation_glyphs := controls.find_children("LegendPlaneGlyph__*", "Control", true, false)
						if rotation_glyphs.size() != expected_planes:
							failures.append("%s must provide one footer glyph per rotation pair" % name)
						var rotation_groups := {}
						for glyph in rotation_glyphs:
							var group := glyph.get_parent()
							var key_group := group.get_node("LegendKeys")
							var plane_label := group.get_node("LegendOperation") as Label
							if group.get_parent() != hud._piece_control_strip._groups_box or rotation_groups.has(group) or key_group.get_child_count() != 2 or plane_label.text != glyph.plane_name():
								failures.append("%s must keep each rotation pair, glyph and plane label in one group" % name)
							rotation_groups[group] = true
	var reloaded = hud._settings_store.get_script().new(hud._settings_registry, hud._settings_store._storage_path)
	reloaded.load_settings()
	if reloaded.value("display.cockpit_layout") != "concept_b":
		failures.append("the selected layout must survive reloading Display settings")
	instance.queue_free()
	await tree.process_frame
	return failures


func _check_menu(tree: SceneTree, hud, size: Vector2i) -> Array:
	var failures: Array = []
	hud.show_screen("main_menu")
	await _frames(tree, 10)
	var label := "%s main menu" % size
	if hud._main_menu_screen.find_child("MainMenuColumns", true, false) != null:
		failures.append("%s must stay one list, not columns" % label)
	var cards: Array = []
	var parents := {}
	for node in hud._main_menu_screen.find_children("CommandCard__*", "Button", true, false):
		if (node as Control).visible:
			cards.append(str(node.name))
			parents[node.get_parent()] = true
	var expected := MENU_ORDER.filter(func(name: String) -> bool: return cards.has(name))
	if cards != expected or not cards.has("CommandCard__Play_2D") or cards.size() < MENU_ORDER.size() - 1:
		failures.append("%s must list %s, got %s" % [label, MENU_ORDER, cards])
	if parents.size() != 1:
		failures.append("%s commands must share one list container, found %d" % [label, parents.size()])
	var play := hud._main_menu_screen.find_child("CommandCard__Play", true, false) as Control
	if play != null and play.get_theme_font_size("font_size") < 24:
		failures.append("%s must keep its 24px command text and scale as a whole" % label)
	var scale: float = hud._main_menu_fit.fit_scale
	if scale < Tokens.MENU_FIT_SCALE_FLOOR - 0.001 or scale > 1.0:
		failures.append("%s fit scale %s outside [floor, 1]" % [label, scale])
	if hud._main_menu_scroll.get_v_scroll_bar().visible:
		failures.append("%s must fit without a scrollbar" % label)
	return failures


func _check_rail(hud, app, mode: String, size: Vector2i) -> Array:
	var failures: Array = []
	var label := "%s %s rail" % [size, mode]
	var cockpit = hud._live_cockpit
	if str(cockpit.deck_placement()) != "side":
		failures.append("%s must stay a side rail" % label)
		return failures
	if cockpit.deck_scroll.get_v_scroll_bar().visible:
		failures.append("%s must show every helper without a scrollbar" % label)
	if not app._camera_rig.fitted_height_limited():
		failures.append("%s must not narrow the height-limited board" % label)
	for node in cockpit.piece_state.find_children("*", "Label", true, false):
		var text_label := node as Label
		if not text_label.is_visible_in_tree() or text_label.text_overrun_behavior == TextServer.OVERRUN_NO_TRIMMING:
			continue
		var width := text_label.get_theme_font("font").get_string_size(text_label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_label.get_theme_font_size("font_size")).x
		if width > text_label.size.x + 1.0:
			failures.append("%s must show '%s' whole" % [label, text_label.text])
	if mode == "live_3d":
		var move := cockpit.piece_controls.find_child("LegendMoveBody", true, false) as Container
		var tops := {}
		if move != null:
			for child in move.get_children():
				if child is Control and (child as Control).visible:
					tops[int((child as Control).position.y)] = true
		if move == null or tops.size() != 1:
			failures.append("%s must keep the MOVE compass beside its drop keys" % label)
	return failures


func _check_4d_split(hud, size: Vector2i) -> Array:
	var failures: Array = []
	var label := "%s live_4d" % size
	var cockpit = hud._live_cockpit
	if str(cockpit.deck_placement()) != "split":
		failures.append("%s must keep the split (legend deck, side column)" % label)
		return failures
	if cockpit.deck_scroll.get_v_scroll_bar().visible:
		failures.append("%s must show the whole legend deck without a scrollbar" % label)
	if cockpit.side_scroll.get_v_scroll_bar().visible:
		failures.append("%s must fit NEXT/HOLD and VIEW in the side column without a scrollbar" % label)
	return failures


func _check_4d_small(hud) -> Array:
	var failures: Array = []
	var label := "%s live_4d" % SMALL_4D
	var cockpit = hud._live_cockpit
	var snapshot: Dictionary = cockpit.deterministic_snapshot()
	var rows: Array = snapshot.get("deck_row_assignment", [])
	if str(cockpit.deck_placement()) != "below" or rows.is_empty() or str((rows[0] as Array)[0]) != "PieceState":
		failures.append("%s deck must sit below the board and lead with NEXT/HOLD, got %s %s" % [label, cockpit.deck_placement(), rows])
	var visible: Rect2 = cockpit.deck_scroll.get_global_rect()
	var next_title := cockpit.piece_state.find_child("NextPieceTitle", true, false) as Control
	if next_title == null or not visible.grow(1.0).encloses(next_title.get_global_rect()):
		failures.append("%s must keep NEXT on screen in the deck" % label)
	if not hud.get_viewport_rect().grow(1.0).encloses(cockpit.control_deck.get_global_rect()):
		failures.append("%s deck must stay inside the window" % label)
	return failures


func _settle_cockpit(tree: SceneTree, cockpit, limit: int = 120) -> void:
	for _frame in range(limit):
		if cockpit.fit_settled():
			return
		await tree.process_frame


func _frames(tree: SceneTree, count: int) -> void:
	for _frame in range(count):
		await tree.process_frame
