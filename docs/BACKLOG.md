# Tet4D Open Work

Updated: 2026-09-07
Scope: active work, explicit deferrals, and near-term acceptance boundaries.

Completed chronology is recoverable from Git, merged PRs, CI, and
`docs/history/`. Programme sequencing and long-horizon intent live under
`docs/plans/`; this file does not duplicate either layer. Earlier detail is in
`docs/history/backlog_archive_2026-07-30.md`.

## Current Authority

- Product programme: `docs/plans/professional_godot_game_programme.md`
- Product behaviour: relevant `docs/rds/*`
- Architecture: `docs/ARCHITECTURE_CONTRACT.md` and
  `docs/architecture/authority_map.md`
- Authority transfer: `docs/architecture/authority_transfer_protocol.md`
- Topology/Explorer: `docs/architecture/topology_playground_current_authority.md`
- Human governance: `AGENTS.md` and the six owners under `docs/governance/`
- Machine governance: `config/project/policy_pack.json`

## Active Work

### Worktree-local verification bootstrap

Provide `scripts/verify_local.sh` as a worktree-local `.venv` cache and
launcher for the canonical `scripts/verify.sh` gate. It must fingerprint only
packaging inputs and interpreter major/minor version, preserve the existing
editable-install ownership check, avoid repeat network/bootstrap work, and
never duplicate the verification graph.

`--rebuild-venv` now refuses before deletion when its selected bootstrap is
inside the `.venv` being replaced. Follow-up: separately review operator
confirmation and recovery messaging for other destructive recreation cases.

The inherited overlay now serves bootstrap, certified selection and execution
mode; two-worktree operation is certified sequentially and concurrently.

With inherited bootstrap active, the selected bootstrap is external to the
worktree, so `--rebuild-venv` may now regard it as safe and permit rebuilding
`.venv`, including replacing a symlink-farm entry with a real environment. That
refusal previously fired on every worktree here. Deferred to the `verify_local`
retirement/rework rather than patched under bootstrap inheritance; symlink-farm
removal remains blocked until then.

Constraint for any future dependency fingerprint over an inherited environment:
a digest of project inputs records what this repository declares, not what the
shared environment contains, and projects outside this workspace mutate that
environment. Treat an unchanged fingerprint as an optimisation, never as
evidence the environment still satisfies the declaration; keep a content check
as the correctness statement. `packaging>=24` is the worked example.

### Camera and relative-control contract

Unify the Godot presentation contract for exact camera basis turns, slice
orientation, and Relative translation without changing native gameplay,
deterministic identity, or accepted 4D resolver behaviour. Issue #74 requires
2D screen-left/right and 3D screen-left/right plus Forward-away/Back-approach
to agree across resolver output, camera basis, direction helpers, and help.

Acceptance boundary:

- exact camera pairs are XZ `1/2`, XW `3/4`, and ZW `5/6`; the public and
  tutorial progression remains XW, ZW, XZ;
- `LiveInputContract` owns shared piece/camera rotation descriptors and 4D
  keeps the existing `B + Q(L.local_yaw)` resolver semantics; `O/L` preserve
  local-yaw decrement/increment without rotating the outer camera rig; and
- coordinate/framing changes are limited to the Stage 55B exact-basis fit
  contract and need independent mapper-oracle coverage.

Cockpit allocation, NEXT/HOLD redesign, grid/spacing polish, and issues
#69/#70 remain separate PR3–PR5 work. Stage 55 semantic export is available
only as reproducible, non-authoritative investigation tooling. Its compact
projection retains runtime provenance when generated wrappers are elided; it
is not a canonical design workflow and its generated captures remain untracked.

### Stage 56 cockpit completion

