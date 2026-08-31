extends RefCounted

class_name DesignScenarioCatalog

const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")

const CATALOG_TYPE := "tet4d.design_scenario_catalog"
const CATALOG_SCHEMA_VERSION := 1
const CATALOG_PATH := "res://config/design_scenario_catalog.json"
const BUNDLE_MANIFEST_PATH := "res://assets/tet4d_bundle/manifest.json"
const TRACE_FAMILIES := ["gameplay", "endgame", "topology"]
const DENSITIES := ["sparse", "dense"]
const SCENARIO_KINDS := ["replay_fixture", "live_session"]
const LIVE_COMMANDS := ["hard_drop", "hold", "soft_drop", "tick"]

var _registry
var _catalog_path := CATALOG_PATH
var _manifest_path := BUNDLE_MANIFEST_PATH
var _loaded := false
var _scenarios: Dictionary = {}
var _ordered_ids: Array = []
var _diagnostics: Array = []


func _init(registry = null, catalog_path: String = CATALOG_PATH, manifest_path: String = BUNDLE_MANIFEST_PATH) -> void:
	_registry = registry
	_catalog_path = catalog_path
	_manifest_path = manifest_path


func list_scenarios() -> Array:
	_ensure_loaded()
	var result: Array = []
	for scenario_id in _ordered_ids:
		result.append(_scenarios.get(scenario_id, {}).duplicate(true))
	return result


func has_scenario(scenario_id: String) -> bool:
	_ensure_loaded()
	return _scenarios.has(scenario_id)


func scenario(scenario_id: String) -> Dictionary:
	_ensure_loaded()
	return _scenarios.get(scenario_id, {}).duplicate(true)


func presentation_profile(scenario_id: String) -> Dictionary:
	var record := scenario(scenario_id)
	if record.is_empty():
		return _failure("Unknown design scenario %s." % scenario_id)
	var profile = PresentationProfileScript.from_snapshot(_registry, record.get("presentation_profile", {}))
	if profile == null or not profile.contract_conforms():
		return _failure("Scenario presentation profile no longer conforms.")
	return _success({"profile": profile.detached_copy()})


func diagnostics() -> Array:
	_ensure_loaded()
	return _diagnostics.duplicate()


func deterministic_snapshot() -> Dictionary:
	return {
		"catalog_schema_version": CATALOG_SCHEMA_VERSION,
		"scenarios": list_scenarios(),
		"diagnostics": diagnostics(),
	}


func _ensure_loaded() -> void:
	if _loaded:
		return
	_loaded = true
	if _registry == null:
		_diagnostics.append("Design scenario catalog requires the settings registry.")
		return
	var manifest := _read_json(_manifest_path)
	var catalog := _read_json(_catalog_path)
	if manifest.is_empty() or catalog.is_empty():
		_diagnostics.append("Design scenario catalog or replay manifest could not be read.")
		return
	if str(catalog.get("catalog_type", "")) != CATALOG_TYPE or int(catalog.get("catalog_schema_version", 0)) != CATALOG_SCHEMA_VERSION:
		_diagnostics.append("Design scenario catalog envelope is unsupported.")
		return
	var trace_index := _trace_index(manifest)
	for raw in catalog.get("scenarios", []):
		var parsed_scenario := _parse_scenario(raw, trace_index)
		if not bool(parsed_scenario.get("ok", false)):
			_diagnostics.append(str(parsed_scenario.get("error", "Invalid design scenario.")))
			continue
		var record: Dictionary = parsed_scenario.get("scenario", {})
		var scenario_id := str(record.get("scenario_id", ""))
		if _scenarios.has(scenario_id):
			_diagnostics.append("Duplicate design scenario ID %s." % scenario_id)
			continue
		_scenarios[scenario_id] = record
		_ordered_ids.append(scenario_id)


func _parse_scenario(raw, trace_index: Dictionary) -> Dictionary:
	if not (raw is Dictionary):
		return _failure("Design scenario entry must be an object.")
	var scenario_id := str(raw.get("scenario_id", ""))
	if not DesignValueScript.safe_id(scenario_id):
		return _failure("Design scenario ID is invalid or unsafe.")
	var display_name := str(raw.get("display_name", "")).strip_edges()
	if display_name.is_empty():
		return _failure("Design scenario %s requires a display name." % scenario_id)
	var dimension := int(raw.get("dimension", 0))
	if dimension < 2 or dimension > 4:
		return _failure("Design scenario %s dimension is unsupported." % scenario_id)
	var density := str(raw.get("density", ""))
	if not DENSITIES.has(density):
		return _failure("Design scenario %s density is unsupported." % scenario_id)
	var snapshot = raw.get("presentation_profile")
	if not (snapshot is Dictionary):
		return _failure("Design scenario %s requires a presentation snapshot." % scenario_id)
	var profile = PresentationProfileScript.from_snapshot(_registry, snapshot)
	if profile == null or not profile.contract_conforms():
		return _failure("Design scenario %s presentation values are invalid." % scenario_id)
	var record := {
		"scenario_id": scenario_id,
		"display_name": display_name,
		"description": str(raw.get("description", "")).strip_edges(),
		"scenario_kind": str(raw.get("scenario_kind", "replay_fixture")),
		"dimension": dimension,
		"density": density,
		"feature_tags": _string_array(raw.get("feature_tags", [])),
		"presentation_profile": profile.snapshot(),
	}
	if not SCENARIO_KINDS.has(record.get("scenario_kind")):
		return _failure("Design scenario %s kind is unsupported." % scenario_id)
	if record.get("scenario_kind") == "live_session":
		var live := _parse_live_session(raw, dimension)
		if not bool(live.get("ok", false)):
			return live
		record.merge(live.get("fields", {}), true)
	else:
		var replay := _parse_replay_fixture(raw, trace_index, dimension)
		if not bool(replay.get("ok", false)):
			return replay
		record.merge(replay.get("fields", {}), true)
	return _success({"scenario": record})


