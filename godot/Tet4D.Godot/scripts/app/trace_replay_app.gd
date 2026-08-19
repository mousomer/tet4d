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
const CameraPresetScript = preload("res://scripts/presentation/camera_preset.gd")
const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")
const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")
const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")
const GhostPieceModelScript = preload("res://scripts/presentation/ghost_piece_model.gd")

const MODE_REPLAY := "replay"
const MODE_LIVE_2D := "live_2d"
const MODE_LIVE_3D := "live_3d"
const MODE_LIVE_4D := "live_4d"
const DEFAULT_LIVE_GRAVITY_INTERVAL_SECONDS := 0.5
const LIVE_GRAVITY_INTERVAL_SECONDS := DEFAULT_LIVE_GRAVITY_INTERVAL_SECONDS
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
var _live_3d_last_rotation_label := "none"
var _live_3d_last_rotation_status := "none"
var _live_4d_paused := false
var _live_4d_session_started := false
var _live_4d_last_rotation_label := "none"
var _live_4d_last_rotation_status := "none"
var _live_4d_basis = SliceBasis4DScript.identity()
var _live_4d_local_orientation = SliceLocalOrientationScript.new()
var _translation_frame := ControlFrameMappingScript.FRAME_RELATIVE
var _rotation_frame := ControlFrameMappingScript.FRAME_RELATIVE
var _live_tick_accumulator := 0.0
var _live_gravity_interval_seconds := DEFAULT_LIVE_GRAVITY_INTERVAL_SECONDS
var _active_live_setup: Dictionary = {}
var _live_repeat_elapsed := {
	"move_left": 0.0,
	"move_right": 0.0,
	"move_x_neg": 0.0,
	"move_x_pos": 0.0,
	"move_z_neg": 0.0,
	"move_z_pos": 0.0,
	"move_w_neg": 0.0,
	"move_w_pos": 0.0,
	"soft_drop": 0.0,
}
var _live_repeat_next := {
	"move_left": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_right": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_x_neg": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_x_pos": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_z_neg": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_z_pos": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_w_neg": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"move_w_pos": LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
	"soft_drop": LIVE_SOFT_DROP_REPEAT_INITIAL_DELAY_SECONDS,
}
var _live_repeat_held := {
	"move_left": false,
	"move_right": false,
	"move_x_neg": false,
	"move_x_pos": false,
	"move_z_neg": false,
	"move_z_pos": false,
	"move_w_neg": false,
	"move_w_pos": false,
	"soft_drop": false,
}
var _live_bridge = Tet4DCoreBridgeScript.new()
var _ghost_model = GhostPieceModelScript.new()
var _ghost_enabled := true
var _ghost_semantic_revision := ""
var _ghost_query_count := 0

var _world_root: Node3D
var _live_4d_presentation_root: Node3D
var _renderer: TraceSceneRenderer
var _camera_rig: CameraRig
var _world_environment: WorldEnvironment
@onready var _hud: ReplayHud = get_parent().get_node("ReplayHud") as ReplayHud


func _ready() -> void:
	# Input can arrive before deferred scene construction completes. Register the
	# action contract synchronously so every input callback sees a valid map.
	_ensure_input_map()
	call_deferred("_deferred_ready")


func _deferred_ready() -> void:
	_wire_hud()
	_build_world_in_game_viewport()
	_renderer.set_display_mode(_state.display_mode)
	_apply_world_palette(_state.display_mode)
	_hud.set_display_mode(_state.display_mode)
	_hud.apply_shell_settings()
	_load_bundle()


func _process(delta: float) -> void:
	if _pending_fit_view:
		_fit_view()
	if _is_live_mode():
		if not _live_mode_paused() and not _live_snapshot_game_over():
			_process_live_input_repeat(delta)
			_live_tick_accumulator += delta
			if _live_tick_accumulator >= _live_gravity_interval_seconds:
				_live_tick_accumulator = 0.0
				if _mode == MODE_LIVE_4D:
					_live_4d_command("tick")
				elif _mode == MODE_LIVE_3D:
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
			if not _state.loop_enabled:
				_state.is_playing = false
				_playback_accumulator = 0.0
				_refresh_hud()
				break
			_state.current_frame_index = 0
			_playback_accumulator = 0.0
			_refresh_snapshot()
			break
	_state.interpolation_alpha = clampf(_playback_accumulator, 0.0, 1.0)
	_refresh_render()
	_refresh_hud()


func _input(event: InputEvent) -> void:
	if _hud != null and _hud.handle_main_menu_shortcut(event):
		get_viewport().set_input_as_handled()
		return
	if not _is_live_viewer_active():
		return
	if _mode == MODE_LIVE_4D and _handle_live_4d_camera_input(event):
		get_viewport().set_input_as_handled()
		return
	if _is_live_mode() and _event_is_camera_mouse_input(event) and _mouse_event_in_game_viewport(event):
		_handle_camera_input(event)
		get_viewport().set_input_as_handled()
		return
	if _is_live_mode() and _event_is_space_pressed_once(event):
		_handle_live_space_hard_drop()
		get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	if _is_live_mode() and not _is_live_viewer_active():
		if _event_action_pressed(event, ["quit", "replay_quit"]) or _event_is_escape(event):
			_return_to_main_menu()
		return
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
	if _mode == MODE_LIVE_4D:
		if _handle_live_4d_input(event):
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
		if _hud.current_screen() == ReplayHud.SCREEN_MAIN_MENU:
			get_tree().quit()
		else:
			_return_to_main_menu()

	_handle_camera_input(event)


func _handle_camera_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var camera_control := LiveInputContractScript.camera_control_for_button(event.button_index)
		if camera_control == "camera_orbit":
			if event.pressed and event.double_click:
				_mouse_orbiting = false
				_mouse_panning = false
				_fit_view()
				return
			_mouse_orbiting = event.pressed
		elif camera_control == "camera_pan":
			_mouse_panning = event.pressed
		elif camera_control == "camera_zoom" and event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			if _camera_rig != null:
				_camera_rig.zoom(-1.0)
				_refresh_camera_status()
		elif camera_control == "camera_zoom" and event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			if _camera_rig != null:
				_camera_rig.zoom(1.0)
				_refresh_camera_status()
	elif event is InputEventMouseMotion:
		if _mouse_orbiting:
			if _mode == MODE_LIVE_4D:
				_apply_live_4d_orientation_drag(event.relative)
			elif _camera_rig != null:
				_camera_rig.orbit(event.relative)
				_refresh_camera_status()
		elif _mouse_panning:
			if _camera_rig != null:
				_camera_rig.pan_screen(event.relative)
				_refresh_camera_status()


func _event_is_camera_mouse_input(event: InputEvent) -> bool:
	if event is InputEventMouseMotion:
		return _mouse_orbiting or _mouse_panning
	if event is InputEventMouseButton:
		return LiveInputContractScript.is_camera_button(event.button_index)
	return false


