extends RefCounted

class_name TraceSnapshotExtractor


static func extract(document: TraceDocument, frame_index: int) -> Dictionary:
	var frame_total := document.frame_count()
	var snapshot := {
		"trace_type": document.trace_type,
		"case_id": document.case_id,
		"dimension": document.dimension,
		"frame_count": frame_total,
		"frame_index": 0,
		"state_hash": document.final.get("state_hash", ""),
		"board_shape": document.board_shape.duplicate(),
		"active_cells": [],
		"locked_cells": [],
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
		"event_lines": [],
		"metadata_lines": [],
		"diagnostics_lines": [],
		"energy_lines": [],
	}
	if frame_total == 0:
		snapshot["metadata_lines"] = ["No frames in trace."]
		return snapshot

	var clamped_index := clampi(frame_index, 0, frame_total - 1)
	var frame := document.frame_at(clamped_index)
	snapshot["frame_index"] = clamped_index
	snapshot["state_hash"] = str(frame.get("state_hash", document.final.get("state_hash", "")))

	match document.trace_type:
		"topology":
			TopologySnapshotExtractor.extract(document, frame, snapshot)
		"gameplay":
			GameplaySnapshotExtractor.extract(document, frame, snapshot)
		"endgame":
			EndgameSnapshotExtractor.extract(document, frame, snapshot)
		_:
			snapshot["metadata_lines"] = [
				"Unknown trace type: %s" % document.trace_type,
				"state_hash: %s" % snapshot.get("state_hash", ""),
			]
			snapshot["diagnostics_lines"] = [_summary_of(frame)]
	return snapshot


static func nested_value(source, path: Array, default_value = null):
	var current = source
	for key in path:
		if current is Dictionary and current.has(key):
			current = current[key]
		else:
			return default_value
	return current


static func nested_dict(source, path: Array) -> Dictionary:
	var value = nested_value(source, path, {})
	return value if value is Dictionary else {}


static func nested_array(source, path: Array) -> Array:
	var value = nested_value(source, path, [])
	return value if value is Array else []


static func append_cell(target: Array, label: String, color_id: int, position: Array, locked: bool) -> void:
	if position.is_empty():
		return
	target.append(
		{
			"label": label,
			"color_id": color_id,
			"position": position.duplicate(),
			"locked": locked,
		}
	)


static func append_marker(target: Array, kind: String, label: String, position: Array) -> void:
	if position.is_empty():
		return
	target.append(
		{
			"kind": kind,
			"label": label,
			"position": position.duplicate(),
		}
	)


static func particle_position(particles: Array, particle_id: int) -> Array:
	for particle in particles:
		if int(particle.get("particle_id", -1)) == particle_id:
			return particle.get("position", [])
	return []


static func first_position(items: Array) -> Array:
	if items.is_empty():
		return []
	return items[0].get("position", [])


static func kv_lines(pairs: Array) -> Array:
	var lines: Array = []
	for pair in pairs:
		if pair.size() < 2:
			continue
		lines.append("%s: %s" % [pair[0], pair[1]])
	return lines


static func summary_lines(value, prefix: String = "") -> Array:
	var summary := _summary_of(value)
	if prefix.is_empty():
		return [summary]
	return ["%s: %s" % [prefix, summary]]


static func _summary_of(value) -> String:
	if value == null:
		return "null"
	if value is Dictionary or value is Array:
		return JSON.stringify(value)
	return str(value)
