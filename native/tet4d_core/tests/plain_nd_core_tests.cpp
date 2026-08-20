#include "tet4d_core/plain_nd.hpp"
#include "tet4d_core/plain_nd_session.hpp"
#include "tet4d_core/plain_nd_trace.hpp"
#include "tet4d_core/plain_piece_catalog.hpp"

#include <algorithm>
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

bool same_shape(
		const tet4d::core::PieceShapeND &left,
		const tet4d::core::PieceShapeND &right) {
	return left.name == right.name && left.color_id == right.color_id &&
			left.blocks == right.blocks;
}

void require_nonterminal(
		const tet4d::core::PlainNDSession &session,
		const std::string &context) {
	require(
			session.snapshot_json().find("\"game_over\":false") != std::string::npos,
			context + " must remain nonterminal");
}

void require_production_shape(
		const tet4d::core::PieceShapeND &shape,
		int dimension,
		const std::string &piece_set_id) {
	const std::vector<tet4d::core::PieceShapeND> catalogue =
			tet4d::core::plain_piece_catalog_nd(dimension, piece_set_id);
	const auto match = std::find_if(
			catalogue.begin(),
			catalogue.end(),
			[&shape](const tet4d::core::PieceShapeND &candidate) {
				return same_shape(candidate, shape);
			});
	require(match != catalogue.end(), "ND preview must be an exact production-catalogue shape");
}

void test_production_piece_catalog_registry_is_complete() {
	const auto &catalogs = tet4d::core::production_piece_catalogs_nd();
	require(!catalogs.empty(), "production ND piece-set registry must not be empty");
	std::vector<std::string> seen_catalogs;
	bool saw_3d = false;
	bool saw_4d = false;
	for (const tet4d::core::ProductionPieceSetND &catalog : catalogs) {
		require(catalog.dimension == 3 || catalog.dimension == 4, "production ND catalogue rank must be 3 or 4");
		require(!catalog.piece_set_id.empty() && !catalog.pieces.empty(), "production ND catalogue identity and pieces are required");
		const std::string key = std::to_string(catalog.dimension) + ":" + catalog.piece_set_id;
		require(std::find(seen_catalogs.begin(), seen_catalogs.end(), key) == seen_catalogs.end(), "production ND catalogue keys must be unique");
		seen_catalogs.push_back(key);
		saw_3d = saw_3d || catalog.dimension == 3;
		saw_4d = saw_4d || catalog.dimension == 4;
		const std::vector<tet4d::core::PieceShapeND> selected =
				tet4d::core::plain_piece_catalog_nd(catalog.dimension, catalog.piece_set_id);
		require(selected.size() == catalog.pieces.size(), "session catalogue lookup must consume the enumerated production registry");
		std::vector<std::string> seen_pieces;
		for (std::size_t index = 0; index < catalog.pieces.size(); ++index) {
			const tet4d::core::PieceShapeND &piece = catalog.pieces[index];
			require(same_shape(piece, selected[index]), "enumerated and session production geometry must match exactly");
			require(!piece.name.empty() && !piece.blocks.empty(), "production piece identity and cells are required");
			require(std::find(seen_pieces.begin(), seen_pieces.end(), piece.name) == seen_pieces.end(), "piece identities must be unique within a production set");
			seen_pieces.push_back(piece.name);
			for (const tet4d::core::CoordND &cell : piece.blocks) {
				require(cell.dimension() == catalog.dimension, "production piece cells must retain the catalogue rank");
			}
		}
	}
	require(saw_3d && saw_4d, "production ND registry must enumerate both Live 3D and Live 4D");
}

tet4d::core::PlainGameSetup setup_nd(
		int dimension,
		const std::vector<int> &shape,
		const std::string &piece_set_id,
		int seed = 1337,
		int speed_level = 1,
		const std::string &random_mode = tet4d::core::RANDOM_MODE_FIXED_SEED);

void test_coord_and_board_model() {
	const tet4d::core::CoordND left{{1, 2, 0}};
	const tet4d::core::CoordND right{{1, 2, 1}};
	require(left.dimension() == 3, "CoordND should expose runtime dimension");
	require(left < right, "CoordND should sort lexicographically");

	tet4d::core::BoardShapeND shape{{5, 5, 5}};
	require(shape.is_valid(), "BoardShapeND should validate positive dimensions");
	require(shape.matches(left), "BoardShapeND should match equal-dimension coord");
	require(!shape.matches({{1, 2, 3, 4}}), "BoardShapeND should reject mismatched dimension");

	tet4d::core::BoardND board(shape);
	board.set_cell(left, 8);
	require(board.has_cell(left), "BoardND should report stored locked cells");
	require(board.cells().begin()->first == left, "BoardND should preserve canonical coord sorting");
}

void test_3d_state_stepper() {
	tet4d::core::GameStateND state({{5, 5, 5}}, 1);
	state.active_piece = tet4d::core::ActivePieceND::from_shape(tet4d::core::trace_shape_3d(), {{2, 2, 2}});
	state.post_lock_spawn_shape = tet4d::core::native_i_shape_3d();
	require(state.can_exist(*state.active_piece), "3D initial trace piece should fit");

	const tet4d::core::CommandResultND moved = tet4d::core::GameStepperND::apply(
		state,
		{"move_z", tet4d::core::GameCommandKindND::MoveAxis, 2, 1}
	);
	require(moved.return_value.has_value() && *moved.return_value, "move_axis should return true");
	require(state.active_cells()[0] == tet4d::core::CoordND{{2, 2, 3}}, "move_axis active cell mismatch");

	tet4d::core::GameStepperND::apply(state, {"soft_drop", tet4d::core::GameCommandKindND::SoftDrop, 0, 0});
	require(state.active_cells()[0] == tet4d::core::CoordND{{2, 3, 3}}, "soft_drop active cell mismatch");

	const tet4d::core::CommandResultND dropped = tet4d::core::GameStepperND::apply(
		state,
		{"hard_drop", tet4d::core::GameCommandKindND::HardDrop, 0, 0}
	);
	require(dropped.locked_cell_delta == 2, "hard_drop should lock trace domino");
	require(state.board.has_cell({{2, 4, 3}}), "hard_drop locked 3D cell missing");
	require(state.active_piece.has_value(), "hard_drop should respawn a 3D active piece");
	require(state.active_piece->shape.name == "I3", "3D post-lock shape should be I3");
	require(state.score == 5, "3D lock score should be 5");
}

void test_4d_state_stepper() {
	tet4d::core::GameStateND state({{5, 5, 4, 4}}, 1);
	state.active_piece = tet4d::core::ActivePieceND::from_shape(tet4d::core::trace_shape_4d(), {{2, 2, 1, 1}});
	state.post_lock_spawn_shape = tet4d::core::standard_stair_shape_4d();

	tet4d::core::GameStepperND::apply(state, {"move_w", tet4d::core::GameCommandKindND::MoveAxis, 3, 1});
	tet4d::core::GameStepperND::apply(state, {"soft_drop", tet4d::core::GameCommandKindND::SoftDrop, 0, 0});
	const tet4d::core::CommandResultND dropped = tet4d::core::GameStepperND::apply(
		state,
		{"hard_drop", tet4d::core::GameCommandKindND::HardDrop, 0, 0}
	);
	require(dropped.locked_cell_delta == 2, "4D hard_drop should lock trace domino");
	require(state.board.has_cell({{2, 4, 1, 2}}), "hard_drop locked 4D cell missing");
	require(state.active_piece.has_value(), "hard_drop should respawn a 4D active piece");
	require(state.active_piece->shape.name == "STAIR4", "4D post-lock shape should be STAIR4");
	require(state.active_piece->pos == tet4d::core::CoordND{{1, -2, 1, 1}}, "4D spawn position mismatch");
}

