#include "tet4d_core/core_api.hpp"
#include "tet4d_core/plain_2d.hpp"
#include "tet4d_core/plain_2d_session.hpp"
#include "tet4d_core/plain_piece_catalog.hpp"
#include "tet4d_core/sha256.hpp"

#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string_view>
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
		const tet4d::core::PieceShape2D &left,
		const tet4d::core::PieceShape2D &right) {
	return left.name == right.name && left.color_id == right.color_id &&
			left.blocks == right.blocks;
}

void require_nonterminal(
		const tet4d::core::Plain2DSession &session,
		const std::string &context) {
	require(
			session.snapshot_json().find("\"game_over\":false") != std::string::npos,
			context + " must remain nonterminal");
}

void require_production_shape(const tet4d::core::PieceShape2D &shape) {
	const std::vector<tet4d::core::PieceShape2D> &catalogue =
			tet4d::core::plain_piece_catalog_2d("classic");
	const auto match = std::find_if(
			catalogue.begin(),
			catalogue.end(),
			[&shape](const tet4d::core::PieceShape2D &candidate) {
				return same_shape(candidate, shape);
			});
	require(match != catalogue.end(), "2D preview must be an exact production-catalogue shape");
}

void test_stable_hash_pilot() {
	const std::vector<std::string> inputs = {
		"",
		"tet4d",
		"oracle-check",
		"hash-bridge",
	};
	std::cout << "{\n  \"cases\": [\n";
	for (std::size_t index = 0; index < inputs.size(); ++index) {
		const std::string &input = inputs[index];
		std::cout << "    {\"input\":\"" << input << "\",\"native_hash\":\""
		          << tet4d::core::stable_hash_text(input) << "\"}";
		if (index + 1 < inputs.size()) {
			std::cout << ",";
		}
		std::cout << "\n";
	}
	std::cout << "  ]\n}\n";
}

void test_board_and_piece_cells() {
	tet4d::core::GameState2D state = tet4d::core::make_builtin_plain_2d_initial_state();
	const std::vector<tet4d::core::Coord2D> cells = state.active_cells();
	require(cells.size() == 2, "initial active piece should have two cells");
	require(cells[0] == tet4d::core::Coord2D{2, 3}, "initial first cell mismatch");
	require(cells[1] == tet4d::core::Coord2D{3, 3}, "initial second cell mismatch");
	require(state.can_exist(*state.active_piece), "initial active piece should fit");
}

void test_command_replay() {
	tet4d::core::GameState2D state = tet4d::core::make_builtin_plain_2d_initial_state();
	const std::vector<tet4d::core::GameCommand2D> commands = tet4d::core::builtin_plain_2d_commands();

	tet4d::core::CommandResult2D first = tet4d::core::GameStepper2D::apply(state, commands[0]);
	require(first.return_value.has_value() && *first.return_value, "move_right should return true");
	require(state.active_cells()[0] == tet4d::core::Coord2D{3, 3}, "move_right first cell mismatch");

	tet4d::core::CommandResult2D second = tet4d::core::GameStepper2D::apply(state, commands[1]);
	require(second.return_value.has_value() && *second.return_value, "soft_drop should return true");
	require(state.active_cells()[0] == tet4d::core::Coord2D{3, 4}, "soft_drop first cell mismatch");

	tet4d::core::CommandResult2D third = tet4d::core::GameStepper2D::apply(state, commands[2]);
	require(!third.return_value.has_value(), "hard_drop should return null");
	require(third.locked_cell_delta == 2, "hard_drop should lock two cells");
	require(state.board.has_cell({3, 5}), "locked cell (3,5) missing");
	require(state.board.has_cell({4, 5}), "locked cell (4,5) missing");
	require(state.score == 5, "final score should be 5");
	require(state.active_piece.has_value(), "hard_drop should respawn active piece");
	require(state.active_piece->shape.name == "I", "respawned shape should be I");
	require(state.active_piece->pos == tet4d::core::Coord2D{2, -2}, "respawn position mismatch");
}

