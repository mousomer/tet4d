#pragma once

#include <string>
#include <vector>

namespace tet4d::core {

std::vector<std::string> list_plain_2d_parity_cases();
std::string export_plain_2d_trace_json(const std::string &case_id = "gameplay_plain_2d_short");
bool run_builtin_plain_2d_smoke_case();
std::string get_plain_2d_parity_status();
bool get_plain_2d_required_field_parity(const std::string &case_id = "gameplay_plain_2d_short");

} // namespace tet4d::core
