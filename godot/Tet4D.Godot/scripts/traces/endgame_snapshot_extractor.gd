extends RefCounted

class_name EndgameSnapshotExtractor


static func extract(document: TraceDocument, frame: Dictionary, snapshot: Dictionary) -> void:
	for cell in document.initial.get("full_locked_cells", []):
		var position := cell
		var color_id := 0
		if cell is Dictionary:
			position = cell.get("coord", [])
			color_id = int(cell.get("color_id", 0))
		TraceSnapshotExtractor.append_cell(snapshot["locked_cells"], "Locked", color_id, position, true)

	for particle_dict in frame.get("particles", []):
		var particle := {
			"particle_id": int(particle_dict.get("particle_id", -1)),
			"color_id": int(particle_dict.get("color_id", 0)),
			"active": bool(particle_dict.get("active", true)),
			"escaped": bool(particle_dict.get("escaped", false)),
			"mass": float(particle_dict.get("mass", 1.0)),
			"radius": float(particle_dict.get("radius", 0.25)),
			"position": particle_dict.get("position", []),
			"velocity": particle_dict.get("velocity", []),
			"source_coord": particle_dict.get("source_coord", []),
			"label": str(particle_dict.get("source_group_id", "")),
		}
		snapshot["particles"].append(particle)

	for event_dict in frame.get("events", []):
		var event_position := TraceSnapshotExtractor.particle_position(
			snapshot["particles"],
			int(event_dict.get("particle_id", -1))
		)
		TraceSnapshotExtractor.append_marker(
			snapshot["event_markers"],
			str(event_dict.get("kind", "event")),
			TraceSnapshotExtractor._summary_of(event_dict),
			event_position
		)
		snapshot["event_lines"].append(TraceSnapshotExtractor._summary_of(event_dict))

	var energy := frame.get("energy", {})
	if energy is Dictionary:
		for key in ["kinetic_energy", "speed_sq_sum", "weighted_speed_sq_sum"]:
			if energy.has(key):
				snapshot["energy_lines"].append("%s: %s" % [key, energy.get(key)])

	snapshot["metadata_lines"] = TraceSnapshotExtractor.kv_lines(
		[
			["mode", "Endgame Replay"],
			["case_id", document.case_id],
			["topology", document.topology_preset],
			["collision", document.collision_mode],
			["particles", snapshot["particles"].size()],
			["dimension", document.dimension],
			["state_hash", snapshot.get("state_hash", "")],
		]
	)
	if frame.has("elapsed_ms"):
		snapshot["diagnostics_lines"].append("elapsed_ms: %s" % frame.get("elapsed_ms"))
	for line in snapshot["energy_lines"]:
		snapshot["diagnostics_lines"].append(line)
