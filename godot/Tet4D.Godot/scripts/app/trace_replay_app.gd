extends Node

class_name TraceReplayApp

const BUNDLE_ROOT := "res://assets/tet4d_bundle"
const TRACE_FAMILIES := ["topology", "gameplay", "endgame"]

var _bundle: Dictionary = {}
var _state := TracePlaybackState.new()
var _current_cases: Array = []
var _current_document: TraceDocument
var _current_snapshot: Dictionary = {}
var _playback_accumulator := 0.0
var _mouse_orbiting := false
var _mouse_panning := false

@onready var _world_root: Node = get_parent().get_node("WorldRoot")
@onready var _renderer: TraceSceneRenderer = _world_root.get_node("TraceSceneRenderer")
@onready var _camera_rig: CameraRig = _world_root.get_node("CameraRig")
@onready var _hud: ReplayHud = get_parent().get_node("UILayer/ReplayHud")


func _ready() -> void:
	call_deferred("_deferred_ready")


func _deferred_ready() -> void:
	_ensure_input_map()
	_wire_hud()
	_load_bundle()


func _process(delta: float) -> void:
	if _current_document == null or not _state.is_playing:
		return
	_playback_accumulator += delta * _state.playback_speed
	while _playback_accumulator >= 1.0:
		_playback_accumulator -= 1.0
		if not _advance_frame(1):
			_state.is_playing = false
			_refresh_hud()
			break


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("replay_prev_frame"):
		_step_frame(-1)
	elif event.is_action_pressed("replay_next_frame"):
		_step_frame(1)
	elif event.is_action_pressed("replay_play_pause"):
		_toggle_play_pause()
	elif event.is_action_pressed("replay_reset"):
		_reset_playback()
	elif event.is_action_pressed("replay_prev_case"):
		_select_case_relative(-1)
	elif event.is_action_pressed("replay_next_case"):
		_select_case_relative(1)
	elif event.is_action_pressed("replay_topology_family"):
		_select_trace_family("topology")
	elif event.is_action_pressed("replay_gameplay_family"):
		_select_trace_family("gameplay")
	elif event.is_action_pressed("replay_endgame_family"):
		_select_trace_family("endgame")

	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_mouse_orbiting = event.pressed and not Input.is_key_pressed(KEY_SHIFT)
			_mouse_panning = event.pressed and Input.is_key_pressed(KEY_SHIFT)
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_camera_rig.zoom(0.9)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_camera_rig.zoom(1.1)
	elif event is InputEventMouseMotion:
		if _mouse_orbiting:
			_camera_rig.orbit(event.relative)
		elif _mouse_panning:
			_camera_rig.pan(event.relative)


func _wire_hud() -> void:
	_hud.trace_family_selected.connect(_select_trace_family)
	_hud.case_selected.connect(_select_case)
	_hud.previous_frame_requested.connect(func() -> void:
		_step_frame(-1)
	)
	_hud.next_frame_requested.connect(func() -> void:
		_step_frame(1)
	)
	_hud.play_pause_requested.connect(_toggle_play_pause)
	_hud.reset_requested.connect(_reset_playback)
	_hud.frame_scrub_requested.connect(func(frame_index: int) -> void:
		_set_frame(frame_index)
	)
	_hud.playback_speed_changed.connect(func(value: float) -> void:
		_state.playback_speed = value
		_refresh_hud()
	)
	_hud.diagnostics_visibility_changed.connect(func(visible: bool) -> void:
		_state.diagnostics_visible = visible
		_refresh_hud()
	)


func _load_bundle() -> void:
	var result := BundleLoader.load_bundle(BUNDLE_ROOT)
	if not result.get("ok", false):
		_hud.set_bundle_status("Bundle status: load failed\n%s" % result.get("error", "unknown error"))
		return
	_bundle = result
	_hud.set_bundle_status(
		"Bundle status: %s  digest=%s" % [
			_bundle.get("manifest", {}).get("bundle_type", "bundle"),
			_bundle.get("manifest", {}).get("config", {}).get("combined_digest", ""),
		]
	)
	_state.selected_trace_type = "topology" if not _bundle.get("cases_by_type", {}).get("topology", []).is_empty() else TRACE_FAMILIES[0]
	_hud.set_trace_families(TRACE_FAMILIES, _state.selected_trace_type)
	_select_trace_family(_state.selected_trace_type)


