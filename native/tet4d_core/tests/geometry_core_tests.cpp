#include "tet4d_core/geometry.hpp"

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string &message) {
	if (!condition) {
		std::cerr << message << "\n";
		std::exit(1);
	}
}

std::string blocks_json(const std::vector<tet4d::core::CoordND> &blocks) {
	std::ostringstream stream;
	stream << "[";
	for (std::size_t block_index = 0; block_index < blocks.size(); ++block_index) {
		if (block_index > 0) {
			stream << ",";
		}
		stream << "[";
		const tet4d::core::CoordND &block = blocks[block_index];
		for (std::size_t axis = 0; axis < block.values.size(); ++axis) {
			if (axis > 0) {
				stream << ",";
			}
			stream << block.values[axis];
		}
		stream << "]";
	}
	stream << "]";
	return stream.str();
}

void print_case(
		const std::string &name,
		const std::vector<tet4d::core::CoordND> &actual,
		bool last) {
	std::cout << "    {\"name\":\"" << name << "\",\"actual\":" << blocks_json(actual) << "}";
	if (!last) {
		std::cout << ",";
	}
	std::cout << "\n";
}

std::vector<tet4d::core::CoordND> blocks_2d() {
	return {{{2, -1}}, {{0, 0}}, {{2, -1}}, {{1, 0}}};
}

std::vector<tet4d::core::CoordND> blocks_3d() {
	return {{{2, -1, 0}}, {{0, 0, 1}}, {{1, 0, -1}}, {{0, 1, 1}}};
}

std::vector<tet4d::core::CoordND> blocks_4d() {
	return {{{1, -2, 0, 3}}, {{0, -1, 1, 2}}, {{2, -2, 0, 1}}, {{1, -3, 1, 2}}};
}

void test_geometry_helpers() {
	require(
		tet4d::core::canonicalize_blocks_nd(blocks_2d()) == std::vector<tet4d::core::CoordND>({{{0, 0}}, {{1, 0}}, {{2, -1}}, {{2, -1}}}),
		"canonicalize should preserve duplicate cells and sort lexicographically"
	);
	require(
		tet4d::core::normalize_blocks_nd(blocks_3d()) == std::vector<tet4d::core::CoordND>({{{-1, 0, 1}}, {{-1, 1, 1}}, {{0, 0, -1}}, {{1, -1, 0}}}),
		"normalize should match Python center and ordering"
	);
	require(
		tet4d::core::translate_blocks_nd(blocks_3d(), {{-2, 3, 1}}) == std::vector<tet4d::core::CoordND>({{{-2, 3, 2}}, {{-2, 4, 2}}, {{-1, 3, 0}}, {{0, 2, 1}}}),
		"translate should sort translated blocks"
	);
	require(
		tet4d::core::rotate_blocks_nd(blocks_3d(), 0, 2, 1) == std::vector<tet4d::core::CoordND>({{{1, -1, -1}}, {{2, 0, 1}}, {{0, 0, 0}}, {{2, 1, 1}}}),
		"3D rotation should match Python pivot-sensitive output"
	);
	require(
		tet4d::core::rotate_blocks_nd(blocks_4d(), 0, 3, -1) == std::vector<tet4d::core::CoordND>({{{0, -2, 0, 2}}, {{1, -1, 1, 1}}, {{2, -2, 0, 3}}, {{1, -3, 1, 2}}}),
		"4D negative quarter turn should match Python output"
	);
	require(
		tet4d::core::rotate_blocks_nd_around_pivot({{{1, 0}}, {{0, 1}}}, 0, 1, 1, 0.0, 0.0) == std::vector<tet4d::core::CoordND>({{{0, -1}}, {{1, 0}}}),
		"explicit pivot rotation should use the requested pivot"
	);
	require(
		tet4d::core::geometry_hash_blocks(blocks_3d()) == "bbec08d1ebde9192",
		"geometry hash should match Python FNV reference over canonical serialization"
	);
}

void print_geometry_parity_json() {
	std::cout << "{\n";
	std::cout << "  \"cases\": [\n";
	print_case("canonicalize_2d_duplicates", tet4d::core::canonicalize_blocks_nd(blocks_2d()), false);
	print_case("normalize_3d_negative_unsorted", tet4d::core::normalize_blocks_nd(blocks_3d()), false);
	print_case("translate_3d", tet4d::core::translate_blocks_nd(blocks_3d(), {{-2, 3, 1}}), false);
	print_case("rotate_3d_xz", tet4d::core::rotate_blocks_nd(blocks_3d(), 0, 2, 1), false);
	print_case("rotate_4d_xw_negative", tet4d::core::rotate_blocks_nd(blocks_4d(), 0, 3, -1), false);
	print_case("rotate_2d_explicit_pivot", tet4d::core::rotate_blocks_nd_around_pivot({{{1, 0}}, {{0, 1}}}, 0, 1, 1, 0.0, 0.0), true);
	std::cout << "  ],\n";
	std::cout << "  \"hash_case\": {\"name\":\"hash_3d\",\"actual\":\"" << tet4d::core::geometry_hash_blocks(blocks_3d()) << "\"}\n";
	std::cout << "}\n";
}

} // namespace

int main(int argc, char **argv) {
	if (argc >= 2 && std::string(argv[1]) == "--geometry-parity") {
		print_geometry_parity_json();
		return 0;
	}
	test_geometry_helpers();
	std::cout << "tet4d_core geometry tests passed\n";
	return 0;
}
