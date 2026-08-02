#include "tet4d_core/topology_transport.hpp"

#include "tet4d_core/generated/topology_contract_v1.hpp"

#include <algorithm>
#include <cctype>
#include <set>
#include <sstream>
#include <utility>

namespace tet4d::core {
namespace {

template <typename T>
TopologyTransportResult<T> failure(
		std::string code,
		std::string path,
		std::string expected,
		std::string actual,
		std::string message) {
	TopologyTransportResult<T> result;
	result.error = TopologyTransportError{
			std::move(code),
			std::move(path),
			std::move(expected),
			std::move(actual),
			std::move(message)};
	return result;
}

template <typename T>
TopologyTransportResult<T> success(T value) {
	TopologyTransportResult<T> result;
	result.value = std::move(value);
	return result;
}

std::string trim(std::string value) {
	const auto first = std::find_if_not(value.begin(), value.end(), [](unsigned char ch) {
		return std::isspace(ch) != 0;
	});
	const auto last = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char ch) {
		return std::isspace(ch) != 0;
	}).base();
	if (first >= last) {
		return {};
	}
	return std::string(first, last);
}

std::string lowercase(std::string value) {
	std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
		return static_cast<char>(std::tolower(ch));
	});
	return value;
}

const TransportValue::Object *require_object(
		const TransportValue &value,
		const std::string &path,
		TopologyTransportError &error) {
	const auto *object = std::get_if<TransportValue::Object>(&value.value);
	if (object == nullptr) {
		error = {"wrong_type", path, "object", transport_value_category(value), path + " must be an object"};
	}
	return object;
}

const TransportValue::Array *require_array(
		const TransportValue &value,
		const std::string &path,
		TopologyTransportError &error) {
	const auto *array = std::get_if<TransportValue::Array>(&value.value);
	if (array == nullptr) {
		error = {"wrong_type", path, "array", transport_value_category(value), path + " must be an array"};
	}
	return array;
}

const TransportValue *required_field(
		const TransportValue::Object &object,
		const std::string &field,
		const std::string &path,
		TopologyTransportError &error) {
	const auto found = object.find(field);
	if (found == object.end()) {
		error = {"missing_field", path + "." + field, "present field", "missing", path + "." + field + " is required"};
		return nullptr;
	}
	return &found->second;
}

bool require_exact_fields(
		const TransportValue::Object &object,
		const std::set<std::string> &fields,
		const std::string &path,
		TopologyTransportError &error) {
	for (const std::string &field : fields) {
		if (object.find(field) == object.end()) {
			error = {"missing_field", path + "." + field, "present field", "missing", path + "." + field + " is required"};
			return false;
		}
	}
	for (const auto &[field, unused] : object) {
		(void)unused;
		if (fields.find(field) == fields.end()) {
			error = {"unknown_required_value", path + "." + field, "known field", "unknown field", path + "." + field + " is not supported"};
			return false;
		}
	}
	return true;
}

const std::int64_t *require_integer(
		const TransportValue &value,
		const std::string &path,
		TopologyTransportError &error) {
	const auto *integer = std::get_if<std::int64_t>(&value.value);
	if (integer == nullptr) {
		error = {"wrong_type", path, "integer", transport_value_category(value), path + " must be an integer"};
	}
	return integer;
}

const bool *require_boolean(
		const TransportValue &value,
		const std::string &path,
		TopologyTransportError &error) {
	const auto *boolean = std::get_if<bool>(&value.value);
	if (boolean == nullptr) {
		error = {"wrong_type", path, "boolean", transport_value_category(value), path + " must be a boolean"};
	}
	return boolean;
}

const std::string *require_string(
		const TransportValue &value,
		const std::string &path,
		TopologyTransportError &error) {
	const auto *string = std::get_if<std::string>(&value.value);
	if (string == nullptr) {
		error = {"wrong_type", path, "string", transport_value_category(value), path + " must be a string"};
	}
	return string;
}

template <typename Container, typename Value>
bool contains(const Container &values, const Value &value) {
	return std::find(values.begin(), values.end(), value) != values.end();
}

