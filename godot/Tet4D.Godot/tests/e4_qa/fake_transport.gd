extends RefCounted

const Client = preload("res://tests/e4_qa/client.gd")

var root: String


func _init(directory: String) -> void:
	root = ProjectSettings.globalize_path(directory)


func send(body: String) -> Dictionary:
	var committed_path := root.path_join("synthetic_server_request")
	if not FileAccess.file_exists(committed_path):
		var file := FileAccess.open(committed_path, FileAccess.WRITE)
		if file == null:
			return {"status": 503}
		file.store_string(body)
		file.flush()
		var error := file.get_error()
		file.close()
		return {"status": 0 if error == OK else 503}
	if FileAccess.get_file_as_string(committed_path) != body:
		return {"status": 409}
	var reply := []
	# Commands use fixed ASCII fields and contain no string with a literal newline.
	var commands: Array = JSON.parse_string(body).commands
	for command in commands:
		reply.append({
			"command": command.id, "digest": Client.digest(_canonical(command)),
			"received_at": "2026-11-22T12:00:00+00:00",
		})
	return {"status": 200, "receipts": reply}


static func _canonical(command: Dictionary) -> String:
	# Godot's JSON parser represents numbers as floats. The v1 fields are integers.
	if command.kind == "submit":
		command.latency_ms = int(command.latency_ms)
		command.response = command.response.map(func(value): return int(value))
	return JSON.stringify(command)
