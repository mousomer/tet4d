# Tet4D Open Work

Updated: 2026-08-05
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

## Closed Programme

The short-term Python boundary-governance programme is complete.

Stage 53E is merged at `22938485`. Stage 53F and its corrective follow-up are
merged and verified on `master` at `91b901f3`.

Stage 54A is complete, human accepted, and merged on `master` at `bcf41519`.
Its settled control and cockpit scope is not active backlog work.

Stage 54B-2 is complete and verified on the active branch. It adds editable
Godot board dimensions, native-validation presentation, and schema-3
last-valid setup persistence without changing gameplay or topology semantics.

Stage 54C is complete and verified on its implementation branch. It adds an
exact Godot-owned signed 4D presentation basis, shared slice reconstruction,
basis-aware controls/HUD/instruction, and deterministic invariance evidence
without changing native gameplay or topology semantics.

Stage 54D-1 implementation and mechanical verification are complete on its
implementation branch, with commit still pending. Developer-rendered
inspection is complete; human preview-readability acceptance remains pending
under Stage 54E. The slice adds one authoritative next-piece query plus a
shared compact Godot 2D/3D/4D thumbnail without changing queue, RNG, snapshot,
hash, replay, or trace semantics.

Do not create Stage 53G or reopen generic boundary-governance work without a
new evidenced problem and owning-format scope.

## Active Work

Primary gate:

```text
PROFESSIONAL_CORE_GAME_READY
```

The first priority is a fully playable and professionally presented 4D Godot
game that is ready for later topology, Explorer, challenge, and simulation
extensions.

The programme is owned by
`docs/plans/professional_godot_game_programme.md`.

## Next Implementation Stage

### Stage 54D-2 — Ghost piece

Status: next implementation slice after Stage 54D-1 is committed separately.

Render the exact authoritative hard-drop destination across every affected
slice without changing scoring, collision, lock, snapshot, hash, replay, or
trace semantics.

## Accepted Immediate Follow-Ups

### Stage 54D — Modern gameplay baseline

Status: Stage 54D-1 implementation complete with commit pending; Stage 54D-2
is next only after that separate commit decision.

Implement as three separate PRs in dependency order.

#### Stage 54D-1 — Next-piece preview

- display exactly one authoritative next piece in live 2D/3D/4D play;
- create one shared 2D/3D/4D piece-thumbnail presentation;
- reuse that presentation later for `HOLD`;
- do not change queue, snapshot, hash, replay, trace, or RNG semantics.

#### Stage 54D-2 — Ghost piece

- render the exact authoritative hard-drop destination;
- show every occupied destination cell across all affected 4D slices;
- expose `Ghost: On / Off`, default `On`;
- do not calculate drop legality independently in GDScript;
- add only a bounded read-only core query if no existing landing query is
  available;
- keep ghost state out of snapshots, hashes, replay identity, scoring,
  collision, and lock state.

#### Stage 54D-3 — Hold

- implement the modern one-slot Hold rule;
- reuse the Stage 54D-1 thumbnail presentation;
- define snapshot, hash, replay, trace, compatibility, restart, and spawn-failure
  behaviour;
- create and complete an `AE-####` authority-establishment record only when the
  implementation contract and evidence are concrete;
- update the authority map when the record reaches `established`.

Do not add an incomplete Hold row to the active establishment table in advance.

### Stage 54E — Visible-GUI professional playability review

Status: after integrated Stage 54B–54D behaviour.

Review representative 2D/3D/4D play with primary emphasis on 4D, including:

- custom setup usability;
- basis-rotation comprehension;
- next-piece and Hold preview readability;
- ghost usefulness and cross-slice comprehension;
- distinction among ghost, active, and locked cells;
- grid contrast and visibility;
- camera recovery;
- menu hierarchy;
- accessibility and minimum viewport composition;
- representative board-size responsiveness.

Stage 54E completes when review evidence is recorded, findings are classified,
and every `PROFESSIONAL_CORE_GAME_READY` blocker is corrected and re-reviewed
or remains an explicit blocker preventing the gate from passing.

Grid visibility: the live 3D/4D grid is currently too weak in some views.
Reassess it during Stage 54E. This does not block Stage 54B, Stage 54C, or Stage
54D. Strengthening becomes mandatory only if review evidence classifies the
current grid as blocking comprehension or accessibility.

### Stage 54F — Professional release hardening

Status: after Stage 54E gate findings.

Use focused slices for demonstrated needs such as:

- keybinding/remapping completion;
- gamepad support if adopted;
- audio and volume controls;
- pause/game-over polish;
- scoring and progression presentation;
- performance correction;
- installer/export/startup reliability;
- release help and final manual acceptance.

Do not turn Stage 54F into an unbounded cleanup programme.

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