void test_authoritative_hard_drop_destination_nd() {
	for (const int dimension : {3, 4}) {
		const tet4d::core::BoardShapeND board_shape = dimension == 3 ?
			tet4d::core::BoardShapeND{{5, 8, 5}} : tet4d::core::BoardShapeND{{5, 8, 4, 3}};
		tet4d::core::GameStateND state(board_shape, 1);
		const tet4d::core::PieceShapeND shape = dimension == 3 ?
			tet4d::core::trace_shape_3d() : tet4d::core::trace_shape_4d();
		const tet4d::core::CoordND pose = dimension == 3 ?
			tet4d::core::CoordND{{2, 0, 2}} : tet4d::core::CoordND{{2, 0, 1, 1}};
		state.active_piece = tet4d::core::ActivePieceND::from_shape(shape, pose);
		const std::vector<tet4d::core::CoordND> before = state.active_cells();
		const auto destination = state.hard_drop_destination();
		require(destination.has_value(), "ND landing query should return an active destination");
		require(state.active_cells() == before, "ND landing query must not mutate the active pose");
		require(!state.can_exist(destination->moved_axis(1, 1)), "ND queried destination must be maximally dropped");
		require(state.try_move_axis(0, 1), "ND landing fixture lateral move should succeed");
		const auto moved_destination = state.hard_drop_destination();
		require(moved_destination.has_value() && moved_destination->cells() != destination->cells(),
			"ND landing query should follow lateral movement");
		state.try_rotate(0, 2, 1);
		require(state.hard_drop_destination().has_value(), "ND landing query should follow rotation");
		require(state.try_soft_drop(), "ND landing fixture soft drop should succeed");
		require(state.hard_drop_destination().has_value(), "ND landing query should remain valid after soft drop");
		state.active_piece = *destination;
		const std::vector<tet4d::core::CoordND> expected_locked = destination->cells();
		state.hard_drop();
		for (const auto &cell : expected_locked) {
			require(state.board.has_cell(cell), "ND hard drop must lock every queried destination cell");
		}
		state.game_over = true;
		require(!state.hard_drop_destination().has_value(), "terminal ND query should be unavailable");
	}

	for (const auto &setup : {
		setup_nd(3, {8, 16, 8}, "embedded_2d"),
		setup_nd(3, {10, 24, 10}, "native_3d"),
		setup_nd(4, {5, 10, 4, 1}, "embedded_2d"),
		setup_nd(4, {8, 16, 5, 12}, "embedded_3d")}) {
		tet4d::core::PlainNDSession session(setup.mode == "live_4d" ? 4 : 3);
		require(session.configure(setup), "production landing-query setup should configure");
		const std::string hash = session.state_hash();
		const auto next = session.peek_next_piece_shape();
		const auto destination = session.hard_drop_destination();
		require(destination.has_value(), "production piece set should expose landing geometry");
		require(session.state_hash() == hash && same_shape(session.peek_next_piece_shape(), next),
			"ND landing query must preserve state, bag, and RNG");
	}
}

void test_configurable_live_plain_nd_sessions() {
	tet4d::core::PlainNDSession session_3d(3);
	const std::string standard_3d_hash = session_3d.state_hash();
	require(session_3d.configure({{8, 16, 8}}), "supported 3D shape should configure");
	require(session_3d.snapshot_json().find("\"board_shape\":[8,16,8]") != std::string::npos, "configured 3D snapshot shape missing");
	require(session_3d.state_hash() != standard_3d_hash, "3D shape must contribute to state identity");
	session_3d.apply_command("hard_drop");
	session_3d.reset();
	require(session_3d.snapshot_json().find("\"board_shape\":[8,16,8]") != std::string::npos, "3D reset should preserve configured shape");
	require(!session_3d.configure({{8, 16, 8, 1}}), "wrong 3D coordinate count should reject");
	require(!session_3d.configure({{3, 16, 8}}), "3D width below semantic minimum should reject");

	tet4d::core::PlainNDSession session_4d(4);
	const std::string standard_4d_hash = session_4d.state_hash();
	require(session_4d.configure({{8, 16, 5, 8}}), "supported W=8 shape should configure");
	require(session_4d.snapshot_json().find("\"board_shape\":[8,16,5,8]") != std::string::npos, "configured W=8 snapshot shape missing");
	require(session_4d.snapshot_json().find("\"w_slice_count\":8") != std::string::npos, "configured W=8 slice count missing");
	require(session_4d.state_hash() != standard_4d_hash, "4D shape must contribute to state identity");
	session_4d.apply_command("move_w_pos");
	session_4d.apply_command("hard_drop");
	session_4d.reset();
	require(session_4d.snapshot_json().find("\"board_shape\":[8,16,5,8]") != std::string::npos, "4D reset should preserve W=8 shape");
	require(!session_4d.configure({{8, 16, 5, 13}}), "W above safe maximum should reject");
}

tet4d::core::PlainGameSetup setup_nd(
		int dimension,
		const std::vector<int> &shape,
		const std::string &piece_set_id,
		int seed,
		int speed_level,
		const std::string &random_mode) {
	tet4d::core::PlainGameSetup setup;
	setup.mode = dimension == 4 ? "live_4d" : "live_3d";
	setup.board_preset_id = "standard";
	setup.board_shape = shape;
	setup.piece_set_id = piece_set_id;
	setup.random_mode = random_mode;
	setup.configured_seed = seed;
	setup.initial_speed_level = speed_level;
	return setup;
}

