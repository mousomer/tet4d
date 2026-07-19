# Stage 49 Configurable Plain Boards and Adaptive 4D Layout

Status: implementation complete; menu-routing regression repaired and automated verification passed; manual reacceptance pending
Date: 2026-07-15

## Authority and scope

Python remains the semantic authority for gameplay rules, topology, replay,
configuration defaults, and parity. The accepted native plain-session owner
remains responsible for live bounded state transitions; Stage 49 only
parameterizes that owner by board shape. Godot owns the New Game setup model,
setup persistence, validation UX, rendering, camera fit, HUD, scrolling, and
focus. Godot must not calculate legality, spawn, clear, scoring, or game-over.

This stage does not resize active games. `Restart Game` reconstructs the same
selected setup; `Change Setup` exits the live session and creates nothing until
`Start Game`; `Main Menu` leaves live play without applying another shape.

## Menu transition interaction invariant

Leaving a live session for `Main Menu` or `Change Setup` must also leave the
live-only input-capture state. A hidden viewer rectangle must never consume
mouse input intended for a visible menu, and the visible screen must receive a
deterministic focus target that activates with Enter/Space. This invariant is
required after every 2D, 3D, and 4D live-session transition, not only on fresh
application startup. Regression coverage must exercise real pointer events and
keyboard acceptance after those transitions.

## Current assumptions audit

### Python configuration authority

- 2D uses `GameConfig.width` and `GameConfig.height`; the durable 2D setup
  envelope is width `6..16` and height `12..30`.
- 3D/4D use `GameConfigND.dims`, ordered `(x, y, z[, w])`.
- Explorer dimensions, topology, challenge layers, piece sets, random mode,
  seed, kick level, progression, bot, endgame, and explosion settings remain
  excluded.
- Python defaults and pygame setup behavior are not changed by this stage.

The Python RDS typical boards (`6x18x6` and `6x18x6x4`) are not the accepted
Godot live defaults. Current native/Godot live play uses `6x6`, `6x10x6`, and
`5x10x4x4`. Stage 49 preserves those accepted live shapes as its Standard
presets rather than silently changing either Python defaults or accepted Godot
behavior.

### Native construction, algorithms, snapshots, and identity

- `Plain2DSession` constructs and resets `GameState2D(6, 6)`; its snapshot
  hard-codes `[6,6]`, its spawn X is hard-coded to `2`, and its state hash does
  not include board shape.
- `PlainNDSession` selects `6x10x6` or `5x10x4x4` through
  `live_board_shape_for_dimension()` and reset restores that hard-coded shape.
- The Godot extension owns one session instance per live mode and exposes only
  reset/command/tick/snapshot/status/hash operations; it has no configure or
  construct-with-shape call.
- 2D bounded legality and line clear iterate the board's width/height and are
  otherwise shape-independent. 2D spawn centering is the shape-dependent gap.
- ND bounded legality, gravity, hard drop, plane clear, and spawn centering
  already derive from `BoardShapeND`. Clear capacity is the product of all
  non-gravity dimensions.
- ND state hashes already include `dimension` and `board_shape`. 2D hashes must
  gain both fields so identical cells on different boards cannot collide.
- Live snapshots already expose `dimension`, `board_shape`, active/locked
  cells, score, clears, current/next piece, and `state_hash`.
- Existing replay/gameplay traces encode shape in trace initial state and
  snapshots. The schema can represent alternate dimensions; no schema redesign
  is required.

### Godot presentation assumptions

- `TraceCoordinateMapper` places every 4D W slice in one horizontal row using
  fixed `slice_stride = 6.0`.
- `CameraRig.frame_board()` expands X by `(W - 1) * slice_stride`; this fits the
  current row but becomes excessively wide for W greater than four.
- `TraceSceneRenderer`, grid, cells, labels, and camera consume actual
  `board_shape`, but all share the mapper's fixed W-row assumption.
- Live HUD metadata exposes `w_slice_count` and singular `active_w`; it does
  not report the complete active-piece layer set or a basis-derived axis.
- Current Godot does not expose XW/ZW view-basis rotation. Stage 49 must not
  fake it. Basis-derived X/ZW relayout is deferred until that view control is
  implemented; the layout API will retain an explicit layer-axis input.
