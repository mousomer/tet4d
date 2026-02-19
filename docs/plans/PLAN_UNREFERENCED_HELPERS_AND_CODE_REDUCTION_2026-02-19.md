# Plan: Unreferenced Helpers, Deduplication, and Code Reduction (2026-02-19)

Status: Partially completed (unreferenced-helper cleanup + profiler path scope done; setup-menu dedup pending)  
Related backlog item: `BKL-P2-007`

## 1. Definitions

1. `Unreferenced helper`: a function/method that has no call sites in production code paths within this repository (excluding its own definition and optional tests).
2. `Dead code`: code that is unreachable or has no meaningful runtime effect.
3. `Duplicate logic`: near-identical behavior implemented in multiple files/functions that can drift.

## 2. Are unreferenced helpers overhead?

1. Runtime overhead is usually near-zero if never called.
2. Maintenance overhead is real:
3. extra LOC and API surface,
4. higher review cost and cognitive load,
5. misleading extension points,
6. higher chance of stale behavior assumptions.

Conclusion:
1. Unreferenced helpers should be either:
2. removed, or
3. explicitly documented and wired to clear call paths.

## 3. Current high-value opportunities

1. Remove or wire currently unreferenced helpers found in review (project-config/menu/runtime helpers).
2. Deduplicate setup menu rendering/value-format paths currently split between:
3. `tetris_nd/frontend_nd.py`,
4. `tetris_nd/front3d_setup.py`.
5. Keep profiler outputs sandboxed to project root only (implemented in this batch for:
6. `tools/profile_4d_render.py`,
7. `tools/bench_playbot.py`,
8. `tools/analyze_playbot_policies.py`).

### 3.1 Current unreferenced-helper candidate list (verified via `rg`)

1. `tetris_nd/frontend_nd.py`: `menu_fields_for_dimension`
2. `tetris_nd/menu_keybinding_shortcuts.py`: `menu_binding_hint_line`
3. `tetris_nd/menu_model.py`: `clamp_int`
4. `tetris_nd/project_config.py`: `reset_project_config_cache`
5. `tetris_nd/project_config.py`: `score_events_file_default_path`
6. `tetris_nd/project_config.py`: `score_summary_file_default_path`
7. `tetris_nd/score_analyzer.py`: `score_analyzer_settings_snapshot`

Classification result (2026-02-19):
1. `remove`: all seven candidates above.
2. `wire`: none.
3. `keep-with-justification`: none.

## 4. Implementation plan

1. Build a verified candidate list:
2. static reference scan + direct `rg` call-site confirmation.
3. classify each candidate as:
4. remove,
5. wire-in (missing call path),
6. keep (intentional API/export) with inline justification.

2. Deduplicate setup menu code:
1. extract shared setup menu draw primitives (layout calc, row rendering, hints/status rendering),
2. extract shared value-format adapter,
3. keep dimension-specific field lists and labels as thin config/data layers.

3. Sanitization and robustness:
1. keep all file outputs repo-local unless explicitly required otherwise,
2. re-check path handling via project-config helpers for state outputs.

4. Verification:
1. `ruff check .`
2. `ruff check . --select C901`
3. `pytest -q`
4. `scripts/ci_check.sh`

## 5. Acceptance criteria

1. No stale unreferenced-helper candidates remain without explicit justification.
2. Setup menu draw/value logic duplication is reduced with parity preserved.
3. No profiler can write outside project root.
4. Docs/backlog/changelog are synchronized with the changes.

## 6. Execution update (2026-02-19)

1. Removed unreferenced helper definitions:
2. `tetris_nd/frontend_nd.py`: `menu_fields_for_dimension`
3. `tetris_nd/menu_keybinding_shortcuts.py`: `menu_binding_hint_line`
4. `tetris_nd/menu_model.py`: `clamp_int`
5. `tetris_nd/project_config.py`: `reset_project_config_cache`
6. `tetris_nd/project_config.py`: `score_events_file_default_path`
7. `tetris_nd/project_config.py`: `score_summary_file_default_path`
8. `tetris_nd/score_analyzer.py`: `score_analyzer_settings_snapshot`
9. Path restriction check remains enforced for profiler/policy tools:
10. `tools/profile_4d_render.py`
11. `tools/bench_playbot.py`
12. `tools/analyze_playbot_policies.py`
13. Remaining open scope in `BKL-P2-007`: setup-menu render/value dedup extraction.