void test_authoritative_hard_drop_destination_2d() {
	tet4d::core::GameState2D state(6, 8);
	state.active_piece = tet4d::core::ActivePiece2D{
		tet4d::core::trace_t_shape_2d(), {2, 0}, 0};
	state.board.set_cell({2, 6}, 8);
	const std::vector<tet4d::core::Coord2D> before = state.active_cells();
	const auto destination = state.hard_drop_destination();
	require(destination.has_value(), "2D landing query should return an active destination");
	require(state.active_cells() == before, "2D landing query must not mutate the active pose");
	require(!state.can_exist(destination->moved(0, 1)), "2D queried destination must be maximally dropped");
	require(state.try_move(1, 0), "2D landing fixture lateral move should succeed");
	const auto moved_destination = state.hard_drop_destination();
	require(moved_destination.has_value() && moved_destination->cells() != destination->cells(),
		"2D landing query should follow lateral movement");
	state.try_rotate(1);
	require(state.hard_drop_destination().has_value(), "2D landing query should follow accepted rotation");
	require(state.try_soft_drop(), "2D landing fixture soft drop should succeed");
	require(state.hard_drop_destination().has_value(), "2D landing query should remain valid after soft drop");
	state.active_piece = *destination;
	const std::vector<tet4d::core::Coord2D> expected_locked = destination->cells();
	state.hard_drop();
	for (const auto &cell : expected_locked) {
		require(state.board.has_cell(cell), "2D hard drop must lock every queried destination cell");
	}

	tet4d::core::GameState2D landed(4, 4);
	landed.active_piece = tet4d::core::ActivePiece2D{
		tet4d::core::trace_dot_shape_2d(), {1, 3}, 0};
	const auto coincident = landed.hard_drop_destination();
	require(coincident.has_value() && coincident->cells() == landed.active_cells(),
		"already-landed 2D query should return the unchanged pose");
	landed.game_over = true;
	require(!landed.hard_drop_destination().has_value(), "terminal 2D query should be unavailable");

	tet4d::core::Plain2DSession session;
	const std::string hash = session.state_hash();
	const auto preview = session.peek_next_piece_shape();
	require(session.hard_drop_destination().has_value(), "live 2D session should expose landing geometry");
	require(session.state_hash() == hash && same_shape(session.peek_next_piece_shape(), preview),
		"live 2D landing queries must preserve state, bag, and RNG");
}

void test_trace_export_smoke() {
	const std::string trace = tet4d::core::export_plain_2d_trace_json();
	require(trace.find("\"case_id\":\"gameplay_plain_2d_short\"") != std::string::npos, "trace case id missing");
	require(trace.find("\"locked_cell_digest\":\"fb9ba70f4dd66a15981efdb41ff9afc393df725af09c9d338143ff8fa2164b5b\"") != std::string::npos, "final locked digest missing");
	require(trace.find("\"state_hash\":\"d02e1823a320d5a4c3203a3cb6d103518c5f5168a67f2ebffc193c23a0e80ced\"") != std::string::npos, "frame 0 state hash missing");
	require(trace.find("\"state_hash\":\"1f07ea939bcd495c97b21501b14fe1cd7a4e44b73e4ad4fad14dfd0ddb381847\"") != std::string::npos, "frame 1 state hash missing");
	require(trace.find("\"state_hash\":\"f1eed6ec35fc8d5aae39ededd81df9eff3bb9148b9def9c8b0d7e5b8e1d59e5a\"") != std::string::npos, "frame 2 state hash missing");
	require(trace.find("\"state_hash\":\"2d3a6eb2744d46bc147ae7d21855036e1ff241a99261ab5324b20958ec353139\"") != std::string::npos, "final state hash missing");
	require(tet4d::core::run_builtin_plain_2d_smoke_case(), "plain 2D smoke API should pass");
	require(tet4d::core::get_plain_2d_required_field_parity(), "required field parity API should pass");
	require(tet4d::core::sha256_hex("tet4d") == "512f04b84d4f239afca4c01d057bafa4fe3a8df37cfe355da2458cbedf3ff821", "sha256 smoke mismatch");
}

