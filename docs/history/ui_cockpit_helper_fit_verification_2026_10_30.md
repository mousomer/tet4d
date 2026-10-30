# Helper fit extraction and content invalidation — 2026-10-30

Base: `1a6dc9d0` on `codex/ui-cockpit-orchestration`. Scope: phase 2 helper-state
extraction and F2, plus public-API migration of the R2 fixtures. No manifest,
packing/geometry policy, gameplay, native or platform-support change.

## Design and implementation

- HelperFitState owns samples, search interval and transitions for one group;
  LiveCockpit retains measurement/application and the existing scheduler.
- Intrinsic content keys include text/font/control/theme inputs but exclude
  allocated size, fit scale and measured wrapping. Compaction keys normalize
  gaps to relaxed values, so a probe does not invalidate its own context.
- Changed content restarts at relaxed full scale and discards the old sample.
  Floor 0.6, search step 0.02 and settle limit 30 are unchanged.
- R2 fixtures now use public observe/snapshot transitions. The new state suite
  is registered in the canonical aggregate runner. No private fixture is used
  to preserve the old mutable dictionary shape.
- LiveCockpit loses 111 lines of mixed transition/search code; separate state
  and intrinsic-key helpers add explicit APIs. This is ownership separation,
  not a claim of total runtime LOC reduction or completed coordinator work.

## Relevant evidence

- `./gov check` passed. Task context resolves Godot product-shell authority.
- Pinned Godot: `4.7.2.stable.official.ed1daf0bf`.
- New real-control regression against the pre-extraction cockpit: four failures,
  twice failing clean-entry equivalence and larger-scale recovery after editing
  the same label from 40 lines to 16 lines at fixed host constraints.
- Final fresh isolated run: 6/6 scripts executed, zero returned failures, no
  script/parse errors: camera rig, helper fit state, live cockpit, locked shell
  layouts, presentation Designer, presentation profile library.
- The final cockpit regression also changes existing font metrics in both
  directions and compares settled scale with clean entry. State cases cover
  cancellation by larger room, rebuilt content and width; changed-content
  convergence; same-frame disagreement; and probe/compaction key invariance.
- Separate targeted run of `test_stage_58b_readability.gd`: 1/1 executed,
  zero failures and no script/parse errors. Its six-style 3D/4D matrix preserves
  drawn board scale, slice positions and camera fitting. Seven relevant suites
  passed across the two runs; this is not the full aggregate suite.
- An initial import caught a missing explicit bool annotation; corrected before
  the final fresh isolated run.
- `CODEX_MODE=1 python tools/governance/validate_handoff_lifecycle.py` passed.
- `CODEX_MODE=1 python tools/governance/validate_project_contracts.py` passed
  (126 required paths). `generate_maintenance_docs.py --check` passed.

Python is the interpreter resolved by `gov doctor` in the preceding batch.
Execution used the isolated project/user-data method described in
`ui_cockpit_focused_verification_2026_10_30.md`, with the six scripts above.
The macOS debug native extension was reused; native source remains unchanged.
The repository aggregate runner was not executed, and this evidence does not
claim the full gate, remote CI, fresh native build, manual 3D/4D review or new
screenshot parity. Historical observation bytes/source identity are untouched.

Scoped secrets/string sanitation over all 12 changed/new files and
`git diff --check` passed.

## Reviewed source identity

- `godot/Tet4D.Godot/scripts/ui/helper_fit_state.gd`: `3442be4560226eb30df365e0a42827bf17cab28345494b33ceca88f83d6b5c7a`
- `godot/Tet4D.Godot/scripts/ui/live_cockpit.gd`: `2c56ec18897b65f0a8b0a769a8e414c3764945e9349a53cd04516fa9bce2435a`
- `godot/Tet4D.Godot/scripts/ui/responsive_panel_policy.gd`: `117ca497b76dbfdc645bed9b3ac5ac29addf78b4c59fa52efa1b9b1613ab7cee`
- `godot/Tet4D.Godot/tests/test_helper_fit_state.gd`: `e3d8cfbb37ae54a35bcf5bcf2191dcabc964f620bc9f5e7abe3ed57152bc22b3`
- `godot/Tet4D.Godot/tests/test_live_cockpit.gd`: `b3874822b481a9dfc69586b1d4919f8d0eb0bf41f2808911b4a286b59b82463f`

## Publication correction

Remote CI run `41057922971` stopped at text formatting because the unchanged
historical observation copy lacked a final newline. The focused sanitizer
had treated those bytes as intentional provenance, while the canonical
formatter has no exception. Diff-only repetition missed the unchanged file.
The repository copy now appends exactly one LF; the manifest separately records
supplied and published hashes. The original bytes are recovered by removing
that single LF. Geometry and original source identity are unchanged.

`test_cockpit_baseline_publication.py` reproduces the failure before repair and
passes all three cases afterward, including actual formatter rejection and
acceptance in a temporary Git repository. The canonical
`scripts/check_text_formatting.sh` now passes and is a required relevant
pre-publication check even when functional testing is scoped.
