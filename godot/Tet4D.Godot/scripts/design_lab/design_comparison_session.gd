extends RefCounted

class_name DesignComparisonSession

const DesignValueScript = preload("res://scripts/design_lab/design_value.gd")

const SCHEMA_VERSION := 2
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
	_session = {
		"session_schema_version": SCHEMA_VERSION,
		"session_id": session_id,
		"created_at_utc": DesignValueScript.timestamp_utc(),
		"scenario": scenario.duplicate(true),
		"scenario_id": str(scenario.get("scenario_id", "")),
		"non_style_fingerprint": non_style_fingerprint.duplicate(true),
		"non_style_hash": DesignValueScript.canonical_hash(non_style_fingerprint),
		"blind": blind,
		"blind_labels": _blind_labels(session_id),
		"shown_arm": ARM_A,
		"arms": {ARM_A: arm_a, ARM_B: arm_b},
		"assignment_revision": 0,
		"toggle_count": 0,
	}
	_active = true
	return _success({"session": snapshot(), "profile": arm_profile_snapshot(ARM_A)})


func active() -> bool:
	return _active


func session_id() -> String:
	return str(_session.get("session_id", "")) if _active else ""


func active_arm() -> String:
	return shown_arm()


func shown_arm() -> String:
	return str(_session.get("shown_arm", "")) if _active else ""


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


func assign(arm: String, resolved: Dictionary, current_non_style_fingerprint: Dictionary) -> Dictionary:
	if not _active or not ARMS.has(arm):
		return _failure("Comparison assignment must target A or B.")
	if not _valid_resolved(resolved):
		return _failure("A registry-valid detached preset is required for assignment.")
	var invariant := verify_non_style_fingerprint(current_non_style_fingerprint)
	if not bool(invariant.get("ok", false)):
		return invariant
	var assigned := _frozen_preset(resolved)
	var other_arm := ARM_B if arm == ARM_A else ARM_A
	if assigned.get("snapshot_hash") == _session.get("arms", {}).get(other_arm, {}).get("snapshot_hash"):
		return _failure("A/B comparison requires two observably different presentation snapshots.")
	var previous: Dictionary = _session.get("arms", {}).get(arm, {})
	if assigned == previous:
		return _success({
			"arm": arm,
			"changed": false,
			"refresh_shown": shown_arm() == arm,
			"profile": arm_profile_snapshot(arm),
			"session": snapshot(),
		})
	_session["arms"][arm] = assigned
	_session["assignment_revision"] = int(_session.get("assignment_revision", 0)) + 1
	_session["session_id"] = _assignment_session_id(arm)
	_session["blind_labels"] = _blind_labels(str(_session.get("session_id", "")))
	_session["last_assignment_at_utc"] = DesignValueScript.timestamp_utc()
	return _success({
		"arm": arm,
		"changed": true,
		"refresh_shown": shown_arm() == arm,
		"profile": arm_profile_snapshot(arm),
		"session": snapshot(),
	})


func activate(arm: String, current_non_style_fingerprint: Dictionary) -> Dictionary:
	if not _active or not ARMS.has(arm):
		return _failure("Comparison arm must be A or B.")
	var invariant := verify_non_style_fingerprint(current_non_style_fingerprint)
	if not bool(invariant.get("ok", false)):
		return invariant
	if arm != shown_arm():
		_session["toggle_count"] = int(_session.get("toggle_count", 0)) + 1
	_session["shown_arm"] = arm
	return _success({"arm": arm, "profile": arm_profile_snapshot(arm), "session": snapshot()})


func toggle(current_non_style_fingerprint: Dictionary) -> Dictionary:
	return activate(ARM_B if shown_arm() == ARM_A else ARM_A, current_non_style_fingerprint)


func reset_request(current_non_style_fingerprint: Dictionary) -> Dictionary:
	var invariant := verify_non_style_fingerprint(current_non_style_fingerprint)
	if not bool(invariant.get("ok", false)):
		return invariant
	_session["shown_arm"] = ARM_A
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


func restore(saved: Dictionary) -> Dictionary:
	if int(saved.get("session_schema_version", 0)) != SCHEMA_VERSION:
		return _failure("Comparison session schema is unsupported.")
	if not DesignValueScript.safe_id(str(saved.get("session_id", ""))) or not _valid_scenario(saved.get("scenario", {})):
		return _failure("Comparison session identity is invalid.")
	if not ARMS.has(str(saved.get("shown_arm", ""))):
		return _failure("Comparison shown arm must be A or B.")
	var arms = saved.get("arms")
	if not (arms is Dictionary) or not _valid_frozen(arms.get(ARM_A, {})) or not _valid_frozen(arms.get(ARM_B, {})):
		return _failure("Comparison assignments are invalid.")
	if arms.get(ARM_A, {}).get("snapshot_hash") == arms.get(ARM_B, {}).get("snapshot_hash"):
		return _failure("A/B comparison requires two observably different presentation snapshots.")
	var fingerprint = saved.get("non_style_fingerprint")
	if not (fingerprint is Dictionary) or DesignValueScript.canonical_hash(fingerprint) != str(saved.get("non_style_hash", "")):
		return _failure("Comparison non-style provenance is inconsistent.")
	_session = saved.duplicate(true)
	_session["blind_labels"] = _blind_labels(str(_session.get("session_id", "")))
	_active = true
	return _success({
		"session": snapshot(),
		"profile": arm_profile_snapshot(shown_arm()),
	})


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


func _assignment_session_id(arm: String) -> String:
	return ("%s|%s|%d|%s|%s|%s" % [
		str(_session.get("session_id", "")),
		arm,
		int(_session.get("assignment_revision", 0)),
		str(_session.get("arms", {}).get(ARM_A, {}).get("snapshot_hash", "")),
		str(_session.get("arms", {}).get(ARM_B, {}).get("snapshot_hash", "")),
		str(Time.get_ticks_usec()),
	]).sha256_text().substr(0, 32)


static func _blind_labels(session_id: String) -> Dictionary:
	var swap := session_id.substr(0, 8).hex_to_int() % 2 == 1
	return {
		ARM_A: "Option 2" if swap else "Option 1",
		ARM_B: "Option 1" if swap else "Option 2",
	}


static func _valid_frozen(preset) -> bool:
	if not (preset is Dictionary) or not DesignValueScript.safe_id(str(preset.get("preset_id", ""))):
		return false
	var profile = preset.get("presentation_profile")
	return profile is Dictionary and not profile.is_empty() and DesignValueScript.canonical_hash(profile) == str(preset.get("snapshot_hash", ""))


static func _valid_scenario(scenario: Dictionary) -> bool:
	if not DesignValueScript.safe_id(str(scenario.get("scenario_id", ""))):
		return false
	var scenario_kind := str(scenario.get("scenario_kind", "replay_fixture"))
	if scenario_kind == "live_session":
		return scenario.get("live_setup") is Dictionary and not scenario.get("live_setup", {}).is_empty()
	return scenario_kind == "replay_fixture" and not str(scenario.get("trace_case_id", "")).is_empty()


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
