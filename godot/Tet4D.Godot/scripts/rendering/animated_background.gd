extends MeshInstance3D

class_name AnimatedBackground

# Bounded environment-layer backdrop.
#
# It renders one screen-covering quad far behind the play volume, driven only by
# authorized `ENVIRONMENT_PRESENTATION` profile values, a locally owned phase,
# and semantic palette roles. It owns no gameplay, board, camera, or layout
# state, writes no depth, and cannot occlude foreground presentation.

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const BackgroundShader = preload("res://assets/shaders/animated_background.gdshader")

const MODE_NONE := "none"
const MODE_TRON_GRID_FLOW := "tron_grid_flow"
const SUPPORTED_MODES := [MODE_NONE, MODE_TRON_GRID_FLOW]

# Far enough behind the fitted play volume that ordinary depth testing always
# resolves in favour of gameplay, and inside the default camera far plane.
const BACKDROP_DISTANCE := 400.0
# Covers the widest supported orthographic frustum with generous margin.
const BACKDROP_EXTENT := 512.0
# Keeps the flow readable over long sessions without strobing.
const PHASE_RATE := 0.42
# Phase wraps on the shader lattice period so long sessions never lose precision.
const PHASE_PERIOD := 10.0

var _mode := MODE_NONE
var _intensity := 0.0
var _speed := 0.0
var _motion_scale := 1.0
var _phase := 0.0
var _display_mode := ReplayVisuals.DISPLAY_MODE_PLAIN
var _base_color := Color.BLACK
var _viewport_aspect := 1.7777778
var _material: ShaderMaterial


func _ready() -> void:
	name = "AnimatedBackground"
	set_meta("presentation_role", "environment_backdrop")
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	var quad := QuadMesh.new()
	quad.size = Vector2(BACKDROP_EXTENT, BACKDROP_EXTENT)
	mesh = quad
	_material = ShaderMaterial.new()
	_material.shader = BackgroundShader
	material_override = _material
	position = Vector3(0.0, 0.0, -BACKDROP_DISTANCE)
	_refresh_viewport_aspect()
	_push_uniforms()
	_refresh_surface_state()


func _process(delta: float) -> void:
	_refresh_viewport_aspect()
	advance_phase(delta)


func apply_presentation_profile(profile) -> bool:
	if profile == null or not profile.has_method("value"):
		return false
	var requested := str(profile.value("environment.background_animation_mode"))
	_mode = requested if SUPPORTED_MODES.has(requested) else MODE_NONE
	_intensity = clampf(float(profile.value("environment.background_animation_intensity")), 0.0, 1.0)
	_speed = maxf(float(profile.value("environment.background_animation_speed")), 0.0)
	# Accessibility motion policy composes over the aesthetic selection instead
	# of introducing a second motion preference.
	_motion_scale = 0.0 if bool(profile.value("accessibility.reduced_motion")) else 1.0
	# A frozen surface stops processing, so refresh the aspect on every apply.
	_refresh_viewport_aspect()
	_push_uniforms()
	_refresh_surface_state()
	return true


func set_display_mode(display_mode: String) -> void:
	_display_mode = ReplayVisuals.normalize_display_mode(display_mode)
	_push_uniforms()


func set_base_color(color: Color) -> void:
	_base_color = color
	_push_uniforms()


func set_viewport_aspect(aspect: float) -> void:
	_viewport_aspect = aspect if aspect > 0.01 else 1.7777778
	_push_uniforms()


func advance_phase(delta: float) -> void:
	if not animation_running():
		return
	_phase = fposmod(_phase + delta * PHASE_RATE * _speed * _motion_scale, PHASE_PERIOD)
	if _material != null:
		_material.set_shader_parameter("animation_phase", _phase)


func reset_phase() -> void:
	_phase = 0.0
	if _material != null:
		_material.set_shader_parameter("animation_phase", _phase)


func surface_animated() -> bool:
	return _mode != MODE_NONE and _intensity > 0.0


func animation_running() -> bool:
	return surface_animated() and _speed > 0.0 and _motion_scale > 0.0


func phase() -> float:
	return _phase


func mode() -> String:
	return _mode


func deterministic_snapshot() -> Dictionary:
	return {
		"mode": _mode,
		"intensity": _intensity,
		"speed": _speed,
		"motion_scale": _motion_scale,
		"animated": surface_animated(),
		"running": animation_running(),
		"phase": _phase,
		"display_mode": _display_mode,
		"base_color": _base_color,
		"line_color": _line_color(),
		"accent_color": _accent_color(),
		"visible": visible,
		"processing": is_processing(),
		"backdrop_distance": BACKDROP_DISTANCE,
		"viewport_aspect": _viewport_aspect,
		"shader_ready": _material != null and _material.shader == BackgroundShader,
	}


func _refresh_viewport_aspect() -> void:
	var viewport := get_viewport()
	if viewport == null:
		return
	var size := viewport.get_visible_rect().size
	if size.y <= 0.0:
		return
	set_viewport_aspect(size.x / size.y)


func _refresh_surface_state() -> void:
	visible = surface_animated()
	set_process(animation_running())
	if not surface_animated():
		reset_phase()


func _push_uniforms() -> void:
	if _material == null:
		return
	_material.set_shader_parameter("base_color", _base_color)
	_material.set_shader_parameter("line_color", _line_color())
	_material.set_shader_parameter("accent_color", _accent_color())
	_material.set_shader_parameter("animation_intensity", _intensity)
	_material.set_shader_parameter("animation_phase", _phase)
	_material.set_shader_parameter("viewport_aspect", _viewport_aspect)
	_material.set_shader_parameter("surface_active", 1.0 if surface_animated() else 0.0)


func _line_color() -> Color:
	return ReplayVisuals.color_for_role(ReplayVisuals.ROLE_LIVE_BOARD_GRID, _display_mode)


func _accent_color() -> Color:
	return ReplayVisuals.color_for_role(ReplayVisuals.ROLE_ACCENT, _display_mode)
