#include "tet4d_core/board_extent_contract.hpp"

#include "tet4d_core/generated/board_extent_contract_v1.hpp"
#include "tet4d_core/generated/topology_contract_v1.hpp"
#include "tet4d_core/plain_piece_catalog.hpp"

#include <algorithm>
#include <limits>
#include <sstream>
#include <string_view>
#include <utility>

namespace tet4d::core {
namespace {

const generated::BoardExtentModeSpec *mode_spec_for(std::string_view mode) {
	const auto found = std::find_if(
			generated::BOARD_EXTENT_MODE_SPECS.begin(),
			generated::BOARD_EXTENT_MODE_SPECS.end(),
			[mode](const generated::BoardExtentModeSpec &spec) { return spec.id == mode; });
	return found == generated::BOARD_EXTENT_MODE_SPECS.end() ? nullptr : &*found;
}

BoardExtentValidationError error(
		std::string code,
		std::string path,
		std::string expected,
		std::string actual,
		std::string message) {
	return {std::move(code), std::move(path), std::move(expected), std::move(actual), std::move(message)};
}

BoardExtentValidationResult rejected(BoardExtentValidationError detail) {
	BoardExtentValidationResult result;
	result.errors.push_back(std::move(detail));
	return result;
}

bool checked_volume(const std::vector<std::int64_t> &shape, std::int64_t &result) {
	result = 1;
	for (const std::int64_t value : shape) {
		if (value < 1 || result > std::numeric_limits<std::int64_t>::max() / value) {
			return false;
		}
		result *= value;
	}
	return true;
}

bool piece_shape_matches_rank(const PieceShape2D &piece, int rank) {
	return rank == 2 && !piece.blocks.empty();
}

bool piece_shape_matches_rank(const PieceShapeND &piece, int rank) {
	return !piece.blocks.empty() && std::all_of(
			piece.blocks.begin(), piece.blocks.end(), [rank](const CoordND &block) {
				return block.dimension() == rank;
			});
}

std::string values_to_string(const std::vector<std::int64_t> &values) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < values.size(); ++index) {
		if (index != 0) {
			out << ", ";
		}
		out << values[index];
	}
	out << "]";
	return out.str();
}

std::string expected_axis_range(const generated::BoardExtentModeSpec &spec, std::size_t axis) {
	std::ostringstream out;
	out << "integer in [" << spec.axis_minima[axis] << ", " << spec.axis_maxima[axis] << "]";
	return out.str();
}

const TransportValue *transport_field(
		const TransportValue::Object &object,
		const std::string &name,
		BoardExtentValidationResult &result) {
	const auto found = object.find(name);
	if (found == object.end()) {
		result.errors.push_back(error(
				"invalid_field_type", "$." + name, "present field", "missing",
				"The live board validation request requires this field."));
		return nullptr;
	}
	return &found->second;
}

bool transport_integer(
		const TransportValue &value,
		const std::string &path,
		std::int64_t &result,
		BoardExtentValidationResult &validation) {
	const auto *integer = std::get_if<std::int64_t>(&value.value);
	if (integer == nullptr) {
		validation.errors.push_back(error(
				"invalid_field_type", path, "integer", transport_value_category(value),
				"This field must be an integer without coercion."));
		return false;
	}
	result = *integer;
	return true;
}

bool transport_string(
		const TransportValue &value,
		const std::string &path,
		std::string &result,
		BoardExtentValidationResult &validation) {
	const auto *string = std::get_if<std::string>(&value.value);
	if (string == nullptr) {
		validation.errors.push_back(error(
				"invalid_field_type", path, "string", transport_value_category(value),
				"This field must be a string."));
		return false;
	}
	result = *string;
	return true;
}

} // namespace

TopologyTransportProfile bounded_topology_profile_for_shape(const std::vector<int> &shape) {
	TopologyTransportProfile profile;
	profile.contract_version = generated::CONTRACT_VERSION;
	profile.rank = static_cast<std::int64_t>(shape.size());
	profile.dimensions.reserve(shape.size());
	for (const int extent : shape) {
		profile.dimensions.push_back(extent);
	}
	return profile;
}

