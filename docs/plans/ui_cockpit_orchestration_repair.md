# UI and cockpit orchestration repair plan

## Decision, scope and status

Owner instruction, 2026-10-27: lock actual results and plan orchestration repairs,
including the preceding P2/P3 findings. Product behavior remains governed by
existing RDS and architecture authorities. This is a bounded Godot implementation
restructure within existing presentation ownership, not an authority transfer.

The normative preservation boundary is
`docs/design/ui_cockpit_result_lock_2026_10_27.md`; its source manifest identifies
the committed master baseline. Do not use a historical branch commit alone as a
substitute for the source/evidence records. Implementation starts on
`codex/ui-cockpit-orchestration` at master `e37441bb`, in a separate worktree.
The dirty release checkout is not the refactor base and is left untouched.
Master's CI classification and workflow changes are retained. Master
`9b2a7e43` was subsequently integrated at `91987bb1`, preserving its deck
reparent protection and next-frame metric checks alongside R1/R2. The original
pre-repair evidence identity remains `e37441bb`; no new baseline was promoted.

Status: result lock recorded; R1/R2 source fixes and regression cases prepared;
Seven relevant suites including state, locked layouts and style matrix pass.
Helper-state and ordinary coordinator/policy extraction are implemented;
Designer panel-session lifecycle is implemented; shell conversion remains pending.
The owner authorizes relevant tests; full gate, remote CI and
manual acceptance remain pending. F3 is fixed against the existing contract.
Evidence: `docs/history/ui_cockpit_focused_verification_2026_10_30.md`.
Scoped secrets/string sanitation covers the 16 changed/new files: no secrets
or newly introduced string/whitespace issues. Existing RDS formatting and the
byte-preserved observation file are retained. This is not functional evidence.

## Problem to solve

The subsystem split is useful: native execution owns gameplay; Godot owns
presentation, and profiles, controls and styling have dedicated components.
The coupling is concentrated in `ReplayHud` and `LiveCockpit`:

- HUD navigation, settings application, viewport transforms, helper fitting and
  Designer transitions reach into one another's private fields.
- Cockpit placement, measurement, compaction, scale-search state, node reparenting
  and deferred settling are mixed in one mutable control.
- Both signals and explicit deferred calls can request another layout. It is
  difficult to identify which context a measurement or callback belongs to.
- Camera fitting and rail budgeting need one geometric observation. Review found
  R1 mixing poses and R2 leaving abandoned fitting state busy; their repairs
  now have focused automated evidence; broader acceptance remains pending.

The goal is explicit ownership and bounded state transitions. Smaller files are
useful only when they remove shared mutable state and private cross-owner access.

## Immediate repairs

### R1: finish the pending orbit before fitting

Owner decision, 2026-10-27: Fit View finishes the requested mouse orbit
immediately, then computes the fit. Snap current yaw/pitch/roll to their existing
targets before any bounds projection. This is not a canonical-view reset and
changes no target, margin, topology or 4D local/basis semantics. Orbit interpolation outside fit requests continues unchanged.

Complete size, anchor, drawn-span and rail-demand calculation for that stable
pose, then notify relative-control consumers of the presented yaw change. The
following process tick cannot silently finish a different orientation.

Acceptance: an asymmetric cuboid has different current and target angles. Fit
finishes the pending orientation. Advance the camera afterward and project all
actual cuboid corners through Camera3D into the viewport; they must remain
contained and the pose/fit size must stay stable. Do not accept only immediate
assertions of the fit's cached span. The regression in `test_camera_rig.gd` uses
public pose snapshots, projected corners and the normal orientation signal.
The focused camera case passes. Full production rail/visual acceptance remains
a later gate.

### R2: cancel the whole helper-fit search

Keep cancellation local to the current owner. Clear search flag, both pending
measurement records, recorded search constraint and interval when relaxation,
rebuilt content or a changed constraint abandons a search. Return to full scale
and let a new context obtain fresh measurements. Do not leave diagnostic busy
state after the actual layout becomes idle.

Acceptance: interrupt an active search with a larger room and separately with
rebuilt content. Both paths return to relaxed full scale with no outstanding
measurement/search state and report settled. Add these state-transition cases
to `test_live_cockpit.gd`; later cover actual resize/rebuild sequences too.

## Intended ownership

`HelperFitState`, `CockpitLayoutCoordinator` and `CockpitLayoutPolicy` are
implemented, as is DesignerPanelSession. ShellViewportLayout remains proposed.
Keep them inside the owning Godot UI/presentation directories.

