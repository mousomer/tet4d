extends VBoxContainer

signal requested(action: String)
var _topology: OptionButton
var _topology_note: Label
var _dimension_controls: Array[Control] = []
var _rotation_title: Label
var _feedback: Label
var _tabs: TabContainer
var _dimension := 0
var _pieces: OptionButton
var _piece_names: Array = []
var view_controls_host: VBoxContainer
var _title: Label
var _four_dimensional_controls: Array[Control] = []


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
	_button(modes, "Play", "play")
	_topology = OptionButton.new()
	_topology.name = "TopologySelector"
	for label in ["Bounded · walls", "Cylinder X · X wraps", "Cylinder Y · Y wraps", "Torus · X/Y wrap"]:
		_topology.add_item(label)
	_topology.item_selected.connect(func(index: int) -> void: requested.emit("topology_%d" % index))
	add_child(_topology)
	_topology_note = _label("Changing topology resets the piece. View is preserved.")
	add_child(_topology_note)
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
	_button(object_page, "Replace piece", "replace")
	_button(object_page, "New target", "target")
	object_page.add_child(_label("Move piece"))
	var moves := GridContainer.new()
	moves.columns = 2
	object_page.add_child(moves)
	for axis in "xyzw":
		_button(moves, "−" + axis.to_upper(), "move_%s_neg" % axis)
		_button(moves, "+" + axis.to_upper(), "move_%s_pos" % axis)
	_rotation_title = _label("Rotate object · quarter turns")
	object_page.add_child(_rotation_title)
	var rotations := GridContainer.new()
	rotations.columns = 2
	object_page.add_child(rotations)
	for plane in ["xy", "xz", "yz", "xw", "yw", "zw"]:
		_button(rotations, plane.to_upper() + " −", "rotate_%s_neg" % plane)
		_button(rotations, plane.to_upper() + " +", "rotate_%s_pos" % plane)
	_button(object_page, "Retry object", "retry")
	_feedback = _readout(1)
	_update_dimension_controls()


func _update_dimension_controls() -> void:
	_title.text = "Explorer · %dD" % _dimension
	_topology.visible = _dimension == 2
	_topology_note.visible = _dimension == 2
	_rotation_title.visible = _dimension != 2
	for control in _dimension_controls:
		var action: String = control.get_meta("practice_action")
		control.visible = _dimension != 2 or (action.begins_with("move_") and action.get_slice("_", 1) in ["x", "y"])
	for control in _four_dimensional_controls:
		control.visible = _dimension == 4


func update_state(feedback: String) -> void:
	var message := feedback if _dimension == 2 or feedback.begins_with("Object unchanged:") or "unavailable" in feedback or "does not fit" in feedback else ""
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


func _button(parent: Node, text: String, action: String) -> void:
	var button := Button.new()
	button.text = text
	button.set_meta("practice_action", action)
	button.clip_text = true
	button.tooltip_text = "Rotate view %s %s90°" % [action.get_slice("_", 1).to_upper(), "−" if action.ends_with("neg") else "+"] if action.begins_with("basis_") else text
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.pressed.connect(func() -> void: requested.emit(action))
	parent.add_child(button)
	if action.begins_with("move_") or action.begins_with("rotate_") or action == "target":
		_dimension_controls.append(button)
	if action.begins_with("slice_") or (action.begins_with("move_") or action.begins_with("rotate_")) and "w" in action:
		_four_dimensional_controls.append(button)


func _label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return label
