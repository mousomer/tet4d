extends RefCounted

class_name Tet4DCoreBridge

const CORE_CLASS := &"Tet4DCoreApi"
const EXTENSION_PATH := "res://addons/tet4d_core/tet4d_core.gdextension"


func is_available() -> bool:
	_ensure_extension_loaded()
	return ClassDB.class_exists(CORE_CLASS)


func get_core_version() -> String:
	return _api().get_core_version()


func get_core_status() -> String:
	return _api().get_core_status()


func echo_text(text: String) -> String:
	return _api().echo_text(text)


func stable_hash_text(text: String) -> String:
	return _api().stable_hash_text(text)


func add_integers(a: int, b: int) -> int:
	return int(_api().add_integers(a, b))


func run_builtin_plain_2d_smoke_case() -> bool:
	return bool(_api().run_builtin_plain_2d_smoke_case())


func get_plain_2d_parity_status() -> String:
	return _api().get_plain_2d_parity_status()


func export_plain_2d_trace_json() -> String:
	return _api().export_plain_2d_trace_json()


func get_plain_2d_required_field_parity() -> bool:
	return bool(_api().get_plain_2d_required_field_parity())


func _api() -> RefCounted:
	_ensure_extension_loaded()
	var instance := ClassDB.instantiate(CORE_CLASS) as RefCounted
	if instance == null:
		push_error("Tet4DCoreApi is unavailable. Build the Stage 8 GDExtension before running native bridge tests.")
	return instance


func _ensure_extension_loaded() -> void:
	if ClassDB.class_exists(CORE_CLASS):
		return
	if GDExtensionManager.is_extension_loaded(EXTENSION_PATH):
		return
	var error := GDExtensionManager.load_extension(EXTENSION_PATH)
	if error != OK and error != ERR_ALREADY_EXISTS:
		push_error("Failed to load Stage 8 GDExtension at %s: %s" % [EXTENSION_PATH, error])