void test_stage50_configured_piece_sets_rng_and_restart() {
	tet4d::core::PlainNDSession native_3d(3);
	require(native_3d.configure(setup_nd(3, {6, 10, 6}, "native_3d")), "True 3D setup should configure");
	std::string snapshot = native_3d.snapshot_json();
	require(snapshot.find("\"current_piece\":\"S3\"") != std::string::npos, "True 3D seed 1337 should match Python shuffle");
	require(snapshot.find("\"next_piece\":\"SCREW3\"") != std::string::npos, "True 3D next piece should match Python shuffle");
	const std::string native_3d_hash = native_3d.state_hash();
	native_3d.apply_command("hard_drop");
	native_3d.reset();
	require(native_3d.state_hash() == native_3d_hash, "True 3D restart should restore exact setup and RNG state");

	tet4d::core::PlainNDSession embedded_3d(3);
	require(embedded_3d.configure(setup_nd(3, {8, 16, 8}, "embedded_2d", 2025, 6)), "3D Embedded 2D alternate setup should configure");
	snapshot = embedded_3d.snapshot_json();
	require(snapshot.find("\"piece_set_id\":\"embedded_2d\"") != std::string::npos, "3D embedded setup identity missing");
	require(snapshot.find("\"initial_speed_level\":6") != std::string::npos, "3D embedded speed missing");
	require(embedded_3d.state_hash() != native_3d_hash, "3D piece set/shape/seed/speed must change identity");

	tet4d::core::PlainNDSession standard_4d(4);
	require(standard_4d.configure(setup_nd(4, {5, 10, 4, 4}, "standard_4d_5")), "True 4D setup should configure");
	snapshot = standard_4d.snapshot_json();
	require(snapshot.find("\"current_piece\":\"CORK4\"") != std::string::npos, "True 4D seed 1337 should match Python shuffle");
	require(snapshot.find("\"next_piece\":\"FORK4\"") != std::string::npos, "True 4D next piece should match Python shuffle");
	const std::string standard_4d_hash = standard_4d.state_hash();

	tet4d::core::PlainNDSession embedded_4d_3d(4);
	require(embedded_4d_3d.configure(setup_nd(4, {8, 16, 5, 8}, "embedded_3d", 2025, 8)), "4D Embedded 3D setup should configure");
	require(embedded_4d_3d.snapshot_json().find("\"piece_set_id\":\"embedded_3d\"") != std::string::npos, "4D Embedded 3D identity missing");
	require(embedded_4d_3d.state_hash() != standard_4d_hash, "4D Embedded 3D identity should differ");

	tet4d::core::PlainNDSession embedded_4d_2d(4);
	require(embedded_4d_2d.configure(setup_nd(4, {5, 10, 4, 4}, "embedded_2d")), "4D Embedded 2D setup should configure");
	require(embedded_4d_2d.snapshot_json().find("\"current_piece\":\"Z_E2\"") != std::string::npos, "4D Embedded 2D should use the Python catalog and shuffle");

	tet4d::core::PlainGameSetup invalid = setup_nd(3, {6, 10, 6}, "standard_4d_5");
	require(!native_3d.configure(invalid), "wrong-dimensional piece set must reject");
	invalid = setup_nd(4, {5, 10, 4, 4}, "random_cells_4d");
	require(!standard_4d.configure(invalid), "deferred 4D random-cell set must reject");
	invalid = setup_nd(4, {5, 10, 4, 4}, "standard_4d_5", 1337, 0);
	require(!standard_4d.configure(invalid), "out-of-range ND speed must reject");
}

void test_stage50_nd_true_random_effective_seed() {
	const tet4d::core::PlainGameSetup setup = setup_nd(
		3,
		{6, 10, 6},
		"native_3d",
		1337,
		2,
		tet4d::core::RANDOM_MODE_TRUE_RANDOM
	);
	tet4d::core::PlainNDSession first(3);
	tet4d::core::PlainNDSession second(3);
	require(first.configure(setup), "first ND true-random setup should configure");
	require(second.configure(setup), "second ND true-random setup should configure");
	require(first.snapshot_json().find("\"configured_seed\":null") != std::string::npos, "ND true-random configured seed should be null");
	require(first.state_hash() != second.state_hash(), "explicit new ND true-random construction should change effective seed");
	const std::string initial_hash = first.state_hash();
	first.apply_command("hard_drop");
	first.reset();
	require(first.state_hash() == initial_hash, "ND true-random restart should preserve effective seed");
}

void test_next_piece_preview_is_exact_and_observational() {
	tet4d::core::PlainNDSession session_3d(3);
	require(session_3d.configure(setup_nd(3, {10, 24, 10}, "native_3d")), "large valid 3D board should configure for preview test");
	const std::string hash_3d = session_3d.state_hash();
	const std::string snapshot_3d = session_3d.snapshot_json();
	const std::string status_3d = session_3d.status();
	const tet4d::core::PieceShapeND preview_3d_1 = session_3d.peek_next_piece_shape();
	const tet4d::core::PieceShapeND preview_3d_2 = session_3d.peek_next_piece_shape();
	const tet4d::core::PieceShapeND preview_3d_3 = session_3d.peek_next_piece_shape();
	require(preview_3d_1.name == "SCREW3", "3D preview should match authoritative shuffled queue");
	require(same_shape(preview_3d_1, preview_3d_2) && same_shape(preview_3d_1, preview_3d_3), "three repeated 3D preview queries should be stable");
	require(preview_3d_1.color_id == 7 && preview_3d_1.blocks.size() == 4, "3D preview should expose production color and cells");
	require_production_shape(preview_3d_1, 3, "native_3d");
	require(session_3d.state_hash() == hash_3d && session_3d.snapshot_json() == snapshot_3d && session_3d.status() == status_3d, "3D preview query must be observational");
	session_3d.apply_command("hard_drop");
	require_nonterminal(session_3d, "3D preview-to-spawn advancement");
	require(session_3d.snapshot_json().find("\"current_piece\":\"" + preview_3d_1.name + "\"") != std::string::npos, "3D preview must become the next normally spawned current piece");
	const tet4d::core::PieceShapeND following_3d = session_3d.peek_next_piece_shape();
	require(session_3d.snapshot_json().find("\"next_piece\":\"" + following_3d.name + "\"") != std::string::npos, "3D post-spawn preview must report the following authoritative entry");

	tet4d::core::PlainNDSession embedded_3d(3);
	require(embedded_3d.configure(setup_nd(3, {10, 24, 10}, "embedded_2d")), "embedded 2D-in-3D preview fixture should configure");
	require_production_shape(embedded_3d.peek_next_piece_shape(), 3, "embedded_2d");
	tet4d::core::PlainNDSession embedded_4d(4);
	require(embedded_4d.configure(setup_nd(4, {8, 24, 8, 8}, "embedded_3d")), "embedded 3D-in-4D preview fixture should configure");
	require_production_shape(embedded_4d.peek_next_piece_shape(), 4, "embedded_3d");

	tet4d::core::PlainNDSession session_4d(4);
	require(session_4d.configure(setup_nd(4, {8, 24, 8, 8}, "standard_4d_5")), "large valid 4D board should configure for preview boundary test");
	const tet4d::core::PieceShapeND preview_4d = session_4d.peek_next_piece_shape();
	require(preview_4d.name == "FORK4", "4D preview should match authoritative shuffled queue");
	require(preview_4d.color_id == 7 && preview_4d.blocks.size() == 5, "4D preview should expose production color and five-cell geometry");
	for (const tet4d::core::CoordND &cell : preview_4d.blocks) {
		require(cell.dimension() == 4, "4D preview cells must retain all four canonical coordinates");
	}
	require_production_shape(preview_4d, 4, "standard_4d_5");
	session_4d.apply_command("hard_drop");
	require_nonterminal(session_4d, "4D preview-to-spawn advancement");
	require(session_4d.snapshot_json().find("\"current_piece\":\"" + preview_4d.name + "\"") != std::string::npos, "4D preview must become the next normally spawned current piece");
	const tet4d::core::PieceShapeND following_4d = session_4d.peek_next_piece_shape();
	require(session_4d.snapshot_json().find("\"next_piece\":\"" + following_4d.name + "\"") != std::string::npos, "4D post-spawn preview must report the following authoritative entry");
	for (int draw = 0; draw < 5; ++draw) {
		session_4d.apply_command("hard_drop");
		require_nonterminal(session_4d, "4D refill-boundary hard-drop fixture");
	}
	require(session_4d.snapshot_json().find("\"next_piece\":\"pending_bag\"") != std::string::npos, "4D boundary fixture should preserve pending_bag snapshot semantics");
	const std::string boundary_hash = session_4d.state_hash();
	const std::string boundary_snapshot = session_4d.snapshot_json();
	const std::string boundary_status = session_4d.status();
	const tet4d::core::PieceShapeND refill_preview_1 = session_4d.peek_next_piece_shape();
	const tet4d::core::PieceShapeND refill_preview_2 = session_4d.peek_next_piece_shape();
	const tet4d::core::PieceShapeND refill_preview_3 = session_4d.peek_next_piece_shape();
	require(same_shape(refill_preview_1, refill_preview_2) && same_shape(refill_preview_1, refill_preview_3), "three empty-bag 4D preview queries should be stable");
	require_production_shape(refill_preview_1, 4, "standard_4d_5");
	require(session_4d.state_hash() == boundary_hash, "empty-bag 4D preview must not advance RNG or hash");
	require(session_4d.snapshot_json() == boundary_snapshot, "empty-bag 4D preview must not refill the real bag");
	require(session_4d.status() == boundary_status, "4D preview query must not change command status");
	session_4d.apply_command("hard_drop");
	require_nonterminal(session_4d, "4D refill prediction spawn");
	require(session_4d.snapshot_json().find("\"current_piece\":\"" + refill_preview_1.name + "\"") != std::string::npos, "4D refill preview must equal the next real draw");
	const tet4d::core::PieceShapeND post_refill_preview = session_4d.peek_next_piece_shape();
	require(session_4d.snapshot_json().find("\"next_piece\":\"" + post_refill_preview.name + "\"") != std::string::npos, "4D refill spawn must expose the following authoritative preview");
}