func _mouse_event_in_game_viewport(event: InputEvent) -> bool:
	if _hud == null:
		return false
	if not (event is InputEventMouseButton or event is InputEventMouseMotion):
		return false
	var rect := _hud.game_viewport_global_rect()
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return false
	return rect.has_point(event.position)


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
	if _event_action_pressed_once(event, ["reset"]):
		_reset_view()
		return true
	if event.is_action_pressed("replay_toggle_help"):
		_hud.toggle_help()
		return true
	if event.is_action_pressed("quit"):
		_return_to_main_menu()
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
		_enter_live_4d_mode()
		return true
	if _event_action_pressed(event, ["live_pause", "live_3d_pause"]):
		_toggle_live_3d_pause()
		return true
	if _event_action_pressed(event, ["live_3d_reset"]):
		_reset_live_3d()
		return true
	if _event_action_pressed_once(event, ["reset"]):
		_reset_view()
		return true
	if event.is_action_pressed("replay_toggle_help"):
		_hud.toggle_help()
		return true
	if event.is_action_pressed("quit"):
		_return_to_main_menu()
		return true
	if _live_3d_paused or _live_snapshot_game_over():
		return _event_action_pressed(event, _live_3d_gameplay_action_names())
	if _event_action_pressed_once(event, ["live_3d_move_x_neg"]):
		_dispatch_live_3d_control_intent("move_x_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_move_x_pos"]):
		_dispatch_live_3d_control_intent("move_x_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_move_z_neg"]):
		_dispatch_live_3d_control_intent("move_z_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_move_z_pos"]):
		_dispatch_live_3d_control_intent("move_z_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_soft_drop"]):
		_dispatch_live_3d_gameplay_command("soft_drop")
		return true
	if _event_action_pressed_once(event, ["live_hard_drop", "live_3d_hard_drop"]):
		_dispatch_live_3d_gameplay_command("hard_drop")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xy_neg"]):
		_dispatch_live_3d_rotation_intent("rotate_xy_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xy_pos"]):
		_dispatch_live_3d_rotation_intent("rotate_xy_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xz_neg"]):
		_dispatch_live_3d_rotation_intent("rotate_xz_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_xz_pos"]):
		_dispatch_live_3d_rotation_intent("rotate_xz_pos")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_yz_neg"]):
		_dispatch_live_3d_rotation_intent("rotate_yz_neg")
		return true
	if _event_action_pressed_once(event, ["live_3d_rotate_yz_pos"]):
		_dispatch_live_3d_rotation_intent("rotate_yz_pos")
		return true
	return false


func _handle_live_4d_input(event: InputEvent) -> bool:
	if event.is_action_pressed("mode_toggle_replay_live"):
		_enter_replay_mode()
		return true
	if _handle_live_4d_camera_input(event):
		return true
	if _handle_live_4d_basis_input(event):
		return true
	if _event_action_pressed(event, ["live_pause", "live_4d_pause"]):
		_toggle_live_4d_pause()
		return true
	if _event_action_pressed(event, ["live_4d_reset"]):
		_reset_live_4d()
		return true
	if _event_is_escape(event):
		_return_to_main_menu()
		return true
	if _live_4d_paused or _live_snapshot_game_over():
		return _event_action_pressed(event, _live_4d_gameplay_action_names())
	if _event_action_pressed_once(event, ["live_4d_move_x_neg"]):
		_dispatch_live_4d_control_intent("move_x_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_move_x_pos"]):
		_dispatch_live_4d_control_intent("move_x_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_move_z_neg"]):
		_dispatch_live_4d_control_intent("move_z_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_move_z_pos"]):
		_dispatch_live_4d_control_intent("move_z_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_move_w_neg"]):
		_dispatch_live_4d_control_intent("move_w_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_move_w_pos"]):
		_dispatch_live_4d_control_intent("move_w_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_soft_drop"]):
		_dispatch_live_4d_gameplay_command("soft_drop")
		return true
	if _event_action_pressed_once(event, ["live_hard_drop", "live_4d_hard_drop"]):
		_dispatch_live_4d_gameplay_command("hard_drop")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_xy_neg"]):
		_dispatch_live_4d_rotation_intent("rotate_xy_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_xy_pos"]):
		_dispatch_live_4d_rotation_intent("rotate_xy_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_xz_neg"]):
		_dispatch_live_4d_rotation_intent("rotate_xz_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_xz_pos"]):
		_dispatch_live_4d_rotation_intent("rotate_xz_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_yz_neg"]):
		_dispatch_live_4d_rotation_intent("rotate_yz_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_yz_pos"]):
		_dispatch_live_4d_rotation_intent("rotate_yz_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_xw_neg"]):
		_dispatch_live_4d_rotation_intent("rotate_xw_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_xw_pos"]):
		_dispatch_live_4d_rotation_intent("rotate_xw_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_yw_neg"]):
		_dispatch_live_4d_rotation_intent("rotate_yw_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_yw_pos"]):
		_dispatch_live_4d_rotation_intent("rotate_yw_pos")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_zw_neg"]):
		_dispatch_live_4d_rotation_intent("rotate_zw_neg")
		return true
	if _event_action_pressed_once(event, ["live_4d_rotate_zw_pos"]):
		_dispatch_live_4d_rotation_intent("rotate_zw_pos")
		return true
	return false


func _handle_live_4d_camera_input(event: InputEvent) -> bool:
	if _event_action_pressed_once(event, ["live_4d_camera_yaw_left"]):
		_nudge_live_4d_local_yaw(-CameraRigScript.LIVE_4D_CAMERA_YAW_STEP_RAD)
		return true
	if _event_action_pressed_once(event, ["live_4d_camera_yaw_right"]):
		_nudge_live_4d_local_yaw(CameraRigScript.LIVE_4D_CAMERA_YAW_STEP_RAD)
		return true
	if _event_action_pressed_once(event, ["live_4d_camera_pitch_up"]):
		_nudge_live_4d_local_pitch(CameraRigScript.LIVE_4D_CAMERA_PITCH_STEP_RAD)
		return true
	if _event_action_pressed_once(event, ["live_4d_camera_pitch_down"]):
		_nudge_live_4d_local_pitch(-CameraRigScript.LIVE_4D_CAMERA_PITCH_STEP_RAD)
		return true
	if _event_is_live_4d_zoom_in(event):
		if _camera_rig != null:
			_camera_rig.zoom(-1.0)
			_refresh_camera_status()
		return true
	if _event_is_live_4d_zoom_out(event):
		if _camera_rig != null:
			_camera_rig.zoom(1.0)
			_refresh_camera_status()
		return true
	return false


func _apply_live_4d_orientation_drag(delta: Vector2) -> void:
	var sensitivity_factor := 1.0
	var invert_y := false
	var orbit_sensitivity := 0.01
	if _camera_rig != null:
		var preferences: Dictionary = _camera_rig.presentation_snapshot()
		sensitivity_factor = float(preferences.get("sensitivity_factor", 1.0))
		invert_y = bool(preferences.get("invert_y", false))
		orbit_sensitivity = _camera_rig.orbit_sensitivity
	var yaw_delta := -delta.x * orbit_sensitivity * sensitivity_factor
	var vertical_direction := 1.0 if invert_y else -1.0
	var pitch_delta := delta.y * orbit_sensitivity * sensitivity_factor * vertical_direction
	_set_live_4d_local_orientation(
		_live_4d_local_orientation.local_yaw + yaw_delta,
		_live_4d_local_orientation.local_pitch + pitch_delta
	)


