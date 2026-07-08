#include "tet4d_core/geometry.hpp"

#include "tet4d_core/core_api.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <sstream>
#include <utility>

namespace tet4d::core {
namespace {

constexpr int MIN_GEOMETRY_DIMENSION = 2;
constexpr int QUARTER_TURNS = 4;
constexpr double ROUND_EPSILON = 1e-9;

int positive_modulo_quarter_turns(int value) {
	const int remainder = value % QUARTER_TURNS;
	return remainder < 0 ? remainder + QUARTER_TURNS : remainder;
}

int python_floor_divide_by_two(int value) {
	if (value >= 0 || value % 2 == 0) {
		return value / 2;
	}
	return (value / 2) - 1;
}

int python_round_to_int(double value) {
	const double lower = std::floor(value);
	const double fraction = value - lower;
	if (fraction < 0.5 - ROUND_EPSILON) {
		return static_cast<int>(lower);
	}
	if (fraction > 0.5 + ROUND_EPSILON) {
		return static_cast<int>(std::ceil(value));
	}
	const int lower_int = static_cast<int>(lower);
	if (lower_int % 2 == 0) {
		return lower_int;
	}
	return static_cast<int>(std::ceil(value));
}

int valid_dimension(const std::vector<CoordND> &blocks) {
	if (blocks.empty()) {
		return 0;
	}
	const int dimension = blocks.front().dimension();
	if (dimension < MIN_GEOMETRY_DIMENSION) {
		return 0;
	}
	for (const CoordND &block : blocks) {
		if (block.dimension() != dimension) {
			return 0;
		}
	}
	return dimension;
}

bool axes_are_valid(int dimension, int axis_a, int axis_b) {
	return axis_a != axis_b && axis_a >= 0 && axis_b >= 0 && axis_a < dimension && axis_b < dimension;
}

std::pair<CoordND, CoordND> axis_bounds(const std::vector<CoordND> &blocks) {
	const int dimension = blocks.front().dimension();
	CoordND mins = blocks.front();
	CoordND maxs = blocks.front();
	for (const CoordND &block : blocks) {
		for (int axis = 0; axis < dimension; ++axis) {
			int &min_value = mins.values[static_cast<std::size_t>(axis)];
			int &max_value = maxs.values[static_cast<std::size_t>(axis)];
			const int value = block.values[static_cast<std::size_t>(axis)];
			min_value = std::min(min_value, value);
			max_value = std::max(max_value, value);
		}
	}
	return {mins, maxs};
}

std::pair<double, double> python_rotation_pivot(
		const std::vector<CoordND> &blocks,
		int axis_a,
		int axis_b) {
	const auto [mins, maxs] = axis_bounds(blocks);
	const int min_a = mins.values[static_cast<std::size_t>(axis_a)];
	const int max_a = maxs.values[static_cast<std::size_t>(axis_a)];
	const int min_b = mins.values[static_cast<std::size_t>(axis_b)];
	const int max_b = maxs.values[static_cast<std::size_t>(axis_b)];
	const bool a_even = ((max_a - min_a) % 2) == 0;
	const bool b_even = ((max_b - min_b) % 2) == 0;
	if (a_even == b_even) {
		return {
			(static_cast<double>(min_a) + static_cast<double>(max_a)) / 2.0,
			(static_cast<double>(min_b) + static_cast<double>(max_b)) / 2.0,
		};
	}

	double center_mass_a = 0.0;
	double center_mass_b = 0.0;
	for (const CoordND &block : blocks) {
		center_mass_a += block.values[static_cast<std::size_t>(axis_a)];
		center_mass_b += block.values[static_cast<std::size_t>(axis_b)];
	}
	center_mass_a /= static_cast<double>(blocks.size());
	center_mass_b /= static_cast<double>(blocks.size());

	double min_dist_sq = std::numeric_limits<double>::infinity();
	CoordND pivot_block = blocks.front();
	for (const CoordND &block : blocks) {
		const double da = static_cast<double>(block.values[static_cast<std::size_t>(axis_a)]) - center_mass_a;
		const double db = static_cast<double>(block.values[static_cast<std::size_t>(axis_b)]) - center_mass_b;
		const double dist_sq = da * da + db * db;
		if (dist_sq < min_dist_sq) {
			min_dist_sq = dist_sq;
			pivot_block = block;
		}
	}
	return {
		static_cast<double>(pivot_block.values[static_cast<std::size_t>(axis_a)]),
		static_cast<double>(pivot_block.values[static_cast<std::size_t>(axis_b)]),
	};
}

std::vector<CoordND> rotate_once_around_pivot(
		const std::vector<CoordND> &blocks,
		int axis_a,
		int axis_b,
		double pivot_a,
		double pivot_b) {
	std::vector<CoordND> rotated;
	rotated.reserve(blocks.size());
	for (const CoordND &block : blocks) {
		CoordND next = block;
		const double rel_a = static_cast<double>(block.values[static_cast<std::size_t>(axis_a)]) - pivot_a;
		const double rel_b = static_cast<double>(block.values[static_cast<std::size_t>(axis_b)]) - pivot_b;
		next.values[static_cast<std::size_t>(axis_a)] = python_round_to_int(rel_b + pivot_a);
		next.values[static_cast<std::size_t>(axis_b)] = python_round_to_int(-rel_a + pivot_b);
		rotated.push_back(next);
	}
	return rotated;
}

} // namespace

std::vector<CoordND> canonicalize_blocks_nd(std::vector<CoordND> blocks) {
	if (valid_dimension(blocks) == 0) {
		return {};
	}
	std::sort(blocks.begin(), blocks.end());
	return blocks;
}

std::vector<CoordND> normalize_blocks_nd(const std::vector<CoordND> &blocks) {
	const int dimension = valid_dimension(blocks);
	if (dimension == 0) {
		return {};
	}
	const auto [mins, maxs] = axis_bounds(blocks);
	std::vector<int> centers;
	centers.reserve(static_cast<std::size_t>(dimension));
	for (int axis = 0; axis < dimension; ++axis) {
		centers.push_back(python_floor_divide_by_two(
				mins.values[static_cast<std::size_t>(axis)] + maxs.values[static_cast<std::size_t>(axis)]));
	}

	std::vector<CoordND> normalized;
	normalized.reserve(blocks.size());
	for (const CoordND &block : blocks) {
		CoordND next = block;
		for (int axis = 0; axis < dimension; ++axis) {
			next.values[static_cast<std::size_t>(axis)] -= centers[static_cast<std::size_t>(axis)];
		}
		normalized.push_back(next);
	}
	return canonicalize_blocks_nd(std::move(normalized));
}

std::vector<CoordND> translate_blocks_nd(const std::vector<CoordND> &blocks, const CoordND &offset) {
	const int dimension = valid_dimension(blocks);
	if (dimension == 0) {
		return {};
	}
	if (offset.dimension() != dimension) {
		return {};
	}
	std::vector<CoordND> translated;
	translated.reserve(blocks.size());
	for (const CoordND &block : blocks) {
		CoordND next = block;
		for (int axis = 0; axis < dimension; ++axis) {
			next.values[static_cast<std::size_t>(axis)] += offset.values[static_cast<std::size_t>(axis)];
		}
		translated.push_back(next);
	}
	return canonicalize_blocks_nd(std::move(translated));
}

std::vector<CoordND> rotate_blocks_nd(
		const std::vector<CoordND> &blocks,
		int axis_a,
		int axis_b,
		int quarter_turns) {
	const int dimension = valid_dimension(blocks);
	if (dimension == 0 || !axes_are_valid(dimension, axis_a, axis_b)) {
		return blocks;
	}
	std::vector<CoordND> rotated = blocks;
	const int steps = positive_modulo_quarter_turns(quarter_turns);
	for (int step = 0; step < steps; ++step) {
		const auto [pivot_a, pivot_b] = python_rotation_pivot(rotated, axis_a, axis_b);
		rotated = rotate_once_around_pivot(rotated, axis_a, axis_b, pivot_a, pivot_b);
	}
	return rotated;
}

std::vector<CoordND> rotate_blocks_nd_around_pivot(
		const std::vector<CoordND> &blocks,
		int axis_a,
		int axis_b,
		int quarter_turns,
		double pivot_a,
		double pivot_b) {
	const int dimension = valid_dimension(blocks);
	if (dimension == 0 || !axes_are_valid(dimension, axis_a, axis_b)) {
		return blocks;
	}
	std::vector<CoordND> rotated = blocks;
	const int steps = positive_modulo_quarter_turns(quarter_turns);
	for (int step = 0; step < steps; ++step) {
		rotated = rotate_once_around_pivot(rotated, axis_a, axis_b, pivot_a, pivot_b);
	}
	return rotated;
}

std::string serialize_geometry_blocks(const std::vector<CoordND> &blocks) {
	const std::vector<CoordND> canonical = canonicalize_blocks_nd(blocks);
	std::ostringstream stream;
	stream << "blocks:";
	for (std::size_t block_index = 0; block_index < canonical.size(); ++block_index) {
		if (block_index > 0) {
			stream << ";";
		}
		stream << "[";
		const CoordND &block = canonical[block_index];
		for (std::size_t axis = 0; axis < block.values.size(); ++axis) {
			if (axis > 0) {
				stream << ",";
			}
			stream << block.values[axis];
		}
		stream << "]";
	}
	return stream.str();
}

std::string geometry_hash_blocks(const std::vector<CoordND> &blocks) {
	return stable_hash_text(serialize_geometry_blocks(blocks));
}

} // namespace tet4d::core
