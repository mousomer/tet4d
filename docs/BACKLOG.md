# Tet4D Open Work

Updated: 2026-08-28
Scope: active work, explicit deferrals, and acceptance boundaries only.

Completed detail is preserved in `docs/history/backlog_archive_2026-07-30.md`,
`docs/history/current_state_archive_2026-07-30.md`, and
`docs/history/DONE_SUMMARIES.md`.

## Current Authority

- Professional product programme and phase gates:
  `docs/plans/professional_godot_game_programme.md`
- Product behaviour: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Topology architecture and invariants:
  `docs/plans/topology_playground_current_authority.md`
- Subsystem authority: `docs/architecture/authority_map.md`
- Authority transfer and establishment:
  `docs/architecture/authority_transfer_protocol.md`
- Documentation routing: `docs/DOCUMENTATION_MAP.md`
- Workflow and change classes: `docs/WORKFLOW_CODEX.md`
- Machine governance: `config/project/policy_pack.json`

## Tracking Boundaries

This backlog tracks the active implementation slice, immediate accepted
follow-ups, and deferrals whose resolution depends on product evidence or an
authority decision.

It does not duplicate the complete programme roadmap.

GitHub issues are for independently actionable, user-visible or reproducible
bugs and their collaboration lifecycle.

## Active Work

Primary gate:

```text
PROFESSIONAL_CORE_GAME_READY
```

The first priority is a fully playable and professionally presented 4D Godot
game ready for later topology, Explorer, challenge, and simulation extensions.
The programme is owned by
`docs/plans/professional_godot_game_programme.md`.

Status: `PROFESSIONAL_CORE_GAME_READY: YES`. Stage 54G passed final manual
release acceptance, closing the Stage 54 Professional Core Game programme.
Future implementation starts as a new programme or stage rather than extending
54G; topology, Explorer, challenge/campaign, simulation, broader distribution,
and post-release polish remain outside this completed gate.

Completed bounded follow-on: the Presentation Parameter Contract is locally
accepted on `codex/presentation-parameter-contract`. It reuses the existing
registry, store, palettes, renderer, and 54E presentation spaces; it does not
reopen Stage 54 or change deterministic/native authority. Focused, pinned,
full-repository, and agent-driven real-window checks pass. The durable contract
is `docs/architecture/presentation_parameter_contract.md`, and the acceptance
record is `docs/plans/presentation_parameter_contract_acceptance.md`.

Completed bounded follow-on: Stage 54F-2 adds the Live Presentation Designer
on `codex/canonical-local-board-geometry`. It generates 16/18/20 applicable
Live-2D/3D/4D controls from the established registry and semantic owners,
edits a detached working B profile, captures immutable A, supports exact
numeric editing plus parameter/group/opening/factory resets, and previews only
through the existing bounded app seam. Full/compact/hidden layout preserves
the board and the existing right cockpit; NEXT and authoritative HOLD
(`AE-0055`) remain simultaneously viewable, while 4D basis and helper/status
content remain visible or immediately inspector-scroll-reachable. Focused,
input/layout, deterministic/store isolation, non-headless visual, pinned
Godot 4.7.1, and full-repository evidence is recorded in
`docs/plans/live_presentation_designer_acceptance.md`. No persistence,
gameplay, profile, registry, geometry, basis, NEXT, HOLD, or camera-pose
authority changes.

Completed bounded review correction: Stage 54F-2R makes the gameplay board the
dominant visual surface, presents native NEXT and HOLD as one compact shared-
thumbnail row, and keeps a passive `LiveInputContract`-derived translation and
rotation vocabulary permanently visible above secondary camera guidance. It
first recovers vertical board allocation, then narrows only the bounds-derived
Live-4D fit clearance. Fit remains readily available. Full/compact Designer,
input and persistence isolation, deterministic state, canonical geometry,
exact basis, helper authority, and native NEXT/HOLD authority are unchanged.
Focused, pinned/full, governance, deterministic/input, responsive-layout, and
production-window evidence is recorded in
`docs/plans/live_presentation_designer_acceptance.md`; independent human
acceptance remains unclaimed.

