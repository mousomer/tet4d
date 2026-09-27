extends RefCounted

class_name ShellPresentationPreferences

const WINDOWED := "windowed"
const FULLSCREEN := "fullscreen"
const UI_SCALE_FACTORS := {
	"small": 0.9,
	"standard": 1.0,
	"large": 1.15,
	"extra_large": 1.3,
}
const HUD_DENSITIES := ["compact", "standard", "detailed"]
const BOARD_DETAILS := ["minimal", "standard", "full"]
const CAMERA_SENSITIVITY_FACTORS := {
	"low": 0.65,
	"standard": 1.0,
	"high": 1.45,
}


static func ui_scale_factor(value: String) -> float:
	return float(UI_SCALE_FACTORS.get(value, UI_SCALE_FACTORS["standard"]))


static func camera_sensitivity_factor(value: String) -> float:
	return float(CAMERA_SENSITIVITY_FACTORS.get(value, CAMERA_SENSITIVITY_FACTORS["standard"]))


static func window_mode_value(window_mode: int) -> String:
	if window_mode in [Window.MODE_FULLSCREEN, Window.MODE_EXCLUSIVE_FULLSCREEN]:
		return FULLSCREEN
	return WINDOWED


static func clamp_windowed_size(requested: Vector2i, minimum: Vector2i, usable_rect: Rect2i) -> Vector2i:
	var usable_size := usable_rect.size
	if usable_size.x <= 0 or usable_size.y <= 0:
		usable_size = Vector2i(maxi(requested.x, minimum.x), maxi(requested.y, minimum.y))
	var maximum := Vector2i(maxi(usable_size.x, minimum.x), maxi(usable_size.y, minimum.y))
	return Vector2i(
		clampi(requested.x, minimum.x, maximum.x),
		clampi(requested.y, minimum.y, maximum.y)
	)


# The window server accepts backing-store pixels while the live-shell contract
# is expressed in player-visible points. A settings profile with no valid prior
# window size must therefore scale its logical default before the first restore.
# Existing persisted sizes already came from Window.size and must not be scaled.
static func fresh_windowed_size(
	requested_points: Vector2i,
	minimum_points: Vector2i,
	display_scale: float,
	usable_rect: Rect2i
) -> Vector2i:
	var scale := maxf(display_scale, 0.01)
	var requested_pixels := Vector2i(
		ceili(float(requested_points.x) * scale),
		ceili(float(requested_points.y) * scale)
	)
	var minimum_pixels := Vector2i(
		ceili(float(minimum_points.x) * scale),
		ceili(float(minimum_points.y) * scale)
	)
	return clamp_windowed_size(requested_pixels, minimum_pixels, usable_rect)


static func size_from_value(value) -> Vector2i:
	if value is Array and value.size() == 2:
		return Vector2i(int(value[0]), int(value[1]))
	return Vector2i.ZERO


static func size_value(size: Vector2i) -> Array:
	return [size.x, size.y]
