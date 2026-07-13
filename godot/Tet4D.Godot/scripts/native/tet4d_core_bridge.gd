extends RefCounted

class_name Tet4DCoreBridge

const CORE_CLASS := &"Tet4DCoreApi"
const EXTENSION_PATH := "res://addons/tet4d_core/tet4d_core.gdextension"

var _api_instance: RefCounted


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


func geometry_normalize_blocks(blocks: Array) -> Array:
	return _api().geometry_normalize_blocks(blocks)


func geometry_translate_blocks(blocks: Array, offset: Array) -> Array:
	return _api().geometry_translate_blocks(blocks, offset)


func geometry_rotate_blocks(blocks: Array, axis_a: int, axis_b: int, quarter_turns: int) -> Array:
	return _api().geometry_rotate_blocks(blocks, axis_a, axis_b, quarter_turns)


func geometry_hash_blocks(blocks: Array) -> String:
	return _api().geometry_hash_blocks(blocks)


func native_piece_pose_diagnostic(dims: Array, piece_cells: Array, occupied_cells: Array = []) -> Dictionary:
	return _api().query_piece_pose_legal(dims, piece_cells, occupied_cells)


func query_topology_axis_wrap_cell_step(dims: Array, wrapped_axes: Array, coord: Array, axis: int, delta: int) -> Dictionary:
	return _api().query_topology_axis_wrap_cell_step(dims, wrapped_axes, coord, axis, delta)


func run_builtin_plain_2d_smoke_case() -> bool:
	return bool(_api().run_builtin_plain_2d_smoke_case())


func list_plain_2d_parity_cases() -> PackedStringArray:
	return _api().list_plain_2d_parity_cases()


func get_plain_2d_parity_status() -> String:
	return _api().get_plain_2d_parity_status()


func export_plain_2d_trace_json(case_id: String = "gameplay_plain_2d_short") -> String:
	return _api().export_plain_2d_trace_json(case_id)


func get_plain_2d_required_field_parity(case_id: String = "gameplay_plain_2d_short") -> bool:
	return bool(_api().get_plain_2d_required_field_parity(case_id))


func run_builtin_plain_nd_smoke_case() -> bool:
	return bool(_api().run_builtin_plain_nd_smoke_case())


func list_plain_nd_parity_cases() -> PackedStringArray:
	return _api().list_plain_nd_parity_cases()


func get_plain_nd_parity_status() -> String:
	return _api().get_plain_nd_parity_status()


func export_plain_nd_trace_json(case_id: String = "gameplay_plain_3d_short") -> String:
	return _api().export_plain_nd_trace_json(case_id)


func get_plain_nd_required_field_parity(case_id: String = "gameplay_plain_3d_short") -> bool:
	return bool(_api().get_plain_nd_required_field_parity(case_id))


func live_2d_configure(board_shape: Array) -> bool:
	return bool(_api().live_2d_configure(board_shape))


func live_2d_reset() -> void:
	_api().live_2d_reset()


func live_2d_apply_command(command: String) -> String:
	return _api().live_2d_apply_command(command)


func live_2d_tick() -> String:
	return _api().live_2d_tick()


func live_2d_snapshot_json() -> String:
	return _api().live_2d_snapshot_json()


func live_2d_status() -> String:
	return _api().live_2d_status()


func live_2d_state_hash() -> String:
	return _api().live_2d_state_hash()


func live_3d_configure(board_shape: Array) -> bool:
	return bool(_api().live_3d_configure(board_shape))


func live_3d_reset() -> void:
	_api().live_3d_reset()


func live_3d_apply_command(command: String) -> String:
	return _api().live_3d_apply_command(command)


func live_3d_tick() -> String:
	return _api().live_3d_tick()


func live_3d_snapshot_json() -> String:
	return _api().live_3d_snapshot_json()


func live_3d_status() -> String:
	return _api().live_3d_status()


func live_3d_state_hash() -> String:
	return _api().live_3d_state_hash()


func live_4d_configure(board_shape: Array) -> bool:
	return bool(_api().live_4d_configure(board_shape))


func live_4d_reset() -> void:
	_api().live_4d_reset()


func live_4d_apply_command(command: String) -> String:
	return _api().live_4d_apply_command(command)


func live_4d_tick() -> String:
	return _api().live_4d_tick()


func live_4d_snapshot_json() -> String:
	return _api().live_4d_snapshot_json()


func live_4d_status() -> String:
	return _api().live_4d_status()


func live_4d_state_hash() -> String:
	return _api().live_4d_state_hash()


func _api() -> RefCounted:
	_ensure_extension_loaded()
	if _api_instance == null:
		_api_instance = ClassDB.instantiate(CORE_CLASS) as RefCounted
	if _api_instance == null:
		push_error("Tet4DCoreApi is unavailable. Build the Stage 8 GDExtension before running native bridge tests.")
	return _api_instance


func _ensure_extension_loaded() -> void:
	if ClassDB.class_exists(CORE_CLASS):
		return
	if GDExtensionManager.is_extension_loaded(EXTENSION_PATH):
		return
	var error := GDExtensionManager.load_extension(EXTENSION_PATH)
	if error != OK and error != ERR_ALREADY_EXISTS:
		push_error("Failed to load Stage 8 GDExtension at %s: %s" % [EXTENSION_PATH, error])
