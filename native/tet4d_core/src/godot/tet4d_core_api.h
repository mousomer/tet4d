#pragma once

#include <godot_cpp/classes/ref_counted.hpp>
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
	bool run_builtin_plain_2d_smoke_case() const;
	PackedStringArray list_plain_2d_parity_cases() const;
	String get_plain_2d_parity_status() const;
	String export_plain_2d_trace_json(const String &case_id) const;
	bool get_plain_2d_required_field_parity(const String &case_id) const;
};

} // namespace godot
