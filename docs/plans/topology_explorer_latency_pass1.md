# Topology Explorer Latency Reduction Pass 1

Status date: 2026-03-12
Status source of truth: [docs/plans/topology_playground_current_authority.md](docs/plans/topology_playground_current_authority.md)
Historical migration audit: `docs/history/topology_playground/topology_playground_reality_audit.md`
Performance/functional source of truth: [docs/history/topology_playground/topology_explorer_functional_audit.md](docs/history/topology_playground/topology_explorer_functional_audit.md)
Completed UI-cleanup context only:
- [docs/history/topology_playground/topology_explorer_menu_audit.md](docs/history/topology_playground/topology_explorer_menu_audit.md)
- [docs/history/topology_playground/topology_explorer_menu_cleanup_pass1.md](docs/history/topology_playground/topology_explorer_menu_cleanup_pass1.md)

## Scope

This pass only reduces the concrete migrated-path latency hot spots called out by the functional audit. It does not reopen completed migration stages, broaden into topology-engine redesign, or remove retained legacy branches outside the audited paths.

## Reduced Hot Paths

- Duplicate dimension-change orchestration
  - _cycle_dimension(...) now marks the explorer state dirty before _sync_explorer_state(...) and stops re-entering _mark_updated(...) on the migrated path.
  - Result: one canonical sync plus one scene refresh remain on the real dimension-change path instead of the earlier sync/refresh pass followed by a second cached post-pass.
- Launch-only Piece Set / Speed edits
  - _mark_play_settings_updated(...) now compares the effective ExplorerPreviewCompileSignature before and after the setting change.
  - When the signature is unchanged, the migrated path updates launch settings only and skips scene refresh entirely.
- Export Explorer Preview
  - _run_export(...) now reuses state.scene_preview when state.scene_preview_signature still matches the current export request.
  - Runtime export writes the provided live preview payload with the export source label instead of recompiling the preview graph.
- Build Experiment Pack
  - _run_experiments(...) now compiles the batch once, stores it in state.experiment_batch, and exports that same payload.
  - Runtime experiment export writes the provided batch instead of rerunning compile_parallel_explorer_experiments(...).

## Measured Effect

Measurement basis for the post-change numbers below:
- 4D migrated explorer path
- explicit empty explorer profile
- default uild_explorer_playground_settings(...) board sizes
- same interaction-timing hooks used by the functional audit

Measured after this pass:
- Export Explorer Preview: audit baseline 402.8 ms -> 2.1 ms handler / 1.9 ms export-call phase when the live preview signature already matches the export request.
- Build Experiment Pack: audit baseline 10.31 s -> 5185.7 ms handler, split into 5183.3 ms compile + 2.3 ms export after removing the second full-pack compile.
- Dimension: migrated-path interaction audit now records exactly one canonical_sync span and one scene_refresh span for the dimension-change handler.

## What Was Short-Circuited Or Reused

- Reused the already-compiled live preview payload for export when the live scene signature equals the export signature.
- Reused the just-compiled experiment batch payload for export instead of rebuilding the pack.
- Short-circuited Piece Set and Speed edits when only launch settings changed and the preview signature stayed stable.
- Bypassed the redundant post-sync _mark_updated(...) refresh path for the migrated dimension-change flow.

## What Still Remains Slow

- First 4D preview compile on explorer entry.
- 4D topology-mutation rebuilds for Board X/Y/Z/W, Explorer Preset, Apply, and Remove; these still block on synchronous uild_movement_graph(...) work.
- Unsafe preset families still pay the same compile cost and can still leave the preview invalid on unsupported board sizes.

## Next Latency Stage

If a follow-up latency stage is opened, it should stay narrow and target the remaining synchronous 4D preview rebuilds on Board *, Explorer Preset, Apply, and Remove without broadening into a general topology-engine redesign.
