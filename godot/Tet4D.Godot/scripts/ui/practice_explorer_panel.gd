extends VBoxContainer

const Contract = preload("res://scripts/input/live_input_contract.gd")

signal requested(action: String)
var _feedback: Label
var _tabs: TabContainer
var _dimension := 0
var _topology_signature := ""
var _topologies: OptionButton
var _topology_host: VBoxContainer
var _pieces: OptionButton
var _piece_names: Array = []
var view_controls_host: VBoxContainer
var _title: Label
var _topology_note: Label
var _undo: Button
var _dimensional_controls: Array[Control] = []
var _board_rows: Dictionary = {}
var _board_readouts: Dictionary = {}
var _board_buttons: Dictionary = {}
var _space_note: Label
var _square_surface := false


func configure(dimension: int) -> void:
	if _dimension == dimension:
		return
	_dimension = dimension
	if _tabs != null:
		_update_dimension_controls()
		return
	_title = _label("Explorer · %dD" % dimension)
	_title.theme_type_variation = "AccentLabel"
	add_child(_title)
	var modes := HBoxContainer.new()
	add_child(modes)
	_button(modes, "2D", "dimension_2")
	_button(modes, "3D", "dimension_3")
	_button(modes, "4D", "dimension_4")
	var session: Dictionary = Contract.explorer_profile(dimension).session
	_button(modes, session.play.label, session.play.command)
	_tabs = TabContainer.new()
	# The outer cockpit fits measured minimums. A ScrollContainer's zero
	# minimum would otherwise collapse both pages to invisible contents.
	_tabs.custom_minimum_size.y = preload("res://scripts/ui/replay_visuals.gd").LIVE_BODY_MIN_HEIGHT
	_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(_tabs)
	view_controls_host = _page("View")
	var object_page := _page("Piece")
	_pieces = OptionButton.new()
	_pieces.name = "PracticePieceSelector"
	_pieces.fit_to_longest_item = false
	_pieces.clip_text = true
	_pieces.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_pieces.item_selected.connect(func(index: int) -> void: requested.emit("piece_%d" % index))
	object_page.add_child(_pieces)
	_piece_names = []
	_button(object_page, session.replace.label, session.replace.command)
	_button(object_page, session.target.label, session.target.command)
	object_page.add_child(_label("Move piece"))
	var moves := GridContainer.new()
	moves.columns = 2
	object_page.add_child(moves)
	for axis in Contract.explorer_profile(4).axes:
		_button(moves, "−" + str(axis.label).to_upper(), axis.negative_command)
		_button(moves, "+" + str(axis.label).to_upper(), axis.positive_command)
	object_page.add_child(_label("Rotate object · quarter turns"))
	var rotations := GridContainer.new()
	rotations.columns = 2
	object_page.add_child(rotations)
	for plane in Contract.explorer_profile(4).rotation_planes:
		_button(rotations, str(plane.label).to_upper() + " −", plane.negative_command)
		_button(rotations, str(plane.label).to_upper() + " +", plane.positive_command)
	_button(object_page, session.retry.label, session.retry.command)
	_undo = _button(object_page, "Undo object action", "undo")
	# Space: what the piece moves through — topology and board size — in every
	# dimension. 3D/4D list later profiles as visibly unavailable.
	var space_page := _page("Space")
	_topology_host = VBoxContainer.new()
	space_page.add_child(_topology_host)
	_topology_host.add_child(_label("Topology"))
	_topologies = OptionButton.new()
	_topologies.name = "ExplorerTopologySelector"
	_topologies.fit_to_longest_item = false
	_topologies.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for record in Contract.explorer_profile(2).topologies:
		_topologies.add_item(record.label)
		_topologies.set_item_metadata(_topologies.item_count - 1, record.id)
		_topologies.set_item_disabled(_topologies.item_count - 1, record.disabled)
	_topologies.item_selected.connect(func(index): requested.emit("topology_" + str(_topologies.get_item_metadata(index))))
	_topology_host.add_child(_topologies)
	_topologies.tooltip_text = "Choose a space at any time. Seam-crossed pieces restore their Retry pose when changing space. Sphere and Projective use one square size N."
	_topology_note = _label("")
	_topology_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_topology_host.add_child(_topology_note)
	_space_note = _label("")
	_space_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_topology_host.add_child(_space_note)
	space_page.add_child(_label("Board size"))
	var board := GridContainer.new()
	board.name = "ExplorerBoardSize"
	board.columns = 4
	space_page.add_child(board)
	for axis in "xyzw":
		var name_label := _label(axis.to_upper())
		name_label.autowrap_mode = TextServer.AUTOWRAP_OFF
		name_label.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		board.add_child(name_label)
		var minus := _button(board, "−", "board_%s_neg" % axis)
		var readout := _label("")
		readout.autowrap_mode = TextServer.AUTOWRAP_OFF
		readout.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		board.add_child(readout)
		var plus := _button(board, "+", "board_%s_pos" % axis)
		minus.tooltip_text = "Shrink the board along %s" % axis.to_upper()
		plus.tooltip_text = "Grow the board along %s" % axis.to_upper()
		_board_rows[axis] = [name_label, minus, readout, plus]
		_board_readouts[axis] = readout
		_board_buttons[axis] = [minus, plus]
	space_page.add_child(_label("Resizing restarts the piece at the centre. Play keeps its own setup."))
	# Two lines so a refusal reason is never cut off mid-word.
	_feedback = _readout(2)
	_update_dimension_controls()