void test_stage11_trace_exports() {
	const std::vector<std::string> cases = tet4d::core::list_plain_2d_parity_cases();
	require(cases.size() == 5, "plain 2D parity should include the Stage 49 configurable case");
	for (const std::string &case_id : cases) {
		const std::string trace = tet4d::core::export_plain_2d_trace_json(case_id);
		require(trace.find("\"case_id\":\"" + case_id + "\"") != std::string::npos, "Stage 11 trace case id missing");
		require(trace.find("\"state_hash\"") != std::string::npos, "Stage 11 trace hash missing");
		require(tet4d::core::get_plain_2d_required_field_parity(case_id), "Stage 11 required field parity API should pass");
	}
	require(
		tet4d::core::export_plain_2d_trace_json("gameplay_plain_2d_rotation_short").find("\"rotation\":1") != std::string::npos,
		"rotation trace should record rotation=1"
	);
	require(
		tet4d::core::export_plain_2d_trace_json("gameplay_plain_2d_line_clear_short").find("\"lines\":1") != std::string::npos,
		"line clear trace should record one cleared line"
	);
}

void test_live_plain_2d_session() {
	tet4d::core::Plain2DSession session;
	const std::string initial_hash = session.state_hash();
	std::string snapshot = session.snapshot_json();
	require(snapshot.find("\"trace_type\":\"live_2d\"") != std::string::npos, "live session snapshot should be renderer-shaped");
	require(snapshot.find("\"case_id\":\"live_plain_2d\"") != std::string::npos, "live session case id missing");
	require(snapshot.find("\"active_cells\"") != std::string::npos, "live session active cells missing");
	require(snapshot.find("\"current_piece\":\"I\"") != std::string::npos, "live session should start with deterministic I piece");
	require(snapshot.find("\"next_piece\":\"O\"") != std::string::npos, "live session should expose next piece");

	session.apply_command("soft_drop");
	require(session.state_hash() != initial_hash, "soft_drop should change live state hash");
	session.apply_command("hard_drop");
	snapshot = session.snapshot_json();
	require(snapshot.find("\"score: 5\"") != std::string::npos, "hard_drop should score live session");
	require(snapshot.find("\"locked_count: 4\"") != std::string::npos, "hard_drop should lock I piece cells");
	require(snapshot.find("\"current_piece\":\"O\"") != std::string::npos, "first live lock should spawn O piece");
	require(snapshot.find("\"next_piece\":\"T\"") != std::string::npos, "post-lock live snapshot should expose next piece");
	require(snapshot.find("\"last_command_status\":\"accepted\"") != std::string::npos, "live hard drop should mark command accepted");
	session.apply_command("hard_drop");
	snapshot = session.snapshot_json();
	require(snapshot.find("\"current_piece\":\"T\"") != std::string::npos, "second live lock should spawn T piece");

	session.reset();
	require(session.state_hash() == initial_hash, "reset should restore initial live state hash");
	require(session.snapshot_json().find("\"current_piece\":\"I\"") != std::string::npos, "reset should restore deterministic initial piece");
	session.apply_command("tick");
	require(session.snapshot_json().find("\"last_command: tick\"") != std::string::npos, "tick command should update live diagnostics");
}

void test_live_plain_2d_gravity_tick_sequence() {
	tet4d::core::Plain2DSession session;
	const std::string initial_hash = session.state_hash();
	session.tick();
	require(session.state_hash() != initial_hash, "gravity tick should change state hash when active piece can fall");
	require(session.snapshot_json().find("\"current_piece\":\"I\"") != std::string::npos, "first gravity tick should keep I active");

	for (int step = 0; step < 8 && session.snapshot_json().find("\"current_piece\":\"O\"") == std::string::npos; ++step) {
		session.tick();
	}
	std::string snapshot = session.snapshot_json();
	require(snapshot.find("\"current_piece\":\"O\"") != std::string::npos, "gravity ticks should eventually lock I and spawn O");
	require(snapshot.find("\"score: 5\"") != std::string::npos, "gravity lock should score through C++");
	require(snapshot.find("\"last_command_status\":\"accepted\"") != std::string::npos, "gravity tick should report accepted status");

	session.reset();
	require(session.state_hash() == initial_hash, "reset after gravity sequence should restore deterministic initial hash");
}

void test_configurable_live_plain_2d_session() {
	tet4d::core::Plain2DSession session;
	const std::string standard_hash = session.state_hash();
	require(session.configure(10, 20), "supported 2D shape should configure");
	require(session.snapshot_json().find("\"board_shape\":[10,20]") != std::string::npos, "configured 2D snapshot shape missing");
	require(session.state_hash() != standard_hash, "2D shape must contribute to state identity");
	session.apply_command("hard_drop");
	session.reset();
	require(session.snapshot_json().find("\"board_shape\":[10,20]") != std::string::npos, "2D reset should preserve configured shape");
	require(!session.configure(3, 20), "2D width below semantic minimum should reject");
	require(!session.configure(10, 31), "2D height above safe maximum should reject");
	require(session.snapshot_json().find("\"board_shape\":[10,20]") != std::string::npos, "invalid configure must preserve session shape");
}

