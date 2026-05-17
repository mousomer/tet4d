extends RefCounted

class_name TracePlaybackState

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

var selected_trace_type := "topology"
var selected_case_id := ""
var current_frame_index := 0
var is_playing := false
var playback_speed := 2.0
var interpolation_alpha := 0.0
var diagnostics_visible := true
var display_mode := ReplayVisuals.default_display_mode()


func reset(playing: bool = false) -> void:
	current_frame_index = 0
	interpolation_alpha = 0.0
	is_playing = playing
