extends RefCounted

class_name PiecePreviewLayout

# NEXT and HOLD consume this one compact cockpit geometry convention. Their
# semantic models and the shared thumbnail renderer remain separate owners.
const PANEL_MIN_HEIGHT := 116.0
const PANEL_4D_MIN_HEIGHT := 132.0
const HORIZONTAL_MARGIN := 6
const VERTICAL_MARGIN := 5
const CONTENT_SEPARATION := 3


static func apply_compact(
	panel: PanelContainer,
	margin: MarginContainer,
	content: VBoxContainer,
	thumbnail,
	dimension: int
) -> void:
	panel.custom_minimum_size.y = PANEL_4D_MIN_HEIGHT if dimension == 4 else PANEL_MIN_HEIGHT
	margin.add_theme_constant_override("margin_left", HORIZONTAL_MARGIN)
	margin.add_theme_constant_override("margin_top", VERTICAL_MARGIN)
	margin.add_theme_constant_override("margin_right", HORIZONTAL_MARGIN)
	margin.add_theme_constant_override("margin_bottom", VERTICAL_MARGIN)
	content.add_theme_constant_override("separation", CONTENT_SEPARATION)
	thumbnail.set_compact_cockpit(true)


# The longest built-in piece name. Sizing to it instead of the current piece
# keeps a host from changing width every time a new piece arrives.
const PIECE_NAME_REFERENCE := "RIBBON8_B"


# Width at which the header shows a full-length piece name instead of trimming
# it. The name label itself yields to its panel (its minimum is the ellipsis),
# so a host that can spare the width has to ask for it.
static func preferred_width(panel: Control, piece_label: Label) -> float:
	var header := piece_label.get_parent() as BoxContainer
	if header == null:
		return panel.get_combined_minimum_size().x
	var font := piece_label.get_theme_font("font")
	var needed := font.get_string_size(PIECE_NAME_REFERENCE, HORIZONTAL_ALIGNMENT_LEFT, -1, piece_label.get_theme_font_size("font_size")).x
	var visible_children := 0
	for child in header.get_children():
		if child is Control and (child as Control).visible:
			visible_children += 1
			if child != piece_label:
				needed += (child as Control).get_combined_minimum_size().x
	needed += float(maxi(visible_children - 1, 0) * header.get_theme_constant("separation"))
	return panel.get_combined_minimum_size().x - header.get_combined_minimum_size().x + needed
