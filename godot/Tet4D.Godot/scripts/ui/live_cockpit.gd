extends VBoxContainer

class_name LiveCockpit

const DesignerPanelSession = preload("res://scripts/ui/designer_panel_session.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const ShellDesignTokensScript = preload("res://scripts/ui/style/shell_design_tokens.gd")
const ResponsivePanelPolicy = preload("res://scripts/ui/responsive_panel_policy.gd")
const LayoutCoordinator = preload("res://scripts/ui/cockpit_layout_coordinator.gd")
const LayoutPolicy = preload("res://scripts/ui/cockpit_layout_policy.gd")
const HelperFitState = preload("res://scripts/ui/helper_fit_state.gd")
const FitScaleContainerScript = preload("res://scripts/ui/fit_scale_container.gd")

const PROFILE_WIDE := "wide"
const PROFILE_STANDARD := "standard"
const PROFILE_NARROW := "narrow"
const PROFILE_SMALL := "small"

# Breakpoints are apparent widths: OS window client pixels divided by the
# display scale and by the requested UI scale. They are not logical viewport
# coordinates, which stay pinned to the design resolution under canvas_items
# stretch and therefore cannot express how large the shell actually looks.
const WIDE_MIN_WIDTH := LayoutPolicy.WIDE_MIN_WIDTH
const STANDARD_MIN_WIDTH := LayoutPolicy.STANDARD_MIN_WIDTH
const NARROW_MIN_WIDTH := LayoutPolicy.NARROW_MIN_WIDTH

const MAX_DECK_ROWS := 3
# Reflow buys width at a height cost: every extra control row adds height while
# the board already holds a large minimum, so a narrow window would otherwise
# have to be TALLER to stay contained. Capping the deck and scrolling the
# overflow keeps every control reachable at any size; the cost is that not all
# of them are visible at once, which is the accepted tradeoff for small shells.
const MAX_DECK_HEIGHT_SHARE := 0.20
# The camera fits the board to any rect, so the board has no aspect-derived
# demand to measure. Below it the deck may instead take the stage height above
# this reserved board share before it scrolls; MAX_DECK_HEIGHT_SHARE stays the
# floor it never drops beneath.
const BOARD_RESERVE_STAGE_SHARE := 0.5
# Smallest uniform scale a helper panel shrinks to before it scrolls. It keeps
# the 22-unit control hints at about 13 units, the smallest helper text that
# stays readable at the 1280-unit design canvas.
const FIT_SCALE_FLOOR := HelperFitState.SCALE_FLOOR
# Outer shell margin above and below the cockpit.
const DECK_VERTICAL_INSET := 24.0
# Product contract for the Live 4D legend deck: at the supported 1280x720
# opening window (720 logical px tall) and above, it shows the whole measured
# legend. Below it the deck gives up exactly the missing height, so the board
# keeps its reference-window allocation, until it reaches the standard compact
# share; from there both shrink together and the legend scales down to fit, scrolling
# only at FIT_SCALE_FLOOR. Header height
# beyond the plain live top bar (an open guide) counts as missing height too.
const LEGEND_FULL_FIT_HEIGHT := 720.0
# Outer shell margin on each side of the cockpit.
const DECK_HORIZONTAL_INSET := 24.0

# A tall board (Live 2D is 1:2) wastes most of a wide window, while a deck
# under it takes the one dimension the board is short of. Beside the board the
# deck spends width instead, the way the Python client's side panel did.
const PLACEMENT_BELOW := "below"
const PLACEMENT_SIDE := "side"
# Live 4D: the piece legend is wide and short, so it stays in the deck; NEXT/
# HOLD and VIEW move to a side column. Together they did not fit one deck row
# at 1440 px. A bounded side column and scrollable bottom deck preserve
# access to every control while prioritizing the gameplay viewport.
const PLACEMENT_SPLIT := "split"
# Stage 58B bounds cockpit chrome independently of the board. The existing
# rail reflows/scrolls its controls instead of consuming a third of gameplay.
const SIDE_RAIL_WIDTH_SHARE := 0.24
const SIDE_RAIL_NARROW_WIDTH_SHARE := 0.24
const SIDE_RAIL_MIN_WIDTH := 260.0
const SIDE_RAIL_MAX_WIDTH := 320.0
const SIDE_RAIL_GAP := 10
# The split column holds only NEXT/HOLD and stacked VIEW, so it stays narrower.
const SPLIT_COLUMN_WIDTH_SHARE := 0.19
# NEXT/HOLD reflow inside the column; their minimum must not resize gameplay.
const SPLIT_COLUMN_MIN_WIDTH := 240.0
const SPLIT_COLUMN_MAX_WIDTH := 280.0

var header_slot: VBoxContainer
var board_stage: HBoxContainer
# Board plus, in the 4D split, the legend deck under it; the side column beside
# this spans the whole stage height instead of only the board's.
var board_column: VBoxContainer
var primary_board_surface: VBoxContainer
var side_column: VBoxContainer
# Between each scroll and its content: helpers shrink to fit before scrolling.
var side_fit
var deck_fit
var side_scroll: ScrollContainer
var control_deck: VBoxContainer
var deck_scroll: ScrollContainer
var deck_row_host: VBoxContainer
var deck_rows: Array[HBoxContainer] = []
var piece_controls: VBoxContainer
var view_controls: VBoxContainer
var piece_state: VBoxContainer
var _layout_size := Vector2.ZERO
var _apparent_size := Vector2.ZERO
var _density := "standard"
var _responsive_profile := PROFILE_STANDARD
var _row_assignment: Array = []
var _layout_coordinator = LayoutCoordinator.new()
var _last_packing_width := -1.0
var _last_module_minimums := Vector3.ZERO
var _last_module_heights := Vector3.ZERO
var _last_header_height := -1.0
var _natural_deck_height := 0.0
var _scroll_required := false
var _side_column_natural_height := 0.0
var _side_column_scroll_required := false
var _last_stage_height := -1.0
var _last_host_widths := Vector2(-1.0, -1.0)
var _split_full_height := false
var _board_aspect := 0.0
# The height the deck below the board may take before it scrolls.
var _deck_room := 0.0
var _board_viewport: Control
# Modules whose gaps are halved because their relaxed height overflowed, and
# per fit group ("deck", "side") whether it is compact and its relaxed height.
var _compacted: Array[String] = []
var _fit_states: Dictionary = {}
var _placement := PLACEMENT_BELOW
var _requested_placement := PLACEMENT_BELOW

signal designer_geometry_changed(rects: Dictionary)

var _designer_session = DesignerPanelSession.new()


func set_designer_layout_enabled(enabled: bool, board: Control) -> void:
	if enabled == _designer_session.active():
		return
	_layout_coordinator.invalidate()
	if enabled:
		_reset_fit()
		_designer_session.open(self, board_stage, control_deck, [
			["Board", board, false], ["Piece controls", piece_controls, true],
			["View controls", view_controls, true], ["NEXT / HOLD", piece_state, true]])
	else:
		_designer_session.close()
		_apply_responsive_policy()


func designer_panels() -> Dictionary:
	return _designer_session.panels()


func designer_session_revision() -> int:
	return _designer_session.revision()


func designer_surface_rect() -> Rect2:
	return _designer_session.surface_rect()


func designer_geometry_snapshot() -> Dictionary:
	return _designer_session.geometry_snapshot()


func restore_designer_geometry(rects: Dictionary) -> void:
	_designer_session.restore_geometry(rects)


func raise_designer_panel(panel_name: String) -> void:
	_designer_session.raise_panel(panel_name)


func constrain_designer_panels() -> void:
	_designer_session.constrain()


func _init() -> void:
	add_child(_designer_session)
	_designer_session.geometry_changed.connect(func(rects: Dictionary) -> void: designer_geometry_changed.emit(rects))
	_layout_coordinator.configure(_apply_layout, _on_deck_metrics_changed)
	add_child(_layout_coordinator)
	name = "LiveCockpit"
	add_theme_constant_override("separation", 4)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	header_slot = _slot("Header")
	header_slot.set_meta("shell_chrome", true)
	add_child(header_slot)
	board_stage = HBoxContainer.new()
	board_stage.name = "BoardStage"
	board_stage.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	board_stage.size_flags_vertical = Control.SIZE_EXPAND_FILL
	board_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	board_stage.add_theme_constant_override("separation", SIDE_RAIL_GAP)
	add_child(board_stage)
	board_column = VBoxContainer.new()
	board_column.name = "BoardColumn"
	board_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	board_column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	board_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	board_column.add_theme_constant_override("separation", 4)
	board_stage.add_child(board_column)
	primary_board_surface = _slot("PrimaryBoardSurface")
	primary_board_surface.size_flags_vertical = Control.SIZE_EXPAND_FILL
	board_column.add_child(primary_board_surface)
	# Scrolls as a whole so a short window never pushes the deck off-screen;
	# NEXT/HOLD sit at its top and stay visible.
	side_scroll = ScrollContainer.new()
	side_scroll.name = "SideColumnScroll"
	side_scroll.visible = false
	side_scroll.size_flags_horizontal = Control.SIZE_SHRINK_END
	side_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	# Never disabled: a disabled axis adopts the content's minimum, which would
	# let a style's fonts resize the 4D viewport and with it the slice tiling.
	side_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	side_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	board_stage.add_child(side_scroll)
	side_column = VBoxContainer.new()
	side_column.name = "SideColumn"
	side_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	side_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side_column.add_theme_constant_override("separation", 6)
	side_fit = FitScaleContainerScript.new()
	side_fit.name = "SideColumnFit"
	side_fit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	side_scroll.add_child(side_fit)
	side_fit.add_child(side_column)
	control_deck = VBoxContainer.new()
	control_deck.name = "ControlDeck"
	control_deck.visible = false
	control_deck.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	control_deck.mouse_filter = Control.MOUSE_FILTER_IGNORE
	control_deck.add_theme_constant_override("separation", 8)
	add_child(control_deck)
	deck_scroll = ScrollContainer.new()
	deck_scroll.name = "DeckScroll"
	deck_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	deck_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	deck_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	deck_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	control_deck.add_child(deck_scroll)
	deck_row_host = VBoxContainer.new()
	deck_row_host.name = "DeckRows"
	deck_row_host.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	deck_row_host.size_flags_vertical = Control.SIZE_EXPAND_FILL
	deck_row_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	deck_fit = FitScaleContainerScript.new()
	deck_fit.name = "DeckRowsFit"
	deck_fit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	deck_fit.size_flags_vertical = Control.SIZE_EXPAND_FILL
	deck_scroll.add_child(deck_fit)
	deck_fit.add_child(deck_row_host)
	for row_index in range(MAX_DECK_ROWS):
		var row := HBoxContainer.new()
		row.name = "DeckRow%d" % row_index
		row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.size_flags_vertical = Control.SIZE_EXPAND_FILL
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_theme_constant_override("separation", 10)
		row.visible = row_index == 0
		deck_row_host.add_child(row)
		deck_rows.append(row)
	for specification in [["PieceControls", 42], ["ViewControls", 33], ["PieceState", 25]]:
		var module := _slot(str(specification[0]))
		module.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		module.size_flags_stretch_ratio = float(specification[1])
		deck_rows[0].add_child(module)
		match str(specification[0]):
			"PieceControls": piece_controls = module
			"ViewControls": view_controls = module
			"PieceState": piece_state = module
	# Packing consumes measured widths, and both inputs settle only after a
	# layout pass: the deck's own width, and each module's minimum once its
	# strip is reparented in. Without re-packing on those signals the deck keeps
	# whatever arrangement a transient early width produced.
	control_deck.resized.connect(_queue_deck_metrics_check)
	for module in [piece_controls, view_controls, piece_state]:
		module.minimum_size_changed.connect(_queue_deck_metrics_check)
	header_slot.minimum_size_changed.connect(_queue_deck_metrics_check)
	side_scroll.resized.connect(_queue_deck_metrics_check)


# These signals fire while Godot propagates visibility or sorts a container,
# when it refuses add_child on the node being notified. The policy reparents
# the deck and modules, and a refused reparent leaves the node with no parent
# at all, so the check runs on the next frame, like the fit settle passes.
# Signals raised by the policy's own pass are dropped as before, and a burst
# coalesces into one check. A deferred call would run inside the same idle
# flush that sorts the containers it resized, so each pass would queue the
# next and flood the message queue.
func _queue_deck_metrics_check() -> void:
	if control_deck.visible and not _layout_coordinator.applying():
		_layout_coordinator.request_metrics()


func set_deck_placement(placement: String) -> void:
	_requested_placement = placement if placement in [PLACEMENT_SIDE, PLACEMENT_SPLIT] else PLACEMENT_BELOW
	_apply_responsive_policy()


# A split column costs width a narrow window cannot spare, so narrow and small
# shells fall back to the reflowing deck below the board.
func _effective_placement() -> String:
	return LayoutPolicy.placement(_requested_placement, _responsive_profile)

func _relocate(next_placement: String) -> void:
	if next_placement == _placement:
		return
	var leaving_split := _placement == PLACEMENT_SPLIT
	_placement = next_placement
	_reset_fit()
	var side := _placement == PLACEMENT_SIDE
	side_scroll.visible = _placement == PLACEMENT_SPLIT
	if _placement == PLACEMENT_SPLIT:
		for module in [piece_state, view_controls]:
			(module as Control).reparent(side_column, false)
		side_column.move_child(piece_state, 0)
	elif leaving_split:
		# Row assignment reparents every module it packs; seed them back first.
		for module in [view_controls, piece_state]:
			(module as Control).reparent(deck_rows[0], false)
	# The split host is chosen per pass by _place_split_deck; start full width.
	var host: Container = board_stage if side else self
	_split_full_height = false
	_move_deck(host)
	control_deck.size_flags_horizontal = Control.SIZE_SHRINK_END if side else Control.SIZE_EXPAND_FILL
	control_deck.size_flags_vertical = Control.SIZE_EXPAND_FILL if side else Control.SIZE_FILL
	for row in deck_rows:
		# Rail rows hug their content so the legend stays put at the top of the
		# rail instead of spreading out as the window grows.
		row.size_flags_vertical = Control.SIZE_FILL if side else Control.SIZE_EXPAND_FILL
	deck_row_host.size_flags_vertical = Control.SIZE_FILL if side else Control.SIZE_EXPAND_FILL


func deck_placement() -> String:
	return _placement


func set_control_deck_visible(enabled: bool, density: String = "standard") -> void:
	if _designer_session.active():
		_designer_session.set_restored_deck_visibility(enabled)
	else:
		control_deck.visible = enabled
	_density = density
	_apply_responsive_policy()


# layout_size is the cockpit's own logical extent and drives row packing.
# apparent_size is what the player actually sees and drives the breakpoint.
func set_available_size(layout_size: Vector2, apparent_size: Vector2, density: String = "standard") -> void:
	_layout_size = layout_size
	_apparent_size = apparent_size
	_density = density
	_apply_responsive_policy()


func responsive_profile_for_size(apparent_size: Vector2) -> String:
	return LayoutPolicy.profile(apparent_size)

func deterministic_snapshot() -> Dictionary:
	return {
		"owner": "LiveCockpit",
		"slots": [str(header_slot.name), str(primary_board_surface.name), str(control_deck.name)],
		"deck_modules": [str(piece_controls.name), str(view_controls.name), str(piece_state.name)],
		"deck_visible": control_deck.visible,
		"deck_placement": _placement,
		"side_column_rect": side_scroll.get_global_rect() if side_scroll.visible else Rect2(),
		"responsive_profile": _responsive_profile,
		"layout_size": _layout_size,
		"apparent_size": _apparent_size,
		# Below the board the deck's height is the cap it imposes; beside it the
		# rail is as tall as the stage, so its laid-out height is the constraint.
		"deck_minimum_height": control_deck.size.y if _placement == PLACEMENT_SIDE else control_deck.custom_minimum_size.y,
		"deck_separation": control_deck.get_theme_constant("separation"),
		"deck_row_count": _row_assignment.size(),
		"deck_natural_height": _natural_deck_height,
		"deck_scroll_required": _scroll_required,
		"side_column_natural_height": _side_column_natural_height,
		"side_column_scroll_required": _side_column_scroll_required,
		"compacted_modules": _compacted.duplicate(),
		"deck_fit_scale": deck_fit.fit_scale,
		"side_fit_scale": side_fit.fit_scale,
		"stage_rect": board_stage.get_global_rect(),
		"board_spare_height": _board_spare_height(),
		"deck_room": _deck_room,
		"split_column_full_height": _split_full_height,
		"board_content_aspect": _board_aspect,
		"rail_width": control_deck.size.x if _placement == PLACEMENT_SIDE else 0.0,
		"deck_rows_rect": deck_row_host.get_global_rect(),
		"deck_row_assignment": _row_assignment.duplicate(true),
		"deck_minimum_width": control_deck.get_combined_minimum_size().x,
		"widest_module_minimum": _widest_module_minimum(),
		"rect": get_global_rect(),
		"header_rect": header_slot.get_global_rect(),
		"primary_rect": primary_board_surface.get_global_rect(),
		"deck_rect": control_deck.get_global_rect(),
	}


# Greedy flow packing by measured minimum width. A fixed per-profile row table
# cannot satisfy its own band: PIECE+VIEW alone need ~1164px while the narrow
# band starts at 800, so the arrangement has to follow measurement, not a
# hard-coded shape. Module identity and order are preserved in every profile.
func _on_deck_metrics_changed() -> void:
	if not control_deck.visible or _layout_coordinator.applying():
		return
	var width := _packing_width()
	var minimums := _module_minimums()
	if is_equal_approx(width, _last_packing_width) and minimums.is_equal_approx(_last_module_minimums) and _module_heights().is_equal_approx(_last_module_heights) and is_equal_approx(_header_height(), _last_header_height) and is_equal_approx(_stage_constraint(), _last_stage_height) and _host_widths().is_equal_approx(_last_host_widths):
		if _placement == PLACEMENT_SIDE:
			_update_side_scroll_state()
		elif _placement == PLACEMENT_SPLIT:
			_update_split_scroll_state()
		return
	_apply_responsive_policy()


func _header_height() -> float:
	return header_slot.get_combined_minimum_size().y


func _module_minimums() -> Vector3:
	return Vector3(
		piece_controls.get_combined_minimum_size().x,
		view_controls.get_combined_minimum_size().x,
		piece_state.get_combined_minimum_size().x
	)


func _module_heights() -> Vector3:
	return Vector3(
		piece_controls.get_combined_minimum_size().y,
		view_controls.get_combined_minimum_size().y,
		piece_state.get_combined_minimum_size().y
	)


func _apply_responsive_policy() -> void:
	_layout_coordinator.apply_now()


func _apply_layout() -> void:
	if _designer_session.active():
		constrain_designer_panels()
		return
	_responsive_profile = responsive_profile_for_size(_apparent_size) if _apparent_size.x > 0.0 else PROFILE_STANDARD
	_relocate(_effective_placement())
	if not control_deck.visible:
		_reset_fit()
		return
	if _placement == PLACEMENT_SIDE:
		_apply_side_policy()
		_layout_coordinator.request_metrics()
		return
	control_deck.custom_minimum_size.x = 0.0
	side_scroll.custom_minimum_size.x = clampf(_layout_size.x * SPLIT_COLUMN_WIDTH_SHARE, SPLIT_COLUMN_MIN_WIDTH, SPLIT_COLUMN_MAX_WIDTH) if _placement == PLACEMENT_SPLIT else 0.0
	if _placement == PLACEMENT_SPLIT:
		_place_split_deck()
	var row_height := _row_height_for_profile()
	var row_separation := _row_separation_for_profile()
	var deck_separation := 8 if _responsive_profile in [PROFILE_NARROW, PROFILE_SMALL] else 6
	var available := _packing_width()
	var packed := _pack_rows(available, row_separation)
	_apply_row_assignment(packed, row_separation)
	_row_assignment = packed
	control_deck.add_theme_constant_override("separation", deck_separation)
	var natural_height := 0.0
	var deck_height := 0.0
	if _placement == PLACEMENT_SPLIT:
		# The legend's own measured height, not the profile row floor, bounded by
		# the current cockpit height. Both inputs are re-read on every pass, so
		# the deck never keeps a height a smaller window imposed.
		var measure := func() -> float: return _natural_height_for_rows(packed, 0.0, deck_separation)
		var shortfall := 0.0
		if _layout_size.y > 1.0:
			var header_growth := maxf(_header_height() - float(ReplayVisuals.LIVE_TOP_BAR_HEIGHT), 0.0)
			shortfall = maxf(LEGEND_FULL_FIT_HEIGHT + header_growth - _layout_size.y, 0.0)
		var cap := _layout_size.y * MAX_DECK_HEIGHT_SHARE if _layout_size.y > 1.0 else INF
		# The board keeps its reference allocation: the deck gives up exactly the
		# missing height, measured against the relaxed legend.
		var room_for := func(relaxed: float) -> float: return LayoutPolicy.split_deck_room(relaxed, shortfall, cap)
		natural_height = _fit_height("deck", [piece_controls], measure, room_for, _deck_settled())
		# Compact: the room follows the recorded relaxed legend, not the compact one.
		var deck_state = _fit_states.get("deck")
		var relaxed_legend: float = deck_state.relaxed_height() if deck_state != null and deck_state.is_compact() else natural_height
		deck_height = minf(natural_height, room_for.call(relaxed_legend))
	else:
		var measure := func() -> float: return _natural_height_for_rows(packed, row_height, deck_separation)
		var height_cap := _layout_size.y * MAX_DECK_HEIGHT_SHARE if _layout_size.y > 1.0 else INF
		var left := _stage_height() - primary_board_surface.get_combined_minimum_size().y - float(get_theme_constant("separation"))
		var room := LayoutPolicy.below_deck_room(height_cap, row_height, _board_spare_height(), left, _layout_size.y > 1.0, FIT_SCALE_FLOOR)
		_deck_room = room
		natural_height = _fit_height("deck", [piece_controls, view_controls, piece_state], measure, func(_relaxed: float) -> float: return room, _deck_settled())
		deck_height = minf(natural_height, room)
	# The rows lay out unscaled inside the fit box.
	deck_row_host.custom_minimum_size.y = natural_height / deck_fit.fit_scale
	control_deck.custom_minimum_size.y = deck_height
	_natural_deck_height = natural_height
	_scroll_required = natural_height > deck_height + 0.5
	if _placement == PLACEMENT_SPLIT:
		var column_room := side_scroll.size.y
		_side_column_natural_height = _fit_height("side", [piece_state, view_controls], func() -> float: return side_column.get_combined_minimum_size().y, func(_relaxed: float) -> float: return column_room, side_scroll.size.x >= side_scroll.custom_minimum_size.x - 1.0)
		_update_split_scroll_state()
	else:
		_side_column_natural_height = 0.0
		_side_column_scroll_required = false
	_last_stage_height = _stage_constraint()
	_last_host_widths = _host_widths()
	_last_packing_width = available
	_last_module_minimums = _module_minimums()
	_last_module_heights = _module_heights()
	_last_header_height = _header_height()
	# Both packing inputs are only final after a layout pass, and the first pass
	# may see a transient width. Re-check once the pass settles; the width and
	# minimum guards make this converge rather than loop.
	_layout_coordinator.request_metrics()


# The share-based width is the rail's floor. Above it the rail grows to what its
# content asks for (full piece names, an unwrapped MOVE row) but only into the
# width the right-anchored board leaves unused, so the board never shrinks.
func _rail_width() -> float:
	if _layout_size.x <= 1.0:
		return SIDE_RAIL_MIN_WIDTH
	var share := SIDE_RAIL_NARROW_WIDTH_SHARE if _responsive_profile in [PROFILE_NARROW, PROFILE_SMALL] else SIDE_RAIL_WIDTH_SHARE
	var base := clampf(_layout_size.x * share, SIDE_RAIL_MIN_WIDTH, SIDE_RAIL_MAX_WIDTH)
	var preferred := _rail_preferred_width()
	if preferred <= base:
		return base
	return LayoutPolicy.rail_width(base, preferred, _rail_room_beside_board())


# Widest content need among the rail's modules, plus room for the rail's own
# scrollbar so a scrolling rail does not rewrap into a taller one.
func _rail_preferred_width() -> float:
	var widest := 0.0
	for module in [piece_state, piece_controls]:
		if (module as Control).visible:
			widest = maxf(widest, _module_preferred_width(module))
	if widest <= 0.0:
		return 0.0
	return widest + deck_scroll.get_v_scroll_bar().get_combined_minimum_size().x


# Helpers that can show more when wider say so: unwrapped_width() is the whole
# control at its unwrapped line, preferred_width() one card laid out in a grid.
func _module_preferred_width(module: Control) -> float:
	var module_minimum := module.get_combined_minimum_size().x
	var best := module_minimum
	for node in module.find_children("*", "Control", true, false):
		var control := node as Control
		if not control.visible:
			continue
		if control.has_method("unwrapped_width"):
			best = maxf(best, module_minimum - control.get_combined_minimum_size().x + float(control.unwrapped_width()))
		elif control.has_method("preferred_width"):
			var grid := control.get_parent() as GridContainer
			if grid != null:
				var columns := maxi(grid.columns, 1)
				var row := float(columns) * float(control.preferred_width()) + float((columns - 1) * grid.get_theme_constant("h_separation"))
				best = maxf(best, module_minimum - grid.get_combined_minimum_size().x + row)
			else:
				best = maxf(best, module_minimum - control.get_combined_minimum_size().x + float(control.preferred_width()))
	return best


# The fitted board's width per unit of height comes from the camera, so the
# board's demand follows the current stage height and the rail may take the
# rest. Unknown aspect or an unsettled stage leaves no room beyond the floor.
func set_board_demand(aspect: float, board_viewport: Control) -> void:
	_board_viewport = board_viewport
	if is_equal_approx(aspect, _board_aspect):
		return
	_board_aspect = aspect
	_apply_responsive_policy()


func _rail_room_beside_board() -> float:
	var stage_height := board_stage.size.y
	if _board_aspect <= 0.0 or stage_height <= 1.0 or _board_viewport == null or not is_instance_valid(_board_viewport):
		return 0.0
	# Frame and padding between the board surface and the rendered viewport.
	var inset := (primary_board_surface.size - _board_viewport.size).max(Vector2.ZERO)
	return LayoutPolicy.rail_room(_layout_size.x, stage_height, inset, _board_aspect,
		primary_board_surface.get_combined_minimum_size().x, DECK_HORIZONTAL_INSET + float(SIDE_RAIL_GAP))


# The rail stacks visible modules top to bottom: what the player glances at
# most (NEXT/HOLD, then the key legend) comes first. Its height is the stage's
# height, so the only overflow is a genuinely short window, which scrolls.
func _apply_side_policy() -> void:
	control_deck.custom_minimum_size = Vector2(_rail_width(), 0.0)
	control_deck.add_theme_constant_override("separation", 6)
	var packed: Array = []
	for module in [piece_state, piece_controls, view_controls]:
		if (module as Control).visible:
			packed.append([str((module as Control).name)])
	# Stacked panels need only a hairline between them; the deck's row gap is
	# sized for modules side by side.
	var row_separation := ShellDesignTokensScript.SPACE_1
	_apply_row_assignment(packed, row_separation)
	_row_assignment = packed
	var rail_room := control_deck.size.y
	_natural_deck_height = _fit_height("deck", [piece_state, piece_controls], func() -> float: return _natural_height_for_rows(packed, 0.0, row_separation), func(_relaxed: float) -> float: return rail_room, control_deck.size.x >= _rail_width() - 1.0)
	deck_row_host.custom_minimum_size.y = _natural_deck_height / deck_fit.fit_scale
	_side_column_natural_height = 0.0
	_side_column_scroll_required = false
	_last_stage_height = _stage_constraint()
	_last_host_widths = _host_widths()
	_last_packing_width = _packing_width()
	_last_module_minimums = _module_minimums()
	_last_module_heights = _module_heights()
	_last_header_height = _header_height()
	_update_side_scroll_state()


func _update_side_scroll_state() -> void:
	var available := control_deck.size.y
	_scroll_required = available > 1.0 and _natural_deck_height > available + 0.5


func _update_split_scroll_state() -> void:
	var available := side_scroll.size.y
	_side_column_scroll_required = available > 1.0 and _side_column_natural_height > available + 0.5


# Helpers fit before they scroll, in three steps: relaxed spacing, then
# halved gaps, then the whole module scaled down uniformly (text, keycaps,
# glyphs and previews together) to FIT_SCALE_FLOOR. Only content that still
# overflows at the floor scrolls.
#
# Minimum sizes settle only after a layout pass, so a step cannot be measured
# in the pass that takes it. Each step therefore acts on a height two settled
# frames agree on and records it: the relaxed height decides when to relax,
# the compact height at the unscaled width sets the scale. Re-measuring while
# scaled would read the wider, less wrapped layout and oscillate. The result
# depends on the current size and content alone, never on history.
# room_for maps the relaxed height to the room (only the split deck's room
# depends on it). A host still at a transient width wraps its labels into a
# meaningless height, so an unsettled pass measures but decides nothing.
# Returns the height the group shows: its measured height times its scale.
func _fit_height(group: String, modules: Array, measure: Callable, room_for: Callable, settled: bool) -> float:
	var state = _fit_states.get(group)
	if state == null:
		state = HelperFitState.new()
		_fit_states[group] = state
	var natural: float = measure.call()
	var savings := 0.0
	var content_key: Array = []
	for module in modules:
		savings += ResponsivePanelPolicy.compact_savings_bound(module)
		content_key.append_array(ResponsivePanelPolicy.fit_content_key(module))
	var fresh: bool = state.is_compact() and _set_compact(modules, true) > 0
	var decision: Dictionary = state.observe(natural, room_for, _fit_host(group).size.x,
		settled and _fit_content_settled(group), Engine.get_process_frames(), savings, fresh, content_key)
	_set_compact(modules, bool(decision["compact"]))
	var fit = _fit_box(group)
	var scale := float(decision["scale"])
	if not is_equal_approx(scale, fit.fit_scale):
		fit.fit_scale = scale
		_schedule_fit_settle()
	if bool(decision["remeasure"]):
		_schedule_fit_settle()
	return natural * scale


# True once every fit group has decided: nothing awaits agreement, no scale
# search is running and no settle pass is queued. Layout checks wait for it.
func fit_settled() -> bool:
	if not _layout_coordinator.idle():
		return false
	for group in _fit_states:
		var state = _fit_states[group]
		if not state.settled():
			return false
	return true


func _fit_box(group: String):
	return side_fit if group == "side" else deck_fit


# The content must have been laid out at the host's width: measured narrower,
# its labels wrap into a height no settled layout would have.
func _fit_content_settled(group: String) -> bool:
	var fit = _fit_box(group)
	var host := _fit_host(group)
	var content: Control = fit.content()
	if content == null or host.size.x <= 1.0:
		return false
	var bar := host.get_v_scroll_bar().get_combined_minimum_size().x
	return fit.size.x >= host.size.x - bar - 1.0 and content.size.x * fit.fit_scale >= fit.size.x - 1.0


# The scroll around a fit box: its width is set by layout alone, while the box
# inside narrows whenever the scrollbar shows, which a fit itself toggles.
func _fit_host(group: String) -> ScrollContainer:
	return side_scroll if group == "side" else deck_scroll


# The toggling pass already sees part of the new minimums, so the metric guard
# can miss the change. Re-measure once the next frame has laid it out.
func _schedule_fit_settle() -> void:
	_layout_coordinator.request_fit()


func _set_compact(modules: Array, enabled: bool) -> int:
	var fresh := 0
	for module in modules:
		# Always applied: a strip rebuilt since the last pass has relaxed gaps.
		fresh += ResponsivePanelPolicy.compact_vertical_gaps(module, enabled)
		var key := str((module as Control).name)
		if enabled and not _compacted.has(key):
			_compacted.append(key)
		elif not enabled:
			_compacted.erase(key)
	return fresh


# Each placement groups the modules differently, so a recorded relaxed height
# is meaningless after a move or while the Designer owns the panels.
func _reset_fit() -> void:
	_set_compact([piece_controls, view_controls, piece_state], false)
	_fit_states.clear()
	for fit in [deck_fit, side_fit]:
		fit.fit_scale = 1.0


# The split column spans the whole stage only when the legend deck, narrowed to
# sit under the board alone, still holds every section on one line with room
# for its scrollbar. Otherwise the legend would wrap and grow taller than the
# column gains, so the deck keeps the full width under board and column. The
# line width does not depend on the deck's host, so this cannot flip-flop.
func _place_split_deck() -> void:
	var narrowed := _layout_size.x - DECK_HORIZONTAL_INSET - side_scroll.custom_minimum_size.x - float(SIDE_RAIL_GAP)
	narrowed -= deck_scroll.get_v_scroll_bar().get_combined_minimum_size().x
	var full_height := _layout_size.x > 1.0 and _legend_single_line_width() <= narrowed
	var host: Container = board_column if full_height else self
	if full_height != _split_full_height or control_deck.get_parent() != host:
		_split_full_height = full_height
		_reset_fit()
		_move_deck(host)


# The policy often runs from the deck's own resized signal, which a container
# emits while sorting its children. A queue_sort raised then is dropped
# because the sort is still pending, so the container the deck left would keep
# the deck's height as dead space. Re-sort both parents after this pass.
func _move_deck(host: Container) -> void:
	var previous := control_deck.get_parent() as Container
	if previous != host:
		control_deck.reparent(host, false)
	host.move_child(control_deck, host.get_child_count() - 1)
	for container in [previous, host]:
		if container != null:
			(container as Container).queue_sort.call_deferred()


func _legend_single_line_width() -> float:
	for child in piece_controls.get_children():
		if child.has_method("unwrapped_width"):
			return float(child.unwrapped_width())
	return piece_controls.get_combined_minimum_size().x


# Only a deck narrower than its packing width wraps into a misleading height; a
# shell held wider by its minimum size is a settled, if wider, layout.
func _deck_settled() -> bool:
	var expected := _packing_width()
	return control_deck.size.x > 1.0 and control_deck.size.x >= expected - maxf(2.0, expected * 0.02)


# Height below the header that the stage (board plus a deck under it) can use.
func _stage_height() -> float:
	if _layout_size.y <= 1.0:
		return 0.0
	return LayoutPolicy.stage_height(_layout_size.y, _header_height(), DECK_VERTICAL_INSET, float(get_theme_constant("separation")))


func _board_spare_height() -> float:
	return _stage_height() * (1.0 - BOARD_RESERVE_STAGE_SHARE)


# Beside-the-board placements size their scroll from the laid-out stage, so a
# stage resize must re-run the fit even when no module metric changed.
func _stage_constraint() -> float:
	return board_stage.size.y if _placement in [PLACEMENT_SIDE, PLACEMENT_SPLIT] else -1.0


# Packing must consume the CONSTRAINT, not the result. control_deck.size.x is
# the deck's own laid-out width, which when the deck overflows is its minimum -
# so reading it makes the deck conclude it has room for the very arrangement
# that overflowed, and it never reflows.
func _packing_width() -> float:
	if _layout_size.x > 1.0:
		var width := _layout_size.x - DECK_HORIZONTAL_INSET
		if _placement == PLACEMENT_SPLIT and _split_full_height:
			# The split deck sits under the board, beside the full-height column.
			width -= side_scroll.custom_minimum_size.x + float(SIDE_RAIL_GAP)
		return maxf(width, 1.0)
	var deck_width := control_deck.size.x
	return deck_width if deck_width > 1.0 else 0.0


func _host_widths() -> Vector2:
	return Vector2(control_deck.size.x, side_scroll.size.x if side_scroll.visible else 0.0)


func _pack_rows(available: float, row_separation: int) -> Array:
	var sources := [piece_controls] if _placement == PLACEMENT_SPLIT else [piece_state, piece_controls, view_controls]
	var measurements: Array = []
	for module in sources:
		measurements.append({"name": str(module.name), "width": module.get_combined_minimum_size().x})
	return LayoutPolicy.pack_rows(measurements, available, row_separation)

func _apply_row_assignment(packed: Array, row_separation: int) -> void:
	var module_by_name := {
		str(piece_controls.name): piece_controls,
		str(view_controls.name): view_controls,
		str(piece_state.name): piece_state,
	}
	for row_index in range(deck_rows.size()):
		var row := deck_rows[row_index]
		row.visible = row_index < packed.size()
		row.add_theme_constant_override("separation", row_separation)
	for row_index in range(packed.size()):
		var row := deck_rows[row_index]
		var names: Array = packed[row_index]
		for position in range(names.size()):
			var module: VBoxContainer = module_by_name[str(names[position])]
			if module.get_parent() != row:
				module.reparent(row, false)
			row.move_child(module, position)
		# Stretch ratios only distribute surplus, so they are a presentation
		# nicety on top of packing, never the mechanism that prevents overflow.
		if names.size() == 3:
			piece_controls.size_flags_stretch_ratio = 42.0
			view_controls.size_flags_stretch_ratio = 33.0
			piece_state.size_flags_stretch_ratio = 25.0
		else:
			for name_value in names:
				(module_by_name[str(name_value)] as Control).size_flags_stretch_ratio = 1.0


func _natural_height_for_rows(packed: Array, profile_floor: float, row_separation: int) -> float:
	var heights: Dictionary = {}
	for module in [piece_controls, view_controls, piece_state]:
		heights[str(module.name)] = module.get_combined_minimum_size().y
	var gap := maxi(row_separation, deck_row_host.get_theme_constant("separation"))
	return LayoutPolicy.rows_height(packed, heights, profile_floor, gap)

func _row_height_for_profile() -> float:
	return LayoutPolicy.row_height(_responsive_profile, _density)


func _row_separation_for_profile() -> int:
	return LayoutPolicy.row_separation(_responsive_profile)

func _widest_module_minimum() -> float:
	return maxf(
		piece_controls.get_combined_minimum_size().x,
		maxf(view_controls.get_combined_minimum_size().x, piece_state.get_combined_minimum_size().x)
	)


func _slot(slot_name: String) -> VBoxContainer:
	var result := VBoxContainer.new()
	result.name = slot_name
	result.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return result
