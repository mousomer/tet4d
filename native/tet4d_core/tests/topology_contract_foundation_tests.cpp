#include "tet4d_core/generated/topology_contract_v1.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {

namespace contract = tet4d::core::generated;

void require(bool condition, const std::string &message) {
	if (!condition) {
		std::cerr << message << "\n";
		std::exit(1);
	}
}

void test_contract_constants() {
	require(contract::CONTRACT_NAME == "tet4d.topology_contract", "contract name mismatch");
	require(contract::CONTRACT_VERSION == 1, "contract version mismatch");
	require(contract::MINIMUM_RANK == 2, "minimum rank mismatch");
	require(contract::MAXIMUM_RANK == 4, "maximum rank mismatch");
	require(contract::MINIMUM_AXIS_LENGTH == 1, "minimum axis length mismatch");
	require(contract::MAXIMUM_AXIS_LENGTH == 1000000, "maximum axis length mismatch");
	require(
			contract::MAXIMUM_INDEXABLE_VOLUME == 9223372036854775807LL,
			"maximum indexable volume mismatch");
	require(contract::AXIS_NAMES[0] == "x" && contract::AXIS_NAMES[3] == "w", "axis names mismatch");
	require(
			contract::VALID_TRANSFORM_SIGNS[0] == -1 &&
					contract::VALID_TRANSFORM_SIGNS[1] == 1,
			"transform signs mismatch");
	require(
			contract::VALID_BOUNDARY_SIDES[0] == "-" &&
					contract::VALID_BOUNDARY_SIDES[1] == "+",
			"boundary sides mismatch");
	require(
			contract::VALID_MOVEMENT_DELTAS[0] == -1 &&
					contract::VALID_MOVEMENT_DELTAS[1] == 1,
			"movement deltas mismatch");
	require(contract::CONTRACT_FINGERPRINT.size() == 64, "contract fingerprint length mismatch");
}

void print_contract_metadata() {
	std::cout
			<< "{\"axis_length\":{\"maximum\":" << contract::MAXIMUM_AXIS_LENGTH
			<< ",\"minimum\":" << contract::MINIMUM_AXIS_LENGTH
			<< "},\"axis_names\":[\"x\",\"y\",\"z\",\"w\"]"
			<< ",\"boundary_sides\":[\"-\",\"+\"]"
			<< ",\"contract\":\"" << contract::CONTRACT_NAME << "\""
			<< ",\"contract_fingerprint\":\"" << contract::CONTRACT_FINGERPRINT << "\""
			<< ",\"contract_version\":" << contract::CONTRACT_VERSION
			<< ",\"maximum_indexable_volume\":" << contract::MAXIMUM_INDEXABLE_VOLUME
			<< ",\"movement_deltas\":[-1,1]"
			<< ",\"rank\":{\"maximum\":" << contract::MAXIMUM_RANK
			<< ",\"minimum\":" << contract::MINIMUM_RANK << "}"
			<< ",\"transform_signs\":[-1,1]}\n";
}

} // namespace

int main(int argc, char **argv) {
	test_contract_constants();
	if (argc >= 2 && std::string(argv[1]) == "--contract-metadata") {
		print_contract_metadata();
		return 0;
	}
	std::cout << "tet4d topology contract foundation tests passed\n";
	return 0;
}
