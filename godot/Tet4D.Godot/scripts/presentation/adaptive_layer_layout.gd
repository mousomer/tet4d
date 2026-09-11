extends RefCounted

class_name AdaptiveLayerLayout

const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")

const MIN_SLICE_GUTTER := 3.0
const MAX_SLICE_GUTTER := 5.0
const MIN_VERTICAL_SLICE_GUTTER := 4.0
const MAX_VERTICAL_SLICE_GUTTER := 6.0
const HORIZONTAL_GUTTER_RATIO := 0.45
const VERTICAL_GUTTER_RATIO := 0.36
const DEFAULT_VIEWPORT_SIZE := Vector2(1600.0, 960.0)
const SCALE_TIE_EPSILON := 0.0001
const NON_PREFERRED_ROW_SCALE_WEIGHT := 0.50
const FINAL_ROW_IMBALANCE_WEIGHT := 0.30

var layer_count := 1
var columns := 1
var rows := 1
var tile_width := 1.0
var tile_height := 1.0
var horizontal_gap := 2.0
var vertical_gap := 2.0
var screen_row_y_per_world_x := 0.0
var viewport_size := DEFAULT_VIEWPORT_SIZE
var projected_board_scale := 1.0
var unused_viewport_area := 0.0


func configure(
	count: int,
	local_width: float,
	local_height: float,
	viewport_aspect: float = 1.7777778,
	spacing_scale: float = 1.0,
	local_depth: float = 1.0,
	screen_row_slope: float = 0.0,
	available_viewport_size: Vector2 = Vector2.ZERO
) -> void:
	layer_count = maxi(count, 1)
	var supported_envelope := SliceLocalOrientationScript.normal_gameplay_extent_envelope(
		Vector3(maxf(local_width, 1.0), maxf(local_height, 1.0), maxf(local_depth, 1.0))
	)
	tile_width = supported_envelope.x
	tile_height = supported_envelope.y
	horizontal_gap = clampf(tile_width * HORIZONTAL_GUTTER_RATIO, MIN_SLICE_GUTTER, MAX_SLICE_GUTTER) * spacing_scale
	vertical_gap = clampf(tile_height * VERTICAL_GUTTER_RATIO, MIN_VERTICAL_SLICE_GUTTER, MAX_VERTICAL_SLICE_GUTTER) * spacing_scale
	screen_row_y_per_world_x = screen_row_slope
	viewport_size = available_viewport_size if available_viewport_size.x > 0.0 and available_viewport_size.y > 0.0 else Vector2(maxf(viewport_aspect, 0.5) * DEFAULT_VIEWPORT_SIZE.y, DEFAULT_VIEWPORT_SIZE.y)
	_select_grid()


func anchor_for_layer(index: int) -> Vector3:
	var safe_index := clampi(index, 0, layer_count - 1)
	return _anchor_for_layer_in_grid(safe_index, columns)


func _anchor_for_layer_in_grid(index: int, candidate_columns: int) -> Vector3:
	var column := index % candidate_columns
	var row := index / candidate_columns
	return Vector3(
		float(column) * (tile_width + horizontal_gap),
		-float(row) * (tile_height + vertical_gap) + float(column) * (tile_width + horizontal_gap) * screen_row_y_per_world_x,
		0.0
	)


func offset_for_layer(index: int) -> Vector3:
	# Compatibility alias for pre-54E-2a callers. Layout owns anchor points;
	# the value is not a local basis vector or gameplay direction.
	return anchor_for_layer(index)


func tile_rect_for_layer(index: int) -> Rect2:
	var anchor := anchor_for_layer(index)
	return Rect2(anchor.x - tile_width * 0.5, anchor.y - tile_height * 0.5, tile_width, tile_height)