std::string export_stage50_setup_case_nd(const std::string &case_id) {
	tet4d::core::PlainGameSetup setup;
	std::vector<std::string> actions;
	int dimension = 3;
	if (case_id == "setup_plain_3d_embedded_2d") {
		setup = setup_nd(3, {8, 16, 8}, "embedded_2d", 2025, 6);
		setup.board_preset_id = "large";
		actions = {"move_z_pos", "rotate_xz_pos", "soft_drop", "hard_drop"};
	} else if (case_id == "setup_plain_4d_embedded_3d") {
		dimension = 4;
		setup = setup_nd(4, {5, 10, 4, 4}, "embedded_3d", 1337, 4);
		actions = {"move_w_pos", "rotate_xw_pos", "soft_drop", "hard_drop"};
	} else if (case_id == "setup_plain_4d_embedded_2d") {
		dimension = 4;
		setup = setup_nd(4, {5, 10, 4, 4}, "embedded_2d", 2025, 3);
		actions = {"rotate_xy_pos", "hard_drop"};
	} else if (case_id == "setup_plain_4d_wide_true") {
		dimension = 4;
		setup = setup_nd(4, {8, 16, 5, 8}, "standard_4d_5", 42, 8);
		setup.board_preset_id = "wide_w";
		actions = {"move_w_pos", "rotate_xw_pos", "hard_drop"};
	} else {
		return "{}";
	}
	tet4d::core::PlainNDSession session(dimension);
	if (!session.configure(setup)) {
		return "{}";
	}
	const std::string initial_hash = session.state_hash();
	std::ostringstream out;
	out << "{\"case_id\":\"" << case_id << "\",\"frames\":["
		<< "{\"action\":\"initial\",\"snapshot\":" << session.snapshot_json() << "}";
	for (const std::string &action : actions) {
		session.apply_command(action);
		out << ",{\"action\":\"" << action << "\",\"snapshot\":" << session.snapshot_json() << "}";
	}
	const std::string final_hash = session.state_hash();
	session.reset();
	out << "],\"final_hash\":\"" << final_hash << "\""
		<< ",\"restart_hash\":\"" << session.state_hash() << "\""
		<< ",\"restart_matches_initial\":" << (session.state_hash() == initial_hash ? "true" : "false")
		<< ",\"restart_snapshot\":" << session.snapshot_json()
		<< "}";
	return out.str();
}

void test_3d_rotation_stepper() {
	tet4d::core::GameStateND state({{5, 5, 5}}, 1);
	state.active_piece = tet4d::core::ActivePieceND::from_shape(tet4d::core::trace_rotation_shape_3d(), {{2, 2, 2}});

	const tet4d::core::CommandResultND rotated = tet4d::core::GameStepperND::apply(
		state,
		{"rotate_xz_cw", tet4d::core::GameCommandKindND::Rotate, 0, 1, 2}
	);
	require(rotated.return_value.has_value() && *rotated.return_value, "3D rotation should return true");
	require(state.active_piece.has_value(), "3D rotation should keep active piece");
	require(state.active_piece->last_rotation_plane.has_value(), "3D rotation should record plane");
	require((*state.active_piece->last_rotation_plane)[0] == 0, "3D rotation plane axis_a mismatch");
	require((*state.active_piece->last_rotation_plane)[1] == 2, "3D rotation plane axis_b mismatch");
	require(state.active_piece->last_rotation_steps == 1, "3D rotation steps mismatch");
	require(
		state.active_piece->rel_blocks == std::vector<tet4d::core::CoordND>({
			{{0, 0, 1}},
			{{0, 0, 0}},
			{{0, 1, 1}},
			{{1, 0, 1}},
		}),
		"3D rotated rel_blocks should match Python order"
	);
	require(
		state.active_cells() == std::vector<tet4d::core::CoordND>({
			{{2, 2, 2}},
			{{2, 2, 3}},
			{{2, 3, 3}},
			{{3, 2, 3}},
		}),
		"3D rotated active cells should match Python fixture"
	);
}

void test_4d_rotation_stepper() {
	tet4d::core::GameStateND state({{5, 5, 5, 5}}, 1);
	state.active_piece = tet4d::core::ActivePieceND::from_shape(tet4d::core::trace_rotation_shape_4d(), {{2, 2, 2, 2}});

	const tet4d::core::CommandResultND rotated = tet4d::core::GameStepperND::apply(
		state,
		{"rotate_xw_cw", tet4d::core::GameCommandKindND::Rotate, 0, 1, 3}
	);
	require(rotated.return_value.has_value() && *rotated.return_value, "4D rotation should return true");
	require(state.active_piece.has_value(), "4D rotation should keep active piece");
	require(state.active_piece->last_rotation_plane.has_value(), "4D rotation should record plane");
	require((*state.active_piece->last_rotation_plane)[0] == 0, "4D rotation plane axis_a mismatch");
	require((*state.active_piece->last_rotation_plane)[1] == 3, "4D rotation plane axis_b mismatch");
	require(state.active_piece->last_rotation_steps == 1, "4D rotation steps mismatch");
	require(
		state.active_piece->rel_blocks == std::vector<tet4d::core::CoordND>({
			{{0, 0, 0, 0}},
			{{0, 0, 0, -1}},
			{{0, 1, 0, 0}},
			{{0, 0, 1, 0}},
		}),
		"4D rotated rel_blocks should match Python order"
	);
	require(
		state.active_cells() == std::vector<tet4d::core::CoordND>({
			{{2, 2, 2, 1}},
			{{2, 2, 2, 2}},
			{{2, 2, 3, 2}},
			{{2, 3, 2, 2}},
		}),
		"4D rotated active cells should match Python fixture"
	);
}