tet4d::core::PlainGameSetup setup_2d(
		int seed,
		int speed_level = 1,
		const std::string &random_mode = tet4d::core::RANDOM_MODE_FIXED_SEED) {
	tet4d::core::PlainGameSetup setup;
	setup.mode = "live_2d";
	setup.board_preset_id = "standard";
	setup.board_shape = {6, 6};
	setup.piece_set_id = "classic";
	setup.random_mode = random_mode;
	setup.configured_seed = seed;
	setup.initial_speed_level = speed_level;
	return setup;
}

void test_stage50_live_plain_2d_setup_identity() {
	tet4d::core::Plain2DSession session;
	require(session.configure(setup_2d(1337)), "valid Stage 50 2D setup should configure");
	const std::string initial = session.snapshot_json();
	require(initial.find("\"current_piece\":\"Z\"") != std::string::npos, "seed 1337 should match Python shuffled 2D bag");
	require(initial.find("\"next_piece\":\"L\"") != std::string::npos, "seed 1337 next piece should match Python");
	require(initial.find("\"piece_set_id\":\"classic\"") != std::string::npos, "2D snapshot piece-set identity missing");
	require(initial.find("\"random_mode\":\"fixed_seed\"") != std::string::npos, "2D snapshot random-mode identity missing");
	require(initial.find("\"configured_seed\":1337") != std::string::npos, "2D configured seed missing");
	require(initial.find("\"effective_seed\":1337") != std::string::npos, "2D effective seed missing");
	require(initial.find("\"initial_speed_level\":1") != std::string::npos, "2D initial speed missing");
	const std::string initial_hash = session.state_hash();
	session.apply_command("hard_drop");
	session.reset();
	require(session.state_hash() == initial_hash, "2D Stage 50 restart should restore setup, bag, RNG, and state");

	tet4d::core::Plain2DSession other_seed;
	require(other_seed.configure(setup_2d(2025, 7)), "alternate Stage 50 2D setup should configure");
	require(other_seed.state_hash() != initial_hash, "different seed/speed must change native state identity");
	require(other_seed.snapshot_json().find("\"initial_speed_level\":7") != std::string::npos, "alternate speed should be visible");

	tet4d::core::PlainGameSetup invalid = setup_2d(1337);
	invalid.piece_set_id = "debug_rectangles_2d";
	require(!session.configure(invalid), "unsupported 2D piece set must reject");
	invalid = setup_2d(1337, 11);
	require(!session.configure(invalid), "out-of-range 2D speed must reject");
	invalid = setup_2d(-1);
	require(!session.configure(invalid), "negative 2D seed must reject");
}

void test_stage50_true_random_seed_and_restart() {
	tet4d::core::Plain2DSession first;
	tet4d::core::PlainGameSetup setup = setup_2d(1337, 3, tet4d::core::RANDOM_MODE_TRUE_RANDOM);
	require(first.configure(setup), "true-random 2D setup should configure");
	const std::string snapshot = first.snapshot_json();
	require(snapshot.find("\"configured_seed\":null") != std::string::npos, "true-random configured seed should be null");
	require(snapshot.find("\"random_mode\":\"true_random\"") != std::string::npos, "true-random mode should be visible");
	const std::string initial_hash = first.state_hash();
	first.apply_command("hard_drop");
	first.reset();
	require(first.state_hash() == initial_hash, "true-random restart must reuse the captured effective seed");

	tet4d::core::Plain2DSession second;
	require(second.configure(setup), "second true-random 2D setup should configure");
	require(second.state_hash() != initial_hash, "new true-random construction should receive a different effective seed");
}

