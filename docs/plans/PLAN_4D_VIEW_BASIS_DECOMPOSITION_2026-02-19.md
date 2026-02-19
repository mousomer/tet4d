# Plan: 4D View Basis Decomposition (`xw` / `zw`)

Date: 2026-02-19  
Status: Completed

## Problem

Current 4D render behavior applies `xw`/`zw` as point-space view transforms and panel reordering, but keeps board decomposition fixed as:

- layer axis: `w`
- board dims: `(x,y,z)`
- layer count: `W`

This does not satisfy expected axis-swap behavior.

## Target Behavior

Discrete quarter-turn view controls must update rendered board decomposition:

1. Identity:
- layer axis=`w`
- board dims=`(x,y,z)`
- layer count=`W`
2. `xw` quarter-turn:
- layer axis=`x`
- board dims=`(w,y,z)`
- layer count=`X`
3. `zw` quarter-turn:
- layer axis=`z`
- board dims=`(x,y,w)`
- layer count=`Z`

Example invariant:
- dims `(5,4,3,2)` + `xw` => `5` boards of `(2,4,3)`.

## Implementation Approach

1. Introduce a discrete signed-axis 4D basis helper in renderer.
2. Build basis from snapped quarter-turn counts for `xw` and `zw`.
3. Derive:
- active layer axis and layer count,
- board-local 3D dimensions,
- mapping from 4D board coords to `(layer_index, cell3)`.
4. Route all per-layer render paths through this mapping:
- locked cells,
- active/overlay cells,
- helper marks,
- clear-animation ghost cells,
- grid/shadow and projection cache keys.
5. Keep gameplay state unchanged (render-only).

## Test Plan

1. Basis decomposition checks for dims `(5,4,3,2)`:
- `xw`: layer_count `5`, board dims `(2,4,3)`.
- `zw`: layer_count `3`, board dims `(5,4,2)`.
2. Mapping invariants:
- every valid 4D coord maps to in-bounds `(layer,cell3)`,
- no collisions in mapping for a fixed basis.
3. Existing 4D render regressions remain green.

## Completion Notes

1. Implemented in:
- `tetris_nd/front4d_render.py`
2. Added/updated regressions in:
- `tetris_nd/tests/test_front4d_render.py`
3. Verified:
- `ruff check tetris_nd/front4d_render.py tetris_nd/tests/test_front4d_render.py`
- `pytest -q tetris_nd/tests/test_front4d_render.py tetris_nd/tests/test_nd_routing.py`
- `pytest -q`
