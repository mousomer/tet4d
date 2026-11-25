extends RefCounted

const Journal = preload("res://tests/e4_qa/journal.gd")
const SLOT := "00000000-0000-4000-8000-000000000001"
const MAX_ATTEMPTS := 4

var journal: RefCounted


func _init(directory: String) -> void:
	journal = Journal.new(directory)


func state_name() -> String:
	return "blocked" if journal.fault else journal.state.status


func present() -> bool:
	if state_name() != "ready":
		return false
	var next: Dictionary = journal.state.duplicate(true)
	next.commands.append(JSON.stringify({
		"id": _uuid(), "kind": "present", "observed_at": null, "slot": SLOT,
	}))
	next.status = "pending"
	return journal.commit(next)


func submit(response: Array[int]) -> bool:
	if state_name() != "pending" or journal.state.commands.size() != 1 or response.size() != 4:
		return false
	for coordinate in response:
		if coordinate < -2147483648 or coordinate > 2147483647:
			return false
	var next: Dictionary = journal.state.duplicate(true)
	next.commands.append(JSON.stringify({
		"attempt": _uuid(), "id": _uuid(), "kind": "submit", "latency_ms": 0,
		"observed_at": null, "response": response, "slot": SLOT,
	}))
	return journal.commit(next)


func flush(now_ms: int, send: Callable, after_ack: Callable = Callable()) -> String:
	var next: Dictionary = journal.state.duplicate(true)
	if state_name() != "pending" or next.commands.size() != 2 or now_ms < int(next.retry_at):
		return state_name()
	if int(next.attempts) >= MAX_ATTEMPTS:
		next.status = "paused"
		journal.commit(next)
		return state_name()
	var body := '{"version":1,"commands":[%s]}' % ",".join(next.commands)
	if body.to_utf8_buffer().size() > 65536:
		next.status = "blocked"
		journal.commit(next)
		return state_name()
	next.attempts = int(next.attempts) + 1
	next.retry_at = now_ms + 5000 * (1 << (int(next.attempts) - 1))
	if not journal.commit(next):
		return state_name()
	var reply: Dictionary = send.call(body)
	next = journal.state.duplicate(true)
	var code: int = reply.get("status", 0)
	if code == 200 and receipts_match(next.commands, reply.get("receipts")):
		next.status = "synced"
		next.commands = []
	elif code == 401 or code == 403:
		next.status = "paused"
	elif code not in [0, 429, 503, 200]:
		next.status = "blocked"
	elif code == 200:
		next.status = "blocked"
	else:
		next.retry_at = maxi(int(next.retry_at), now_ms + int(reply.get("retry_after_ms", 0)))
		if int(next.attempts) >= MAX_ATTEMPTS:
			next.status = "paused"
	var boundary := after_ack if next.status == "synced" else Callable()
	journal.commit(next, Callable(), boundary)
	return state_name()


static func receipts_match(commands: Array, receipts: Variant) -> bool:
	if not receipts is Array or receipts.size() != commands.size():
		return false
	var expected := {}
	for command: String in commands:
		var value = JSON.parse_string(command)
		if not value is Dictionary or expected.has(value.get("id")):
			return false
		expected[value.id] = digest(command)
	for receipt in receipts:
		if not receipt is Dictionary or not expected.has(receipt.get("command")):
			return false
		if expected[receipt.command] != receipt.get("digest"):
			return false
		if not _valid_receipt_time(receipt.get("received_at")):
			return false
		expected.erase(receipt.command)
	return expected.is_empty()


static func _valid_receipt_time(value: Variant) -> bool:
	if not value is String:
		return false
	var pattern := RegEx.create_from_string(
		"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\\.[0-9]{1,6})?(Z|\\+00:00)$"
	)
	if pattern.search(value) == null:
		return false
	var year := int(value.substr(0, 4))
	var month := int(value.substr(5, 2))
	var leap := year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
	var days := [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
	return year > 0 and int(value.substr(8, 2)) <= int(days[month - 1])


static func digest(canonical_command: String) -> String:
	return ('{"command":' + canonical_command + ',"version":1}').sha256_text()


static func _uuid() -> String:
	var bytes := Crypto.new().generate_random_bytes(16)
	bytes[6] = (bytes[6] & 15) | 64
	bytes[8] = (bytes[8] & 63) | 128
	var hex := bytes.hex_encode()
	return "%s-%s-%s-%s-%s" % [
		hex.substr(0, 8), hex.substr(8, 4), hex.substr(12, 4), hex.substr(16, 4), hex.substr(20)
	]