void verify_2d_refill_boundary(const std::string &random_mode) {
	tet4d::core::Plain2DSession shuffled;
	tet4d::core::PlainGameSetup setup = setup_2d(1337, 1, random_mode);
	setup.board_shape = {10, 30};
	require(shuffled.configure(setup), "large valid 2D board should configure for nonterminal preview boundary test");
	require_nonterminal(shuffled, "initial 2D boundary fixture");
	const std::string initial_hash = shuffled.state_hash();
	const std::string initial_snapshot = shuffled.snapshot_json();
	const std::string initial_status = shuffled.status();
	const tet4d::core::PieceShape2D initial_preview = shuffled.peek_next_piece_shape();
	const tet4d::core::PieceShape2D repeated_preview_2 = shuffled.peek_next_piece_shape();
	const tet4d::core::PieceShape2D repeated_preview_3 = shuffled.peek_next_piece_shape();
	require(same_shape(initial_preview, repeated_preview_2) && same_shape(initial_preview, repeated_preview_3), "three repeated 2D preview queries should be stable");
	if (random_mode == tet4d::core::RANDOM_MODE_FIXED_SEED) {
		require(initial_preview.name == "L", "fixed seed 1337 must retain the established 2D queue sequence");
	}
	require_production_shape(initial_preview);
	require(shuffled.state_hash() == initial_hash, "2D preview query must not change state hash");
	require(shuffled.snapshot_json() == initial_snapshot, "2D preview query must not change snapshot");
	require(shuffled.status() == initial_status, "2D preview query must not change command status");
	shuffled.apply_command("hard_drop");
	require_nonterminal(shuffled, "2D preview-to-spawn advancement");
	require(shuffled.snapshot_json().find("\"current_piece\":\"" + initial_preview.name + "\"") != std::string::npos, "2D preview must become the next normally spawned current piece");
	const tet4d::core::PieceShape2D following_preview = shuffled.peek_next_piece_shape();
	require(shuffled.snapshot_json().find("\"next_piece\":\"" + following_preview.name + "\"") != std::string::npos, "2D post-spawn preview must report the following authoritative entry");

	for (int draw = 0; draw < 5; ++draw) {
		shuffled.apply_command("hard_drop");
		require_nonterminal(shuffled, "2D refill-boundary hard-drop fixture");
	}
	require(shuffled.snapshot_json().find("\"next_piece\":\"pending_bag\"") != std::string::npos, "boundary fixture should preserve existing pending_bag snapshot semantics");
	const std::string boundary_hash = shuffled.state_hash();
	const std::string boundary_snapshot = shuffled.snapshot_json();
	const std::string boundary_status = shuffled.status();
	const tet4d::core::PieceShape2D refill_preview_1 = shuffled.peek_next_piece_shape();
	const tet4d::core::PieceShape2D refill_preview_2 = shuffled.peek_next_piece_shape();
	const tet4d::core::PieceShape2D refill_preview_3 = shuffled.peek_next_piece_shape();
	require(same_shape(refill_preview_1, refill_preview_2) && same_shape(refill_preview_1, refill_preview_3), "three empty-bag 2D preview queries should be stable");
	require_production_shape(refill_preview_1);
	require(shuffled.state_hash() == boundary_hash, "empty-bag 2D preview must not advance RNG or hash");
	require(shuffled.snapshot_json() == boundary_snapshot, "empty-bag 2D preview must not refill the real bag");
	require(shuffled.status() == boundary_status, "empty-bag 2D preview must not change bag/index/current observable status");
	shuffled.apply_command("hard_drop");
	require_nonterminal(shuffled, "2D refill prediction spawn");
	require(shuffled.snapshot_json().find("\"current_piece\":\"" + refill_preview_1.name + "\"") != std::string::npos, "2D refill preview must equal the next real draw");
	const tet4d::core::PieceShape2D post_refill_preview = shuffled.peek_next_piece_shape();
	require(shuffled.snapshot_json().find("\"next_piece\":\"" + post_refill_preview.name + "\"") != std::string::npos, "2D refill spawn must expose the following authoritative preview");
}

void test_next_piece_preview_is_exact_and_observational() {
	tet4d::core::Plain2DSession legacy;
	const tet4d::core::PieceShape2D legacy_preview = legacy.peek_next_piece_shape();
	require(legacy_preview.name == "O", "legacy 2D preview should report the exact next piece");
	require(legacy_preview.color_id == 2 && legacy_preview.blocks.size() == 4, "legacy 2D preview should expose production color and cells");
	require_production_shape(legacy_preview);

	verify_2d_refill_boundary(tet4d::core::RANDOM_MODE_FIXED_SEED);
	verify_2d_refill_boundary(tet4d::core::RANDOM_MODE_TRUE_RANDOM);
}

