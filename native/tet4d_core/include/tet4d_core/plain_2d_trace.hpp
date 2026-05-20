#pragma once

#include <string>

namespace tet4d::core {

std::string export_plain_2d_trace_json();
bool run_builtin_plain_2d_smoke_case();
std::string get_plain_2d_parity_status();
bool get_plain_2d_required_field_parity();

} // namespace tet4d::core