std::vector<int> canonical_live_board_shape(const std::string &mode) {
	const generated::BoardExtentModeSpec *spec = mode_spec_for(mode);
	if (spec == nullptr) {
		return {};
	}
	std::vector<int> result;
	result.reserve(static_cast<std::size_t>(spec->rank));
	for (std::int64_t axis = 0; axis < spec->rank; ++axis) {
		result.push_back(static_cast<int>(spec->canonical_default_shape[static_cast<std::size_t>(axis)]));
	}
	return result;
}

BoardExtentValidationResult validate_live_board_setup(
		const BoardExtentValidationRequest &request) {
	if (request.contract_version != generated::BOARD_EXTENT_CONTRACT_VERSION) {
		return rejected(error(
				"unsupported_contract_version", "$.contract_version",
				std::to_string(generated::BOARD_EXTENT_CONTRACT_VERSION),
				std::to_string(request.contract_version),
				"The requested board-extent contract version is not supported."));
	}
	const generated::BoardExtentModeSpec *spec = mode_spec_for(request.mode);
	if (spec == nullptr) {
		return rejected(error(
				"unsupported_mode", "$.mode", "live_2d, live_3d, or live_4d", request.mode,
				"The requested live mode is not supported by this contract."));
	}
	if (request.board_shape.size() != static_cast<std::size_t>(spec->rank)) {
		return rejected(error(
				"rank_mismatch", "$.board_shape", std::to_string(spec->rank) + " integer extents",
				std::to_string(request.board_shape.size()) + " extents",
				"The board shape rank must match the selected live mode."));
	}

	BoardExtentValidationResult result;
	for (std::size_t axis = 0; axis < request.board_shape.size(); ++axis) {
		const std::int64_t value = request.board_shape[axis];
		const std::string path = "$.board_shape[" + std::to_string(axis) + "]";
		if (value < spec->axis_minima[axis]) {
			result.errors.push_back(error(
					"axis_below_minimum", path, expected_axis_range(*spec, axis), std::to_string(value),
					"The board extent is below the professional live minimum."));
		} else if (value > spec->axis_maxima[axis]) {
			result.errors.push_back(error(
					"axis_above_maximum", path, expected_axis_range(*spec, axis), std::to_string(value),
					"The board extent exceeds the professional live maximum."));
		}
	}
	if (!result.errors.empty()) {
		return result;
	}

	std::int64_t volume = 0;
	if (!checked_volume(request.board_shape, volume)) {
		return rejected(error(
				"native_volume_overflow", "$.board_shape", "signed 64-bit cell product",
				values_to_string(request.board_shape),
				"The requested board volume cannot be represented safely by the native implementation."));
	}
	if (volume > spec->native_maximum_cells) {
		return rejected(error(
				"native_volume_limit_exceeded", "$.board_shape",
				"at most " + std::to_string(spec->native_maximum_cells) + " cells",
				std::to_string(volume) + " cells",
				"The requested board exceeds the product-level native cell limit."));
	}

	const TopologyTransportProfile &topology = request.topology_profile;
	if (topology.rank != spec->rank || topology.dimensions.size() != request.board_shape.size()) {
		return rejected(error(
				"topology_dimensions_mismatch", "$.topology_profile.rank",
				"rank " + std::to_string(spec->rank) + " matching the selected mode",
				std::to_string(topology.rank),
				"Topology rank must match the selected live mode."));
	}
	if (topology.dimensions != request.board_shape) {
		return rejected(error(
				"topology_dimensions_mismatch", "$.topology_profile.dimensions",
				values_to_string(request.board_shape), values_to_string(topology.dimensions),
				"Topology dimensions must exactly match the requested board shape."));
	}
	if (!topology.seams.empty()) {
		return rejected(error(
				"unsupported_topology_rule", "$.topology_profile.seams", "empty seams for bounded topology",
				std::to_string(topology.seams.size()) + " seams",
				"Stage 54B-1 supports only the bounded no-seam topology rule."));
	}

	if (!is_supported_live_piece_set(static_cast<int>(spec->rank), request.piece_set_id)) {
		const bool known_elsewhere = is_known_live_piece_set(request.piece_set_id);
		return rejected(error(
				known_elsewhere ? "piece_dimension_mismatch" : "unsupported_piece_set",
				"$.piece_set_id",
				known_elsewhere ? "piece set compatible with mode rank " + std::to_string(spec->rank) : "supported production piece set",
				request.piece_set_id,
				known_elsewhere ? "The selected production piece set belongs to another live dimension." : "The selected piece set is not a production live catalogue."));
	}

	std::vector<int> shape;
	shape.reserve(request.board_shape.size());
	for (const std::int64_t extent : request.board_shape) {
		shape.push_back(static_cast<int>(extent));
	}
	if (spec->rank == 2) {
		for (const PieceShape2D &piece : plain_piece_catalog_2d(request.piece_set_id)) {
			if (!piece_shape_matches_rank(piece, 2)) {
				return rejected(error("piece_dimension_mismatch", "$.piece_set_id", "2D production pieces", piece.name, "The catalogue contains a piece with the wrong dimensionality."));
			}
			if (!canonical_spawn_viable_2d(shape[0], shape[1], piece)) {
				return rejected(error("spawn_not_viable", "$.piece_set_id", "canonical viable spawn", piece.name, "A production piece cannot enter this empty board through its canonical spawn path."));
			}
		}
	} else {
		const BoardShapeND board{shape};
		for (const PieceShapeND &piece : plain_piece_catalog_nd(static_cast<int>(spec->rank), request.piece_set_id)) {
			if (!piece_shape_matches_rank(piece, static_cast<int>(spec->rank))) {
				return rejected(error("piece_dimension_mismatch", "$.piece_set_id", "production pieces matching board rank", piece.name, "The catalogue contains a piece with the wrong dimensionality."));
			}
			if (!canonical_spawn_viable_nd(board, 1, piece)) {
				return rejected(error("spawn_not_viable", "$.piece_set_id", "canonical viable spawn", piece.name, "A production piece cannot enter this empty board through its canonical spawn path."));
			}
		}
	}

	result.ok = true;
	result.validated_setup = ValidatedLiveBoardSetup{
			request.contract_version, request.mode, std::move(shape), request.piece_set_id,
			request.topology_profile, volume};
	return result;
}

