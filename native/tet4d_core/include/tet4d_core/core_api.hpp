#pragma once

#include <cstdint>
#include <string>
#include <string_view>

namespace tet4d::core {

std::string get_core_version();
std::string get_core_status();
std::string echo_text(std::string_view text);
std::string stable_hash_text(std::string_view text);
std::int64_t add_integers(std::int64_t a, std::int64_t b);

} // namespace tet4d::core
