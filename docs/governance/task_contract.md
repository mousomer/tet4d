# Task Contract — Reconcile Stage 54E-4a View Semantics and Human Findings

## Objective

Correct the Stage 54E-4a architecture contract to the accepted human
view/persistence/reset model, reconcile active programme status, and assign all
current human-visible findings to bounded owners. This is documentation-only
architecture and staged handoff work. It implements no runtime or visual fix.

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
- authority-map wording;
- programme, backlog, restart-handoff, and this task contract; and
- no runtime, config, test, scene, asset, or generated-maintenance file.

## Required Changes

1. Define current view as transient presentation-context state, not a
   preference or gameplay-run state.
2. Define one composite Reset View that restores every mode-owned canonical
   view component without taking ownership of those components.
3. Define Fit View as framing-only and require a separate internal canonical
   establishment path.
4. Refine lifecycle so same-context Restart/new game preserves view, while
   setup/menu/mode exit destroys it and re-entry/application restart establishes
   a fresh canonical view.
5. Replace persistent/derived current-preset identity with named view actions;
   retire `Custom`, `resolve_id()`, and the `0.001`-radian identity requirement
   where they have no other product purpose.
6. Define canonical/reset/fit ownership for 2D, 3D, Live 4D, and replay, with a
   flat/front-on canonical 2D view.
7. Classify projection from runtime evidence and reconcile UI-scale reset
   ownership as accessibility presentation.
8. Make the E4b component and automated/visible evidence plans implementable
   without another product decision.
9. Record bounded pre-54F correctness briefs for 3D control-arrow truthfulness
   and 3D/4D NEXT geometry fidelity.
10. Preserve #69, #70, the 4D-slice-as-3D comprehension criterion, and the E3
    validation-error colour advisory under Stage 54F.
11. Reconcile programme status and the E4a/E4b/E5/54F/54G human-review register.

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

1. The active architecture has one non-contradictory transient/persistent split.
2. Reset View, Fit View, restart, same-context new game, teardown, and re-entry
   have complete 2D/3D/4D/replay semantics.
3. Named presets are actions and no continuous identity machinery remains in
   the product contract.
4. UI scale belongs operationally to Accessibility Reset; Display Reset,
   Reset View, Fit View, and Restart preserve it.
5. Projection is resolved from actual product affordances, not implementation
   convenience.
6. The E4b plan identifies exact components, migration steps, automated
   evidence, focused visible review, authority impact, and forbidden scope.
7. Stage 54E-3 remains COMPLETE / REVIEWED GREEN with human product review
   deferred to 54F; Stage 54E-4a is ready only for independent re-review; E4b
   is not started/ineligible; Hold remains independently eligible.
8. Both pre-54F correctness defects have reproduction, owner, components,
   invariant, regression strategy, visible verification, exclusions, and
   timing.
9. 54F retains #69, #70, 4D-slice volumetric readability, and validation-error
   colour without claiming fixes.
10. Only documentation changes, required verification passes, one semantic
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

- `docs/architecture/camera_gui_preset_semantics.md`: corrected canonical
  forward contract and E4b evidence plan.
- `docs/architecture/4d_presentation_interaction_architecture.md`: lifecycle
  supersession and canonical-owner pointer.
- `docs/architecture/authority_map.md`: clarified existing Godot presentation
  authority.
- `docs/plans/professional_godot_game_programme.md`: programme status, defect
  briefs, 54F criteria, and human-review register.
- `docs/BACKLOG.md` and `CURRENT_STATE.md`: open-work and restart handoff.
- this task contract: corrected scope and acceptance.

## Explicit Deferrals

- all E4b runtime work;
- both pre-54F correctness fixes;
- Stage 54F visual/comprehension implementation and integrated audit;
- E5 cockpit consolidation, Hold, and later programme stages.

## Handoff target

Stage 54E-4a ends with human semantics accepted, the contract corrected, and a
fresh independent technical re-review required. Stage 54E-4b remains
ineligible until that review returns green.
