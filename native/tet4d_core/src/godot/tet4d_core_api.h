#pragma once

#include "tet4d_core/plain_2d_session.hpp"
#include "tet4d_core/plain_nd_session.hpp"

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/packed_string_array.hpp>
#include <godot_cpp/variant/string.hpp>

namespace godot {

class Tet4DCoreApi : public RefCounted {
	GDCLASS(Tet4DCoreApi, RefCounted);

protected:
	static void _bind_methods();

public:
	String get_core_version() const;
	String get_core_status() const;
	String echo_text(const String &text) const;
	String stable_hash_text(const String &text) const;
	int64_t add_integers(int64_t a, int64_t b) const;
	Array geometry_normalize_blocks(const Array &blocks) const;
	Array geometry_translate_blocks(const Array &blocks, const Array &offset) const;
	Array geometry_rotate_blocks(const Array &blocks, int64_t axis_a, int64_t axis_b, int64_t quarter_turns) const;
	String geometry_hash_blocks(const Array &blocks) const;
	Dictionary query_piece_pose_legal(const Array &dims, const Array &piece_cells, const Array &occupied_cells) const;
	Dictionary query_topology_axis_wrap_cell_step(const Array &dims, const Array &wrapped_axes, const Array &coord, int64_t axis, int64_t delta) const;
	bool run_builtin_plain_2d_smoke_case() const;
	PackedStringArray list_plain_2d_parity_cases() const;
	String get_plain_2d_parity_status() const;
	String export_plain_2d_trace_json(const String &case_id) const;
	bool get_plain_2d_required_field_parity(const String &case_id) const;
	bool run_builtin_plain_nd_smoke_case() const;
	PackedStringArray list_plain_nd_parity_cases() const;
	String get_plain_nd_parity_status() const;
	String export_plain_nd_trace_json(const String &case_id) const;
	bool get_plain_nd_required_field_parity(const String &case_id) const;
	void live_2d_reset();
	String live_2d_apply_command(const String &command);
	String live_2d_tick();
	String live_2d_snapshot_json() const;
	String live_2d_status() const;
	String live_2d_state_hash() const;
	void live_3d_reset();
	String live_3d_apply_command(const String &command);
	String live_3d_tick();
	String live_3d_snapshot_json() const;
	String live_3d_status() const;
	String live_3d_state_hash() const;
	void live_4d_reset();
	String live_4d_apply_command(const String &command);
	String live_4d_tick();
	String live_4d_snapshot_json() const;
	String live_4d_status() const;
	String live_4d_state_hash() const;

private:
	mutable tet4d::core::Plain2DSession live_2d_session_;
	mutable tet4d::core::PlainNDSession live_3d_session_{3};
	mutable tet4d::core::PlainNDSession live_4d_session_{4};
};

} // namespace godot