func _update_dimension_controls() -> void:
	_title.text = "Explorer · %dD" % _dimension
	var profile: Dictionary = Contract.explorer_profile(_dimension)
	_topology_host.visible = true
	for index in _topologies.item_count:
		_topologies.set_item_disabled(index, _dimension != 2 and str(_topologies.get_item_metadata(index)) != "bounded")
	_space_note.text = "" if profile.capabilities.topology_selector else "%dD Explorer is bounded for now; other spaces are 2D only." % _dimension
	_space_note.visible = not _space_note.text.is_empty()
	for axis in _board_rows:
		for control in _board_rows[axis]:
			control.visible = "xyzw".find(axis) < _dimension
	var commands: Array = []
	for record in profile.axes + profile.rotation_planes:
		commands.append_array([record.negative_command, record.positive_command])
	for control in _dimensional_controls:
		control.visible = control.get_meta("practice_action") in commands


func update_topology(topology: String) -> void:
	# The dropdown changes itself on click before the model accepts or refuses,
	# so always snap it back to the active topology, even when nothing changed.
	for index in _topologies.item_count:
		if str(_topologies.get_item_metadata(index)) == topology:
			if _topologies.selected != index:
				_topologies.select(index)
	var signature := "%d|%s" % [_dimension, topology]
	if signature == _topology_signature:
		return
	_topology_signature = signature
	_square_surface = _dimension == 2 and topology in ["sphere_adjacent_positive", "projective"]
	for axis in _board_rows:
		for control in _board_rows[axis]:
			control.visible = "xyzw".find(axis) < _dimension and not (_square_surface and axis == "y")
	(_board_rows.x[0] as Label).text = "N" if _square_surface else "X"
	_undo.visible = _dimension == 2 and topology != "bounded"
	_topology_note.text = str({
		"mobius": "Left/right join with a flip; top/bottom stay open.",
		"klein": "Left/right wrap; top/bottom join with a flip.",
		"projective": "Experimental projective plane: both edge pairs join with flips.",
		"sphere_adjacent_positive": "Sphere: left joins top and right joins bottom, preserving tangent direction. A piece can block on itself at the corners.",
		"sphere_double_2d": "Sphere: chart A on the left, B on the right. Matching boundaries join. The gap is outside the surface.",
	}.get(topology, ""))
	_topology_note.visible = not _topology_note.text.is_empty()


func update_board(shape: Array, minima: Array, maxima: Array) -> void:
	for index in mini(shape.size(), 4):
		var axis := "xyzw"[index]
		_board_readouts[axis].text = str(int(shape[index]))
		if index < minima.size() and index < maxima.size():
			_board_buttons[axis][0].disabled = int(shape[index]) <= int(minima[index])
			_board_buttons[axis][1].disabled = int(shape[index]) >= int(maxima[index])
	if _square_surface and shape.size() >= 2 and minima.size() >= 2 and maxima.size() >= 2:
		_board_buttons.x[0].disabled = int(shape[0]) <= maxi(int(minima[0]), int(minima[1]))
		_board_buttons.x[1].disabled = int(shape[0]) >= mini(int(maxima[0]), int(maxima[1]))


func update_state(feedback: String) -> void:
	var message := feedback if feedback.begins_with("Object unchanged:") or "unavailable" in feedback or "does not fit" in feedback or "Retry pose restored" in feedback or "square board" in feedback else ""
	if _feedback.text != message:
		_feedback.text = message


func dimension() -> int:
	return _dimension


func update_piece_choices(names: Array, selected: int) -> void:
	if names != _piece_names:
		_piece_names = names.duplicate()
		_pieces.clear()
		for name in names:
			_pieces.add_item(str(name))
	_pieces.disabled = names.is_empty()
	if _pieces.selected != selected:
		_pieces.select(selected)
	_pieces.tooltip_text = str(names[selected]) if selected >= 0 and selected < names.size() else "Choose a piece"


func _page(title: String) -> VBoxContainer:
	var scroll := ScrollContainer.new()
	scroll.name = title
	# View is the primary panel: report its static controls to the outer
	# fit/scroll owner so all six planes are visible before any overflow.
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED if title == "View" else ScrollContainer.SCROLL_MODE_AUTO
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_tabs.add_child(scroll)
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(box)
	return box


# Live readouts must not resize the cockpit and restart its fit search. Reserve
# readable lines using the current font; longer text scrolls within that slot.
# The line counts are the pose/status presentation structure, not fit thresholds.
func _readout(lines: int) -> Label:
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var label := _label("")
	scroll.add_child(label)
	add_child(scroll)
	var update_height := func() -> void:
		var font_height := label.get_theme_font("font").get_height(label.get_theme_font_size("font_size"))
		scroll.custom_minimum_size.y = ceilf(font_height * lines + maxf(label.get_theme_constant("line_spacing"), 0) * (lines - 1))
	label.theme_changed.connect(update_height)
	update_height.call()
	return label


func _button(parent: Node, text: String, action: String) -> Button:
	var button := Button.new()
	button.text = text
	button.set_meta("practice_action", action)
	button.clip_text = true
	button.tooltip_text = "Rotate view %s %s90°" % [action.get_slice("_", 1).to_upper(), "−" if action.ends_with("neg") else "+"] if action.begins_with("basis_") else text
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.pressed.connect(func() -> void: requested.emit(action))
	parent.add_child(button)
	if action.begins_with("move_") or action.begins_with("rotate_"):
		_dimensional_controls.append(button)
	return button


func _label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return label
