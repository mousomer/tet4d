#include "tet4d_core/explorer_piece.hpp"

#include <algorithm>
#include <array>
#include <limits>
#include <set>
#include <stdexcept>

namespace tet4d::core {
namespace {
PieceProposal failure(PieceFailure reason) {
    return {std::nullopt, reason};
}

PieceFailure step_cells(const ExplorerPiece& source, const std::vector<MoveStepQuery>& steps,
                        ExplorerPiece& target, std::vector<PieceWitness>& witnesses) {
    target = source;
    std::set<std::pair<int, CoordND>> destinations;
    for (std::size_t i = 0; i < source.cells.size(); ++i) {
        PieceWitness witness;
        const auto status =
            step_explorer_cell(source, source.cells[i], steps[i], target.cells[i], witness);
        if (status != PieceFailure::none)
            return status;
        witnesses.push_back(std::move(witness));
        // Injectivity is the only occupancy rule: two cells never share one surface site.
        if (!destinations.insert({target.cells[i].domain, target.cells[i].coordinate}).second)
            return PieceFailure::destination_collision;
    }
    ExplorerPiece checked;
    const auto valid = validate_explorer_piece(target, checked);
    if (valid != PieceFailure::none)
        return valid == PieceFailure::resource_limit ? valid : PieceFailure::invalid_transport;
    return PieceFailure::none;
}
PieceProposal translate(const ExplorerPiece& source, std::int64_t revision, MoveStepQuery action) {
    PieceCandidate candidate;
    auto status = validate_explorer_piece(source, candidate.source);
    if (status != PieceFailure::none)
        return failure(status);
    if (action.axis < 0 || action.axis >= 2 || (action.delta != -1 && action.delta != 1))
        return failure(PieceFailure::invalid_action);
    if (revision < 0)
        return failure(PieceFailure::invalid_piece_state);
    if (revision == std::numeric_limits<std::int64_t>::max())
        return failure(PieceFailure::resource_limit);
    candidate.source_revision = revision;
    candidate.action = action;
    // Board-axis input is identical for every cell. Frames carry orientation only.
    const std::vector<MoveStepQuery> steps(candidate.source.cells.size(), action);
    status = step_cells(candidate.source, steps, candidate.target, candidate.witnesses);
    if (status != PieceFailure::none)
        return failure(status);
    candidate.classification = classify_piece_correspondence(candidate.source, candidate.target);
    candidate.inverse = {EXPLORER_INVERSE_VERSION, candidate.source, action};
    return {std::move(candidate), PieceFailure::none};
}
PieceProposal inverse(const ExplorerPiece& current, std::int64_t revision,
                      const PieceInverse& descriptor) {
    if (descriptor.version != EXPLORER_INVERSE_VERSION)
        return failure(PieceFailure::unsupported_representation);
    ExplorerPiece source;
    auto status = validate_explorer_piece(current, source);
    if (status != PieceFailure::none)
        return failure(status);
    // Reconstruct descriptor provenance using production forward transport; no trusted snapshots.
    auto forward = descriptor.rotation ? propose_piece_rotation(descriptor.source, revision,
                                                                descriptor.forward.delta)
                                       : translate(descriptor.source, revision, descriptor.forward);
    if (!forward.candidate)
        return forward;
    if (!(forward.candidate->target == source))
        return failure(PieceFailure::inverse_mismatch);
    PieceCandidate result;
    result.source_revision = revision;
    result.source = std::move(source);
    result.action = descriptor.forward;
    result.inverse = forward.candidate->inverse;
    result.is_inverse = true;
    result.rotation = descriptor.rotation;
    // The source-bound forward candidate was recomputed and matched in full, so Undo restores
    // the recorded source exactly; it never re-derives the source by stepping backwards.
    result.target = forward.candidate->source;
    result.classification = classify_piece_correspondence(result.source, result.target);
    return {std::move(result), PieceFailure::none};
}
} // namespace

PieceClassification classify_piece_correspondence(const ExplorerPiece& source,
                                                  const ExplorerPiece& target) {
    PieceFrame common;
    std::array<std::int64_t, 2> displacement{};
    for (std::size_t i = 0; i < source.cells.size(); ++i) {
        const auto& from = source.cells[i];
        const auto& to = target.cells[i];
        auto relative = compose_piece_frames(to.frame, inverse_piece_frame(from.frame));
        std::array<std::int64_t, 2> shift{to.coordinate.values[0], to.coordinate.values[1]};
        for (std::size_t j = 0; j < 2; ++j)
            shift[static_cast<std::size_t>(relative.permutation[j])] -=
                static_cast<std::int64_t>(relative.signs[j]) * from.coordinate.values[j];
        for (const auto& seam : source.profile.seams) {
            // Individually eligible periods, independently of how this action crossed the chart.
            if (!seam.enabled || seam.source.axis != seam.target.axis ||
                seam.source.side == seam.target.side ||
                seam.transform.permutation != std::vector<std::int64_t>{0} ||
                seam.transform.signs != std::vector<std::int64_t>{1})
                continue;
            const auto axis = static_cast<std::size_t>(seam.source.axis);
            const auto extent = source.profile.dimensions[axis];
            shift[axis] = (shift[axis] % extent + extent) % extent;
        }
        if (from.domain != to.domain)
            return PieceClassification::cellwise_deformation;
        if (i == 0) {
            common = relative;
            displacement = shift;
        } else if (!(relative == common) || shift != displacement)
            return PieceClassification::cellwise_deformation;
    }
    return common == PieceFrame{} ? PieceClassification::plain_translation
                                  : PieceClassification::rigid_transform;
}
std::size_t explorer_reference_cell(const ExplorerPiece& canonical) {
    // The material pivot of propose_piece_rotation, computed on immutable rest geometry so the
    // reference never depends on where the cells currently sit.
    const auto& rest = canonical.rest_cells;
    std::array<std::int64_t, 2> low{}, high{}, sum{};
    for (std::size_t i = 0; i < rest.size(); ++i)
        for (std::size_t axis = 0; axis < 2; ++axis) {
            const std::int64_t value = rest[i].coordinate.values[axis];
            low[axis] = i == 0 ? value : std::min(low[axis], value);
            high[axis] = i == 0 ? value : std::max(high[axis], value);
            sum[axis] += value;
        }
    if ((high[0] - low[0]) % 2 != (high[1] - low[1]) % 2) {
        std::size_t nearest = 0;
        const auto count = static_cast<std::int64_t>(rest.size());
        for (std::size_t i = 1; i < rest.size(); ++i) {
            std::int64_t difference = 0;
            for (std::size_t axis = 0; axis < 2; ++axis) {
                const std::int64_t a = rest[i].coordinate.values[axis];
                const std::int64_t b = rest[nearest].coordinate.values[axis];
                difference += (a - b) * (count * (a + b) - 2 * sum[axis]);
            }
            if (difference < 0)
                nearest = i;
        }
        return nearest; // The pivot is this cell's centre.
    }
    std::size_t best = 0;
    std::int64_t best_distance = std::numeric_limits<std::int64_t>::max();
    for (std::size_t i = 0; i < rest.size(); ++i) {
        std::int64_t distance = 0;
        for (std::size_t axis = 0; axis < 2; ++axis) {
            const auto offset = 2 * static_cast<std::int64_t>(rest[i].coordinate.values[axis]) -
                                (low[axis] + high[axis]);
            distance += offset * offset;
        }
        if (distance < best_distance) {
            best = i;
            best_distance = distance;
        }
    }
    return best;
}
MoveStepQuery apply_piece_frame(const PieceFrame& frame, MoveStepQuery step) {
    const auto axis = static_cast<std::size_t>(step.axis);
    return {frame.permutation[axis], frame.signs[axis] * step.delta};
}
PieceFailure step_explorer_cell(const ExplorerPiece& piece, const PieceCell& cell,
                                MoveStepQuery step, PieceCell& next, PieceWitness& witness) {
    const auto profile = topology_query_profile_from_transport(piece.profile);
    const BoardShapeND board{{static_cast<int>(piece.profile.dimensions[0]),
                              static_cast<int>(piece.profile.dimensions[1])}};
    auto resolved = resolve_topology_cell_step_query(profile, board, cell.coordinate, step);
    int target_domain = cell.domain;
    if (resolved.ok && !resolved.target && piece.version == EXPLORER_DOMAIN_VERSION) {
        // The spherical double joins identical complete boundaries of two disk charts.
        resolved.target = cell.coordinate;
        target_domain = 1 - cell.domain;
        PieceFrame reflected;
        reflected.signs[static_cast<std::size_t>(step.axis)] = -1;
        resolved.piece_frame_transform =
            TopologyFrameQueryTransform{reflected.permutation, reflected.signs, {{0, 0}}};
        resolved.glue_id = "double_" + std::to_string(step.axis) + (step.delta < 0 ? "-" : "+");
    }
    if (!resolved.ok)
        return PieceFailure::invalid_transport;
    if (!resolved.target)
        return PieceFailure::unconnected_boundary;
    PieceFrame transport;
    if (resolved.piece_frame_transform)
        transport = {resolved.piece_frame_transform->permutation,
                     resolved.piece_frame_transform->signs};
    else if (resolved.glue_id)
        return PieceFailure::invalid_transport;
    if (!valid_piece_frame(transport))
        return PieceFailure::invalid_transport;
    next = cell;
    next.coordinate = *resolved.target;
    next.domain = target_domain;
    next.frame = compose_piece_frames(transport, cell.frame);
    // r_i = -T_i a: each cell has its own physical reverse direction.
    auto reverse = apply_piece_frame(transport, step);
    reverse.delta = -reverse.delta;
    witness = {cell.id, cell.coordinate,  next.coordinate, transport,    step,
               reverse, resolved.glue_id, cell.domain,     target_domain};
    return PieceFailure::none;
}

PieceProposal propose_piece_translation(const ExplorerPiece& source, std::int64_t revision,
                                        MoveStepQuery action) {
    try {
        return translate(source, revision, action);
    } catch (const std::bad_alloc&) {
        return failure(PieceFailure::resource_limit);
    } catch (const std::length_error&) {
        return failure(PieceFailure::resource_limit);
    }
}
PieceProposal propose_piece_neighbor(const ExplorerPiece& source, std::int64_t id,
                                     MoveStepQuery action) {
    ExplorerPiece canonical;
    auto status = validate_explorer_piece(source, canonical);
    if (status != PieceFailure::none)
        return failure(status);
    if (id < 0 || static_cast<std::size_t>(id) >= canonical.cells.size())
        return failure(PieceFailure::invalid_action);
    // One-cell probe keeps the selected ID's material frame and domain; it never commits.
    const auto cell = canonical.cells[static_cast<std::size_t>(id)];
    canonical.rest_cells = {{0, {{0, 0}}}};
    canonical.cells = {cell};
    canonical.cells.front().id = 0;
    return propose_piece_translation(canonical, 0, action);
}
PieceProposal propose_piece_inverse(const ExplorerPiece& current, std::int64_t revision,
                                    const PieceInverse& descriptor) {
    try {
        return inverse(current, revision, descriptor);
    } catch (const std::bad_alloc&) {
        return failure(PieceFailure::resource_limit);
    } catch (const std::length_error&) {
        return failure(PieceFailure::resource_limit);
    }
}
} // namespace tet4d::core
