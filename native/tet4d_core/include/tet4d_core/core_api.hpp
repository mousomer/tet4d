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
bool run_builtin_plain_2d_smoke_case();
std::string get_plain_2d_parity_status();
std::string export_plain_2d_trace_json();

} // namespace tet4d::core
