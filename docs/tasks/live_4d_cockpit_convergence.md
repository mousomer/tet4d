# Task Contract — Live 4D Cockpit Convergence

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

## Explicit non-goals

No 2D/3D redesign, action/key/pointer changes, clickable gameplay controls,
camera translation or fit-policy bypass, native change, authority transfer,
profile/persistence change, publication, merge, or release is authorized.
