extends VBoxContainer

class_name LiveCockpit

const DesignerPanelFrame = preload("res://scripts/ui/designer_panel_frame.gd")
const ShellDesignTokensScript = preload("res://scripts/ui/style/shell_design_tokens.gd")

const PROFILE_WIDE := "wide"
const PROFILE_STANDARD := "standard"
const PROFILE_NARROW := "narrow"
const PROFILE_SMALL := "small"

# Breakpoints are apparent widths: OS window client pixels divided by the
# display scale and by the requested UI scale. They are not logical viewport
# coordinates, which stay pinned to the design resolution under canvas_items
# stretch and therefore cannot express how large the shell actually looks.
const WIDE_MIN_WIDTH := 1680.0
const STANDARD_MIN_WIDTH := 1180.0
const NARROW_MIN_WIDTH := 800.0

const MAX_DECK_ROWS := 3
# Reflow buys width at a height cost: every extra row is another ~190px while
# the board already holds a large minimum, so a narrow window would otherwise
# have to be TALLER to stay contained. Capping the deck and scrolling the
# overflow keeps every control reachable at any size; the cost is that not all
# of them are visible at once, which is the accepted tradeoff for small shells.
const MAX_DECK_HEIGHT_SHARE := 0.28
# Outer shell margin on each side of the cockpit.
const DECK_HORIZONTAL_INSET := 24.0

# A tall board (Live 2D is 1:2) wastes most of a wide window, while a deck
# under it takes the one dimension the board is short of. Beside the board the
# deck spends width instead, the way the Python client's side panel did.
const PLACEMENT_BELOW := "below"
const PLACEMENT_SIDE := "side"
# Live 4D: the piece legend is wide and short, so it stays in the deck; NEXT/
# HOLD and VIEW move to a side column. Together they did not fit one deck row
# at 1440 px. The column narrows the width-limited slice row (about 30 -> 26 px
# cells at 1440x900); that is the price of every 4D control visible unscrolled.
const PLACEMENT_SPLIT := "split"
# Standard and wide shells need ~440 px at the 1280 px reference width for the
# 3D compass and drops to share a row; narrow shells scroll the rail anyway and
# give the width back to the board (and an open Designer panel).
const SIDE_RAIL_WIDTH_SHARE := 0.35
const SIDE_RAIL_NARROW_WIDTH_SHARE := 0.30
const SIDE_RAIL_MIN_WIDTH := 280.0
const SIDE_RAIL_MAX_WIDTH := 460.0
const SIDE_RAIL_GAP := 10
# The split column holds only NEXT/HOLD and stacked VIEW, so it stays narrower.
const SPLIT_COLUMN_WIDTH_SHARE := 0.22
# NEXT/HOLD side by side need about 290 px; below that they clip.
const SPLIT_COLUMN_MIN_WIDTH := 300.0
const SPLIT_COLUMN_MAX_WIDTH := 340.0

var header_slot: VBoxContainer
var board_stage: HBoxContainer
var primary_board_surface: VBoxContainer
var side_column: VBoxContainer
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
var _packing_in_progress := false
var _last_packing_width := -1.0
var _last_module_minimums := Vector3.ZERO
var _last_module_heights := Vector3.ZERO
var _natural_deck_height := 0.0
var _scroll_required := false
var _placement := PLACEMENT_BELOW
var _requested_placement := PLACEMENT_BELOW

var _designer_host: Control
var _designer_frames: Dictionary = {}
var _designer_origins: Dictionary = {}
var _designer_rects: Dictionary = {}
var _designer_enabled := false
var _designer_deck_visible := false


func set_designer_layout_enabled(enabled: bool, board: Control) -> void:
	if enabled == _designer_enabled:
		return
	_designer_enabled = enabled
	if enabled:
		_designer_deck_visible = control_deck.visible
		_designer_host = Control.new()
		_designer_host.name = "DesignerCockpitSurface"
		_designer_host.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_designer_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_designer_host)
		_designer_host.resized.connect(_constrain_designer_panels)
		for entry in [["Board", board], ["Piece controls", piece_controls], ["View controls", view_controls], ["NEXT / HOLD", piece_state]]:
			var panel: Control = entry[1]
			var key := str(panel.name)
			_designer_origins[key] = {"parent": panel.get_parent(), "index": panel.get_index(), "visible": panel.visible}
			var frame = DesignerPanelFrame.new()
			_designer_host.add_child(frame)
			frame.configure(str(entry[0]), panel, panel != board)
			panel.show()
			frame.geometry_edited.connect(func(rect: Rect2) -> void: _designer_rects[key] = rect)
			_designer_frames[key] = frame
		board_stage.hide()
		control_deck.hide()
		call_deferred("_constrain_designer_panels")
	else:
		for key in _designer_frames:
			var frame = _designer_frames[key]
			_designer_rects[key] = Rect2(frame.position, frame.size)
			var origin: Dictionary = _designer_origins[key]
			frame.content.reparent(origin["parent"], false)
			frame.content.visible = origin["visible"]
			origin["parent"].move_child(frame.content, mini(origin["index"], origin["parent"].get_child_count() - 1))
		_designer_host.queue_free()
		_designer_host = null
		_designer_frames.clear()
		_designer_origins.clear()
		board_stage.show()
		control_deck.visible = _designer_deck_visible
		_apply_responsive_policy()


