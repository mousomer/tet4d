#pragma once

#include "tet4d_core/board_extent_contract.hpp"
#include "tet4d_core/generated/board_extent_contract_v1.hpp"
#include "tet4d_core/plain_game_setup.hpp"

namespace tet4d::core::detail {

inline bool has_valid_extent(const std::string &mode, const std::vector<int> &shape, const std::string &piece_set) {
	BoardExtentValidationRequest request;
	request.contract_version = generated::BOARD_EXTENT_CONTRACT_VERSION;
	request.mode = mode;
	request.board_shape.assign(shape.begin(), shape.end());
	request.piece_set_id = piece_set;
	request.topology_profile = bounded_topology_profile_for_shape(shape);
	return validate_live_board_setup(request).ok;
}

inline std::optional<PlainGameSetup> prepare_setup(const PlainGameSetup &requested, const std::string &mode) {
	if (requested.schema_version != PLAIN_SETUP_SCHEMA_VERSION ||
			requested.mode != mode ||
			!is_valid_plain_random_mode(requested.random_mode) ||
			!is_valid_plain_speed(requested.initial_speed_level) ||
			!has_valid_extent(mode, requested.board_shape, requested.piece_set_id) ||
			(requested.random_mode == RANDOM_MODE_FIXED_SEED &&
			 (!requested.configured_seed.has_value() || !is_valid_plain_seed(*requested.configured_seed)))) {
		return std::nullopt;
	}
	PlainGameSetup validated = requested;
	validated.shuffle_bag = true;
	if (validated.random_mode == RANDOM_MODE_TRUE_RANDOM) {
		validated.configured_seed.reset();
		validated.effective_seed = generate_effective_seed();
	} else {
		validated.effective_seed = *validated.configured_seed;
	}
	return validated;
}

} // namespace tet4d::core::detail