bool decode_integer_array(
		const TransportValue &value,
		const std::string &path,
		std::vector<std::int64_t> &result,
		TopologyTransportError &error) {
	const TransportValue::Array *array = require_array(value, path, error);
	if (array == nullptr) {
		return false;
	}
	result.clear();
	result.reserve(array->size());
	for (std::size_t index = 0; index < array->size(); ++index) {
		const std::string item_path = path + "[" + std::to_string(index) + "]";
		const std::int64_t *item = require_integer((*array)[index], item_path, error);
		if (item == nullptr) {
			return false;
		}
		result.push_back(*item);
	}
	return true;
}

bool decode_boundary(
		const TransportValue &value,
		const std::string &path,
		std::int64_t rank,
		TopologyTransportBoundary &result,
		TopologyTransportError &error) {
	const TransportValue::Object *object = require_object(value, path, error);
	if (object == nullptr || !require_exact_fields(*object, {"axis", "side"}, path, error)) {
		return false;
	}
	const TransportValue *axis_value = required_field(*object, "axis", path, error);
	const TransportValue *side_value = required_field(*object, "side", path, error);
	if (axis_value == nullptr || side_value == nullptr) {
		return false;
	}
	const std::string *raw_axis = require_string(*axis_value, path + ".axis", error);
	if (raw_axis == nullptr) {
		return false;
	}
	const std::string axis = lowercase(trim(*raw_axis));
	auto axis_found = std::find(generated::AXIS_NAMES.begin(), generated::AXIS_NAMES.end(), axis);
	if (axis_found == generated::AXIS_NAMES.end() ||
			std::distance(generated::AXIS_NAMES.begin(), axis_found) >= rank) {
		error = {"invalid_axis", path + ".axis", "axis name within profile rank", axis, path + ".axis is outside the profile rank"};
		return false;
	}
	const std::string *raw_side = require_string(*side_value, path + ".side", error);
	if (raw_side == nullptr) {
		return false;
	}
	const std::string side = trim(*raw_side);
	if (!contains(generated::VALID_BOUNDARY_SIDES, std::string_view(side))) {
		error = {"invalid_side", path + ".side", "- or +", side, path + ".side must be a contract boundary side"};
		return false;
	}
	result.axis = std::distance(generated::AXIS_NAMES.begin(), axis_found);
	result.side = side;
	return true;
}

bool decode_transform(
		const TransportValue &value,
		const std::string &path,
		std::int64_t rank,
		TopologyTransportTransform &result,
		TopologyTransportError &error) {
	const TransportValue::Object *object = require_object(value, path, error);
	if (object == nullptr || !require_exact_fields(*object, {"permutation", "signs"}, path, error)) {
		return false;
	}
	if (!decode_integer_array(object->at("permutation"), path + ".permutation", result.permutation, error) ||
			!decode_integer_array(object->at("signs"), path + ".signs", result.signs, error)) {
		return false;
	}
	const std::size_t tangent_rank = static_cast<std::size_t>(rank - 1);
	if (result.permutation.size() != tangent_rank) {
		error = {"invalid_permutation", path + ".permutation", "one entry per tangent axis", std::to_string(result.permutation.size()), path + ".permutation length must equal rank minus one"};
		return false;
	}
	if (result.signs.size() != tangent_rank) {
		error = {"invalid_sign", path + ".signs", "one sign per tangent axis", std::to_string(result.signs.size()), path + ".signs length must equal rank minus one"};
		return false;
	}
	std::set<std::int64_t> seen;
	for (std::size_t index = 0; index < tangent_rank; ++index) {
		const std::int64_t permutation = result.permutation[index];
		if (permutation < 0 || permutation >= rank - 1 || !seen.insert(permutation).second) {
			error = {"invalid_permutation", path + ".permutation[" + std::to_string(index) + "]", "unique tangent-axis index", std::to_string(permutation), path + ".permutation must be a complete permutation"};
			return false;
		}
		const std::int64_t sign = result.signs[index];
		if (!contains(generated::VALID_TRANSFORM_SIGNS, sign)) {
			error = {"invalid_sign", path + ".signs[" + std::to_string(index) + "]", "-1 or 1", std::to_string(sign), path + ".signs must contain contract signs"};
			return false;
		}
	}
	return true;
}

