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
const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")

const MODE_REPLAY := "replay"
const MODE_LIVE_2D := "live_2d"
const MODE_LIVE_3D := "live_3d"
const LIVE_GRAVITY_INTERVAL_SECONDS := 0.5
const LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS := 0.22
const LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS := 0.08
const LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS := 0.08
const LIVE_SOFT_DROP_REPEAT_INTERVAL_SECONDS := 0.055

var _bundle: Dictionary = {}
var _state := TracePlaybackState.new()
var _current_cases: Array = []
var _current_document: TraceDocument
var _current_snapshot: Dictionary = {}
var _playback_accumulator := 0.0
var _mouse_orbiting := false
var _mouse_panning := false
var _pending_fit_view := false
var _mode := MODE_REPLAY
var _live_2d_paused := false
var _live_2d_session_started := false
var _live_3d_paused := false
var _live_3d_session_started := false
var _live_tick_accumulator := 0.0
var _live_repeat_elapsed := {
	"move_left": 0.0,
	"move_right": 0.0,
	"move_x_neg": 0.0,
	"move_x_pos": 0.0,
	"move_z_neg": 0.0,
	"move_z_pos": 0.0,
	"soft_drop": 0.0,
}
var _live_repeat_next := {
	"move_left": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_right": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_x_neg": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_x_pos": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_z_neg": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_z_pos": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"soft_drop": LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS,
}
var _live_repeat_held := {
	"move_left": false,
	"move_right": false,
	"move_x_neg": false,
	"move_x_pos": false,
	"move_z_neg": false,
	"move_z_pos": false,
	"soft_drop": false,
}
var _live_bridge := Tet4DCoreBridgeScript.new()

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
	if _mode == MODE_LIVE_2D or _mode == MODE_LIVE_3D:
		if not _live_mode_paused() and not _live_snapshot_game_over():
			_process_live_input_repeat(delta)
			_live_tick_accumulator += delta
			if _live_tick_accumulator >= LIVE_GRAVITY_INTERVAL_SECONDS:
				_live_tick_accumulator = 0.0
				if _mode == MODE_LIVE_3D:
					_live_3d_command("tick")
				else:
					_live_2d_command("tick")
		return
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
	if _mode == MODE_LIVE_2D:
		if _handle_live_2d_input(event):
			return
		_handle_camera_input(event)
		return
	if _mode == MODE_LIVE_3D:
		if _handle_live_3d_input(event):
			return
		_handle_camera_input(event)
		return
	if event.is_action_pressed("mode_toggle_replay_live"):
		_enter_live_2d_mode()
		return
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
	elif _event_action_pressed(event, ["quit", "replay_quit"]):
		get_tree().quit()

	_handle_camera_input(event)


func _handle_camera_input(event: InputEvent) -> void:
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


func _handle_live_2d_input(event: InputEvent) -> bool:
	if event.is_action_pressed("mode_toggle_replay_live"):
		_enter_live_3d_mode()
		return true
	if _event_action_pressed(event, ["live_pause", "live_2d_pause"]):
		_toggle_live_2d_pause()
		return true
	if _event_action_pressed(event, ["live_reset", "replay_reset"]):
		_reset_live_2d()
		return true
	if event.is_action_pressed("replay_fit_view"):
		_fit_view()
		return true
	if event.is_action_pressed("replay_toggle_help"):
		_hud.toggle_help()
		return true
	if _event_action_pressed(event, ["quit", "replay_quit"]):
		get_tree().quit()
		return true
	if _live_2d_paused or _live_snapshot_game_over():
		return _event_action_pressed(event, _live_gameplay_action_names())
	if _event_action_pressed_once(event, ["live_move_left", "live_2d_move_left"]):
		_dispatch_live_gameplay_command("move_left")
		return true
	if _event_action_pressed_once(event, ["live_move_right", "live_2d_move_right"]):
		_dispatch_live_gameplay_command("move_right")
		return true
	if _event_action_pressed_once(event, ["live_rotate_cw", "live_2d_rotate_cw"]):
		_dispatch_live_gameplay_command("rotate_cw")
		return true
	if _event_action_pressed_once(event, ["live_rotate_ccw", "live_2d_rotate_ccw"]):
		_dispatch_live_gameplay_command("rotate_ccw")
		return true
	if _event_action_pressed_once(event, ["live_soft_drop", "live_2d_soft_drop"]):
		_dispatch_live_gameplay_command("soft_drop")
		return true
	if _event_action_pressed_once(event, ["live_hard_drop", "live_2d_hard_drop"]):
		_dispatch_live_gameplay_command("hard_drop")
		return true
	return false