func designer_panels() -> Dictionary:
	return _designer_frames.duplicate()


func raise_designer_panel(panel_name: String) -> void:
	if _designer_enabled and _designer_frames.has(panel_name):
		_designer_host.move_child(_designer_frames[panel_name], _designer_host.get_child_count() - 1)


func _constrain_designer_panels() -> void:
	if not _designer_enabled or _designer_host == null or _designer_host.size.x < 1:
		return
	var extent := _designer_host.size
	var index := 0
	for key in _designer_frames:
		var frame = _designer_frames[key]
		var gap := 8.0
		var half_width := (extent.x - gap) * 0.65
		var right_origin := half_width + gap
		var column_width := extent.x - right_origin
		var module_width := column_width
		var row_height := (extent.y - gap * 2) / 3.0
		var initial := Rect2(Vector2.ZERO, Vector2(half_width, extent.y))
		if index == 1:
			initial = Rect2(Vector2(right_origin, 0), Vector2(module_width, row_height))
		elif index == 2:
			initial = Rect2(Vector2(right_origin, row_height + gap), Vector2(module_width, row_height))
		elif index == 3:
			initial = Rect2(Vector2(right_origin, (row_height + gap) * 2), Vector2(module_width, row_height))
		frame.constrain(_designer_rects.get(key, initial))
		_designer_rects[key] = Rect2(frame.position, frame.size)
		index += 1


func _init() -> void:
	name = "LiveCockpit"
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
	primary_board_surface = _slot("PrimaryBoardSurface")
	primary_board_surface.size_flags_vertical = Control.SIZE_EXPAND_FILL
	board_stage.add_child(primary_board_surface)
	# Scrolls as a whole so a short window never pushes the deck off-screen;
	# NEXT/HOLD sit at its top and stay visible.
	side_scroll = ScrollContainer.new()
	side_scroll.name = "SideColumnScroll"
	side_scroll.visible = false
	side_scroll.size_flags_horizontal = Control.SIZE_SHRINK_END
	side_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	# Never disabled: a disabled axis adopts the content's minimum, which would
	# let a style's fonts resize the 4D viewport and with it the slice tiling.
	side_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	side_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	board_stage.add_child(side_scroll)
	side_column = VBoxContainer.new()
	side_column.name = "SideColumn"
	side_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	side_column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side_column.add_theme_constant_override("separation", 6)
	side_scroll.add_child(side_column)
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
	deck_scroll.add_child(deck_row_host)
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
	control_deck.resized.connect(_on_deck_metrics_changed)
	for module in [piece_controls, view_controls, piece_state]:
		module.minimum_size_changed.connect(_on_deck_metrics_changed)


func set_deck_placement(placement: String) -> void:
	_requested_placement = placement if placement in [PLACEMENT_SIDE, PLACEMENT_SPLIT] else PLACEMENT_BELOW
	_apply_responsive_policy()


# A split column costs width a narrow window cannot spare, so narrow and small
# shells fall back to the reflowing deck below the board.
func _effective_placement() -> String:
	if _requested_placement == PLACEMENT_SPLIT and _responsive_profile in [PROFILE_NARROW, PROFILE_SMALL]:
		return PLACEMENT_BELOW
	return _requested_placement


