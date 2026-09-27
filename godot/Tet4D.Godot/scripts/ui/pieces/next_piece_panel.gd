extends PanelContainer

class_name NextPiecePanel

const PieceThumbnailModelScript = preload("res://scripts/ui/pieces/piece_thumbnail_model.gd")
const PieceThumbnailScript = preload("res://scripts/ui/pieces/piece_thumbnail.gd")
const PiecePreviewLayoutScript = preload("res://scripts/ui/pieces/piece_preview_layout.gd")

var _model = PieceThumbnailModelScript.new()
var _thumbnail
var _piece_label: Label
var _status_label: Label
var _preview_signature := ""
var _margin: MarginContainer
var _content: VBoxContainer


func _init() -> void:
	name = "NextPiecePanel"
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(0, PiecePreviewLayoutScript.PANEL_MIN_HEIGHT)
	theme_type_variation = "ViewportFrame"
	set_meta("semantic_role", "passive_preview_panel")
	_margin = MarginContainer.new()
	add_child(_margin)
	_content = VBoxContainer.new()
	_margin.add_child(_content)
	var header := HBoxContainer.new()
	_content.add_child(header)
	var title := Label.new()
	title.name = "NextPieceTitle"
	title.text = "NEXT"
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", 13)
	header.add_child(title)
	_piece_label = Label.new()
	_piece_label.name = "NextPieceName"
	_piece_label.text = "—"
	_piece_label.theme_type_variation = "SecondaryLabel"
	_piece_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	# Piece names run to nine characters. Letting the name set the panel minimum
	# made the cockpit deck reflow whenever a longer name arrived, pushing
	# NEXT/HOLD below the standard window (Stage 56H-R3.1). The name now yields
	# to its panel; the full name stays in the tooltip.
	_piece_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_piece_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_piece_label.mouse_filter = Control.MOUSE_FILTER_PASS
	header.add_child(_piece_label)
	_thumbnail = PieceThumbnailScript.new()
	_content.add_child(_thumbnail)
	_status_label = Label.new()
	_status_label.name = "NextPieceStatus"
	_status_label.text = "Waiting for live session"
	_status_label.theme_type_variation = "DimLabel"
	_status_label.add_theme_font_size_override("font_size", 11)
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_content.add_child(_status_label)
	PiecePreviewLayoutScript.apply_compact(self, _margin, _content, _thumbnail, 0)


func set_preview(payload: Dictionary) -> bool:
	var candidate = PieceThumbnailModelScript.new()
	if not candidate.configure(payload):
		_model = PieceThumbnailModelScript.new()
		_preview_signature = ""
		_thumbnail.clear()
		_piece_label.text = "—"
		_piece_label.tooltip_text = ""
		_status_label.text = "Preview unavailable"
		PiecePreviewLayoutScript.apply_compact(self, _margin, _content, _thumbnail, 0)
		return false
	var candidate_signature: String = candidate.cache_signature()
	if candidate_signature != _preview_signature:
		_model = candidate
		_preview_signature = candidate_signature
		_thumbnail.set_model(_model)
	_piece_label.text = _model.piece_name
	_piece_label.tooltip_text = _model.piece_name
	_status_label.text = "%dD · %d cells" % [_model.dimension, _model.canonical_cells.size()]
	PiecePreviewLayoutScript.apply_compact(self, _margin, _content, _thumbnail, _model.dimension)
	return true


func clear_preview() -> void:
	set_preview({})


func set_style_manager(style_manager) -> void:
	_thumbnail.set_style_manager(style_manager)


func deterministic_snapshot() -> Dictionary:
	return {
		"visible": visible,
		"piece_name_text": _piece_label.text,
		"status_text": _status_label.text,
		"minimum_height": custom_minimum_size.y,
		"preview_signature": _preview_signature,
		"model": _model.deterministic_snapshot(),
		"thumbnail": _thumbnail.deterministic_snapshot(),
	}
