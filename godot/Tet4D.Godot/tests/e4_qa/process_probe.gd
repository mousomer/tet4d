extends SceneTree
## Subprocess boundary driver. The outer test kills this process at the marker.

const Client = preload("res://tests/e4_qa/client.gd")
const FakeTransport = preload("res://tests/e4_qa/fake_transport.gd")


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var root := args[0]
	var mode := args[1]
	var client := Client.new(root)
	var values: Array[int] = [-3, 5, 1, 2]
	if mode == "verify":
		var expected := args[2]
		var matches := client.state_name() == expected
		if expected == "synced":
			matches = matches and client.journal.state.commands.is_empty()
		quit(0 if matches else 1)
		return
	if not client.present():
		quit(1)
		return
	var next: Dictionary = client.journal.state.duplicate(true)
	if mode == "before_publish":
		next.commands = []
		next.status = "synced"
		client.journal.commit(next, _park)
	elif mode == "after_publish":
		client.journal.commit(next, Callable(), _park)
	elif client.submit(values):
		var transport := FakeTransport.new(root)
		client.flush(10000, transport.send)
		client.flush(15000, transport.send, _park)
	quit(1)


func _park() -> void:
	print("E4_KILL_BOUNDARY")
	OS.delay_msec(30000)
