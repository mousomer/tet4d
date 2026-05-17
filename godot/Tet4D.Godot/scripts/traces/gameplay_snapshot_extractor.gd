extends RefCounted

class_name GameplaySnapshotExtractor


static func extract(document: TraceDocument, frame: Dictionary, snapshot: Dictionary) -> void:
	var active_piece: Dictionary = frame.get("active_piece", {})
	var active_cells: Array = active_piece.get("cells", [])
	var active_color_id := int(active_piece.get("color_id", 1))
	for cell in active_cells:
		TraceSnapshotExtractor.append_cell(
			snapshot["active_cells"],
			"Active",
			active_color_id,
			{"position": cell},
			false
		)

	for cell in frame.get("locked_cells", []):
		TraceSnapshotExtractor.append_cell(
			snapshot["locked_cells"],
			"Locked",
			0,
			{"position": cell},
			true
		)

	var event_position := TraceSnapshotExtractor.first_position(snapshot["active_cells"])
	var topology_event: Variant = frame.get("topology_event", null)
	if topology_event is Dictionary:
		for traversal in topology_event.get("traversals", []):
			TraceSnapshotExtractor.append_marker(
				snapshot["event_markers"],
				"topology",
				TraceSnapshotExtractor._summary_of(traversal),
				event_position
			)
			snapshot["event_lines"].append(TraceSnapshotExtractor._summary_of(traversal))
	elif topology_event != null:
		snapshot["event_lines"].append(TraceSnapshotExtractor._summary_of(topology_event))

	snapshot["metadata_lines"] = TraceSnapshotExtractor.kv_lines(
		[
			["mode", "Gameplay Replay"],
			["case_id", document.case_id],
			["command", frame.get("command_id", "")],
			["score", frame.get("score", "")],
			["lines", frame.get("lines", "")],
			["locked_count", TraceSnapshotExtractor.nested_value(frame, ["drop_lock_status", "locked_cell_count"], "")],
			["dimension", document.dimension],
			["state_hash", snapshot.get("state_hash", "")],
		]
	)
	var diagnostics_lines: Array = []
	var drop_lock_status: Variant = frame.get("drop_lock_status", {})
	if drop_lock_status is Dictionary:
		for key in ["game_over", "locked_cell_count", "soft_drop_legal_after"]:
			if drop_lock_status.has(key):
				diagnostics_lines.append("%s: %s" % [key, drop_lock_status.get(key)])
	var legal_moves: Variant = frame.get("legal_moves", {})
	if legal_moves is Dictionary and legal_moves.has("moves"):
		diagnostics_lines.append("legal_moves: %s" % TraceSnapshotExtractor._summary_of(legal_moves.get("moves")))
	if topology_event != null and snapshot["event_lines"].is_empty():
		diagnostics_lines.append("topology_event: %s" % TraceSnapshotExtractor._summary_of(topology_event))
	snapshot["diagnostics_lines"] = diagnostics_lines