std::string export_stage50_setup_case_2d(const std::string &case_id) {
	tet4d::core::PlainGameSetup setup = setup_2d(1337);
	std::vector<std::string> actions = {"move_right", "rotate_cw", "soft_drop", "hard_drop"};
	if (case_id == "setup_plain_2d_alternate") {
		setup.board_preset_id = "large";
		setup.board_shape = {10, 20};
		setup.configured_seed = 2025;
		setup.initial_speed_level = 7;
		actions = {"soft_drop", "hard_drop"};
	} else if (case_id != "setup_plain_2d_standard") {
		return "{}";
	}
	tet4d::core::Plain2DSession session;
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

void test_game_over_spawn_blocked_and_rejected_commands() {
	tet4d::core::GameState2D blocked_state(6, 6);
	blocked_state.active_piece = tet4d::core::ActivePiece2D{tet4d::core::trace_dot_shape_2d(), {0, 5}, 0};
	blocked_state.post_lock_spawn_shape = tet4d::core::classic_i_shape_2d();
	for (int x = 1; x <= 4; ++x) {
		blocked_state.board.set_cell({x, 0}, 2);
	}

	blocked_state.hard_drop();
	require(blocked_state.game_over, "spawn-blocked fixture should set game_over");
	require(blocked_state.game_over_reason == "spawn_blocked", "spawn-blocked fixture should record reason");

	tet4d::core::Plain2DSession session;
	for (int step = 0; step < 40 && session.snapshot_json().find("\"game_over\":true") == std::string::npos; ++step) {
		session.apply_command("hard_drop");
	}
	std::string snapshot = session.snapshot_json();
	require(snapshot.find("\"game_over\":true") != std::string::npos, "live session should eventually reach game_over");
	require(snapshot.find("\"game_over_reason\":\"") != std::string::npos, "live game_over snapshot should include reason");
	const std::string game_over_hash = session.state_hash();
	const std::string status = session.apply_command("move_left");
	require(status.find("last_command=rejected:move_left") != std::string::npos, "game_over command should be rejected");
	require(status.find("last_command_status=rejected") != std::string::npos, "game_over command should report rejected status");
	require(session.state_hash() == game_over_hash, "rejected game_over command should not change state hash");

	session.reset();
	snapshot = session.snapshot_json();
	require(snapshot.find("\"game_over\":false") != std::string::npos, "reset should clear game_over");
	require(snapshot.find("\"game_over_reason\":\"\"") != std::string::npos, "reset should clear game_over reason");
	require(session.state_hash() == tet4d::core::Plain2DSession().state_hash(), "reset game_over session should restore deterministic hash");
}

void test_authoritative_hold_transition_2d() {
	tet4d::core::Plain2DSession session;
	require(!session.held_piece_shape().has_value(), "new 2D session Hold must be empty");
	require(session.hold_available(), "new 2D active lifecycle must allow Hold");
	require(session.snapshot_json().find("\"held_piece\":null") != std::string::npos, "2D snapshot must expose intentional empty Hold");
	require(session.snapshot_json().find("\"hold_available\":true") != std::string::npos, "2D snapshot must expose Hold availability");

	const auto first_next = session.peek_next_piece_shape();
	const std::string initial_hash = session.state_hash();
	const std::string first_result = session.apply_command("hold");
	require(first_result.find("last_command_status=accepted") != std::string::npos, "first 2D Hold must be accepted");
	require(session.held_piece_shape().has_value() && session.held_piece_shape()->name == "I", "first 2D Hold must store active identity");
	require(session.snapshot_json().find("\"current_piece\":\"" + first_next.name + "\"") != std::string::npos, "first 2D Hold must consume exactly the former NEXT piece");
	require(session.peek_next_piece_shape().name == "T", "first 2D Hold must advance the queue exactly once");
	require(!session.hold_available(), "Hold must be unavailable until the resulting active locks");
	require(session.state_hash() != initial_hash, "held identity and availability must affect 2D state hash");

	const std::string rejected_hash = session.state_hash();
	const auto rejected_next = session.peek_next_piece_shape();
	const auto rejected_held = session.held_piece_shape();
	require(session.apply_command("hold").find("last_command_status=rejected") != std::string::npos, "second 2D Hold before lock must reject explicitly");
	require(session.state_hash() == rejected_hash && same_shape(session.peek_next_piece_shape(), rejected_next), "rejected 2D Hold must preserve hash, queue, and RNG");
	require(session.held_piece_shape().has_value() && same_shape(*session.held_piece_shape(), *rejected_held), "rejected 2D Hold must preserve held identity");

	const std::string query_hash = session.state_hash();
	(void) session.held_piece_shape();
	(void) session.hold_available();
	require(session.state_hash() == query_hash, "2D Hold queries must be observationally pure");

	session.apply_command("hard_drop");
	require(session.hold_available(), "successful 2D lock and spawn must begin a Hold-eligible lifecycle");
	const auto occupied_next = session.peek_next_piece_shape();
	session.apply_command("move_right");
	session.apply_command("rotate_cw");
	require(session.apply_command("hold").find("last_command_status=accepted") != std::string::npos, "occupied 2D Hold must be accepted");
	require(session.snapshot_json().find("\"current_piece\":\"I\"") != std::string::npos, "occupied 2D Hold must retrieve the held identity");
	require(session.snapshot_json().find("\"current_piece_color_id\":1") != std::string::npos, "retrieved 2D piece must retain production identity");
	require(session.held_piece_shape().has_value() && session.held_piece_shape()->name == "T", "occupied 2D Hold must store outgoing identity only");
	require(same_shape(session.peek_next_piece_shape(), occupied_next), "occupied 2D Hold must not consume queue or RNG");
	require(session.snapshot_json().find("\"active_cells\":[{\"color_id\":1") != std::string::npos, "retrieved 2D piece must use canonical active geometry");

	const tet4d::core::Plain2DSession value_snapshot = session;
	session.apply_command("hard_drop");
	session = value_snapshot;
	require(session.state_hash() == value_snapshot.state_hash() && session.held_piece_shape()->name == "T" && !session.hold_available(), "2D value snapshot/restore must preserve complete Hold state");

	const std::vector<std::string> replay = {"hold", "hold", "hard_drop", "move_right", "rotate_cw", "hold"};
	tet4d::core::Plain2DSession replay_a;
	tet4d::core::Plain2DSession replay_b;
	for (const std::string &command : replay) {
		replay_a.apply_command(command);
		replay_b.apply_command(command);
	}
	require(replay_a.state_hash() == replay_b.state_hash() && replay_a.snapshot_json() == replay_b.snapshot_json(), "2D semantic Hold command replay must reproduce exact final state");

	session.reset();
	require(!session.held_piece_shape().has_value() && session.hold_available(), "2D restart must restore empty, available Hold");
}

} // namespace

