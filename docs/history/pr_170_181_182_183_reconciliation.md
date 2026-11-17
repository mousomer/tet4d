# Explorer PR reconciliation after #184

Role: history
Scope: requirement disposition for PRs #170, #181, #182 and #183.
Baseline: merged #184 (`626fdcc2`); current RDS and contracts remain authoritative.
This record does not promote implementation, mathematical certification, human
acceptance or runtime authority transfer.

## #181: playable 2D Explorer

| Requirement | Disposition |
| --- | --- |
| Existing Explorer entry and 2D dimension | Preserved by #184's existing shell and dimension-access tests. |
| Bounded, Cylinder X/Y and Torus selection | Preserved by the current string-preset surface API and Space tab; newer twisted/square surfaces remain available. |
| Native deterministic movement, atomic refusal, Retry and Undo | Current native surface runtime and its conformance suite supersede the earlier four-preset adapter. Snapshot Undo follows the newer RDS; opposite-key physical recovery is not a forward-move gate. |
| Strict values, stale/tampered proposals, stable IDs | Retain native runtime validation and preservation tests; do not expose the superseded dictionary proposal API as a second product path. |
| No gravity and no Play state mutation | Preserved by the detached practice model, unchanged gameplay sessions and existing isolation tests. |
| Replacement and actionable feedback | Current replacement updates its Retry baseline and clears rejected-action feedback; add a wall-rejection/replacement regression to the current Explorer suite. |
| Cyclic/deep and repeatedly shared Variant rejection | Unique missing fix: retain #181's depth/value budgets and `resource_limit`, with profile, query, setup and unchanged-session regressions in the already registered topology boundary suite. |
| Test registration | Extend the existing registered boundary/Explorer tests; no orphan or nested legacy test runner. |
| Topology changes | Newer RDS preserves compatible poses and explicitly recovers incompatible poses, superseding unconditional reset. |
| Human/fullscreen and terminal T2 acceptance | Remain open in the backlog; automated integration does not close them. |

The older `explorer_2d_adapter.gd`, `explorer_piece_api.cpp` and integer-selector
UI are superseded. Retaining them would create competing Explorer paths.

## #182: square S²/RP² requirements

The current `RDS_EXPLORER_TOPOLOGIES.md` §§2.5, 4.1, 8.3.1, 9–13 retains:

- Adjacent-positive S² and opposite-negative RP² edge pairings, quotient/link,
  orientability, Euler characteristic and boundary evidence.
- Single `N` extent, enforced square setup and square cells, explicit rectangular
  transition/recovery, and square saved-state admission.
- Persistent pair letters/colours/directional arrows from normalized native
  seams, no colour-only identification, and shared Builder annotation intent.
- Atomic, functional and injective cell movement; deformation/disconnection
  permitted; malformed or ambiguous transport rejected without mutation.
- Distinct space/construction/profile identity and historical sphere compatibility.
- T2S requirements and human inspection distinct from T2 transfer; later builders,
  higher-dimensional transport and optional T6 doubles stay separately gated.

Two details are explicitly superseded by the later owner amendment in §2.5:
`sphere_adjacent_positive` reuses the existing distinct positive construction
instead of inventing `sphere_square_2d`; forward admission does not require
physical inverse recovery. Snapshot Undo restores source state. The RDS also
reconciles diagram directions with engine Y-down coordinates. These are deliberate
successors, not missing requirements. T2S comprehension/visual acceptance and
terminal T2 transfer remain open.

## #183: rendering cleanup

#184 retains the removals of the spawn-entry label and orientation-gizmo centre
ball, the shared `BOARD_LABEL_*` tokens, removal of dead visual-role/token
exceptions, and the updated renderer/2D shell regressions. The active-piece
origin cube remains governed by its existing context-specific rendering rules.
Historical cockpit/stage text records the supersession. Explorer chart cleanup
and typography fixture follow-ups requested by #183 are included in #184.
No new human visual acceptance is inferred.

## #170: older proposed Live 4D policy RDS

The accepted topology-first RDS already supersedes the proposed bounded-only,
4D-first, gameplay-session-policy design. Do not add its proposed RDS as a
competing authority. Its durable requirements map as follows:

| Requirement family | Current owner/disposition |
| --- | --- |
| One production piece, gravity-free deliberate movement, all relevant piece rotations | Topology RDS §§3–6 and bounded practice contract. |
| Shared shell/styles/renderer/camera/basis/input/help/settings; no independent geometry solver | Topology RDS §§2–4, 9, 11; bounded practice contract and shared LiveInputContract. |
| Session isolation, no lock/drop/hold/score/queue progression; validated fresh Play | Bounded practice contract and existing Explorer/Play regression suites. |
| Native legality and atomic rejection; no invented gameplay bypass | Native/query contracts and topology RDS. Approved 2D cellwise amendment is scoped; ordinary Play and 3D/4D retain their authority. |
| Exact six-plane view turns, signed mapper/inverse, Y-as-slice and relative/absolute control correctness | Bounded practice contract, shared signed-basis architecture and tests. Normal Play remains Y-fixed. |
| Explicit exception/authority boundaries; legacy Python profile, hashes and traces | Current authority map, topology RDS §§2.1–2.4 and compatibility contracts; no transfer by documentation. |
| Explorer priority over unrelated polish | Product programme Phase II and research E1, subordinate to the accepted topology RDS. |
| Novice discovery, object/view distinction, adjacency comprehension, responsive/fullscreen and physical-key review | Existing EXPLORER_LEARNING_READY and T2/T2S/T7 acceptance remain open; see backlog. No automated pass substitutes for them. |
| No study backend, telemetry, participant identities or curriculum in this slice | Existing product/research gates and deferred work; no new collection activated. |

The draft's EX-D1–EX-D7 are not silently approved: EX-D1 remains no general
bounds/collision bypass; EX-D2/EX-D7 are superseded by current documented shared
Z/X and Shift view bindings (YZ and YW use the current order), with physical-key
acceptance still required. EX-D3 uses no gameplay drop; EX-D4 uses production
piece replacement without gameplay Hold; EX-D5 uses validated existing extents
and no new mandatory preset; EX-D6 remains a scoped novice/adjacency acceptance
duty. The current documented lifecycle retains practice on menu return and
separates Retry from Reset View, superseding the draft's menu-clear/restart
proposal. The later topology replan permits presets and a secondary Builder,
superseding the draft's bounded-only exclusion.

The original PRs remain the immutable review references. Closing a superseded
PR retires its competing proposal, not the outstanding acceptance obligations.
