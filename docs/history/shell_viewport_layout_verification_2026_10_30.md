# Shell viewport conversion verification — 2026-10-30

Base: `32752f8b` (Claude's resize/fit/test fixes). Scope: phase 5 shell
conversion and F1 pan distance inside existing Godot presentation authority.
No manifest, native, profile schema, grid, allocation or scale-parameter changes.

## Implementation and acceptance

ShellViewportLayout owns pure window/UI/safe-area/rectangle conversions formerly
embedded in ReplayHud. Existing references, floors, rounding and public wrapper
methods are retained. ReplayHud keeps OS queries, application and composition.
GameplayViewportSurface supplies its current transform and actual render extent
for root-input delta conversion. The app passes render pixels to CameraRig;
reflection/direction, camera fitting and accepted layout results are preserved.
Acceptance: projected movement equals input distance across density/UI scales,
and the existing responsive, cockpit, Designer and style checks remain green.

## Regression evidence

Pinned Godot `4.7.2.stable.official.ed1daf0bf`, isolated copied project and user
data, reused debug native extension; no fresh native build. The new registered
suite checks safe-area/UI and HiDPI conversions, zero-size guards, actual camera
projection across 3 UI transforms × 4 render densities × 2 reflection states,
and the real app input handler in 3D/4D at standard/large UI scale.

Replacing only the app input handler with committed `32752f8b` reproduces four
failures: a (12, -7) root drag moves the board approximately (6, -3.5) at standard
UI scale and (6.9, -4.025) at large scale. The corrected handler passes all four.
After resizing the viewport, the test waits a frame for projection state before
measuring; it does not change tolerances to hide an unsettled camera projection.

Focused shell-only run: 1/1 passed. Separate six-style 3D/4D readability matrix:
1/1 passed. Expanded focused run: 12/12 passed, zero failures and no script/parse
errors: camera rig, shell viewport layout, fit container, Stage 56G responsive
cockpit, cockpit density hierarchy, coordinator, Designer session, helper state,
live cockpit, locked layouts, Designer and profile library.

Governance check, semantic-boundary scan (198 scripts), aggregate governance,
generated-document freshness, handoff lifecycle, canonical text formatting,
Ruff lint/format on the publication regression and scoped secrets/string checks
passed. Existing governance advisories remain; local native tooling is advisory.
CURRENT_STATE remains 150 lines. These are synthetic root-space events, not physical HiDPI mouse
or visual acceptance. Complete local gate, fresh native build and manual device
acceptance are not claimed for this phase.

## Publication and remaining work

Claude base remote run `41097196667` completed successfully, including selected
Godot/native lanes. That result applies to `32752f8b`, not this new diff.
F4 capture settling/fingerprint revalidation remains open; broader HUD composition
review and manual integrated acceptance are separate. Stage 58B scale stays
frozen and original baseline/provenance bytes remain unchanged.
