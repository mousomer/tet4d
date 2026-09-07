# Task Contract — Stage 56 Cockpit Completion

Status: in progress on `codex/live-4d-cockpit-convergence-rebuilt`; not accepted.

## Objective

Preserve and converge the proposed Live-4D cockpit implementation in the Godot product shell:
a stable horizontal W1–W4 board sequence with one bottom deck ordered `PIECE |
VIEW | PIECE STATE`.  The task is presentation-only.  It makes exact 4D view
operations discoverable as passive, contract-derived View guidance and keeps
the existing gameplay, input, camera, geometry, queue, Hold, and deterministic
owners unchanged.

## Authority and scope

The routes are `godot_product_shell` and `product_planning`; the workflow
modifier is `cross_layer`. `LiveInputContract` remains the only action and
binding authority. `LivePieceControlStrip` remains the Piece consumer;
`PieceThumbnailModel` and `PieceThumbnail` remain NEXT/HOLD authority
consumers. Canonical local geometry, slice layout, collection bounds, the
existing bounds-driven fit path, native session, and Presentation Designer
retain their current ownership.

| Layer | Allowed change | Consumer evidence |
| --- | --- | --- |
| Live-4D shell layout | Horizontal slice allocation and bottom-deck composition. | Stable ordered slice, contained board, no permanent gameplay inspector. |
| Input presentation | Contract-derived passive `VIEW` groups. | Actual exact-view, orientation, framing, and pointer labels update with the contract. |
| Piece state | Shared quiet HOLD/NEXT presentation allocation. | Existing thumbnails and state remain adjacent and contained. |
| Documents/tests | Supersede the relevant passive-help hierarchy and record scope. | Layout, Designer isolation, and deterministic regression evidence. |

## Proposed acceptance criteria

1. Live 4D has ordered horizontal W1, W2, W3, W4 geometry; no activity may
   reorder or resize those slots.
2. Its deck is below and non-overlapping with the board and keeps `PIECE`,
   `VIEW`, then `PIECE STATE` at all supported density and scale states.
3. Piece and View are distinct passive semantic components. View derives its
   groups and bindings from `LiveInputContract`; it introduces no binding map.
4. HOLD and NEXT remain adjacent consumers of the existing thumbnail path;
   empty Hold remains explicit.
5. Designer full/compact operation and all gameplay, input, camera/basis,
   queue/Hold, snapshot/hash, and replay identity remain unchanged.
6. Automated Godot acceptance plus real runtime captures and measurements cover
   190/200 normal, full, compact, occupied Hold, Designer, and constrained
   states. The 190/200 choice remains a human A/B decision if both comply.

None of these criteria is accepted by this reconstruction. The current branch
only preserves the work on the repaired camera/control contract and establishes
focused structural evidence for later review.

## Stage 56 execution contract

The completion programme is deliberately serial: `56A` rosette correctness,
`56B` deterministic slice tiling, `56C` semantic helper rows, `56D` shared
cockpit grammar, `56E` Live 3D migration, `56F` Live 2D migration, `56G`
responsive acceptance, `56H` human playability acceptance, and `56I` bounded
polish. Each stage requires its own focused green evidence and reviewable
commit. A failed stage gate blocks the next stage.

### Stage 56A — state-driven Live-4D orientation rosette

The rosette is a passive projection of the same app-owned exact basis `B`,
shared slice-local orientation `L`, and `ControlFrameMapping` snapshot already
consumed by rendering and relative controls. `CameraRig` may cache only a
render snapshot supplied through that path; it must not mutate or reconstruct
an independent orientation model, dispatch input, or touch native gameplay.

Acceptance requires the initial state, XZ/XW/ZW exact turns, continuous yaw,
continuous pitch, and Reset View to leave the rosette semantic snapshot equal
to the current authoritative presentation snapshot. Drawing and refreshing the
rosette must be observational, native snapshot/hash must remain unchanged, and
Live-3D orientation behavior must remain on its existing camera-driven path.

Stage 56A is implemented and focused-green. Its evidence covers the three
state owners, all required operations, passive redraw, native snapshot/hash
isolation, and the retained Live-3D path. Stage 56B is now eligible; Stages
56C–56I remain gated.

### Stage 56B — deterministic viewport-aware slice tiling

`AdaptiveLayerLayout` evaluates count-derived row/column candidates against
the available board viewport and the stable local-orientation envelope. The
selection maximizes projected per-slice scale, prefers at most two rows for
the expected Live-4D range, and then rejects unbalanced final rows. It must not
consume axis identity, active-slice identity, cell occupancy, or gameplay
state. Assignment remains monotonically row-major.

At the 1600×960 reference viewport the required results are `5→3×2`,
`6→3×2`, `7→4×2`, and `8→4×2`. Evidence records viewport, tile rectangles,
projected scale, and unused area and compares fixed-four alternatives. A
partial final row remains left aligned because it preserves stable columns and
sequence scanning. In the real oblique cockpit projection it also preserves a
slightly larger fit than centering; visual preference remains eligible for the
explicit human A/B gate.

Stage 56B is implemented and focused-green. During cockpit integration it
exposed bounded repair `56B-R`: the stretched render SubViewport can report a
transient `120×2` allocation before the real game area settles, so the HUD's
stable game-area geometry now owns layout invalidation and supplies the board
viewport to the renderer. The repair changes presentation geometry only and
does not alter slice identity, activity, gameplay, or deterministic state.
The measured candidate table and required A/B captures are recorded in
`docs/design/stage_56b_slice_tiling_evidence.md`. Stage 56C is now eligible;
Stages 56D–56I remain gated.

## Explicit non-goals for Stage 56A

No 2D/3D redesign, slice-layout choice, helper/deck refactor,
action/key/pointer changes, clickable gameplay controls, camera translation or
fit-policy bypass, native change, authority transfer, profile/persistence
change, publication, merge, or release is authorized.