func snapshot() -> Dictionary:
	var assignments := []
	for index in range(layer_count):
		var anchor := anchor_for_layer(index)
		assignments.append({
			"layer": index,
			"column": index % columns,
			"row": index / columns,
			"anchor": anchor,
			"offset": anchor,
		})
	return {
		"layer_count": layer_count,
		"columns": columns,
		"rows": rows,
		"tile_width": tile_width,
		"tile_height": tile_height,
		"horizontal_gap": horizontal_gap,
		"vertical_gap": vertical_gap,
		"viewport_size": viewport_size,
		"projected_board_scale": projected_board_scale,
		"unused_viewport_area": unused_viewport_area,
		# Reported, not configurable: row-major assignment from column 0 always
		# leaves a partial final row left aligned.
		"partial_row_alignment": "left",
		"tile_rects": range(layer_count).map(func(index): return tile_rect_for_layer(index)),
		"content_rect": _layout_rect(columns),
		"assignments": assignments,
	}


func candidate_snapshot(candidate_columns: int) -> Dictionary:
	if candidate_columns < 1 or candidate_columns > layer_count:
		return {}
	return _candidate(candidate_columns).duplicate(true)


func _select_grid() -> void:
	var best := {}
	for candidate_columns in range(1, layer_count + 1):
		var candidate := _candidate(candidate_columns)
		if best.is_empty() or _candidate_is_better(candidate, best):
			best = candidate
	columns = int(best.get("columns", 1))
	rows = int(best.get("rows", 1))
	projected_board_scale = float(best.get("projected_board_scale", 1.0))
	unused_viewport_area = float(best.get("unused_viewport_area", 0.0))


func _candidate(candidate_columns: int) -> Dictionary:
	var candidate_rows := int(ceil(float(layer_count) / float(candidate_columns)))
	var content_rect := _layout_rect(candidate_columns)
	var content_width := content_rect.size.x
	var content_height := content_rect.size.y
	var scale := minf(viewport_size.x / maxf(content_width, 0.001), viewport_size.y / maxf(content_height, 0.001))
	var projected_area := content_width * scale * content_height * scale
	var last_row_count := layer_count - (candidate_rows - 1) * candidate_columns
	var last_row_imbalance := float(candidate_columns - last_row_count) / float(candidate_columns)
	var preferred_row_count := layer_count <= 4 or candidate_rows == 2
	return {
		"columns": candidate_columns,
		"rows": candidate_rows,
		"projected_board_scale": scale,
		"selection_score": scale * (1.0 if preferred_row_count else NON_PREFERRED_ROW_SCALE_WEIGHT) * (1.0 - FINAL_ROW_IMBALANCE_WEIGHT * last_row_imbalance),
		"unused_viewport_area": maxf(viewport_size.x * viewport_size.y - projected_area, 0.0),
		"last_row_imbalance": last_row_imbalance,
		"content_rect": content_rect,
	}


func _layout_rect(candidate_columns: int) -> Rect2:
	var result := Rect2()
	for index in range(layer_count):
		var anchor := _anchor_for_layer_in_grid(index, candidate_columns)
		var tile_rect := Rect2(anchor.x - tile_width * 0.5, anchor.y - tile_height * 0.5, tile_width, tile_height)
		result = tile_rect if index == 0 else result.merge(tile_rect)
	return result


func _candidate_is_better(candidate: Dictionary, current: Dictionary) -> bool:
	var candidate_score := float(candidate.get("selection_score", 0.0))
	var current_score := float(current.get("selection_score", 0.0))
	if candidate_score > current_score + SCALE_TIE_EPSILON:
		return true
	if current_score > candidate_score + SCALE_TIE_EPSILON:
		return false
	var candidate_scale := float(candidate.get("projected_board_scale", 0.0))
	var current_scale := float(current.get("projected_board_scale", 0.0))
	if not is_equal_approx(candidate_scale, current_scale):
		return candidate_scale > current_scale
	var candidate_imbalance := float(candidate.get("last_row_imbalance", 1.0))
	var current_imbalance := float(current.get("last_row_imbalance", 1.0))
	if not is_equal_approx(candidate_imbalance, current_imbalance):
		return candidate_imbalance < current_imbalance
	var candidate_unused := float(candidate.get("unused_viewport_area", INF))
	var current_unused := float(current.get("unused_viewport_area", INF))
	if not is_equal_approx(candidate_unused, current_unused):
		return candidate_unused < current_unused
	return int(candidate.get("columns", layer_count)) < int(current.get("columns", layer_count))
