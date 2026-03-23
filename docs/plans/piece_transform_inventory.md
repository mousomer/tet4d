Role: reference
Status: reference
Source of truth: none
Supersedes: none
Last updated: 2026-03-22

# Piece Transform Inventory

Status: audited on 2026-03-07 against current `master`.

## Canonical owner

### Owner
- `src/tet4d/engine/core/piece_transform.py`

### Owned responsibilities
- block bounds
- local canonical ordering
- local normalization
- 2D block rotation
- ND block rotation in an active plane
- point rotation primitives
- ND rotation plane enumeration
- ND orientation enumeration

## Consumer inventory

### Engine gameplay consumers

1. `src/tet4d/engine/gameplay/pieces2d.py`
   - uses `normalize_blocks_2d`
   - uses `rotate_blocks_2d`
   - imports `rotate_point_2d` only as compatibility exposure
2. `src/tet4d/engine/gameplay/pieces_nd.py`
   - uses `normalize_blocks_nd`
   - uses `rotate_blocks_nd`
   - imports `rotate_point_nd` only as compatibility exposure
3. `src/tet4d/engine/gameplay/rotation_anim.py`
   - uses canonicalized local block geometry for tween endpoints

### Tutorial consumer

1. `src/tet4d/engine/tutorial/setup_apply.py`
   - uses `block_axis_bounds`
   - uses `rotate_blocks_2d`

### AI consumers

1. `src/tet4d/ai/playbot/planner_2d.py`
   - uses `rotate_blocks_2d`
   - uses `canonicalize_blocks_2d`
2. `src/tet4d/ai/playbot/planner_nd_search.py`
   - uses `canonicalize_blocks_nd`
   - uses `enumerate_orientations_nd`
3. `src/tet4d/ai/playbot/planner_nd_core.py`
   - uses `block_axis_bounds`
4. `src/tet4d/ai/playbot/controller.py`
   - uses `canonicalize_blocks_nd`
   - uses `rotate_blocks_nd`

### Compatibility facade consumer

1. `src/tet4d/engine/api.py`
   - re-exports canonical piece-transform helpers
   - does not own transform semantics

## Duplicate-owner audit

### Active duplicate owners found
- none

### Compatibility-only exposures that remain
1. `src/tet4d/engine/api.py`
   - compatibility facade only
2. `src/tet4d/engine/gameplay/pieces2d.py`
   - `rotate_point_2d` import kept only for compatibility exposure
3. `src/tet4d/engine/gameplay/pieces_nd.py`
   - `rotate_point_nd` import kept only for compatibility exposure

These are not alternate owners. They reuse the canonical kernel.

## Consumer call graph summary

1. Gameplay state and piece models depend downward on `engine/core/piece_transform.py`.
2. Tutorial setup depends downward on `engine/core/piece_transform.py`.
3. AI planner/controller depends downward on `engine/core/piece_transform.py`.
4. UI animation depends downward on gameplay state plus canonical transform helpers; it does not define its own transform math.

## Acceptance check

As of this audit, the following are true:
1. All block-rotation, normalization, canonicalization, and ND orientation helpers are engine-core owned.
2. No AI-owned, tutorial-owned, or UI-owned transform implementation remains.
3. The current repo already satisfies the requested extraction ownership model.

## References checked in this audit

- `src/tet4d/engine/core/piece_transform.py`
- `src/tet4d/engine/gameplay/pieces2d.py`
- `src/tet4d/engine/gameplay/pieces_nd.py`
- `src/tet4d/engine/gameplay/rotation_anim.py`
- `src/tet4d/engine/tutorial/setup_apply.py`
- `src/tet4d/ai/playbot/planner_2d.py`
- `src/tet4d/ai/playbot/planner_nd_search.py`
- `src/tet4d/ai/playbot/planner_nd_core.py`
- `src/tet4d/ai/playbot/controller.py`
- `src/tet4d/engine/api.py`
