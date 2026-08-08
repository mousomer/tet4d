extends RefCounted

class_name CameraPreset

# Presentation-only camera shortcuts.  These values deliberately contain no
# signed 4D basis or gameplay state; ControlFrameMapping quantizes the yaw.
const ISO := "iso"
const FRONT := "front"
const SIDE := "side"
const BACK := "back"
const TOP := "top"
const OPPOSITE_ISO := "opposite_iso"
const CUSTOM := "custom"

const PRESETS := {
	ISO: {"id": ISO, "label": "Iso", "yaw": 0.5585053606381855, "pitch": 0.4537856055185257, "zoom": 1.0, "pan": Vector3.ZERO},
	FRONT: {"id": FRONT, "label": "Front", "yaw": 0.0, "pitch": 0.0, "zoom": 1.0, "pan": Vector3.ZERO},
	SIDE: {"id": SIDE, "label": "Side", "yaw": PI * 0.5, "pitch": 0.0, "zoom": 1.0, "pan": Vector3.ZERO},
	BACK: {"id": BACK, "label": "Back", "yaw": PI, "pitch": 0.0, "zoom": 1.0, "pan": Vector3.ZERO},
	TOP: {"id": TOP, "label": "Top", "yaw": 0.0, "pitch": 1.0471975511965976, "zoom": 1.0, "pan": Vector3.ZERO},
	OPPOSITE_ISO: {"id": OPPOSITE_ISO, "label": "Opposite Iso", "yaw": -2.5830872929516078, "pitch": 0.4537856055185257, "zoom": 1.0, "pan": Vector3.ZERO},
}


static func ids() -> Array:
	return [ISO, FRONT, SIDE, BACK, TOP, OPPOSITE_ISO]


static func definition(id: String) -> Dictionary:
	return PRESETS.get(id, PRESETS[ISO]).duplicate(true)


static func label(id: String) -> String:
	if id == CUSTOM:
		return "Custom"
	return str(definition(id).get("label", "Iso"))


static func is_known(id: String) -> bool:
	return PRESETS.has(id)
