#include "tet4d_core/core_api.hpp"

#include <array>

namespace tet4d::core {
namespace {

constexpr std::uint64_t FNV_OFFSET_BASIS = 14695981039346656037ULL;
constexpr std::uint64_t FNV_PRIME = 1099511628211ULL;

std::string to_fixed_hex(std::uint64_t value) {
	constexpr std::array<char, 16> HEX = {
		'0', '1', '2', '3', '4', '5', '6', '7',
		'8', '9', 'a', 'b', 'c', 'd', 'e', 'f',
	};
	std::string result(16, '0');
	for (int index = 15; index >= 0; --index) {
		result[static_cast<std::size_t>(index)] = HEX[value & 0x0F];
		value >>= 4;
	}
	return result;
}

} // namespace

std::string get_core_version() {
	return "0.1.0-stage8";
}

std::string get_core_status() {
	return "native tet4d core skeleton loaded; gameplay not implemented";
}

std::string echo_text(std::string_view text) {
	return std::string(text);
}

std::string stable_hash_text(std::string_view text) {
	std::uint64_t hash = FNV_OFFSET_BASIS;
	for (const unsigned char byte : text) {
		hash ^= static_cast<std::uint64_t>(byte);
		hash *= FNV_PRIME;
	}
	return to_fixed_hex(hash);
}

std::int64_t add_integers(std::int64_t a, std::int64_t b) {
	return a + b;
}

} // namespace tet4d::core
