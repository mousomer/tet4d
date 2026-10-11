extends RefCounted

# One frozen snapshot owner for Designer and laboratory comparison previews.
signal changed

var _snapshots: Dictionary = {}
var _shown := "CURRENT"


func set_snapshot(side: String, snapshot: Dictionary) -> bool:
	if not ["A", "B"].has(side) or snapshot.is_empty():
		return false
	_snapshots[side] = snapshot.duplicate(true)
	changed.emit()
	return true


func snapshot_for(side: String) -> Dictionary:
	return _snapshots.get(side, {}).duplicate(true)


func ready() -> bool:
	return _snapshots.has("A") and _snapshots.has("B")


func show_side(side: String) -> bool:
	if not _snapshots.has(side):
		return false
	_shown = side
	changed.emit()
	return true


func show_current() -> void:
	_shown = "CURRENT"
	changed.emit()


func shown() -> String:
	return _shown


func clear() -> void:
	_snapshots.clear()
	show_current()
