# Supplied pre-repair cockpit evidence

The owner supplied these historical 2026-10-26 runs during review on
2026-10-27. They are not executions performed by this change.

- `observations.json` is the exact byte copy of run 1.
- All three supplied runs: 410 observations and zero recorded failures;
  SHA-256 `9687a9225c3b95d29affe4d748f658148c31c437c1cbbabebc450f8b7ded9ca9`.
- `manifest.json` records run identities, reported environment/source and 358
  screenshot hashes. PNGs remain at the external directory named there.
- `source-note.txt` retains the supplied provenance note without rewriting it.

The reported runtime is master `bda1abe7`, before R1/R2. Current implementation
starts at master `e37441bb`, which adds owner workflow/CI classification. Source
identity and environment must be reconciled before claiming exact output parity.

For each future authorized phase, compare an equivalent run's observation bytes
with this file, then inspect every changed field and corresponding screenshot.
A difference is evidence to explain, not permission to replace the baseline.
Unchanged bytes are useful geometry evidence but do not replace corner checks,
input/native checks, screenshot review or owner acceptance. Per-run metadata
may differ; any approved normalization must be explicit and preserve geometry.
No comparison run, test or screenshot review was performed in this pass.
