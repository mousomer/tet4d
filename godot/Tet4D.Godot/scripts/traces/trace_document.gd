extends RefCounted

class_name TraceDocument

var root: Dictionary = {}
var trace_type := ""
var case_id := ""
var dimension := 0
var topology_id := ""
var topology_preset := ""
var collision_mode := ""
var source_path := ""
var initial: Dictionary = {}
var final: Dictionary = {}
var frames: Array = []
var board_shape: Array = []


static func from_dictionary(data: Dictionary, trace_path: String = "") -> TraceDocument:
	var document := TraceDocument.new()
	document.root = data
	document.trace_type = str(data.get("trace_type", ""))
	document.case_id = str(data.get("case_id", ""))
	document.dimension = int(data.get("dimension", 0))
	document.topology_id = str(data.get("topology_id", ""))
	document.topology_preset = str(data.get("topology_preset", data.get("topology", "")))
	document.collision_mode = str(data.get("collision_mode", ""))
	document.source_path = trace_path
	document.initial = data.get("initial", {})
	document.final = data.get("final", {})
	document.frames = data.get("frames", [])
	document.board_shape = data.get("board_shape", [])
	if document.board_shape.is_empty():
		document.board_shape = document.initial.get("board_shape", [])
	if document.board_shape.is_empty():
		document.board_shape = document.initial.get("axis_sizes", [])
	return document


func frame_count() -> int:
	return frames.size()


func frame_at(frame_index: int) -> Dictionary:
	if frames.is_empty():
		return {}
	var clamped_index := clampi(frame_index, 0, frames.size() - 1)
	return frames[clamped_index]


func state_hash_at(frame_index: int) -> String:
	var frame := frame_at(frame_index)
	return str(frame.get("state_hash", final.get("state_hash", "")))
