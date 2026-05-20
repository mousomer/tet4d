#include "tet4d_core/core_api.hpp"
#include "tet4d_core/plain_2d.hpp"
#include "tet4d_core/sha256.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string &message) {
	if (!condition) {
		std::cerr << message << "\n";
		std::exit(1);
	}
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
	require(cases.size() == 4, "Stage 11 should expose four plain 2D parity cases");
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

} // namespace

int main(int argc, char **argv) {
	if (argc >= 2 && std::string(argv[1]) == "--export-plain-2d-trace") {
		const std::string case_id = argc >= 3 ? std::string(argv[2]) : "gameplay_plain_2d_short";
		std::cout << tet4d::core::export_plain_2d_trace_json(case_id) << "\n";
		return 0;
	}
	test_board_and_piece_cells();
	test_command_replay();
	test_trace_export_smoke();
	test_stage11_trace_exports();
	std::cout << "tet4d_core native plain 2D tests passed\n";
	return 0;
}
