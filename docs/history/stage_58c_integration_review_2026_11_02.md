# Stage 58C integration review — 2026-11-02

Integration retains the original renderer tuning, merges master through
`84c06016`, corrects the four historical evidence inaccuracies identified on
PR #154, and adds a scaffold instance/generation/node-identity assertion.
Owner-reported acceptance is recorded separately in
`stage_58c_owner_acceptance_2026_11_02.md`.

## Automated evidence

- Approved Python source-mode environment resolves to this review checkout.
- Pinned Godot is `4.7.2.stable.official.ed1daf0bf`; godot-cpp is the declared
  `5ffd70e34d0ab87009a9f0ffa3361bc8f4b09731` checkout.
- Focused Stage 58C, trace-renderer and live-presentation scripts reported zero
  findings. The direct probe encountered sandbox user-log writes; it is not
  used as the authoritative full-gate result.
- The normal isolated `scripts/verify_godot_4_7.sh` passed all 96 scripts,
  59 shared topology-transport cases, extension API checks and boot checks.
  It retains the known macOS ObjectDB snapshot-storage advisory.
- That gate ran on integration `d2c580e4`. The subsequent acceptance/history
  documentation preserves the exact Godot-project tree
  `b2e219d58db92aaf62afb9544b14156ce00b9ce5`.
- Native sources are unchanged. Local execution reused the existing macOS
  debug framework and verified the pinned extension/API boundary; this does
  not claim a fresh local native compilation.

## Current Metal inspection

The production-renderer capture harness ran on Apple M1 Pro / Metal Forward+
with 2× pixel density. Eight paired captures compare master `84c06016` with
the integrated renderer using identical fixture, effective profile and image
resolution records: blue active pieces, `3d_moderate` and `4d_seven`, Arcade
Neon and High Contrast, Border and Full at the reference board-region sizes.
The same harness executed against each project's renderer with `masks=0`;
no new numerical lightness or performance measurement is inferred.

Agent comparison confirms the intended stronger active-piece presentation,
rear-cell/slice recession and reduced Full-lattice interference in these
fixtures. It does not replace interactive owner acceptance, certify every
view/style combination, or establish historical PNG parity. The generated
captures remain local review artifacts rather than promoted design baselines.

Reproduce with `tests/run_spatial_readability_capture.gd`, filters
`scenes=3d_moderate,4d_seven`, `styles=arcade_neon,high_contrast_access`,
`grids=border,full`, `sizes=ref`, `colors=6`, `scale=2`, `masks=0`.
