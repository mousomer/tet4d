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
    const auto profile = topology_query_profile_from_transport(source.profile);
    const BoardShapeND board{{static_cast<int>(source.profile.dimensions[0]),
                              static_cast<int>(source.profile.dimensions[1])}};
    std::set<CoordND> destinations;
    for (std::size_t i = 0; i < source.cells.size(); ++i) {
        const auto& cell = source.cells[i];
        const auto step = steps[i];
        const auto resolved =
            resolve_topology_cell_step_query(profile, board, cell.coordinate, step);
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
        auto& next = target.cells[i];
        next.coordinate = *resolved.target;
        next.frame = compose_piece_frames(transport, cell.frame);
        // r_i = -T_i a: each cell has its own physical reverse direction.
        const auto axis = static_cast<std::size_t>(step.axis);
        MoveStepQuery reverse{transport.permutation[axis], -transport.signs[axis] * step.delta};
        witnesses.push_back({cell.id, cell.coordinate, next.coordinate, transport, step, reverse,
                             resolved.glue_id});
        if (!destinations.insert(next.coordinate).second)
            return PieceFailure::destination_collision;
    }
    ExplorerPiece checked;
    const auto valid = validate_explorer_piece(target, checked);
    if (valid != PieceFailure::none)
        return valid == PieceFailure::resource_limit ? valid : PieceFailure::invalid_transport;
    return PieceFailure::none;
}
std::vector<MoveStepQuery> reverse_steps(const std::vector<PieceWitness>& witnesses) {
    std::vector<MoveStepQuery> steps;
    for (const auto& witness : witnesses)
        steps.push_back(witness.reverse);
    return steps;
}
PieceClassification classify(const ExplorerPiece& source, const ExplorerPiece& target) {
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
        if (i == 0) {
            common = relative;
            displacement = shift;
        } else if (!(relative == common) || shift != displacement)
            return PieceClassification::cellwise_deformation;
    }
    return common == PieceFrame{} ? PieceClassification::plain_translation
                                  : PieceClassification::rigid_transform;
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
    status = step_cells(candidate.source, std::vector<MoveStepQuery>(source.cells.size(), action),
                        candidate.target, candidate.witnesses);
    if (status != PieceFailure::none)
        return failure(status);
    ExplorerPiece recovered;
    std::vector<PieceWitness> backwards;
    status = step_cells(candidate.target, reverse_steps(candidate.witnesses), recovered, backwards);
    if (status != PieceFailure::none)
        return failure(status);
    if (!(recovered == candidate.source))
        return failure(PieceFailure::inverse_mismatch);
    for (std::size_t i = 0; i < backwards.size(); ++i)
        if (!(backwards[i].transport == inverse_piece_frame(candidate.witnesses[i].transport)))
            return failure(PieceFailure::inverse_mismatch);
    candidate.classification = classify(candidate.source, candidate.target);
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
    auto forward = translate(descriptor.source, revision, descriptor.forward);
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
    status = step_cells(result.source, reverse_steps(forward.candidate->witnesses), result.target,
                        result.witnesses);
    if (status != PieceFailure::none)
        return failure(status);
    if (!(result.target == result.inverse.source))
        return failure(PieceFailure::inverse_mismatch);
    result.classification = classify(result.source, result.target);
    return {std::move(result), PieceFailure::none};
}
} // namespace

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
