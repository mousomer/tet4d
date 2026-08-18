# Task Contract — Close Final Stage 54E-4a Review Blockers

## Objective

Close P1-1/P1-2 and the related P2-1/P2-2 findings from the final independent
Stage 54E-4a technical re-review without reopening the accepted human view
semantics or starting E4b. This is documentation-only architecture and staged
handoff work. It implements no runtime, test, configuration, scene, gameplay,
or visual fix.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `staged_handoff`.
- Affected layers: documentation and governance records.
- Verification requirements: `documentation`, `governance_structure`.
- Typical `godot` evidence is omitted because no Godot runtime, scene,
  resource, configuration, or test changes; executable evidence cannot prove a
  prose-only architecture correction.
- Full repository gate: required because this changes an architecture
  authority and prepares an independent-review handoff.

## Current Authority

- `docs/architecture/camera_gui_preset_semantics.md` for the forward view
  lifecycle and operation contract;
- `docs/architecture/4d_presentation_interaction_architecture.md` for the
  accepted `B/L/layout/V/P` separation and historical Stage 54E-2 evidence;
- `docs/plans/professional_godot_game_programme.md` for programme gates and
  human-review responsibilities;
- `docs/rds/RDS_MENU_STRUCTURE.md` for setup/presentation separation;
- `docs/ARCHITECTURE_CONTRACT.md` and `docs/architecture/authority_map.md` for
  subsystem boundaries; and
- `docs/BACKLOG.md` and `CURRENT_STATE.md` for open work and restart handoff.

Authority effect: clarify/supersede presentation lifecycle semantics within
existing Godot presentation authority. No gameplay authority transfer and no
native authority establishment.

## Allowed Systems and Paths

- the E4a view architecture owner and its consumed 4D architecture pointer;
- the historical configurable-board architecture statement about dead
  `frame_board()`;
- authority-map wording;
- programme, backlog, restart-handoff, and this task contract; and
- no runtime, config, test, scene, asset, or generated-maintenance file.

## Required Changes

1. Define `CameraRig.establish_outer_view(yaw, pitch, roll,
   reflection_active)` as an arbitrary absolute outer-orientation seam with
   exact allowed/forbidden mutations and an orientation-only snap.
2. Define named outer actions as target resolution followed by that seam, and
   define Reset/re-entry as mode-owner restoration, arbitrary outer-view
   establishment, then framing-only fit.
3. Keep Live-4D local yaw/pitch exclusively `L`-owned while using the new seam
   only for its fixed outer mount/reflection during canonical establishment.
4. Record that `CameraRig.frame_board()` has zero live callers and require its
   deletion in E4b; correct the historical document that presented it as an
   active production path.
5. Extend the identity audit to both unknown-ID replay fallback and known-ID
   false labels, including Live-4D `Camera: Iso` at outer yaw 205 degrees.
6. Make reflection routing consistent: defined outer targets may establish it;
   current 3D/replay actions use false; Live-4D `L` actions and all Fit/framing
   paths preserve it.
7. Recheck exact CameraRig/TraceReplayApp/action routing so E4b needs no further
   API or product decision.
8. Reconcile staged status to final confirmation review pending, with no
   remaining human decision.

## Forbidden Changes

- E4b runtime camera/settings implementation;
- the 3D movement/control fix or NEXT renderer/geometry fix;
- #69 spacing, #70 grid styling, or a 4D renderer redesign;
- E5 cockpit consolidation, Hold, topology, Explorer, campaign, or simulation;
- rewriting, deleting, resetting, or absorbing the separate E3 defect branch;
- claiming any documented defect fixed;
- self-certifying E4a REVIEWED GREEN; or
- pushing or opening a PR.

## Acceptance Criteria

1. The rig-owned arbitrary outer-orientation seam has exact arguments, state
   effects, snap behavior, exclusions, and presentation-only scope.
2. Named actions and canonical Reset/re-entry compose that seam with the right
   mode owners and framing operations; Live-4D `L` remains separate.
3. Zero-caller `frame_board()` is classified as dead and assigned deletion,
   with no active production evidence attributed to it.
4. Both persistent-identity false-label classes and their common retirement
   path are explicit, with no replacement continuous identity.
5. Reflection semantics agree across actions, canonical establishment, Fit,
   and framing helpers.
6. The E4b table is implementable without another mechanical or product choice.
7. Accepted lifecycle, Reset, Fit, persistence, UI-scale, mode, and defect
   semantics remain unchanged.
8. E4a is ready for final confirmation review but is not self-certified green;
   E4b remains not started/ineligible and no human decision remains.
9. Only documentation changes, required verification passes, one semantic
   commit is created, and the final worktree is clean.

## Automated Verification

- policy-backed resolver for the classification above;
- `git diff --check`;
- `./scripts/check_git_sanitation_repo.sh`;
- documentation/governance/configuration validators; and
- `CODEX_MODE=1 ./scripts/verify.sh` because an architecture authority and
  independent-review handoff are changed.

No manual verification is required for this documentation-only slice. The
contract records focused E4b and integrated 54F human-visible obligations.

## Manual Verification

None for this documentation-only slice. Focused E4b and integrated 54F
human-visible obligations are specified but not performed or claimed here.

## Documentation Updates

- `docs/architecture/camera_gui_preset_semantics.md`: corrected runtime audit,
  canonical outer-orientation seam, dead-code/label/reflection dispositions,
  composition, and exact E4b plan.
- `docs/architecture/configurable_plain_boards_and_4d_layout.md`: classify
  `frame_board()` as dead rather than a production presentation assumption.
- `docs/architecture/authority_map.md`,
  `docs/plans/professional_godot_game_programme.md`, `docs/BACKLOG.md`, and
  `CURRENT_STATE.md`: final confirmation-review handoff status.
- this task contract: bounded re-review scope and acceptance.

## Explicit Deferrals

- all E4b runtime work;
- both pre-54F correctness fixes;
- Stage 54F visual/comprehension implementation and integrated audit;
- E5 cockpit consolidation, Hold, and later programme stages.

## Handoff target

Stage 54E-4a ends with human semantics accepted, the final two blocking
technical findings and related P2 findings corrected, and final confirmation
review required. Stage 54E-4b remains ineligible until that review returns
green. Remaining human decisions: none.
