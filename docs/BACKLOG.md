# Tet4D Open Work

Updated: 2026-08-03
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

This backlog tracks the active product slice, immediate accepted follow-ups,
and deferrals whose resolution depends on product evidence or an authority
decision.

It does not duplicate the complete programme roadmap.

GitHub issues are for independently actionable, user-visible or reproducible
bugs and their collaboration lifecycle.

## Closed Programme

The short-term Python boundary-governance programme is complete.

Stage 53E is merged at `22938485`. Stage 53F and its corrective follow-up are
merged and verified on `master` at `91b901f3`.

Replay, trace/hash, gameplay configuration, movement-cache, topology-store,
and validation-ownership boundaries are strict. The separate movement-cache
performance item below is a product/representation deferral, not incomplete
correctness.

Do not create Stage 53G or reopen generic boundary-governance work without a
new evidenced problem and owning-format scope.

## Active Work

### Professional Godot core-game programme

Status: active.

Primary gate:

```text
PROFESSIONAL_CORE_GAME_READY
```

The first priority is a fully playable and professionally presented 4D Godot
game that is ready for later topology, Explorer, challenge, and simulation
extensions.

The programme is owned by
`docs/plans/professional_godot_game_programme.md`.

Stage 54A is complete, human accepted, and merged on `master` at `bcf41519`.
Its settled control and cockpit scope is not active backlog work.

### Stage 54B — Complete custom board configuration

Status: next implementation slice.

Objective:

- expose direct X/Y/Z/W axis-size editing for every active dimension;
- retain presets as shortcuts that populate editable fields;
- enforce one shared minimum/maximum authority;
- validate piece-set compatibility;
- persist the last valid setup;
- distinguish `Reset Sizes` from `Reset Setup`;
- preserve frozen active-session and restart semantics.

Stage 49 and Stage 50 remain accurate records of their curated-preset scope.
Stage 54B extends the active product boundary rather than rewriting those
records.

### Accepted immediate follow-ups

After Stage 54B:

1. Stage 54C — game-safe 4D slice-basis quarter-turns and focused instruction;
2. Stage 54D — modern one-slot Hold-piece gameplay across 2D/3D/4D;
3. Stage 54E — visible-GUI professional playability review and
   evidence-driven correction;
4. Stage 54F — remaining professional gaming-experience and release hardening.

Do not replace these new capabilities with another broad lifecycle-verification
framework.

Grid visibility: the live 3D/4D grid is currently too weak in some views.
Reassess grid contrast, opacity, and accessibility composition during the
Stage 54E visible-GUI playability review. This does not block Stage 54B,
Stage 54C, or Stage 54D.

## Authority Transition Work

The repository no longer treats Python as the universal semantic oracle.

Python remains reference authority for inherited, untransferred behaviour.

New behaviour without a predecessor may establish authority directly in:

- Godot for product/presentation semantics;
- native C++ for deterministic shared semantics;
- versioned declarative data for challenge/campaign content.

Immediate documentation/governance requirement:

- keep `docs/architecture/authority_map.md` aligned with actual subsystem
  owners;
- use transfer records for inherited behaviour;
- use establishment records for genuinely new behaviour;
- do not create Python mirrors solely to manufacture parity.

Potential future bounded reviews include explicit native transfer of existing
bounded gameplay and topology subsystems. Do not transfer the full gameplay
loop or topology system as one undifferentiated unit.

## Later Programme Phases

The following are accepted later phases, not current implementation scope.

### First-class topology games

- ordinary 2D setup choices for Bounded, Strip, and Möbius Strip;
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
- gamepad support, audio, and broad control-remapping work until their focused
  Phase I hardening slices;
- piece-record and migration/config-bundle import readers identified by the
  Stage 53E audit, pending owning-format evidence and focused acceptance tests;
- unrelated settings recovery identified by Stage 53E, pending individual
  stored-schema review and named migration-adapter evidence;
- Stage 53E retirement candidates that retain active callers, product/policy
  roles, benchmark roles, or released compatibility obligations.

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

## Governance Watchlist

- Keep one semantic objective per PR.
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
