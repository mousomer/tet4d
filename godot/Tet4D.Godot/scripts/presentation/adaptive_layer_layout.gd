extends RefCounted

class_name AdaptiveLayerLayout

const MIN_SLICE_GUTTER := 3.0
const MAX_SLICE_GUTTER := 5.0
const MIN_VERTICAL_SLICE_GUTTER := 4.0
const MAX_VERTICAL_SLICE_GUTTER := 6.0
const HORIZONTAL_GUTTER_RATIO := 0.45
const VERTICAL_GUTTER_RATIO := 0.36

var layer_count := 1
var columns := 1
var rows := 1
var tile_width := 1.0
var tile_height := 1.0
var horizontal_gap := 2.0
var vertical_gap := 2.0


func configure(
	count: int,
	local_width: float,
	local_height: float,
	viewport_aspect: float = 1.7777778,
	spacing_scale: float = 1.0
) -> void:
	layer_count = maxi(count, 1)
	tile_width = maxf(local_width, 1.0)
	tile_height = maxf(local_height, 1.0)
	horizontal_gap = clampf(tile_width * HORIZONTAL_GUTTER_RATIO, MIN_SLICE_GUTTER, MAX_SLICE_GUTTER) * spacing_scale
	vertical_gap = clampf(tile_height * VERTICAL_GUTTER_RATIO, MIN_VERTICAL_SLICE_GUTTER, MAX_VERTICAL_SLICE_GUTTER) * spacing_scale
	if layer_count <= 3:
		columns = layer_count
	elif layer_count == 4:
		columns = 2
	else:
		var target := sqrt(float(layer_count) * maxf(viewport_aspect, 0.5) * tile_height / tile_width)
		columns = clampi(int(round(target)), 2, layer_count)
	rows = int(ceil(float(layer_count) / float(columns)))


func anchor_for_layer(index: int) -> Vector3:
	var safe_index := clampi(index, 0, layer_count - 1)
	var column := safe_index % columns
	var row := safe_index / columns
	return Vector3(
		float(column) * (tile_width + horizontal_gap),
		-float(row) * (tile_height + vertical_gap),
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
		"assignments": assignments,
	}
