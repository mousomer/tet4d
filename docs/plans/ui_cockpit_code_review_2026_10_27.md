# UI and cockpit static code review — 2026-10-27

## Identity, scope and evidence

Reviewed commit: `52986aa296b3fd423c52f50b08b62e7fc49bc31d`, published on
`codex/ui-cockpit-orchestration`, based on master `e37441bb`. The remote branch
identity was read back after push. This is a static source review, not runtime
reproduction or visual acceptance. No functional tests, application, capture or
CI were run. The owner permits only secrets and string-sanitation checks.
The local test-running pre-push hook was omitted for publication under that
instruction; normal verification remains outstanding.

The review traces `ReplayHud`, `LiveCockpit`, `CameraRig`,
`GameplayViewportSurface`, `FitScaleContainer`, `ResponsivePanelPolicy`,
`DesignerPanelFrame`, `PresentationDesigner`, and their app callers. Adjacent
piece/view strips, NEXT/HOLD, comparison preview and laboratory capture paths
were inspected for ownership and invalidation. This is not an exhaustive audit
of native gameplay, persistence, all renderers, packaging or the entire repo.

Acceptance for this review: distinguish bugs from structural debt; identify a
concrete trigger, code path, consequence and bounded repair for each finding;
preserve the result lock and keep unexecuted evidence explicitly pending.
Authorities consulted include the 3D/4D RDS, shell stabilization contract,
live Designer contract, laboratory capture contract and authority map.

## Findings

### F1 / P2 — panning mixes root input units and render pixels

`camera_rig.gd:345–361` divides the incoming delta by the gameplay SubViewport's
render height. The app's `_handle_camera_input` passes `event.relative` from
the root viewport unchanged (`trace_replay_app.gd:337`). The world is shown
through a TextureRect; the event is not forwarded into that SubViewport.
`gameplay_viewport_surface.gd:29–36` deliberately multiplies logical size by
the canvas/window transform when choosing render resolution.

At a 2× render-to-root display scale, a drag of 12 root units moves the image
by about 6 root units. Enlarged UI and window stretch introduce the same
dependency. The existing camera regression checks direction within the render
viewport, so it does not establish pointer-following magnitude in the shell.

Repair: convert root deltas into gameplay texture coordinates once at the app/
surface boundary, or pass an explicit root-space surface extent to the camera.
Preserve the current reflection/sign convention. Future acceptance: project a
probe through the real surface transform and compare its root-space movement
with a drag at 1×, 2× and enlarged UI, for reflected and unreflected views.

### F2 / P2 — finished helper fits ignore changed content metrics

`live_cockpit.gd:783–806` invalidates a scaled fit only when host width or room
changes. Once `searching` is false, an agreed new natural height simply returns
the old scale. `_fit_height` refreshes the relaxed-height bound only at full
scale, and fresh-compaction detection identifies new containers, not edits to
existing labels or theme metrics.

Trigger: let a group complete a scaled fit, then change existing content at the
same host width and height. HOLD's existing status label changes between
`Available · C` and `Used until lock`; at a wrapping boundary its height changes
without rebuilding the containers. Theme spacing can change existing metrics
too. A larger measured group may begin scrolling despite being able to fit at
a smaller scale; a smaller group may stay unnecessarily shrunken. The existing
R2 cancellation repair does not invalidate this completed fit.

Repair: key settled fit results and relaxed measurements by content/theme
generation as well as constraints. Distinguish a real context change from the
measurement changes caused by the search's own probes. Future acceptance:
increase and decrease existing-label height after a completed fit, without
rebuilding nodes or resizing the host; compare with clean entry into each final
context. Implement with `HelperFitState` and coordinator invalidation.

### F3 / P2 — group Reset ignores the saved/loaded baseline

`presentation_designer.gd:313–320` restores an owner's values from
`_opening_profile`. In contrast, parameter Reset uses `_saved_profile_baseline`,
and Save, Save As and Load replace that baseline through `_set_loaded_profile`
at lines 1097–1102. The Designer architecture explicitly requires parameter and
group Reset to use the complete saved/opening working baseline.