int main(int argc, char **argv) {
	if (argc >= 2 && std::string(argv[1]) == "--pilot-stable-hash") {
		test_stable_hash_pilot();
		return 0;
	}
	if (argc >= 2 && std::string(argv[1]) == "--export-plain-2d-trace") {
		const std::string case_id = argc >= 3 ? std::string(argv[2]) : "gameplay_plain_2d_short";
		std::cout << tet4d::core::export_plain_2d_trace_json(case_id) << "\n";
		return 0;
	}
	if (argc >= 2 && std::string(argv[1]) == "--export-plain-setup") {
		const std::string case_id = argc >= 3 ? std::string(argv[2]) : "setup_plain_2d_standard";
		std::cout << export_stage50_setup_case_2d(case_id) << "\n";
		return 0;
	}
	test_board_and_piece_cells();
	test_command_replay();
	test_authoritative_hard_drop_destination_2d();
	test_trace_export_smoke();
	test_stage11_trace_exports();
	test_live_plain_2d_session();
	test_live_plain_2d_gravity_tick_sequence();
	test_configurable_live_plain_2d_session();
	test_stage50_live_plain_2d_setup_identity();
	test_stage50_true_random_seed_and_restart();
	test_next_piece_preview_is_exact_and_observational();
	test_game_over_spawn_blocked_and_rejected_commands();
	test_authoritative_hold_transition_2d();
	std::cout << "tet4d_core native plain 2D tests passed\n";
	return 0;
}
