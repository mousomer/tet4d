extends SceneTree

const TestScript = preload("res://tests/test_topology_transport_boundary.gd")


func _initialize() -> void:
	var results: Dictionary = TestScript.new().export_parity_results()
	print("TET4D_TOPOLOGY_TRANSPORT_PARITY=" + JSON.stringify(results))
	quit(1 if results.has("harness_error") else 0)