func _nudge_live_4d_local_yaw(delta_radians: float) -> void:
	var sensitivity_factor := 1.0
	if _camera_rig != null:
		sensitivity_factor = float(_camera_rig.presentation_snapshot().get("sensitivity_factor", 1.0))
	_set_live_4d_local_orientation(
		_live_4d_local_orientation.local_yaw + delta_radians * sensitivity_factor,
		_live_4d_local_orientation.local_pitch
	)


func _nudge_live_4d_local_pitch(delta_radians: float) -> void:
	var sensitivity_factor := 1.0
	var vertical_direction := 1.0
	if _camera_rig != null:
		var preferences: Dictionary = _camera_rig.presentation_snapshot()
		sensitivity_factor = float(preferences.get("sensitivity_factor", 1.0))
		vertical_direction = -1.0 if bool(preferences.get("invert_y", false)) else 1.0
	_set_live_4d_local_orientation(
		_live_4d_local_orientation.local_yaw,
		_live_4d_local_orientation.local_pitch + delta_radians * sensitivity_factor * vertical_direction
	)


# Sole normal-game semantic boundary for mutable shared L. It keeps renderer
# geometry, oriented bounds, the renderer fit reference, and resolver/HUD
# consumers on the same orientation without invoking a native transition.
func _set_live_4d_local_orientation(yaw_radians: float, pitch_radians: float) -> bool:
	var before := _live_4d_local_orientation.snapshot()
	_live_4d_local_orientation.set_normal_gameplay_angles(yaw_radians, pitch_radians)
	var after := _live_4d_local_orientation.snapshot()
	if before == after:
		return false
	_refresh_live_4d_presentation(true)
	_refresh_camera_status()
	return true


func _refresh_live_4d_presentation(reset_fit_reference: bool = false) -> void:
	if _mode != MODE_LIVE_4D or _renderer == null:
		return
	if reset_fit_reference:
		_renderer.reset_live_4d_fit_envelope()
	_renderer.set_live_4d_local_orientation(_live_4d_local_orientation)
	_refresh_render()
	_refresh_control_frame_presentation()


func _handle_live_4d_basis_input(event: InputEvent) -> bool:
	if _event_action_pressed_once(event, ["view_xw_neg"]):
		_apply_live_4d_basis_turn("xw", -1)
		return true
	if _event_action_pressed_once(event, ["view_xw_pos"]):
		_apply_live_4d_basis_turn("xw", 1)
		return true
	if _event_action_pressed_once(event, ["view_zw_neg"]):
		_apply_live_4d_basis_turn("zw", -1)
		return true
	if _event_action_pressed_once(event, ["view_zw_pos"]):
		_apply_live_4d_basis_turn("zw", 1)
		return true
	if _event_action_pressed_once(event, ["view_zx_neg"]):
		_apply_live_4d_basis_turn("zx", -1)
		return true
	if _event_action_pressed_once(event, ["view_zx_pos"]):
		_apply_live_4d_basis_turn("zx", 1)
		return true
	if _event_action_pressed_once(event, ["reset"]):
		_reset_view()
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
	_hud.replay_loop_changed.connect(func(enabled: bool) -> void:
		_state.loop_enabled = enabled
	)
	_hud.display_w_labels_changed.connect(func(visible: bool) -> void:
		_renderer.set_show_w_labels(visible)
		_refresh_render()
	)
	_hud.projection_strength_changed.connect(func(value: float) -> void:
		_renderer.set_projection_strength(value)
		_refresh_render()
	)
	_hud.board_detail_changed.connect(func(detail: String) -> void:
		_renderer.set_board_detail(detail)
		_refresh_render()
	)
	_hud.ghost_visibility_changed.connect(func(visible: bool) -> void:
		_ghost_enabled = visible
		if visible:
			_ghost_semantic_revision = ""
			_refresh_ghost_cache()
		else:
			_clear_ghost_cache()
		_refresh_render()
	)
	_hud.locked_cell_opacity_changed.connect(func(opacity: float) -> void:
		_renderer.set_locked_cell_opacity(opacity)
		_refresh_render()
	)
	_hud.grid_visibility_changed.connect(func(visible: bool) -> void:
		_renderer.set_grid_visible(visible)
		_refresh_render()
	)
	_hud.accessibility_policy_changed.connect(func(policy: Dictionary) -> void:
		_renderer.set_accessibility_policy(
			bool(policy.get("high_contrast", false)),
			bool(policy.get("reduced_motion", false))
		)
		_refresh_render()
	)
	_hud.camera_preferences_changed.connect(func(sensitivity_factor: float, invert_y: bool, interpolation_scale: float) -> void:
		if _camera_rig != null:
			_camera_rig.set_presentation_preferences(sensitivity_factor, invert_y, interpolation_scale)
			_refresh_camera_status()
	)
	_hud.camera_preset_requested.connect(func(id: String) -> void:
		var applied := _apply_live_4d_view_action(id) if _mode == MODE_LIVE_4D else (_camera_rig != null and _camera_rig.apply_outer_view_action(id))
		if applied and _camera_rig != null:
			_refresh_camera_status()
	)
	_hud.diagnostics_visibility_changed.connect(func(visible: bool) -> void:
		_state.diagnostics_visible = visible
		_refresh_hud()
	)
	_hud.display_mode_changed.connect(func(display_mode: String) -> void:
		_state.display_mode = ReplayVisuals.normalize_display_mode(display_mode)
		_renderer.set_display_mode(_state.display_mode)
		_apply_world_palette(_state.display_mode)
		_hud.set_display_mode(_state.display_mode)
		if not _current_snapshot.is_empty():
			_refresh_render()
		_refresh_hud()
	)
	_hud.fit_view_requested.connect(_fit_view)
	_hud.reset_view_requested.connect(_reset_view)
	_hud.quit_requested.connect(_quit_application)
	_hud.main_menu_requested.connect(_return_to_main_menu)
	_hud.live_2d_requested.connect(_enter_live_2d_mode)
	_hud.live_3d_requested.connect(_enter_live_3d_mode)
	_hud.live_4d_requested.connect(_enter_live_4d_mode)
	_hud.live_game_start_requested.connect(_start_configured_live_game)
	_hud.change_setup_requested.connect(_change_live_setup)
	_hud.new_random_game_requested.connect(_start_new_random_game)
	_hud.replay_mode_requested.connect(_enter_replay_mode)
	_hud.basis_turn_requested.connect(_apply_live_4d_basis_turn)


func _quit_application() -> void:
	get_tree().quit(0)


