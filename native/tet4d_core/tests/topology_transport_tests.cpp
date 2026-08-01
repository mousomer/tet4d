#include "tet4d_core/generated/topology_contract_v1.hpp"
#include "tet4d_core/topology_transport.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <utility>

namespace {

using tet4d::core::TransportValue;

void require(bool condition, const std::string &message) {
	if (!condition) {
		std::cerr << "FAIL: " << message << '\n';
		std::exit(1);
	}
}

TransportValue integer(std::int64_t value) {
	return TransportValue(value);
}

TransportValue array(std::initializer_list<TransportValue> values) {
	return TransportValue(TransportValue::Array(values));
}

TransportValue object(std::initializer_list<std::pair<const std::string, TransportValue>> values) {
	return TransportValue(TransportValue::Object(values));
}

TransportValue boundary(const char *axis, const char *side) {
	return object({{"axis", TransportValue(axis)}, {"side", TransportValue(side)}});
}

TransportValue seam(
		const char *id = "wrap_x",
		TransportValue source = boundary("x", "-"),
		TransportValue target = boundary("x", "+"),
		TransportValue permutation = array({integer(0)}),
		TransportValue signs = array({integer(1)}),
		TransportValue enabled = TransportValue(true)) {
	return object({
			{"id", TransportValue(id)},
			{"source", std::move(source)},
			{"target", std::move(target)},
			{"transform", object({{"permutation", std::move(permutation)}, {"signs", std::move(signs)}})},
			{"enabled", std::move(enabled)},
	});
}

TransportValue profile(
		TransportValue version = integer(1),
		TransportValue rank = integer(2),
		TransportValue dimensions = array({integer(3), integer(4)}),
		TransportValue seams = array({seam()})) {
	return object({
			{"contract_version", std::move(version)},
			{"rank", std::move(rank)},
			{"dimensions", std::move(dimensions)},
			{"seams", std::move(seams)},
	});
}

TransportValue query(
		TransportValue dimensions = array({integer(3), integer(4)}),
		TransportValue coordinate = array({integer(2), integer(1)}),
		TransportValue axis = integer(0),
		TransportValue delta = integer(1)) {
	return object({
			{"dimensions", std::move(dimensions)},
			{"coordinate", std::move(coordinate)},
			{"axis", std::move(axis)},
			{"delta", std::move(delta)},
	});
}

template <typename T>
void require_error(
		const tet4d::core::TopologyTransportResult<T> &result,
		const std::string &code,
		const std::string &path) {
	require(!result.ok(), "expected transport rejection");
	require(result.error.has_value(), "transport rejection should include an error");
	require(result.error->code == code, "error code mismatch: " + result.error->code);
	require(result.error->path == path, "error path mismatch: " + result.error->path);
}

void test_profile_transport() {
	const auto decoded = tet4d::core::decode_topology_transport_profile(profile());
	require(decoded.ok(), "valid minimum-rank profile should decode");
	require(decoded.value->contract_version == tet4d::core::generated::CONTRACT_VERSION, "generated version should be consumed");
	require(decoded.value->rank == 2, "profile rank should be preserved");
	require(decoded.value->dimensions == std::vector<std::int64_t>({3, 4}), "dimensions should be preserved");
	require(decoded.value->seams.size() == 1 && decoded.value->seams[0].enabled, "enabled seam should be preserved");

	const auto rank_four = tet4d::core::decode_topology_transport_profile(profile(
			integer(1),
			integer(4),
			array({integer(7), integer(7), integer(7), integer(7)}),
			array({seam(
					"swap_xw",
					boundary("x", "-"),
					boundary("w", "+"),
					array({integer(2), integer(0), integer(1)}),
					array({integer(1), integer(-1), integer(1)}),
					TransportValue(false))}))) ;
	require(rank_four.ok(), "valid maximum-rank disabled seam should decode");
	require(!rank_four.value->seams[0].enabled, "disabled state should be preserved");
	require(rank_four.value->seams[0].transform.permutation == std::vector<std::int64_t>({2, 0, 1}), "non-identity permutation should be preserved");
}

void test_exact_types() {
	require_error(tet4d::core::decode_topology_transport_profile(profile(TransportValue(true))), "wrong_type", "profile.contract_version");
	require_error(tet4d::core::decode_topology_transport_profile(profile(TransportValue(1.0))), "wrong_type", "profile.contract_version");
	require_error(tet4d::core::decode_topology_transport_profile(profile(TransportValue("1"))), "wrong_type", "profile.contract_version");
	require_error(tet4d::core::decode_topology_transport_profile(profile(integer(0))), "contract_version_mismatch", "profile.contract_version");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({TransportValue(true), integer(4)}))), "wrong_type", "profile.dimensions[0]");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({TransportValue(3.9), integer(4)}))), "wrong_type", "profile.dimensions[0]");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({TransportValue("3"), integer(4)}))), "wrong_type", "profile.dimensions[0]");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({integer(3), integer(4)}),
			array({seam("wrap_x", boundary("x", "-"), boundary("x", "+"), array({integer(0)}), array({integer(1)}), integer(1))}))),
			"wrong_type", "profile.seams[0].enabled");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({integer(3), integer(4)}),
			array({seam("wrap_x", boundary("x", "-"), boundary("x", "+"), array({TransportValue(true)}))}))),
			"wrong_type", "profile.seams[0].transform.permutation[0]");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({integer(3), integer(4)}),
			array({seam("wrap_x", boundary("x", "-"), boundary("x", "+"), array({integer(0)}), array({TransportValue("1")}))}))),
			"wrong_type", "profile.seams[0].transform.signs[0]");
}