std::vector<std::int64_t> boundary_extents(
		const std::vector<std::int64_t> &dimensions,
		std::int64_t axis) {
	std::vector<std::int64_t> result;
	for (std::size_t index = 0; index < dimensions.size(); ++index) {
		if (static_cast<std::int64_t>(index) != axis) {
			result.push_back(dimensions[index]);
		}
	}
	return result;
}

bool same_boundary(const TopologyTransportBoundary &left, const TopologyTransportBoundary &right) {
	return left.axis == right.axis && left.side == right.side;
}

std::string boundary_key(const TopologyTransportBoundary &boundary) {
	return std::to_string(boundary.axis) + boundary.side;
}

} // namespace

std::string transport_value_category(const TransportValue &value) {
	if (std::holds_alternative<std::monostate>(value.value)) return "null";
	if (std::holds_alternative<bool>(value.value)) return "boolean";
	if (std::holds_alternative<std::int64_t>(value.value)) return "integer";
	if (std::holds_alternative<double>(value.value)) return "float";
	if (std::holds_alternative<std::string>(value.value)) return "string";
	if (std::holds_alternative<TransportValue::Array>(value.value)) return "array";
	if (std::holds_alternative<TransportValue::Object>(value.value)) return "object";
	return std::get<UnsupportedTransportValue>(value.value).category;
}