BoardExtentValidationResult validate_live_board_setup_transport(const TransportValue &payload) {
	const auto *object = std::get_if<TransportValue::Object>(&payload.value);
	if (object == nullptr) {
		return rejected(error("invalid_field_type", "$", "object", transport_value_category(payload), "The live board validation request must be an object."));
	}
	BoardExtentValidationResult structure;
	const TransportValue *version = transport_field(*object, "contract_version", structure);
	const TransportValue *mode = transport_field(*object, "mode", structure);
	const TransportValue *shape = transport_field(*object, "board_shape", structure);
	const TransportValue *piece_set = transport_field(*object, "piece_set_id", structure);
	const TransportValue *topology = transport_field(*object, "topology_profile", structure);
	if (!structure.errors.empty()) {
		return structure;
	}
	BoardExtentValidationRequest request;
	bool valid = transport_integer(*version, "$.contract_version", request.contract_version, structure) &&
			transport_string(*mode, "$.mode", request.mode, structure) &&
			transport_string(*piece_set, "$.piece_set_id", request.piece_set_id, structure);
	const auto *shape_array = std::get_if<TransportValue::Array>(&shape->value);
	if (shape_array == nullptr) {
		structure.errors.push_back(error("invalid_field_type", "$.board_shape", "array of integers", transport_value_category(*shape), "Board shape must be an array of integers."));
		valid = false;
	} else {
		for (std::size_t index = 0; index < shape_array->size(); ++index) {
			std::int64_t extent = 0;
			if (!transport_integer((*shape_array)[index], "$.board_shape[" + std::to_string(index) + "]", extent, structure)) {
				valid = false;
				break;
			}
			request.board_shape.push_back(extent);
		}
	}
	const auto *topology_object = std::get_if<TransportValue::Object>(&topology->value);
	if (topology_object == nullptr) {
		structure.errors.push_back(error("invalid_field_type", "$.topology_profile", "object", transport_value_category(*topology), "Topology profile must be an object."));
		valid = false;
	} else {
		auto decoded = decode_topology_transport_profile(*topology);
		if (!decoded.ok()) {
			const TopologyTransportError &detail = *decoded.error;
			structure.errors.push_back(error("invalid_field_type", "$.topology_profile", "strict topology profile", detail.actual, detail.message));
			valid = false;
		} else {
			request.topology_profile = std::move(*decoded.value);
		}
	}
	return valid ? validate_live_board_setup(request) : structure;
}

} // namespace tet4d::core
