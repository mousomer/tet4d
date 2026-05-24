#include "tet4d_core/plain_nd.hpp"
#include "tet4d_core/plain_nd_trace.hpp"

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

void test_trace_exports() {
	const std::vector<std::string> cases = tet4d::core::list_plain_nd_parity_cases();
	require(cases.size() == 2, "Stage 15 should expose two plain ND parity cases");
	require(cases[0] == "gameplay_plain_3d_short", "first ND case id mismatch");
	require(cases[1] == "gameplay_plain_4d_short", "second ND case id mismatch");
	require(tet4d::core::run_builtin_plain_nd_smoke_case(), "plain ND smoke API should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_short"), "3D required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_short"), "4D required fields should pass");

	const std::string trace_3d = tet4d::core::export_plain_nd_trace_json("gameplay_plain_3d_short");
	require(trace_3d.find("\"dimension\":3") != std::string::npos, "3D trace dimension missing");
	require(trace_3d.find("\"state_hash\":\"9e183b178d0badec86b59a833782702d581b13a72d75bddeeda7f88333826dd7\"") != std::string::npos, "3D final hash missing");
	require(trace_3d.find("\"locked_cell_digest\":\"4b7a6b700d15a928dd23c2a187403358cb3dcf1fd03c8855559d26663d6ded1d\"") != std::string::npos, "3D locked digest missing");

	const std::string trace_4d = tet4d::core::export_plain_nd_trace_json("gameplay_plain_4d_short");
	require(trace_4d.find("\"dimension\":4") != std::string::npos, "4D trace dimension missing");
	require(trace_4d.find("\"state_hash\":\"d34d21da0a1c4aa6e947230e68e8b16a3e212b40bb7da1ccaef24200e7f80449\"") != std::string::npos, "4D final hash missing");
	require(trace_4d.find("\"locked_cell_digest\":\"49a3a8a0dffab41bfaaf4c5dc3210d2d50de7f52d9891f4a2ec812d645114463\"") != std::string::npos, "4D locked digest missing");

	const std::string unsupported = tet4d::core::export_plain_nd_trace_json("gameplay_plain_nd_rotation_deferred");
	require(unsupported.find("\"error\":\"unsupported plain ND parity case\"") != std::string::npos, "unsupported ND trace case should fail clearly");
}

} // namespace

int main(int argc, char **argv) {
	if (argc >= 2 && std::string(argv[1]) == "--export-plain-nd-trace") {
		const std::string case_id = argc >= 3 ? std::string(argv[2]) : "gameplay_plain_3d_short";
		std::cout << tet4d::core::export_plain_nd_trace_json(case_id) << "\n";
		return 0;
	}
	test_coord_and_board_model();
	test_3d_state_stepper();
	test_4d_state_stepper();
	test_trace_exports();
	std::cout << "tet4d_core native plain ND tests passed\n";
	return 0;
}
