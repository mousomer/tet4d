extends RefCounted


static func success(extra: Dictionary = {}) -> Dictionary:
	return _build(true, "", extra)


static func failure(message: String, extra: Dictionary = {}) -> Dictionary:
	return _build(false, message, extra)


static func _build(ok: bool, error: String, extra: Dictionary) -> Dictionary:
	var result := {"ok": ok, "error": error}
	result.merge(extra, true)
	return result
