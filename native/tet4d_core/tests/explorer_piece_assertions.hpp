#pragma once

#include "tet4d_core/explorer_piece.hpp"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <set>

namespace explorer_test {
using namespace tet4d::core;
inline std::string context;
inline std::size_t atomic_rejections = 0;
inline void require(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << " [" << context << "]\n";
        std::exit(1);
    }
}
inline void assert_valid_local_frames(const ExplorerPiece& piece) {
    for (const auto& cell : piece.cells)
        require(valid_piece_frame(cell.frame), "valid frame");
}
inline void assert_unique_occupancy(const ExplorerPiece& piece) {
    std::set<CoordND> coordinates;
    for (const auto& cell : piece.cells) {
        require(coordinates.insert(cell.coordinate).second, "unique destination");
        require(cell.domain == 0 && cell.coordinate.dimension() == piece.profile.rank,
                "domain/rank");
        for (std::size_t j = 0; j < cell.coordinate.values.size(); ++j)
            require(cell.coordinate.values[j] >= 0 &&
                        cell.coordinate.values[j] < piece.profile.dimensions[j],
                    "in bounds");
    }
}
inline void assert_piece_preserved(const ExplorerPiece& before, const ExplorerPiece& after) {
    require(before.cells.size() == after.cells.size(), "conserved count");
    std::set<std::int64_t> first, second;
    for (const auto& cell : before.cells)
        require(first.insert(cell.id).second, "unique source ID");
    for (const auto& cell : after.cells)
        require(second.insert(cell.id).second, "unique destination ID");
    require(first == second, "persistent ID set");
    auto metadata = after;
    metadata.cells = before.cells;
    require(metadata == before, "unchanged version/object/profile/original geometry");
    assert_valid_local_frames(after);
    assert_unique_occupancy(after);
}
inline void assert_exact_semantic_recovery(const ExplorerPiece& initial,
                                           const ExplorerPiece& recovered) {
    require(initial == recovered, "exact semantic recovery");
}
inline void assert_atomic_noop(const PieceEnvelope& before, const PieceEnvelope& after) {
    require(before == after, "entire envelope unchanged");
    ++atomic_rejections;
}
inline void assert_deterministic_proposal(const ExplorerPiece& source, MoveStepQuery action) {
    auto first = propose_piece_translation(source, 0, action);
    auto reordered = source;
    std::reverse(reordered.cells.begin(), reordered.cells.end());
    std::reverse(reordered.rest_cells.begin(), reordered.rest_cells.end());
    auto second = propose_piece_translation(reordered, 0, action);
    require(first.failure == second.failure && first.candidate == second.candidate,
            "row-order-independent complete candidate/witness");
}
struct FixtureCase {
    std::string id;
    ExplorerPiece source;
    std::int64_t revision = 0;
    MoveStepQuery action;
    std::string failure;
    PieceClassification classification = PieceClassification::blocked;
    ExplorerPiece target;
    std::string inverse_version;
    std::vector<PieceWitness> witnesses;
    bool unsupported_profile = false;
};
} // namespace explorer_test
