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
	var gameplay_cases: Array = result.get("cases_by_type", {}).get("gameplay", [])
	for case_id in [
		"gameplay_plain_2d_rotation_short",
		"gameplay_plain_2d_hard_drop_lock",
		"gameplay_plain_2d_line_clear_short",
	]:
		if not _has_case(gameplay_cases, case_id):
			failures.append("missing Stage 11 gameplay case %s" % case_id)
	return failures


func _has_case(cases: Array, case_id: String) -> bool:
	for case_entry in cases:
		if str(case_entry.get("case_id", "")) == case_id:
			return true
	return false