void test_rotation_rejects_invalid_axes_clearly() {
	tet4d::core::GameStateND state({{5, 5, 5}}, 1);
	state.active_piece = tet4d::core::ActivePieceND::from_shape(tet4d::core::trace_rotation_shape_3d(), {{2, 2, 2}});
	const tet4d::core::CommandResultND rejected = tet4d::core::GameStepperND::apply(
		state,
		{"bad_rotate", tet4d::core::GameCommandKindND::Rotate, 0, 1, 0}
	);
	require(rejected.return_value.has_value() && !*rejected.return_value, "invalid rotation plane should return false");
	require(state.game_over_reason == "invalid_rotation_axis", "invalid rotation should expose a clear reason");
}

void test_3d_plane_clear_stepper() {
	tet4d::core::GameStateND state({{2, 3, 2}}, 1);
	state.active_piece = tet4d::core::ActivePieceND::from_shape(tet4d::core::trace_single_shape_3d(), {{0, 2, 0}});
	state.board.set_cell({{1, 2, 0}}, 1);
	state.board.set_cell({{0, 2, 1}}, 1);
	state.board.set_cell({{1, 2, 1}}, 1);
	state.board.set_cell({{1, 1, 1}}, 2);

	const tet4d::core::CommandResultND locked = tet4d::core::GameStepperND::apply(
		state,
		{"lock_plane_clear", tet4d::core::GameCommandKindND::LockCurrentPiece, 0, 0}
	);
	require(locked.return_int_value.has_value() && *locked.return_int_value == 1, "3D clear should return one cleared plane");
	require(locked.locked_cell_delta == -3, "3D clear locked-cell delta should match Python");
	require(state.lines == 1, "3D clear should increment generic lines counter");
	require(state.score == 45, "3D clear score should be lock points plus single-clear points");
	require(state.board.cells().size() == 1, "3D clear should leave one compacted locked cell");
	require(state.board.has_cell({{1, 2, 1}}), "3D clear should compact surviving cell toward gravity direction");
	require(state.board.cells().at({{1, 2, 1}}) == 2, "3D compacted survivor value mismatch");
	require(state.active_piece.has_value(), "explicit lock_current_piece snapshot should keep active piece like Python");
}

void test_4d_plane_clear_stepper() {
	tet4d::core::GameStateND state({{2, 3, 1, 2}}, 1);
	state.active_piece = tet4d::core::ActivePieceND::from_shape(tet4d::core::trace_single_shape_4d(), {{0, 2, 0, 0}});
	state.board.set_cell({{1, 2, 0, 0}}, 1);
	state.board.set_cell({{0, 2, 0, 1}}, 1);
	state.board.set_cell({{1, 2, 0, 1}}, 1);
	state.board.set_cell({{1, 1, 0, 1}}, 2);

	const tet4d::core::CommandResultND locked = tet4d::core::GameStepperND::apply(
		state,
		{"lock_hyperplane_clear", tet4d::core::GameCommandKindND::LockCurrentPiece, 0, 0}
	);
	require(locked.return_int_value.has_value() && *locked.return_int_value == 1, "4D clear should return one cleared hyperplane");
	require(locked.locked_cell_delta == -3, "4D clear locked-cell delta should match Python");
	require(state.lines == 1, "4D clear should increment generic lines counter");
	require(state.score == 45, "4D clear score should be lock points plus single-clear points");
	require(state.board.cells().size() == 1, "4D clear should leave one compacted locked cell");
	require(state.board.has_cell({{1, 2, 0, 1}}), "4D clear should compact surviving cell toward gravity direction");
	require(state.board.cells().at({{1, 2, 0, 1}}) == 2, "4D compacted survivor value mismatch");
	require(state.active_piece.has_value(), "explicit 4D lock_current_piece snapshot should keep active piece like Python");
}

void test_3d_spawn_blocked_stepper() {
	tet4d::core::GameStateND state({{5, 5, 5}}, 1);
	state.post_lock_spawn_shape = tet4d::core::trace_spawn_blocked_shape_3d();
	state.board.set_cell({{2, 0, 2}}, 9);
	require(!state.active_piece.has_value(), "3D spawn-blocked fixture starts without active piece");

	const tet4d::core::CommandResultND spawned = tet4d::core::GameStepperND::apply(
		state,
		{"spawn_blocked", tet4d::core::GameCommandKindND::SpawnNewPiece, 0, 0}
	);
	require(!spawned.return_value.has_value(), "spawn_new_piece should return null like Python trace export");
	require(spawned.locked_cell_delta == 0, "3D blocked spawn should not mutate locked cells");
	require(state.game_over, "3D blocked spawn should set game_over");
	require(state.game_over_reason == "spawn_blocked", "3D blocked spawn reason mismatch");
	require(state.active_piece.has_value(), "3D blocked spawn should keep the rejected active piece");
	require(state.active_piece->shape.name == "TRACE_3D_NEXT", "3D blocked spawn shape mismatch");
	require(state.active_piece->shape.color_id == 7, "3D blocked spawn color mismatch");
	require(state.active_piece->pos == tet4d::core::CoordND{{2, -2, 2}}, "3D blocked spawn position mismatch");
	require(
		state.active_cells() == std::vector<tet4d::core::CoordND>({
			{{2, -2, 2}},
			{{2, 0, 2}},
		}),
		"3D blocked spawn active cells should match Python"
	);
	require(state.board.cells().size() == 1, "3D blocked spawn locked cell count mismatch");
	require(state.board.has_cell({{2, 0, 2}}), "3D blocked spawn should preserve blocking locked cell");
	require(state.board.cells().at({{2, 0, 2}}) == 9, "3D blocked spawn locked cell value mismatch");
}

