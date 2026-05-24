#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace tet4d::core {

std::string get_core_version();
std::string get_core_status();
std::string echo_text(std::string_view text);
std::string stable_hash_text(std::string_view text);
std::int64_t add_integers(std::int64_t a, std::int64_t b);
bool run_builtin_plain_2d_smoke_case();
std::vector<std::string> list_plain_2d_parity_cases();
std::string get_plain_2d_parity_status();
std::string export_plain_2d_trace_json(const std::string &case_id = "gameplay_plain_2d_short");
bool get_plain_2d_required_field_parity(const std::string &case_id = "gameplay_plain_2d_short");
bool run_builtin_plain_nd_smoke_case();
std::vector<std::string> list_plain_nd_parity_cases();
std::string get_plain_nd_parity_status();
std::string export_plain_nd_trace_json(const std::string &case_id = "gameplay_plain_3d_short");
bool get_plain_nd_required_field_parity(const std::string &case_id = "gameplay_plain_3d_short");

} // namespace tet4d::core
