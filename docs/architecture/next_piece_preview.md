# One-Piece Next Preview Contract

Status: Stage 54D-1 implementation complete; pre-54F 3D/4D geometry-fidelity
correction implemented and automated green; focused human-visible review pending

## Objective and authority

Live 2D, 3D, and 4D play present exactly one authoritative next piece in the
Godot cockpit. Existing deterministic session and queue owners continue to
choose the piece. Godot owns only the compact thumbnail model, rendering, HUD
placement, accessibility composition, and player-facing labels.

This stage does not transfer inherited queue or randomizer authority. It does
not establish new deterministic gameplay behaviour.

## Task boundary

Primary task type: `godot_product_shell`.

Workflow modifier: `cross_layer`.

| Layer | Why it must change | Allowed paths | Verification |
| --- | --- | --- | --- |
| Native deterministic session | Supply the exact queued shape through a read-only query | `native/tet4d_core/include/tet4d_core/plain_*_session.hpp`, `native/tet4d_core/src/core/plain_*_session.cpp`, focused native tests | Native build/tests; repeated-query, bag-boundary, and state-identity invariance |
| GDExtension boundary | Convert the native shape query to a checked Godot dictionary | `native/tet4d_core/src/godot/tet4d_core_api.*`, `godot/Tet4D.Godot/scripts/native/tet4d_core_bridge.gd` | Extension and bridge tests |
| Godot product shell | Model, render, place, and update the live preview | `godot/Tet4D.Godot/scripts/ui/**`, `godot/Tet4D.Godot/scripts/app/trace_replay_app.gd`, focused Godot tests | Model, renderer, HUD-order, lifecycle, layout, and replay-exclusion tests; visible-window inspection |
| Product and architecture documentation | Record durable behaviour, ownership, and active-stage closure | Relevant `docs/**` owners | Governance validators and maintenance-doc check |

## Authoritative read-only query

Each live native session exposes a `peek_next_piece_shape()` query. Its result
contains:

```text
dimension
piece_set_id
piece_name
color_id
canonical piece-local cells
```

The GDExtension converts that result to one dictionary with stable keys:

```text
dimension
piece_set_id
piece_name
color_id
cells
status (`piece` or `failure`)
```

The query is observational. Calling it once or repeatedly must not change the
queue, bag, RNG state, current piece, snapshot, state hash, trace identity, or
command status.

Gameplay refill and empty-bag preview use one shared
`build_shuffled_piece_bag()` operation. Gameplay supplies the live RNG and
commits the returned bag. Preview supplies a copied RNG, inspects the returned
temporary bag, and discards both copied mutations. A later authoritative draw
must therefore produce the reported piece without a second shuffle algorithm.

`color_id` predates this feature as metadata on the production `PieceShape`
used by active and locked gameplay cells. Native transports that existing
identifier. Godot remains authoritative for palette mapping, theme variants,
High Contrast, outlines, and all other accessibility styling.

## Shared thumbnail presentation

`PieceThumbnailModel` is a reusable Godot presentation model. It validates and
normalizes payload ordering for drawing while retaining the exact canonical
piece-local cells. "Normalize" here permits no geometric rotation, reflection,
axis permutation, dimensional collapse, or per-group translation. It exposes
deterministic drawing groups:

- 2D: one XY cell group;
- 3D: one compact isometric XYZ group;
- 4D: ordered W groups, each rendered as a compact isometric XYZ slice with an
  explicit signed `W` coordinate label.

Within each isometric XYZ group, canonical face-neighbours use the matching
projected cube-face edge as their centre-to-centre step, so a connected piece
reads as one face-connected polycube without background gaps. Distinct 4D `W`
groups remain intentionally separated and explicitly labeled; presentation
must not merge cells across different `W` coordinates into a false 3D shape.

The thumbnail coordinate contract is exact. Embedded 2D pieces retain fixed
`Z=0` in 3D and fixed `Z=W=0` in 4D; embedded 3D pieces retain fixed `W=0` in
4D. The model may sort cells and the renderer may fit the piece with one
uniform scale and translation. No other transform is authorized.

For 4D slice decomposition, every occupied W pane uses the same XYZ isometric
projection, uniform scale, and pane-local origin derived from the complete
piece before W grouping. Pane anchors separate the labeled W views, but cannot
independently center or scale their cells. Consequently equal XYZ coordinates
align in every pane, relative XYZ offsets between panes remain visible, and a
cross-W face adjacency is represented by equal pane-local XYZ position in
adjacent W labels.

## Pre-54F geometry-fidelity correction

The authoritative query and thumbnail model retain correct geometry. The
original renderer fitted every W pane from that pane's local bounds. Those
independent bounds, scales, and origins erased shared XYZ placement between W
groups even though cell count and labels remained correct. `FORK4` exposes the
failure: its canonical cells are:

```text
W=0: (-1,0,0), (0,0,0), (1,0,0)
W=1: (0,0,1), (0,1,0)
```

The W=1 cells carry a Z/Y offset pattern relative to the centre of the W=0 X
bar, not a pane-local two-cell bar normalized to an unrelated origin. The
correction must fit both panes from one whole-piece XYZ frame and retain the
existing face-connected cube projection. It must not special-case `FORK4`.

