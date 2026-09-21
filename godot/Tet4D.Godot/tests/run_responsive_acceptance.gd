extends SceneTree

# Stage 56G production-equivalent responsive acceptance.
#
# This runs against the REAL root window, not a SubViewport and not headless.
# Both of those falsify the thing under test: a SubViewport has no content
# scale, so a resized child Control merely looks responsive, and the headless
# DisplayServer reports window_get_size() == (0, 0) and ignores resize
# requests. The original Stage 56G evidence was produced in the first of those
# and reported three captures of one layout at three scales as proof of three
# profiles. Run this with a windowed DisplayServer.

const CockpitScript = preload("res://scripts/ui/live_cockpit.gd")

const MIN_GAME_WIDTH_SHARE := 0.55
const MIN_GAME_HEIGHT_SHARE := 0.30

const CASES := [
	{"points": Vector2i(1728, 1080), "profile": CockpitScript.PROFILE_WIDE},
	{"points": Vector2i(1440, 900), "profile": CockpitScript.PROFILE_STANDARD},
	{"points": Vector2i(1200, 800), "profile": CockpitScript.PROFILE_STANDARD},
	{"points": Vector2i(1000, 720), "profile": CockpitScript.PROFILE_NARROW},
	{"points": Vector2i(860, 640), "profile": CockpitScript.PROFILE_NARROW},
	{"points": Vector2i(720, 600), "profile": CockpitScript.PROFILE_SMALL},
]

var _failures: Array = []


func _initialize() -> void:
	_run()


func _run() -> void:
	await process_frame
	if DisplayServer.get_name() == "headless":
		push_error("Stage 56G responsive acceptance requires a windowed DisplayServer, got headless")
		quit(2)
		return
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	var scene_root := scene.instantiate() as Control
	root.add_child(scene_root)
	var hud = scene_root.get_node("ReplayHud")
	var app = scene_root.get_node("App")
	await process_frame
	await process_frame
	hud._apply_ui_scale("standard")
	hud._apply_hud_density("standard")
	hud._set_onboarding_visible(false)
	var display_scale := maxf(DisplayServer.screen_get_scale(), 0.01)
	var active_mode := ""
	for case in CASES:
		var points: Vector2i = case["points"]
		DisplayServer.window_set_size(Vector2i(
			int(round(float(points.x) * display_scale)),
			int(round(float(points.y) * display_scale))
		))
		for i in range(10):
			await process_frame
		# Resizing an already-active live session is a separate path from mode
		# entry. Keep it in the matrix so deferred container sorting cannot leave
		# controls clipped until the player changes mode.
		if not active_mode.is_empty():
			_assert_case(hud, case, "%s resize" % active_mode)
		for mode in ["2D", "3D", "4D"]:
			match mode:
				"2D": app._enter_live_2d_mode()
				"3D": app._enter_live_3d_mode()
				"4D": app._enter_live_4d_mode()
			for i in range(8):
				await process_frame
			_assert_case(hud, case, mode)
			active_mode = mode
	if _failures.is_empty():
		print("STAGE_56G_RESPONSIVE_ACCEPTANCE PASS (%d mode entries + %d active resizes)" % [CASES.size() * 3, CASES.size() - 1])
		quit(0)
		return
	for failure in _failures:
		push_error(failure)
	print("STAGE_56G_RESPONSIVE_ACCEPTANCE FAIL (%d findings)" % _failures.size())
	quit(1)


