#pragma once

// Material-rigidity helper and randomized rigidity suite are intentionally retired:
// superseded_forward_explorer by the free-cellwise translation amendment.
// Surface-specific conformance runs against production proposals and serialized commits.
inline void surface_cases() {
    using namespace explorer_test;
    for (const auto& fixture : reviewed_cellwise_sequences()) {
        context = fixture.id;
        auto piece = make_piece({{{0, 0}}}, 8, 8, false);
        piece.profile = fixture.profile;
        piece.cells[0].coordinate = fixture.source;
        ExplorerPieceRuntime runtime({0, piece, piece, {}});
        std::vector<PieceInverse> history;
        for (std::size_t i = 0; i < fixture.targets.size(); ++i) {
            auto before = runtime.snapshot();
            auto moved = propose_piece_translation(before.piece, before.revision, {1, -1});
            require(moved.candidate.has_value(), "owner Up trajectory accepted");
            require(moved.candidate->target.cells[0].coordinate == fixture.targets[i] &&
                        moved.candidate->target.cells[0].frame == fixture.frames[i],
                    "owner trajectory and accumulated orientation match");
            history.push_back(moved.candidate->inverse);
            commit(runtime, *moved.candidate);
        }
        while (!history.empty()) { undo(runtime, history.back()); history.pop_back(); }
        assert_exact_semantic_recovery(piece, runtime.snapshot().piece);
        // A vertical domino has one seam cell and one ordinary interior cell.
        auto domino = make_piece({{{0, 0}}, {{0, 1}}}, 8, 8, false);
        domino.profile = fixture.profile;
        domino.cells[0].coordinate = {{2, 0}};
        domino.cells[1].coordinate = {{2, 1}};
        ExplorerPieceRuntime deformation({0, domino, domino, {}});
        auto first = propose_piece_translation(domino, 0, {1, -1});
        require(first.candidate && first.candidate->classification == PieceClassification::cellwise_deformation,
                "mixed seam/interior translation accepts deformation");
        require(first.candidate->target.cells[0].coordinate == fixture.targets[0] &&
                    first.candidate->target.cells[1].coordinate == CoordND{{2, 0}},
                "domino cells independently follow board Up");
        commit(deformation, *first.candidate);
        auto second = propose_piece_translation(deformation.snapshot().piece, 1, {1, -1});
        require(second.candidate && second.candidate->target.cells[0].coordinate == fixture.targets[1] &&
                    second.candidate->target.cells[1].coordinate == fixture.targets[0],
                "continued Up never remaps through a cell frame");
        commit(deformation, *second.candidate);
        undo(deformation, second.candidate->inverse);
        undo(deformation, first.candidate->inverse);
        assert_exact_semantic_recovery(domino, deformation.snapshot().piece);
    }
    const std::vector<std::string> presets{"mobius", "klein", "projective", "sphere"};
    std::size_t crossings = 0;
    for (const auto& preset : presets)
        for (const auto& size : std::vector<std::array<int, 2>>{{1, 1}, {1, 2}, {2, 1}, {2, 2}, {3, 4}})
            for (int domain = 0; domain < (preset == "sphere" ? 2 : 1); ++domain)
                for (int x = 0; x < size[0]; ++x)
                    for (int y = 0; y < size[1]; ++y)
                        for (int axis = 0; axis < 2; ++axis)
                            for (int delta : {-1, 1}) {
                                context = preset + " neighbor " + std::to_string(x) + "," +
                                          std::to_string(y) + " domain " + std::to_string(domain);
                                auto piece = make_piece({{{0, 0}}}, size[0], size[1], false);
                                if (preset == "sphere") piece.version = EXPLORER_DOMAIN_VERSION;
                                else {
                                    piece.profile.seams.push_back({"x", {0, "-"}, {0, "+"},
                                                                   {{0}, {preset == "klein" ? 1 : -1}}, true});
                                    if (preset != "mobius")
                                        piece.profile.seams.push_back({"y", {1, "-"}, {1, "+"}, {{0}, {-1}}, true});
                                }
                                piece.cells[0].coordinate = {{x, y}};
                                piece.cells[0].domain = domain;
                                ExplorerPiece canonical;
                                require(validate_explorer_piece(piece, canonical) == PieceFailure::none,
                                        "admit surface state");
                                ExplorerPieceRuntime runtime({0, canonical, canonical, {}});
                                auto before = runtime.snapshot();
                                auto proposed = propose_piece_translation(piece, 0, {axis, delta});
                                bool boundary = (axis == 0 ? x : y) + delta < 0 ||
                                                (axis == 0 ? x : y) + delta >= size[axis];
                                if (preset == "mobius" && axis == 1 && boundary) {
                                    require(proposed.failure == PieceFailure::unconnected_boundary && !proposed.candidate,
                                            "Mobius boundary remains open");
                                    assert_atomic_noop(before, runtime.snapshot());
                                    continue;
                                }
                                require(proposed.candidate.has_value(), "surface step exists");
                                const auto& target = proposed.candidate->target.cells[0];
                                auto expected = piece.cells[0];
                                if (!boundary) expected.coordinate.values[axis] += delta;
                                else if (preset == "sphere") {
                                    expected.domain = 1 - domain;
                                    expected.frame.signs[axis] = -1;
                                } else {
                                    expected.coordinate.values[axis] = delta < 0 ? size[axis] - 1 : 0;
                                    if (preset == "projective" || preset == "mobius" || axis == 1) {
                                        expected.coordinate.values[1-axis] = size[1-axis] - 1 - expected.coordinate.values[1-axis];
                                        expected.frame.signs[1-axis] = -1;
                                    }
                                }
                                require(target == expected, "independent signed-boundary expectation");
                                commit(runtime, *proposed.candidate);
                                undo(runtime, proposed.candidate->inverse);
                                assert_exact_semantic_recovery(canonical, runtime.snapshot().piece);
                                if (boundary) ++crossings;
                            }
    context = "sphere collision across domains";
    auto sphere = make_piece({{{0, 0}}, {{1, 0}}}, 4, 4, false);
    sphere.version = EXPLORER_DOMAIN_VERSION;
    sphere.cells[1].domain = 1;
    ExplorerPieceRuntime runtime({0, sphere, sphere, {}});
    auto before = runtime.snapshot();
    auto blocked = propose_piece_translation(sphere, 0, {0, -1});
    require(blocked.failure == PieceFailure::destination_collision && !blocked.candidate,
            "cross-domain many-to-one blocked");
    assert_atomic_noop(before, runtime.snapshot());
    sphere.cells[1].coordinate = {{0, 0}};
    ExplorerPiece canonical;
    require(validate_explorer_piece(sphere, canonical) == PieceFailure::none,
            "same coordinate in two domains is distinct occupancy");
    auto invalid = sphere;
    invalid.cells[0].domain = 2;
    require(validate_explorer_piece(invalid, canonical) == PieceFailure::unsupported_representation,
            "unknown sphere domain rejected");
    invalid = sphere;
    invalid.profile.seams = {{"x", {0, "-"}, {0, "+"}, {{0}, {1}}, true}};
    require(validate_explorer_piece(invalid, canonical) == PieceFailure::invalid_profile,
            "sphere cannot smuggle v1 seams");
    for (const auto& preset : presets) {
        context = preset + " rotation identities";
        auto piece = make_piece({{{0, 0}}, {{0, 1}}, {{1, 0}}}, 6, 6, false);
        for (auto& cell : piece.cells) { cell.coordinate.values[0] += 2; cell.coordinate.values[1] += 2; }
        if (preset == "sphere") piece.version = EXPLORER_DOMAIN_VERSION;
        else {
            piece.profile.seams = {{"x", {0, "-"}, {0, "+"}, {{0}, {preset == "klein" ? 1 : -1}}, true}};
            if (preset != "mobius") piece.profile.seams.push_back({"y", {1, "-"}, {1, "+"}, {{0}, {-1}}, true});
        }
        require(validate_explorer_piece(piece, canonical) == PieceFailure::none, "rotation baseline valid");
        ExplorerPieceRuntime turns({0, canonical, canonical, {}});
        for (int i = 0; i < 4; ++i) {
            auto current = turns.snapshot();
            auto turn = propose_piece_rotation(current.piece, current.revision, 1);
            require(turn.candidate.has_value(), "coherent in-chart rotation supported");
            commit(turns, *turn.candidate);
            auto recovery = propose_piece_inverse(turns.snapshot().piece, turns.snapshot().revision, turn.candidate->inverse);
            require(recovery.candidate && recovery.candidate->target == current.piece, "recorded rotation undo");
        }
        assert_exact_semantic_recovery(canonical, turns.snapshot().piece);
        auto mixed = canonical;
        mixed.cells[1].frame.signs[0] = -1;
        auto rebuilt = propose_piece_rotation(mixed, 0, 1);
        require(rebuilt.candidate.has_value(), "mixed frames rotate from the anchor cell");
        for (const auto& cell : rebuilt.candidate->target.cells)
            require(cell.frame == rebuilt.candidate->target.cells.front().frame,
                    "in-chart rebuilt rotation shares the anchor frame");
        require(turns.retry() == PieceFailure::none && turns.snapshot().undo.empty(), "surface Retry clears history");
        assert_exact_semantic_recovery(canonical, turns.snapshot().piece);
    }
    for (const auto& preset : presets) for (int frame_code = 0; frame_code < 8; ++frame_code) {
        context = preset + " fixed-seed material-frame sequence " + std::to_string(frame_code);
        auto piece = make_piece({{{0, 0}}, {{1, 0}}, {{1, 1}}}, 4, 5, false);
        if (preset == "sphere") piece.version = EXPLORER_DOMAIN_VERSION;
        else {
            piece.profile.seams = {{"x", {0, "-"}, {0, "+"}, {{0}, {preset == "klein" ? 1 : -1}}, true}};
            if (preset != "mobius") piece.profile.seams.push_back({"y", {1, "-"}, {1, "+"}, {{0}, {-1}}, true});
        }
        const PieceFrame material{frame_code & 4 ? std::vector<int>{1, 0} : std::vector<int>{0, 1},
                                  {frame_code & 1 ? -1 : 1, frame_code & 2 ? -1 : 1}};
        for (auto& cell : piece.cells) cell.frame = material;
        require(validate_explorer_piece(piece, canonical) == PieceFailure::none, "sequence source valid");
        ExplorerPieceRuntime sequence({0, canonical, canonical, {}});
        std::mt19937 random(20261115 + frame_code);
        std::vector<PieceInverse> history;
        for (int step = 0; step < 64; ++step) {
            auto before_action = sequence.snapshot();
            int action = static_cast<int>(random() % 6);
            auto proposed = action < 4
                ? propose_piece_translation(before_action.piece, before_action.revision, {action / 2, action % 2 ? 1 : -1})
                : propose_piece_rotation(before_action.piece, before_action.revision, action == 4 ? -1 : 1);
            if (!proposed.candidate) {
                require(proposed.failure != PieceFailure::none, "blocked sequence has reason");
                assert_atomic_noop(before_action, sequence.snapshot());
                continue;
            }
            history.push_back(proposed.candidate->inverse);
            auto forged = *proposed.candidate;
            forged.target.cells.front().domain = 99;
            reject_apply(sequence, forged, PieceFailure::candidate_mismatch);
            commit(sequence, *proposed.candidate);
        }
        while (!history.empty()) { undo(sequence, history.back()); history.pop_back(); }
        assert_exact_semantic_recovery(canonical, sequence.snapshot().piece);
        require(sequence.snapshot().undo.empty(), "sequence complete inverse history");
    }
    // Superseded material-frame/rigid-straddling expectations are replaced by
    // focused board-axis deformation and snapshot Undo cases below.
    context = "Mobius straddling board-axis translation";
    {
        auto piece = make_piece({{{0, 0}}, {{1, 0}}}, 4, 4, false);
        piece.profile.seams = {{"x", {0, "-"}, {0, "+"}, {{0}, {-1}}, true}};
        piece.cells[0].coordinate = {{3, 2}};
        piece.cells[0].frame.signs = {1, -1};
        piece.cells[1].coordinate = {{0, 1}};
        ExplorerPieceRuntime runtime({0, piece, piece, {}});
        auto moved = propose_piece_translation(piece, 0, {1, -1});
        require(moved.candidate.has_value(), "straddling domino deforms successfully");
        require(moved.candidate->target.cells[0].coordinate == CoordND{{3, 1}} &&
                    moved.candidate->target.cells[1].coordinate == CoordND{{0, 0}},
                "same board Y- reaches both cells regardless of frames");
        commit(runtime, *moved.candidate);
        undo(runtime, moved.candidate->inverse);
        assert_exact_semantic_recovery(piece, runtime.snapshot().piece);
    }

    context = "Mobius turns across the flipped seam keep one screen sense";
    {
        auto bar = make_piece({{{0, 0}}, {{0, 1}}, {{0, 2}}}, 8, 8, false);
        bar.profile.seams = {{"x", {0, "-"}, {0, "+"}, {{0}, {-1}}, true}};
        for (auto& cell : bar.cells) cell.frame.signs = {-1, 1};
        ExplorerPiece canonical_bar;
        require(validate_explorer_piece(bar, canonical_bar) == PieceFailure::none, "bar valid");
        auto quarter = propose_piece_rotation(canonical_bar, 0, 1);
        require(quarter.candidate.has_value(), "turn crosses the seam");
        require(quarter.candidate->target.cells[0].coordinate == CoordND{{7, 6}} &&
                    quarter.candidate->target.cells[1].coordinate == CoordND{{0, 1}},
                "the end cell crosses the flipped seam, the centre stays");
        auto back = propose_piece_rotation(quarter.candidate->target, 0, -1);
        require(back.candidate && back.candidate->target == canonical_bar,
                "CW then CCW restores the bar");
        auto half = propose_piece_rotation(quarter.candidate->target, 0, 1);
        require(half.candidate && !(half.candidate->target == canonical_bar),
                "CW twice is a half turn, not a flip back");
    }

    context = "cone points refuse overlap instead of collapsing cells";
    {
        auto fold = make_piece({{{0, 0}}, {{1, 0}}}, 4, 4, false);
        fold.profile.seams = {{"seam_000", {0, "-"}, {1, "-"}, {{0}, {1}}, true},
                              {"seam_001", {0, "+"}, {1, "+"}, {{0}, {1}}, true}};
        ExplorerPiece canonical_fold;
        require(validate_explorer_piece(fold, canonical_fold) == PieceFailure::none,
                "adjacent-edge sphere is ordinary v1 state");
        auto collapsed = propose_piece_translation(fold, 0, {0, -1});
        require(collapsed.failure == PieceFailure::destination_collision && !collapsed.candidate,
                "sphere fold corner refuses two cells on one site");
        auto overlapping = fold;
        overlapping.cells[1].coordinate = overlapping.cells[0].coordinate;
        require(validate_explorer_piece(overlapping, canonical_fold) == PieceFailure::invalid_piece_state,
                "coincident cells are never admitted");
    }
    require(crossings > 100, "all surface/extent/direction boundary combinations exercised");
    std::cout << "surface_conformance: " << crossings << " signed seam crossings and exact inverses\n";
}
