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
