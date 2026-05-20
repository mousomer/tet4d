#include "tet4d_core/core_api.hpp"
#include "tet4d_core/plain_2d.hpp"

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
	require(tet4d::core::run_builtin_plain_2d_smoke_case(), "plain 2D smoke API should pass");
}

} // namespace

int main(int argc, char **argv) {
	if (argc == 2 && std::string(argv[1]) == "--export-plain-2d-trace") {
		std::cout << tet4d::core::export_plain_2d_trace_json() << "\n";
		return 0;
	}
	test_board_and_piece_cells();
	test_command_replay();
	test_trace_export_smoke();
	std::cout << "tet4d_core native plain 2D tests passed\n";
	return 0;
}
