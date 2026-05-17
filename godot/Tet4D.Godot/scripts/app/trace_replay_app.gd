extends Node

class_name TraceReplayApp

const BUNDLE_ROOT := "res://assets/tet4d_bundle"
const TRACE_FAMILIES := ["topology", "gameplay", "endgame"]
const STARTUP_TRACE_TYPE := "endgame"
const STARTUP_CASE_CANDIDATES := [
	"endgame_4d_wrap_all",
	"endgame_4d_elastic_if_stable",
	"endgame_4d_no_collision",
]
const REPLAY_BASE_FPS := 4.0
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const TraceSceneRendererScript = preload("res://scripts/rendering/trace_scene_renderer.gd")
const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")

var _bundle: Dictionary = {}
var _state := TracePlaybackState.new()
var _current_cases: Array = []
var _current_document: TraceDocument
var _current_snapshot: Dictionary = {}
var _playback_accumulator := 0.0
var _mouse_orbiting := false
var _mouse_panning := false
var _pending_fit_view := false

var _world_root: Node3D
var _renderer: TraceSceneRenderer
var _camera_rig: CameraRig
@onready var _hud: ReplayHud = get_parent().get_node("ReplayHud") as ReplayHud


func _ready() -> void:
	call_deferred("_deferred_ready")


func _deferred_ready() -> void:
	_ensure_input_map()
	_wire_hud()
	_build_world_in_game_viewport()
	_renderer.set_display_mode(_state.display_mode)
	_hud.set_display_mode(_state.display_mode)
	_load_bundle()


func _process(delta: float) -> void:
	if _pending_fit_view:
		_fit_view()
	if _current_document == null or not _state.is_playing:
		return
	_playback_accumulator += delta * REPLAY_BASE_FPS * _state.playback_speed
	while _playback_accumulator >= 1.0:
		_playback_accumulator -= 1.0
		if not _advance_frame(1):
			_state.current_frame_index = 0
			_playback_accumulator = 0.0
			_refresh_snapshot()
			break
	_state.interpolation_alpha = clampf(_playback_accumulator, 0.0, 1.0)
	_refresh_render()
	_refresh_hud()


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
	elif event.is_action_pressed("replay_fit_view"):
		_fit_view()
	elif event.is_action_pressed("replay_toggle_help"):
		_hud.toggle_help()
	elif event.is_action_pressed("replay_quit"):
		get_tree().quit()

	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_mouse_orbiting = event.pressed and not Input.is_key_pressed(KEY_SHIFT)
			_mouse_panning = event.pressed and Input.is_key_pressed(KEY_SHIFT)
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			if _camera_rig != null:
				_camera_rig.zoom(0.9)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			if _camera_rig != null:
				_camera_rig.zoom(1.1)
	elif event is InputEventMouseMotion:
		if _camera_rig == null:
			return
		if _mouse_orbiting:
			_camera_rig.orbit(event.relative)
		elif _mouse_panning:
			_camera_rig.pan(event.relative)