func _handle_live_3d_input(event: InputEvent) -> bool:
	if event.is_action_pressed("mode_toggle_replay_live"):
		_enter_replay_mode()
		return true
	if _event_action_pressed(event, ["live_pause", "live_3d_pause"]):
		_toggle_live_3d_pause()
		return true
	if _event_action_pressed(event, ["live_3d_reset"]):
		_reset_live_3d()
		return true
	if event.is_action_pressed("replay_toggle_help"):
		_hud.toggle_help()
		return true
	if _event_action_pressed(event, ["quit", "replay_quit"]):
		get_tree().quit()
		return true
	if _live_3d_paused or _live_snapshot_game_over():
		return _event_action_pressed(event, _live_3d_gameplay_action_names())
	if _event_action_pressed_once(event, ["live_3d_move_x_neg"]):
		_dispatch_live_3d_gameplay_command("move_x_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_move_x_pos"]):
		_dispatch_live_3d_gameplay_command("move_x_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_move_z_neg"]):
		_dispatch_live_3d_gameplay_command("move_z_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_move_z_pos"]):
		_dispatch_live_3d_gameplay_command("move_z_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_soft_drop"]):
		_dispatch_live_3d_gameplay_command("soft_drop")
		return true
	if _event_action_pressed_once(event, ["live_hard_drop", "live_3d_hard_drop"]):
		_dispatch_live_3d_gameplay_command("hard_drop")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xy_neg"]):
		_dispatch_live_3d_gameplay_command("rotate_xy_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xy_pos"]):
		_dispatch_live_3d_gameplay_command("rotate_xy_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xz_neg"]):
		_dispatch_live_3d_gameplay_command("rotate_xz_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xz_pos"]):
		_dispatch_live_3d_gameplay_command("rotate_xz_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_yz_neg"]):
		_dispatch_live_3d_gameplay_command("rotate_yz_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_yz_pos"]):
		_dispatch_live_3d_gameplay_command("rotate_yz_pos")
		return true
	return false


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
	_hud.live_2d_requested.connect(_enter_live_2d_mode)
	_hud.live_3d_requested.connect(_enter_live_3d_mode)
	_hud.replay_mode_requested.connect(_enter_replay_mode)


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
	_mode = MODE_REPLAY
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
	_mode = MODE_REPLAY
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
	if _mode == MODE_LIVE_2D:
		_toggle_live_2d_pause()
		return
	if _mode == MODE_LIVE_3D:
		_toggle_live_3d_pause()
		return
	if _current_document == null:
		return
	_state.is_playing = not _state.is_playing
	_refresh_hud()


