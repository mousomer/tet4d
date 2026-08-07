#pragma once

#include "tet4d_core/topology_transport.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace tet4d::core {

struct BoardExtentValidationError {
	std::string code;
	std::string path;
	std::string expected;
	std::string actual;
	std::string message;
};

struct BoardExtentValidationRequest {
	std::int64_t contract_version = 0;
	std::string mode;
	std::vector<std::int64_t> board_shape;
	std::string piece_set_id;
	TopologyTransportProfile topology_profile;
};

struct ValidatedLiveBoardSetup {
	std::int64_t contract_version = 0;
	std::string mode;
	std::vector<int> board_shape;
	std::string piece_set_id;
	TopologyTransportProfile topology_profile;
	std::int64_t native_cell_count = 0;
};

struct BoardExtentValidationResult {
	bool ok = false;
	std::optional<ValidatedLiveBoardSetup> validated_setup;
	std::vector<BoardExtentValidationError> errors;
};

// Validates the Stage 54B professional live-board envelope without constructing
// or mutating a session. Errors are stable in code and path order.
BoardExtentValidationResult validate_live_board_setup(
		const BoardExtentValidationRequest &request);

// Decodes strict Variant-transport values using the same type categories as
// Stage 53B. This is the GDExtension boundary entry point.
BoardExtentValidationResult validate_live_board_setup_transport(
		const TransportValue &payload);

TopologyTransportProfile bounded_topology_profile_for_shape(
		const std::vector<int> &shape);
std::vector<int> canonical_live_board_shape(const std::string &mode);

} // namespace tet4d::core
