extends RefCounted

const Session = preload("res://scripts/ui/designer_panel_session.gd")

class DetachedProbe extends Control:
	var detached := false
	func set_detached_layout(value: bool) -> void:
		detached = value


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var surface := VBoxContainer.new()
	surface.size = Vector2(1000, 700)
	tree.root.add_child(surface)
	var stage := HBoxContainer.new()
	stage.size_flags_vertical = Control.SIZE_EXPAND_FILL
	surface.add_child(stage)
	var deck := VBoxContainer.new()
	surface.add_child(deck)
	var board := VBoxContainer.new()
	board.name = "Board"
	stage.add_child(board)
	var first := VBoxContainer.new()
	first.name = "First"
	first.size_flags_horizontal = Control.SIZE_SHRINK_END
	first.size_flags_vertical = Control.SIZE_FILL
	first.size_flags_stretch_ratio = 2.5
	stage.add_child(first)
	var probe := DetachedProbe.new()
	first.add_child(probe)
	stage.add_child(Control.new()) # A non-detached sibling must retain its place.
	var second := VBoxContainer.new()
	second.name = "Second"
	stage.add_child(second)
	var third := VBoxContainer.new()
	third.name = "Third"
	third.hide()
	stage.add_child(third)
	var original_order := stage.get_children()
	var session = Session.new()
	surface.add_child(session)
	# Deliberately detach siblings out of their original order.
	var entries := [["Board", board, false], ["Second", second, true], ["First", first, true], ["Third", third, true]]
	session.open(surface, stage, deck, entries)
	for _frame in range(4):
		await tree.process_frame
	var old_frame = session.panels()["First"]
	session.set_restored_deck_visibility(false)
	session.close()
	if stage.get_children() != original_order or first.get_parent() != stage:
		failures.append("close must synchronously restore parent and original sibling indices")
	if first.size_flags_horizontal != Control.SIZE_SHRINK_END or first.size_flags_vertical != Control.SIZE_FILL or first.size_flags_stretch_ratio != 2.5:
		failures.append("close must restore the panel's original sizing flags")
	if probe.detached or third.visible or deck.visible or not stage.visible:
		failures.append("close must restore layout modes and original/requested visibility synchronously")
	if session.active() or not session.panels().is_empty() or session.surface_rect() != Rect2():
		failures.append("closed session must release its active surface and frames")
	# Reopen before the old queued frames are freed. Their callbacks must never
	# reset new detached controls or overwrite the new session's geometry.
	session.open(surface, stage, deck, entries)
	var current_geometry: Dictionary = session.geometry_snapshot()
	old_frame.geometry_edited.emit(Rect2(99, 99, 999, 999))
	if session.geometry_snapshot() != current_geometry:
		failures.append("old frame edits must not overwrite a reopened session")
	for _frame in range(4):
		await tree.process_frame
	if not probe.detached or session.panels().size() != 4:
		failures.append("old frame teardown must not reset the reopened detached layout")
	session.close()
	# Owner teardown with an active session must also be safe.
	session.open(surface, stage, deck, entries)
	surface.queue_free()
	await tree.process_frame
	return failures
