# Tet4D Open Work

Updated: 2026-09-01
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

### Re-governance PR 3

Lock the PR 1/PR 2 model against ownership drift, append-only lifecycle growth,
unowned validator policy, and active-context expansion.

Acceptance boundary:

- exactly six canonical human owners and compositional routes remain;
- all active routes resolve and none enters history;
- active governance is at most 2,500 lines;
- canonically serialized `policy_pack.json` is at most 1,000 lines and 80,000
  bytes;
- `CURRENT_STATE.md` is at most 150 lines and this file at most 250;
- provenance derives exactly from the real Python/shell enforcement graph,
  broadened lifecycle variants fail, and precise volatile-count gates pass;
- focused, adversarial, generated-document, sanitation, and full verification
  are green.

Stop after this cut. Windows/iPad release remediation is separate work.

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

- `codex/windows-release-without-debug-records` remains frozen through the
  governance cut. Reconcile it separately after PR 3 merges.
- Clean-machine Windows and iPadOS runtime acceptance remain real-platform
  evidence, not claims inferred from macOS or package structure.
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