| Owner | Responsibility | Must not own |
| --- | --- | --- |
| `CameraRig` | Presented pose, fit observation, camera application; exposes board demand as presentation data. | HUD nodes, rail policy, native commands. |
| `ShellViewportLayout` | One conversion from actual client/backing pixels, UI scale and safe area into usable logical rectangles. | Preferences persistence, navigation, board/camera semantics. |
| `CockpitLayoutPolicy` | Compute placement, module order, budgets and row packing from an explicit context and measured metrics. | Scene-tree mutation, deferred callbacks, text shaping. |
| `HelperFitState` | Relaxed/compact/probing/scrolling transitions, constraints, pending samples and cancellation for one group. | Node references, native state, viewport allocation. |
| `CockpitLayoutCoordinator` | Own invalidation, measurement/apply phases, context generations and completion. | Product defaults, native rules, profile persistence. |
| `LiveCockpit` | Build slots, retain node references, measure controls and apply a decision through public methods. | A second policy/search scheduler. |
| `DesignerPanelSession` | Enter/leave detached layout, panel origins, geometry, ordering and synchronous restoration. | Profile composition/storage or camera refits. |
| `ReplayHud` | Compose surfaces, route navigation/settings intent and connect public owner APIs. | Fit-search internals, private frame dictionaries or duplicate coordinate conversion. |

Avoid a new general-purpose framework, global service locator or event bus.
Retain the existing `ResponsivePanelPolicy` and `FitScaleContainer` as small
mechanisms where suitable; do not create competing implementations.

## Data and lifecycle contracts

- A layout context names mode/product, placement preference, usable logical
  bounds, UI scale, density, guide/overlay state and camera-fit observation.
  Measured minimums/unwrapped widths carry the context generation they describe.
- Policy yields a decision: placement, module assignment, region budgets and
  required helper-fit actions. Policy does not query arbitrary scene nodes.
- Reflowed text still uses Godot's actual measurement; do not build a parallel
  font/layout engine or infer final wrapped height from a width formula.
- One coordinator coalesces invalidations. A change of width, height, UI scale,
  theme/content, mode, guide or Designer ownership advances the context and
  cancels superseded probes. Old deferred work cannot publish a new decision.
- Measurement, apply and completion are distinct. A stable same-generation
  observation may advance a helper fit. An unchanged decision writes no new overrides.
  An idle state has no scheduled work and no pending/search flags.
- Synchronous explicit Fit/Reset remains synchronous when visible geometry is
  valid; explicit Fit first finishes the pending orbit, per the owner decision. Do not replace it with arbitrary frame delays or a timer-based repair.
- Public APIs expose viewport/demand, layout decisions, session transitions and
  snapshots. HUD/app callers stop accessing cockpit private fields incrementally.
- Designer exit restores parents, order, visibility and layout modes before
  releasing frames. Close/reopen and pending callbacks cannot restore a newer
  session using an older session's state. Session geometry stays nonpersistent
  except through the existing explicit profile contract.

## Incremental delivery

| Phase | Work | Completion boundary |
| --- | --- | --- |
| 0 | Record result lock, source identity and evidence limits. | Accepted output is explicit; no new acceptance claim. |
| 1 | R1/R2 fixes only, with regression cases. | Focused camera/cockpit suites pass; broader integration and visual acceptance pending. |
| 2 | Extract `HelperFitState`; keep current policy and view tree. | One group owner, same decisions/floors; migrate R2 fixtures from `_fit_states` to the new public state/transition API in this same phase. |
| 3 | Separate policy/measurement/application; establish coordinator as the sole layout scheduler. | Same packing, budgets and result lock; obsolete callbacks cannot apply; idle work is bounded. |
| 4 | Extract Designer session lifecycle and replace private cross-owner access with public adapters. | Geometry/profile isolation and ordinary-layout restoration preserved. |
| 5 | Isolate shell coordinate conversion and reduce HUD to composition/routing. | One viewport/safe-area conversion; menu, setup, overlays and cockpit preserve results. |
| 6 | Review the final dependency flow and perform authorized acceptance. | Result lock, functional gates and owner visual review pass; no retained duplicate owners. |

Each phase is a separate reviewable commit when implementation is authorized.
Finish and review a phase before continuing. Move a bounded responsibility with
its consumers; do not keep the old and new owner permanently active. If a
phase changes the result lock, stop and seek an explicit product decision.
Do not combine extraction with UI polish or scale/framing changes.

## Acceptance and verification plan

Focused automated evidence is recorded separately; it does not establish all
functional or visual acceptance steps below. Relevant tests are now permitted.

0. Preserve the supplied 2026-10-26 observations (three identical runs, 410
   observations, zero recorded failures) as historical pre-repair evidence. See
   `docs/design/baselines/cockpit_windowed_2026_10_26/README.md`. Compare future
   same-environment runs by exact bytes first; inspect every difference rather
   than regenerating the baseline. Screenshots remain independently relevant.
1. Review the owning source and public callers; inspect encoding/literal escapes,
   secret exposure and diff sanitation. Keep existing test expectations intact.