func _wire_hud() -> void:
	_hud.trace_family_selected.connect(func(trace_type: String) -> void:
		_select_trace_family(trace_type, "", false, false)
	)
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
	_hud.display_mode_changed.connect(func(display_mode: String) -> void:
		_state.display_mode = ReplayVisuals.normalize_display_mode(display_mode)
		_renderer.set_display_mode(_state.display_mode)
		_hud.set_display_mode(_state.display_mode)
		if not _current_snapshot.is_empty():
			_refresh_render()
		_refresh_hud()
	)
	_hud.fit_view_requested.connect(_fit_view)
	_hud.quit_requested.connect(func() -> void:
		get_tree().quit()
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
	_state.selected_trace_type = STARTUP_TRACE_TYPE if not _bundle.get("cases_by_type", {}).get(STARTUP_TRACE_TYPE, []).is_empty() else TRACE_FAMILIES[0]
	_hud.set_trace_families(TRACE_FAMILIES, _state.selected_trace_type)
	_select_trace_family(_state.selected_trace_type, _choose_startup_case_id(_state.selected_trace_type), false, false)


func _select_trace_family(trace_type: String, preferred_case_id: String = "", start_playing: bool = false, open_case: bool = true) -> void:
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
	var case_id := preferred_case_id if not preferred_case_id.is_empty() else str(_current_cases[0].get("case_id", ""))
	if open_case:
		_select_case(case_id, start_playing)
	else:
		_hud.set_cases(_current_cases, case_id)


func _select_case(case_id: String, start_playing: bool = false) -> void:
	if case_id.is_empty():
		return
	for case_entry in _current_cases:
		if str(case_entry.get("case_id", "")) != case_id:
			continue
		var result: Dictionary = BundleLoader.load_trace_document(
			str(_bundle.get("bundle_root", BUNDLE_ROOT)),
			case_entry
		)
		if not result.get("ok", false):
			_hud.set_bundle_status("Bundle status: failed to load %s" % case_id)
			return
		_state.selected_case_id = case_id
		_state.reset(start_playing)
		_playback_accumulator = 0.0
		_current_document = result.get("document") as TraceDocument
		_refresh_snapshot()
		_fit_view()
		_hud.set_cases(_current_cases, case_id)
		_hud.show_replay_viewer()
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
	_playback_accumulator = 0.0
	_state.interpolation_alpha = 0.0
	_advance_frame(delta)


func _advance_frame(delta: int) -> bool:
	if _current_document == null:
		return false
	var next_frame := clampi(_state.current_frame_index + delta, 0, _current_document.frame_count() - 1)
	var changed := next_frame != _state.current_frame_index
	_state.current_frame_index = next_frame
	_state.interpolation_alpha = 0.0
	_refresh_snapshot()
	return changed


func _set_frame(frame_index: int) -> void:
	if _current_document == null:
		return
	_state.current_frame_index = clampi(frame_index, 0, _current_document.frame_count() - 1)
	_playback_accumulator = 0.0
	_state.interpolation_alpha = 0.0
	_refresh_snapshot()


func _toggle_play_pause() -> void:
	if _current_document == null:
		return
	_state.is_playing = not _state.is_playing
	_refresh_hud()


func _reset_playback() -> void:
	_state.reset(_state.is_playing)
	_playback_accumulator = 0.0
	_refresh_snapshot()
	_fit_view()


func _refresh_snapshot() -> void:
	if _current_document == null:
		return
	_current_snapshot = TraceSnapshotExtractor.extract(_current_document, _state.current_frame_index)
	_refresh_render()
	_refresh_hud()


func _refresh_render() -> void:
	if _current_document == null or _current_snapshot.is_empty():
		return
	var next_snapshot := _next_snapshot()
	_renderer.render_interpolated_snapshot(_current_snapshot, next_snapshot, _state.interpolation_alpha)


func _fit_view() -> void:
	_resolve_scene_nodes()
	if _camera_rig == null or _renderer == null or not _camera_rig.has_method("fit_bounds"):
		_pending_fit_view = true
		return
	var bounds := _renderer.current_bounds()
	if not bounds.get("ok", false):
		_pending_fit_view = true
		return
	_camera_rig.fit_bounds(bounds, 1.14)
	_pending_fit_view = false


func _resolve_scene_nodes() -> void:
	if _world_root == null:
		_build_world_in_game_viewport()
	if _renderer == null:
		_renderer = _world_root.get_node_or_null("TraceSceneRenderer") as TraceSceneRenderer
	if _camera_rig == null:
		_camera_rig = _world_root.get_node_or_null("CameraRig") as CameraRig


func _build_world_in_game_viewport() -> void:
	if _world_root != null:
		return
	_world_root = Node3D.new()
	_world_root.name = "WorldRoot"

	_renderer = TraceSceneRendererScript.new() as TraceSceneRenderer
	_renderer.name = "TraceSceneRenderer"
	_world_root.add_child(_renderer)

	_camera_rig = CameraRigScript.new() as CameraRig
	_camera_rig.name = "CameraRig"
	_world_root.add_child(_camera_rig)

	var camera := Camera3D.new()
	camera.name = "Camera3D"
	camera.current = true
	camera.fov = 50.0
	_camera_rig.add_child(camera)

	var light := DirectionalLight3D.new()
	light.name = "DirectionalLight3D"
	light.rotation = Vector3(-0.785398, 0.523599, 0.0)
	light.light_energy = 2.2
	_world_root.add_child(light)

	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.0196078, 0.027451, 0.0392157, 1)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.95, 0.98, 1, 1)
	environment.ambient_light_energy = 1.85
	environment.glow_enabled = false
	var world_environment := WorldEnvironment.new()
	world_environment.name = "AmbientWorld"
	world_environment.environment = environment
	_world_root.add_child(world_environment)

	_hud.set_world_root(_world_root)


func _refresh_hud() -> void:
	_hud.set_playback_state(_state.is_playing, _state.playback_speed, _state.diagnostics_visible)
	if _current_snapshot.is_empty():
		return
	_hud.set_summary(
		str(_current_snapshot.get("trace_type", "")),
		str(_current_snapshot.get("case_id", "")),
		int(_current_snapshot.get("dimension", 0)),
		int(_current_snapshot.get("frame_index", 0)),
		_next_frame_index(),
		int(_current_snapshot.get("frame_count", 0)),
		str(_current_snapshot.get("state_hash", ""))
	)
	_hud.set_snapshot(_current_snapshot, _state.diagnostics_visible)


func _next_snapshot() -> Dictionary:
	if _current_document == null:
		return {}
	return TraceSnapshotExtractor.extract(_current_document, _next_frame_index())


func _next_frame_index() -> int:
	if _current_document == null or _current_document.frame_count() <= 0:
		return 0
	if _state.current_frame_index >= _current_document.frame_count() - 1:
		return 0 if _state.is_playing else _state.current_frame_index
	return _state.current_frame_index + 1


func _choose_startup_case_id(trace_type: String) -> String:
	var cases: Array = _bundle.get("cases_by_type", {}).get(trace_type, [])
	if cases.is_empty():
		return ""
	for preferred in STARTUP_CASE_CANDIDATES:
		for case_entry in cases:
			if str(case_entry.get("case_id", "")) == preferred:
				return preferred
	for case_entry in cases:
		if str(case_entry.get("case_id", "")).contains("4d"):
			return str(case_entry.get("case_id", ""))
	return str(cases[0].get("case_id", ""))


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
	_ensure_key_action("replay_fit_view", KEY_F)
	_ensure_key_action("replay_toggle_help", KEY_H)
	_ensure_key_action("replay_quit", KEY_Q)
	_ensure_key_action("replay_quit", KEY_ESCAPE)
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