Complete the accepted cockpit direction through serial green stages. Stage
56A repaired the Live-4D orientation rosette as a passive consumer of the
existing `B + L + ControlFrameMapping` presentation snapshot. Stage 56B now
provides deterministic viewport-aware, activity-independent slice tiling and
records bounded repair 56B-R for settled HUD viewport ownership and manual-fit
preservation. Stage 56C now renders PIECE and VIEW as shared passive semantic
rows whose labels are injected from `LiveInputContract` across all densities.
Stage 56D extracts the Header, PrimaryBoardSurface, and three-module
ControlDeck allocation into the authority-free `LiveCockpit` shell. Stage 56E
has now migrated Live 3D with a larger primary board and dimension-filtered
PIECE/VIEW rows. Stage 56F has now migrated Live 2D and has implementation and
automated evidence complete; its regression evidence is independent of
machine-local onboarding preferences while preserving the profile-owned
guidance setting. Responsive acceptance, human playability/overlay acceptance,
final polish, and the 190/200 human A/B choice remain gated as Stages 56G–56I.

### Three-product packaging gaps

Implement the missing package identities required by the authoritative
`product_platform_contract` without treating transitional jobs as support.

Acceptance boundary:

- The shared Godot tree now has explicit game and Designer bootstrap/profile
  selection; this establishes identity and startup separation only, not new
  platform support or a 0.9.0 release profile.
- Product-profile staging must reject the canonical Godot project and every
  resolved descendant as an export target; disposable staging remains outside
  the source tree and does not alter product identity or platform support.

- Godot game / Windows and Godot game / Linux need distinct distributable
  packages and acceptance; the existing Windows package is Designer only;
- Godot game / Android and Godot game / iPadOS must replace the transitional
  Designer-identity tablet exports with game identity and entry semantics;
- the iPadOS game implementation must resolve godot-cpp static-link composition
  and simulator architecture compatibility; and
- Designer / macOS needs a genuinely distinct application identity and entry
  contract; renaming the current `Tet4D.app` game ZIP is insufficient.

The existing Python macOS/Windows/Linux packages, Godot game macOS package, and
Designer Windows package are implemented cells and remain separate evidence
from runtime acceptance or publication. Their release filename templates must
remain bound to their product's canonical `artifact_name_token`; the
transitional tablet consumers retain Designer naming only under their closed,
named status exception.

### 0.9.0 release-control boundary

The 0.9.0 release-control path may release an arbitrary validated subset of the
seven registered packaging consumers without changing the ten-cell product
target matrix. The expected first candidate is the Godot game macOS consumer
and the Designer Windows consumer, but that pair is not hard-coded: the manual
candidate workflow accepts registered `consumer_id` scope and records the exact
selected bytes in a v2 manifest before it creates a draft. A separate manual
publication workflow can publish only that inspected, byte-validated draft.

The initial full-matrix candidate remains blocked until the Windows Designer
validator proves exported identity through the PCK resource table rather than
source configuration text. This narrow blocker is tracked by the active task
record `docs/tasks/windows_designer_package_identity_validation.md`; it does
not authorize another candidate dispatch or alter release scope.

This operational readiness does not close any missing target cell. Godot game
Windows/Linux/Android/iPadOS and Designer macOS remain separate package and
acceptance work. The transitional Designer Android artifact and transitional
Designer iPadOS artifact remain technical evidence under their machine
identifiers; they do not become supported Designer platforms or game packages.

The repaired grandfathered `legacy_designer_ipados` package path provides
technical evidence for native archive composition, matching godot-cpp linkage,
truthful `arm64` device and `x86_64` simulator slices, XCFramework/native-symbol
validation, and an unsigned hosted simulator final link. It remains
transitional evidence only; it does not promote Designer/iPadOS or close the
Godot game/iPadOS target gap.

## Accepted Next Product Boundaries

- Stage 54F-6 default style selection/polish must consume reviewed human Design
  Laboratory evidence. See
  `docs/plans/design_evaluation_laboratory_acceptance.md`.
- Topology, Explorer, challenge, and simulation work must begin as a new
  approved stage under the relevant plan and architecture owners.