void test_contract_limits_and_overflow() {
	require_error(tet4d::core::decode_topology_transport_profile(profile(integer(1), integer(1))), "invalid_rank", "profile.rank");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({integer(0), integer(4)}))), "out_of_range", "profile.dimensions[0]");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({integer(1000001), integer(4)}))), "out_of_range", "profile.dimensions[0]");
	const auto exact_maximum = tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(4),
			array({integer(454279), integer(337), integer(92737), integer(649657)}),
			array({}))) ;
	require(exact_maximum.ok(), "exact maximum volume should decode");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(4),
			array({integer(1000000), integer(1000000), integer(1000000), integer(1000000)}),
			array({}))), "volume_overflow", "profile.dimensions");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(3), array({integer(4), integer(4), integer(4)}),
			array({seam("bad", boundary("x", "-"), boundary("z", "+"),
					array({integer(0), integer(0)}), array({integer(1), integer(1)}))}))),
			"invalid_permutation", "profile.seams[0].transform.permutation[1]");
	require_error(tet4d::core::decode_topology_transport_profile(profile(
			integer(1), integer(2), array({integer(3), integer(4)}),
			array({seam("bad", boundary("x", "-"), boundary("x", "+"),
					array({integer(0)}), array({integer(0)}))}))),
			"invalid_sign", "profile.seams[0].transform.signs[0]");
}

void test_query_transport_and_resolution() {
	const auto decoded_profile = tet4d::core::decode_topology_transport_profile(profile());
	require(decoded_profile.ok(), "query test profile should decode");
	const auto decoded_query = tet4d::core::decode_topology_transport_query(query(), *decoded_profile.value);
	require(decoded_query.ok(), "valid query should decode");
	const auto result = tet4d::core::resolve_topology_transport_query(*decoded_profile.value, *decoded_query.value);
	require(result.ok, "validated query should resolve");
	require(result.target.has_value() && result.target->values == std::vector<int>({0, 1}), "wrapped target should match existing resolver");
	require(result.glue_id == std::optional<std::string>("wrap_x"), "seam id should cross unchanged");

	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({TransportValue(true), integer(1)})), *decoded_profile.value),
			"wrong_type", "query.coordinate[0]");
	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({TransportValue(2.9), integer(1)})), *decoded_profile.value),
			"wrong_type", "query.coordinate[0]");
	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({TransportValue("2"), integer(1)})), *decoded_profile.value),
			"wrong_type", "query.coordinate[0]");
	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({integer(3), integer(1)})), *decoded_profile.value),
			"coordinate_out_of_bounds", "query.coordinate[0]");
	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({integer(2)})), *decoded_profile.value),
			"coordinate_rank_mismatch", "query.coordinate");
	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({integer(2), integer(1)}), TransportValue(true)), *decoded_profile.value),
			"wrong_type", "query.axis");
	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({integer(2), integer(1)}), integer(0), TransportValue(1.9)), *decoded_profile.value),
			"wrong_type", "query.delta");
	require_error(tet4d::core::decode_topology_transport_query(
			query(array({integer(3), integer(4)}), array({integer(2), integer(1)}), integer(0), integer(0)), *decoded_profile.value),
			"invalid_delta", "query.delta");
}

} // namespace

int main() {
	test_profile_transport();
	test_exact_types();
	test_contract_limits_and_overflow();
	test_query_transport_and_resolution();
	std::cout << "tet4d topology transport tests passed\n";
	return 0;
}
