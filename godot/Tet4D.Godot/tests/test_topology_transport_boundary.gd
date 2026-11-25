extends RefCounted

const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")
const FIXTURE_PATH := "res://tests/fixtures/topology_transport_v1.json"


func run() -> Array:
	var failures: Array = []
	var bridge := Tet4DCoreBridgeScript.new()
	if not bridge.is_available():
		failures.append("Tet4DCoreApi is required for topology transport boundary tests")
		return failures
	var fixture := _load_fixture(failures)
	if fixture.is_empty():
		return failures
	_assert_valid_profiles(failures, bridge, fixture)
	_assert_invalid_profiles(failures, bridge, fixture)
	_assert_valid_queries(failures, bridge, fixture)
	_assert_invalid_queries(failures, bridge, fixture)
	_assert_hostile_variants(failures, bridge, fixture)
	return failures


func export_parity_results() -> Dictionary:
	var failures: Array = []
	var fixture := _load_fixture(failures)
	var bridge := Tet4DCoreBridgeScript.new()
	if not failures.is_empty() or not bridge.is_available():
		return {"harness_error": failures}
	var results := {}
	var profiles: Dictionary = fixture.get("profiles", {})
	for case in fixture.get("valid_profile_cases", []):
		var result: Dictionary = bridge.topology_transport_profile(profiles.get(case.get("profile")))
		results["profile:%s" % case.get("id")] = _parity_case_result(result, "profile")
	for case in fixture.get("invalid_profile_cases", []):
		var supplied = _replace_path(profiles.get(case.get("base")), case.get("path", []), case.get("value"))
		var result: Dictionary = bridge.topology_transport_profile(supplied)
		results["profile:%s" % case.get("id")] = _parity_case_result(result, "profile")
	var queries: Dictionary = fixture.get("queries", {})
	for case in fixture.get("valid_query_cases", []):
		var source: Dictionary = queries.get(case.get("query"), {})
		var result: Dictionary = bridge.native_topology_transport_query(profiles.get(source.get("profile")), _query_payload(source))
		results["query:%s" % case.get("id")] = _parity_case_result(result, "query")
	for case in fixture.get("invalid_query_cases", []):
		var source = _replace_path(queries.get(case.get("base")), case.get("path", []), case.get("value"))
		var result: Dictionary = bridge.native_topology_transport_query(profiles.get(source.get("profile")), _query_payload(source))
		results["query:%s" % case.get("id")] = _parity_case_result(result, "query")
	return results


func _parity_case_result(result: Dictionary, value_key: String) -> Dictionary:
	if bool(result.get("ok", false)):
		return {"accepted": true, "value": result.get(value_key)}
	var error: Dictionary = result.get("error", {})
	return {
		"accepted": false,
		"code": error.get("code"),
		"path": error.get("path"),
	}


func _load_fixture(failures: Array) -> Dictionary:
	var file := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	if file == null:
		failures.append("topology transport fixture should be readable: %s" % FIXTURE_PATH)
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		failures.append("topology transport fixture should parse as a dictionary")
		return {}
	if parsed.get("slice") != "topology_transport_v1":
		failures.append("topology transport fixture slice should be topology_transport_v1")
		return {}
	return _materialize(parsed)


func _materialize(value):
	if typeof(value) == TYPE_DICTIONARY:
		if value.size() == 1 and value.has("$float"):
			return float(value["$float"])
		var result := {}
		for key in value:
			result[key] = _materialize(value[key])
		return result
	if typeof(value) == TYPE_ARRAY:
		var result := []
		for item in value:
			result.append(_materialize(item))
		return result
	if typeof(value) == TYPE_FLOAT and value == floor(value):
		return int(value)
	return value


func _assert_valid_profiles(failures: Array, bridge: RefCounted, fixture: Dictionary) -> void:
	var profiles: Dictionary = fixture.get("profiles", {})
	for case in fixture.get("valid_profile_cases", []):
		var source = profiles.get(case.get("profile"))
		var result: Dictionary = bridge.topology_transport_profile(source)
		_assert_equal(failures, result.get("ok"), true, "%s profile accepted" % case.get("id"))
		if not bool(result.get("ok", false)):
			continue
		var normalized: Dictionary = result.get("profile", {})
		_assert_equal(failures, normalized.get("contract_version"), 1, "%s contract version" % case.get("id"))
		_assert_equal(failures, normalized.get("rank"), source.get("rank"), "%s rank" % case.get("id"))
		_assert_equal(failures, normalized.get("dimensions"), source.get("dimensions"), "%s dimensions" % case.get("id"))
		_assert_equal(failures, normalized.get("seams", []).size(), source.get("seams", []).size(), "%s seam count" % case.get("id"))
	if profiles.has("disabled_nonidentity_4d"):
		var normalized_result: Dictionary = bridge.topology_transport_profile(profiles["disabled_nonidentity_4d"])
		var seam: Dictionary = normalized_result.get("profile", {}).get("seams", [])[0]
		_assert_equal(failures, seam.get("enabled"), false, "disabled seam preserved")
		_assert_equal(failures, seam.get("source"), {"axis": "x", "side": "-"}, "axis and side normalization")
		_assert_equal(failures, seam.get("transform", {}).get("permutation"), [2, 0, 1], "non-identity permutation preserved")
		_assert_equal(failures, seam.get("transform", {}).get("signs"), [1, -1, 1], "negative sign preserved")


