extends RefCounted

class_name TracePlaybackState

var selected_trace_type := "topology"
var selected_case_id := ""
var current_frame_index := 0
var is_playing := false
var playback_speed := 6.0
var diagnostics_visible := true


func reset() -> void:
	current_frame_index = 0
	is_playing = false