TopologyTransportResult<TopologyTransportProfile> decode_topology_transport_profile(
		const TransportValue &payload) {
	TopologyTransportError error;
	const auto *object = require_object(payload, "profile", error);
	if (object == nullptr || !require_exact_fields(*object, {"contract_version", "dimensions", "rank", "seams"}, "profile", error)) {
		return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
	}
	TopologyTransportProfile profile;
	const std::int64_t *version = require_integer(object->at("contract_version"), "profile.contract_version", error);
	if (version == nullptr) {
		return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
	}
	if (*version != generated::CONTRACT_VERSION) {
		return failure<TopologyTransportProfile>("contract_version_mismatch", "profile.contract_version", std::to_string(generated::CONTRACT_VERSION), std::to_string(*version), "profile.contract_version is unsupported");
	}
	profile.contract_version = *version;
	const std::int64_t *rank = require_integer(object->at("rank"), "profile.rank", error);
	if (rank == nullptr) {
		return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
	}
	if (*rank < generated::MINIMUM_RANK || *rank > generated::MAXIMUM_RANK) {
		return failure<TopologyTransportProfile>("invalid_rank", "profile.rank", "contract rank range", std::to_string(*rank), "profile.rank is outside the contract range");
	}
	profile.rank = *rank;
	if (!decode_integer_array(object->at("dimensions"), "profile.dimensions", profile.dimensions, error)) {
		return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
	}
	if (profile.dimensions.size() != static_cast<std::size_t>(profile.rank)) {
		return failure<TopologyTransportProfile>("invalid_dimension_count", "profile.dimensions", "one dimension per rank axis", std::to_string(profile.dimensions.size()), "profile.dimensions length must equal rank");
	}
	std::int64_t volume = 1;
	for (std::size_t index = 0; index < profile.dimensions.size(); ++index) {
		const std::int64_t dimension = profile.dimensions[index];
		const std::string path = "profile.dimensions[" + std::to_string(index) + "]";
		if (dimension < generated::MINIMUM_AXIS_LENGTH || dimension > generated::MAXIMUM_AXIS_LENGTH) {
			return failure<TopologyTransportProfile>("out_of_range", path, "contract axis-length range", std::to_string(dimension), path + " is outside the contract axis-length range");
		}
		if (volume > generated::MAXIMUM_INDEXABLE_VOLUME / dimension) {
			return failure<TopologyTransportProfile>("volume_overflow", "profile.dimensions", "product at most maximum indexable volume", "product exceeds maximum", "profile.dimensions product exceeds the contract maximum");
		}
		volume *= dimension;
	}
	const TransportValue::Array *seams = require_array(object->at("seams"), "profile.seams", error);
	if (seams == nullptr) {
		return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
	}
	std::set<std::string> ids;
	std::set<std::string> active_boundaries;
	for (std::size_t index = 0; index < seams->size(); ++index) {
		const std::string path = "profile.seams[" + std::to_string(index) + "]";
		const TransportValue::Object *row = require_object((*seams)[index], path, error);
		if (row == nullptr || !require_exact_fields(*row, {"enabled", "id", "source", "target", "transform"}, path, error)) {
			return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
		}
		TopologyTransportSeam seam;
		const std::string *raw_id = require_string(row->at("id"), path + ".id", error);
		if (raw_id == nullptr) {
			return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
		}
		seam.id = trim(*raw_id);
		if (seam.id.empty() || !ids.insert(seam.id).second) {
			return failure<TopologyTransportProfile>("unknown_required_value", path + ".id", "unique non-empty string", seam.id.empty() ? "empty" : seam.id, path + ".id must be unique and non-empty");
		}
		if (!decode_boundary(row->at("source"), path + ".source", profile.rank, seam.source, error) ||
				!decode_boundary(row->at("target"), path + ".target", profile.rank, seam.target, error) ||
				!decode_transform(row->at("transform"), path + ".transform", profile.rank, seam.transform, error)) {
			return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
		}
		const bool *enabled = require_boolean(row->at("enabled"), path + ".enabled", error);
		if (enabled == nullptr) {
			return failure<TopologyTransportProfile>(error.code, error.path, error.expected, error.actual, error.message);
		}
		seam.enabled = *enabled;
		if (same_boundary(seam.source, seam.target)) {
			return failure<TopologyTransportProfile>("invalid_side", path + ".target", "boundary distinct from source", boundary_key(seam.target), path + " cannot identify a boundary with itself");
		}
		const auto source_extents = boundary_extents(profile.dimensions, seam.source.axis);
		const auto target_extents = boundary_extents(profile.dimensions, seam.target.axis);
		for (std::size_t source_index = 0; source_index < seam.transform.permutation.size(); ++source_index) {
			const std::size_t target_index = static_cast<std::size_t>(seam.transform.permutation[source_index]);
			if (source_extents[source_index] != target_extents[target_index]) {
				return failure<TopologyTransportProfile>("invalid_permutation", path + ".transform.permutation[" + std::to_string(source_index) + "]", "extent-compatible tangent mapping", std::to_string(seam.transform.permutation[source_index]), path + ".transform does not preserve boundary extents");
			}
		}
		if (seam.enabled &&
				(!active_boundaries.insert(boundary_key(seam.source)).second ||
				 !active_boundaries.insert(boundary_key(seam.target)).second)) {
			return failure<TopologyTransportProfile>("unknown_required_value", path, "unused active boundaries", "duplicate active boundary", path + " reuses an active boundary");
		}
		profile.seams.push_back(std::move(seam));
	}
	return success(std::move(profile));
}