void test_4d_spawn_blocked_stepper() {
	tet4d::core::GameStateND state({{5, 5, 5, 5}}, 1);
	state.post_lock_spawn_shape = tet4d::core::trace_spawn_blocked_shape_4d();
	state.board.set_cell({{2, 0, 2, 2}}, 9);
	require(!state.active_piece.has_value(), "4D spawn-blocked fixture starts without active piece");

	const tet4d::core::CommandResultND spawned = tet4d::core::GameStepperND::apply(
		state,
		{"spawn_blocked", tet4d::core::GameCommandKindND::SpawnNewPiece, 0, 0}
	);
	require(!spawned.return_value.has_value(), "4D spawn_new_piece should return null like Python trace export");
	require(spawned.locked_cell_delta == 0, "4D blocked spawn should not mutate locked cells");
	require(state.game_over, "4D blocked spawn should set game_over");
	require(state.game_over_reason == "spawn_blocked", "4D blocked spawn reason mismatch");
	require(state.active_piece.has_value(), "4D blocked spawn should keep the rejected active piece");
	require(state.active_piece->shape.name == "TRACE_4D_NEXT", "4D blocked spawn shape mismatch");
	require(state.active_piece->shape.color_id == 7, "4D blocked spawn color mismatch");
	require(state.active_piece->pos == tet4d::core::CoordND{{2, -2, 2, 2}}, "4D blocked spawn position mismatch");
	require(
		state.active_cells() == std::vector<tet4d::core::CoordND>({
			{{2, -2, 2, 2}},
			{{2, 0, 2, 2}},
		}),
		"4D blocked spawn active cells should match Python"
	);
	require(state.board.cells().size() == 1, "4D blocked spawn locked cell count mismatch");
	require(state.board.has_cell({{2, 0, 2, 2}}), "4D blocked spawn should preserve blocking locked cell");
	require(state.board.cells().at({{2, 0, 2, 2}}) == 9, "4D blocked spawn locked cell value mismatch");
}

void test_trace_exports() {
	const std::vector<std::string> cases = tet4d::core::list_plain_nd_parity_cases();
	require(cases.size() == 10, "plain ND parity should include Stage 49 configurable cases");
	for (const std::string &expected : {
			"gameplay_plain_3d_short",
			"gameplay_plain_4d_short",
			"gameplay_plain_3d_rotation_short",
			"gameplay_plain_4d_rotation_short",
			"gameplay_plain_3d_plane_clear_short",
			"gameplay_plain_4d_plane_clear_short",
			"gameplay_plain_3d_spawn_blocked_game_over",
			"gameplay_plain_4d_spawn_blocked_game_over",
			"gameplay_plain_3d_configurable",
			"gameplay_plain_4d_configurable_w8",
		}) {
		require(std::find(cases.begin(), cases.end(), expected) != cases.end(), "missing ND parity case: " + expected);
	}
	require(tet4d::core::run_builtin_plain_nd_smoke_case(), "plain ND smoke API should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_short"), "3D required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_short"), "4D required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_rotation_short"), "3D rotation required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_rotation_short"), "4D rotation required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_plane_clear_short"), "3D clear required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_plane_clear_short"), "4D clear required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_spawn_blocked_game_over"), "3D spawn-blocked required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_spawn_blocked_game_over"), "4D spawn-blocked required fields should pass");

	const std::string trace_3d = tet4d::core::export_plain_nd_trace_json("gameplay_plain_3d_short");
	require(trace_3d.find("\"dimension\":3") != std::string::npos, "3D trace dimension missing");
	require(trace_3d.find("\"state_hash\":\"9e183b178d0badec86b59a833782702d581b13a72d75bddeeda7f88333826dd7\"") != std::string::npos, "3D final hash missing");
	require(trace_3d.find("\"locked_cell_digest\":\"4b7a6b700d15a928dd23c2a187403358cb3dcf1fd03c8855559d26663d6ded1d\"") != std::string::npos, "3D locked digest missing");

	const std::string trace_4d = tet4d::core::export_plain_nd_trace_json("gameplay_plain_4d_short");
	require(trace_4d.find("\"dimension\":4") != std::string::npos, "4D trace dimension missing");
	require(trace_4d.find("\"state_hash\":\"d34d21da0a1c4aa6e947230e68e8b16a3e212b40bb7da1ccaef24200e7f80449\"") != std::string::npos, "4D final hash missing");
	require(trace_4d.find("\"locked_cell_digest\":\"49a3a8a0dffab41bfaaf4c5dc3210d2d50de7f52d9891f4a2ec812d645114463\"") != std::string::npos, "4D locked digest missing");

	const std::string trace_3d_rotation = tet4d::core::export_plain_nd_trace_json("gameplay_plain_3d_rotation_short");
	require(trace_3d_rotation.find("\"last_rotation_plane\":[0,2]") != std::string::npos, "3D rotation plane missing");
	require(trace_3d_rotation.find("\"last_rotation_steps\":1") != std::string::npos, "3D rotation steps missing");
	require(trace_3d_rotation.find("\"state_hash\":\"2d2ada3b5b425bf649c66cd8e6b2c3c2e24a57c4f8a7dc8aab26ac72a33a7e4d\"") != std::string::npos, "3D rotation final hash missing");
	require(trace_3d_rotation.find("\"state_hash\":\"6e9736bfeeff1119a014150e839556f02743b5ae6dcd10309dbd57d61370cee1\"") != std::string::npos, "3D rotation frame hash missing");

	const std::string trace_4d_rotation = tet4d::core::export_plain_nd_trace_json("gameplay_plain_4d_rotation_short");
	require(trace_4d_rotation.find("\"last_rotation_plane\":[0,3]") != std::string::npos, "4D rotation plane missing");
	require(trace_4d_rotation.find("\"last_rotation_steps\":1") != std::string::npos, "4D rotation steps missing");
	require(trace_4d_rotation.find("\"state_hash\":\"c3ccf55ccbac1998e7973ba4dc5e163398f2e32a6999cc933a3e4065dd71d34c\"") != std::string::npos, "4D rotation final hash missing");
	require(trace_4d_rotation.find("\"state_hash\":\"0910d159c061826ae492aca543c28bae8d7a8d7ca430282afa7de23e62cbdcc0\"") != std::string::npos, "4D rotation frame hash missing");

	const std::string trace_3d_clear = tet4d::core::export_plain_nd_trace_json("gameplay_plain_3d_plane_clear_short");
	require(trace_3d_clear.find("\"lines\":1") != std::string::npos, "3D clear lines missing");
	require(trace_3d_clear.find("\"score\":45") != std::string::npos, "3D clear score missing");
	require(trace_3d_clear.find("\"locked_cell_delta\":-3") != std::string::npos, "3D clear locked-cell delta missing");
	require(trace_3d_clear.find("\"locked_cell_digest\":\"5e9f3e56cd4891c7e96d954d52ed20072b2a62d12ac347db608cf8f630d4bd8b\"") != std::string::npos, "3D clear locked digest missing");
	require(trace_3d_clear.find("\"state_hash\":\"9c1737872582996818277166c9b8d900a2362868315f15d1a8f9338e7afa6d57\"") != std::string::npos, "3D clear final hash missing");
	require(trace_3d_clear.find("\"state_hash\":\"40af964de14050ef5d068e95d559385a6880450998b76d230da5450b7e2528d3\"") != std::string::npos, "3D clear frame hash missing");

	const std::string trace_4d_clear = tet4d::core::export_plain_nd_trace_json("gameplay_plain_4d_plane_clear_short");
	require(trace_4d_clear.find("\"lines\":1") != std::string::npos, "4D clear lines missing");
	require(trace_4d_clear.find("\"score\":45") != std::string::npos, "4D clear score missing");
	require(trace_4d_clear.find("\"locked_cell_delta\":-3") != std::string::npos, "4D clear locked-cell delta missing");
	require(trace_4d_clear.find("\"locked_cell_digest\":\"06d0e35d7aea4e8c938561bdda9e42e377b77b3a09281e7ffdfd03e30e84fb4b\"") != std::string::npos, "4D clear locked digest missing");
	require(trace_4d_clear.find("\"state_hash\":\"7b18f81b698dd0638fc1a11db4a896273f6d3bf3e5e31ded6241af3b6d1bee1f\"") != std::string::npos, "4D clear final hash missing");
	require(trace_4d_clear.find("\"state_hash\":\"6a6506b6f88f177570acac30881d5e17d6cbbc24a86143a22018a4e1164fec2b\"") != std::string::npos, "4D clear frame hash missing");

	const std::string trace_3d_spawn_blocked = tet4d::core::export_plain_nd_trace_json("gameplay_plain_3d_spawn_blocked_game_over");
	require(trace_3d_spawn_blocked.find("\"game_over\":true") != std::string::npos, "3D spawn-blocked game_over missing");
	require(trace_3d_spawn_blocked.find("\"shape\":\"TRACE_3D_NEXT\"") != std::string::npos, "3D spawn-blocked shape missing");
	require(trace_3d_spawn_blocked.find("\"pos\":[2,-2,2]") != std::string::npos, "3D spawn-blocked position missing");
	require(trace_3d_spawn_blocked.find("\"cells\":[[2,-2,2],[2,0,2]]") != std::string::npos, "3D spawn-blocked active cells missing");
	require(trace_3d_spawn_blocked.find("\"locked_cell_delta\":0") != std::string::npos, "3D spawn-blocked locked delta missing");
	require(trace_3d_spawn_blocked.find("\"soft_drop_legal_after\":true") != std::string::npos, "3D spawn-blocked soft-drop status missing");
	require(trace_3d_spawn_blocked.find("\"locked_cell_digest\":\"79dc09f39b5262ff1799fcca6103cf58a19393a8a08595aedbc926820a1e086b\"") != std::string::npos, "3D spawn-blocked locked digest missing");
	require(trace_3d_spawn_blocked.find("\"state_hash\":\"a950c1badd7dd47dda27d140b7aef5097e9331a890c145419076f1e938317619\"") != std::string::npos, "3D spawn-blocked final hash missing");
	require(trace_3d_spawn_blocked.find("\"state_hash\":\"3d0edddb4835421ecc60f681144bed191d90081b69bf7746d3bd6fb601310cef\"") != std::string::npos, "3D spawn-blocked frame hash missing");

	const std::string trace_4d_spawn_blocked = tet4d::core::export_plain_nd_trace_json("gameplay_plain_4d_spawn_blocked_game_over");
	require(trace_4d_spawn_blocked.find("\"game_over\":true") != std::string::npos, "4D spawn-blocked game_over missing");
	require(trace_4d_spawn_blocked.find("\"shape\":\"TRACE_4D_NEXT\"") != std::string::npos, "4D spawn-blocked shape missing");
	require(trace_4d_spawn_blocked.find("\"pos\":[2,-2,2,2]") != std::string::npos, "4D spawn-blocked position missing");
	require(trace_4d_spawn_blocked.find("\"cells\":[[2,-2,2,2],[2,0,2,2]]") != std::string::npos, "4D spawn-blocked active cells missing");
	require(trace_4d_spawn_blocked.find("\"locked_cell_delta\":0") != std::string::npos, "4D spawn-blocked locked delta missing");
	require(trace_4d_spawn_blocked.find("\"soft_drop_legal_after\":true") != std::string::npos, "4D spawn-blocked soft-drop status missing");
	require(trace_4d_spawn_blocked.find("\"locked_cell_digest\":\"3bdf132722194fb8c15892d5f679a439d6802c53803b2d7d15a1024d5b0c6031\"") != std::string::npos, "4D spawn-blocked locked digest missing");
	require(trace_4d_spawn_blocked.find("\"state_hash\":\"ee8f825bce34feb8fa7f9bdd15157f699bba9c34a650a582de6a6a3ee81d8ad6\"") != std::string::npos, "4D spawn-blocked final hash missing");
	require(trace_4d_spawn_blocked.find("\"state_hash\":\"5a1262677f381cba918b8b3da7e73eb21f12c2fb5728cc2f7f02ea90142a7fdd\"") != std::string::npos, "4D spawn-blocked frame hash missing");

	const std::string unsupported = tet4d::core::export_plain_nd_trace_json("gameplay_plain_nd_rotation_deferred");
	require(unsupported.find("\"error\":\"unsupported plain ND parity case\"") != std::string::npos, "unsupported ND trace case should fail clearly");
}

