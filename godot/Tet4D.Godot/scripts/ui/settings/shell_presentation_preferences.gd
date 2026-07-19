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
const CONTRAST_MODES := ["standard", "high"]
const ANIMATION_MODES := ["reduced", "standard"]
const CAMERA_SENSITIVITY_FACTORS := {
	"low": 0.65,
	"standard": 1.0,
	"high": 1.45,
}
const CONTEXTUAL_HELP_MODES := ["automatic", "always", "hidden"]


static func ui_scale_factor(value: String) -> float:
	return float(UI_SCALE_FACTORS.get(value, UI_SCALE_FACTORS["standard"]))


static func camera_sensitivity_factor(value: String) -> float:
	return float(CAMERA_SENSITIVITY_FACTORS.get(value, CAMERA_SENSITIVITY_FACTORS["standard"]))


static func clamp_windowed_size(requested: Vector2i, minimum: Vector2i, usable_rect: Rect2i) -> Vector2i:
	var usable_size := usable_rect.size
	if usable_size.x <= 0 or usable_size.y <= 0:
		usable_size = Vector2i(maxi(requested.x, minimum.x), maxi(requested.y, minimum.y))
	var maximum := Vector2i(maxi(usable_size.x, minimum.x), maxi(usable_size.y, minimum.y))
	return Vector2i(
		clampi(requested.x, minimum.x, maximum.x),
		clampi(requested.y, minimum.y, maximum.y)
	)


static func size_from_value(value) -> Vector2i:
	if value is Array and value.size() == 2:
		return Vector2i(int(value[0]), int(value[1]))
	return Vector2i.ZERO


static func size_value(size: Vector2i) -> Array:
	return [size.x, size.y]
