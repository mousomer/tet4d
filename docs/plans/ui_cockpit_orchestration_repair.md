# UI and cockpit orchestration repair plan

Updated: 2026-10-30. Implementation base: `5f139ef2`, with F4 in this change, on
`codex/ui-cockpit-orchestration`, draft PR #162. This document owns sequencing
and acceptance; `docs/BACKLOG.md` owns open-task status and `docs/history/`
owns execution records. Planned work below is not implemented evidence.

## Goal and authority

Finish the UI orchestration repairs with explicit ownership, bounded deferred
work and trustworthy capture provenance. Preserve the accepted screens and
interaction behavior. File size alone is not an extraction criterion.

Authorities: `docs/design/ui_cockpit_result_lock_2026_10_27.md`,
`docs/architecture/godot_shell_layout_stabilization.md`,
`docs/architecture/camera_gui_preset_semantics.md`,
`docs/architecture/live_presentation_designer.md`,
`docs/architecture/design_evaluation_laboratory.md`, the 3D/4D RDS and
`docs/architecture/authority_map.md`. Governance and verification follow the
project dispatcher and `docs/governance/CHANGE_GOVERNANCE.md` and
`docs/governance/VERIFICATION.md`. No semantic authority transfer is proposed.

The locked source/evidence baseline remains master `e37441bb`; master
`9b2a7e43` was integrated at `91987bb1`. Neither later implementation nor a
passing CI run silently promotes a new visual baseline. Preserve the supplied
2026-10-26 observations and provenance, including the separately documented
publication-only final-LF correction. Leave other checkouts untouched.

## Current implementation and evidence

| Work | Implementation | Remaining acceptance |
| --- | --- | --- |
| R1: Fit finishes the existing pending orbit, then fits | Implemented; actual projected-corner regression and orientation notification | Integrated rail/visual review |
| R2: cancel abandoned helper search and pending samples | Implemented; public HelperFitState transition coverage | Integrated transition/manual review |
| Phase 2 / F2: helper state and intrinsic-content invalidation | Implemented; height-neutral edits preserve settled fits | Integrated review |
| Phase 3: sole cockpit scheduler and pure layout policy | Implemented; generation-bound callbacks; resize-roundtrip fix retained | Final dependency audit |
| Phase 4: DesignerPanelSession lifecycle | Implemented; synchronous restoration and close/reopen regression | Integrated Designer review |
| F3: group Reset uses saved/loaded baseline | Implemented; Load, Save and Save As regressions | Integrated Designer review |
| Phase 5 / F1: shell conversions and pan distance | Implemented at `2049ff26`; old input handler reproduces four failures | Physical pointer/HiDPI review |
| F5: Fit documentation consistency | Reconciled | Preserve during final docs review |
| F4: settled, identity-safe laboratory capture | Implemented; focused and real-window 3D/4D pair capture pass | Final integrated/owner review |
| Final composition review, full gate and owner acceptance | Dependency review and local gates completed; publication CI/owner review pending | Steps 5–6 below |

At `2049ff26`, 12 focused scripts and the separate six-style 3D/4D matrix
passed. Publication formatting, scoped sanitation and governance checks passed.
Claude base `32752f8b` completed remote CI successfully; run `41103770668` for
`2049ff26` also completed successfully. This is a dated snapshot,
not a claim about a future head. The final local repository and pinned Godot gates passed (94 scripts and
59 shared transport cases). Exact publication-head CI and owner acceptance
remain required.

Evidence: `docs/history/ui_cockpit_focused_verification_2026_10_30.md`,
`ui_cockpit_helper_fit_verification_2026_10_30.md`,
`ui_cockpit_coordinator_verification_2026_10_30.md`,
`designer_panel_session_verification_2026_10_30.md`,
`ui_cockpit_review_fixes_verification_2026_10_30.md` and
`shell_viewport_layout_verification_2026_10_30.md`,
`helper_fit_idle_verification_2026_10_30.md`,
`inactive_cockpit_verification_2026_10_30.md` and
`design_capture_verification_2026_10_30.md`, all under `docs/history/`.
Historical static findings remain in
`docs/plans/ui_cockpit_code_review_2026_10_27.md`; current status is above.

## Ownership to preserve

| Owner | Responsibility | Boundary |
| --- | --- | --- |
| CameraRig | Pose, fit, projection and render-pixel pan | No HUD policy, native commands or root-input conversion |
| ShellViewportLayout | Pure client/UI/safe-area/rectangle and delta conversions | No OS queries, persistence or camera semantics |
| GameplayViewportSurface | Actual logical/render extents and canvas transform | No assumed density or second input stretch conversion |
| CockpitLayoutPolicy | Placement, packing and numeric budgets | No nodes, scheduling or font engine |
| HelperFitState | One group's fit transitions, samples and cancellation | No scene references or deferred work |
| CockpitLayoutCoordinator | Ordinary layout scheduling, generations and idle state | No profile storage or duplicate policy |
| LiveCockpit | Build, measure and apply decisions to controls | No second scheduler or private state shared with HUD |
| DesignerPanelSession | Detached ownership, frame geometry and synchronous restoration | No profile semantics or camera refits |
| ReplayHud | Compose surfaces, query environment and route public owner APIs | No duplicate conversion or lifecycle/search internals |
| DesignComparisonSession | Frozen arms, shown arm and comparison identity | No renderer or capture scheduling |
| Laboratory capture orchestration | Coordinate readiness, request lifetime and identity checks | No replacement gameplay fingerprint or comparison store |
| DesignCaptureStore | Persist images and their validated provenance | No guessing whether the renderer is settled |