func _relocate(next_placement: String) -> void:
	if next_placement == _placement:
		return
	var leaving_split := _placement == PLACEMENT_SPLIT
	_placement = next_placement
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
	control_deck.reparent(board_stage if side else self, false)
	if not side:
		move_child(control_deck, get_child_count() - 1)
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
	if _designer_enabled:
		_designer_deck_visible = enabled
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
	if apparent_size.x >= WIDE_MIN_WIDTH:
		return PROFILE_WIDE
	if apparent_size.x >= STANDARD_MIN_WIDTH:
		return PROFILE_STANDARD
	if apparent_size.x >= NARROW_MIN_WIDTH:
		return PROFILE_NARROW
	return PROFILE_SMALL


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
	if _packing_in_progress:
		return
	var width := _packing_width()
	var minimums := _module_minimums()
	if is_equal_approx(width, _last_packing_width) and minimums.is_equal_approx(_last_module_minimums) and _module_heights().is_equal_approx(_last_module_heights):
		if _placement == PLACEMENT_SIDE:
			_update_side_scroll_state()
		return
	_apply_responsive_policy()


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
	if _designer_enabled:
		_constrain_designer_panels()
		return
	if _packing_in_progress:
		return
	_packing_in_progress = true
	_responsive_profile = responsive_profile_for_size(_apparent_size) if _apparent_size.x > 0.0 else PROFILE_STANDARD
	_relocate(_effective_placement())
	if _placement == PLACEMENT_SIDE:
		_apply_side_policy()
		_packing_in_progress = false
		if is_inside_tree():
			call_deferred("_on_deck_metrics_changed")
		return
	control_deck.custom_minimum_size.x = 0.0
	side_scroll.custom_minimum_size.x = clampf(_layout_size.x * SPLIT_COLUMN_WIDTH_SHARE, SPLIT_COLUMN_MIN_WIDTH, SPLIT_COLUMN_MAX_WIDTH) if _placement == PLACEMENT_SPLIT else 0.0
	var row_height := _row_height_for_profile()
	var row_separation := _row_separation_for_profile()
	var deck_separation := 8 if _responsive_profile in [PROFILE_NARROW, PROFILE_SMALL] else 6
	var available := _packing_width()
	var packed := _pack_rows(available, row_separation)
	_apply_row_assignment(packed, row_separation)
	_row_assignment = packed
	control_deck.add_theme_constant_override("separation", deck_separation)
	var row_count := packed.size()
	var natural_height := _natural_height_for_rows(packed, row_height, deck_separation)
	var height_cap := _layout_size.y * MAX_DECK_HEIGHT_SHARE if _layout_size.y > 1.0 else natural_height
	var deck_height := minf(natural_height, maxf(height_cap, row_height))
	if _placement == PLACEMENT_SPLIT:
		# A fixed height keeps the 4D viewport, and so its slice tiling, independent
		# of the active style's metrics; the legend scrolls if a style outgrows it.
		deck_height = row_height
	deck_row_host.custom_minimum_size.y = natural_height
	control_deck.custom_minimum_size.y = deck_height
	_natural_deck_height = natural_height
	_scroll_required = natural_height > deck_height + 0.5
	_last_packing_width = available
	_last_module_minimums = _module_minimums()
	_last_module_heights = _module_heights()
	_packing_in_progress = false
	# Both packing inputs are only final after a layout pass, and the first pass
	# may see a transient width. Re-check once the pass settles; the width and
	# minimum guards make this converge rather than loop.
	if is_inside_tree():
		call_deferred("_on_deck_metrics_changed")


func _rail_width() -> float:
	if _layout_size.x <= 1.0:
		return SIDE_RAIL_MIN_WIDTH
	var share := SIDE_RAIL_NARROW_WIDTH_SHARE if _responsive_profile in [PROFILE_NARROW, PROFILE_SMALL] else SIDE_RAIL_WIDTH_SHARE
	return clampf(_layout_size.x * share, SIDE_RAIL_MIN_WIDTH, SIDE_RAIL_MAX_WIDTH)


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
	_natural_deck_height = _natural_height_for_rows(packed, 0.0, row_separation)
	deck_row_host.custom_minimum_size.y = _natural_deck_height
	_last_packing_width = _packing_width()
	_last_module_minimums = _module_minimums()
	_last_module_heights = _module_heights()
	_update_side_scroll_state()


func _update_side_scroll_state() -> void:
	var available := control_deck.size.y
	_scroll_required = available > 1.0 and _natural_deck_height > available + 0.5


# Packing must consume the CONSTRAINT, not the result. control_deck.size.x is
# the deck's own laid-out width, which when the deck overflows is its minimum -
# so reading it makes the deck conclude it has room for the very arrangement
# that overflowed, and it never reflows.
func _packing_width() -> float:
	if _layout_size.x > 1.0:
		return maxf(_layout_size.x - DECK_HORIZONTAL_INSET, 1.0)
	var deck_width := control_deck.size.x
	return deck_width if deck_width > 1.0 else 0.0


func _pack_rows(available: float, row_separation: int) -> Array:
	var modules := [piece_controls] if _placement == PLACEMENT_SPLIT else [piece_controls, view_controls, piece_state]
	if available <= 0.0:
		return [modules.map(func(module): return str((module as Control).name))]
	var rows: Array = []
	var current: Array = []
	var current_width := 0.0
	for module in modules:
		var module_width: float = (module as Control).get_combined_minimum_size().x
		var addition := module_width if current.is_empty() else module_width + float(row_separation)
		if not current.is_empty() and current_width + addition > available:
			rows.append(current)
			current = [str((module as Control).name)]
			current_width = module_width
		else:
			current.append(str((module as Control).name))
			current_width += addition
	if not current.is_empty():
		rows.append(current)
	return rows


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
	var module_by_name := {
		str(piece_controls.name): piece_controls,
		str(view_controls.name): view_controls,
		str(piece_state.name): piece_state,
	}
	var height := 0.0
	for names in packed:
		var measured_row_height := profile_floor
		for name_value in names:
			measured_row_height = maxf(
				measured_row_height,
				(module_by_name[str(name_value)] as Control).get_combined_minimum_size().y
			)
		height += measured_row_height
	return height + float(row_separation * maxi(packed.size() - 1, 0))


func _row_height_for_profile() -> float:
	var base := 150.0 if _density == "compact" else 220.0
	match _responsive_profile:
		PROFILE_NARROW:
			return minf(base, 170.0)
		PROFILE_SMALL:
			return minf(base, 150.0)
	return base


func _row_separation_for_profile() -> int:
	match _responsive_profile:
		PROFILE_NARROW:
			return 8
		PROFILE_SMALL:
			return 6
	return 10


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