func _reset_playback() -> void:
	if _mode == MODE_LIVE_2D:
		_reset_live_2d()
		return
	if _mode == MODE_LIVE_3D:
		_reset_live_3d()
		return
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
	if _mode == MODE_LIVE_2D or _mode == MODE_LIVE_3D:
		if not _current_snapshot.is_empty():
			_renderer.render_snapshot(_current_snapshot)
		return
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
	if _mode == MODE_LIVE_2D:
		var game_over := _live_snapshot_game_over()
		_hud.set_live_2d_mode(
			_live_2d_paused,
			game_over,
			_live_snapshot_last_command(),
			_live_snapshot_game_over_reason(),
			LIVE_GRAVITY_INTERVAL_SECONDS
		)
	elif _mode == MODE_LIVE_3D:
		var game_over := _live_snapshot_game_over()
		_hud.set_live_3d_mode(
			_live_3d_paused,
			game_over,
			_live_snapshot_last_command(),
			_live_snapshot_game_over_reason(),
			LIVE_GRAVITY_INTERVAL_SECONDS
		)
	else:
		_hud.set_replay_mode_labels(_state.is_playing, _state.playback_speed, _state.diagnostics_visible)
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


func _enter_live_2d_mode() -> void:
	_mode = MODE_LIVE_2D
	_state.is_playing = false
	_live_3d_paused = true
	if not _live_2d_session_started:
		_live_bridge.live_2d_reset()
		_live_2d_session_started = true
		_live_2d_paused = false
	_live_tick_accumulator = 0.0
	_reset_live_repeat_state()
	_refresh_live_2d_snapshot()
	_fit_view()
	_hud.show_replay_viewer()


func _enter_live_3d_mode() -> void:
	_mode = MODE_LIVE_3D
	_state.is_playing = false
	_live_2d_paused = true
	if not _live_3d_session_started:
		_live_bridge.live_3d_reset()
		_live_3d_session_started = true
		_live_3d_paused = false
	_live_tick_accumulator = 0.0
	_reset_live_repeat_state()
	_refresh_live_3d_snapshot()
	_fit_view()
	_hud.show_replay_viewer()
	_refresh_live_3d_snapshot()


func _enter_replay_mode() -> void:
	_mode = MODE_REPLAY
	_live_2d_paused = true
	_live_3d_paused = true
	_reset_live_repeat_state()
	if _current_document == null:
		var trace_type := _state.selected_trace_type if not _state.selected_trace_type.is_empty() else STARTUP_TRACE_TYPE
		_select_trace_family(trace_type, _choose_startup_case_id(trace_type), false, true)
	else:
		_refresh_snapshot()
		_fit_view()
		_hud.show_replay_viewer()


func _live_2d_command(command: String) -> void:
	if command == "hard_drop" or command == "soft_drop":
		_live_tick_accumulator = 0.0
	_live_bridge.live_2d_apply_command(command)
	_refresh_live_2d_snapshot()


func _live_3d_command(command: String) -> void:
	if command == "hard_drop" or command == "soft_drop":
		_live_tick_accumulator = 0.0
	_live_bridge.live_3d_apply_command(command)
	_refresh_live_3d_snapshot()


func _dispatch_live_gameplay_command(command: String) -> bool:
	if _live_2d_paused or _live_snapshot_game_over():
		return false
	_live_2d_command(command)
	return true


func _dispatch_live_3d_gameplay_command(command: String) -> bool:
	if _live_3d_paused or _live_snapshot_game_over():
		return false
	_live_3d_command(command)
	return true


func _reset_live_2d() -> void:
	_live_bridge.live_2d_reset()
	_live_2d_session_started = true
	_live_tick_accumulator = 0.0
	_live_2d_paused = false
	_reset_live_repeat_state()
	_refresh_live_2d_snapshot()
	_fit_view()


func _reset_live_3d() -> void:
	_live_bridge.live_3d_reset()
	_live_3d_session_started = true
	_live_tick_accumulator = 0.0
	_live_3d_paused = false
	_reset_live_repeat_state()
	_refresh_live_3d_snapshot()
	_fit_view()


func _toggle_live_2d_pause() -> void:
	_live_2d_paused = not _live_2d_paused
	_reset_live_repeat_state()
	_refresh_hud()


func _toggle_live_3d_pause() -> void:
	_live_3d_paused = not _live_3d_paused
	_reset_live_repeat_state()
	_refresh_hud()