func _load_bundle() -> void:
	var result := BundleLoader.load_bundle(BUNDLE_ROOT)
	if not result.get("ok", false):
		_hud.set_bundle_status("Bundle: load failed", "Bundle load failed: %s" % result.get("error", "unknown error"))
		return
	_bundle = result
	var manifest: Dictionary = _bundle.get("manifest", {})
	var bundle_type := str(manifest.get("bundle_type", "bundle"))
	var digest := str(manifest.get("config", {}).get("combined_digest", ""))
	_hud.set_bundle_status(
		"Bundle: OK · %d cases" % _bundle_case_count(),
		"Bundle: %s · digest %s" % [bundle_type, digest]
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
		_hud.set_bundle_status("Bundle: no %s cases" % trace_type, "Bundle has no cases for selected trace family %s" % trace_type)
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
			_hud.set_bundle_status("Bundle: case load failed", "Bundle failed to load case %s" % case_id)
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
	if _mode == MODE_LIVE_4D:
		_toggle_live_4d_pause()
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
	if _mode == MODE_LIVE_4D:
		_reset_live_4d()
		return
	_state.reset(_state.is_playing)
	_playback_accumulator = 0.0
	_refresh_snapshot()


func _refresh_snapshot() -> void:
	if _current_document == null:
		return
	_current_snapshot = TraceSnapshotExtractor.extract(_current_document, _state.current_frame_index)
	_refresh_hud()
	_refresh_render()


func _refresh_render() -> void:
	if _is_live_mode():
		if not _current_snapshot.is_empty():
			_renderer.render_snapshot(_presentation_snapshot_for_render())
		return
	if _current_document == null or _current_snapshot.is_empty():
		return
	var next_snapshot := _next_snapshot()
	_renderer.render_interpolated_snapshot(_current_snapshot, next_snapshot, _state.interpolation_alpha)


func _presentation_snapshot_for_render() -> Dictionary:
	var presentation_snapshot := _current_snapshot.duplicate(true)
	presentation_snapshot["ghost_cells"] = _ghost_model.render_cells(_current_snapshot.get("active_cells", [])) if _ghost_enabled else []
	if _mode == MODE_LIVE_4D and _hud != null:
		var onboarding: Dictionary = _hud.onboarding_snapshot()
		var target_coordinate: Array = onboarding.get("target_coordinate", [])
		if bool(onboarding.get("visible", false)) and str(onboarding.get("step_id", "")) == "find_coordinate" and target_coordinate.size() == 4:
			var probes: Array = presentation_snapshot.get("probe_markers", []).duplicate(true)
			probes.append({"kind": "probe_after", "presentation_role": "lesson_target", "position": target_coordinate.duplicate()})
			presentation_snapshot["probe_markers"] = probes
	return presentation_snapshot


func _refresh_ghost_cache() -> void:
	if not _ghost_enabled or not _is_live_mode() or _current_snapshot.is_empty():
		_clear_ghost_cache()
		return
	var revision := "%s|%s" % [_mode, str(_current_snapshot.get("state_hash", ""))]
	if revision == _ghost_semantic_revision:
		return
	_ghost_semantic_revision = revision
	if bool(_current_snapshot.get("game_over", false)) or _current_snapshot.get("active_cells", []).is_empty():
		_ghost_model.clear()
		return
	var payload: Dictionary = {}
	match _mode:
		MODE_LIVE_2D:
			payload = _live_bridge.live_2d_hard_drop_destination()
		MODE_LIVE_3D:
			payload = _live_bridge.live_3d_hard_drop_destination()
		MODE_LIVE_4D:
			payload = _live_bridge.live_4d_hard_drop_destination()
	_ghost_query_count += 1
	if not _ghost_model.configure(payload, revision):
		push_warning("Authoritative ghost destination unavailable; ghost hidden for revision %s." % revision)


func _clear_ghost_cache() -> void:
	_ghost_semantic_revision = ""
	_ghost_model.clear()


func ghost_cache_snapshot() -> Dictionary:
	var result: Dictionary = _ghost_model.deterministic_snapshot()
	result["enabled"] = _ghost_enabled
	result["query_count"] = _ghost_query_count
	return result


func _apply_live_4d_view_action(id: String) -> bool:
	if _mode != MODE_LIVE_4D or _camera_rig == null or not CameraPresetScript.is_known(id):
		return false
	var preset := CameraPresetScript.definition(id)
	_set_live_4d_local_orientation(
		float(preset.get("yaw", _live_4d_local_orientation.local_yaw)),
		float(preset.get("pitch", _live_4d_local_orientation.local_pitch))
	)
	_camera_rig.restore_fitted_framing()
	return true


func _fit_view() -> void:
	_resolve_scene_nodes()
	if _camera_rig == null or _renderer == null:
		_pending_fit_view = true
		return
	var bounds := _renderer.current_bounds()
	if not bounds.get("ok", false):
		_pending_fit_view = true
		return
	var margin := 1.14
	if _mode == MODE_LIVE_2D:
		margin = CameraRigScript.LIVE_2D_FIT_MARGIN
	elif _mode == MODE_LIVE_3D:
		margin = CameraRigScript.LIVE_3D_FIT_MARGIN
	elif _mode == MODE_LIVE_4D:
		margin = CameraRigScript.LIVE_4D_FIT_MARGIN
	_camera_rig.fit_current_bounds(bounds, margin)
	_camera_rig.set_orientation_gizmo_visible(_mode in [MODE_LIVE_3D, MODE_LIVE_4D])
	_pending_fit_view = false
	_refresh_camera_status()


func _establish_canonical_view_and_fit(mode_name: String) -> void:
	_resolve_scene_nodes()
	if _camera_rig == null or _renderer == null:
		_pending_fit_view = true
		return
	if mode_name == MODE_LIVE_4D:
		_restore_live_4d_presentation_defaults()
		_refresh_live_4d_presentation(true)
	_camera_rig.establish_canonical_projection()
	match mode_name:
		MODE_LIVE_2D:
			_camera_rig.establish_outer_view(0.0, 0.0, 0.0, false)
		MODE_LIVE_3D:
			_camera_rig.establish_outer_view(
				CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD,
				CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD,
				0.0,
				false
			)
		MODE_LIVE_4D:
			_camera_rig.establish_outer_view(
				CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD,
				CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD,
				0.0,
				true
			)
		_:
			_camera_rig.establish_outer_view(
				CameraRigScript.PYTHON_DISPLAY_YAW_RAD,
				CameraRigScript.PYTHON_DISPLAY_PITCH_RAD,
				0.0,
				false
			)
	_fit_view()


func _reset_view() -> void:
	_establish_canonical_view_and_fit(_mode)
	_refresh_hud()


func _resolve_scene_nodes() -> void:
	if _world_root == null:
		_build_world_in_game_viewport()
	if _renderer == null:
		_renderer = _world_root.get_node_or_null("Live4DPresentationRoot/TraceSceneRenderer") as TraceSceneRenderer
	if _camera_rig == null:
		_camera_rig = _world_root.get_node_or_null("CameraRig") as CameraRig
	if _live_4d_presentation_root == null:
		_live_4d_presentation_root = _world_root.get_node_or_null("Live4DPresentationRoot") as Node3D
	if _camera_rig != null:
		_camera_rig.set_world_presentation_root(_live_4d_presentation_root)


func _build_world_in_game_viewport() -> void:
	if _world_root != null:
		return
	_world_root = Node3D.new()
	_world_root.name = "WorldRoot"
	_live_4d_presentation_root = Node3D.new()
	_live_4d_presentation_root.name = "Live4DPresentationRoot"
	_world_root.add_child(_live_4d_presentation_root)

	_renderer = TraceSceneRendererScript.new() as TraceSceneRenderer
	_renderer.name = "TraceSceneRenderer"
	_renderer.set_live_4d_basis(_live_4d_basis, false)
	_renderer.set_live_4d_local_orientation(_live_4d_local_orientation)
	_live_4d_presentation_root.add_child(_renderer)

	_camera_rig = CameraRigScript.new() as CameraRig
	_camera_rig.name = "CameraRig"
	_world_root.add_child(_camera_rig)

	var camera := Camera3D.new()
	camera.name = "Camera3D"
	camera.current = true
	camera.fov = 50.0
	_camera_rig.add_child(camera)
	_camera_rig.set_world_presentation_root(_live_4d_presentation_root)

	var light := DirectionalLight3D.new()
	light.name = "DirectionalLight3D"
	light.rotation = Vector3(-0.785398, 0.523599, 0.0)
	light.light_energy = 2.2
	_world_root.add_child(light)

	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = ReplayVisuals.color_for_role(ReplayVisuals.ROLE_BACKGROUND, _state.display_mode)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.95, 0.98, 1, 1)
	environment.ambient_light_energy = 1.85
	environment.glow_enabled = false
	_world_environment = WorldEnvironment.new()
	_world_environment.name = "AmbientWorld"
	_world_environment.environment = environment
	_world_root.add_child(_world_environment)

	_hud.set_world_root(_world_root)
	_refresh_camera_status()