Completed bounded post-review cleanup: Stage 54F-2R.1 closes the two P2
advisories from the independent reviewed-green cockpit review. Reset View now
has explicit live-only visibility across replay -> live -> replay rather than
depending on its shared camera parent. X/Z/W translation rows now compact from
minimal direction/signed-axis metadata supplied by `LiveInputContract`, with
no HUD display-string parsing or duplicate action/binding inventory. The
reviewed Stage 54F-2R hierarchy, layout, Designer, camera behavior, gameplay,
and authority boundaries remain unchanged. Evidence is appended to
`docs/plans/live_presentation_designer_acceptance.md`.

Completed bounded follow-on: Stage 54F-3 implements the explicit Presentation
Profile Library on `codex/canonical-local-board-geometry`. Named user profiles
use generated stable IDs and independently validated versioned files under
Godot user data. The lifecycle includes list, Save As, explicit Save, detached
load into B, duplicate, rename, confirmed delete, import, and export. The
existing registry/profile schema remains authoritative, ordinary settings are
not rewritten, and normal Designer edits remain runtime-only. Focused storage,
validation, Designer, 2D/3D/4D, cockpit, deterministic-isolation, canonical/
pinned Godot 4.7.1, settings/governance/semantic-boundary, sanitation, full-
repository, and bounded production-window evidence is green. The durable
contract and evidence are
`docs/architecture/presentation_profile_library.md` and
`docs/plans/presentation_profile_library_acceptance.md`.

Completed bounded post-review hardening: Stage 54F-3R starts from reviewed-green
Stage 54F-3 HEAD `47c90c67d5a13a84bd826f17f2838f0de3f38ec5`
on the same unpublished branch. It closes only four P2 findings: shared profile/
settings file mechanics now check the flushed temporary write before install;
profile replacement restores by rename then copy and retains an explicit
recoverable backup on total failure; library diagnostics are deterministic
current-scan state; and a production Live-4D regression protects exact gameplay
viewport allocation across collapsed/expanded library disclosure. Focused
profile, settings, and cockpit suites; canonical and pinned Godot 4.7.1;
governance/generated-doc/settings/semantic-boundary and sanitation checks; the
full repository gate; and bounded production-window inspection are green.
Stage 54F-3 semantics and reviewed-green status, separate persistence ownership,
schemas, Designer A/B behavior, gameplay/deterministic state, camera/basis, and
cockpit design are unchanged.

Completed bounded geometry review correction: Stage 54F-1 established the correct
canonical local-board architecture on `codex/canonical-local-board-geometry`,
but review found that continuous 2D/3D endgame points were routed through its
strict cell domain. Stage 54F-1R preserves one geometry owner while separating
strict lattice-cell and finite continuous affine APIs, adds production
particle/interpolation/trail/event-marker regressions, replaces tautological
slice-isolation evidence, and makes adaptive slice layout consume canonical
local extent. One canonical local-board geometry continues to own unit cells,
centred extent, coordinate conversion, face-grid segments,
and boundary segments for Live 2D, Live 3D, and every local Live-4D slice.
Semantic 2D embeds as presentation `[X,Y,1]`; exact `SliceBasis4D` supplies 4D
visible signed axes; slice-set layout, camera/framing, and profile styling stay
separate. Focused, governance, sanitation, pinned/full, deterministic-isolation,
and agent-driven 2D/3D endgame evidence pass; evidence is recorded in
`docs/plans/canonical_local_board_presentation_geometry_acceptance.md`.

Explicit deferrals from these follow-ons are formal A/B assignment/telemetry,
free-form palette-role editing, built-in style/theme profiles,
procedural/animated environments, broader theme work, and independent human
review of both the Designer workflow and the
intentional full-depth 2D mesh under unusual debug camera views. Stage 54F-2
adds the editing instrument only; it does not begin the following
profile-management/theme stage or another geometry implementation.

## Next Work

### Stage 54E-1 — Presentation-space architecture/design

Status: COMPLETE — HUMAN ACCEPTED.

