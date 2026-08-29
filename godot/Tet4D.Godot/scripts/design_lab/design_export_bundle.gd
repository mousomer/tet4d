extends RefCounted

class_name DesignExportBundle

const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")
const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const PersistentFileReplacementScript = preload("res://scripts/persistence/persistent_file_replacement.gd")

const PRESET_TYPE := "tet4d.design_candidate_preset"
const PRESET_SCHEMA_VERSION := 1
const SUMMARY_TYPE := "tet4d.design_comparison_summary"
const SUMMARY_SCHEMA_VERSION := 1

var _registry


func _init(registry = null) -> void:
	_registry = registry


func export_candidate(resolved_candidate: Dictionary, reference: Dictionary, evaluations: Array, destination_root: String, build_identity: Dictionary, catalog_version: int) -> Dictionary:
	var candidate := _conform_resolved_candidate(resolved_candidate)
	if not bool(candidate.get("ok", false)):
		return candidate
	var descriptor: Dictionary = resolved_candidate.get("descriptor", {})
	var preset_id := str(descriptor.get("preset_id", ""))
	if destination_root.strip_edges().is_empty():
		return _failure("Choose a design export destination.")
	var export_directory := destination_root.trim_suffix("/").path_join(preset_id)
	var ensure := _ensure_directory(export_directory)
	if not bool(ensure.get("ok", false)):
		return ensure
	var preset := _preset_document(resolved_candidate, build_identity)
	var summary := _summary_document(preset_id, evaluations, build_identity, catalog_version)
	var proposal := _proposal_document(resolved_candidate, reference, summary)
	for output in [
		["preset.json", JSON.stringify(preset, "  ", true) + "\n"],
		["comparison_summary.json", JSON.stringify(summary, "  ", true) + "\n"],
		["DESIGN_PROPOSAL.md", proposal],
	]:
		var path := export_directory.path_join(str(output[0]))
		var written := PersistentFileReplacementScript.write_text(path, str(output[1]), true)
		if not bool(written.get("ok", false)):
			return _failure("Design export failed for %s: %s" % [output[0], written.get("detail", "replacement failed")])
	return _success({
		"directory": export_directory,
		"preset_path": export_directory.path_join("preset.json"),
		"summary_path": export_directory.path_join("comparison_summary.json"),
		"proposal_path": export_directory.path_join("DESIGN_PROPOSAL.md"),
	})


func conform_preset_document(document: Dictionary) -> Dictionary:
	if _registry == null:
		return _failure("Canonical settings registry is required.")
	if str(document.get("preset_type", "")) != PRESET_TYPE or int(document.get("preset_schema_version", 0)) != PRESET_SCHEMA_VERSION:
		return _failure("Design preset envelope is unsupported.")
	if not DesignValueScript.safe_id(str(document.get("preset_id", ""))):
		return _failure("Design preset identity is invalid or unsafe.")
	var snapshot := {
		"schema_version": int(document.get("presentation_profile_schema_version", 0)),
		"values": document.get("properties", {}).duplicate(true) if document.get("properties") is Dictionary else {},
	}
	var profile = PresentationProfileScript.from_snapshot(_registry, snapshot)
	if profile == null or not profile.contract_conforms():
		return _failure("Design preset properties fail canonical registry validation.")
	var owners = document.get("semantic_owners")
	if not (owners is Dictionary) or owners.size() != profile.values().size():
		return _failure("Design preset semantic-owner map is incomplete.")
	for property_id in profile.values().keys():
		var spec = _registry.get_spec(property_id)
		if spec == null or str(owners.get(property_id, "")) != spec.semantic_owner():
			return _failure("Design preset semantic owner mismatch for %s." % property_id)
	return _success({"profile": profile.detached_copy()})


func _conform_resolved_candidate(resolved: Dictionary) -> Dictionary:
	if not bool(resolved.get("ok", false)) or not (resolved.get("snapshot") is Dictionary):
		return _failure("A resolved registry-valid design candidate is required.")
	var descriptor: Dictionary = resolved.get("descriptor", {})
	if not DesignValueScript.safe_id(str(descriptor.get("preset_id", ""))):
		return _failure("Candidate identity is invalid or unsafe.")
	var document := _preset_document(resolved, {})
	return conform_preset_document(document)


func _preset_document(resolved: Dictionary, build_identity: Dictionary) -> Dictionary:
	var descriptor: Dictionary = resolved.get("descriptor", {})
	var snapshot: Dictionary = resolved.get("snapshot", {})
	var properties: Dictionary = snapshot.get("values", {}).duplicate(true)
	var owners: Dictionary = {}
	for property_id in properties.keys():
		var spec = _registry.get_spec(str(property_id)) if _registry != null else null
		owners[str(property_id)] = spec.semantic_owner() if spec != null else ""
	return {
		"preset_type": PRESET_TYPE,
		"preset_schema_version": PRESET_SCHEMA_VERSION,
		"preset_id": str(descriptor.get("preset_id", "")),
		"display_name": str(descriptor.get("display_name", "")),
		"status": "nominated_candidate",
		"presentation_profile_schema_version": int(snapshot.get("schema_version", 0)),
		"properties": properties,
		"semantic_owners": owners,
		"snapshot_hash": DesignValueScript.canonical_hash(snapshot),
		"source": {
			"kind": str(descriptor.get("source_kind", "")),
			"provenance": str(descriptor.get("provenance", "")),
		},
		"build_identity": build_identity.duplicate(true),
		"exported_at_utc": DesignValueScript.timestamp_utc(),
	}


