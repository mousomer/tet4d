extends RefCounted

class_name SafeAreaInsets

# Window-relative insets for displays whose usable area is smaller than the
# window: notches, camera housings, rounded corners, and home indicators on
# Android tablets and iPads.
#
# The shell keeps one cockpit layout for every platform. Handheld adaptation is
# expressed purely as additional outer margin, so nothing about the relative
# priority of the board, NEXT/HOLD, piece controls, or Design Laboratory
# changes. On desktop the safe area equals the window and every inset is zero,
# which makes this inert there by construction.
#
# The display reports its safe area in desktop coordinates, which share the
# window's origin only on the display at the desktop origin. A MacBook screen
# arranged below an external monitor starts at y=2952, so reading that
# position as an inset pushed the fullscreen cockpit entirely off-screen.
# Resolution therefore always works in window-local coordinates.

const ZERO := {"left": 0, "top": 0, "right": 0, "bottom": 0}


# Pure resolution so every device geometry can be asserted headlessly.
# `window_position` is the window's client-area origin in the same desktop
# coordinates as `safe_area`.
static func resolve(safe_area: Rect2i, window_size: Vector2i, window_position := Vector2i.ZERO) -> Dictionary:
	if window_size.x <= 0 or window_size.y <= 0:
		return ZERO.duplicate()
	if safe_area.size.x <= 0 or safe_area.size.y <= 0:
		return ZERO.duplicate()
	var local := Rect2i(safe_area.position - window_position, safe_area.size)
	# A safe area that does not sit inside the window (larger than it, or
	# reported for another display) cannot be interpreted as an inset; treat
	# it as no inset at all.
	if not Rect2i(Vector2i.ZERO, window_size).encloses(local):
		return ZERO.duplicate()
	return {
		"left": local.position.x,
		"top": local.position.y,
		"right": window_size.x - local.end.x,
		"bottom": window_size.y - local.end.y,
	}


static func current() -> Dictionary:
	return resolve(
		DisplayServer.get_display_safe_area(),
		DisplayServer.window_get_size(),
		DisplayServer.window_get_position()
	)


# The display reports insets in window pixels; layout runs in canvas units,
# which canvas_items stretch scales away from window pixels. A macOS notch is
# 78 backing pixels but only ~24 units of a 1280-unit canvas at 4112 pixels,
# so applying pixels directly left a ~54-unit dead band above the cockpit.
static func to_canvas(insets: Dictionary, window_size: Vector2i, canvas_size: Vector2) -> Dictionary:
	if window_size.x <= 0 or window_size.y <= 0 or canvas_size.x <= 0.0 or canvas_size.y <= 0.0:
		return ZERO.duplicate()
	var factor := canvas_size / Vector2(window_size)
	return {
		"left": int(ceilf(float(insets.get("left", 0)) * factor.x)),
		"top": int(ceilf(float(insets.get("top", 0)) * factor.y)),
		"right": int(ceilf(float(insets.get("right", 0)) * factor.x)),
		"bottom": int(ceilf(float(insets.get("bottom", 0)) * factor.y)),
	}


static func current_in_canvas(canvas_size: Vector2) -> Dictionary:
	return to_canvas(current(), DisplayServer.window_get_size(), canvas_size)