func _apply_world_palette(display_mode: String) -> void:
	if _world_environment == null or _world_environment.environment == null:
		return
	_world_environment.environment.background_color = ReplayVisuals.color_for_role(
		ReplayVisuals.ROLE_BACKGROUND,
		display_mode
	)


func _refresh_hud() -> void:
	_refresh_control_frame_presentation()
	if _mode == MODE_LIVE_2D:
		var game_over := _live_snapshot_game_over()
		if not game_over:
			_hud.set_next_piece_preview(_live_bridge.live_2d_next_piece_preview())
		_hud.set_live_2d_mode(
			_live_2d_paused,
			game_over,
			_live_snapshot_last_command(),
			_live_snapshot_game_over_reason(),
			_live_gravity_interval_seconds
		)
	elif _mode == MODE_LIVE_3D:
		var game_over := _live_snapshot_game_over()
		if not game_over:
			_hud.set_next_piece_preview(_live_bridge.live_3d_next_piece_preview())
		_hud.set_live_3d_mode(
			_live_3d_paused,
			game_over,
			_live_snapshot_last_command(),
			_live_snapshot_game_over_reason(),
			_live_gravity_interval_seconds
		)
	elif _mode == MODE_LIVE_4D:
		var game_over := _live_snapshot_game_over()
		if not game_over:
			_hud.set_next_piece_preview(_live_bridge.live_4d_next_piece_preview())
		_hud.set_live_4d_basis_snapshot(_live_4d_basis_hud_snapshot())
		_hud.set_live_4d_mode(
			_live_4d_paused,
			game_over,
			_live_snapshot_last_command(),
			_live_snapshot_game_over_reason(),
			_live_gravity_interval_seconds
		)
	else:
		_hud.set_replay_mode_labels(_state.is_playing, _state.playback_speed, _state.diagnostics_visible)
	if _current_snapshot.is_empty():
		return
	_refresh_camera_status()
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


func _refresh_camera_status() -> void:
	if _hud == null:
		return
	_resolve_scene_nodes()
	if _camera_rig != null and _camera_rig.has_method("view_status_text"):
		_hud.set_camera_status(_camera_rig.view_status_text())
	_refresh_control_frame_presentation()


func _live_4d_basis_hud_snapshot() -> Dictionary:
	var result: Dictionary = _live_4d_basis.indicator_snapshot()
	var shape: Array = _current_snapshot.get("board_shape", [])
	result["visible_dimensions"] = _live_4d_basis.visible_dimensions(shape) if shape.size() == 4 else []
	result["layer_count"] = _live_4d_basis.layer_count(shape) if shape.size() == 4 else 1
	var active_layers := []
	if shape.size() == 4:
		for cell in _current_snapshot.get("active_cells", []):
			var mapped: Dictionary = _live_4d_basis.presentation_coordinate(cell.get("position", []), shape)
			if bool(mapped.get("ok", false)) and not active_layers.has(int(mapped.get("layer_index", -1))):
				active_layers.append(int(mapped.get("layer_index", -1)))
	active_layers.sort()
	result["active_layers"] = active_layers
	return result


func _sync_control_frames_from_setup() -> void:
	if _hud == null or not _hud.has_method("live_control_frames"):
		return
	var frames: Dictionary = _hud.live_control_frames()
	_translation_frame = ControlFrameMappingScript.normalize_frame(str(frames.get("translation_frame", _translation_frame)))
	_rotation_frame = ControlFrameMappingScript.normalize_frame(str(frames.get("rotation_frame", _rotation_frame)))


func _refresh_control_frame_presentation() -> void:
	if _mode not in [MODE_LIVE_3D, MODE_LIVE_4D]:
		return
	var mapping = _control_frame_mapping(4 if _mode == MODE_LIVE_4D else 3)
	var snapshot: Dictionary = mapping.snapshot()
	snapshot["translation_frame"] = _translation_frame
	snapshot["rotation_frame"] = _rotation_frame
	if _camera_rig != null and _camera_rig.has_method("set_control_frame_mapping"):
		_camera_rig.set_control_frame_mapping(snapshot)
	if _hud != null and _hud.has_method("set_control_frame_snapshot"):
		_hud.set_control_frame_snapshot(snapshot)


func _bundle_case_count() -> int:
	var total := 0
	var cases_by_type: Dictionary = _bundle.get("cases_by_type", {})
	for key in cases_by_type.keys():
		total += (cases_by_type.get(key, []) as Array).size()
	return total


func _start_configured_live_game(setup: Dictionary, preserve_current_view: bool = false) -> void:
	_sync_control_frames_from_setup()
	var mode_name := str(setup.get("mode", ""))
	var configured := false
	var validation: Dictionary = {}
	match mode_name:
		MODE_LIVE_2D:
			validation = _live_bridge.live_2d_configure_checked(setup)
			configured = bool(validation.get("ok", false))
			_live_2d_session_started = configured
		MODE_LIVE_3D:
			validation = _live_bridge.live_3d_configure_checked(setup)
			configured = bool(validation.get("ok", false))
			_live_3d_session_started = configured
		MODE_LIVE_4D:
			validation = _live_bridge.live_4d_configure_checked(setup)
			configured = bool(validation.get("ok", false))
			_live_4d_session_started = configured
	if not configured:
		push_error("Native live session rejected setup: %s" % str(validation.get("errors", [])))
		return
	_active_live_setup = setup.duplicate(true)
	_live_gravity_interval_seconds = _gravity_interval_for_setup(_active_live_setup)
	match mode_name:
		MODE_LIVE_2D:
			_enter_live_2d_mode(preserve_current_view)
		MODE_LIVE_3D:
			_enter_live_3d_mode(preserve_current_view)
		MODE_LIVE_4D:
			_enter_live_4d_mode(preserve_current_view)


func _start_new_random_game() -> void:
	if _active_live_setup.is_empty() or str(_active_live_setup.get("random_mode", "")) != "true_random":
		return
	_start_configured_live_game(_active_live_setup.duplicate(true), true)