Prefer public adapters on existing owners. Introduce a small capture operation
owner only if request lifetime cannot stay clear in the panel; avoid a generic
workflow framework, global event bus or second layout scheduler.

## Step 1 — establish the exact implementation checkpoint

1. Read current local/remote heads, worktree changes, PR state and CI results.
   Preserve unrelated work and retain the existing draft PR.
2. Resolve governance routes and pinned runtime. Inspect any new upstream diff
   before integrating it; do not assume an earlier green run covers new code.
3. Review unresolved failures first. Preserve Claude's resize-roundtrip,
   height-neutral fit and public Designer-surface test fixes.
4. Record the base for the F4 commit and the applicable evidence set.

Acceptance: exact source identity is recorded; every failing/pending lane is
accounted for. No code change is required merely to refresh status.

## Step 2 — define and expose capture readiness

First update the laboratory and shell architecture contracts with the bounded
capture handshake. Trace existing coordinator, helper-fit, HUD layout and app
presentation-guard owners; use their public state rather than private polling.

The readiness observation must identify the presentation/layout revision and
report whether ordinary layout work, helper probes, viewport sizing and the
app's profile-application guard have completed. Coordinator generation alone
is insufficient unless every relevant producer participates. A content/theme,
window/UI-scale, mode or ownership change invalidates the observation.

Wait for a settled observation, then a draw of that state, then revalidate it.
A draw is necessary for pixels but is not proof that layout has settled. A
process-frame count, arbitrary sleep or cached fit span is not a substitute.
Use a bounded wait with a diagnostic failure, and cancellation on owner teardown;
a headless test must not hang waiting for a draw signal it cannot receive.
Choose the bound through the existing configuration convention and observed
settling behavior; document it instead of scattering magic constants.

Acceptance: a public readiness adapter correctly distinguishes pending,
settled, superseded and cancelled work. Fit remains synchronous where visible
geometry is valid. Existing layout choices and camera targets are unchanged.

## Step 3 — repair F4 capture lifetime and provenance

Implement one active capture operation per laboratory panel. Reject a second
request while busy with a clear status; do not queue an unbounded request list.
Disable capture controls while active, but also enforce serialization in code.
Mutations from other paths must still invalidate the operation.

1. Before activation, freeze request/session identity, both arm snapshot hashes,
   requested arm, scenario/non-style fingerprint and the original shown arm.
2. Activate through the existing profile-application path and verify success.
3. Await Step 2 readiness. After every asynchronous boundary, revalidate request
   lifetime, comparison identity, requested shown arm, hashes and fingerprint.
4. After the matching draw, read pixels and revalidate again before storage.
   Use the frozen validated metadata, not a fresh unrelated session snapshot.
5. Abort diagnostically on timeout, changed identity, close, teardown or failed
   application. A stale operation cannot write images or restore an old arm.
6. For a pair, use one operation identity for A and B. Each image must carry its
   own validated arm provenance. Report a partial failure honestly; never claim
   a complete pair unless both succeed. Preserve valid existing captures and
   avoid destructive cleanup or an unnecessary capture-schema migration.
7. Restore the originally shown arm after pair success or recoverable failure
   only while this operation still owns the unchanged comparison. Await its
   readiness; report restoration failure separately from capture success.
8. Release busy state through one completion/cancellation path. An older
   completion cannot clear a newer operation's state.

Required regression cases:

- Multi-pass fitting and profile guard: no image/store call before readiness.
- Layout revision changes during settling and between settling and drawing.
- Arm reassignment, new comparison, scenario reset and fingerprint change while
  awaiting; stale requests write nothing and cannot restore the old arm.
- Duplicate single/pair request, panel close/reopen and teardown while waiting.
- Timeout, failed apply, image read failure, store failure and pair partial
  failure; busy state clears and a later valid request can succeed.
- Successful A/B pair: exact arm hashes and non-style identity match each image;
  original shown arm is restored without gameplay commands or profile writes.

Use controllable completion/draw adapters for deterministic lifecycle tests,
then a production runtime integration case with actual multi-pass layout.
Register cases in the existing laboratory runners. Demonstrate the old one-draw
path fails the regression without weakening assertions. Real rendered PNG
acceptance remains separate from headless sequencing evidence.