The accepted architecture contract is
`docs/architecture/4d_presentation_interaction_architecture.md`. It defines
the three spaces, composition, ownership, lifecycle, scene implications,
`DEFECTIVE` current resolver verdict, anchor-only layout, shared slice-local
orientation, active/passive yaw and displayed-depth contract, verification
strategy, and mandatory green 54E-2 slices. Decisions A/B/C are accepted:
Option A; normal-gameplay roll removal while preserving Explorer/free-inspection
roll; and constrained pitch-depth preservation. No runtime implementation is
part of this acceptance record.

### Stage 54E-2a — Presentation state and coordinate decomposition

Status: COMPLETE — REVIEWED GREEN.

The implementation introduces the first-class shared Godot
`SliceLocalOrientation`, separates exact `B` mapping, centred `G_D` point
mapping, anchor lookup, and compatibility world composition, and executes the
accepted active/passive yaw, point-difference, signed-basis, asymmetric-board,
anchor-only, and `W=1` contracts. At the reviewed-green 54E-2a boundary the
renderer remained on the compatibility `G_D(p) + anchor_i` path; the separate
54E-2b implementation below now migrates that path.

### Stage 54E-2b — Renderer composition

Status: COMPLETE — REVIEWED GREEN.

The implementation migrates Live-4D cells, Ghost, geometry-attached markers,
grid/floor/lattice, ordinary and active frames, slice-label placement, and
camera-fit bounds to `B -> G_D -> L -> anchor`. It uses one shared continuous
orientation across all slice-local content, leaves anchors/layout/exact basis
unchanged, derives world AABBs from transformed local corners, and retains
2D/3D identity behavior. Focused Godot evidence covers asymmetric dimensions,
quarter/non-quarter yaw, pitch, signed basis, W=1 re-slicing, multiple slices,
Ghost alignment, grid/frame orientation, label identity, and bounds
containment. Technical review accepted this evidence; Stage 54E-2c has since
completed and been reviewed green.

### Stage 54E-2c — Interaction and camera-rig separation

Status: COMPLETE — REVIEWED GREEN.

Normal Live-4D left-drag and keyboard yaw/pitch mutate the one shared
`SliceLocalOrientation`; the app-owned mutation seam rerenders presentation,
recomputes oriented bounds, and refreshes the renderer fit reference. Relative
commands use exact `B + Q(L.local_yaw)` and ignore outer framing. Right-drag,
wheel/zoom, and Fit remain framing operations; gameplay roll is detached while
generic roll remains reusable. Legacy presets are temporarily decomposed into
`L` orientation and `V/P` framing. The fixed fitted mount applies one
renderer-only outer `V` reflection across the active camera's vertical/depth
plane, with Camera3D and HUD outside it. Actual Camera3D projection proves
resolver-selected Right screen-right, and effective camera-space depth proves
resolver-selected Forward receding across continuous yaw. Review-correction
evidence gives the strict all-yaw pitch interval as approximately
`(-42.480 degrees, +86.240 degrees)` and selects the asymmetric product range
`[-40 degrees, +60 degrees]`, retaining a `2.480-degree` lower margin. Final
visual review corrects Live-4D active spawn cells with negative canonical `Y`:
they retain their basis-derived slice and above-board position instead of
collapsing to a shared renderer origin. The same final visual pass corrects
shared NEXT-thumbnail cell adjacency so connected cells share projected cube
faces within each intentional `W` group.

### Stage 54E-2d — Lifecycle, authority, and contract reconciliation

Status: COMPLETE — REVIEWED GREEN.

The implementation restores fresh `B/L/V/P` defaults on Live-4D entry,
configured/random launch, Restart Game, and Reset View; keeps Reset View
presentation-only; provides an internal basis-only reset; synchronously clears
renderer, fit, reflection, focus/zoom/projection, and interpolation state on
setup/menu/mode exit; and rebuilds coherent defaults on re-entry. Normal
gameplay no longer registers/routes/advertises roll, while generic `CameraRig`
roll remains reusable. Persistence and deterministic-isolation tests exclude
ephemeral presentation state while retaining established preferences. No
authority transfer or establishment occurs. External technical review accepted
the implementation and its evidence. Aggregate Stage 54E-2 is COMPLETE /
REVIEWED GREEN.
The fresh-restart statement above is historical implementation evidence. The
accepted Stage 54E-4 forward contract intentionally changes same-context
Restart/new-game behaviour to preserve current view; it does not rewrite the
Stage 54E-2d review outcome.