# tet4d-semantic-boundary: allow adapter-routing
func _gravity_interval_for_setup(setup: Dictionary) -> float:
	var config_bundle: Dictionary = _bundle.get("config", {})
	var source_files: Dictionary = config_bundle.get("source_files", {})
	var tuning_record: Dictionary = source_files.get("config/gameplay/tuning.json", {})
	var tuning: Dictionary = tuning_record.get("payload", {})
	var curves: Dictionary = tuning.get("speed_curve", {})
	var mode_name := str(setup.get("mode", ""))
	var curve_key := "2d" if mode_name == MODE_LIVE_2D else ("3d" if mode_name == MODE_LIVE_3D else "4d_plus")
	var curve: Dictionary = curves.get(curve_key, {})
	var speed := clampi(int(setup.get("initial_speed_level", 1)), 1, 10)
	var base_ms := int(curve.get("base_ms", int(DEFAULT_LIVE_GRAVITY_INTERVAL_SECONDS * 1000.0)))
	var min_ms := int(curve.get("min_ms", base_ms))
	return float(maxi(min_ms, int(base_ms / speed))) / 1000.0


func _enter_live_2d_mode(preserve_current_view: bool = false) -> void:
	_prepare_live_mode_entry(MODE_LIVE_2D, preserve_current_view)
	if not _live_2d_session_started:
		_live_bridge.live_2d_reset()
		_live_2d_session_started = true
	_refresh_live_2d_snapshot()
	if not preserve_current_view:
		_establish_canonical_view_and_fit(MODE_LIVE_2D)
	_hud.show_replay_viewer()


func _enter_live_3d_mode(preserve_current_view: bool = false) -> void:
	_prepare_live_mode_entry(MODE_LIVE_3D, preserve_current_view)
	if not _live_3d_session_started:
		_live_bridge.live_3d_reset()
		_live_3d_session_started = true
	_refresh_live_3d_snapshot()
	if not preserve_current_view:
		_establish_canonical_view_and_fit(MODE_LIVE_3D)
	_hud.show_replay_viewer()
	_refresh_live_3d_snapshot()


func _enter_live_4d_mode(preserve_current_view: bool = false) -> void:
	_prepare_live_mode_entry(MODE_LIVE_4D, preserve_current_view)
	if not _live_4d_session_started:
		_live_bridge.live_4d_reset()
		_live_4d_session_started = true
	_refresh_live_4d_snapshot()
	if not preserve_current_view:
		_establish_canonical_view_and_fit(MODE_LIVE_4D)
	_hud.show_replay_viewer()
	_refresh_live_4d_snapshot()


func _prepare_live_mode_entry(mode_name: String, preserve_current_view: bool = false) -> void:
	if not preserve_current_view or _mode != mode_name:
		if _mode == MODE_LIVE_4D:
			_clear_live_4d_presentation_state(false)
		elif _camera_rig != null:
			_camera_rig.clear_presentation_state()
	_mode = mode_name
	_state.is_playing = false
	if mode_name == MODE_LIVE_4D:
		# A live 4D launch must never inherit a replay document as its first view.
		_current_document = null
	_hud.set_live_keyboard_capture(true)
	_clear_live_ui_focus()
	_live_2d_paused = mode_name != MODE_LIVE_2D
	_live_3d_paused = mode_name != MODE_LIVE_3D
	_live_4d_paused = mode_name != MODE_LIVE_4D
	_live_tick_accumulator = 0.0
	_reset_live_repeat_state()


func _return_to_main_menu() -> void:
	_state.is_playing = false
	_live_2d_paused = true
	_live_3d_paused = true
	_live_4d_paused = true
	_reset_live_repeat_state()
	_hud.set_live_keyboard_capture(false)
	_clear_ghost_cache()
	if _mode == MODE_LIVE_4D:
		_clear_live_4d_presentation_state(true)
	else:
		if _camera_rig != null:
			_camera_rig.clear_presentation_state()
		_refresh_render()
	_hud.show_screen(ReplayHud.SCREEN_MAIN_MENU)


func _change_live_setup(mode_name: String) -> void:
	_state.is_playing = false
	_live_2d_paused = true
	_live_3d_paused = true
	_live_4d_paused = true
	_reset_live_repeat_state()
	_hud.set_live_keyboard_capture(false)
	_clear_ghost_cache()
	if _mode == MODE_LIVE_4D:
		_clear_live_4d_presentation_state(true)
	else:
		if _camera_rig != null:
			_camera_rig.clear_presentation_state()
		_refresh_render()
	_hud.open_game_setup(mode_name)


func _enter_replay_mode() -> void:
	if _mode == MODE_LIVE_4D:
		_clear_live_4d_presentation_state(false)
	elif _camera_rig != null:
		_camera_rig.clear_presentation_state()
	_mode = MODE_REPLAY
	_clear_ghost_cache()
	_hud.set_live_keyboard_capture(false)
	_live_2d_paused = true
	_live_3d_paused = true
	_live_4d_paused = true
	_reset_live_repeat_state()
	if _current_document == null:
		var trace_type := _state.selected_trace_type if not _state.selected_trace_type.is_empty() else STARTUP_TRACE_TYPE
		_select_trace_family(trace_type, _choose_startup_case_id(trace_type), false, true)
	else:
		_refresh_snapshot()
	_establish_canonical_view_and_fit(MODE_REPLAY)
	_hud.show_replay_viewer()


func _clear_live_ui_focus() -> void:
	var viewport := get_viewport()
	if viewport == null:
		return
	var focus_owner := viewport.gui_get_focus_owner()
	if focus_owner != null:
		focus_owner.release_focus()


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


func _live_4d_command(command: String) -> void:
	if command == "hard_drop" or command == "soft_drop":
		_live_tick_accumulator = 0.0
	_live_bridge.live_4d_apply_command(command)
	_refresh_live_4d_snapshot()


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


func _dispatch_live_4d_gameplay_command(command: String) -> bool:
	if _live_4d_paused or _live_snapshot_game_over():
		return false
	_live_4d_command(command)
	return true


func _control_frame_mapping(dimension: int):
	if dimension >= 4:
		return ControlFrameMappingScript.for_4d(
			_live_4d_basis,
			_live_4d_local_orientation.local_yaw
		)
	var yaw := _camera_rig.control_frame_yaw() if _camera_rig != null and _camera_rig.has_method("control_frame_yaw") else 0.0
	return ControlFrameMappingScript.for_3d(yaw)


func _dispatch_live_3d_control_intent(intent: String) -> bool:
	return _dispatch_live_3d_gameplay_command(_control_frame_mapping(3).translation_command(intent, _translation_frame))


func _dispatch_live_3d_rotation_intent(intent: String) -> bool:
	return _dispatch_live_3d_gameplay_command(_control_frame_mapping(3).rotation_command(intent, _rotation_frame))


func _dispatch_live_4d_control_intent(intent: String) -> bool:
	return _dispatch_live_4d_gameplay_command(_control_frame_mapping(4).translation_command(intent, _translation_frame))


