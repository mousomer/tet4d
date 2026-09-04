# Tet4D Open Work

Updated: 2026-09-02
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
