#include "tet4d_core/explorer_piece.hpp"

#include <array>
#include <limits>
#include <set>
#include <stdexcept>

namespace tet4d::core {
namespace {
using Point = std::array<std::int64_t, 2>;
PieceProposal rotate(const ExplorerPiece& source, std::int64_t revision, int direction) {
    PieceCandidate result;
    auto status = validate_explorer_piece(source, result.source);
    if (status != PieceFailure::none)
        return {std::nullopt, status};
    if (direction != -1 && direction != 1)
        return {std::nullopt, PieceFailure::invalid_action};
    if (revision < 0)
        return {std::nullopt, PieceFailure::invalid_piece_state};
    if (revision == std::numeric_limits<std::int64_t>::max())
        return {std::nullopt, PieceFailure::resource_limit};
    const auto& piece = result.source;
    const auto reference = explorer_reference_cell(piece);
    const auto& anchor = piece.cells[reference];
    // Develop the material shape in the reference (anchor) cell's chart. Other cells' current sites
    // are not consulted: the turned piece is rebuilt from the anchor, so no consistency check
    // applies.
    std::vector<Point> developed;
    Point low{}, high{}, sum{};
    for (std::size_t i = 0; i < piece.cells.size(); ++i) {
        Point point{anchor.coordinate.values[0], anchor.coordinate.values[1]};
        for (std::size_t axis = 0; axis < 2; ++axis)
            point[static_cast<std::size_t>(anchor.frame.permutation[axis])] +=
                static_cast<std::int64_t>(anchor.frame.signs[axis]) *
                (piece.rest_cells[i].coordinate.values[axis] -
                 piece.rest_cells[reference].coordinate.values[axis]);
        for (std::size_t axis = 0; axis < 2; ++axis) {
            low[axis] = i == 0 ? point[axis] : std::min(low[axis], point[axis]);
            high[axis] = i == 0 ? point[axis] : std::max(high[axis], point[axis]);
            sum[axis] += point[axis];
        }
        developed.push_back(point);
    }
    Point twice_pivot{low[0] + high[0], low[1] + high[1]};
    if ((high[0] - low[0]) % 2 != (high[1] - low[1]) % 2) {
        std::size_t nearest = 0;
        const auto count = static_cast<std::int64_t>(developed.size());
        for (std::size_t i = 1; i < developed.size(); ++i) {
            // Difference of squared centroid distances, avoiding overflowing n^2*u^2.
            std::int64_t difference = 0;
            for (std::size_t axis = 0; axis < 2; ++axis)
                difference +=
                    (developed[i][axis] - developed[nearest][axis]) *
                    (count * (developed[i][axis] + developed[nearest][axis]) - 2 * sum[axis]);
            if (difference < 0)
                nearest = i;
        }
        twice_pivot = {2 * developed[nearest][0], 2 * developed[nearest][1]};
    }
    result.target = piece;
    const PieceFrame quarter{{1, 0}, {-direction, direction}};
    const auto turned = compose_piece_frames(quarter, anchor.frame);
    std::set<std::pair<int, CoordND>> occupied;
    for (std::size_t i = 0; i < developed.size(); ++i) {
        const Point offset{2 * developed[i][0] - twice_pivot[0],
                           2 * developed[i][1] - twice_pivot[1]};
        const Point numerator{twice_pivot[0] + direction * offset[1],
                              twice_pivot[1] - direction * offset[0]};
        if (numerator[0] % 2 || numerator[1] % 2)
            return {std::nullopt, PieceFailure::rotation_undefined};
        // Walk the surface from the anchor to the turned site: axis 0, then axis 1, in the
        // anchor chart's directions transported across every seam the walk crosses.
        PieceCell walker = anchor;
        PieceFrame carried;
        for (int axis = 0; axis < 2; ++axis) {
            const auto distance = numerator[static_cast<std::size_t>(axis)] / 2 -
                                  anchor.coordinate.values[static_cast<std::size_t>(axis)];
            const int sign = distance < 0 ? -1 : 1;
            for (std::int64_t step = 0; step < (distance < 0 ? -distance : distance); ++step) {
                PieceCell next;
                PieceWitness witness;
                const auto moved = step_explorer_cell(
                    piece, walker, apply_piece_frame(carried, {axis, sign}), next, witness);
                if (moved != PieceFailure::none)
                    return {std::nullopt, moved};
                carried = compose_piece_frames(witness.transport, carried);
                walker = std::move(next);
            }
        }
        auto& target = result.target.cells[i];
        target.coordinate = walker.coordinate;
        target.domain = walker.domain;
        target.frame = compose_piece_frames(carried, turned);
        if (!occupied.insert({target.domain, target.coordinate}).second)
            return {std::nullopt, PieceFailure::destination_collision};
    }
    ExplorerPiece checked;
    status = validate_explorer_piece(result.target, checked);
    if (status != PieceFailure::none)
        return {std::nullopt, status};
    result.source_revision = revision;
    result.action = {0, direction};
    result.rotation = true;
    result.classification = classify_piece_correspondence(result.source, result.target);
    result.inverse = {EXPLORER_INVERSE_VERSION, piece, result.action, true};
    return {std::move(result), PieceFailure::none};
}
} // namespace
PieceProposal propose_piece_rotation(const ExplorerPiece& source, std::int64_t revision,
                                     int direction) {
    try {
        return rotate(source, revision, direction);
    } catch (const std::bad_alloc&) {
        return {std::nullopt, PieceFailure::resource_limit};
    } catch (const std::length_error&) {
        return {std::nullopt, PieceFailure::resource_limit};
    }
}
} // namespace tet4d::core