2. Once permitted, run R1/R2 regressions and cancellation cases for mode changes,
   guide toggles, content/style rebuild, resize during probing and Designer
   close/reopen. Compare clean entry with the same context reached by transitions.
3. Preserve native hashes/commands, Relative/Absolute movement, held-input timing,
   Stage 57 restart, saved profiles and explicit A/B/Designer semantics. Keep the
   mandatory translation runner and its CI marker/lane selection.
4. Compare settled regions, drawn content and independently projected content
   corners across the locked windows/modes/styles. Do not use only the fit
   method's own reported span as its correctness oracle. Preserve no clipping,
   no needless helper scrolling and backing-pixel render density.
5. When authorized, run the focused suites, then serial canonical repository and
   pinned Godot gates. Real macOS fullscreen/HiDPI and other device/platform
   claims require their own evidence. Hosted CI is separate from local evidence.
6. Owner review compares the accepted screens before/after at actual window sizes,
   with any visible differences identified. A passing geometry check or source
   manifest does not establish visual acceptance.

Keep unexecuted acceptance boundaries explicitly pending.
Do not publish/merge these changes as functionally accepted or silently mark
future gates complete. Record authorized evidence before completing a phase.

## Exclusions and rollback

No HUD redesign, control removal, new defaults, scale/framing retuning, depth or
contrast work, W-label tracking, grid topology/material changes, gameplay/native
semantics, packaging/platform support change or governance-pack migration.
The stale shown-slot A/B preview is separate; extracting session plumbing must
preserve current behavior and must not silently expand into repairing it.

Keep result locks and evidence when reverting a failed extraction. Revert only
the responsible phase through a reviewed ordinary Git change; never reset the
working tree over pre-existing edits. Review fixes can be retained independently
of the broader extraction. User confirmation is needed for product deviations,
not for routine implementation choices inside the locked behavior.

## Review reconciliation and remaining limits

The supplied review correctly identifies the transient-pose weakness in the
first R1 attempt. Its statement that `_process()` clears `_fit_span` does not
match current master/source: it updates the camera and emits orientation change,
without that clearing operation. The stale final-fit problem still stands.
R2 is retained. R1 now follows the owner's explicit finish-orbit decision.

R2 fixtures now use the public HelperFitState transition interface and are
registered in `test_helper_fit_state.gd`; they no longer inject `_fit_states`.
Private-field compatibility is not part of the result lock. Other existing
private-field tests are migrated with their owning phase, not used to prevent it.
Existing recordings and source inspection do not establish fresh execution,
rendering, or owner acceptance of either repair.

## Continued static review

R1/R2 and the result lock were committed and pushed at `52986aa2` before the
continued review. The findings and exact source paths are recorded in
`docs/plans/ui_cockpit_code_review_2026_10_27.md`; backlog status remains open.

- F1: include input/render-space delta conversion in phase 5's shell boundary;
  preserve current pan signs and prove root-space movement across display scales.
- F2: helper state now invalidates completed fits on intrinsic content/theme
  changes, excluding allocation/scale probes. Existing-label and font edits
  match clean-entry results. Phase 3 now owns generation-bound queued work and pure policy decisions.
- F3: repaired group Reset against the current saved/loaded baseline, with
  focused Load/Save/Save As regressions passing before phase 4 extraction.
- F4: keep laboratory capture settling and asynchronous identity validation as
  an adjacent explicit follow-up; do not hide it inside the cockpit extraction.
- F5: documentation reconciliation is implemented across the owning camera
  contract, authority map and dependent Fit references. Evidence metadata now
  uses a portable capture ID; screenshots still need an external bundle.
  The immediate handoff boundary is integrated R1/R2 acceptance. That batch established no functional or visual acceptance; subsequent focused
  evidence is recorded in the verification history.

The original review was static. F3 now uses the saved/loaded baseline and
passes regression cases after Load, Save and Save As. Shell extraction and F1/F4 work remain open. Phase 2 and F2 have focused evidence in
`docs/history/ui_cockpit_helper_fit_verification_2026_10_30.md`; broader
integration/visual gates remain pending.

Review fixes after the first completed remote Godot lane (resize round trip,
stale Designer test read, fit replay on height-neutral edits) are recorded in
`docs/history/ui_cockpit_review_fixes_verification_2026_10_30.md`.

Phase 3 implementation and evidence are recorded in
`docs/history/ui_cockpit_coordinator_verification_2026_10_30.md`. The coordinator
owns scheduling revisions; measurements are read fresh rather than stored in
queued callbacks. No accepted visual parameters or layout results are retuned.

Phase 4 delegates detached panel lifecycle to DesignerPanelSession and replaces
HUD access to cockpit host/constraint internals with public APIs. Synchronous
restoration and session-revision guards protect close/reopen. Evidence and
remaining limits: `docs/history/designer_panel_session_verification_2026_10_30.md`.