Acceptance: pixels and metadata belong to the same settled frozen arm; stale
operations cannot publish. The laboratory's complete-profile and blind-label
contracts, immutable comparison arms and native fingerprint authority hold.
Deliver the handshake and its F4 consumer together if either alone would leave
an unused or incomplete API; keep that commit separate from broad cleanup.

## Step 4 — finish the dependency and composition review

Trace public entry points through app → HUD → cockpit/session/layout owners.
Review navigation, settings/profile application, mode changes, guides, ordinary
versus detached layouts, window/safe-area changes and shutdown. Check for:

- Remaining private cross-owner calls, including HUD access to laboratory
  comparison/activation internals; replace only verified boundary violations
  with narrow public operations that preserve behavior.
- Duplicate conversion, policy or scheduling owners and stale deferred work.
- Measurements retained across changed contexts, tree-exit callbacks affecting
  new sessions, and tests coupled to removed private implementation fields.
- Main-menu fit invalidation on intrinsic content/theme changes. This was a
  review concern, not a reproduced defect; promote it only with a concrete
  normal-user trigger and a failing behavior regression.

For each finding, record trigger, consequence, owner and bounded repair. Fix
confirmed in-scope defects separately with relevant tests. Do not extract every
remaining HUD responsibility for file-size reduction. Record unresolved debt
explicitly and remove duplicate dead paths only when their callers are known.

Acceptance: final dependency flow has one owner per concern; no newly retained
private lifecycle/search dependency or speculative defect is marked resolved.

## Step 5 — integrated automated and human acceptance

Run focused checks first against the actual final diff. Relevant tests are
authorized. Include camera, shell conversion, helper/coordinator/fit container,
responsive resize history, density hierarchy, locked layouts, Designer/session,
profile library and laboratory capture/runtime suites; repeat the style matrix.
Use the manifest-pinned runtime and declared interpreter. Expand only for new
changes, failures or unresolved risk. Record reused versus freshly built native
artifacts. Never treat a script/parse error as an empty passing result.

Before completion, run `CODEX_MODE=1 ./scripts/verify.sh` and the declared pinned
Godot verification path serially, or explicitly retain any user-restricted or
blocked gate as outstanding. Include canonical text formatting, applicable Ruff
format/lint, semantic-boundary, generated-document freshness, handoff and
secrets/string checks. Verify CI selection includes the mandatory translation
runner/marker and all diff-required lanes. Do not bypass failures or redefine
scanner rules to manufacture a pass.

Manual review uses the existing local launch recipe and seeded settings at
1280×720, 1280×800 and fullscreen on macOS, plus small/wide resize round trips.
Cover 2D navigation preservation and actual 3D/4D gameplay. Verify:

- Fit during eased orbit finishes the requested pose; no subsequent clipping.
- Pointer-distance pan at actual UI/HiDPI scales; reflection signs unchanged.
- Helpers settle without stale busy state, needless scrolling or visible
  height-neutral fit replay after NEXT/HOLD changes.
- Designer open/close/reopen, detached placement, profiles and all Reset paths.
- Capture under differing arm UI scale/density; inspect PNGs and metadata,
  interrupt pending capture, and confirm safe recovery.
- Stage 57 controls/restart, movement modes, input timing, native state identity,
  grid semantics, style-invariant board geometry and backing-pixel rendering.

Compare same-environment observations by exact bytes first; inspect differences
rather than regenerating the lock. Inspect screenshots independently. Record
source, seed/settings, runtime, platform/window, expected/observed result and
owner verdict. Hosted CI does not substitute for manual or other-device proof.

## Step 6 — publish, review and close

Update owning contracts before finalizing changed semantics; keep backlog,
CURRENT_STATE and evidence records consistent. Commit bounded phases separately.
Run the applicable publication gate, push, then inspect CI for that exact head;
fix failures and verify the replacement head. Keep PR title/body aligned with
the final implementation and list remaining manual/device limitations.

Merge only when required CI and integrated acceptance are satisfied under the
existing owner authorization. Verify the merged master SHA and its remote CI;
a green feature-head run is not merged-master proof. Confirm local/remote state
and leave a clean handoff. Mark R1/R2 and the overall programme complete only
when their remaining acceptance is recorded, not when source extraction ends.

## Exclusions, rollback and completion boundary

No HUD redesign, removed controls, new defaults, scale/framing retuning, grid
or Border/Full changes, gameplay/native semantics, packaging support change or
governance migration. Depth/contrast hierarchy belongs to 58C; W-label tracking
belongs to Stage 59. The stale Designer A/B preview remains separate unless an
explicit scope decision brings it in. F4 touches capture orchestration only.

Revert a failed bounded phase through an ordinary reviewed commit, preserving
result locks, evidence and unrelated work. Stop for an owner product decision
if a repair requires changing the accepted screens or interaction contract.
Completion requires F4 correctness, resolved in-scope review findings, applicable
local and remote gates, recorded manual acceptance and verified integration.
