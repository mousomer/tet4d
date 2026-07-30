#include "tet4d_core_api.h"

#include "tet4d_core/core_api.hpp"
#include "tet4d_core/geometry.hpp"
#include "tet4d_core/plain_game_setup.hpp"
#include "tet4d_core/query.hpp"

#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/core/error_macros.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/char_string.hpp>
#include <godot_cpp/variant/variant.hpp>

#include <string>
#include <limits>
#include <optional>
#include <set>
#include <utility>
#include <vector>

namespace godot {
namespace {

std::string to_std_string(const String &text) {
	const CharString utf8 = text.utf8();
	return std::string(utf8.get_data());
}

String to_godot_string(const std::string &text) {
	return String::utf8(text.c_str());
}

tet4d::core::CoordND coord_from_array(const Array &values, bool &valid) {
	tet4d::core::CoordND coord;
	coord.values.reserve(static_cast<std::size_t>(values.size()));
	for (int64_t index = 0; index < values.size(); ++index) {
		const Variant value = values[index];
		if (value.get_type() != Variant::INT) {
			ERR_PRINT("Tet4D geometry coordinates must contain integer values.");
			valid = false;
			return {};
		}
		coord.values.push_back(static_cast<int>(value));
	}
	valid = true;
	return coord;
}

std::vector<int> ints_from_array(const Array &values, bool &valid) {
	std::vector<int> result;
	result.reserve(static_cast<std::size_t>(values.size()));
	for (int64_t index = 0; index < values.size(); ++index) {
		const Variant value = values[index];
		if (value.get_type() != Variant::INT) {
			ERR_PRINT("Tet4D query arrays must contain integer values.");
			valid = false;
			return {};
		}
		const int64_t integer = static_cast<int64_t>(value);
		if (integer < std::numeric_limits<int>::min() || integer > std::numeric_limits<int>::max()) {
			ERR_PRINT("Tet4D query integers exceed native range.");
			valid = false;
			return {};
		}
		result.push_back(static_cast<int>(integer));
	}
	valid = true;
	return result;
}

std::vector<tet4d::core::CoordND> blocks_from_array(const Array &blocks, bool &valid) {
	std::vector<tet4d::core::CoordND> result;
	result.reserve(static_cast<std::size_t>(blocks.size()));
	for (int64_t index = 0; index < blocks.size(); ++index) {
		const Variant value = blocks[index];
		if (value.get_type() != Variant::ARRAY) {
			ERR_PRINT("Tet4D geometry blocks must be arrays of integer coordinates.");
			valid = false;
			return {};
		}
		bool coord_valid = false;
		tet4d::core::CoordND coord = coord_from_array(static_cast<Array>(value), coord_valid);
		if (!coord_valid) {
			valid = false;
			return {};
		}
		result.push_back(std::move(coord));
	}
	valid = true;
	return result;
}

Dictionary legality_result_to_dictionary(const tet4d::core::LegalityQueryResult &result) {
	Dictionary dictionary;
	dictionary["ok"] = true;
	dictionary["legal"] = result.legal;
	dictionary["reason"] = to_godot_string(result.reason);
	return dictionary;
}

Dictionary query_error_dictionary(const String &message) {
	Dictionary dictionary;
	dictionary["ok"] = false;
	dictionary["legal"] = false;
	dictionary["reason"] = message;
	dictionary["error"] = message;
	return dictionary;
}

Array coord_to_array(const tet4d::core::CoordND &coord) {
	Array result;
	for (const int value : coord.values) {
		result.push_back(value);
	}
	return result;
}

Array blocks_to_array(const std::vector<tet4d::core::CoordND> &blocks) {
	Array result;
	for (const tet4d::core::CoordND &coord : blocks) {
		result.push_back(coord_to_array(coord));
	}
	return result;
}

String boundary_label(const tet4d::core::BoundaryQueryRef &boundary) {
	const char *names[] = {"x", "y", "z", "w"};
	return String(names[boundary.axis]) + (boundary.side < 0 ? "-" : "+");
}

String step_label(const tet4d::core::MoveStepQuery &step) {
	const char *names[] = {"x", "y", "z", "w"};
	return String(names[step.axis]) + (step.delta < 0 ? "-" : "+");
}

std::optional<tet4d::core::PlainGameSetup> plain_setup_from_dictionary(
		const Dictionary &payload,
		const std::string &expected_mode) {
	static const std::set<std::string> allowed_fields = {
		"schema_version",
		"mode",
		"board_preset_id",
		"board_shape",
		"piece_set_id",
		"random_mode",
		"seed",
		"initial_speed_level",
	};
	const Array keys = payload.keys();
	for (int64_t index = 0; index < keys.size(); ++index) {
		const Variant key_value = keys[index];
		if (key_value.get_type() != Variant::STRING &&
				key_value.get_type() != Variant::STRING_NAME) {
			ERR_PRINT("Tet4D live setup keys must be strings.");
			return std::nullopt;
		}
		const std::string key = to_std_string(static_cast<String>(key_value));
		if (allowed_fields.find(key) == allowed_fields.end()) {
			ERR_PRINT(("Tet4D live setup contains unsupported field: " + key).c_str());
			return std::nullopt;
		}
	}
	for (const char *required : {
			"schema_version",
			"mode",
			"board_preset_id",
			"board_shape",
			"piece_set_id",
			"random_mode",
			"initial_speed_level",
		}) {
		if (!payload.has(required)) {
			ERR_PRINT((std::string("Tet4D live setup missing required field: ") + required).c_str());
			return std::nullopt;
		}
	}
	const Variant schema_version = payload["schema_version"];
	const Variant mode = payload["mode"];
	const Variant preset_id = payload["board_preset_id"];
	const Variant board_shape = payload["board_shape"];
	const Variant piece_set_id = payload["piece_set_id"];
	const Variant random_mode = payload["random_mode"];
	const Variant speed_level = payload["initial_speed_level"];
	if (schema_version.get_type() != Variant::INT ||
			mode.get_type() != Variant::STRING ||
			preset_id.get_type() != Variant::STRING ||
			board_shape.get_type() != Variant::ARRAY ||
			piece_set_id.get_type() != Variant::STRING ||
			random_mode.get_type() != Variant::STRING ||
			speed_level.get_type() != Variant::INT) {
		ERR_PRINT("Tet4D live setup field types are invalid.");
		return std::nullopt;
	}
	bool shape_valid = false;
	const std::vector<int> dims = ints_from_array(static_cast<Array>(board_shape), shape_valid);
	if (!shape_valid) {
		return std::nullopt;
	}
	tet4d::core::PlainGameSetup result;
	result.schema_version = static_cast<int>(static_cast<int64_t>(schema_version));
	result.mode = to_std_string(static_cast<String>(mode));
	result.board_preset_id = to_std_string(static_cast<String>(preset_id));
	result.board_shape = dims;
	result.piece_set_id = to_std_string(static_cast<String>(piece_set_id));
	result.random_mode = to_std_string(static_cast<String>(random_mode));
	result.initial_speed_level = static_cast<int>(static_cast<int64_t>(speed_level));
	if (result.mode != expected_mode) {
		ERR_PRINT("Tet4D live setup mode does not match the native session.");
		return std::nullopt;
	}
	if (payload.has("seed")) {
		const Variant seed = payload["seed"];
		if (seed.get_type() != Variant::INT) {
			ERR_PRINT("Tet4D live setup seed must be an integer.");
			return std::nullopt;
		}
		const int64_t raw_seed = static_cast<int64_t>(seed);
		if (raw_seed < std::numeric_limits<int>::min() ||
				raw_seed > std::numeric_limits<int>::max()) {
			ERR_PRINT("Tet4D live setup seed exceeds native integer range.");
			return std::nullopt;
		}
		result.configured_seed = static_cast<int>(raw_seed);
	} else {
		result.configured_seed.reset();
	}
	if (result.random_mode == tet4d::core::RANDOM_MODE_FIXED_SEED &&
			!result.configured_seed.has_value()) {
		ERR_PRINT("Tet4D fixed-seed live setup requires seed.");
		return std::nullopt;
	}
	return result;
}

} // namespace

void Tet4DCoreApi::_bind_methods() {
	ClassDB::bind_method(D_METHOD("get_core_version"), &Tet4DCoreApi::get_core_version);
	ClassDB::bind_method(D_METHOD("get_core_status"), &Tet4DCoreApi::get_core_status);
	ClassDB::bind_method(D_METHOD("echo_text", "text"), &Tet4DCoreApi::echo_text);
	ClassDB::bind_method(D_METHOD("stable_hash_text", "text"), &Tet4DCoreApi::stable_hash_text);
	ClassDB::bind_method(D_METHOD("add_integers", "a", "b"), &Tet4DCoreApi::add_integers);
	ClassDB::bind_method(D_METHOD("geometry_normalize_blocks", "blocks"), &Tet4DCoreApi::geometry_normalize_blocks);
	ClassDB::bind_method(D_METHOD("geometry_translate_blocks", "blocks", "offset"), &Tet4DCoreApi::geometry_translate_blocks);
	ClassDB::bind_method(D_METHOD("geometry_rotate_blocks", "blocks", "axis_a", "axis_b", "quarter_turns"), &Tet4DCoreApi::geometry_rotate_blocks);
	ClassDB::bind_method(D_METHOD("geometry_hash_blocks", "blocks"), &Tet4DCoreApi::geometry_hash_blocks);
	ClassDB::bind_method(D_METHOD("query_piece_pose_legal", "dims", "piece_cells", "occupied_cells"), &Tet4DCoreApi::query_piece_pose_legal);
	ClassDB::bind_method(D_METHOD("query_topology_axis_wrap_cell_step", "dims", "wrapped_axes", "coord", "axis", "delta"), &Tet4DCoreApi::query_topology_axis_wrap_cell_step);
	ClassDB::bind_method(D_METHOD("run_builtin_plain_2d_smoke_case"), &Tet4DCoreApi::run_builtin_plain_2d_smoke_case);
	ClassDB::bind_method(D_METHOD("list_plain_2d_parity_cases"), &Tet4DCoreApi::list_plain_2d_parity_cases);
	ClassDB::bind_method(D_METHOD("get_plain_2d_parity_status"), &Tet4DCoreApi::get_plain_2d_parity_status);
	ClassDB::bind_method(D_METHOD("export_plain_2d_trace_json", "case_id"), &Tet4DCoreApi::export_plain_2d_trace_json);
	ClassDB::bind_method(D_METHOD("get_plain_2d_required_field_parity", "case_id"), &Tet4DCoreApi::get_plain_2d_required_field_parity);
	ClassDB::bind_method(D_METHOD("run_builtin_plain_nd_smoke_case"), &Tet4DCoreApi::run_builtin_plain_nd_smoke_case);
	ClassDB::bind_method(D_METHOD("list_plain_nd_parity_cases"), &Tet4DCoreApi::list_plain_nd_parity_cases);
	ClassDB::bind_method(D_METHOD("get_plain_nd_parity_status"), &Tet4DCoreApi::get_plain_nd_parity_status);
	ClassDB::bind_method(D_METHOD("export_plain_nd_trace_json", "case_id"), &Tet4DCoreApi::export_plain_nd_trace_json);
	ClassDB::bind_method(D_METHOD("get_plain_nd_required_field_parity", "case_id"), &Tet4DCoreApi::get_plain_nd_required_field_parity);
	ClassDB::bind_method(D_METHOD("live_2d_configure", "setup"), &Tet4DCoreApi::live_2d_configure);
	ClassDB::bind_method(D_METHOD("live_2d_reset"), &Tet4DCoreApi::live_2d_reset);
	ClassDB::bind_method(D_METHOD("live_2d_apply_command", "command"), &Tet4DCoreApi::live_2d_apply_command);
	ClassDB::bind_method(D_METHOD("live_2d_tick"), &Tet4DCoreApi::live_2d_tick);
	ClassDB::bind_method(D_METHOD("live_2d_snapshot_json"), &Tet4DCoreApi::live_2d_snapshot_json);
	ClassDB::bind_method(D_METHOD("live_2d_status"), &Tet4DCoreApi::live_2d_status);
	ClassDB::bind_method(D_METHOD("live_2d_state_hash"), &Tet4DCoreApi::live_2d_state_hash);
	ClassDB::bind_method(D_METHOD("live_3d_configure", "setup"), &Tet4DCoreApi::live_3d_configure);
	ClassDB::bind_method(D_METHOD("live_3d_reset"), &Tet4DCoreApi::live_3d_reset);
	ClassDB::bind_method(D_METHOD("live_3d_apply_command", "command"), &Tet4DCoreApi::live_3d_apply_command);
	ClassDB::bind_method(D_METHOD("live_3d_tick"), &Tet4DCoreApi::live_3d_tick);
	ClassDB::bind_method(D_METHOD("live_3d_snapshot_json"), &Tet4DCoreApi::live_3d_snapshot_json);
	ClassDB::bind_method(D_METHOD("live_3d_status"), &Tet4DCoreApi::live_3d_status);
	ClassDB::bind_method(D_METHOD("live_3d_state_hash"), &Tet4DCoreApi::live_3d_state_hash);
	ClassDB::bind_method(D_METHOD("live_4d_configure", "setup"), &Tet4DCoreApi::live_4d_configure);
	ClassDB::bind_method(D_METHOD("live_4d_reset"), &Tet4DCoreApi::live_4d_reset);
	ClassDB::bind_method(D_METHOD("live_4d_apply_command", "command"), &Tet4DCoreApi::live_4d_apply_command);
	ClassDB::bind_method(D_METHOD("live_4d_tick"), &Tet4DCoreApi::live_4d_tick);
	ClassDB::bind_method(D_METHOD("live_4d_snapshot_json"), &Tet4DCoreApi::live_4d_snapshot_json);
	ClassDB::bind_method(D_METHOD("live_4d_status"), &Tet4DCoreApi::live_4d_status);
	ClassDB::bind_method(D_METHOD("live_4d_state_hash"), &Tet4DCoreApi::live_4d_state_hash);
}

String Tet4DCoreApi::get_core_version() const {
	return to_godot_string(tet4d::core::get_core_version());
}

String Tet4DCoreApi::get_core_status() const {
	return to_godot_string(tet4d::core::get_core_status());
}

String Tet4DCoreApi::echo_text(const String &text) const {
	return to_godot_string(tet4d::core::echo_text(to_std_string(text)));
}

String Tet4DCoreApi::stable_hash_text(const String &text) const {
	return to_godot_string(tet4d::core::stable_hash_text(to_std_string(text)));
}

int64_t Tet4DCoreApi::add_integers(int64_t a, int64_t b) const {
	return tet4d::core::add_integers(a, b);
}

Array Tet4DCoreApi::geometry_normalize_blocks(const Array &blocks) const {
	bool valid = false;
	const std::vector<tet4d::core::CoordND> converted = blocks_from_array(blocks, valid);
	if (!valid) {
		return {};
	}
	return blocks_to_array(tet4d::core::normalize_blocks_nd(converted));
}

Array Tet4DCoreApi::geometry_translate_blocks(const Array &blocks, const Array &offset) const {
	bool valid = false;
	const std::vector<tet4d::core::CoordND> converted = blocks_from_array(blocks, valid);
	if (!valid) {
		return {};
	}
	bool offset_valid = false;
	const tet4d::core::CoordND converted_offset = coord_from_array(offset, offset_valid);
	if (!offset_valid) {
		return {};
	}
	return blocks_to_array(tet4d::core::translate_blocks_nd(converted, converted_offset));
}

Array Tet4DCoreApi::geometry_rotate_blocks(const Array &blocks, int64_t axis_a, int64_t axis_b, int64_t quarter_turns) const {
	bool valid = false;
	const std::vector<tet4d::core::CoordND> converted = blocks_from_array(blocks, valid);
	if (!valid) {
		return {};
	}
	return blocks_to_array(tet4d::core::rotate_blocks_nd(
			converted,
			static_cast<int>(axis_a),
			static_cast<int>(axis_b),
			static_cast<int>(quarter_turns)));
}

String Tet4DCoreApi::geometry_hash_blocks(const Array &blocks) const {
	bool valid = false;
	const std::vector<tet4d::core::CoordND> converted = blocks_from_array(blocks, valid);
	if (!valid) {
		return String();
	}
	return to_godot_string(tet4d::core::geometry_hash_blocks(converted));
}

Dictionary Tet4DCoreApi::query_piece_pose_legal(const Array &dims, const Array &piece_cells, const Array &occupied_cells) const {
	bool dims_valid = false;
	const std::vector<int> converted_dims = ints_from_array(dims, dims_valid);
	if (!dims_valid) {
		return query_error_dictionary("invalid_dims");
	}
	bool cells_valid = false;
	const std::vector<tet4d::core::CoordND> converted_cells = blocks_from_array(piece_cells, cells_valid);
	if (!cells_valid) {
		return query_error_dictionary("invalid_piece_cells");
	}
	bool occupied_valid = false;
	const std::vector<tet4d::core::CoordND> converted_occupied = blocks_from_array(occupied_cells, occupied_valid);
	if (!occupied_valid) {
		return query_error_dictionary("invalid_occupied_cells");
	}
	return legality_result_to_dictionary(tet4d::core::piece_pose_legal_query(
			tet4d::core::BoardShapeND{converted_dims},
			converted_cells,
			converted_occupied));
}

Dictionary Tet4DCoreApi::query_topology_axis_wrap_cell_step(const Array &dims, const Array &wrapped_axes, const Array &coord, int64_t axis, int64_t delta) const {
	bool dims_valid = false;
	const std::vector<int> converted_dims = ints_from_array(dims, dims_valid);
	if (!dims_valid) {
		return query_error_dictionary("invalid_dims");
	}
	bool axes_valid = false;
	const std::vector<int> converted_axes = ints_from_array(wrapped_axes, axes_valid);
	if (!axes_valid) {
		return query_error_dictionary("invalid_wrapped_axes");
	}
	bool coord_valid = false;
	const tet4d::core::CoordND converted_coord = coord_from_array(coord, coord_valid);
	if (!coord_valid) {
		return query_error_dictionary("invalid_coord");
	}
	const tet4d::core::TopologyCellStepQueryResult result = tet4d::core::resolve_topology_cell_step_query(
			tet4d::core::axis_wrap_topology_profile(static_cast<int>(converted_dims.size()), converted_axes),
			tet4d::core::BoardShapeND{converted_dims},
			converted_coord,
			tet4d::core::MoveStepQuery{static_cast<int>(axis), static_cast<int>(delta)});
	Dictionary dictionary;
	dictionary["ok"] = result.ok;
	dictionary["error"] = to_godot_string(result.error);
	if (result.target.has_value()) {
		dictionary["target"] = coord_to_array(*result.target);
	} else {
		dictionary["target"] = Variant();
	}
	dictionary["glue_id"] = result.glue_id.has_value() ? to_godot_string(*result.glue_id) : String();
	dictionary["source_boundary"] = result.source_boundary.has_value() ? boundary_label(*result.source_boundary) : String();
	dictionary["target_boundary"] = result.target_boundary.has_value() ? boundary_label(*result.target_boundary) : String();
	dictionary["entry_step"] = step_label(result.entry_step);
	return dictionary;
}

bool Tet4DCoreApi::run_builtin_plain_2d_smoke_case() const {
	return tet4d::core::run_builtin_plain_2d_smoke_case();
}

PackedStringArray Tet4DCoreApi::list_plain_2d_parity_cases() const {
	PackedStringArray result;
	for (const std::string &case_id : tet4d::core::list_plain_2d_parity_cases()) {
		result.push_back(to_godot_string(case_id));
	}
	return result;
}

String Tet4DCoreApi::get_plain_2d_parity_status() const {
	return to_godot_string(tet4d::core::get_plain_2d_parity_status());
}

String Tet4DCoreApi::export_plain_2d_trace_json(const String &case_id) const {
	return to_godot_string(tet4d::core::export_plain_2d_trace_json(to_std_string(case_id)));
}

bool Tet4DCoreApi::get_plain_2d_required_field_parity(const String &case_id) const {
	return tet4d::core::get_plain_2d_required_field_parity(to_std_string(case_id));
}

bool Tet4DCoreApi::run_builtin_plain_nd_smoke_case() const {
	return tet4d::core::run_builtin_plain_nd_smoke_case();
}

PackedStringArray Tet4DCoreApi::list_plain_nd_parity_cases() const {
	PackedStringArray result;
	for (const std::string &case_id : tet4d::core::list_plain_nd_parity_cases()) {
		result.push_back(to_godot_string(case_id));
	}
	return result;
}

String Tet4DCoreApi::get_plain_nd_parity_status() const {
	return to_godot_string(tet4d::core::get_plain_nd_parity_status());
}

String Tet4DCoreApi::export_plain_nd_trace_json(const String &case_id) const {
	return to_godot_string(tet4d::core::export_plain_nd_trace_json(to_std_string(case_id)));
}

bool Tet4DCoreApi::get_plain_nd_required_field_parity(const String &case_id) const {
	return tet4d::core::get_plain_nd_required_field_parity(to_std_string(case_id));
}

bool Tet4DCoreApi::live_2d_configure(const Dictionary &setup) {
	const auto parsed = plain_setup_from_dictionary(setup, "live_2d");
	return parsed.has_value() && live_2d_session_.configure(*parsed);
}

void Tet4DCoreApi::live_2d_reset() {
	live_2d_session_.reset();
}

String Tet4DCoreApi::live_2d_apply_command(const String &command) {
	return to_godot_string(live_2d_session_.apply_command(to_std_string(command)));
}

String Tet4DCoreApi::live_2d_tick() {
	return to_godot_string(live_2d_session_.tick());
}

String Tet4DCoreApi::live_2d_snapshot_json() const {
	return to_godot_string(live_2d_session_.snapshot_json());
}

String Tet4DCoreApi::live_2d_status() const {
	return to_godot_string(live_2d_session_.status());
}

String Tet4DCoreApi::live_2d_state_hash() const {
	return to_godot_string(live_2d_session_.state_hash());
}

bool Tet4DCoreApi::live_3d_configure(const Dictionary &setup) {
	const auto parsed = plain_setup_from_dictionary(setup, "live_3d");
	return parsed.has_value() && live_3d_session_.configure(*parsed);
}

void Tet4DCoreApi::live_3d_reset() {
	live_3d_session_.reset();
}

String Tet4DCoreApi::live_3d_apply_command(const String &command) {
	return to_godot_string(live_3d_session_.apply_command(to_std_string(command)));
}

String Tet4DCoreApi::live_3d_tick() {
	return to_godot_string(live_3d_session_.tick());
}

String Tet4DCoreApi::live_3d_snapshot_json() const {
	return to_godot_string(live_3d_session_.snapshot_json());
}

String Tet4DCoreApi::live_3d_status() const {
	return to_godot_string(live_3d_session_.status());
}

String Tet4DCoreApi::live_3d_state_hash() const {
	return to_godot_string(live_3d_session_.state_hash());
}

bool Tet4DCoreApi::live_4d_configure(const Dictionary &setup) {
	const auto parsed = plain_setup_from_dictionary(setup, "live_4d");
	return parsed.has_value() && live_4d_session_.configure(*parsed);
}

void Tet4DCoreApi::live_4d_reset() {
	live_4d_session_.reset();
}

String Tet4DCoreApi::live_4d_apply_command(const String &command) {
	return to_godot_string(live_4d_session_.apply_command(to_std_string(command)));
}

String Tet4DCoreApi::live_4d_tick() {
	return to_godot_string(live_4d_session_.tick());
}

String Tet4DCoreApi::live_4d_snapshot_json() const {
	return to_godot_string(live_4d_session_.snapshot_json());
}

String Tet4DCoreApi::live_4d_status() const {
	return to_godot_string(live_4d_session_.status());
}

String Tet4DCoreApi::live_4d_state_hash() const {
	return to_godot_string(live_4d_session_.state_hash());
}

} // namespace godot