func _process_live_input_repeat(delta: float) -> void:
	if _mode == MODE_LIVE_3D:
		_process_live_3d_input_repeat(delta)
		return
	var left_held := _any_action_pressed(["live_move_left", "live_2d_move_left"])
	var right_held := _any_action_pressed(["live_move_right", "live_2d_move_right"])
	if left_held and right_held:
		_reset_live_repeat_action("move_left")
		_reset_live_repeat_action("move_right")
	else:
		_process_live_repeat_action(
			"move_left",
			left_held,
			"move_left",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
		_process_live_repeat_action(
			"move_right",
			right_held,
			"move_right",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
	_process_live_repeat_action(
		"soft_drop",
		_any_action_pressed(["live_soft_drop", "live_2d_soft_drop"]),
		"soft_drop",
		LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS,
		LIVE_SOFT_DROP_REPEAT_INTERVAL_SECONDS,
		delta
	)


func _process_live_3d_input_repeat(delta: float) -> void:
	var x_neg_held := _any_action_pressed(["live_3d_move_x_neg"])
	var x_pos_held := _any_action_pressed(["live_3d_move_x_pos"])
	if x_neg_held and x_pos_held:
		_reset_live_repeat_action("move_x_neg")
		_reset_live_repeat_action("move_x_pos")
	else:
		_process_live_repeat_action(
			"move_x_neg",
			x_neg_held,
			"move_x_neg",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
		_process_live_repeat_action(
			"move_x_pos",
			x_pos_held,
			"move_x_pos",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
	var z_neg_held := _any_action_pressed(["live_3d_move_z_neg"])
	var z_pos_held := _any_action_pressed(["live_3d_move_z_pos"])
	if z_neg_held and z_pos_held:
		_reset_live_repeat_action("move_z_neg")
		_reset_live_repeat_action("move_z_pos")
	else:
		_process_live_repeat_action(
			"move_z_neg",
			z_neg_held,
			"move_z_neg",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
		_process_live_repeat_action(
			"move_z_pos",
			z_pos_held,
			"move_z_pos",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
	_process_live_repeat_action(
		"soft_drop",
		_any_action_pressed(["live_3d_soft_drop"]),
		"soft_drop",
		LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS,
		LIVE_SOFT_DROP_REPEAT_INTERVAL_SECONDS,
		delta
	)


func _process_live_repeat_action(
	key: String,
	held: bool,
	command: String,
	initial_delay: float,
	repeat_interval: float,
	delta: float
) -> void:
	if not held:
		_reset_live_repeat_action(key)
		return
	if not bool(_live_repeat_held.get(key, false)):
		_live_repeat_held[key] = true
		_live_repeat_elapsed[key] = 0.0
		_live_repeat_next[key] = initial_delay
		return
	_live_repeat_elapsed[key] = float(_live_repeat_elapsed.get(key, 0.0)) + delta
	if float(_live_repeat_elapsed[key]) < float(_live_repeat_next[key]):
		return
	_live_repeat_elapsed[key] = 0.0
	_live_repeat_next[key] = repeat_interval
	if _mode == MODE_LIVE_3D:
		_dispatch_live_3d_gameplay_command(command)
	else:
		_dispatch_live_gameplay_command(command)


func _reset_live_repeat_state() -> void:
	for key in _live_repeat_held.keys():
		_reset_live_repeat_action(str(key))


func _reset_live_repeat_action(key: String) -> void:
	_live_repeat_held[key] = false
	_live_repeat_elapsed[key] = 0.0
	_live_repeat_next[key] = LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS if key == "soft_drop" else LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS


func _live_mode_paused() -> bool:
	return _live_3d_paused if _mode == MODE_LIVE_3D else _live_2d_paused


func _refresh_live_2d_snapshot() -> void:
	var parsed = JSON.parse_string(_live_bridge.live_2d_snapshot_json())
	if typeof(parsed) != TYPE_DICTIONARY:
		_current_snapshot = {
			"trace_type": "live_2d",
			"case_id": "live_plain_2d",
			"dimension": 2,
			"frame_index": 0,
			"frame_count": 1,
			"state_hash": _live_bridge.live_2d_state_hash(),
			"board_shape": [6, 6],
			"active_cells": [],
			"locked_cells": [],
			"probe_markers": [],
			"event_markers": [],
			"particles": [],
			"event_lines": [],
			"metadata_lines": ["Failed to parse native live snapshot."],
			"diagnostics_lines": [_live_bridge.live_2d_status()],
			"energy_lines": [],
			"game_over": false,
			"game_over_reason": "",
			"paused": _live_2d_paused,
			"trace_name": "live_plain_2d",
			"entity_count": 0,
			"frame_count_matches_metadata": true,
			"entity_count_matches_metadata": true,
		}
	else:
		_current_snapshot = parsed
		_current_snapshot["paused"] = _live_2d_paused
	_refresh_render()
	_refresh_hud()


func _refresh_live_3d_snapshot() -> void:
	var parsed = JSON.parse_string(_live_bridge.live_3d_snapshot_json())
	if typeof(parsed) != TYPE_DICTIONARY:
		_current_snapshot = {
			"trace_type": "live_3d",
			"case_id": "live_plain_3d",
			"dimension": 3,
			"frame_index": 0,
			"frame_count": 1,
			"state_hash": _live_bridge.live_3d_state_hash(),
			"board_shape": [6, 10, 6],
			"active_cells": [],
			"locked_cells": [],
			"probe_markers": [],
			"event_markers": [],
			"particles": [],
			"event_lines": [],
			"metadata_lines": ["Failed to parse native live 3D snapshot."],
			"diagnostics_lines": [_live_bridge.live_3d_status()],
			"energy_lines": [],
			"game_over": false,
			"game_over_reason": "",
			"paused": _live_3d_paused,
			"trace_name": "live_plain_3d",
			"entity_count": 0,
			"frame_count_matches_metadata": true,
			"entity_count_matches_metadata": true,
		}
	else:
		_current_snapshot = parsed
		_current_snapshot["paused"] = _live_3d_paused
	_refresh_render()
	_refresh_hud()


func _live_snapshot_last_command() -> String:
	var last_command := str(_current_snapshot.get("last_command", ""))
	if not last_command.is_empty():
		return last_command
	for line in _current_snapshot.get("diagnostics_lines", []):
		var text := str(line)
		if text.begins_with("last_command: "):
			return text.substr("last_command: ".length())
	return ""


func _live_snapshot_game_over() -> bool:
	if _current_snapshot.has("game_over"):
		return bool(_current_snapshot.get("game_over", false))
	for line in _current_snapshot.get("diagnostics_lines", []):
		if str(line) == "game_over: true":
			return true
	return false


func _live_snapshot_game_over_reason() -> String:
	var reason := str(_current_snapshot.get("game_over_reason", ""))
	if not reason.is_empty():
		return reason
	for line in _current_snapshot.get("diagnostics_lines", []):
		var text := str(line)
		if text.begins_with("game_over_reason: "):
			return text.substr("game_over_reason: ".length())
	return ""


func _event_action_pressed(event: InputEvent, action_names: Array) -> bool:
	for action_name in action_names:
		if event.is_action_pressed(str(action_name)):
			return true
	return false


func _event_action_pressed_once(event: InputEvent, action_names: Array) -> bool:
	if event is InputEventKey and (event as InputEventKey).echo:
		return false
	return _event_action_pressed(event, action_names)


func _any_action_pressed(action_names: Array) -> bool:
	for action_name in action_names:
		if Input.is_action_pressed(str(action_name)):
			return true
	return false


func _live_gameplay_action_names() -> Array:
	return [
		"live_move_left",
		"live_2d_move_left",
		"live_move_right",
		"live_2d_move_right",
		"live_rotate_cw",
		"live_2d_rotate_cw",
		"live_rotate_ccw",
		"live_2d_rotate_ccw",
		"live_soft_drop",
		"live_2d_soft_drop",
		"live_hard_drop",
		"live_2d_hard_drop",
	]


func _live_3d_gameplay_action_names() -> Array:
	return [
		"live_3d_move_x_neg",
		"live_3d_move_x_pos",
		"live_3d_move_z_neg",
		"live_3d_move_z_pos",
		"live_3d_soft_drop",
		"live_hard_drop",
		"live_3d_hard_drop",
		"live_3d_rotate_xy_neg",
		"live_3d_rotate_xy_pos",
		"live_3d_rotate_xz_neg",
		"live_3d_rotate_xz_pos",
		"live_3d_rotate_yz_neg",
		"live_3d_rotate_yz_pos",
	]


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
	_ensure_key_action("quit", KEY_Q)
	_ensure_key_action("quit", KEY_ESCAPE)
	_ensure_key_action("mode_toggle_replay_live", KEY_TAB)
	_ensure_key_action("live_move_left", KEY_LEFT)
	_ensure_key_action("live_move_left", KEY_A)
	_ensure_key_action("live_move_right", KEY_RIGHT)
	_ensure_key_action("live_move_right", KEY_D)
	_ensure_key_action("live_rotate_cw", KEY_UP)
	_ensure_key_action("live_rotate_cw", KEY_W)
	_ensure_key_action("live_rotate_cw", KEY_X)
	_ensure_key_action("live_rotate_ccw", KEY_Z)
	_ensure_key_action("live_soft_drop", KEY_DOWN)
	_ensure_key_action("live_soft_drop", KEY_S)
	_ensure_key_action("live_hard_drop", KEY_SPACE)
	_ensure_key_action("live_pause", KEY_P)
	_ensure_key_action("live_reset", KEY_R)
	_ensure_key_action("live_2d_move_left", KEY_LEFT)
	_ensure_key_action("live_2d_move_right", KEY_RIGHT)
	_ensure_key_action("live_2d_rotate_cw", KEY_UP)
	_ensure_key_action("live_2d_rotate_ccw", KEY_Z)
	_ensure_key_action("live_2d_soft_drop", KEY_DOWN)
	_ensure_key_action("live_2d_hard_drop", KEY_SPACE)
	_ensure_key_action("live_2d_pause", KEY_P)
	_ensure_key_action("live_3d_move_x_neg", KEY_LEFT)
	_ensure_key_action("live_3d_move_x_neg", KEY_A)
	_ensure_key_action("live_3d_move_x_pos", KEY_RIGHT)
	_ensure_key_action("live_3d_move_x_pos", KEY_D)
	_ensure_key_action("live_3d_move_z_neg", KEY_UP)
	_ensure_key_action("live_3d_move_z_neg", KEY_W)
	_ensure_key_action("live_3d_move_z_pos", KEY_DOWN)
	_ensure_key_action("live_3d_move_z_pos", KEY_S)
	_ensure_key_action("live_3d_soft_drop", KEY_SHIFT)
	_ensure_key_action("live_3d_hard_drop", KEY_SPACE)
	_ensure_key_action("live_3d_rotate_xy_neg", KEY_R)
	_ensure_key_action("live_3d_rotate_xy_pos", KEY_T)
	_ensure_key_action("live_3d_rotate_xz_neg", KEY_F)
	_ensure_key_action("live_3d_rotate_xz_pos", KEY_G)
	_ensure_key_action("live_3d_rotate_yz_neg", KEY_V)
	_ensure_key_action("live_3d_rotate_yz_pos", KEY_B)
	_ensure_key_action("live_3d_pause", KEY_P)
	_ensure_key_action("live_3d_reset", KEY_BACKSPACE)
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
