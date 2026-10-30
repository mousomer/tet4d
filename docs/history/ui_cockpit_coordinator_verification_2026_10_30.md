# Cockpit coordinator/policy verification — 2026-10-30

Base: `ea44af90` plus the separate Ruff formatting correction `ccbef2e6`.
Scope: phase 3 ordinary cockpit scheduling and pure layout decision extraction.
Route: Godot product shell, bounded structural change under the existing shell
and result-lock contracts. No manifest, native, grid, style or platform changes.

## Ownership and preservation

- One coordinator coalesces metric/fit requests, cancels superseded callbacks,
  advances scheduling generations for synchronous context changes, and cancels
  work on ownership change/exit. No old scene measurements are stored in work.
- Pure policy receives scalar/dictionary measurements and returns decisions.
  LiveCockpit measures/applies; HelperFitState owns its existing search.
- Numeric policy, packing order, scale floor and visual parameters are retained.
  Synchronous setters stay synchronous; queued metrics stay on the next frame.
- Deferred Designer constraints and Godot container sort notifications remain at
  their existing boundaries. This phase does not claim Designer session or shell
  conversion extraction, pan conversion, capture completion or full acceptance.

## Relevant evidence

Pinned Godot: `4.7.2.stable.official.ed1daf0bf`, isolated project and user data,
with the existing debug native extension as in the earlier focused records.
Final source run: 7/7 suites, zero failures or script/parse errors: camera rig,
cockpit layout coordinator, helper fit state, live cockpit, locked shell layouts,
presentation Designer, presentation profile library. Separate six-style 3D/4D
readability suite: 1/1 passed. These eight suites are not the aggregate full gate.

Coordinator coverage exercises burst coalescing, required-fit precedence,
synchronous generation advancement, cancellation of obsolete queued work,
Designer-style ownership invalidation, continuation during application, idle
completion and teardown cancellation. Policy coverage checks packing boundaries,
module order, split fallback and the readable row floor. Existing production
regressions exercise visibility propagation, content invalidation and locked
layouts; the style matrix checks board scale, slice positions and camera fitting.

## Remote CI boundary

Run `41063217103` passed CI plan/baseline after the final-LF correction. Its
Python and documentation jobs then failed `ruff_format` on the new publication
regression: lint had passed, but the separate formatter had not been run.
Commit `ccbef2e6` applies pinned Ruff formatting; Ruff lint, formatting and all
three publication regressions pass locally. The relevant pre-publication set
must include both canonical text formatting and Ruff formatting for Python
changes. Overall remote CI remains pending for the resulting new commit.

Full repository gate, full Godot runner, fresh native build, platform/device and
manual acceptance are not claimed. Original baseline/source identity and the
declared final-LF representation are preserved.

Governance context, project contracts (126 required paths), handoff lifecycle
and generated maintenance-document checks passed. Canonical tracked-text
formatting, pinned Ruff lint/format for the publication regression, scoped
secrets/string sanitation and diff whitespace passed. CURRENT_STATE stays at
150 lines. No full pre-push test gate is claimed from these focused checks.
