#pragma once

#include "tet4d_core/query.hpp"

#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace tet4d::core {

struct UnsupportedTransportValue {
	std::string category;
};

struct TransportValue {
	using Array = std::vector<TransportValue>;
	using Object = std::map<std::string, TransportValue>;
	using Storage = std::variant<
			std::monostate,
			bool,
			std::int64_t,
			double,
			std::string,
			Array,
			Object,
			UnsupportedTransportValue>;

	Storage value;

	TransportValue() = default;
	explicit TransportValue(bool input) : value(input) {}
	explicit TransportValue(std::int64_t input) : value(input) {}
	explicit TransportValue(double input) : value(input) {}
	explicit TransportValue(std::string input) : value(std::move(input)) {}
	explicit TransportValue(const char *input) : value(std::string(input)) {}
	explicit TransportValue(Array input) : value(std::move(input)) {}
	explicit TransportValue(Object input) : value(std::move(input)) {}
	explicit TransportValue(UnsupportedTransportValue input) : value(std::move(input)) {}
};

struct TopologyTransportError {
	std::string code;
	std::string path;
	std::string expected;
	std::string actual;
	std::string message;
};

template <typename T>
struct TopologyTransportResult {
	std::optional<T> value;
	std::optional<TopologyTransportError> error;

	[[nodiscard]] bool ok() const { return value.has_value(); }
};

struct TopologyTransportBoundary {
	std::int64_t axis = 0;
	std::string side;
};

struct TopologyTransportTransform {
	std::vector<std::int64_t> permutation;
	std::vector<std::int64_t> signs;
};

struct TopologyTransportSeam {
	std::string id;
	TopologyTransportBoundary source;
	TopologyTransportBoundary target;
	TopologyTransportTransform transform;
	bool enabled = true;
};

struct TopologyTransportProfile {
	std::int64_t contract_version = 0;
	std::int64_t rank = 0;
	std::vector<std::int64_t> dimensions;
	std::vector<TopologyTransportSeam> seams;
};

struct TopologyTransportQuery {
	std::vector<std::int64_t> dimensions;
	std::vector<std::int64_t> coordinate;
	std::int64_t axis = 0;
	std::int64_t delta = 0;
};

std::string transport_value_category(const TransportValue &value);
TopologyTransportResult<TopologyTransportProfile> decode_topology_transport_profile(
		const TransportValue &payload);
TopologyTransportResult<TopologyTransportQuery> decode_topology_transport_query(
		const TransportValue &payload,
		const TopologyTransportProfile &profile);
TopologyQueryProfile topology_query_profile_from_transport(
		const TopologyTransportProfile &profile);
TopologyCellStepQueryResult resolve_topology_transport_query(
		const TopologyTransportProfile &profile,
		const TopologyTransportQuery &query);

} // namespace tet4d::core