func _dispatch_live_4d_rotation_intent(intent: String) -> bool:
	return _dispatch_live_4d_gameplay_command(_control_frame_mapping(4).rotation_command(intent, _rotation_frame))


func _apply_live_4d_basis_turn(plane: String, direction: int) -> void:
	if _mode != MODE_LIVE_4D or _renderer == null:
		return
	_live_4d_basis = _live_4d_basis.turned(plane, direction)
	_renderer.set_live_4d_basis(_live_4d_basis, true)
	if _camera_rig != null:
		_camera_rig.set_orientation_basis(_live_4d_basis)
	_refresh_live_4d_presentation()
	_refresh_hud()


# Internal semantic seam used by lifecycle tests and future non-public tooling.
# It changes only exact presentation basis B and dependent layout/bounds.
func _reset_live_4d_basis_only() -> void:
	if _mode != MODE_LIVE_4D:
		return
	_live_4d_basis = SliceBasis4DScript.identity()
	if _renderer != null:
		_renderer.set_live_4d_basis(_live_4d_basis, false)
	if _camera_rig != null:
		_camera_rig.set_orientation_basis(_live_4d_basis)
	_refresh_live_4d_presentation()
	_refresh_hud()


# Restores the complete ephemeral Live-4D presentation state. Native gameplay,
# the frozen setup, and persisted shell preferences are deliberately excluded.
func _restore_live_4d_presentation_defaults() -> void:
	_live_4d_basis = SliceBasis4DScript.identity()
	_live_4d_local_orientation.set_normal_gameplay_angles(0.0, 0.0)
	if _renderer != null:
		_renderer.clear_presentation()
		_renderer.set_live_4d_basis(_live_4d_basis, false)
		_renderer.set_live_4d_local_orientation(_live_4d_local_orientation)
	if _camera_rig != null:
		_camera_rig.set_orientation_basis(_live_4d_basis)
	_pending_fit_view = false


# Tears down presentation authority at session/mode boundaries. Setting
# end_session marks the native session for reconstruction on its next entry;
# native deterministic state is otherwise untouched at teardown time.
func _clear_live_4d_presentation_state(end_session: bool) -> void:
	_restore_live_4d_presentation_defaults()
	if _camera_rig != null:
		_camera_rig.clear_presentation_state()
	_clear_ghost_cache()
	_live_4d_last_rotation_label = "none"
	_live_4d_last_rotation_status = "none"
	if end_session:
		_live_4d_session_started = false


func _reset_live_2d() -> void:
	_live_bridge.live_2d_reset()
	_live_2d_session_started = true
	_live_tick_accumulator = 0.0
	_live_2d_paused = false
	_reset_live_repeat_state()
	_refresh_live_2d_snapshot()


func _reset_live_3d() -> void:
	_live_3d_last_rotation_label = "none"
	_live_3d_last_rotation_status = "none"
	_live_bridge.live_3d_reset()
	_live_3d_session_started = true
	_live_tick_accumulator = 0.0
	_live_3d_paused = false
	_reset_live_repeat_state()
	_refresh_live_3d_snapshot()


func _reset_live_4d() -> void:
	_live_4d_last_rotation_label = "none"
	_live_4d_last_rotation_status = "none"
	_live_bridge.live_4d_reset()
	_live_4d_session_started = true
	_live_tick_accumulator = 0.0
	_live_4d_paused = false
	_reset_live_repeat_state()
	_refresh_live_4d_snapshot()


func _toggle_live_2d_pause() -> void:
	_live_2d_paused = not _live_2d_paused
	_reset_live_repeat_state()
	_refresh_hud()


func _toggle_live_3d_pause() -> void:
	_live_3d_paused = not _live_3d_paused
	_reset_live_repeat_state()
	_refresh_hud()


func _toggle_live_4d_pause() -> void:
	_live_4d_paused = not _live_4d_paused
	_reset_live_repeat_state()
	_refresh_hud()


func _process_live_input_repeat(delta: float) -> void:
	if _mode == MODE_LIVE_4D:
		_process_live_4d_input_repeat(delta)
		return
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


