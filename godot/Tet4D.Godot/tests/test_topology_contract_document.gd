extends RefCounted

const Document := preload("res://scripts/native/topology_contract_document.gd")


func run() -> Array[String]:
	var failures: Array[String] = []
	var payload := {
		"schema": "tet4d.topology_contract",
		"schema_version": 1,
		"dimension": 3,
		"board_dimensions": [4, 6, 4],
		"gluings": [{"id": "seam_000"}],
	}
	var document := Document.new()
	if not document.load_payload(payload):
		failures.append("canonical topology contract should load")
	if document.dimension() != 3 or document.board_dimensions() != [4, 6, 4]:
		failures.append("canonical topology contract shape should remain unchanged")
	payload["schema_version"] = 2
	if document.load_payload(payload) or document.is_loaded():
		failures.append("unsupported topology contract version should fail closed")
	return failures
