extends RefCounted
## Single synthetic visit. Each published generation holds the whole bounded outbox.

const CAP := 4 * 1024 * 1024
const PREFIX := "generation_"

var root: String
var generation := 0
var state := {"commands": [], "status": "ready", "attempts": 0, "retry_at": 0}
var fault := false


func _init(directory: String) -> void:
	root = ProjectSettings.globalize_path(directory)
	if DirAccess.make_dir_recursive_absolute(root) != OK:
		fault = true
		return
	var names := DirAccess.get_files_at(root)
	names.sort()
	for name in names:
		if name.begins_with(PREFIX) and name.ends_with(".json"):
			if not _load_generation(name):
				fault = true
				return
		elif name.ends_with(".pending"):
			DirAccess.remove_absolute(root.path_join(name))
	var watermark := root.path_join("high_water")
	if FileAccess.file_exists(watermark):
		var expected := FileAccess.get_file_as_string(watermark)
		if not expected.is_valid_int() or int(expected) > generation:
			fault = true
			return
	if generation > 0:
		if not _publish_watermark(generation):
			fault = true
			return
		_reclaim()



func _load_generation(name: String) -> bool:
	var number := name.trim_prefix(PREFIX).trim_suffix(".json")
	if not number.is_valid_int() or int(number) <= generation:
		return false
	if generation > 0 and int(number) != generation + 1:
		return false
	var path := root.path_join(name)
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > CAP:
		return false
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK:
		return false
	var packet = parser.data
	if not packet is Dictionary or packet.get("version") != 1:
		return false
	var body = packet.get("body")
	if not body is String or body.sha256_text() != packet.get("checksum"):
		return false
	if parser.parse(body) != OK:
		return false
	var value = parser.data
	if not value is Dictionary or not value.get("commands") is Array:
		return false
	if value.get("status") not in ["ready", "pending", "synced", "paused", "blocked"]:
		return false
	if typeof(value.get("attempts")) != TYPE_FLOAT or typeof(value.get("retry_at")) != TYPE_FLOAT:
		return false
	for command in value.commands:
		if not command is String:
			return false
	state = value
	generation = int(number)
	return true


func commit(
	next: Dictionary, before_publish: Callable = Callable(), after_publish: Callable = Callable()
) -> bool:
	if fault:
		return false
	var number := generation + 1
	var destination := root.path_join("%s%010d.json" % [PREFIX, number])
	var pending := destination + ".pending"
	var body := JSON.stringify(next)
	var packet := JSON.stringify({"version": 1, "body": body, "checksum": body.sha256_text()})
	if packet.to_utf8_buffer().size() > CAP:
		return false
	var file := FileAccess.open(pending, FileAccess.WRITE)
	if file == null:
		fault = true
		return false
	file.store_string(packet)
	file.flush()
	var error := file.get_error()
	file.close()
	if before_publish.is_valid():
		before_publish.call()
	if error != OK or DirAccess.rename_absolute(pending, destination) != OK:
		fault = true
		return false
	if not _publish_watermark(number):
		fault = true
		return false
	if after_publish.is_valid():
		after_publish.call()
	generation = number
	state = next
	_reclaim()
	return true


func _reclaim() -> void:
	for name in DirAccess.get_files_at(root):
		var index := name.trim_prefix(PREFIX).trim_suffix(".json")
		if name.begins_with(PREFIX) and name.ends_with(".json") and index.is_valid_int():
			if int(index) < generation:
				DirAccess.remove_absolute(root.path_join(name))


func _publish_watermark(number: int) -> bool:
	var path := root.path_join("high_water")
	var pending := path + ".pending"
	var file := FileAccess.open(pending, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(str(number))
	file.flush()
	var error := file.get_error()
	file.close()
	return error == OK and DirAccess.rename_absolute(pending, path) == OK