func _parse_replay_fixture(raw: Dictionary, trace_index: Dictionary, dimension: int) -> Dictionary:
	var family := str(raw.get("trace_family", ""))
	var case_id := str(raw.get("trace_case_id", ""))
	var trace: Dictionary = trace_index.get("%s:%s" % [family, case_id], {})
	if not TRACE_FAMILIES.has(family) or trace.is_empty():
		return _failure("Design scenario references an unknown replay case.")
	var frame_index := int(raw.get("frame_index", -1))
	if frame_index < 0 or frame_index >= int(trace.get("frame_count", 0)):
		return _failure("Design scenario frame is outside its replay case.")
	if dimension != int(trace.get("dimension", 0)):
		return _failure("Design scenario dimension disagrees with replay truth.")
	return _success({"fields": {
		"trace_family": family,
		"trace_case_id": case_id,
		"frame_index": frame_index,
		"trace_identity_digest": str(trace.get("identity_digest", "")),
		"trace_final_state_hash": str(trace.get("final_state_hash", "")),
	}})


func _parse_live_session(raw: Dictionary, dimension: int) -> Dictionary:
	var setup = raw.get("live_setup")
	if not (setup is Dictionary):
		return _failure("Live design scenario requires a canonical setup.")
	var mode := str(setup.get("mode", ""))
	var expected_mode := "live_%dd" % dimension
	if mode != expected_mode:
		return _failure("Live design scenario mode disagrees with its dimension.")
	var shape = setup.get("board_shape")
	if not (shape is Array):
		return _failure("Live design scenario board setup is not canonical.")
	var canonical_shape: Array = []
	for value in shape:
		canonical_shape.append(int(value))
	if GameSetupSpecScript.preset_id_for_shape(mode, canonical_shape) != str(setup.get("board_preset_id", "")):
		return _failure("Live design scenario board setup is not canonical.")
	if not GameSetupSpecScript.is_piece_set_supported(mode, str(setup.get("board_preset_id", "")), str(setup.get("piece_set_id", ""))):
		return _failure("Live design scenario piece set is unsupported.")
	if str(setup.get("random_mode", "")) != GameSetupSpecScript.RANDOM_MODE_FIXED_SEED or not GameSetupSpecScript.is_valid_seed(setup.get("seed")):
		return _failure("Live design scenario must use a valid fixed seed.")
	if not GameSetupSpecScript.is_valid_speed(setup.get("initial_speed_level")):
		return _failure("Live design scenario speed is invalid.")
	var canonical_topology := GameSetupSpecScript.bounded_topology_profile(canonical_shape)
	if DesignValueScript.canonical_hash(setup.get("topology_profile", {})) != DesignValueScript.canonical_hash(canonical_topology):
		return _failure("Live design scenario topology must remain the canonical bounded profile.")
	var commands := _string_array(raw.get("commands", []))
	for command in commands:
		if not LIVE_COMMANDS.has(command):
			return _failure("Live design scenario command %s is unsupported." % command)
	var canonical_setup: Dictionary = setup.duplicate(true)
	canonical_setup["schema_version"] = int(setup.get("schema_version", 0))
	canonical_setup["contract_version"] = int(setup.get("contract_version", 0))
	canonical_setup["board_shape"] = canonical_shape
	canonical_setup["seed"] = int(setup.get("seed", 0))
	canonical_setup["initial_speed_level"] = int(setup.get("initial_speed_level", 0))
	canonical_setup["topology_profile"] = canonical_topology
	var identity := {"setup": canonical_setup, "commands": commands.duplicate()}
	return _success({"fields": {
		"live_setup": canonical_setup,
		"commands": commands,
		"trace_identity_digest": DesignValueScript.canonical_hash(identity),
		"trace_final_state_hash": "computed_at_runtime",
		"frame_index": commands.size(),
	}})


func _trace_index(manifest: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	var traces = manifest.get("traces", {})
	if not (traces is Dictionary):
		return result
	for family in TRACE_FAMILIES:
		for raw in traces.get(family, []):
			if raw is Dictionary:
				result["%s:%s" % [family, str(raw.get("case_id", ""))]] = raw.duplicate(true)
	return result


func _read_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}


static func _string_array(value) -> Array:
	var result: Array = []
	if value is Array:
		for item in value:
			var text := str(item).strip_edges()
			if not text.is_empty() and not result.has(text):
				result.append(text)
	return result


static func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


static func _failure(error: String) -> Dictionary:
	return {"ok": false, "error": error}
