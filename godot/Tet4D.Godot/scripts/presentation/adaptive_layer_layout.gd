extends RefCounted

class_name AdaptiveLayerLayout

var layer_count := 1
var columns := 1
var rows := 1
var tile_width := 1.0
var tile_height := 1.0
var horizontal_gap := 2.0
var vertical_gap := 2.0


func configure(count: int, local_width: float, local_height: float, viewport_aspect: float = 1.7777778) -> void:
	layer_count = maxi(count, 1)
	tile_width = maxf(local_width, 1.0)
	tile_height = maxf(local_height, 1.0)
	if layer_count <= 3:
		columns = layer_count
	elif layer_count == 4:
		columns = 2
	else:
		var target := sqrt(float(layer_count) * maxf(viewport_aspect, 0.5) * tile_height / tile_width)
		columns = clampi(int(round(target)), 2, layer_count)
	rows = int(ceil(float(layer_count) / float(columns)))


func offset_for_layer(index: int) -> Vector3:
	var safe_index := clampi(index, 0, layer_count - 1)
	var column := safe_index % columns
	var row := safe_index / columns
	return Vector3(
		float(column) * (tile_width + horizontal_gap),
		-float(row) * (tile_height + vertical_gap),
		0.0
	)


func snapshot() -> Dictionary:
	var assignments := []
	for index in range(layer_count):
		var offset := offset_for_layer(index)
		assignments.append({"layer": index, "column": index % columns, "row": index / columns, "offset": offset})
	return {"layer_count": layer_count, "columns": columns, "rows": rows, "assignments": assignments}
