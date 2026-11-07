#include "tet4d_core/explorer_piece.hpp"
#include "tet4d_core/generated/topology_contract_v1.hpp"

#include <algorithm>
#include <array>
#include <limits>
#include <set>
#include <stdexcept>

namespace tet4d::core {
namespace {
bool same_profile(const TopologyTransportProfile& a, const TopologyTransportProfile& b) {
    if (std::tie(a.contract_version, a.rank, a.dimensions) !=
            std::tie(b.contract_version, b.rank, b.dimensions) ||
        a.seams.size() != b.seams.size())
        return false;
    for (std::size_t i = 0; i < a.seams.size(); ++i) {
        const auto& x = a.seams[i];
        const auto& y = b.seams[i];
        if (std::tie(x.id, x.source.axis, x.source.side, x.target.axis, x.target.side,
                     x.transform.permutation, x.transform.signs, x.enabled) !=
            std::tie(y.id, y.source.axis, y.source.side, y.target.axis, y.target.side,
                     y.transform.permutation, y.transform.signs, y.enabled))
            return false;
    }
    return true;
}
TransportValue integers(const std::vector<std::int64_t>& values) {
    TransportValue::Array rows;
    for (auto value : values)
        rows.emplace_back(value);
    return TransportValue(std::move(rows));
}
TransportValue boundary(const TopologyTransportBoundary& value) {
    // Invalid axis values remain invalid decoder inputs; never narrow or index them unchecked.
    const auto axis =
        value.axis >= 0 && value.axis < static_cast<std::int64_t>(generated::AXIS_NAMES.size())
            ? std::string(generated::AXIS_NAMES[static_cast<std::size_t>(value.axis)])
            : "invalid";
    return TransportValue(TransportValue::Object{{"axis", TransportValue(axis)},
                                                 {"side", TransportValue(value.side)}});
}
PieceFailure canonical_profile(const TopologyTransportProfile& source,
                               TopologyTransportProfile& result) {
    if (source.contract_version != generated::CONTRACT_VERSION || source.rank != 2)
        return PieceFailure::unsupported_representation;
    if (source.seams.size() > 64)
        return PieceFailure::resource_limit;
    TransportValue::Array seams;
    for (const auto& seam : source.seams) {
        seams.emplace_back(TransportValue::Object{
            {"id", TransportValue(seam.id)},
            {"source", boundary(seam.source)},
            {"target", boundary(seam.target)},
            {"enabled", TransportValue(seam.enabled)},
            {"transform", TransportValue(TransportValue::Object{
                              {"permutation", integers(seam.transform.permutation)},
                              {"signs", integers(seam.transform.signs)}})}});
    }
    const auto decoded = decode_topology_transport_profile(TransportValue(
        TransportValue::Object{{"contract_version", TransportValue(source.contract_version)},
                               {"rank", TransportValue(source.rank)},
                               {"dimensions", integers(source.dimensions)},
                               {"seams", TransportValue(std::move(seams))}}));
    if (!decoded.ok())
        return PieceFailure::invalid_profile;
    result = *decoded.value;
    result.seams.clear();
    // T2A admits bounded/cylinder/torus. This is admission and canonical v1 normalization,
    // never a transport solver. Pure-wrap inverse tangents are the same identity transform.
    std::array<bool, 2> wrapped{false, false};
    for (const auto& seam : decoded.value->seams) {
        if (!seam.enabled)
            continue;
        if (seam.source.axis != seam.target.axis || seam.source.side == seam.target.side ||
            seam.transform.permutation != std::vector<std::int64_t>{0} ||
            seam.transform.signs != std::vector<std::int64_t>{1})
            return PieceFailure::unsupported_representation;
        wrapped[static_cast<std::size_t>(seam.source.axis)] = true;
    }
    for (std::int64_t axis = 0; axis < 2; ++axis) {
        if (wrapped[static_cast<std::size_t>(axis)])
            result.seams.push_back({result.seams.empty() ? "seam_000" : "seam_001",
                                    {axis, "-"},
                                    {axis, "+"},
                                    {{0}, {1}},
                                    true});
    }
    return PieceFailure::none;
}
template <typename T> void sort_ids(std::vector<T>& rows) {
    std::sort(rows.begin(), rows.end(), [](const T& a, const T& b) { return a.id < b.id; });
}
PieceFailure validate(const ExplorerPiece& source, ExplorerPiece& result) {
    if (source.version != EXPLORER_PIECE_VERSION)
        return PieceFailure::unsupported_representation;
    if (source.cells.size() > EXPLORER_MAX_CELLS || source.rest_cells.size() > EXPLORER_MAX_CELLS)
        return PieceFailure::resource_limit;
    TopologyTransportProfile profile;
    const auto status = canonical_profile(source.profile, profile);
    if (status != PieceFailure::none)
        return status;
    if (source.object_namespace.size() != 32 || source.object_ordinal < 0 ||
        source.object_namespace.find_first_not_of("0123456789abcdef") != std::string::npos ||
        source.cells.empty() || source.cells.size() != source.rest_cells.size() ||
        source.cells.size() >
            static_cast<std::uint64_t>(profile.dimensions[0] * profile.dimensions[1]))
        return PieceFailure::invalid_piece_state;
    ExplorerPiece canonical = source;
    canonical.profile = std::move(profile);
    sort_ids(canonical.cells);
    sort_ids(canonical.rest_cells);
    std::set<CoordND> rest, occupied;
    std::array<int, 2> mins{std::numeric_limits<int>::max(), std::numeric_limits<int>::max()};
    for (std::size_t i = 0; i < canonical.cells.size(); ++i) {
        const auto& cell = canonical.cells[i];
        const auto& original = canonical.rest_cells[i];
        if (cell.domain != 0)
            return PieceFailure::unsupported_representation;
        if (cell.id != static_cast<std::int64_t>(i) || original.id != cell.id ||
            cell.coordinate.dimension() != 2 || original.coordinate.dimension() != 2 ||
            !valid_piece_frame(cell.frame) || !rest.insert(original.coordinate).second ||
            !occupied.insert(cell.coordinate).second)
            return PieceFailure::invalid_piece_state;
        if (i > 0 && !(canonical.rest_cells[i - 1].coordinate < original.coordinate))
            return PieceFailure::invalid_piece_state;
        for (std::size_t axis = 0; axis < 2; ++axis) {
            if (cell.coordinate.values[axis] < 0 ||
                cell.coordinate.values[axis] >= canonical.profile.dimensions[axis] ||
                original.coordinate.values[axis] < 0 ||
                original.coordinate.values[axis] >= generated::MAXIMUM_AXIS_LENGTH)
                return PieceFailure::invalid_piece_state;
            mins[axis] = std::min(mins[axis], original.coordinate.values[axis]);
        }
    }
    if (mins != std::array<int, 2>{0, 0})
        return PieceFailure::invalid_piece_state;
    // Connectivity is required only for immutable original geometry, never for current cells.
    std::vector<CoordND> frontier{canonical.rest_cells.front().coordinate};
    rest.erase(frontier.front());
    for (std::size_t i = 0; i < frontier.size(); ++i) {
        for (std::size_t axis = 0; axis < 2; ++axis)
            for (int delta : {-1, 1}) {
                auto neighbor = frontier[i];
                neighbor.values[axis] += delta;
                if (rest.erase(neighbor))
                    frontier.push_back(std::move(neighbor));
            }
    }
    if (!rest.empty())
        return PieceFailure::invalid_piece_state;
    result = std::move(canonical);
    return PieceFailure::none;
}
} // namespace

const char* piece_failure_name(PieceFailure failure) {
    switch (failure) {
    case PieceFailure::none:
        return "";
    case PieceFailure::unsupported_representation:
        return "unsupported_representation";
    case PieceFailure::invalid_profile:
        return "invalid_profile";
    case PieceFailure::invalid_piece_state:
        return "invalid_piece_state";
    case PieceFailure::invalid_action:
        return "invalid_action";
    case PieceFailure::unconnected_boundary:
        return "unconnected_boundary";
    case PieceFailure::destination_collision:
        return "destination_collision";
    case PieceFailure::invalid_transport:
        return "invalid_transport";
    case PieceFailure::inverse_mismatch:
        return "inverse_mismatch";
    case PieceFailure::stale_candidate:
        return "stale_candidate";
    case PieceFailure::candidate_mismatch:
        return "candidate_mismatch";
    case PieceFailure::resource_limit:
        return "resource_limit";
    }
    return "unsupported_representation";
}
bool valid_piece_frame(const PieceFrame& frame) {
    return (frame.permutation == std::vector<int>{0, 1} ||
            frame.permutation == std::vector<int>{1, 0}) &&
           frame.signs.size() == 2 && (frame.signs[0] == -1 || frame.signs[0] == 1) &&
           (frame.signs[1] == -1 || frame.signs[1] == 1);
}
PieceFrame compose_piece_frames(const PieceFrame& left, const PieceFrame& right) {
    if (!valid_piece_frame(left) || !valid_piece_frame(right))
        return {{}, {}};
    PieceFrame result;
    for (std::size_t j = 0; j < 2; ++j) {
        const auto k = static_cast<std::size_t>(right.permutation[j]);
        result.permutation[j] = left.permutation[k];
        result.signs[j] = right.signs[j] * left.signs[k];
    }
    return result;
}
PieceFrame inverse_piece_frame(const PieceFrame& frame) {
    if (!valid_piece_frame(frame))
        return {{}, {}};
    PieceFrame result;
    for (std::size_t j = 0; j < 2; ++j) {
        const auto k = static_cast<std::size_t>(frame.permutation[j]);
        result.permutation[k] = static_cast<int>(j);
        result.signs[k] = frame.signs[j];
    }
    return result;
}
PieceFailure validate_explorer_piece(const ExplorerPiece& piece, ExplorerPiece& canonical) {
    try {
        return validate(piece, canonical);
    } catch (const std::bad_alloc&) {
        return PieceFailure::resource_limit;
    } catch (const std::length_error&) {
        return PieceFailure::resource_limit;
    }
}
bool ExplorerPiece::operator==(const ExplorerPiece& other) const {
    // Exact canonical value equality; callers canonicalize admitted inputs, never coordinate-sort
    // IDs.
    return std::tie(version, object_namespace, object_ordinal, rest_cells, cells) ==
               std::tie(other.version, other.object_namespace, other.object_ordinal,
                        other.rest_cells, other.cells) &&
           same_profile(profile, other.profile);
}
bool PieceInverse::operator==(const PieceInverse& other) const {
    return version == other.version && source == other.source &&
           forward.axis == other.forward.axis && forward.delta == other.forward.delta;
}
bool PieceWitness::operator==(const PieceWitness& other) const {
    return std::tie(id, source, target, transport, step.axis, step.delta, reverse.axis,
                    reverse.delta, seam) ==
           std::tie(other.id, other.source, other.target, other.transport, other.step.axis,
                    other.step.delta, other.reverse.axis, other.reverse.delta, other.seam);
}
bool PieceCandidate::operator==(const PieceCandidate& other) const {
    return std::tie(version, source_revision, source, target, action.axis, action.delta, inverse,
                    is_inverse, classification, witnesses) ==
           std::tie(other.version, other.source_revision, other.source, other.target,
                    other.action.axis, other.action.delta, other.inverse, other.is_inverse,
                    other.classification, other.witnesses);
}
bool PieceEnvelope::operator==(const PieceEnvelope& other) const {
    return std::tie(revision, piece, initial_piece, undo) ==
           std::tie(other.revision, other.piece, other.initial_piece, other.undo);
}
} // namespace tet4d::core
