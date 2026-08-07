#include "tet4d_core_api.h"

#include "topology_transport_variant.h"

#include "tet4d_core/board_extent_contract.hpp"
#include "tet4d_core/core_api.hpp"
#include "tet4d_core/generated/board_extent_contract_v1.hpp"
#include "tet4d_core/geometry.hpp"
#include "tet4d_core/plain_game_setup.hpp"
#include "tet4d_core/query.hpp"
#include "tet4d_core/topology_transport.hpp"

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

Variant frame_to_variant(const std::optional<tet4d::core::TopologyFrameQueryTransform> &frame) {
	if (!frame.has_value()) {
		return Variant();
	}
	Dictionary result;
	Array permutation;
	Array signs;
	for (const int value : frame->permutation) {
		permutation.push_back(value);
	}
	for (const int value : frame->signs) {
		signs.push_back(value);
	}
	result["permutation"] = permutation;
	result["signs"] = signs;
	result["translation"] = coord_to_array(frame->translation);
	return result;
}

Dictionary topology_query_result_to_dictionary(const tet4d::core::TopologyCellStepQueryResult &result) {
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
	dictionary["frame_transform"] = frame_to_variant(result.frame_transform);
	dictionary["piece_frame_transform"] = frame_to_variant(result.piece_frame_transform);
	return dictionary;
}

Array board_shape_to_array(const std::vector<int> &shape) {
	Array result;
	for (const int extent : shape) {
		result.push_back(extent);
	}
	return result;
}

Dictionary board_extent_error_dictionary(const tet4d::core::BoardExtentValidationError &detail) {
	Dictionary result;
	result["code"] = to_godot_string(detail.code);
	result["path"] = to_godot_string(detail.path);
	result["expected"] = to_godot_string(detail.expected);
	result["actual"] = to_godot_string(detail.actual);
	result["message"] = to_godot_string(detail.message);
	return result;
}

Dictionary board_extent_result_dictionary(const tet4d::core::BoardExtentValidationResult &result) {
	Dictionary response;
	response["ok"] = result.ok;
	Array errors;
	for (const tet4d::core::BoardExtentValidationError &detail : result.errors) {
		errors.push_back(board_extent_error_dictionary(detail));
	}
	response["errors"] = errors;
	Dictionary validated;
	if (result.validated_setup.has_value()) {
		const tet4d::core::ValidatedLiveBoardSetup &setup = *result.validated_setup;
		validated["contract_version"] = setup.contract_version;
		validated["mode"] = to_godot_string(setup.mode);
		validated["board_shape"] = board_shape_to_array(setup.board_shape);
		validated["piece_set_id"] = to_godot_string(setup.piece_set_id);
		validated["native_cell_count"] = setup.native_cell_count;
		validated["topology_profile"] = topology_transport_profile_dictionary(setup.topology_profile).get("profile", Dictionary());
	}
	response["validated_setup"] = validated;
	return response;
}

Dictionary configuration_error_dictionary(const std::string &path, const std::string &message) {
	tet4d::core::BoardExtentValidationResult result;
	result.errors.push_back({"invalid_field_type", path, "valid live setup", "invalid", message});
	return board_extent_result_dictionary(result);
}

