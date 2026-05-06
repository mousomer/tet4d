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
