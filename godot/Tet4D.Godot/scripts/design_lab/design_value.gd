extends RefCounted

class_name DesignValue


static func canonical_json(value) -> String:
	return JSON.stringify(_canonicalized(value), "", true)


static func canonical_hash(value) -> String:
	return canonical_json(value).sha256_text()


static func safe_copy(value):
	return value.duplicate(true) if value is Array or value is Dictionary else value


static func safe_id(value: String, max_length: int = 80) -> bool:
	if value.is_empty() or value.length() > max_length:
		return false
	for index in range(value.length()):
		var code := value.unicode_at(index)
		if not ((code >= 97 and code <= 122) or (code >= 48 and code <= 57) or code == 95 or code == 45):
			return false
	return true


static func timestamp_utc() -> String:
	return Time.get_datetime_string_from_system(true, true)


static func _canonicalized(value):
	if value is Dictionary:
		var result: Dictionary = {}
		var keys: Array = value.keys()
		keys.sort_custom(func(left, right) -> bool: return str(left) < str(right))
		for key in keys:
			result[str(key)] = _canonicalized(value.get(key))
		return result
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_canonicalized(item))
		return result
	# Godot's JSON parser may materialize an integral JSON number as a float.
	# Normalize mathematically integral values so persisted provenance hashes are
	# stable across the in-memory -> JSON -> in-memory boundary. Registry type
	# validation still distinguishes integer and float semantics separately.
	if value is float and is_finite(value) and floorf(value) == value:
		return int(value)
	return value