Stage 54E-3 is COMPLETE / REVIEWED GREEN: Stage 54E-3a
taxonomy and classification and Stage 54E-3b progressive-disclosure rendering
are implemented and accepted by external technical review. Ordinary setup is
the board preset shortcut, the piece-set choice where a mode publishes more
than one set, and the starting speed; board customization, reproducibility, and
control frames sit behind secondary disclosure. Disclosure is ephemeral
presentation state excluded from canonical session setup, setup persistence,
and native session state, so no schema version changes. Its distinct human
product review remains outstanding and is owned by integrated Stage 54F unless
performed sooner. Stage 54E-4a is REVIEWED GREEN. Stage 54E-4b implements the
accepted contract and is COMPLETE / FOCUSED VISIBLE REVIEW ACCEPTED; aggregate
Stage 54E-4 is COMPLETE / REVIEWED GREEN.

## Hold

### Stage 54D-3 — Hold

Status: COMPLETE / DETERMINISTIC AUTHORITY ESTABLISHED / HUMAN VISIBLE
ACCEPTED (`AE-0055`).

Native live sessions own the one-slot transition, lifecycle legality,
queue/RNG and canonical-spawn consequences, state hash, and snapshot fields.
Godot dispatches one edge-triggered `C` action and renders authoritative HOLD
state through the shared NEXT thumbnail pipeline. Fixed replay/trace schema and
historical fixtures remain unchanged. Multiple slots, buffering, and a setup
toggle remain outside this stage.

## Forward Work

- Stage 54E-2b — renderer composition (COMPLETE / REVIEWED GREEN).
- Stage 54E-2c — interaction and camera-rig separation (COMPLETE / REVIEWED
  GREEN).
- Stage 54E-2d — lifecycle, authority, and contract reconciliation (COMPLETE /
  REVIEWED GREEN).
- Stage 54E-3 — setup/menu information architecture (COMPLETE / REVIEWED
  GREEN): direct seed input is the semantic control type `numeric_entry`,
  and board-axis controls remain `stepper` because their ranges make stepping
  the primary interaction. No control factory was introduced. A
  post-acceptance registry validation defect is FIXED: declarations are now
  validated before mode expansion, so empty mode sets cannot disappear.
- Stage 54E-4 — camera/GUI presets (COMPLETE / REVIEWED GREEN): Stage 54E-4a is
  REVIEWED GREEN and Stage 54E-4b is COMPLETE / FOCUSED VISIBLE REVIEW
  ACCEPTED, with no remaining human design decisions. It defines transient
  presentation-context view state, one composite Reset View, framing-only Fit
  View, restart/new-game preservation,
  context re-entry defaults, mode-specific 2D/3D/4D/replay ownership,
  accessibility-owned UI scale, and action-based presets with no continuous
  `Custom`/state-equality identity. The focused real-window review required two
  live view-affordance corrections before acceptance: Live 2D and Live 3D now
  route the existing `reset` action (key `0`) to the one composite Reset View,
  and Live 3D help states its real double-click Fit affordance instead of
  advertising `F`, which remains Rotate XZ.
- Stage 54E-5 — gameplay cockpit consolidation — COMPLETE / HUMAN PRODUCT
  REVIEW ACCEPTED. The accepted
  bounded design removes replay/developer chrome from ordinary live play,
  simplifies the live status summary, exposes distinct View and Session action
  families, derives mode-specific cockpit guidance from the existing live
  input contract, suppresses gameplay input while View Actions owns its popup,
  keeps NEXT prominent, and preserves replay diagnostics through their existing
  routes. It changes no gameplay, view lifecycle, movement/control-frame,
  NEXT, Ghost, or deterministic authority. Focused Godot, keybinding,
  sanitation, pinned Godot 4.7.1, and full repository verification passed.
  Real-window 2D/3D/4D review accepted the default, smaller, and larger cockpit
  composition, stateless View Actions, recovery/session actions, and
  progressive disclosure.

  E5 also carries two findings from Stage 54E-4a
  section 12.1: `display.show_w_labels` is presented in 2D and 3D where the
  renderer gates it on `dimension >= 4`, which needs a declared applicability
  mechanism in the settings registry; and `display.projection_strength` is
  misleadingly named, since it scales cell, particle, and event size in every
  mode rather than expressing a 4D projection.