func _summary_document(preset_id: String, evaluations: Array, build_identity: Dictionary, catalog_version: int) -> Dictionary:
	var matching: Array = []
	for record in evaluations:
		if not (record is Dictionary):
			continue
		var includes_candidate := false
		for arm in ["A", "B"]:
			if str(record.get("presets", {}).get(arm, {}).get("preset_id", "")) == preset_id:
				includes_candidate = true
		if includes_candidate:
			matching.append(record.duplicate(true))
	return {
		"summary_type": SUMMARY_TYPE,
		"summary_schema_version": SUMMARY_SCHEMA_VERSION,
		"nominated_preset_id": preset_id,
		"evaluation_records": matching,
		"evaluated_scenario_ids": _unique_scenario_ids(matching),
		"build_identity": build_identity.duplicate(true),
		"catalog_schema_version": catalog_version,
		"generated_at_utc": DesignValueScript.timestamp_utc(),
		"aggregation_note": "Individual human design judgments; no statistical inference is claimed.",
	}


func _proposal_document(candidate: Dictionary, reference: Dictionary, summary: Dictionary) -> String:
	var descriptor: Dictionary = candidate.get("descriptor", {})
	var candidate_values: Dictionary = candidate.get("snapshot", {}).get("values", {})
	var reference_values: Dictionary = reference.get("snapshot", {}).get("values", {}) if reference.get("snapshot") is Dictionary else {}
	var reference_name := str(reference.get("descriptor", {}).get("display_name", "No explicit reference"))
	var lines: Array = [
		"# Design Proposal: %s" % str(descriptor.get("display_name", "Candidate")),
		"",
		"> Review input only. This proposal is not architecture authority and does not change production defaults.",
		"",
		"## Candidate",
		"",
		"Preset ID: `%s`" % str(descriptor.get("preset_id", "")),
		"",
		"## Compared against",
		"",
		reference_name,
		"",
		"## Evaluation coverage",
		"",
		", ".join(summary.get("evaluated_scenario_ids", [])) if not summary.get("evaluated_scenario_ids", []).is_empty() else "No matching saved evaluations were included.",
		"",
		"## Designer findings",
		"",
		_format_findings(summary.get("evaluation_records", [])),
		"",
		"## Canonical property changes",
		"",
		"| Property | Existing/reference | Proposed | Semantic owner |",
		"| --- | --- | --- | --- |",
	]
	var property_ids: Array = candidate_values.keys()
	property_ids.sort()
	for property_id in property_ids:
		var proposed = candidate_values.get(property_id)
		var existing = reference_values.get(property_id, "—")
		if existing == proposed and not reference_values.is_empty():
			continue
		var spec = _registry.get_spec(str(property_id)) if _registry != null else null
		lines.append("| `%s` | `%s` | `%s` | `%s` |" % [property_id, str(existing), str(proposed), spec.semantic_owner() if spec != null else ""])
	lines.append_array([
		"",
		"## Relevant scenarios",
		"",
		", ".join(summary.get("evaluated_scenario_ids", [])) if not summary.get("evaluated_scenario_ids", []).is_empty() else "None recorded.",
		"",
		"## Provenance",
		"",
		"Generated by Tet4D Design Laboratory from exact registry-validated values and saved local evaluation records.",
		"",
	])
	return "\n".join(lines)


static func _format_findings(records: Array) -> String:
	if records.is_empty():
		return "No matching saved findings were included."
	var lines: Array = []
	for record in records:
		var note := str(record.get("notes", "")).replace("\n", " ").strip_edges()
		lines.append("- `%s` · %s%s" % [str(record.get("scenario_id", "")), str(record.get("preference", "")), " · %s" % note if not note.is_empty() else ""])
	return "\n".join(lines)


static func _unique_scenario_ids(records: Array) -> Array:
	var result: Array = []
	for record in records:
		var scenario_id := str(record.get("scenario_id", ""))
		if not scenario_id.is_empty() and not result.has(scenario_id):
			result.append(scenario_id)
	result.sort()
	return result


static func _ensure_directory(path: String) -> Dictionary:
	var absolute := ProjectSettings.globalize_path(path)
	if DirAccess.dir_exists_absolute(absolute):
		return _success()
	var error := DirAccess.make_dir_recursive_absolute(absolute)
	return _success() if error == OK else _failure("Design export directory could not be created (error %s)." % error)


static func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


static func _failure(error: String) -> Dictionary:
	return {"ok": false, "error": error}
