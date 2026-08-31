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

const PRESETS := {
	ISO: {"id": ISO, "label": "Iso", "yaw": 0.5585053606381855, "pitch": 0.4537856055185257},
	FRONT: {"id": FRONT, "label": "Front", "yaw": 0.0, "pitch": 0.0},
	SIDE: {"id": SIDE, "label": "Side", "yaw": PI * 0.5, "pitch": 0.0},
	BACK: {"id": BACK, "label": "Back", "yaw": PI, "pitch": 0.0},
	TOP: {"id": TOP, "label": "Top", "yaw": 0.0, "pitch": 1.0471975511965976},
	OPPOSITE_ISO: {"id": OPPOSITE_ISO, "label": "Opposite Iso", "yaw": -2.5830872929516078, "pitch": 0.4537856055185257},
}


static func ids() -> Array:
	return [ISO, FRONT, SIDE, BACK, TOP, OPPOSITE_ISO]


static func definition(id: String) -> Dictionary:
	return PRESETS.get(id, {}).duplicate(true)


static func label(id: String) -> String:
	return str(definition(id).get("label", id))


static func is_known(id: String) -> bool:
	return PRESETS.has(id)
