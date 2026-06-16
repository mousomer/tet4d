#include "tet4d_core/plain_nd.hpp"
#include "tet4d_core/plain_nd_session.hpp"
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
	require(cases.size() == 8, "Stage 20 should expose eight implemented plain ND parity cases");
	require(cases[0] == "gameplay_plain_3d_short", "first ND case id mismatch");
	require(cases[1] == "gameplay_plain_4d_short", "second ND case id mismatch");
	require(cases[2] == "gameplay_plain_3d_rotation_short", "third ND case id mismatch");
	require(cases[3] == "gameplay_plain_4d_rotation_short", "fourth ND case id mismatch");
	require(cases[4] == "gameplay_plain_3d_plane_clear_short", "fifth ND case id mismatch");
	require(cases[5] == "gameplay_plain_4d_plane_clear_short", "sixth ND case id mismatch");
	require(cases[6] == "gameplay_plain_3d_spawn_blocked_game_over", "seventh ND case id mismatch");
	require(cases[7] == "gameplay_plain_4d_spawn_blocked_game_over", "eighth ND case id mismatch");
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
	test_coord_and_board_model();
	test_3d_state_stepper();
	test_4d_state_stepper();
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
