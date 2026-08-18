# Task Contract — Close Stage 54E-4a Independent Re-review Findings

## Objective

Close the independent Stage 54E-4a technical re-review's implementation-audit
and planning findings without reopening the accepted human view semantics or
starting E4b. This is documentation-only architecture and staged handoff work.
It implements no runtime, test, configuration, scene, gameplay, or visual fix.

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

1. Assign the real identity machinery and every writer/reader/HUD consumer to
   `camera_rig.gd`; remove planned runtime-removal work for the already-absent
   `resolve_id()` and membership tolerance while classifying the real `CUSTOM`
   sentinel.
2. Give `apply_framing_preset()` and `apply_preset()` concrete action-based E4b
   dispositions, permitted mutations, forbidden mutations, and callers.
3. Inventory the six public IDs, `CUSTOM`, and
   `PYTHON_DIAGRAM_REPLAY_VIEW`, including replay's current `Camera: Iso`
   fallback and its removal path.
4. State canonical Live-4D `L` numerically as `(0.0, 0.0)`.
5. Clarify that Fit preserves projection while today's fitted production path
   supports only orthographic projection and needs no fictitious perspective
   regression.
6. Complete the `fit_bounds()` mutation audit, including identity/diagnostic
   bookkeeping and snap-to-current effects.
7. Recheck every E4b component row against real files, symbols, callers,
   retained fields, removed fields, and target behaviour.
8. Reconcile staged status to final independent technical re-review pending.

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

1. The eight-value current identity inventory and replay mislabel are exact.
2. Every real identity symbol, writer, reader, diagnostic coupling, HUD caller,
   and test impact has an owner and target disposition.
3. No plan row assigns nonexistent runtime removal work.
4. The framing adapter and 3D/replay orientation action have fixed, compatible
   target contracts; Live-4D orientation reaches only `L`.
5. Canonical `L`, Fit/projection evidence, and the complete `fit_bounds()`
   mutation set are explicit.
6. The E4b table is implementable without another mechanical or product choice.
7. Accepted lifecycle, Reset, Fit, persistence, UI-scale, mode, and defect
   semantics remain unchanged.
8. E4a is ready for final independent technical re-review but is not self-
   certified green; E4b remains not started/ineligible.
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
  adapter/inventory dispositions, evidence wording, and exact E4b plan.
- `docs/architecture/authority_map.md`,
  `docs/plans/professional_godot_game_programme.md`, `docs/BACKLOG.md`, and
  `CURRENT_STATE.md`: final independent re-review handoff status.
- this task contract: bounded re-review scope and acceptance.

## Explicit Deferrals

- all E4b runtime work;
- both pre-54F correctness fixes;
- Stage 54F visual/comprehension implementation and integrated audit;
- E5 cockpit consolidation, Hold, and later programme stages.

## Handoff target

Stage 54E-4a ends with human semantics accepted, all current technical findings
corrected, and final independent technical re-review required. Stage 54E-4b
remains ineligible until that review returns green.
