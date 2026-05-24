#pragma once

#include <string>
#include <vector>

namespace tet4d::core {

std::vector<std::string> list_plain_nd_parity_cases();
std::string export_plain_nd_trace_json(const std::string &case_id);
bool run_builtin_plain_nd_smoke_case();
std::string get_plain_nd_parity_status();
bool get_plain_nd_required_field_parity(const std::string &case_id);

} // namespace tet4d::core