func _assert_case(hud, case: Dictionary, mode: String) -> void:
	var points: Vector2i = case["points"]
	var label := "%dx%d Live %s" % [points.x, points.y, mode]
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = snapshot.get("live_cockpit", {})
	var usable := root.get_visible_rect()
	var deck: Rect2 = snapshot.get("live_4d_deck", Rect2())
	var board: Rect2 = snapshot.get("game_area", Rect2())
	var game_viewport: Rect2 = snapshot.get("game_viewport", Rect2())
	var header: Rect2 = cockpit.get("header_rect", Rect2())
	var rows_rect: Rect2 = cockpit.get("deck_rows_rect", Rect2())
	var modules: Array[Rect2] = [
		snapshot.get("piece_module_rect", Rect2()),
		snapshot.get("view_module_rect", Rect2()),
		snapshot.get("piece_state_module_rect", Rect2()),
	]

	if str(cockpit.get("responsive_profile", "")) != str(case["profile"]):
		_fail("%s should select profile %s, got %s at apparent %s" % [
			label, case["profile"], cockpit.get("responsive_profile"), str(cockpit.get("apparent_size")),
		])
	if not _contains(usable, deck):
		_fail("%s must keep the control deck inside the window: %s in %s" % [label, deck, usable])
	if not _contains(usable, game_viewport):
		_fail("%s must keep the gameplay surface inside the window: %s in %s" % [label, game_viewport, usable])
	if not _contains(usable, header):
		_fail("%s must keep the live header inside the window: %s in %s" % [label, header, usable])
	if board.intersects(deck):
		_fail("%s must keep the game surface and control deck separate" % label)

	var flattened: Array = []
	for row in cockpit.get("deck_row_assignment", []):
		for module_name in row:
			flattened.append(str(module_name))
	if flattened != ["PieceControls", "ViewControls", "PieceState"]:
		_fail("%s must preserve PIECE / VIEW / PIECE STATE order across rows, got %s" % [label, str(flattened)])
	for index in range(modules.size()):
		if not _contains(rows_rect, modules[index]):
			_fail("%s module %d must stay inside the deck row host: %s in %s" % [label, index, modules[index], rows_rect])

	var width_share := game_viewport.size.x / maxf(usable.size.x, 1.0)
	var height_share := game_viewport.size.y / maxf(usable.size.y, 1.0)
	if width_share < MIN_GAME_WIDTH_SHARE:
		_fail("%s gameplay surface must keep >= %d%% of window width, got %d%%" % [label, int(MIN_GAME_WIDTH_SHARE * 100.0), int(width_share * 100.0)])
	if height_share < MIN_GAME_HEIGHT_SHARE:
		_fail("%s gameplay surface must keep >= %d%% of window height, got %d%%" % [label, int(MIN_GAME_HEIGHT_SHARE * 100.0), int(height_share * 100.0)])

	# Scrolling is the constrained-size escape hatch. It is legitimate wherever
	# the deck genuinely cannot fit - which includes part of the standard band,
	# because the profile bands are apparent-size bands and do not align with
	# the deck's measured 1467px one-row minimum. What must hold is that a wide
	# shell never needs it, and that scrolling is only ever a response to a
	# natural height the cap actually clipped.
	var scroll_required := bool(cockpit.get("deck_scroll_required", false))
	if scroll_required and str(case["profile"]) == CockpitScript.PROFILE_WIDE:
		_fail("%s must not need deck scrolling at a wide shell (natural %s, deck %s)" % [
			label, cockpit.get("deck_natural_height"), cockpit.get("deck_minimum_height"),
		])
	if scroll_required and float(cockpit.get("deck_natural_height", 0.0)) <= float(cockpit.get("deck_minimum_height", 0.0)) + 0.5:
		_fail("%s reported deck scrolling without a clipped natural height" % label)
	if not scroll_required and float(cockpit.get("deck_natural_height", 0.0)) > float(cockpit.get("deck_minimum_height", 0.0)) + 0.5:
		_fail("%s clipped the deck without enabling scrolling" % label)
	var preview_row: Rect2 = snapshot.get("piece_preview_row_rect", Rect2())
	if not bool(snapshot.get("piece_preview_row_visible", false)) or not _contains(modules[2], preview_row):
		_fail("%s must keep HOLD and NEXT grouped inside PIECE STATE" % label)
	for action_key in [
		"live_fit_view_button_rect",
		"live_reset_view_button_rect",
		"quick_settings_button_rect",
		"grid_toggle_button_rect",
		"designer_button_rect",
		"restart_game_button_rect",
		"new_random_game_button_rect",
		"change_setup_button_rect",
	]:
		var action_rect: Rect2 = snapshot.get(action_key, Rect2())
		if action_rect.size != Vector2.ZERO and not _contains(usable, action_rect):
			_fail("%s must keep %s reachable inside the window: %s in %s" % [label, action_key, action_rect, usable])


func _fail(message: String) -> void:
	_failures.append(message)


func _contains(outer: Rect2, inner: Rect2) -> bool:
	return (
		inner.size.x > 0.0
		and inner.size.y > 0.0
		and inner.position.x >= outer.position.x - 0.5
		and inner.position.y >= outer.position.y - 0.5
		and inner.end.x <= outer.end.x + 0.5
		and inner.end.y <= outer.end.y + 0.5
	)
