extends VBoxContainer

class_name LiveCockpit

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
const MAX_DECK_HEIGHT_SHARE := 0.34
# Outer shell margin on each side of the cockpit.
const DECK_HORIZONTAL_INSET := 24.0

var header_slot: VBoxContainer
var primary_board_surface: VBoxContainer
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
var _natural_deck_height := 0.0
var _scroll_required := false


func _init() -> void:
	name = "LiveCockpit"
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	header_slot = _slot("Header")
	add_child(header_slot)
	primary_board_surface = _slot("PrimaryBoardSurface")
	primary_board_surface.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(primary_board_surface)
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


func set_control_deck_visible(enabled: bool, density: String = "standard") -> void:
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
		"responsive_profile": _responsive_profile,
		"layout_size": _layout_size,
		"apparent_size": _apparent_size,
		"deck_minimum_height": control_deck.custom_minimum_size.y,
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
	if is_equal_approx(width, _last_packing_width) and minimums.is_equal_approx(_last_module_minimums):
		return
	_apply_responsive_policy()


func _module_minimums() -> Vector3:
	return Vector3(
		piece_controls.get_combined_minimum_size().x,
		view_controls.get_combined_minimum_size().x,
		piece_state.get_combined_minimum_size().x
	)


func _apply_responsive_policy() -> void:
	if _packing_in_progress:
		return
	_packing_in_progress = true
	_responsive_profile = responsive_profile_for_size(_apparent_size) if _apparent_size.x > 0.0 else PROFILE_STANDARD
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
	deck_row_host.custom_minimum_size.y = natural_height
	control_deck.custom_minimum_size.y = deck_height
	_natural_deck_height = natural_height
	_scroll_required = natural_height > deck_height + 0.5
	_last_packing_width = available
	_last_module_minimums = _module_minimums()
	_packing_in_progress = false
	# Both packing inputs are only final after a layout pass, and the first pass
	# may see a transient width. Re-check once the pass settles; the width and
	# minimum guards make this converge rather than loop.
	if is_inside_tree():
		call_deferred("_on_deck_metrics_changed")


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
	var modules := [piece_controls, view_controls, piece_state]
	if available <= 0.0:
		return [[str(piece_controls.name), str(view_controls.name), str(piece_state.name)]]
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
	var base := 150.0 if _density == "compact" else (220.0 if _density == "detailed" else 190.0)
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