func _select_trace_family(trace_type: String) -> void:
	if _bundle.is_empty():
		return
	_state.selected_trace_type = trace_type
	_current_cases = _bundle.get("cases_by_type", {}).get(trace_type, [])
	_hud.set_cases(_current_cases, "")
	if _current_cases.is_empty():
		_current_document = null
		_current_snapshot = {}
		_hud.set_bundle_status("Bundle status: no cases for %s" % trace_type)
		return
	_select_case(str(_current_cases[0].get("case_id", "")))


func _select_case(case_id: String) -> void:
	if case_id.is_empty():
		return
	for case_entry in _current_cases:
		if str(case_entry.get("case_id", "")) != case_id:
			continue
		var result := BundleLoader.load_trace_document(
			str(_bundle.get("bundle_root", BUNDLE_ROOT)),
			case_entry
		)
		if not result.get("ok", false):
			_hud.set_bundle_status("Bundle status: failed to load %s" % case_id)
			return
		_state.selected_case_id = case_id
		_state.reset()
		_current_document = result.get("document")
		_refresh_snapshot()
		_hud.set_cases(_current_cases, case_id)
		return


func _select_case_relative(delta: int) -> void:
	if _current_cases.is_empty():
		return
	var index := 0
	for item_index in range(_current_cases.size()):
		if str(_current_cases[item_index].get("case_id", "")) == _state.selected_case_id:
			index = item_index
			break
	index = clampi(index + delta, 0, _current_cases.size() - 1)
	_select_case(str(_current_cases[index].get("case_id", "")))


func _step_frame(delta: int) -> void:
	_state.is_playing = false
	_advance_frame(delta)


func _advance_frame(delta: int) -> bool:
	if _current_document == null:
		return false
	var next_frame := clampi(_state.current_frame_index + delta, 0, _current_document.frame_count() - 1)
	var changed := next_frame != _state.current_frame_index
	_state.current_frame_index = next_frame
	_refresh_snapshot()
	return changed


func _set_frame(frame_index: int) -> void:
	if _current_document == null:
		return
	_state.current_frame_index = clampi(frame_index, 0, _current_document.frame_count() - 1)
	_refresh_snapshot()


func _toggle_play_pause() -> void:
	if _current_document == null:
		return
	_state.is_playing = not _state.is_playing
	_refresh_hud()


func _reset_playback() -> void:
	_state.reset()
	_playback_accumulator = 0.0
	_refresh_snapshot()


func _refresh_snapshot() -> void:
	if _current_document == null:
		return
	_current_snapshot = TraceSnapshotExtractor.extract(_current_document, _state.current_frame_index)
	_renderer.render_snapshot(_current_snapshot)
	_camera_rig.frame_board(_current_snapshot.get("board_shape", []), int(_current_snapshot.get("dimension", 0)), _renderer.current_slice_stride)
	_refresh_hud()


func _refresh_hud() -> void:
	_hud.set_playback_state(_state.is_playing, _state.playback_speed, _state.diagnostics_visible)
	if _current_snapshot.is_empty():
		return
	_hud.set_summary(
		str(_current_snapshot.get("trace_type", "")),
		str(_current_snapshot.get("case_id", "")),
		int(_current_snapshot.get("dimension", 0)),
		int(_current_snapshot.get("frame_index", 0)),
		int(_current_snapshot.get("frame_count", 0)),
		str(_current_snapshot.get("state_hash", ""))
	)
	_hud.set_snapshot(_current_snapshot, _state.diagnostics_visible)


func _ensure_input_map() -> void:
	_ensure_key_action("replay_prev_frame", KEY_LEFT)
	_ensure_key_action("replay_next_frame", KEY_RIGHT)
	_ensure_key_action("replay_play_pause", KEY_SPACE)
	_ensure_key_action("replay_reset", KEY_R)
	_ensure_key_action("replay_prev_case", KEY_UP)
	_ensure_key_action("replay_next_case", KEY_DOWN)
	_ensure_key_action("replay_topology_family", KEY_1)
	_ensure_key_action("replay_gameplay_family", KEY_2)
	_ensure_key_action("replay_endgame_family", KEY_3)
	_ensure_mouse_action("camera_orbit", MOUSE_BUTTON_LEFT)
	_ensure_mouse_action("camera_zoom", MOUSE_BUTTON_WHEEL_UP)


func _ensure_key_action(action_name: String, keycode: Key) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	var event := InputEventKey.new()
	event.keycode = keycode
	if not InputMap.action_has_event(action_name, event):
		InputMap.action_add_event(action_name, event)


func _ensure_mouse_action(action_name: String, button_index: MouseButton) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	var event := InputEventMouseButton.new()
	event.button_index = button_index
	if not InputMap.action_has_event(action_name, event):
		InputMap.action_add_event(action_name, event)
