extends RefCounted

class_name GhostPieceModel

var available := false
var dimension := 0
var piece_name := ""
var color_id := 0
var canonical_cells: Array = []
var source_revision := ""
var geometry_revision := 0


func configure(payload: Dictionary, revision: String) -> bool:
	var parsed := _parse_cells(payload)
	if parsed.is_empty():
		clear()
		return false
	var next_dimension := int(payload.get("dimension", 0))
	var signature := "%d|%s|%s" % [next_dimension, str(payload.get("piece_name", "")), JSON.stringify(parsed)]
	var previous_signature := "%d|%s|%s" % [dimension, piece_name, JSON.stringify(canonical_cells)]
	if not available or signature != previous_signature:
		geometry_revision += 1
	available = true
	dimension = next_dimension
	piece_name = str(payload.get("piece_name", ""))
	color_id = int(payload.get("color_id", 0))
	canonical_cells = parsed
	source_revision = revision
	return true


func clear() -> void:
	available = false
	dimension = 0
	piece_name = ""
	color_id = 0
	canonical_cells = []
	source_revision = ""


func render_cells(active_cells: Array) -> Array:
	if not available or _positions(active_cells) == canonical_cells:
		return []
	var result: Array = []
	for cell in canonical_cells:
		result.append({"position": cell.duplicate(), "color_id": color_id, "label": "Ghost", "locked": false})
	return result


func deterministic_snapshot() -> Dictionary:
	return {
		"available": available,
		"dimension": dimension,
		"piece_name": piece_name,
		"color_id": color_id,
		"canonical_cells": canonical_cells.duplicate(true),
		"source_revision": source_revision,
		"geometry_revision": geometry_revision,
	}


func _parse_cells(payload: Dictionary) -> Array:
	if not bool(payload.get("ok", false)) or str(payload.get("status", "")) != "destination":
		return []
	var rank := int(payload.get("dimension", 0))
	if rank < 2 or rank > 4:
		return []
	var cells_value = payload.get("cells", [])
	if not cells_value is Array or cells_value.is_empty():
		return []
	var parsed: Array = []
	for value in cells_value:
		if not value is Array or value.size() != rank:
			return []
		var coord: Array = []
		for component in value:
			if typeof(component) != TYPE_INT:
				return []
			coord.append(int(component))
		if parsed.has(coord):
			return []
		parsed.append(coord)
	parsed.sort_custom(func(left: Array, right: Array) -> bool: return _coord_key(left) < _coord_key(right))
	return parsed


func _positions(cells: Array) -> Array:
	var result: Array = []
	for cell in cells:
		if not cell is Dictionary:
			return []
		var position = cell.get("position", [])
		if not position is Array or position.size() != dimension:
			return []
		result.append(position.duplicate())
	result.sort_custom(func(left: Array, right: Array) -> bool: return _coord_key(left) < _coord_key(right))
	return result


func _coord_key(coord: Array) -> String:
	var parts: PackedStringArray = []
	for value in coord:
		parts.append("%+012d" % int(value))
	return ":".join(parts)
