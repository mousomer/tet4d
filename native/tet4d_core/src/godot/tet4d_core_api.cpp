#include "tet4d_core_api.h"

#include "tet4d_core/core_api.hpp"
#include "tet4d_core/geometry.hpp"

#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/char_string.hpp>
#include <godot_cpp/variant/variant.hpp>

#include <string>
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

tet4d::core::CoordND coord_from_array(const Array &values) {
	tet4d::core::CoordND coord;
	coord.values.reserve(static_cast<std::size_t>(values.size()));
	for (int64_t index = 0; index < values.size(); ++index) {
		coord.values.push_back(static_cast<int>(values[index]));
	}
	return coord;
}

std::vector<tet4d::core::CoordND> blocks_from_array(const Array &blocks, bool &valid) {
	std::vector<tet4d::core::CoordND> result;
	result.reserve(static_cast<std::size_t>(blocks.size()));
	for (int64_t index = 0; index < blocks.size(); ++index) {
		const Variant value = blocks[index];
		if (value.get_type() != Variant::ARRAY) {
			valid = false;
			return {};
		}
		result.push_back(coord_from_array(static_cast<Array>(value)));
	}
	valid = true;
	return result;
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
	ClassDB::bind_method(D_METHOD("live_2d_reset"), &Tet4DCoreApi::live_2d_reset);
	ClassDB::bind_method(D_METHOD("live_2d_apply_command", "command"), &Tet4DCoreApi::live_2d_apply_command);
	ClassDB::bind_method(D_METHOD("live_2d_tick"), &Tet4DCoreApi::live_2d_tick);
	ClassDB::bind_method(D_METHOD("live_2d_snapshot_json"), &Tet4DCoreApi::live_2d_snapshot_json);
	ClassDB::bind_method(D_METHOD("live_2d_status"), &Tet4DCoreApi::live_2d_status);
	ClassDB::bind_method(D_METHOD("live_2d_state_hash"), &Tet4DCoreApi::live_2d_state_hash);
	ClassDB::bind_method(D_METHOD("live_3d_reset"), &Tet4DCoreApi::live_3d_reset);
	ClassDB::bind_method(D_METHOD("live_3d_apply_command", "command"), &Tet4DCoreApi::live_3d_apply_command);
	ClassDB::bind_method(D_METHOD("live_3d_tick"), &Tet4DCoreApi::live_3d_tick);
	ClassDB::bind_method(D_METHOD("live_3d_snapshot_json"), &Tet4DCoreApi::live_3d_snapshot_json);
	ClassDB::bind_method(D_METHOD("live_3d_status"), &Tet4DCoreApi::live_3d_status);
	ClassDB::bind_method(D_METHOD("live_3d_state_hash"), &Tet4DCoreApi::live_3d_state_hash);
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
	return blocks_to_array(tet4d::core::translate_blocks_nd(converted, coord_from_array(offset)));
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
