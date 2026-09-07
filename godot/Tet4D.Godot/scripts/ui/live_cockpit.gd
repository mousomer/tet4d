extends VBoxContainer

class_name LiveCockpit

var header_slot: VBoxContainer
var primary_board_surface: VBoxContainer
var control_deck: HBoxContainer
var piece_controls: VBoxContainer
var view_controls: VBoxContainer
var piece_state: VBoxContainer


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
	control_deck = HBoxContainer.new()
	control_deck.name = "ControlDeck"
	control_deck.visible = false
	control_deck.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	control_deck.mouse_filter = Control.MOUSE_FILTER_IGNORE
	control_deck.add_theme_constant_override("separation", 10)
	add_child(control_deck)
	for specification in [["PieceControls", 42], ["ViewControls", 33], ["PieceState", 25]]:
		var module := _slot(str(specification[0]))
		module.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		module.size_flags_stretch_ratio = float(specification[1])
		control_deck.add_child(module)
		match str(specification[0]):
			"PieceControls": piece_controls = module
			"ViewControls": view_controls = module
			"PieceState": piece_state = module


func set_control_deck_visible(enabled: bool, density: String = "standard") -> void:
	control_deck.visible = enabled
	control_deck.custom_minimum_size.y = 150.0 if density == "compact" else (220.0 if density == "detailed" else 190.0)


func deterministic_snapshot() -> Dictionary:
	return {
		"owner": "LiveCockpit",
		"slots": [str(header_slot.name), str(primary_board_surface.name), str(control_deck.name)],
		"deck_modules": [str(piece_controls.name), str(view_controls.name), str(piece_state.name)],
		"deck_ratios": [piece_controls.size_flags_stretch_ratio, view_controls.size_flags_stretch_ratio, piece_state.size_flags_stretch_ratio],
		"deck_visible": control_deck.visible,
		"rect": get_global_rect(),
		"header_rect": header_slot.get_global_rect(),
		"primary_rect": primary_board_surface.get_global_rect(),
		"deck_rect": control_deck.get_global_rect(),
	}


func _slot(slot_name: String) -> VBoxContainer:
	var result := VBoxContainer.new()
	result.name = slot_name
	result.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return result