void test_live_plain_3d_session() {
	tet4d::core::PlainNDSession session(3);
	const std::string initial_hash = session.state_hash();
	const std::string initial_snapshot = session.snapshot_json();
	require(initial_snapshot.find("\"trace_type\":\"live_3d\"") != std::string::npos, "live 3D snapshot trace type missing");
	require(initial_snapshot.find("\"case_id\":\"live_plain_3d\"") != std::string::npos, "live 3D snapshot case id missing");
	require(initial_snapshot.find("\"dimension\":3") != std::string::npos, "live 3D snapshot dimension missing");
	require(initial_snapshot.find("\"board_shape\":[6,10,6]") != std::string::npos, "live 3D board shape missing");
	require(initial_snapshot.find("\"current_piece\":\"I3\"") != std::string::npos, "live 3D initial piece missing");
	require(initial_snapshot.find("\"next_piece\":\"O3\"") != std::string::npos, "live 3D next piece missing");
	require(initial_snapshot.find("\"state_hash\":\"" + initial_hash + "\"") != std::string::npos, "live 3D snapshot hash mismatch");

	session.apply_command("move_x_pos");
	require(session.state_hash() != initial_hash, "live 3D move X should change hash");
	require(session.status().find("last_command=move_x_pos") != std::string::npos, "live 3D move X status missing");
	const std::string after_x_hash = session.state_hash();
	session.apply_command("move_z_pos");
	require(session.state_hash() != after_x_hash, "live 3D move Z should change hash");
	require(session.status().find("last_command=move_z_pos") != std::string::npos, "live 3D move Z status missing");

	tet4d::core::PlainNDSession rotate_xy_session(3);
	const std::string before_xy = rotate_xy_session.state_hash();
	rotate_xy_session.apply_command("rotate_xy_pos");
	require(rotate_xy_session.status().find("last_command=rotate_xy_pos") != std::string::npos, "live 3D rotate XY status missing");
	require(rotate_xy_session.snapshot_json().find("\"last_rotation_plane\":\"XY\"") != std::string::npos, "live 3D rotate XY plane missing");
	require(rotate_xy_session.state_hash() != before_xy, "live 3D rotate XY should change hash");
	tet4d::core::PlainNDSession rotate_xz_session(3);
	rotate_xz_session.apply_command("rotate_xz_pos");
	require(rotate_xz_session.status().find("last_command=rotate_xz_pos") != std::string::npos, "live 3D rotate XZ status missing");
	require(rotate_xz_session.snapshot_json().find("\"last_rotation_plane\":\"XZ\"") != std::string::npos, "live 3D rotate XZ plane missing");
	tet4d::core::PlainNDSession rotate_yz_session(3);
	rotate_yz_session.apply_command("rotate_yz_pos");
	require(rotate_yz_session.status().find("last_command=rotate_yz_pos") != std::string::npos, "live 3D rotate YZ status missing");
	require(rotate_yz_session.snapshot_json().find("\"last_rotation_plane\":\"YZ\"") != std::string::npos, "live 3D rotate YZ plane missing");

	const std::string before_soft = session.state_hash();
	session.apply_command("soft_drop");
	require(session.state_hash() != before_soft, "live 3D soft drop should change hash");
	session.tick();
	require(session.status().find("last_command=tick") != std::string::npos, "live 3D tick status missing");

	session.apply_command("hard_drop");
	const std::string after_hard_drop = session.snapshot_json();
	require(after_hard_drop.find("\"score\":5") != std::string::npos, "live 3D hard drop should score lock points");
	require(after_hard_drop.find("\"locked_cells\":[") != std::string::npos, "live 3D hard drop should expose locked cells");
	require(after_hard_drop.find("\"current_piece\":\"O3\"") != std::string::npos, "live 3D hard drop should spawn deterministic next piece");
	require(session.status().find("next_piece=L3") != std::string::npos, "live 3D status should expose following piece");

	session.reset();
	require(session.state_hash() == initial_hash, "live 3D reset should restore initial hash");
	require(session.snapshot_json().find("\"game_over\":false") != std::string::npos, "live 3D reset should clear game_over");
}

