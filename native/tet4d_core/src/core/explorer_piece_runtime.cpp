#include "tet4d_core/explorer_piece.hpp"

#include <limits>
#include <stdexcept>

namespace tet4d::core {
namespace {
PieceFailure validate_envelope(const PieceEnvelope& state, ExplorerPiece& current,
                               ExplorerPiece& initial) {
    if (state.revision < 0)
        return PieceFailure::invalid_piece_state;
    if (state.revision == std::numeric_limits<std::int64_t>::max() ||
        state.undo.size() > EXPLORER_MAX_UNDO)
        return PieceFailure::resource_limit;
    auto status = validate_explorer_piece(state.piece, current);
    if (status != PieceFailure::none)
        return status;
    status = validate_explorer_piece(state.initial_piece, initial);
    if (status != PieceFailure::none)
        return status;
    auto baseline = initial;
    baseline.cells = current.cells;
    if (!(baseline == current))
        return PieceFailure::invalid_piece_state;
    return PieceFailure::none;
}
} // namespace

ExplorerPieceRuntime::ExplorerPieceRuntime(PieceEnvelope envelope)
    : state_(std::make_unique<PieceEnvelope>(std::move(envelope))) {}

PieceEnvelope ExplorerPieceRuntime::snapshot() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return *state_;
}
PieceFailure ExplorerPieceRuntime::apply(const PieceCandidate& candidate) {
    std::lock_guard<std::mutex> lock(mutex_);
    try {
        if (candidate.version != EXPLORER_PIECE_VERSION)
            return PieceFailure::unsupported_representation;
        if (candidate.source_revision != state_->revision)
            return PieceFailure::stale_candidate;
        ExplorerPiece current, initial;
        auto status = validate_envelope(*state_, current, initial);
        if (status != PieceFailure::none)
            return status;
        if (!(candidate.source == current))
            return PieceFailure::stale_candidate;
        auto recomputed =
            candidate.is_inverse
                ? propose_piece_inverse(current, state_->revision, candidate.inverse)
                : propose_piece_translation(current, state_->revision, candidate.action);
        if (!recomputed.candidate)
            return recomputed.failure == PieceFailure::resource_limit
                       ? recomputed.failure
                       : PieceFailure::candidate_mismatch;
        if (!(candidate == *recomputed.candidate))
            return PieceFailure::candidate_mismatch;
        if (!candidate.is_inverse && state_->undo.size() == EXPLORER_MAX_UNDO)
            return PieceFailure::resource_limit;
        auto next = std::make_unique<PieceEnvelope>(*state_);
        next->piece = recomputed.candidate->target;
        ++next->revision;
        if (candidate.is_inverse) {
            // Descriptors remain usable independently of optional retained history.
            if (!next->undo.empty() && next->undo.back() == candidate.inverse)
                next->undo.pop_back();
        } else
            next->undo.push_back(recomputed.candidate->inverse);
        state_.swap(next); // noexcept publication under the same serialized mutation boundary.
        return PieceFailure::none;
    } catch (const std::bad_alloc&) {
        return PieceFailure::resource_limit;
    } catch (const std::length_error&) {
        return PieceFailure::resource_limit;
    }
}
PieceFailure ExplorerPieceRuntime::retry() {
    std::lock_guard<std::mutex> lock(mutex_);
    try {
        ExplorerPiece current, initial;
        auto status = validate_envelope(*state_, current, initial);
        if (status != PieceFailure::none)
            return status;
        auto next = std::make_unique<PieceEnvelope>(*state_);
        next->piece = std::move(initial);
        next->undo.clear();
        ++next->revision;
        state_.swap(next);
        return PieceFailure::none;
    } catch (const std::bad_alloc&) {
        return PieceFailure::resource_limit;
    } catch (const std::length_error&) {
        return PieceFailure::resource_limit;
    }
}
} // namespace tet4d::core
