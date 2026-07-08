#pragma once

#include "tet4d_core/plain_nd.hpp"

#include <string>
#include <vector>

namespace tet4d::core {

std::vector<CoordND> canonicalize_blocks_nd(std::vector<CoordND> blocks);
std::vector<CoordND> normalize_blocks_nd(const std::vector<CoordND> &blocks);
std::vector<CoordND> translate_blocks_nd(const std::vector<CoordND> &blocks, const CoordND &offset);
std::vector<CoordND> rotate_blocks_nd(
		const std::vector<CoordND> &blocks,
		int axis_a,
		int axis_b,
		int quarter_turns);
std::vector<CoordND> rotate_blocks_nd_around_pivot(
		const std::vector<CoordND> &blocks,
		int axis_a,
		int axis_b,
		int quarter_turns,
		double pivot_a,
		double pivot_b);
std::string serialize_geometry_blocks(const std::vector<CoordND> &blocks);
std::string geometry_hash_blocks(const std::vector<CoordND> &blocks);

} // namespace tet4d::core
