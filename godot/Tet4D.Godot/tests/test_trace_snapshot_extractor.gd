extends RefCounted


func run() -> Array:
	var failures: Array = []
	var bundle_result := BundleLoader.load_bundle()
	if not bundle_result.get("ok", false):
		failures.append("bundle load failed: %s" % bundle_result.get("error", "unknown"))
		return failures
	for trace_type in ["topology", "gameplay", "endgame"]:
		var cases: Array = bundle_result.get("cases_by_type", {}).get(trace_type, [])
		if cases.is_empty():
			failures.append("no %s case available" % trace_type)
			continue
		var document_result := BundleLoader.load_trace_document(
			str(bundle_result.get("bundle_root", "")),
			cases[0]
		)
		if not document_result.get("ok", false):
			failures.append("failed to load %s document" % trace_type)
			continue
		var document: TraceDocument = document_result.get("document")
		if trace_type == "topology":
			_assert_all_topology_cases_extract(failures, bundle_result, cases)
		if trace_type == "gameplay":
			_assert_all_gameplay_cases_extract(failures, bundle_result, cases)
		if document.frame_count() <= 0:
			failures.append("%s document has no frames" % trace_type)
			continue
		var snapshot := TraceSnapshotExtractor.extract(document, 0)
		if str(snapshot.get("state_hash", "")).is_empty():
			failures.append("%s snapshot missing state hash" % trace_type)
		if trace_type == "endgame" and snapshot.get("particles", []).is_empty():
			failures.append("endgame snapshot missing particles")
		if trace_type == "gameplay" and snapshot.get("active_cells", []).is_empty():
			failures.append("gameplay snapshot missing active cells")
		if trace_type == "topology" and snapshot.get("probe_markers", []).is_empty():
			failures.append("topology snapshot missing probe markers")
	return failures


func _assert_all_topology_cases_extract(failures: Array, bundle_result: Dictionary, cases: Array) -> void:
	for case_entry in cases:
		var document_result := BundleLoader.load_trace_document(
			str(bundle_result.get("bundle_root", "")),
			case_entry
		)
		if not document_result.get("ok", false):
			failures.append("failed to load topology document %s" % case_entry.get("case_id", ""))
			continue
		_assert_all_topology_frames_extract(failures, document_result.get("document") as TraceDocument)


func _assert_all_topology_frames_extract(failures: Array, document: TraceDocument) -> void:
	for frame_index in range(document.frame_count()):
		var snapshot := TraceSnapshotExtractor.extract(document, frame_index)
		if str(snapshot.get("case_id", "")) != document.case_id:
			failures.append("%s frame %d extracted wrong case" % [document.case_id, frame_index])


func _assert_all_gameplay_cases_extract(failures: Array, bundle_result: Dictionary, cases: Array) -> void:
	for case_entry in cases:
		var document_result := BundleLoader.load_trace_document(
			str(bundle_result.get("bundle_root", "")),
			case_entry
		)
		if not document_result.get("ok", false):
			failures.append("failed to load gameplay document %s" % case_entry.get("case_id", ""))
			continue
		_assert_all_gameplay_frames_extract(failures, document_result.get("document") as TraceDocument)


func _assert_all_gameplay_frames_extract(failures: Array, document: TraceDocument) -> void:
	for frame_index in range(document.frame_count()):
		var snapshot := TraceSnapshotExtractor.extract(document, frame_index)
		if str(snapshot.get("case_id", "")) != document.case_id:
			failures.append("%s frame %d extracted wrong case" % [document.case_id, frame_index])
