extends RefCounted


func run() -> Array:
	var failures: Array = []
	var result := BundleLoader.load_bundle()
	if not result.get("ok", false):
		failures.append("bundle load failed: %s" % result.get("error", "unknown"))
		return failures
	var manifest: Dictionary = result.get("manifest", {})
	var authority: Dictionary = manifest.get("authority", {})
	if authority.get("exported_bundle_is_authority", true):
		failures.append("bundle authority flag should be false")
	for trace_type in ["topology", "gameplay", "endgame"]:
		if result.get("cases_by_type", {}).get(trace_type, []).is_empty():
			failures.append("missing %s cases" % trace_type)
	return failures
