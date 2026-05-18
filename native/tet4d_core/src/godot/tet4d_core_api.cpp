#include "tet4d_core_api.h"

#include "tet4d_core/core_api.hpp"

#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/char_string.hpp>

#include <string>

namespace godot {
namespace {

std::string to_std_string(const String &text) {
	const CharString utf8 = text.utf8();
	return std::string(utf8.get_data());
}

String to_godot_string(const std::string &text) {
	return String::utf8(text.c_str());
}

} // namespace

void Tet4DCoreApi::_bind_methods() {
	ClassDB::bind_method(D_METHOD("get_core_version"), &Tet4DCoreApi::get_core_version);
	ClassDB::bind_method(D_METHOD("get_core_status"), &Tet4DCoreApi::get_core_status);
	ClassDB::bind_method(D_METHOD("echo_text", "text"), &Tet4DCoreApi::echo_text);
	ClassDB::bind_method(D_METHOD("stable_hash_text", "text"), &Tet4DCoreApi::stable_hash_text);
	ClassDB::bind_method(D_METHOD("add_integers", "a", "b"), &Tet4DCoreApi::add_integers);
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

} // namespace godot