TopologyTransportResult<TopologyTransportQuery> decode_topology_transport_query(
		const TransportValue &payload,
		const TopologyTransportProfile &profile) {
	TopologyTransportError error;
	const auto *object = require_object(payload, "query", error);
	if (object == nullptr || !require_exact_fields(*object, {"axis", "coordinate", "delta", "dimensions"}, "query", error)) {
		return failure<TopologyTransportQuery>(error.code, error.path, error.expected, error.actual, error.message);
	}
	TopologyTransportQuery query;
	if (!decode_integer_array(object->at("dimensions"), "query.dimensions", query.dimensions, error) ||
			!decode_integer_array(object->at("coordinate"), "query.coordinate", query.coordinate, error)) {
		return failure<TopologyTransportQuery>(error.code, error.path, error.expected, error.actual, error.message);
	}
	if (query.dimensions.size() != static_cast<std::size_t>(profile.rank)) {
		return failure<TopologyTransportQuery>("invalid_dimension_count", "query.dimensions", "one dimension per profile rank axis", std::to_string(query.dimensions.size()), "query.dimensions length must equal profile rank");
	}
	if (query.dimensions != profile.dimensions) {
		return failure<TopologyTransportQuery>("unknown_required_value", "query.dimensions", "dimensions equal to validated profile", "different dimensions", "query.dimensions must equal profile.dimensions");
	}
	if (query.coordinate.size() != static_cast<std::size_t>(profile.rank)) {
		return failure<TopologyTransportQuery>("coordinate_rank_mismatch", "query.coordinate", "one coordinate per profile rank axis", std::to_string(query.coordinate.size()), "query.coordinate length must equal profile rank");
	}
	for (std::size_t index = 0; index < query.coordinate.size(); ++index) {
		if (query.coordinate[index] < 0 || query.coordinate[index] >= query.dimensions[index]) {
			const std::string path = "query.coordinate[" + std::to_string(index) + "]";
			return failure<TopologyTransportQuery>("coordinate_out_of_bounds", path, "coordinate inside board dimensions", std::to_string(query.coordinate[index]), path + " is outside the board");
		}
	}
	const std::int64_t *axis = require_integer(object->at("axis"), "query.axis", error);
	if (axis == nullptr) {
		return failure<TopologyTransportQuery>(error.code, error.path, error.expected, error.actual, error.message);
	}
	if (*axis < 0 || *axis >= profile.rank) {
		return failure<TopologyTransportQuery>("invalid_axis", "query.axis", "axis index within profile rank", std::to_string(*axis), "query.axis is outside the profile rank");
	}
	query.axis = *axis;
	const std::int64_t *delta = require_integer(object->at("delta"), "query.delta", error);
	if (delta == nullptr) {
		return failure<TopologyTransportQuery>(error.code, error.path, error.expected, error.actual, error.message);
	}
	if (!contains(generated::VALID_MOVEMENT_DELTAS, *delta)) {
		return failure<TopologyTransportQuery>("invalid_delta", "query.delta", "-1 or 1", std::to_string(*delta), "query.delta must be a contract unit movement delta");
	}
	query.delta = *delta;
	return success(std::move(query));
}

TopologyQueryProfile topology_query_profile_from_transport(
		const TopologyTransportProfile &profile) {
	TopologyQueryProfile result;
	result.dimension = static_cast<int>(profile.rank);
	for (const TopologyTransportSeam &seam : profile.seams) {
		BoundaryQueryTransform transform;
		for (const std::int64_t value : seam.transform.permutation) transform.permutation.push_back(static_cast<int>(value));
		for (const std::int64_t value : seam.transform.signs) transform.signs.push_back(static_cast<int>(value));
		result.gluings.push_back(GluingQueryDescriptor{
				seam.id,
				BoundaryQueryRef{static_cast<int>(profile.rank), static_cast<int>(seam.source.axis), seam.source.side == "-" ? -1 : 1},
				BoundaryQueryRef{static_cast<int>(profile.rank), static_cast<int>(seam.target.axis), seam.target.side == "-" ? -1 : 1},
				std::move(transform),
				seam.enabled});
	}
	return result;
}

TopologyCellStepQueryResult resolve_topology_transport_query(
		const TopologyTransportProfile &profile,
		const TopologyTransportQuery &query) {
	std::vector<int> dimensions;
	CoordND coordinate;
	for (const std::int64_t value : query.dimensions) dimensions.push_back(static_cast<int>(value));
	for (const std::int64_t value : query.coordinate) coordinate.values.push_back(static_cast<int>(value));
	return resolve_topology_cell_step_query(
			topology_query_profile_from_transport(profile),
			BoardShapeND{std::move(dimensions)},
			coordinate,
			MoveStepQuery{static_cast<int>(query.axis), static_cast<int>(query.delta)});
}

} // namespace tet4d::core