func _process_live_4d_input_repeat(delta: float) -> void:
	var x_neg_held := _any_action_pressed(["live_4d_move_x_neg"])
	var x_pos_held := _any_action_pressed(["live_4d_move_x_pos"])
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
	var z_neg_held := _any_action_pressed(["live_4d_move_z_neg"])
	var z_pos_held := _any_action_pressed(["live_4d_move_z_pos"])
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
	var w_neg_held := _any_action_pressed(["live_4d_move_w_neg"])
	var w_pos_held := _any_action_pressed(["live_4d_move_w_pos"])
	if w_neg_held and w_pos_held:
		_reset_live_repeat_action("move_w_neg")
		_reset_live_repeat_action("move_w_pos")
	else:
		_process_live_repeat_action(
			"move_w_neg",
			w_neg_held,
			"move_w_neg",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
		_process_live_repeat_action(
			"move_w_pos",
			w_pos_held,
			"move_w_pos",
			LIVE_HORIZONTAL_REPEAT_INITIAL_DELAY_SECONDS,
			LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS,
			delta
		)
	_process_live_repeat_action(
		"soft_drop",
		_any_action_pressed(["live_4d_soft_drop"]),
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
	if _mode == MODE_LIVE_4D:
		if command.begins_with("move_") and command not in ["move_up", "move_down"]:
			_dispatch_live_4d_control_intent(command)
		else:
			_dispatch_live_4d_gameplay_command(command)
	elif _mode == MODE_LIVE_3D:
		if command.begins_with("move_") and command not in ["move_up", "move_down"]:
			_dispatch_live_3d_control_intent(command)
		else:
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
	if _mode == MODE_LIVE_4D:
		return _live_4d_paused
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
	_refresh_ghost_cache()
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
		_update_live_3d_rotation_feedback(_current_snapshot)
	_refresh_ghost_cache()
	_refresh_render()
	_refresh_hud()


func _refresh_live_4d_snapshot() -> void:
	var parsed = JSON.parse_string(_live_bridge.live_4d_snapshot_json())
	if typeof(parsed) != TYPE_DICTIONARY:
		_current_snapshot = {
			"trace_type": "live_4d",
			"case_id": "live_plain_4d",
			"dimension": 4,
			"frame_index": 0,
			"frame_count": 1,
			"state_hash": _live_bridge.live_4d_state_hash(),
			"board_shape": [5, 10, 4, 4],
			"active_cells": [],
			"locked_cells": [],
			"probe_markers": [],
			"event_markers": [],
			"particles": [],
			"event_lines": [],
			"metadata_lines": ["Failed to parse native live 4D snapshot."],
			"diagnostics_lines": [_live_bridge.live_4d_status()],
			"energy_lines": [],
			"game_over": false,
			"game_over_reason": "",
			"paused": _live_4d_paused,
			"trace_name": "live_plain_4d",
			"entity_count": 0,
			"frame_count_matches_metadata": true,
			"entity_count_matches_metadata": true,
			"w_slice_count": 4,
			"active_w": 0,
		}
	else:
		_current_snapshot = parsed
		_current_snapshot["paused"] = _live_4d_paused
		_update_live_4d_rotation_feedback(_current_snapshot)
	_refresh_ghost_cache()
	_refresh_render()
	_refresh_hud()


func _update_live_3d_rotation_feedback(snapshot: Dictionary) -> void:
	var last_command := str(snapshot.get("last_command", ""))
	var rotation_label := _rotation_label_for_command(last_command)
	if rotation_label != "":
		_live_3d_last_rotation_label = rotation_label
		_live_3d_last_rotation_status = str(snapshot.get("last_command_status", "unknown"))
	snapshot["last_rotation_label"] = _live_3d_last_rotation_label
	snapshot["last_rotation_status"] = _live_3d_last_rotation_status


func _update_live_4d_rotation_feedback(snapshot: Dictionary) -> void:
	var last_command := str(snapshot.get("last_command", ""))
	var rotation_label := _rotation_label_for_command(last_command)
	if rotation_label != "":
		_live_4d_last_rotation_label = rotation_label
		_live_4d_last_rotation_status = str(snapshot.get("last_command_status", "unknown"))
	snapshot["last_rotation_label"] = _live_4d_last_rotation_label
	snapshot["last_rotation_status"] = _live_4d_last_rotation_status


func _rotation_label_for_command(command: String) -> String:
	match command:
		"rotate_xy_neg":
			return "XY-"
		"rotate_xy_pos":
			return "XY+"
		"rotate_xz_neg":
			return "XZ-"
		"rotate_xz_pos":
			return "XZ+"
		"rotate_yz_neg":
			return "YZ-"
		"rotate_yz_pos":
			return "YZ+"
		"rotate_xw_neg":
			return "XW-"
		"rotate_xw_pos":
			return "XW+"
		"rotate_yw_neg":
			return "YW-"
		"rotate_yw_pos":
			return "YW+"
		"rotate_zw_neg":
			return "ZW-"
		"rotate_zw_pos":
			return "ZW+"
		_:
			return ""


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


func _event_is_escape(event: InputEvent) -> bool:
	return event is InputEventKey and event.is_pressed() and (event as InputEventKey).keycode == KEY_ESCAPE


func _event_is_space_pressed_once(event: InputEvent) -> bool:
	return (
		event is InputEventKey
		and event.is_pressed()
		and not (event as InputEventKey).echo
		and (event as InputEventKey).keycode == KEY_SPACE
	)


func _event_is_live_4d_zoom_in(event: InputEvent) -> bool:
	if _event_action_pressed_once(event, ["live_4d_camera_zoom_in"]):
		return true
	return _event_key_pressed_once(event, [KEY_EQUAL, KEY_PLUS, KEY_KP_ADD], ["=", "+"])


func _event_is_live_4d_zoom_out(event: InputEvent) -> bool:
	if _event_action_pressed_once(event, ["live_4d_camera_zoom_out"]):
		return true
	return _event_key_pressed_once(event, [KEY_MINUS, KEY_KP_SUBTRACT], ["-"])


func _event_key_pressed_once(event: InputEvent, keycodes: Array, unicode_chars: Array) -> bool:
	if not (event is InputEventKey):
		return false
	var key_event := event as InputEventKey
	if not key_event.is_pressed() or key_event.echo:
		return false
	for keycode in keycodes:
		if key_event.keycode == keycode or key_event.physical_keycode == keycode:
			return true
	var typed_char := char(key_event.unicode) if key_event.unicode > 0 else ""
	return not typed_char.is_empty() and unicode_chars.has(typed_char)


func _handle_live_space_hard_drop() -> bool:
	if _mode == MODE_LIVE_4D:
		_dispatch_live_4d_gameplay_command("hard_drop")
	elif _mode == MODE_LIVE_3D:
		_dispatch_live_3d_gameplay_command("hard_drop")
	else:
		_dispatch_live_gameplay_command("hard_drop")
	return true


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


func _live_4d_gameplay_action_names() -> Array:
	return [
		"live_4d_move_x_neg",
		"live_4d_move_x_pos",
		"live_4d_move_z_neg",
		"live_4d_move_z_pos",
		"live_4d_move_w_neg",
		"live_4d_move_w_pos",
		"live_4d_soft_drop",
		"live_hard_drop",
		"live_4d_hard_drop",
		"live_4d_rotate_xy_neg",
		"live_4d_rotate_xy_pos",
		"live_4d_rotate_xz_neg",
		"live_4d_rotate_xz_pos",
		"live_4d_rotate_yz_neg",
		"live_4d_rotate_yz_pos",
		"live_4d_rotate_xw_neg",
		"live_4d_rotate_xw_pos",
		"live_4d_rotate_yw_neg",
		"live_4d_rotate_yw_pos",
		"live_4d_rotate_zw_neg",
		"live_4d_rotate_zw_pos",
		"view_xw_neg",
		"view_xw_pos",
		"view_zw_neg",
		"view_zw_pos",
		"view_zx_neg",
		"view_zx_pos",
	]


func _is_live_mode() -> bool:
	return _mode == MODE_LIVE_2D or _mode == MODE_LIVE_3D or _mode == MODE_LIVE_4D


func _is_live_viewer_active() -> bool:
	return _is_live_mode() and _hud != null and _hud.current_screen() == ReplayHud.SCREEN_VIEWER


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
	_remove_key_action("quit", KEY_Q)
	# These IDs were briefly registered during Stage 54E-2c. Normal gameplay
	# has no roll control; erase stale process-local registrations as well as
	# omitting them from the durable action contract.
	for obsolete_action in ["live_4d_camera_roll_left", "live_4d_camera_roll_right"]:
		if InputMap.has_action(obsolete_action):
			InputMap.erase_action(obsolete_action)
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
	_ensure_key_action("quit", KEY_ESCAPE)
	_ensure_key_action("mode_toggle_replay_live", KEY_TAB)
	var live_action_specs := LiveInputContractScript.action_specs()
	for action_name in live_action_specs:
		var spec: Dictionary = live_action_specs.get(action_name, {})
		for forbidden_key in spec.get("forbidden_keys", []):
			_remove_key_action(str(action_name), int(forbidden_key) as Key)
		for keycode in spec.get("keys", []):
			_ensure_key_action(str(action_name), int(keycode) as Key)
	_ensure_mouse_action("camera_orbit", LiveInputContractScript.CAMERA_ORBIT_BUTTON)
	_ensure_mouse_action("camera_pan", LiveInputContractScript.CAMERA_PAN_BUTTON)
	_ensure_mouse_action("camera_zoom", MOUSE_BUTTON_WHEEL_UP)


func _ensure_key_action(action_name: String, keycode: Key) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	var event := InputEventKey.new()
	event.keycode = keycode
	if not InputMap.action_has_event(action_name, event):
		InputMap.action_add_event(action_name, event)


func _remove_key_action(action_name: String, keycode: Key) -> void:
	if not InputMap.has_action(action_name):
		return
	for raw_event in InputMap.action_get_events(action_name):
		if raw_event is InputEventKey and (raw_event as InputEventKey).keycode == keycode:
			InputMap.action_erase_event(action_name, raw_event)


func _ensure_mouse_action(action_name: String, button_index: MouseButton) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	var event := InputEventMouseButton.new()
	event.button_index = button_index
	if not InputMap.action_has_event(action_name, event):
		InputMap.action_add_event(action_name, event)
