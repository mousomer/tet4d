extends RefCounted

const PanelScript = preload("res://scripts/ui/practice_explorer_panel.gd")

signal requested(action: String)

var panel: PanelScript
var active := false


# Returns whether the HUD needs to update its shell chrome and helper layout.
func update_panel(host: VBoxContainer, dimension: int, feedback: String, pieces: Array, selected_piece: int, topology: String, board: Array, board_minima: Array, board_maxima: Array, prepare_panel: Callable) -> bool:
	var show := dimension in [2, 3, 4]
	var same_dimension: bool = show and active and panel != null and panel.dimension() == dimension
	active = show
	if show and panel == null:
		panel = PanelScript.new()
		panel.name = "PracticeExplorerPanel"
		panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
		host.add_child(panel)
		panel.requested.connect(func(action: String) -> void: requested.emit(action))
	if panel != null:
		panel.visible = show
	if show:
		if not same_dimension:
			panel.configure(dimension)
		panel.update_state(feedback)
		panel.update_piece_choices(pieces, selected_piece)
		panel.update_topology(topology)
		panel.update_board(board, board_minima, board_maxima)
		if not same_dimension:
			prepare_panel.call(panel)
	return not same_dimension


func view_host(live_host: Control) -> Control:
	return panel.view_controls_host if active and panel != null else live_host


func place_view_helper(helper: Control, live_host: Control) -> void:
	var host := view_host(live_host)
	if helper.get_parent() != host:
		helper.reparent(host, false)
	helper.set_detached_layout(active)
	helper.set_fit_to_content(active)
