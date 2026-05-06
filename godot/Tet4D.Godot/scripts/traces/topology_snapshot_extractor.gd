extends RefCounted

class_name TopologySnapshotExtractor


static func extract(document: TraceDocument, frame: Dictionary, snapshot: Dictionary) -> void:
	var before_probe := TraceSnapshotExtractor.nested_array(frame, ["before", "probe_coord"])
	var after_probe := TraceSnapshotExtractor.nested_array(frame, ["after", "probe_coord"])
	TraceSnapshotExtractor.append_marker(snapshot["probe_markers"], "probe_before", "Probe Before", before_probe)
	TraceSnapshotExtractor.append_marker(snapshot["probe_markers"], "probe_after", "Probe After", after_probe)

	for moved_cell in TraceSnapshotExtractor.nested_array(frame, ["piece_transport", "moved_cells"]):
		TraceSnapshotExtractor.append_cell(snapshot["active_cells"], "Transport", 1, moved_cell, false)

	var traversal := TraceSnapshotExtractor.nested_dict(frame, ["probe_result", "traversal"])
	if not traversal.is_empty():
		TraceSnapshotExtractor.append_marker(
			snapshot["event_markers"],
			"seam",
			TraceSnapshotExtractor._summary_of(traversal),
			after_probe if not after_probe.is_empty() else before_probe
		)
		snapshot["event_lines"].append(TraceSnapshotExtractor._summary_of(traversal))

	for cell_step in TraceSnapshotExtractor.nested_array(frame, ["piece_transport", "cell_steps"]):
		var cell_traversal := cell_step.get("traversal", {})
		if cell_traversal.is_empty():
			continue
		TraceSnapshotExtractor.append_marker(
			snapshot["event_markers"],
			"cell_step",
			TraceSnapshotExtractor._summary_of(cell_traversal),
			cell_step.get("to", before_probe)
		)
		snapshot["event_lines"].append(TraceSnapshotExtractor._summary_of(cell_traversal))

	snapshot["metadata_lines"] = TraceSnapshotExtractor.kv_lines(
		[
			["mode", "Topology Replay"],
			["case_id", document.case_id],
			["command", frame.get("command_id", "")],
			["legal", frame.get("legal", "")],
			["dimension", document.dimension],
			["state_hash", snapshot.get("state_hash", "")],
		]
	)
	var diagnostics := frame.get("diagnostics", document.initial.get("diagnostics", {}))
	if diagnostics is Dictionary:
		if diagnostics.has("summary"):
			snapshot["diagnostics_lines"].append("summary: %s" % diagnostics.get("summary"))
		for warning in diagnostics.get("warnings", []):
			snapshot["diagnostics_lines"].append("warning: %s" % warning)
		if snapshot["diagnostics_lines"].is_empty():
			snapshot["diagnostics_lines"].append(TraceSnapshotExtractor._summary_of(diagnostics))
	else:
		snapshot["diagnostics_lines"].append(TraceSnapshotExtractor._summary_of(diagnostics))