void test_live_plain_4d_session() {
	tet4d::core::PlainNDSession session(4);
	const std::string initial_hash = session.state_hash();
	const std::string initial_snapshot = session.snapshot_json();
	require(initial_snapshot.find("\"trace_type\":\"live_4d\"") != std::string::npos, "live 4D snapshot trace type missing");
	require(initial_snapshot.find("\"case_id\":\"live_plain_4d\"") != std::string::npos, "live 4D snapshot case id missing");
	require(initial_snapshot.find("\"dimension\":4") != std::string::npos, "live 4D snapshot dimension missing");
	require(initial_snapshot.find("\"board_shape\":[5,10,4,4]") != std::string::npos, "live 4D board shape missing");
	require(initial_snapshot.find("\"w_slice_count\":4") != std::string::npos, "live 4D W slice count missing");
	require(initial_snapshot.find("\"current_piece\":\"TRACE_4D\"") != std::string::npos, "live 4D initial piece missing");
	require(initial_snapshot.find("\"next_piece\":\"STAIR4\"") != std::string::npos, "live 4D next piece missing");
	require(initial_snapshot.find("\"state_hash\":\"" + initial_hash + "\"") != std::string::npos, "live 4D snapshot hash mismatch");

	session.apply_command("move_w_pos");
	require(session.state_hash() != initial_hash, "live 4D W move should change hash");
	require(session.status().find("last_command=move_w_pos") != std::string::npos, "live 4D W move status missing");
	require(session.snapshot_json().find("\"active_w\":2") != std::string::npos, "live 4D W move active slice missing");

	tet4d::core::PlainNDSession rotate_xw_session(4);
	rotate_xw_session.apply_command("rotate_xw_pos");
	require(rotate_xw_session.status().find("last_command=rotate_xw_pos") != std::string::npos, "live 4D rotate XW status missing");
	require(rotate_xw_session.snapshot_json().find("\"last_rotation_plane\":\"XW\"") != std::string::npos, "live 4D rotate XW plane missing");
	tet4d::core::PlainNDSession rotate_yw_session(4);
	rotate_yw_session.apply_command("rotate_yw_pos");
	require(rotate_yw_session.status().find("last_command=rotate_yw_pos") != std::string::npos, "live 4D rotate YW status missing");
	require(rotate_yw_session.snapshot_json().find("\"last_rotation_plane\":\"YW\"") != std::string::npos, "live 4D rotate YW plane missing");
	tet4d::core::PlainNDSession rotate_zw_session(4);
	rotate_zw_session.apply_command("rotate_zw_pos");
	require(rotate_zw_session.status().find("last_command=rotate_zw_pos") != std::string::npos, "live 4D rotate ZW status missing");
	require(rotate_zw_session.snapshot_json().find("\"last_rotation_plane\":\"ZW\"") != std::string::npos, "live 4D rotate ZW plane missing");

	const std::string before_soft = session.state_hash();
	session.apply_command("soft_drop");
	require(session.state_hash() != before_soft, "live 4D soft drop should change hash");
	session.tick();
	require(session.status().find("last_command=tick") != std::string::npos, "live 4D tick status missing");

	session.apply_command("hard_drop");
	const std::string after_hard_drop = session.snapshot_json();
	require(after_hard_drop.find("\"score\":5") != std::string::npos, "live 4D hard drop should score lock points");
	require(after_hard_drop.find("\"locked_cells\":[") != std::string::npos, "live 4D hard drop should expose locked cells");
	require(after_hard_drop.find("\"current_piece\":\"STAIR4\"") != std::string::npos, "live 4D hard drop should spawn deterministic next piece");
	require(session.status().find("next_piece=") != std::string::npos, "live 4D status should expose following piece");

	session.reset();
	require(session.state_hash() == initial_hash, "live 4D reset should restore initial hash");
	require(session.snapshot_json().find("\"game_over\":false") != std::string::npos, "live 4D reset should clear game_over");
}

} // namespace

int main(int argc, char **argv) {
	if (argc >= 2 && std::string(argv[1]) == "--export-plain-nd-trace") {
		const std::string case_id = argc >= 3 ? std::string(argv[2]) : "gameplay_plain_3d_short";
		std::cout << tet4d::core::export_plain_nd_trace_json(case_id) << "\n";
		return 0;
	}
	if (argc >= 2 && std::string(argv[1]) == "--export-plain-setup") {
		const std::string case_id = argc >= 3 ? std::string(argv[2]) : "setup_plain_3d_embedded_2d";
		std::cout << export_stage50_setup_case_nd(case_id) << "\n";
		return 0;
	}
	test_coord_and_board_model();
	test_production_piece_catalog_registry_is_complete();
	test_3d_state_stepper();
	test_4d_state_stepper();
	test_authoritative_hard_drop_destination_nd();
	test_configurable_live_plain_nd_sessions();
	test_stage50_configured_piece_sets_rng_and_restart();
	test_stage50_nd_true_random_effective_seed();
	test_next_piece_preview_is_exact_and_observational();
	test_3d_rotation_stepper();
	test_4d_rotation_stepper();
	test_rotation_rejects_invalid_axes_clearly();
	test_3d_plane_clear_stepper();
	test_4d_plane_clear_stepper();
	test_3d_spawn_blocked_stepper();
	test_4d_spawn_blocked_stepper();
	test_trace_exports();
	test_live_plain_3d_session();
	test_live_plain_4d_session();
	std::cout << "tet4d_core native plain ND tests passed\n";
	return 0;
}
