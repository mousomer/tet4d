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


func topology_transport_profile(profile) -> Dictionary:
	return _api().topology_transport_profile(profile)


func native_topology_transport_query(profile, query) -> Dictionary:
	return _api().topology_transport_resolve_cell_step(profile, query)


func get_board_extent_contract() -> Dictionary:
	return _api().get_board_extent_contract()


# tet4d-semantic-boundary: allow adapter-routing
func validate_live_board_setup(setup: Dictionary) -> Dictionary:
	return _api().validate_live_board_setup(setup)


func live_2d_production_piece_catalog() -> Array:
	return _api().get_live_2d_production_piece_catalog()


func live_nd_production_piece_catalog() -> Array:
	return _api().get_live_nd_production_piece_catalog()


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


func live_configure(dimension: int, setup: Dictionary) -> bool:
	return bool(_api().live_configure(dimension, setup))


func live_configure_checked(dimension: int, setup: Dictionary) -> Dictionary:
	return _api().live_configure_checked(dimension, setup)


# Fixture seam only: resizes the unconfigured session's board while keeping its
# fixed piece order. Ordinary play configures through live_configure_checked.
func live_2d_configure_fixture_board(width: int, height: int) -> bool:
	return bool(_api().live_2d_configure_fixture_board(width, height))


func live_reset(dimension: int) -> void:
	_api().live_reset(dimension)


func live_apply_command(dimension: int, command: String) -> String:
	return _api().live_apply_command(dimension, command)


func live_tick(dimension: int) -> String:
	return _api().live_tick(dimension)


func live_snapshot_json(dimension: int) -> String:
	return _api().live_snapshot_json(dimension)


func live_next_piece_preview(dimension: int) -> Dictionary:
	return _api().live_next_piece_preview(dimension)


func live_held_piece_preview(dimension: int) -> Dictionary:
	return _api().live_held_piece_preview(dimension)


func live_hold_available(dimension: int) -> bool:
	return _api().live_hold_available(dimension)


func live_hard_drop_destination(dimension: int) -> Dictionary:
	return _api().live_hard_drop_destination(dimension)


func live_status(dimension: int) -> String:
	return _api().live_status(dimension)


func live_state_hash(dimension: int) -> String:
	return _api().live_state_hash(dimension)


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


func explorer_begin(dims: Array, original: Array, cells: Array, preset: String) -> Dictionary:
	return _api().explorer_begin(dims, original, cells, preset)


func explorer_move(axis: int, direction: int) -> Dictionary:
	return _api().explorer_move(axis, direction)


func explorer_retry() -> Dictionary:
	return _api().explorer_retry()


func explorer_rotate(direction: int) -> Dictionary:
	return _api().explorer_rotate(direction)


func explorer_undo() -> Dictionary:
	return _api().explorer_undo()


func explorer_neighbors(cell_id: int) -> Dictionary:
	return _api().explorer_neighbors(cell_id)