std::optional<tet4d::core::PlainGameSetup> plain_setup_from_dictionary(
		const Dictionary &payload,
		const std::string &expected_mode) {
	static const std::set<std::string> allowed_fields = {
		"schema_version",
		"contract_version",
		"mode",
		"board_preset_id",
		"board_shape",
		"piece_set_id",
		"random_mode",
		"seed",
		"initial_speed_level",
		"topology_profile",
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
			"contract_version",
			"mode",
			"board_preset_id",
			"board_shape",
			"piece_set_id",
			"random_mode",
			"initial_speed_level",
			"topology_profile",
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

template <typename Session>
Dictionary configure_checked(
		const Dictionary &setup,
		const std::string &mode,
		Session &session) {
	auto transported = topology_transport_value_from_variant(setup, "$");
	if (!transported.ok()) {
		return configuration_error_dictionary("$", "The live setup contains an unsupported Variant value.");
	}
	const tet4d::core::BoardExtentValidationResult validation =
			tet4d::core::validate_live_board_setup_transport(*transported.value);
	if (!validation.ok) {
		return board_extent_result_dictionary(validation);
	}
	const auto parsed = plain_setup_from_dictionary(setup, mode);
	if (!parsed.has_value()) {
		return configuration_error_dictionary("$", "The non-extent live setup fields are invalid.");
	}
	if (!session.configure(*parsed)) {
		return configuration_error_dictionary("$", "The validated setup could not be committed atomically.");
	}
	return board_extent_result_dictionary(validation);
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
	ClassDB::bind_method(D_METHOD("topology_transport_profile", "profile"), &Tet4DCoreApi::topology_transport_profile);
	ClassDB::bind_method(D_METHOD("topology_transport_resolve_cell_step", "profile", "query"), &Tet4DCoreApi::topology_transport_resolve_cell_step);
	ClassDB::bind_method(D_METHOD("get_board_extent_contract"), &Tet4DCoreApi::get_board_extent_contract);
	ClassDB::bind_method(D_METHOD("validate_live_board_setup", "setup"), &Tet4DCoreApi::validate_live_board_setup);
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
	ClassDB::bind_method(D_METHOD("live_2d_configure_checked", "setup"), &Tet4DCoreApi::live_2d_configure_checked);
	ClassDB::bind_method(D_METHOD("live_2d_reset"), &Tet4DCoreApi::live_2d_reset);
	ClassDB::bind_method(D_METHOD("live_2d_apply_command", "command"), &Tet4DCoreApi::live_2d_apply_command);
	ClassDB::bind_method(D_METHOD("live_2d_tick"), &Tet4DCoreApi::live_2d_tick);
	ClassDB::bind_method(D_METHOD("live_2d_snapshot_json"), &Tet4DCoreApi::live_2d_snapshot_json);
	ClassDB::bind_method(D_METHOD("live_2d_status"), &Tet4DCoreApi::live_2d_status);
	ClassDB::bind_method(D_METHOD("live_2d_state_hash"), &Tet4DCoreApi::live_2d_state_hash);
	ClassDB::bind_method(D_METHOD("live_3d_configure", "setup"), &Tet4DCoreApi::live_3d_configure);
	ClassDB::bind_method(D_METHOD("live_3d_configure_checked", "setup"), &Tet4DCoreApi::live_3d_configure_checked);
	ClassDB::bind_method(D_METHOD("live_3d_reset"), &Tet4DCoreApi::live_3d_reset);
	ClassDB::bind_method(D_METHOD("live_3d_apply_command", "command"), &Tet4DCoreApi::live_3d_apply_command);
	ClassDB::bind_method(D_METHOD("live_3d_tick"), &Tet4DCoreApi::live_3d_tick);
	ClassDB::bind_method(D_METHOD("live_3d_snapshot_json"), &Tet4DCoreApi::live_3d_snapshot_json);
	ClassDB::bind_method(D_METHOD("live_3d_status"), &Tet4DCoreApi::live_3d_status);
	ClassDB::bind_method(D_METHOD("live_3d_state_hash"), &Tet4DCoreApi::live_3d_state_hash);
	ClassDB::bind_method(D_METHOD("live_4d_configure", "setup"), &Tet4DCoreApi::live_4d_configure);
	ClassDB::bind_method(D_METHOD("live_4d_configure_checked", "setup"), &Tet4DCoreApi::live_4d_configure_checked);
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
	return topology_query_result_to_dictionary(result);
}

Dictionary Tet4DCoreApi::topology_transport_profile(const Variant &profile) const {
	auto transported = topology_transport_value_from_variant(profile, "profile");
	if (!transported.ok()) {
		return topology_transport_error_dictionary(*transported.error);
	}
	auto decoded = tet4d::core::decode_topology_transport_profile(*transported.value);
	if (!decoded.ok()) {
		return topology_transport_error_dictionary(*decoded.error);
	}
	return topology_transport_profile_dictionary(*decoded.value);
}

Dictionary Tet4DCoreApi::topology_transport_resolve_cell_step(const Variant &profile, const Variant &query) const {
	auto transported_profile = topology_transport_value_from_variant(profile, "profile");
	if (!transported_profile.ok()) {
		return topology_transport_error_dictionary(*transported_profile.error);
	}
	auto decoded_profile = tet4d::core::decode_topology_transport_profile(*transported_profile.value);
	if (!decoded_profile.ok()) {
		return topology_transport_error_dictionary(*decoded_profile.error);
	}
	auto transported_query = topology_transport_value_from_variant(query, "query");
	if (!transported_query.ok()) {
		return topology_transport_error_dictionary(*transported_query.error);
	}
	auto decoded_query = tet4d::core::decode_topology_transport_query(*transported_query.value, *decoded_profile.value);
	if (!decoded_query.ok()) {
		return topology_transport_error_dictionary(*decoded_query.error);
	}
	const auto result = tet4d::core::resolve_topology_transport_query(*decoded_profile.value, *decoded_query.value);
	if (!result.ok) {
		return topology_transport_error_dictionary({
				"unknown_required_value", "query", "valid resolver query", result.error,
				"validated topology query was rejected by the native resolver"});
	}
	Dictionary response = topology_query_result_to_dictionary(result);
	response["query"] = topology_transport_query_dictionary(*decoded_query.value);
	return response;
}

Dictionary Tet4DCoreApi::get_board_extent_contract() const {
	Dictionary result;
	result["contract"] = to_godot_string(std::string(tet4d::core::generated::BOARD_EXTENT_CONTRACT_NAME));
	result["contract_version"] = tet4d::core::generated::BOARD_EXTENT_CONTRACT_VERSION;
	result["fingerprint"] = to_godot_string(std::string(tet4d::core::generated::BOARD_EXTENT_CONTRACT_FINGERPRINT));
	Array modes;
	for (const tet4d::core::generated::BoardExtentModeSpec &spec : tet4d::core::generated::BOARD_EXTENT_MODE_SPECS) {
		Dictionary mode;
		mode["id"] = to_godot_string(std::string(spec.id));
		mode["rank"] = spec.rank;
		Array axes;
		Array minima;
		Array maxima;
		Array defaults;
		for (std::int64_t axis = 0; axis < spec.rank; ++axis) {
			axes.push_back(to_godot_string(std::string(spec.axis_order[static_cast<std::size_t>(axis)])));
			minima.push_back(spec.axis_minima[static_cast<std::size_t>(axis)]);
			maxima.push_back(spec.axis_maxima[static_cast<std::size_t>(axis)]);
			defaults.push_back(spec.canonical_default_shape[static_cast<std::size_t>(axis)]);
		}
		mode["axis_order"] = axes;
		mode["axis_minima"] = minima;
		mode["axis_maxima"] = maxima;
		mode["canonical_default_shape"] = defaults;
		mode["native_maximum_cells"] = spec.native_maximum_cells;
		mode["supported_topology_kind"] = to_godot_string(std::string(spec.supported_topology_kind));
		modes.push_back(mode);
	}
	result["modes"] = modes;
	return result;
}

Dictionary Tet4DCoreApi::validate_live_board_setup(const Variant &setup) const {
	auto transported = topology_transport_value_from_variant(setup, "$");
	if (!transported.ok()) {
		return configuration_error_dictionary("$", "The live setup contains an unsupported Variant value.");
	}
	return board_extent_result_dictionary(tet4d::core::validate_live_board_setup_transport(*transported.value));
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
	return bool(live_2d_configure_checked(setup).get("ok", false));
}

Dictionary Tet4DCoreApi::live_2d_configure_checked(const Dictionary &setup) {
	return configure_checked(setup, "live_2d", live_2d_session_);
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
	return bool(live_3d_configure_checked(setup).get("ok", false));
}

Dictionary Tet4DCoreApi::live_3d_configure_checked(const Dictionary &setup) {
	return configure_checked(setup, "live_3d", live_3d_session_);
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
	return bool(live_4d_configure_checked(setup).get("ok", false));
}

Dictionary Tet4DCoreApi::live_4d_configure_checked(const Dictionary &setup) {
	return configure_checked(setup, "live_4d", live_4d_session_);
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