Trigger: open with value X, load or save a design with value Y, edit to Z, then
press the owner's Reset. The group returns to X while individual Reset and
Revert return to Y. A subsequent save can persist the unintended old values.
The existing group-reset case only covers the original opening baseline.

Resolution, 2026-10-30: group Reset now reads the saved/loaded baseline and
its tooltip explains that boundary. New regression cases fail on the old code
after Save As, Save and Load, and pass on the repaired code. They check another
owner, frozen comparison and write-count isolation through public APIs. See
`docs/history/ui_cockpit_focused_verification_2026_10_30.md`.

Repair: resolve one current reset baseline and use it for both parameter and
owner reset, including the displayed message. Future acceptance: exercise
group Reset after Load, Save and Save As, with an opening profile distinct from
the new baseline. Include another owner to prove the reset stays bounded.

### F4 / P2 — capture treats one drawn frame as settled layout

`design_laboratory_panel.gd:483–487` returns success after just
`RenderingServer.frame_post_draw`. Single and paired capture immediately read
the image afterward. Applying a complete arm can change UI scale, density and
geometry, while cockpit fitting explicitly needs samples across frame
boundaries and can perform multiple search probes. The app's presentation guard
also spans two process frames. One render event is not the owning layout's
completion signal.

Trigger: capture a comparison whose complete designs alter layout in a
constrained window. The first drawn frame can contain an intermediate viewport
and camera fit, yet the PNG receives the frozen arm's provenance. The capture
path also does not revalidate comparison revision/arm/fingerprint after its
await; a second capture or arm mutation can supersede the pending operation.
The laboratory architecture requires settled rendering and stable non-style
identity throughout capture.

Repair: wait for a bounded same-generation layout-completion signal and a draw
of that generation; revalidate session, arm snapshot and fingerprint before
writing. Serialize capture requests or cancel superseded ones. Future acceptance:
capture arms requiring multiple fit passes, interrupt one with a new comparison,
and verify pixels/metadata refer to the same settled arm. Keep this as an
adjacent follow-up, not an unreviewed expansion of the current extraction.

### F5 / P3 — authority map omits the approved Fit exception

`docs/architecture/authority_map.md:43` still says Fit View is framing-only.
The updated RDS and shell contract now explicitly allow completion of the
pending requested orbit before fitting. Clarify that exception in the map;
do not change the target orientation or canonical-reset semantics. This is a
documentation mismatch, not another requested runtime behavior change.

Resolution, 2026-10-30: the owning camera contract, authority map, keybindings
and dependent architecture references now describe the pending-orbit exception.
The associated documentation compliance repairs also replace the absolute
capture path with a portable ID and make the immediate handoff boundary clear.
This closes F5 at documentation level; R1/R2 runtime acceptance remains pending.

## Structural assessment and prior findings

The repo has meaningful subsystem boundaries. Gameplay/native semantics,
profiles, settings, styling and presentation components are distinct. The
concentrated problem is orchestration: `ReplayHud` combines composition,
navigation, settings, coordinate conversion and Designer lifecycle;
`LiveCockpit` combines scene-tree ownership, placement, measurement, search and
scheduling. Private access and shared mutable state make context invalidation
difficult to follow. The assessment is modular subsystems with tangled UI
orchestration, rather than a uniformly unstructured codebase.

R1 now completes the requested orbit before fitting and emits the presented-yaw
notification after the fit. Its new case checks actual corners after advancing
the camera; it has not run. R2 now clears abandoned search and pending state;
its fixture remains private-state based until the planned extraction. Neither
is closed by this review. The earlier stale Designer A/B-preview item remains
separate. This review does not reopen scale/framing tuning, grid topology,
58C contrast work or Stage 59 label tracking.

The main-menu overflow ceiling is also cached by room alone. Content-generation
invalidation deserves coverage during shell extraction, but this pass does not
promote it to a confirmed additional product defect without a sufficiently
established normal-user trigger.

## Delivery boundary

No further runtime fixes or broad extraction were made in this review. The
backlog owns status; the repair plan maps F1–F3 into bounded work and preserves
F4 as an adjacent follow-up. Each repair needs its own future regression and
the applicable product/integration/manual evidence once tests are authorized.
The required full gate remains `CODEX_MODE=1 ./scripts/verify.sh`; it was not run.
