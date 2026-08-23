# Authoritative deterministic Hold

Status: normative Stage 54D-3 contract; authority establishment evidence is
recorded as `AE-0055` only after its implementation and conformance gates pass.

## Scope and ownership

Hold is available in every production native live session: classic 2D,
embedded and native 3D piece sets, and embedded 2D, embedded 3D, and native 4D
piece sets. The modern live product enables its single Hold slot by default.
The current setup schema does not expose a Hold toggle; adding one is a later,
separate product decision.

The native deterministic session owns the held piece identity, legality,
transition, queue and spawn consequences, and deterministic identity. Godot
owns one edge-triggered input affordance and presentation of native queries.
Python has no Hold implementation and is not a second authority.

The canonical state addition is:

- an optional production `PieceShape2D` or `PieceShapeND`, storing identity and
  canonical cells only; and
- one availability bit for the current active-piece lifecycle.

Godot never derives or mutates either value.

## Transition table

| Case | Before | Command result | After |
| --- | --- | --- | --- |
| A — empty slot | active `A`; Hold empty; queue `B, C, ...`; available | accepted | Hold `A`; active `B`; queue `C, ...`; unavailable |
| B — occupied slot | active `A`; Hold `H`; queue `B, C, ...`; available | accepted | Hold `A`; active `H`; queue unchanged as `B, C, ...`; unavailable |
| C — repeated command | active present; unavailable | rejected, deterministic no-op | active, Hold, queue, RNG, board, and hash unchanged |
| D — next lifecycle | current active successfully locks and the ordinary spawn succeeds | not a Hold command | Hold unchanged; new active is available to Hold |
| E — reset/new game | any state | reset | Hold empty; initial active spawned normally; available |
| F — blocked Hold spawn | A or B, but incoming canonical spawn collides | accepted transition followed by ordinary spawn failure | existing `spawn_blocked` game-over policy; terminal state has no Hold availability |

Every piece entering play from Hold uses the existing authoritative
`spawn_piece` path. It receives the ordinary canonical spawn origin and
orientation. Translation, rotation, dimensional embedding transform,
presentation basis, slice state, camera, and layout state are never stored.

## Queue and randomizer

Empty-slot Hold draws exactly one piece through the current queue/randomizer,
because it must create a replacement active piece. Occupied-slot Hold draws
none. Rejected commands and all Hold/preview queries draw none. Hold never
reseeds, reshuffles, or otherwise changes future queue order beyond the one
ordinary draw required by an empty-slot transition.

## State identity and snapshots

The held shape's complete canonical identity and lifecycle availability are
part of the native session hash in both legacy-sequence and shuffled-bag live
sessions. The live snapshot transport exposes `held_piece` and
`hold_available` alongside active and next state. Held-piece queries reuse the
Stage 54D-1 production preview dictionary and are observationally pure.

Native sessions are value state: copying a session captures board, active,
queue/bag, RNG, held identity, availability, counters, and hash, and restoring
that value restores subsequent Hold behaviour exactly. The Godot JSON snapshot
is a read-only presentation transport, not a persistence/restore format.

## Commands, replay, and compatibility

`hold` is one semantic native live command and one Godot input action. It is
recordable/replayable wherever live semantic command sequences are retained;
replaying the same initial setup and commands must reproduce the final state
and hash, including rejected attempts.

The fixed exported replay/trace corpus is a separate, already-versioned
presentation format and does not serialize mutable native live sessions. Its
schema therefore does not change. Historical fixtures contain no `hold`
command and retain their prior behaviour and expected results. Starting a live
session, including one derived from older setup data, implies the canonical
empty-and-available Hold state.

## Presentation contract

The physical binding is `C`, which is free in the current Godot live action
contract. It dispatches on a non-echo press only and uses existing pause,
modal, setup, menu, and replay ownership suppression. Help text is generated
from the same action contract.

The cockpit presents HOLD beside the existing immediate NEXT information. The
empty state says `EMPTY`; the unavailable state says `Used until lock` as well
as using subdued styling, so meaning never depends on colour alone. Populated
previews reuse `PieceThumbnailModel` and `PieceThumbnail`, including shared
cross-W projection framing. Hold changes no view/control-frame state, and
Ghost refreshes from the newly authoritative active piece through its existing
query path.

## Stage 54D-3 acceptance evidence

The 2026-08-23 pinned Godot 4.7.1 real-window review exercised Hold after an
empty-slot transition in live 2D, 3D, and 4D. It covered compact, standard, and
detailed cockpit density; standard, large, and extra-large UI scale; requested
960x640, 1180x760, 1600x960, and 1920x1080 window sizes; and the actual High
Contrast accessibility policy. In every case NEXT and HOLD remained distinct,
the held identity and `Used until lock` state were readable without relying on
colour, the board remained primary, and no gameplay/view semantics changed.

Verdict: accepted with no Stage 54D-3 blocker. The already-recorded slight
standard-mode 4D volume-legibility weakness remains bounded to Stage 54G polish
and does not reopen Stage 54F layout, projection, grid, controls, or authority.
