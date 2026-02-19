# Plan: 4D Render Gap Closure (2026-02-19)

Status: Completed  
Scope: Close 4 remaining gaps after 4D cache/zoom correctness fixes.

## 1. Goals

1. Run full local CI wrapper and confirm no hidden regressions.
2. Add black-box render-cache regression coverage for cross-config `W`-size changes.
3. Profile 4D render path after hyper-aware zoom fitting and quantify overhead.
4. Normalize open `P3` backlog items into explicit, actionable maintenance entries.

## 2. RDS Alignment

Reference: `docs/rds/RDS_4D_TETRIS.md`

Aligned requirements:
1. Projection cache keys must include full layer-view context including total `W` size.
2. Per-layer zoom fit must remain robust under `xw`/`zw` hyper-view turns.
3. Regression tests must cover cache separation and view-fit behavior.

## 3. Execution Steps

1. CI wrapper validation:
1. Run `scripts/ci_check.sh`.
2. Resolve any blocking failures and rerun until green.

2. Black-box cache regression:
1. Add test-safe cache observability helpers in `tetris_nd/projection3d.py`.
2. Add full-frame cross-config regression in `tetris_nd/tests/test_front4d_render.py`.
3. Validate that both `W=3` and `W=4` cache entries coexist after consecutive frame draws.

3. Render profiling:
1. Add `tools/profile_4d_render.py`.
2. Measure baseline and hyper-view scenarios over repeated frame draws.
3. Emit average/frame and relative overhead report.
4. Apply optimization only if overhead exceeds threshold (`>15%` or `>2.0 ms/frame` in default scene).

4. Backlog normalization:
1. Convert open `P3` lines in `docs/BACKLOG.md` to explicit entries with IDs, cadence, trigger, and done criteria.
2. Add canonical-maintenance structure checks for backlog entry format.

## 4. Deliverables

1. Updated tests and cache observability helper API.
2. Profiling tool and documented output.
3. Updated backlog structure and maintenance contract rules.
4. Changelog entries for this gap-closure batch.

## 5. Acceptance Criteria

1. `scripts/ci_check.sh` passes.
2. New black-box cache regression test passes and fails if `W`-size cache context is removed.
3. Profiling output is recorded and overhead status is explicit (within threshold or mitigated).
4. Open `P3` backlog items are actionable and machine-checkable for structure.

## 6. Execution Results

1. Local CI wrapper passed (`scripts/ci_check.sh`) after final edits.
2. Black-box frame-cache regression was added to `tetris_nd/tests/test_front4d_render.py` and is passing.
3. Profiling report was generated at `state/bench/4d_render_profile_latest.json`.
4. Sparse-scenario overhead threshold check passed (`--assert-threshold`): no mitigation required.
5. Open `P3` backlog entries were normalized to structured IDs with cadence/trigger/done fields.
