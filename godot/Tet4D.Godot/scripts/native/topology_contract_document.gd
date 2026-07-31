extends RefCounted

class_name TopologyContractDocument

const SCHEMA := "tet4d.topology_contract"
const SCHEMA_VERSION := 1

var _payload: Dictionary = {}


func load_payload(payload: Dictionary) -> bool:
	if payload.get("schema") != SCHEMA or payload.get("schema_version") != SCHEMA_VERSION:
		_payload = {}
		return false
	var dimension := int(payload.get("dimension", 0))
	var board_dimensions: Variant = payload.get("board_dimensions")
	var gluings: Variant = payload.get("gluings")
	if dimension < 2 or dimension > 4:
		_payload = {}
		return false
	if not board_dimensions is Array or board_dimensions.size() != dimension:
		_payload = {}
		return false
	if not gluings is Array:
		_payload = {}
		return false
	_payload = payload.duplicate(true)
	return true


func is_loaded() -> bool:
	return not _payload.is_empty()


func dimension() -> int:
	return int(_payload.get("dimension", 0))


func board_dimensions() -> Array:
	return _payload.get("board_dimensions", []).duplicate()


func gluings() -> Array:
	return _payload.get("gluings", []).duplicate(true)
