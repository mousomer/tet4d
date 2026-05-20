#pragma once

#include <string>
#include <string_view>

namespace tet4d::core {

std::string sha256_hex(std::string_view text);

} // namespace tet4d::core
