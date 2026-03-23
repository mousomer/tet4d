Role: reference
Status: reference
Source of truth: none
Supersedes: none
Last updated: 2026-03-22

# Piece Transform Extraction

Status: implemented historically on 2026-03-05; documented explicitly on 2026-03-07.

## Objective

Record the completed extraction of piece-local transform semantics into one canonical engine-core owner and lock the intended ownership model.

Canonical owner:
- `src/tet4d/engine/core/piece_transform.py`

## Scope

In scope:
- piece-local rotation
- piece-local translation helpers
- local normalization / canonicalization
- orientation equality / canonical ordering helpers
- active-plane ND transform helpers

Out of scope:
- collision detection
- topology / wrap / invert behavior
- wall kicks
- spawn rules
- lock / scoring
- menu / input / render policy
- packaging / governance cleanup

## Historical Stage Contract

The original extraction task had one critical non-goal:
- no semantic change during extraction

That extraction stage is already complete and is recorded in `docs/BACKLOG.md` under:
- `Current sub-batch (2026-03-05): canonical piece-transform extraction (no behavior change).`

Important current-state note:
- Current `HEAD` has already completed the later follow-up semantic swap to center-of-piece rotation semantics.
- So this document is a retrospective record of the extraction stage and current ownership, not a request to revert current semantics.

## Stage Mapping

### Stage 0 - Freeze behavior

Completed historically.

Recorded evidence:
- `docs/BACKLOG.md` notes the extraction batch as no-behavior-change.
- `tests/unit/engine/test_piece_transform.py` provides the kernel contract now used as the canonical regression anchor.

### Stage 1 - Inventory owners and consumers

Completed and documented in:
- `docs/plans/piece_transform_inventory.md`

### Stage 2 - Create the canonical kernel

Completed.

Owner:
- `src/tet4d/engine/core/piece_transform.py`

Canonical exported surface currently includes:
- `block_axis_bounds`
- `canonicalize_blocks_2d`
- `canonicalize_blocks_nd`
- `enumerate_orientations_nd`
- `normalize_blocks_2d`
- `normalize_blocks_nd`
- `rotate_blocks_2d`
- `rotate_blocks_nd`
- `rotate_point_2d`
- `rotate_point_nd`
- `rotation_planes_nd`

### Stage 3 - Migrate engine gameplay first

Completed.

Gameplay consumers:
- `src/tet4d/engine/gameplay/pieces2d.py`
- `src/tet4d/engine/gameplay/pieces_nd.py`
- `src/tet4d/engine/gameplay/rotation_anim.py`

### Stage 4 - Migrate non-engine consumers

Completed.

Non-engine / non-gameplay consumers:
- `src/tet4d/engine/tutorial/setup_apply.py`
- `src/tet4d/ai/playbot/planner_2d.py`
- `src/tet4d/ai/playbot/planner_nd_search.py`
- `src/tet4d/ai/playbot/planner_nd_core.py`
- `src/tet4d/ai/playbot/controller.py`
- `src/tet4d/engine/api.py` (compatibility re-export surface)

### Stage 5 - Equivalence verification

Completed for the extraction batch historically, then superseded by the later center-of-piece semantic change.

Current regression coverage for the canonical owner is in:
- `tests/unit/engine/test_piece_transform.py`

Current higher-level coverage using the same owner includes:
- `tests/unit/engine/test_peces_2d.py`
- `tests/unit/engine/test_game2d.py`
- `tests/unit/engine/test_game_nd.py`

### Stage 6 - Delete duplicates

Completed in practical ownership terms.

Result:
- exactly one canonical owner remains for piece-local transform semantics
- remaining compatibility exposures are re-exports only, not alternate owners

## Acceptance

Accepted current-state conditions:
1. One canonical piece-transform owner exists in engine core.
2. Gameplay, AI, tutorial setup, and animation consume that owner.
3. No independent transform owner remains outside `src/tet4d/engine/core/piece_transform.py`.
4. Current architecture docs point at the canonical owner.

## Evidence

Primary code references:
- `src/tet4d/engine/core/piece_transform.py`
- `src/tet4d/engine/gameplay/pieces2d.py`
- `src/tet4d/engine/gameplay/pieces_nd.py`
- `src/tet4d/engine/gameplay/rotation_anim.py`
- `src/tet4d/engine/tutorial/setup_apply.py`
- `src/tet4d/ai/playbot/planner_2d.py`
- `src/tet4d/ai/playbot/planner_nd_search.py`
- `src/tet4d/ai/playbot/controller.py`

Primary maintenance references:
- `docs/BACKLOG.md`
- `docs/ARCHITECTURE_CONTRACT.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/rds/RDS_TETRIS_GENERAL.md`
