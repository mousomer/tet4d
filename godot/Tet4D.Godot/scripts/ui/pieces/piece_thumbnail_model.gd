extends RefCounted

class_name PieceThumbnailModel

var dimension := 0
var piece_set_id := ""
var piece_name := ""
var color_id := 0
var canonical_cells: Array = []
var _drawing_groups: Array = []


func configure(payload: Dictionary) -> bool:
	_reset()
	if not bool(payload.get("ok", false)) or payload.get("status") != "piece":
		return false
	var raw_dimension = payload.get("dimension")
	var raw_piece_set = payload.get("piece_set_id")
	var raw_name = payload.get("piece_name")
	var raw_color = payload.get("color_id")
	var raw_cells = payload.get("cells")
	if typeof(raw_dimension) != TYPE_INT or int(raw_dimension) not in [2, 3, 4]:
		return false
	if typeof(raw_piece_set) != TYPE_STRING or str(raw_piece_set).strip_edges().is_empty():
		return false
	if typeof(raw_name) != TYPE_STRING or str(raw_name).strip_edges().is_empty():
		return false
	if typeof(raw_color) != TYPE_INT or int(raw_color) < 0:
		return false
	if typeof(raw_cells) != TYPE_ARRAY or raw_cells.is_empty():
		return false
	dimension = int(raw_dimension)
	piece_set_id = str(raw_piece_set)
	piece_name = str(raw_name)
	color_id = int(raw_color)
	var seen := {}
	for raw_cell in raw_cells:
		if typeof(raw_cell) != TYPE_ARRAY or raw_cell.size() != dimension:
			_reset()
			return false
		var cell: Array = []
		for raw_value in raw_cell:
			if typeof(raw_value) != TYPE_INT:
				_reset()
				return false
			cell.append(int(raw_value))
		var key := ",".join(cell)
		if seen.has(key):
			_reset()
			return false
		seen[key] = true
		canonical_cells.append(cell)
	canonical_cells.sort_custom(_coord_less)
	_build_drawing_groups()
	return true


func is_available() -> bool:
	return dimension in [2, 3, 4] and not canonical_cells.is_empty()


func drawing_groups() -> Array:
	return _drawing_groups.duplicate(true)


func cache_signature() -> String:
	return JSON.stringify([
		dimension,
		piece_set_id,
		piece_name,
		color_id,
		canonical_cells,
	])


func deterministic_snapshot() -> Dictionary:
	return {
		"available": is_available(),
		"dimension": dimension,
		"piece_set_id": piece_set_id,
		"piece_name": piece_name,
		"color_id": color_id,
		"canonical_cells": canonical_cells.duplicate(true),
		"drawing_groups": drawing_groups(),
	}


func _build_drawing_groups() -> void:
	if dimension < 4:
		_drawing_groups = [{"slice_coordinate": 0, "label": "", "cells": canonical_cells.duplicate(true)}]
		return
	var by_w := {}
	for cell in canonical_cells:
		var w := int(cell[3])
		if not by_w.has(w):
			by_w[w] = []
		by_w[w].append([int(cell[0]), int(cell[1]), int(cell[2])])
	var coordinates: Array = by_w.keys()
	coordinates.sort()
	for coordinate in coordinates:
		var cells: Array = by_w[coordinate]
		cells.sort_custom(_coord_less)
		_drawing_groups.append({
			"slice_coordinate": int(coordinate),
			"label": "W=%+d" % int(coordinate),
			"cells": cells,
		})


func _reset() -> void:
	dimension = 0
	piece_set_id = ""
	piece_name = ""
	color_id = 0
	canonical_cells = []
	_drawing_groups = []


func _coord_less(left: Array, right: Array) -> bool:
	for index in range(min(left.size(), right.size())):
		if int(left[index]) != int(right[index]):
			return int(left[index]) < int(right[index])
	return left.size() < right.size()