- Path-sensitive CI Slice C may map evidence to explicit lanes only after
  duplicate push/PR execution is measured and removed; retain a conservative
  full-gate fallback.

## Explicit Deferrals

### Workspace governance extraction

- v0.1 retains `config/project/policy_pack.json` as authority for unmigrated
  Tet4D-specific facts. Future extraction should migrate one bounded fact family
  at a time with generated/validated compatibility output.
- General prompt classification, runtime execution graphs, cross-repository
  orchestration, migration engines, and planner/runner redesign remain deferred.
- Round 2 hardens bootstrap diagnostics, canonical-owner coverage, field-use
  mutation evidence, and executable contradiction fixtures. Generic generated
  documents and the Godot-namespaced full-gate pointer remain deferred.
- The v0.1 integrity repair makes project routes canonical and retains legacy
  routes only as a parity-validated facade. Do not extract another policy family
  until the repaired contract receives independent review.
- The vendored v0.1 pack is internally integrity-checked here; upstream
  canonical reconstruction or export of that pack remains deferred.

### Release and platform

- Clean-machine Windows and iPadOS runtime acceptance remain real-platform
  evidence, not claims inferred from macOS or package structure.
- Hosted CI platform lanes exist for macOS and iPadOS only. `platform_windows`,
  `platform_linux`, and `platform_android` are declared manual in
  `config/project/codex_ci_lanes.json`: a change to those packaging paths
  reports outstanding platform evidence instead of borrowing another platform's
  job. Adding those hosted lanes needs their own scope and runner contract.
- Developer ID signing/notarization and broader distribution are separate
  release prerequisites.

### Product and presentation

- First-class topology games, complete Godot Topology Lab/Explorer, the general
  challenge/campaign runner, and unified gameplay-to-simulation flow remain in
  `docs/plans/`.
- Multi-piece next preview, configurable preview depth, ghost style/opacity,
  multiple/buffered Hold, gamepad, audio, and broad remapping require separate
  product slices.
- Non-blocking polish remains for Live-4D volume legibility, the pause badge,
  narrow-window clipping, replay-list keyboard access, very-small windows,
  HiDPI defaults, and window size/position persistence.

### Migration and compatibility

- Piece-record and migration/config-bundle readers require owning-format
  evidence and focused acceptance tests.
- Settings recovery requires stored-schema review and named adapter evidence.
- Stage 53E candidates with active callers, product/policy roles, benchmark
  roles, or released compatibility obligations remain retained.
- `codex/explosion-architecture-inventory` remains a manual-review candidate
  under a separate authorized task because it may contain unique changes.

### Engineering debt

- `TD-0001`: Godot presentation/trace constant advisories. Trigger: before
  strict config-authority mode.
- `TD-0002`: duplicate bridge/native trace-export helper-name advisories.
  Trigger: before strict utility-reuse mode.
- `TD-0004`: reproducible clang-format, clang-tidy, and
  `compile_commands.json`. Trigger: before strict native tooling in CI.
- Python movement-graph persistent caching remains deferred until a native
  representation decision or representative latency evidence; current
  diagnostics show no cold-start benefit.
- `docs/history/DONE_SUMMARIES.md` compaction is a separate history-hygiene
  batch.

## Governance Watchlist

- Keep one semantic objective per PR and use scope matrices for cross-layer
  integration.
- Never weaken tests, deterministic identity, replay/schema compatibility,
  sanitation, or explicit deferrals.
- Keep authority records aligned with actual ownership; do not manufacture
  Python mirrors for new authority.
- Keep generated outputs tied to their source and generator.
- Keep invalid topology-profile storage non-saveable through ordinary updates.
- Record new warnings separately from known advisories.

## Completion Boundary

Work is complete only when acceptance passes, authorities are current, required
checks are green, publication state is reported, and the worktree is clean. A
branch or draft PR alone is not completion.