- Python `front4d_render.py` already demonstrates the semantic/presentation
  split: basis determines layer axis/local coordinates, while layout uses
  approximately square rows and columns. Godot may reuse that presentation
  concept without importing Python gameplay logic.

### Tests and fixtures with fixed dimensions

- Native live-session tests assert the three accepted default shapes and hashes.
- Plain gameplay golden traces use compact case-specific shapes such as `6x6`,
  `5x5x5`, and `5x5x4x4`; they remain unchanged regression fixtures.
- Godot renderer, camera, live-loop, HUD, onboarding, navigation, and scene tests
  assert current W-slice and default-shape behavior.
- Stage 49 adds focused configurable-session and layout tests rather than
  rewriting the accepted default fixtures.

## Limits and supported presets

Native integrity limits are intentionally separate from product support.

| Mode | Native semantic minimum | Native safe maximum | Stage 49 presets |
| --- | --- | --- | --- |
| 2D | `4x6` | `16x30` | Compact `4x6`; Standard `6x6`; Large `10x20` |
| 3D | `4x6x2` | `10x24x10` | Compact `4x8x4`; Standard `6x10x6`; Large `8x16x8` |
| 4D | `4x6x2x1` | `12x24x8x12` | Compact `4x8x3x3`; Standard `5x10x4x4`; Wide W `8x16x5x8` |

The minima accommodate every accepted live piece sequence and spawn geometry.
The maxima bound clear-plane multiplication, rendering density, and matrix
layout. Godot exposes only the curated presets and validates them before
construction; native code independently validates coordinate count, bounds,
and spawn viability.

The 2D Standard height is the accepted live compatibility shape even though it
is below the pygame product setup minimum. This is a migration compatibility
exception, not a change to Python defaults or the Python product envelope.

## Setup and persistence ownership

Godot owns a separate `game_setup` model containing supported specs, the
selected preset per mode, validation, and canonical snapshots. Optional
last-selection persistence uses versioned `user://game_setup.json`. It stores
only preset IDs by mode, validates them against checked-in specs, falls back to
Standard for missing/malformed/unsupported data, and never reads or writes
`user://shell_settings.json`.

No active board, score, pieces, cells, RNG, pause state, or game-over state is
persisted.

## Adaptive 4D presentation

The renderer uses one deterministic layout result for cells, grid, labels,
frames, camera bounds, and active-layer emphasis:

1. derive layer count from the presentation basis (W in the currently exposed
   identity view);
2. choose columns from layer count, viewport aspect, local-board aspect, and a
   minimum readable tile span;
3. set rows to `ceil(layer_count / columns)`;
4. assign every layer exactly once in stable row-major order;
5. derive mapper offsets and camera bounds from the same assignment;
6. highlight every layer occupied by active-piece cells.

Counts up to four prefer one row or `2x2`; five through twelve use an
approximately square matrix. All Stage 49 presets remain fully represented and
Fit View restores the whole matrix. In Live 4D, Shift+mouse-wheel pans the
matrix focus by deterministic row steps while the normal wheel retains camera
zoom; Fit View restores the complete overview. Matrix scrolling/panning is
presentation only, does not dispatch gameplay commands, and does not take live
keyboard focus.

Full tile-node virtualization is deferred. The supported maximum is twelve
layers, for which complete instantiation is bounded. A future virtualization
threshold is any supported design above twelve layers; it should retain stable
layer IDs, visible tiles plus overscan, and complete session state outside tile
nodes.

## Parity evidence

Alternate-size deterministic cases must reuse the existing gameplay trace
schema and case registry. Evidence is deliberately bounded: one alternate 2D,
one alternate 3D, and one alternate 4D W=8 sequence must prove construction,
boundary movement/rotation, drop/lock, clear/game-over where existing case
helpers permit, final shape, and final hash. Mismatch output must identify case,
mode, board shape, command index, cells/state, and hash/shape differences.

## Explicit deferrals

- topology transport, presets, seams, and topology-aware Godot gameplay;
- arbitrary custom dimensions beyond curated presets;
- explorer dimensions and exploration mode;
- piece-set, RNG/seed, kick, progression, bot, endgame, and explosion migration;
- replay-schema redesign or authority transfer;
- XW/ZW view-basis controls not already exposed by Godot;
- virtualization above the twelve-layer supported maximum;
- Steam/export packaging and broad Python deduplication.
