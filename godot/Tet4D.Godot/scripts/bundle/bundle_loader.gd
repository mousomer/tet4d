extends RefCounted

class_name BundleLoader

const DEFAULT_BUNDLE_ROOT := "res://assets/tet4d_bundle"


static func load_bundle(bundle_root: String = DEFAULT_BUNDLE_ROOT) -> Dictionary:
	var bundle_dir := DirAccess.open(bundle_root)
	if bundle_dir == null:
		return {
			"ok": false,
			"error": "Bundle root missing: %s" % bundle_root,
		}

	var manifest_result := _load_json("%s/manifest.json" % bundle_root)
	if not manifest_result.get("ok", false):
		return manifest_result
	var manifest: Dictionary = manifest_result.get("value", {})
	var authority: Dictionary = manifest.get("authority", {})
	if authority.get("exported_bundle_is_authority", false):
		return {
			"ok": false,
			"error": "Bundle authority flag is invalid for replay-only mode.",
		}

	var config_result := _load_json("%s/config/tet4d_config_bundle.json" % bundle_root, true)
	var docs_result := _load_json("%s/docs/authority_index.json" % bundle_root, true)
	var schema_result := _load_json("%s/schemas/schema_index.json" % bundle_root, true)
	var cases_by_type := _discover_trace_cases(bundle_root, manifest)

	return {
		"ok": true,
		"bundle_root": bundle_root,
		"manifest": manifest,
		"config": config_result.get("value", {}),
		"docs": docs_result.get("value", {}),
		"schemas": schema_result.get("value", {}),
		"cases_by_type": cases_by_type,
	}


static func load_trace_document(bundle_root: String, case_entry: Dictionary) -> Dictionary:
	var relative_path := str(case_entry.get("path", ""))
	if relative_path.is_empty():
		return {
			"ok": false,
			"error": "Trace case is missing a relative path.",
		}
	var json_result := _load_json("%s/%s" % [bundle_root, relative_path])
	if not json_result.get("ok", false):
		return json_result
	return {
		"ok": true,
		"document": TraceDocument.from_dictionary(
			json_result.get("value", {}),
			relative_path
		),
	}


static func _discover_trace_cases(bundle_root: String, manifest: Dictionary) -> Dictionary:
	var grouped: Dictionary = {
		"topology": [],
		"gameplay": [],
		"endgame": [],
	}
	var trace_groups: Dictionary = manifest.get("traces", {})
	for trace_type in grouped.keys():
		var from_manifest: Array = trace_groups.get(trace_type, [])
		if not from_manifest.is_empty():
			for case_entry in from_manifest:
				grouped[trace_type].append(case_entry)
			continue
		var directory_path := "%s/traces/%s" % [bundle_root, trace_type]
		var directory := DirAccess.open(directory_path)
		if directory == null:
			continue
		for file_name in directory.get_files():
			if not file_name.ends_with(".json"):
				continue
			grouped[trace_type].append(
				{
					"trace_type": trace_type,
					"case_id": file_name.trim_suffix(".json"),
					"path": "traces/%s/%s" % [trace_type, file_name],
				}
			)
		grouped[trace_type].sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
			return str(a.get("case_id", "")) < str(b.get("case_id", ""))
		)
	return grouped


static func _load_json(path: String, allow_missing: bool = false) -> Dictionary:
	if not FileAccess.file_exists(path):
		if allow_missing:
			return {"ok": true, "value": {}}
		return {"ok": false, "error": "Missing JSON file: %s" % path}

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"ok": false, "error": "Failed to open JSON file: %s" % path}
	var parser := JSON.new()
	var text := file.get_as_text()
	var parse_status := parser.parse(text)
	if parse_status != OK:
		return {
			"ok": false,
			"error": "Failed to parse %s: %s at line %d" % [
				path,
				parser.get_error_message(),
				parser.get_error_line(),
			],
		}
	return {"ok": true, "value": parser.data}
