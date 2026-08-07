#include "tet4d_core/board_extent_contract.hpp"
#include "tet4d_core/generated/board_extent_contract_v1.hpp"
#include "tet4d_core/plain_2d_session.hpp"
#include "tet4d_core/plain_nd_session.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <tuple>
#include <vector>

namespace {

void require(bool condition, const std::string &message) {
	if (!condition) {
		std::cerr << "board extent contract test failure: " << message << "\n";
		std::exit(1);
	}
}

tet4d::core::BoardExtentValidationRequest request(
		const std::string &mode,
		std::vector<std::int64_t> shape,
		const std::string &piece_set) {
	tet4d::core::BoardExtentValidationRequest result;
	result.contract_version = tet4d::core::generated::BOARD_EXTENT_CONTRACT_VERSION;
	result.mode = mode;
	result.board_shape = std::move(shape);
	result.piece_set_id = piece_set;
	std::vector<int> int_shape;
	for (const std::int64_t extent : result.board_shape) {
		int_shape.push_back(static_cast<int>(extent));
	}
	result.topology_profile = tet4d::core::bounded_topology_profile_for_shape(int_shape);
	return result;
}

void require_error(
		const tet4d::core::BoardExtentValidationResult &result,
		const std::string &code,
		const std::string &path) {
	require(!result.ok, "expected a rejected request");
	require(!result.errors.empty(), "rejected request must include an error");
	require(result.errors.front().code == code, "unexpected error code");
	require(result.errors.front().path == path, "unexpected error path");
}

void test_generated_contract_and_valid_presets() {
	require(
			tet4d::core::generated::BOARD_EXTENT_CONTRACT_NAME == "tet4d.board_extent_contract",
			"contract name mismatch");
	require(tet4d::core::generated::BOARD_EXTENT_MODE_SPECS.size() == 3, "mode count mismatch");
	require(
			tet4d::core::generated::BOARD_EXTENT_MODE_SPECS[2].axis_order[3] == "W",
			"generated axis order mismatch");
	for (const auto &[mode, shape, piece_set] : std::vector<std::tuple<std::string, std::vector<std::int64_t>, std::string>>{
				{"live_2d", {4, 6}, "classic"},
				{"live_2d", {6, 6}, "classic"},
				{"live_2d", {10, 20}, "classic"},
				{"live_3d", {4, 8, 4}, "native_3d"},
				{"live_3d", {6, 10, 6}, "embedded_2d"},
				{"live_3d", {8, 16, 8}, "native_3d"},
				{"live_4d", {4, 8, 3, 3}, "standard_4d_5"},
				{"live_4d", {5, 10, 4, 4}, "embedded_3d"},
				{"live_4d", {8, 16, 5, 8}, "embedded_2d"},
		}) {
		require(tet4d::core::validate_live_board_setup(request(mode, shape, piece_set)).ok, "supported preset must validate");
	}
}

void test_minimum_shapes_and_piece_set_admission() {
	for (const auto &[mode, shape, piece_set] : std::vector<std::tuple<std::string, std::vector<std::int64_t>, std::string>>{
				{"live_2d", {4, 6}, "classic"},
				{"live_3d", {4, 6, 2}, "native_3d"},
				{"live_3d", {4, 6, 2}, "embedded_2d"},
				{"live_4d", {4, 6, 2, 2}, "standard_4d_5"},
				{"live_4d", {4, 6, 2, 1}, "embedded_3d"},
				{"live_4d", {4, 6, 2, 1}, "embedded_2d"},
		}) {
		require(
				tet4d::core::validate_live_board_setup(request(mode, shape, piece_set)).ok,
				"the selected piece set must admit its supported minimum shape");
	}
	require_error(
			tet4d::core::validate_live_board_setup(
					request("live_4d", {4, 6, 2, 1}, "standard_4d_5")),
			"spawn_not_viable", "$.piece_set_id");
	const tet4d::core::PieceShapeND too_wide{
			"synthetic_too_wide", {{{0, 0, 0, 0}}, {{0, 0, 0, 2}}}, 0};
	require(
			!tet4d::core::canonical_spawn_viable_nd(
					tet4d::core::BoardShapeND{{4, 6, 2, 2}}, 1, too_wide),
			"pure spawn viability must reject an out-of-board synthetic piece");
}

void test_bounds_topology_and_piece_errors() {
	require_error(tet4d::core::validate_live_board_setup(request("live_2d", {3, 6}, "classic")), "axis_below_minimum", "$.board_shape[0]");
	require_error(tet4d::core::validate_live_board_setup(request("live_3d", {4, 6, 11}, "native_3d")), "axis_above_maximum", "$.board_shape[2]");
	require_error(tet4d::core::validate_live_board_setup(request("live_4d", {4, 6, 2, 13}, "standard_4d_5")), "axis_above_maximum", "$.board_shape[3]");
	require_error(tet4d::core::validate_live_board_setup(request("unsupported", {6, 6}, "classic")), "unsupported_mode", "$.mode");
	require_error(tet4d::core::validate_live_board_setup(request("live_3d", {6, 10}, "native_3d")), "rank_mismatch", "$.board_shape");

	auto mismatch = request("live_3d", {6, 10, 6}, "native_3d");
	mismatch.topology_profile.dimensions = {6, 10, 5};
	require_error(tet4d::core::validate_live_board_setup(mismatch), "topology_dimensions_mismatch", "$.topology_profile.dimensions");
	auto seams = request("live_2d", {6, 6}, "classic");
	seams.topology_profile.seams.push_back({});
	require_error(tet4d::core::validate_live_board_setup(seams), "unsupported_topology_rule", "$.topology_profile.seams");
	require_error(tet4d::core::validate_live_board_setup(request("live_3d", {6, 10, 6}, "standard_4d_5")), "piece_dimension_mismatch", "$.piece_set_id");
	require_error(tet4d::core::validate_live_board_setup(request("live_4d", {5, 10, 4, 4}, "unknown")), "unsupported_piece_set", "$.piece_set_id");
}

void test_every_axis_boundary() {
	for (const tet4d::core::generated::BoardExtentModeSpec &spec : tet4d::core::generated::BOARD_EXTENT_MODE_SPECS) {
		const std::string mode(spec.id);
		const std::string piece_set = mode == "live_2d" ? "classic" :
				(mode == "live_3d" ? "native_3d" : "embedded_3d");
		std::vector<std::int64_t> baseline;
		for (std::int64_t axis = 0; axis < spec.rank; ++axis) {
			baseline.push_back(spec.canonical_default_shape[static_cast<std::size_t>(axis)]);
		}
		for (std::size_t axis = 0; axis < baseline.size(); ++axis) {
			const std::string path = "$.board_shape[" + std::to_string(axis) + "]";
			auto shape = baseline;
			shape[axis] = spec.axis_minima[axis];
			require(tet4d::core::validate_live_board_setup(request(mode, shape, piece_set)).ok, "axis minimum must validate");
			shape[axis] = spec.axis_minima[axis] - 1;
			require_error(tet4d::core::validate_live_board_setup(request(mode, shape, piece_set)), "axis_below_minimum", path);
			shape[axis] = spec.axis_maxima[axis];
			require(tet4d::core::validate_live_board_setup(request(mode, shape, piece_set)).ok, "axis maximum must validate");
			shape[axis] = spec.axis_maxima[axis] + 1;
			require_error(tet4d::core::validate_live_board_setup(request(mode, shape, piece_set)), "axis_above_maximum", path);
		}
	}
}

void test_strict_transport_and_atomic_sessions() {
	using tet4d::core::TransportValue;
	TransportValue::Object setup;
	setup.emplace("contract_version", TransportValue(true));
	setup.emplace("mode", TransportValue("live_2d"));
	setup.emplace("board_shape", TransportValue(TransportValue::Array{TransportValue(std::int64_t(6)), TransportValue(std::int64_t(6))}));
	setup.emplace("piece_set_id", TransportValue("classic"));
	setup.emplace("topology_profile", TransportValue(TransportValue::Object{}));
	require_error(tet4d::core::validate_live_board_setup_transport(TransportValue(setup)), "invalid_field_type", "$.contract_version");

	tet4d::core::Plain2DSession session_2d;
	const std::string hash_2d = session_2d.state_hash();
	const std::string snapshot_2d = session_2d.snapshot_json();
	require(!session_2d.configure(3, 6), "invalid 2D configure must fail");
	require(session_2d.state_hash() == hash_2d && session_2d.snapshot_json() == snapshot_2d, "failed 2D configure must be atomic");

	tet4d::core::PlainNDSession session_3d(3);
	const std::string hash_3d = session_3d.state_hash();
	require(!session_3d.configure(tet4d::core::BoardShapeND{{6, 10, 1}}), "invalid 3D configure must fail");
	require(session_3d.state_hash() == hash_3d, "failed 3D configure must be atomic");

	tet4d::core::PlainNDSession session_4d(4);
	const std::string hash_4d = session_4d.state_hash();
	require(!session_4d.configure(tet4d::core::BoardShapeND{{5, 10, 4, 13}}), "invalid 4D configure must fail");
	require(session_4d.state_hash() == hash_4d, "failed 4D configure must be atomic");

	require(!tet4d::core::Plain2DSession::create_validated(3, 6).has_value(), "strict 2D factory must reject invalid shape");
	require(!tet4d::core::PlainNDSession::create_validated(3, {{6, 10, 1}}).has_value(), "strict 3D factory must reject invalid shape");
	require(!tet4d::core::PlainNDSession::create_validated(4, {{5, 10, 4, 13}}).has_value(), "strict 4D factory must reject invalid shape");
	require(!tet4d::core::PlainNDSession::create_validated(4, {{5, 10, 4}}).has_value(), "strict ND factory must reject wrong-rank shape");
}

} // namespace

int main() {
	test_generated_contract_and_valid_presets();
	test_minimum_shapes_and_piece_set_admission();
	test_bounds_topology_and_piece_errors();
	test_every_axis_boundary();
	test_strict_transport_and_atomic_sessions();
	std::cout << "tet4d_core board extent contract tests passed\n";
	return 0;
}
