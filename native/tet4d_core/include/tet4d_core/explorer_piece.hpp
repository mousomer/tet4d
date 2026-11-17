#pragma once

#include "tet4d_core/topology_transport.hpp"

#include <memory>
#include <mutex>
#include <tuple>

namespace tet4d::core {

inline constexpr const char* EXPLORER_PIECE_VERSION = "explorer-piece-transport/1";
inline constexpr const char* EXPLORER_INVERSE_VERSION = "explorer-piece-inverse/1";
inline constexpr const char* EXPLORER_DOMAIN_VERSION = "explorer-piece-domains/2";
inline constexpr std::size_t EXPLORER_MAX_CELLS = 4096;
inline constexpr std::size_t EXPLORER_MAX_UNDO = 4096;

enum class PieceFailure {
    none,
    unsupported_representation,
    invalid_profile,
    invalid_piece_state,
    invalid_action,
    unconnected_boundary,
    destination_collision,
    invalid_transport,
    inverse_mismatch,
    stale_candidate,
    candidate_mismatch,
    resource_limit,
    rotation_undefined
};
const char* piece_failure_name(PieceFailure failure);

struct PieceFrame {
    std::vector<int> permutation{0, 1};
    std::vector<int> signs{1, 1};
    bool operator==(const PieceFrame& other) const {
        return std::tie(permutation, signs) == std::tie(other.permutation, other.signs);
    }
};
struct PieceRestCell {
    std::int64_t id = 0;
    CoordND coordinate;
    bool operator==(const PieceRestCell& other) const {
        return id == other.id && coordinate == other.coordinate;
    }
};
struct PieceCell {
    std::int64_t id = 0;
    int domain = 0;
    CoordND coordinate;
    PieceFrame frame;
    bool operator==(const PieceCell& other) const {
        return std::tie(id, domain, coordinate, frame) ==
               std::tie(other.id, other.domain, other.coordinate, other.frame);
    }
};
// Value-owned semantic state. Input rows may be reordered; validation canonicalizes by ID.
// Original geometry is never inferred from current occupancy or rewritten by an action.
struct ExplorerPiece {
    std::string version = EXPLORER_PIECE_VERSION;
    std::string object_namespace;
    std::int64_t object_ordinal = 0;
    TopologyTransportProfile profile;
    std::vector<PieceRestCell> rest_cells;
    std::vector<PieceCell> cells;
    bool operator==(const ExplorerPiece& other) const;
};
struct PieceInverse {
    std::string version = EXPLORER_INVERSE_VERSION;
    ExplorerPiece source;
    MoveStepQuery forward;
    bool rotation = false;
    bool operator==(const PieceInverse& other) const;
};
struct PieceWitness {
    std::int64_t id = 0;
    CoordND source;
    CoordND target;
    PieceFrame transport;
    MoveStepQuery step;
    MoveStepQuery reverse;
    std::optional<std::string> seam;
    int source_domain = 0;
    int target_domain = 0;
    bool operator==(const PieceWitness& other) const;
};
enum class PieceClassification {
    plain_translation,
    rigid_transform,
    cellwise_deformation,
    blocked
};
struct PieceCandidate {
    std::string version = EXPLORER_PIECE_VERSION;
    std::int64_t source_revision = 0;
    ExplorerPiece source;
    ExplorerPiece target;
    MoveStepQuery action;
    // Forward: derived undo descriptor. Inverse: supplied descriptor and its forward redo action.
    PieceInverse inverse;
    bool is_inverse = false;
    PieceClassification classification = PieceClassification::blocked;
    std::vector<PieceWitness> witnesses;
    bool rotation = false;
    bool operator==(const PieceCandidate& other) const;
};
struct PieceProposal {
    std::optional<PieceCandidate> candidate;
    PieceFailure failure = PieceFailure::none;
};

// No borrowed state escapes. Pure operations validate all input and return no candidate on failure.
// All structurally valid rank-2 profiles supported by the shared decoder are admitted.
// An action is refused only when two cells would share a site (destination_collision) or a cell
// would leave through an unglued edge (unconnected_boundary); no other geometric check applies.
// It is detached Explorer state, never an import into persistent gameplay occupancy.
PieceFailure validate_explorer_piece(const ExplorerPiece& piece, ExplorerPiece& canonical);
bool valid_piece_frame(const PieceFrame& frame);
PieceFrame compose_piece_frames(const PieceFrame& left, const PieceFrame& right);
PieceFrame inverse_piece_frame(const PieceFrame& frame);
// Chart-level label of an ID correspondence; descriptive only, never a reason to refuse.
PieceClassification classify_piece_correspondence(const ExplorerPiece& source,
                                                  const ExplorerPiece& target);
// Chart direction of `step` (given in the frame's source axes) after applying `frame`.
MoveStepQuery apply_piece_frame(const PieceFrame& frame, MoveStepQuery step);
// One unit step of one cell on the surface, carrying its domain and material frame across seams.
PieceFailure step_explorer_cell(const ExplorerPiece& piece, const PieceCell& cell,
                                MoveStepQuery step, PieceCell& next, PieceWitness& witness);
// Rotation-only reference: the cell nearest the material pivot
// (lowest ID on ties). It is where the piece's centre is drawn, so actions read on screen there.
std::size_t explorer_reference_cell(const ExplorerPiece& canonical);
// Every cell receives the same board-axis action; accumulated frames never remap input.
// Deformation is permitted. Undo records the exact source semantic snapshot.
PieceProposal propose_piece_translation(const ExplorerPiece& source, std::int64_t revision,
                                        MoveStepQuery action);
PieceProposal propose_piece_inverse(const ExplorerPiece& current, std::int64_t revision,
                                    const PieceInverse& descriptor);
// 2D quarter turn about the piece's developed pivot, as seen in the reference cell's frame. Each
// cell reaches its turned site by walking the surface from that cell; direction is -1 or +1.
// No wall kicks. Undo restores the recorded source exactly.
PieceProposal propose_piece_rotation(const ExplorerPiece& source, std::int64_t revision,
                                    int direction);
// Pure per-ID single-cell neighbor query, retaining domain and frame correspondence.
PieceProposal propose_piece_neighbor(const ExplorerPiece& source, std::int64_t id,
                                    MoveStepQuery action);

struct PieceEnvelope {
    std::int64_t revision = 0;
    ExplorerPiece piece;
    ExplorerPiece initial_piece;
    std::vector<PieceInverse> undo;
    bool operator==(const PieceEnvelope& other) const;
};
// Candidate implementation, no authority transfer. One owner serializes every apply/Retry and
// snapshot with a mutex. Constructor takes an owned envelope (including restored sessions);
// apply/Retry revalidate it. No pointers/references into the envelope are exposed. Undo baseline
// is empty; no diagnostic trace is retained in T2A. Failure leaves the entire envelope intact.
class ExplorerPieceRuntime {
  public:
    explicit ExplorerPieceRuntime(PieceEnvelope envelope);
    PieceEnvelope snapshot() const;
    PieceFailure apply(const PieceCandidate& candidate);
    PieceFailure retry();

  private:
    mutable std::mutex mutex_;
    std::unique_ptr<PieceEnvelope> state_;
};

} // namespace tet4d::core