Exhaustive conformance enumerates the admitted 3D and 4D piece-set registries
and their native production definitions through a read-only diagnostic. Every
definition passes through the actual `PieceThumbnailModel` and renderer plan.
The oracle requires exact reconstructed cells, uniqueness, coordinate extents,
dimensional embedding, W membership, face-adjacency edges, one renderer cell
per model cell, and one pane per occupied W coordinate. Named `FORK4` and
independent-W-recentering cases supplement, but do not replace, that registry
coverage.

Current registry coverage is 14 Live-3D definitions (`embedded_2d` and
`native_3d`) and 21 Live-4D definitions (`embedded_2d`, `embedded_3d`, and
`standard_4d_5`). This count is descriptive rather than a test allow-list: the
oracle iterates the registry and therefore automatically covers future
production additions.

`PieceThumbnail` is the shared renderer. `NextPiecePanel` supplies the `NEXT`
title and piece name and owns no queue decisions. Stage 54D-3 Hold must reuse
this model and renderer rather than create a second piece-preview system.

Colour is not the only identity cue: the piece name and 4D slice labels remain
visible. The thumbnail uses the shared shell palette, semantic panel styling,
and high-contrast outlines, and scales with the existing UI-scale policy.

## HUD placement and lifecycle

The preview is a live-only panel in the scrollable right inspector. Visible
direct-child order is:

```text
onboarding, when enabled
NEXT
4D BASIS, in live 4D only
CONTROLS
remaining inspector sections
```

In live 2D and 3D, `NEXT` occupies the same slot and the 4D basis panel is
hidden. The preview uses the inspector width and a bounded height so the board
remains the primary surface and controls remain reachable by scrolling at the
supported minimum viewport.

The application refreshes the preview after a successful live configure,
reset, tick, or nonterminal command snapshot refresh. Ordinary game over
freezes the last successfully rendered authoritative thumbnail; it does not
issue a new query after the terminal snapshot. Current validated live sessions
always have a next draw and therefore expose no successful `no_next` state.
If that state is introduced later it requires a distinct documented provider
status and an empty presentation rather than reuse of old geometry.

Replay and all non-live screens hide the panel. A structured provider failure,
malformed payload, or unavailable query clears old geometry and shows
`Preview unavailable`; Godot does not infer a replacement piece from a
catalogue or the current piece. Failure is presentation-local and does not
block gameplay.

The thumbnail cache identity comprises dimension, piece-set ID, piece name,
existing colour ID, and exact canonical cells. Identical HUD refreshes reuse
the renderer model. Relevant style/accessibility changes invalidate drawing
through the Godot style manager separately. Camera, Stage 54C basis, score,
gravity ticks, active position, and board dimensions are not cache inputs, so
they cannot reorient or rebuild canonical preview geometry.

## Deterministic exclusions

Stage 54D-1 does not change:

- queue order, bag refill, randomizer, seed, or RNG consumption;
- gameplay snapshots or state hashes;
- replay, trace, or compatibility schemas;
- spawn, legality, collision, rotation, drop, lock, clear, or scoring;
- setup, persistence, topology, camera, or 4D slice-basis semantics.

Multiple preview entries, configurable preview depth, randomizer-history
presentation, ghost pieces, and Hold behaviour are explicitly deferred.

## Acceptance criteria

1. Live 2D, 3D, and 4D display exactly the piece returned by the native query.
2. Name, colour identifier, dimension, and canonical cells match the production
   piece selected by the next real draw.
3. Repeated queries and HUD refreshes do not alter snapshots, hashes, RNG, bag,
   or command status, including at a bag-refill boundary.
4. One shared model and renderer cover 2D, 3D, and W-sliced 4D thumbnails and
   are suitable for later Hold reuse.
5. The live inspector order is onboarding, `NEXT`, optional `4D BASIS`, then
   controls; Replay never shows the panel.
6. The panel composes with supported viewport, UI-scale, theme, and high-
   contrast settings without obscuring the gameplay board.
7. Native, GDExtension, Godot, governance, sanitation, and full repository
   verification pass. Visible-window inspection confirms practical readability.

## Implementation and verification

The native sessions implement `peek_next_piece_shape()` and the GDExtension
exports mode-specific checked dictionaries. Godot consumes those dictionaries
through `PieceThumbnailModel`, `PieceThumbnail`, and `NextPiecePanel`; the live
application refreshes the panel independently of gameplay snapshots.

Focused native tests cover legacy and shuffled queues, repeated observation,
empty-bag copied-RNG prediction, unchanged snapshots/hashes/status, and equality
with the next real draw. Godot tests cover the three dimensional presentations,
GDExtension transport, shared-renderer reuse, live inspector order, minimum
viewport composition, accessibility styling, and replay exclusion.

Developer visible-window inspection passed for representative Live 2D, Live
3D, and Live 4D sessions at `1600 x 960`. This is rendered inspection evidence,
not human/user acceptance. Integrated human playability and preview-readability
acceptance remains part of Stage 54E. The repository-wide `CODEX_MODE=1`
verification gate passed after the implementation and focused checks.
