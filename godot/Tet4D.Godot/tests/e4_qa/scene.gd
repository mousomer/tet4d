extends Control

const Client = preload("res://tests/e4_qa/client.gd")
const FakeTransport = preload("res://tests/e4_qa/fake_transport.gd")
const ROOT := "user://participant_data/e4_synthetic_qa"

var writer := Thread.new()
var active := false
var label: Label
var answer: LineEdit
var buttons: Array[Button] = []


func _ready() -> void:
	var column := VBoxContainer.new()
	add_child(column)
	column.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	column.position -= Vector2(245, 100)
	column.custom_minimum_size.x = 490
	var prompt := Label.new()
	prompt.text = "Synthetic assessment\nRotate (2, 1, 0, 0) by a positive quarter turn in the X–Z plane."
	column.add_child(prompt)
	label = Label.new()
	column.add_child(label)
	answer = LineEdit.new()
	answer.placeholder_text = "Enter four comma-separated integers"
	column.add_child(answer)
	_add_button(column, "Present synthetic item", "present")
	_add_button(column, "Save answer offline", "submit")
	_add_button(column, "Reconnect and flush", "flush")
	_start("inspect")


func _add_button(column: VBoxContainer, title: String, action: String) -> void:
	var button := Button.new()
	button.text = title
	button.pressed.connect(_start.bind(action))
	buttons.append(button)
	column.add_child(button)


func _start(action: String) -> void:
	if active:
		return
	var values: Array[int] = []
	if action == "submit":
		for part in answer.text.split(","):
			if not part.strip_edges().is_valid_int():
				label.text = "Enter four comma-separated integers."
				return
			values.append(int(part))
		if values.size() != 4:
			label.text = "Enter four comma-separated integers."
			return
	var now_ms := int(Time.get_unix_time_from_system() * 1000.0)
	var root := OS.get_environment("TET4D_E4_QA_ROOT")
	if root.is_empty():
		root = ROOT
	if writer.start(_operate.bind(root, action, values, now_ms)) != OK:
		label.text = "Could not start the journal worker."
		return
	active = true
	for button in buttons:
		button.disabled = true


static func _operate(root: String, action: String, values: Array[int], now_ms: int) -> String:
	var client := Client.new(root)
	var saved := true
	match action:
		"present": saved = client.present()
		"submit": saved = client.submit(values)
		"flush": client.flush(now_ms, FakeTransport.new(root).send)
		_: pass
	var status := client.state_name().capitalize()
	return status if saved else "Unchanged (%s). Action was not saved." % status


func _process(_delta: float) -> void:
	if active and not writer.is_alive():
		label.text = writer.wait_to_finish()
		active = false
		for button in buttons:
			button.disabled = false


func _exit_tree() -> void:
	if active:
		writer.wait_to_finish()
