# Tet4D Open Work

Updated: 2026-08-08
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
anchor-only, and `W=1` contracts. The renderer remains on the compatibility
`G_D(p) + anchor_i` path. This implementation is reviewed and accepted green;
Stage 54E-2b is next and eligible.

## Hold

### Stage 54D-3 — Hold

Status: unblocked deterministic-core work after the 54E-1 acceptance record
is merged.

Hold does not require 54E-2. Its shared thumbnail dependency is already
satisfied by 54D-1. Its eventual implementation must establish the one-slot
deterministic contract and complete its concrete `AE-####` record; do not add
a placeholder authority record in advance.

## Forward Work

- Stage 54E-2b — renderer composition (NEXT / ELIGIBLE).
- Stage 54E-2c — interaction and camera-rig separation (blocked until
  reviewed-green 54E-2b).
- Stage 54E-2d — lifecycle, authority, and contract reconciliation (blocked
  until reviewed-green 54E-2c).
- Stage 54E-3 — setup/menu information architecture.
- Stage 54E-4 — camera/GUI presets.
- Stage 54E-5 — cockpit consolidation.
- Stage 54F — integrated professional playability/visual acceptance.
- Stage 54G — professional gaming-experience and release hardening.

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