- Stage 54F — COMPLETE / HUMAN INTEGRATED PLAYABILITY ACCEPTED. The bounded
  implementation, agent-driven real-DisplayServer evidence, and 2026-08-23
  human verdict are recorded in
  `docs/plans/stage_54f_integrated_visual_acceptance.md`.
- Stage 54G — COMPLETE / FINAL MANUAL RELEASE ACCEPTANCE PASSED. The
  independent matrix found one release blocker: after Live 4D exited through
  Main Menu and navigated through Advanced / Diagnostics, Replay Demos, and
  Viewer, the retained native session was exposed with cleared live board
  presentation. Viewer navigation now returns through the app lifecycle owner,
  rebuilds the canonical live presentation, and preserves native gameplay and
  the retained pause state. Focused all-mode/replay coverage, pinned Godot,
  full verification, rebuilt packaging, outside-tree smoke, and an actual-app
  Live-4D reproduction pass. Independent final blocker re-acceptance passed
  running and paused Live 4D, shared Live 2D/3D return, replay, immediate board
  visibility, retained gameplay/HOLD/NEXT/Ghost coherence, restored input
  ownership, and clean runtime logs. `PROFESSIONAL_CORE_GAME_READY` is `YES`.

### Stage 54F integrated visual findings

- [x] [Increase Live-4D inter-slice board spacing (#69)](https://github.com/mousomer/tet4d/issues/69):
  closed in the Stage 54F candidate through deterministic board-size-derived
  horizontal/vertical gutters, label-aware row clearance, stable slice
  assignment, non-overlap tests, and whole-collection Fit evidence for
  representative `2x2`, `W=8`, asymmetric, and constrained-window layouts.
- [x] [Refine Live-4D grid and board-wireframe visual hierarchy (#70)](https://github.com/mousomer/tet4d/issues/70):
  closed in the Stage 54F candidate. Internal-grid alpha is now operational
  and subordinate; wireframe and active-frame roles remain distinct; the
  active-frame multipliers are reduced; High Contrast preserves the ordering;
  and occupied real-window evidence keeps pieces and Ghost dominant.
- [x] Every displayed 4D W-slice reads as a 3D board volume in the agent-driven
  real-window matrix: front/back face grids, floor lattice, wireframe cage,
  piece/Ghost depth, responsive separation, and rotated-view evidence remain
  legible. Human integrated acceptance and final release acceptance passed.
- [x] The Stage 54E-3 setup-colour advisory is closed. Invalid setup now
  carries error-coloured summary and disclosure treatment plus literal
  `ERROR` text when the responsible section is collapsed, in standard and
  High Contrast modes.
- [x] The E5 display-setting findings are closed without changing setting IDs
  or persistence schema: runtime UI contexts now filter inapplicable quick
  settings, and player-facing labels describe cell-outline strength, 4D slice
  labels, and replay-object scale truthfully. The same audit also corrected
  runtime UI scale so it visibly reflows the shell instead of changing only a
  stored factor.
- [x] Supported-small-window Settings reachability is repaired: content and
  both reset actions scroll into range, and keyboard focus reveals an
  off-screen target instead of remaining stranded.

No new Stage 54F blockers remain in automated or agent-driven real-window
review.

- **Stage 54G polish — modest standard-mode Live-4D volume legibility.**
  Human review found that Live-4D gameboxes remain slightly less legible than
  equivalent 2D/3D boards in the standard presentation. The current
  presentation remains usable and comprehensible, and High Contrast provides
  a strong alternative, so this does not block Stage 54F acceptance. During
  The 54G comparison selected disposition B: no sufficiently clear low-risk
  improvement justified reopening the human-accepted rendering candidate.
  Retain this as non-blocking post-release polish, not a correctness or
  architecture defect.
- **Post-release polish — live pause status badge.** Pausing correctly stops
  live gameplay, but the cockpit badge can continue to display `[ RUNNING ]`.
  Track this separately from the Viewer-return release blocker; do not expand
  the bounded restoration fix into status-presentation work.
- **Post-release shell/accessibility follow-ups.** Preserve the non-blocking
  small-width `SPAWN ENTRY` clipping, replay case-list keyboard limitation,
  very-small-window/minimum-size behavior, HiDPI default physical-point
  sizing, and window size/position persistence observations for later bounded
  product work. Developer ID signing and notarization remain a separate macOS
  distribution prerequisite, not part of Professional Core Game readiness.

### Pre-54F correctness findings

- **Cross-dimensional relative-control truthfulness — COMPLETE / REVIEWED GREEN
  / issue #74.** Live 2D now resolves
  signed canonical X from presented outer yaw. Live 3D now resolves
  screen-relative Left/Right and viewer-away/viewer-toward Forward/Back from
  the outer-camera convention. Initial/repeated input, HUD, and the 3D gizmo
  consume one effective mapping; Absolute and accepted Live-4D
  `B + Q(L.local_yaw)` behaviour are protected by regression tests. Focused
  Godot verification and the full repository gate are green. Human-visible
  review accepted 2D Relative Left/Right, 3D Relative Left/Right and
  Forward/Back, and preservation of accepted 4D behaviour. E4 lifecycle and
  view architecture remain closed.
- **3D/4D NEXT geometry fidelity — COMPLETE / HUMAN VISIBLE REVIEW
  ACCEPTED.** The queue payload and thumbnail model were exact;
  independent renderer fitting per W pane erased shared XYZ placement. One
  complete-piece projection frame now preserves cross-W offsets. Registry-led
  conformance covers all 14 production Live-3D and 21 production Live-4D
  definitions, embedded lower-dimensional paths, FORK4, renderer completeness,
  and queued identity/update without changing queue or RNG semantics. Focused
  Godot 4.7.1 real-window review accepted representative native and embedded
  3D/4D pieces, FORK4's shared cross-W placement, renderer completeness, and
  queue progression. This closes only the bounded correctness item; do not
  absorb it into E4a or integrated 54F acceptance.

## Authority Transition Work

The repository no longer treats Python as the universal semantic oracle.

Python remains reference authority for inherited, untransferred behaviour.

New behaviour without a predecessor may establish authority directly in:

- Godot for product/presentation semantics;
- native C++ for deterministic shared semantics;
- versioned declarative data for challenge/campaign content.

Stage 54D exercises three distinct lanes:

- next preview: Godot presentation of inherited queue state;
- ghost: Godot presentation over an inherited read-only landing query;
- Hold: new deterministic state requiring authority establishment.

Immediate governance requirements:

- keep `docs/architecture/authority_map.md` aligned with actual subsystem
  owners;
- use transfer records for inherited behaviour;
- use establishment records for genuinely new behaviour;
- do not create Python mirrors solely to manufacture parity;
- do not add placeholder authority-record rows without the required concrete
  evidence.

Potential future bounded reviews include explicit native transfer of existing
bounded gameplay and topology subsystems. Do not transfer the full gameplay
loop or topology system as one undifferentiated unit.

## Later Programme Phases

The following are accepted later phases, not current implementation scope.

### First-class topology games

- ordinary 2D setup choices for Bounded, Strip, and Möbius Strip;
- Strip/Möbius board-extent rules through the Stage 54B validation interface;
- later selected 3D/4D topology presets;
- exact canonical topology transport;
- visible seam/transformation feedback;
- no silent fallback to bounded play.

### Godot Explorer as spatial practice

- free movement on all axes, including Y;
- independent object rotation, 3D camera orientation, 4D view basis, slice
  axis, and active-slice state;
- exact camera quarter-turns;
- complete X/slice, Y/slice, and Z/slice basis exchange;
- topology inspection and transitions into Play;
- no duplicate movement or topology rule system.

### Challenge and learning system

- data-driven target-pose, camera, basis, navigation, placement, clearing, and
  topology challenges;
- declarative challenge/campaign authority;
- native deterministic predicates where required;
- Godot instructions, hints, progress, and campaign navigation;
- a four-dimensional challenge campaign that replaces the conventional
  tutorial as the primary curriculum.

### Unified simulation flow

- explicit transitions from game, Explorer, or challenge state into the
  existing explosion simulator and future physics systems;
- versioned conversion boundaries;
- no silent reinterpretation of gameplay state as physics state.

## Explicit Deferrals

- topology-aware Godot gameplay until the professional core-game gate is
  substantially complete;
- full Godot Topology Lab/editor migration;
- complete Explorer implementation;
- general challenge runner and campaign;
- unified gameplay/endgame/explosion launch integration;
- multi-piece next-queue display and configurable preview depth;
- ghost style/opacity menus;
- multiple Hold slots, Hold buffering, or competitive Hold variants;
- gamepad support, audio, and broad control-remapping work until their focused
  Phase I hardening slices;
- piece-record and migration/config-bundle import readers identified by the
  Stage 53E audit, pending owning-format evidence and focused acceptance tests;
- unrelated settings recovery identified by Stage 53E, pending individual
  stored-schema review and named migration-adapter evidence;
- Stage 53E retirement candidates that retain active callers, product/policy
  roles, benchmark roles, or released compatibility obligations;
- compaction or splitting of `docs/history/DONE_SUMMARIES.md`, which belongs to
  a separate documentation-hygiene batch and is not active product work.

## Python Movement-Graph Persistent-Cache Performance

Status: deferred pending a native movement-graph authority/representation
decision or user-facing latency evidence.

Stage 53F correctness is complete: malformed or incompatible cache data is a
derived-data miss, and valid cache acceptance remains bounded without full
graph construction.

The diagnostic 20³ benchmark measured direct construction at approximately
`.054` seconds and a cold strict JSON cache read at approximately `.318`
seconds. The cache therefore makes no cold-start performance claim.

This affects setup and topology transitions only; it has no steady-state
movement, rendering, collision, determinism, or frame-rate impact.

Revisit when:

- a native movement-graph representation is designed; or
- representative normal start/topology-switch latency exceeds the accepted
  product budget.

## Codex Routing Follow-Ups

The machine-readable authority pointers, task taxonomy, workflow modifiers,
and composable verification-requirement schema are implemented in Slice A.

Slice B is now implemented: the policy-backed resolver consumes the routing model,
enforces read-only and repository-change invariants, composes requirements by
union, emits scope matrices, and renders stable JSON or Markdown reports.

Accepted follow-up:

- **Slice C — path-sensitive CI lanes:** map resolved requirements to explicit
  baseline, governance, Python, Godot, native, deterministic/parity, packaging,
  platform, and release lanes with conservative full-gate fallback.

Measure Slice C only against the CI baseline after duplicate push/PR execution
has been removed. Do not combine either follow-up with Stage 54B-1 runtime work.

## Governance Watchlist

- Keep one semantic objective per PR.
- Use the implementation-stage boundaries in the professional programme.
- Require a scope matrix for deliberately cross-layer integration PRs.
- Never weaken tests to fit an implementation.
- Keep subsystem authority and transfer/establishment records aligned with
  actual ownership.
- Do not create Python implementations solely to preserve a universal-oracle
  claim.
- Keep invalid topology-profile storage non-saveable through ordinary update
  paths; read-only fallback is not mutation authority.
- Keep generated outputs tied to their source authority and generator.
- Record new warnings separately from known advisories.
- Keep all Tet4D GitHub writes on the verified owner identity for canonical
  `origin`, without publishing unrelated account or local identity details.

## Completion Boundary

Work is complete only when the stated acceptance criteria pass, authoritative
documentation is current, required checks are green, publication state is
reported, and the tracked worktree is clean.

Opening a branch or draft PR is not completion.
