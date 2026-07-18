#include "tet4d_core/core_api.hpp"
#include "tet4d_core/plain_2d.hpp"
#include "tet4d_core/plain_2d_session.hpp"
#include "tet4d_core/sha256.hpp"

#include <cstdlib>
#include <iostream>
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
	test_board_and_piece_cells();
	test_command_replay();
	test_trace_export_smoke();
	test_stage11_trace_exports();
	test_live_plain_2d_session();
	test_live_plain_2d_gravity_tick_sequence();
	test_configurable_live_plain_2d_session();
	test_stage50_live_plain_2d_setup_identity();
	test_stage50_true_random_seed_and_restart();
	test_game_over_spawn_blocked_and_rejected_commands();
	std::cout << "tet4d_core native plain 2D tests passed\n";
	return 0;
}
