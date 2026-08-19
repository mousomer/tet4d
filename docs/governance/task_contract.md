# Task Contract — Stage 54E-4b View / Camera Runtime

## Objective

Implement the independently reviewed-green Stage 54E-4a contract without
reopening its product decisions. The target handoff is Stage 54E-4b
`IMPLEMENTED / READY_FOR_FOCUSED_VISIBLE_REVIEW`; aggregate Stage 54E-4 remains
open until that focused real-window review is accepted.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `staged_handoff`.
- Affected layers: Godot product shell, tests, documentation, and governance.
- Required evidence: `godot`, `integration`, `human_visual`, `documentation`,
  and `governance_structure`.
- Full repository gate: required because the implementation consumes an
  architecture authority and changes shared camera/lifecycle behavior.

## Current Authority

- `docs/architecture/camera_gui_preset_semantics.md` owns the accepted view
  lifecycle, operation, action, reset, fit, and preference contract.
- `docs/architecture/4d_presentation_interaction_architecture.md` owns the
  accepted `B/L/layout/V/P` separation.
- `docs/architecture/authority_map.md` and `docs/ARCHITECTURE_CONTRACT.md` own
  subsystem boundaries.
- `docs/plans/professional_godot_game_programme.md`, `docs/BACKLOG.md`, and
  `CURRENT_STATE.md` own programme and handoff status.

Authority effect: implement within existing Godot presentation authority. No
native deterministic gameplay or Python authority transfer is performed.

## Allowed Systems and Paths

- Godot camera rig, app orchestration, HUD/help/onboarding, and settings
  registry paths required by the accepted contract;
- focused Godot tests for those contracts; and
- owning architecture, generated settings reference, programme, backlog,
  current-state, and governance records.

## Required Changes

1. Split canonical outer orientation and framing into
   `establish_outer_view()`, `fit_current_bounds()`, and
   `restore_fitted_framing()` with disjoint snap paths.
2. Compose mode-aware canonical entry/reset in the app: flat orthographic 2D,
   the accepted 3D mount, canonical `B/L/layout` plus accepted reflected outer
   mount for Live 4D, and the replay-owned mount.
3. Make Restart Game and same-context New Random Game preserve current view;
   clear transient view on setup/menu/mode exit and establish canonical view on
   re-entry.
4. Retire continuous preset identity, `Custom`, pseudo-preset status labels,
   ID-owned framing, and zero-caller `frame_board()`.
5. Present the six retained IDs as stateless view actions, hide them in 2D,
   expose one composite Reset View, and correct help/onboarding text.
6. Route `display.ui_scale` to Accessibility reset ownership without changing
   its persistent ID or schema.
7. Add executable state-ownership, reset, lifecycle, action, retirement, and
   settings coverage.

## Forbidden Changes

- issue #74 movement-resolution changes;
- 3D/4D NEXT geometry work;
- Stage 54F spacing, grid, slice-readability, validation-colour, or polish;
- Stage 54E-5 cockpit consolidation, Hold, topology, Explorer, campaign,
  simulation, or general settings/input redesign;
- native gameplay or Python parity implementation; and
- push or PR creation.

## Acceptance Criteria

1. Orientation helpers cannot copy framing state, and framing helpers cannot
   write orientation, projection, reflection-active state, `B`, `L`, or layout.
2. Reset View restores exact canonical presentation while preserving gameplay
   and preferences in 2D, 3D, 4D, and replay.
3. Fit preserves current orientation, projection, reflection-active state,
   `B`, `L`, layout, content, and preferences.
4. Restart/new same context preserve view; context destruction and re-entry do
   not leak transient pose.
5. No continuous preset identity or `frame_board()` definition/caller remains.
6. Display Reset preserves UI scale; Accessibility Reset restores its default;
   persistence remains compatible.
7. Focused tests, pinned Godot verification, full repository verification, and
   real-window review evidence are recorded truthfully.

## Automated Verification

- focused Godot suite and touched-contract tests;
- `git diff --check`;
- `./scripts/check_git_sanitation_repo.sh`;
- routed documentation/governance/configuration validators;
- pinned `GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot
  ./scripts/verify_godot_4_7.sh`;
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

- real-window 2D/3D/4D/replay review without claiming headless tests as visual
  acceptance.

## Documentation Updates

- record the concrete implementation in the canonical view architecture and
  Live-4D pointer;
- update authority-map wording without claiming an authority transfer;
- update the programme, backlog, and restart handoff to the E4b visible-review
  gate; and
- regenerate the settings reference after the UI-scale category correction.

## Explicit Deferrals

- issue #74 movement resolution;
- NEXT geometry fidelity;
- Stage 54F findings; and
- Stage 54E-5 and later programme work.

## Handoff

Automated completion advances Stage 54E-4b only to
`IMPLEMENTED / READY_FOR_FOCUSED_VISIBLE_REVIEW`. Issue #74, NEXT fidelity,
Stage 54F findings, and E5/later remain explicitly open and separate.
