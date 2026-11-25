extends RefCounted

const Client = preload("res://tests/e4_qa/client.gd")
const Journal = preload("res://tests/e4_qa/journal.gd")
const FakeTransport = preload("res://tests/e4_qa/fake_transport.gd")
const QaScene = preload("res://tests/e4_qa/scene.tscn")


func run() -> Array[String]:
	var errors: Array[String] = []
	var base := OS.get_environment("TET4D_E4_QA_ROOT")
	if base.is_empty():
		base = "user://participant_data"
	var root := base.path_join("e4_synthetic_test_%d_%d" % [OS.get_process_id(), Time.get_ticks_usec()])
	var client := Client.new(root)
	var values: Array[int] = [-3, 5, 1, 2]
	if not client.present() or not client.submit(values):
		errors.append("Could not save synthetic commands")
		return errors
	var temporary := FileAccess.open(root.path_join("unpublished.pending"), FileAccess.WRITE)
	temporary.store_string("truncated")
	temporary.close()
	var restarted := Client.new(root)
	if restarted.journal.state.commands != client.journal.state.commands:
		errors.append("Restart changed the frozen command bytes")
	var transport := FakeTransport.new(root)
	if restarted.flush(10000, transport.send) != "pending":
		errors.append("A lost reply should leave the visit pending")
	restarted = Client.new(root)
	if restarted.flush(14999, transport.send) != "pending":
		errors.append("Restart ignored the persisted cooldown")
	if restarted.flush(15000, transport.send) != "synced":
		errors.append("Exact replay after restart did not verify")
	restarted = Client.new(root)
	if restarted.state_name() != "synced" or not restarted.journal.state.commands.is_empty():
		errors.append("Durable receipt checkpoint did not survive reboot")
	_check_negative_cases(root, errors)
	_check_failed_write(root, errors)
	var vectors = JSON.parse_string(FileAccess.get_file_as_string("res://tests/e4_qa/wire_golden.json"))
	for vector in vectors:
		var encoded := FakeTransport._canonical(vector.command)
		if encoded != vector.canonical or Client.digest(encoded) != vector.digest:
			errors.append("Godot command bytes or digest disagree with the RFC 8785 fixture")
	var scene := QaScene.instantiate()
	scene.free()
	return errors


func _check_negative_cases(root: String, errors: Array[String]) -> void:
	var client := Client.new(root.path_join("negative"))
	var coordinates: Array[int] = [1, 2, 3, 4]
	if not client.present() or not client.submit(coordinates):
		errors.append("Could not prepare negative receipt test")
		return
	var invalid := func(_body): return {"status": 200, "receipts": [{"digest": "wrong"}]}
	if client.flush(0, invalid) != "blocked" or client.journal.state.commands.size() != 2:
		errors.append("An incomplete receipt must block and preserve the batch")
	var commands: Array = client.journal.state.commands
	var receipts := []
	for command in commands:
		receipts.append({
			"command": JSON.parse_string(command).id,
			"digest": Client.digest(command), "received_at": "2026-11-22T12:00:00Z",
		})
	if not Client.receipts_match(commands, receipts):
		errors.append("Valid receipts should verify regardless of order")
	receipts.reverse()
	if not Client.receipts_match(commands, receipts):
		errors.append("Receipt order must not matter")
	receipts[0].digest = "wrong"
	if Client.receipts_match(commands, receipts):
		errors.append("A complete receipt set with a wrong digest must be rejected")
	receipts[0].digest = Client.digest(commands[1])
	receipts[0].received_at = "2026-02-31T12:00:00Z"
	if Client.receipts_match(commands, receipts):
		errors.append("An impossible receipt date must be rejected")
	var directory := root.path_join("negative")
	var names := DirAccess.get_files_at(directory)
	var committed := ""
	for name in names:
		if name.begins_with("generation_"):
			committed = name
	var file := FileAccess.open(directory.path_join(committed), FileAccess.WRITE)
	file.store_string("corrupt")
	file.close()
	if not Journal.new(directory).fault:
		errors.append("A corrupt committed journal must block recovery")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(directory.path_join(committed)))
	if not Journal.new(directory).fault:
		errors.append("A missing committed generation must block recovery")

func _check_failed_write(root: String, errors: Array[String]) -> void:
	var directory := root.path_join("failed_write")
	var client := Client.new(directory)
	var blocked_path := ProjectSettings.globalize_path(directory.path_join("generation_0000000001.json.pending"))
	DirAccess.make_dir_absolute(blocked_path)
	if client.present() or client.state_name() != "blocked":
		errors.append("A failed journal write must not report success")
