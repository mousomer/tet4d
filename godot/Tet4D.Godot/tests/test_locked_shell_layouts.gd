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
	tree.root.size = original_size
	tree.root.content_scale_size = original_scale
	tree.root.min_size = original_minimum
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
