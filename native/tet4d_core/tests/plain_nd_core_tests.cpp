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

void test_trace_exports() {
	const std::vector<std::string> cases = tet4d::core::list_plain_nd_parity_cases();
	require(cases.size() == 6, "Stage 19 should expose six implemented plain ND parity cases");
	require(cases[0] == "gameplay_plain_3d_short", "first ND case id mismatch");
	require(cases[1] == "gameplay_plain_4d_short", "second ND case id mismatch");
	require(cases[2] == "gameplay_plain_3d_rotation_short", "third ND case id mismatch");
	require(cases[3] == "gameplay_plain_4d_rotation_short", "fourth ND case id mismatch");
	require(cases[4] == "gameplay_plain_3d_plane_clear_short", "fifth ND case id mismatch");
	require(cases[5] == "gameplay_plain_4d_plane_clear_short", "sixth ND case id mismatch");
	require(tet4d::core::run_builtin_plain_nd_smoke_case(), "plain ND smoke API should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_short"), "3D required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_short"), "4D required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_rotation_short"), "3D rotation required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_rotation_short"), "4D rotation required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_3d_plane_clear_short"), "3D clear required fields should pass");
	require(tet4d::core::get_plain_nd_required_field_parity("gameplay_plain_4d_plane_clear_short"), "4D clear required fields should pass");

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
	test_3d_rotation_stepper();
	test_4d_rotation_stepper();
	test_rotation_rejects_invalid_axes_clearly();
	test_3d_plane_clear_stepper();
	test_4d_plane_clear_stepper();
	test_trace_exports();
	std::cout << "tet4d_core native plain ND tests passed\n";
	return 0;
}
