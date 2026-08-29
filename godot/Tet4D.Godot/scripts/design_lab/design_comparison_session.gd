extends RefCounted

class_name DesignComparisonSession

const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")

const SCHEMA_VERSION := 1
const ARM_A := "A"
const ARM_B := "B"
const ARMS := [ARM_A, ARM_B]

var _active := false
var _session: Dictionary = {}


func start(scenario: Dictionary, resolved_a: Dictionary, resolved_b: Dictionary, non_style_fingerprint: Dictionary, blind: bool = false) -> Dictionary:
	if not _valid_scenario(scenario):
		return _failure("A valid deterministic design scenario is required.")
	if not _valid_resolved(resolved_a) or not _valid_resolved(resolved_b):
		return _failure("Two registry-valid detached presets are required.")
	var arm_a := _frozen_preset(resolved_a)
	var arm_b := _frozen_preset(resolved_b)
	if arm_a.get("snapshot_hash") == arm_b.get("snapshot_hash"):
		return _failure("A/B comparison requires two observably different presentation snapshots.")
	var seed_material := "%s|%s|%s|%s" % [
		str(scenario.get("scenario_id", "")),
		str(arm_a.get("preset_id", "")),
		str(arm_b.get("preset_id", "")),
		str(Time.get_ticks_usec()),
	]
	var session_id := seed_material.sha256_text().substr(0, 32)
	var swap_blind_labels := session_id.substr(0, 8).hex_to_int() % 2 == 1
	_session = {
		"session_schema_version": SCHEMA_VERSION,
		"session_id": session_id,
		"created_at_utc": DesignValueScript.timestamp_utc(),
		"scenario": scenario.duplicate(true),
		"scenario_id": str(scenario.get("scenario_id", "")),
		"non_style_fingerprint": non_style_fingerprint.duplicate(true),
		"non_style_hash": DesignValueScript.canonical_hash(non_style_fingerprint),
		"blind": blind,
		"blind_labels": {
			ARM_A: "Option 2" if swap_blind_labels else "Option 1",
			ARM_B: "Option 1" if swap_blind_labels else "Option 2",
		},
		"active_arm": ARM_A,
		"arms": {ARM_A: arm_a, ARM_B: arm_b},
		"toggle_count": 0,
	}
	_active = true
	return _success({"session": snapshot(), "profile": arm_profile_snapshot(ARM_A)})


func active() -> bool:
	return _active


func session_id() -> String:
	return str(_session.get("session_id", "")) if _active else ""


func active_arm() -> String:
	return str(_session.get("active_arm", "")) if _active else ""


func arm_label(arm: String) -> String:
	if not _active or not ARMS.has(arm):
		return ""
	if bool(_session.get("blind", false)):
		return str(_session.get("blind_labels", {}).get(arm, arm))
	return str(_session.get("arms", {}).get(arm, {}).get("display_name", arm))


func set_blind(enabled: bool) -> Dictionary:
	if not _active:
		return _failure("No comparison session is active.")
	_session["blind"] = enabled
	return _success({"session": snapshot()})


func activate(arm: String, current_non_style_fingerprint: Dictionary) -> Dictionary:
	if not _active or not ARMS.has(arm):
		return _failure("Comparison arm must be A or B.")
	var invariant := verify_non_style_fingerprint(current_non_style_fingerprint)
	if not bool(invariant.get("ok", false)):
		return invariant
	if arm != active_arm():
		_session["toggle_count"] = int(_session.get("toggle_count", 0)) + 1
	_session["active_arm"] = arm
	return _success({"arm": arm, "profile": arm_profile_snapshot(arm), "session": snapshot()})


func toggle(current_non_style_fingerprint: Dictionary) -> Dictionary:
	return activate(ARM_B if active_arm() == ARM_A else ARM_A, current_non_style_fingerprint)


func reset_request(current_non_style_fingerprint: Dictionary) -> Dictionary:
	var invariant := verify_non_style_fingerprint(current_non_style_fingerprint)
	if not bool(invariant.get("ok", false)):
		return invariant
	_session["active_arm"] = ARM_A
	return _success({
		"scenario": _session.get("scenario", {}).duplicate(true),
		"arm": ARM_A,
		"profile": arm_profile_snapshot(ARM_A),
	})


func verify_non_style_fingerprint(current: Dictionary) -> Dictionary:
	if not _active:
		return _failure("No comparison session is active.")
	var expected_hash := str(_session.get("non_style_hash", ""))
	var actual_hash := DesignValueScript.canonical_hash(current)
	if actual_hash != expected_hash:
		return _failure("Comparison stopped because deterministic non-style state changed.", {
			"expected_hash": expected_hash,
			"actual_hash": actual_hash,
		})
	return _success()


func arm_profile_snapshot(arm: String) -> Dictionary:
	if not _active or not ARMS.has(arm):
		return {}
	return _session.get("arms", {}).get(arm, {}).get("presentation_profile", {}).duplicate(true)


func frozen_arm(arm: String) -> Dictionary:
	if not _active or not ARMS.has(arm):
		return {}
	return _session.get("arms", {}).get(arm, {}).duplicate(true)


func snapshot() -> Dictionary:
	return _session.duplicate(true) if _active else {}


func _frozen_preset(resolved: Dictionary) -> Dictionary:
	var descriptor: Dictionary = resolved.get("descriptor", {})
	var snapshot: Dictionary = resolved.get("snapshot", {})
	return {
		"source_kind": str(descriptor.get("source_kind", "")),
		"preset_id": str(descriptor.get("preset_id", "")),
		"preset_version": int(descriptor.get("preset_version", snapshot.get("schema_version", 0))),
		"display_name": str(descriptor.get("display_name", "")),
		"provenance": str(descriptor.get("provenance", "")),
		"presentation_profile": snapshot.duplicate(true),
		"snapshot_hash": DesignValueScript.canonical_hash(snapshot),
	}


static func _valid_scenario(scenario: Dictionary) -> bool:
	return DesignValueScript.safe_id(str(scenario.get("scenario_id", ""))) and not str(scenario.get("trace_case_id", "")).is_empty()


static func _valid_resolved(resolved: Dictionary) -> bool:
	return bool(resolved.get("ok", false)) and resolved.get("snapshot") is Dictionary and not resolved.get("snapshot", {}).is_empty()


static func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


static func _failure(error: String, extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": false, "error": error}
	result.merge(extra, true)
	return result