func _assert_invalid_profiles(failures: Array, bridge: RefCounted, fixture: Dictionary) -> void:
	var profiles: Dictionary = fixture.get("profiles", {})
	for case in fixture.get("invalid_profile_cases", []):
		var supplied = _replace_path(profiles.get(case.get("base")), case.get("path", []), case.get("value"))
		var result: Dictionary = bridge.topology_transport_profile(supplied)
		_assert_error(failures, result, case, "profile")


func _assert_valid_queries(failures: Array, bridge: RefCounted, fixture: Dictionary) -> void:
	var profiles: Dictionary = fixture.get("profiles", {})
	var queries: Dictionary = fixture.get("queries", {})
	for case in fixture.get("valid_query_cases", []):
		var source: Dictionary = queries.get(case.get("query"), {})
		var query := _query_payload(source)
		var result: Dictionary = bridge.native_topology_transport_query(profiles.get(source.get("profile")), query)
		_assert_equal(failures, result.get("ok"), true, "%s query accepted" % case.get("id"))
		_assert_equal(failures, result.get("target"), case.get("target"), "%s target" % case.get("id"))


func _assert_invalid_queries(failures: Array, bridge: RefCounted, fixture: Dictionary) -> void:
	var profiles: Dictionary = fixture.get("profiles", {})
	var queries: Dictionary = fixture.get("queries", {})
	for case in fixture.get("invalid_query_cases", []):
		var source = _replace_path(queries.get(case.get("base")), case.get("path", []), case.get("value"))
		var profile = profiles.get(source.get("profile"))
		var result: Dictionary = bridge.native_topology_transport_query(profile, _query_payload(source))
		_assert_error(failures, result, case, "query")


func _query_payload(source: Dictionary) -> Dictionary:
	var result := source.duplicate(true)
	result.erase("profile")
	return result


func _replace_path(source, path: Array, value):
	var result = source.duplicate(true)
	var parent = result
	for component in path.slice(0, path.size() - 1):
		parent = parent[component]
	parent[path[-1]] = value
	return result


func _assert_error(failures: Array, result: Dictionary, case: Dictionary, kind: String) -> void:
	_assert_equal(failures, result.get("ok"), false, "%s %s rejected" % [case.get("id"), kind])
	var error: Dictionary = result.get("error", {})
	_assert_equal(failures, error.get("code"), case.get("code"), "%s error code" % case.get("id"))
	_assert_equal(failures, error.get("path"), case.get("error_path"), "%s error path" % case.get("id"))
	for field in ["expected", "actual", "message"]:
		if str(error.get(field, "")).is_empty():
			failures.append("%s error should include %s" % [case.get("id"), field])


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


# PR #181 regression: cycles overflowed the native stack before schema admission;
# repeated aliases expanded exponentially. Exercise every shared DTO entry point.
func _assert_hostile_variants(failures: Array, bridge: RefCounted, fixture: Dictionary) -> void:
	var profiles: Dictionary = fixture.profiles
	var valid: Dictionary = profiles.values()[0]
	var cyclic := valid.duplicate(true)
	cyclic["self"] = cyclic
	var looped: Array = []
	looped.append(looped)
	var array_cycle := valid.duplicate(true)
	array_cycle["seams"] = looped
	var diamond: Variant = 0
	for level in 20:
		diamond = {"left": diamond, "right": diamond}
	var wide := valid.duplicate(true)
	wide["extra"] = diamond
	var hashes := [bridge.live_state_hash(2), bridge.live_state_hash(3), bridge.live_state_hash(4)]
	for hostile in [cyclic, array_cycle, wide]:
		var profile_result: Dictionary = bridge.topology_transport_profile(hostile)
		_assert_equal(failures, profile_result.get("error", {}).get("code"), "resource_limit", "hostile profile bounded")
		var query_profile: Dictionary = bridge.native_topology_transport_query(hostile, {})
		_assert_equal(failures, query_profile.get("error", {}).get("code"), "resource_limit", "hostile query profile bounded")
		var query_value: Dictionary = bridge.native_topology_transport_query(valid, hostile)
		_assert_equal(failures, query_value.get("error", {}).get("code"), "resource_limit", "hostile query payload bounded")
	var setup := {"contract_version": 1, "mode": "live_2d", "board_shape": [10, 20], "piece_set_id": "classic", "topology_profile": cyclic}
	_assert_equal(failures, bridge.validate_live_board_setup(setup).get("ok"), false, "cyclic live setup rejected")
	_assert_equal(failures, bridge.live_configure(2, setup), false, "cyclic live configuration rejected")
	_assert_equal(failures, [bridge.live_state_hash(2), bridge.live_state_hash(3), bridge.live_state_hash(4)], hashes, "hostile requests preserve Play sessions")
	cyclic.erase("self")
	looped.clear()
