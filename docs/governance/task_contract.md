# Task Contract — Stage 54E-4a Camera and GUI Preset Semantic Audit and Design

## Objective

Audit every camera, view, layout, and GUI preset-like operation in the Godot
product shell against the accepted Stage 54E-2 presentation-space separation,
assign each mutable presentation property exactly one semantic owner, and
record the durable preset contract plus a concrete Stage 54E-4b implementation
plan. This is a design and audit slice. It changes no runtime behaviour.

## Current Authority

- `docs/architecture/4d_presentation_interaction_architecture.md`: the
  `C -> B -> G_D -> L -> anchor/layout -> V/P` separation, the section 14
  ownership and lifecycle contract, and the section 13 camera-preset audit that
  explicitly defers taxonomy, persistence, reset, labels, and layout-preset
  scope to Stage 54E-4.
- `docs/plans/professional_godot_game_programme.md`: Stage 54E-4 scope and its
  ordering after Stage 54E-2.
- `docs/rds/RDS_MENU_STRUCTURE.md`: menu and setup information architecture,
  including the section 4.4 setup taxonomy whose `presentation_preference`
  category is declared and deliberately empty.
- `docs/ARCHITECTURE_CONTRACT.md` and `docs/architecture/authority_map.md`:
  Godot presentation ownership and the native deterministic boundary.
- `config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`, `AGENTS.md`, and
  `godot/AGENTS.md`: routing and verification governance.

Godot owns the presentation surface. This slice performs no authority transfer
and no authority establishment; it clarifies existing Godot presentation
ownership.

## Allowed Systems and Paths

- `docs/architecture/camera_gui_preset_semantics.md` as the new canonical owner
  of preset semantics.
- A pointer from `docs/architecture/4d_presentation_interaction_architecture.md`
  section 13 to that document.
- Programme, backlog, restart-handoff, and task-contract status records.

## Required Changes

- Inventory every preset-like operation with its entry surface, implementation
  owner, actual mutations, lifecycle, persistence, mode applicability, tests,
  legacy coupling, intended owner, and disposition, including hidden
  compatibility adapters and concepts not named "preset".
- Trace each preset from player action through dispatch, resolver, state
  mutation, renderer update, persistence, and lifecycle reset, recording actual
  rather than named behaviour.
- Audit the Stage 54E-2c compatibility adapter and decide whether it survives.
- Classify every mutable presentation property into exactly one owner from
  `EXACT_BASIS`, `SLICE_LOCAL_ORIENTATION`, `SLICE_LAYOUT`, `OUTER_FRAMING`,
  `PROJECTION`, `GUI_LAYOUT`, `GUI_VISIBILITY`, `ACCESSIBILITY_PRESENTATION`,
  or `OTHER`.
- Decide the durable taxonomy, the `B` policy, the `L` policy, layout policy,
  outer-framing policy, projection policy, GUI policy, and combined-preset
  policy.
- Define the reset and lifecycle matrix, persistence classification, view
  identity under manual mutation, compatibility mapping, mode applicability,
  the Stage 54E-3 integration boundary, and the Explorer boundary.
- Record the Stage 54E-4b implementation plan, automated evidence design, and
  human-visible verification design.

## Forbidden Changes

- Any Godot runtime, scene, resource, input, keybinding, camera, layout,
  renderer, or settings-persistence change.
- `SliceLocalOrientation`, `SliceBasis4D`, `CameraRig`, layout algorithms,
  native code, Python gameplay or reference code, gameplay semantics, board
  configuration, snapshots, hashes, replay and trace schemas, topology, NEXT,
  Ghost, or Hold.
- Reopening any reviewed-green Stage 54E-2 decision.
- Stage 54E-4b implementation; Stage 54E-5 cockpit consolidation; Stage 54F
  visual work including issues #69 and #70; Stage 54D-3 Hold; Explorer.
- Modifying Stage 54E-3 completion status on behalf of that stage.

## Acceptance Criteria

1. Every preset-like operation in the Godot shell is inventoried, including the
   Stage 54E-2c compatibility adapter, Fit View, Reset View, and preset-adjacent
   settings; concepts sharing the word "preset" from other domains are recorded
   as out of scope with a reason.
2. Each preset's recorded mutations match the traced runtime path rather than
   its name.
3. Every mutable presentation property resolves to exactly one semantic owner.
4. The taxonomy decision states whether layout and GUI preset families exist,
   with the reason, rather than assuming them from the architecture's spaces.
5. The `B` policy is explicit and audited against current behaviour.
6. Reset View has exactly one documented meaning, consistent with the accepted
   section 14 contract.
7. Every preset-owned property has a persistence classification, and no
   presentation state enters deterministic identity.
8. View identity cannot disagree with the state that produced it.
9. Every legacy preset ID has a disposition and, where applicable, an explicit
   mapping.
10. The Stage 54E-4b plan names files, old and target behaviour, migration,
    tests, evidence, authority impact, and forbidden adjacent work.
11. Unresolved product decisions number at most three and are stated with a
    recommendation, the strongest alternative, and the tradeoff.
12. No runtime file is modified, and resolver-required verification passes with
    a clean worktree.

## Automated Verification

- Policy resolver: `godot_product_shell` with `staged_handoff`, affected layers
  `documentation` and `governance`, requirements `documentation` and
  `governance_structure`.
- The typical `godot` requirement is omitted with the recorded reason that this
  slice changes no Godot runtime, scene, resource, or test, so the Godot suite
  would prove nothing about the diff.
- Governance and documentation validators required by the touched paths,
  through `CODEX_MODE=1 ./scripts/verify.sh`.
- `git diff --check` and `./scripts/check_git_sanitation_repo.sh`.

## Manual Verification

None. This slice changes no visible behaviour. The human-visible verification
design it records is an obligation of Stage 54E-4b, not of this slice.

## Documentation Updates

- `docs/architecture/camera_gui_preset_semantics.md`: new canonical owner of
  preset semantics.
- `docs/architecture/4d_presentation_interaction_architecture.md`: section 13
  pointer to that owner.
- `docs/plans/professional_godot_game_programme.md`, `docs/BACKLOG.md`, and
  `CURRENT_STATE.md`: Stage 54E-4a status and next steps.

## Resolved Decisions

- Exactly one preset family exists: View. Layout has one adaptive algorithm and
  no player-facing alternatives; GUI state is already a set of independent
  persistent settings including the three-step `display.hud_density`. Neither
  justifies a preset family, so neither is created.
- No ordinary View preset may change the exact basis `B`. Current behaviour
  already complies and becomes an explicit test.
- No combined View/Layout/GUI presets. With no layout or GUI families there is
  nothing to combine, so a composite family would only rebuild the coupling
  Stage 54E-2 removed.
- Reset View restores the canonical product default, matching the accepted
  section 14 contract, rather than a persisted preference or session-entry
  state.
- View identity derives from state equality rather than a tracked flag, which
  structurally removes the current false "Iso" label after Fit View and Reset
  View.
- Nothing new is persisted and no schema changes, because view identity is
  derived and `L` and framing remain session-local.
- Presentation presets do not belong in game setup. Stage 54E-4b adds no setup
  field and requires no Stage 54E-3 change.
- Decision A, accepted 2026-08-17: the View selector is hidden in Live 2D and
  retained in Live 3D and Live 4D. Section 12.1 of the design generalises this
  into a durable rule — a presentation control is not offered in a mode where
  it cannot change what the player sees — and records the only other live
  violation, `display.show_w_labels`, which needs a settings-registry
  applicability mechanism and is therefore assigned to Stage 54E-5.
- Decision B, accepted 2026-08-17: applying a View preset restores the fitted
  framing baseline, discarding manual pan and zoom. This matches current
  behaviour, so it becomes a declared rule rather than a change.

No unresolved design question remains.

## Explicit Deferrals

- Stage 54E-4b implementation of the accepted contract.
- A persisted user-configured starting view preference, deliberately not
  introduced; canonical defaults are retained on Restart and Reset View.
- Named composite profiles for a future Explorer or campaign surface.
- Stage 54E-5 cockpit consolidation, including any renaming of the inspector
  `Camera` panel.
- Stage 54F visual acceptance, including issues #69 and #70.
- Stage 54D-3 Hold and Explorer.

## Review Outcome

Stage 54E-4a is design complete and its two product decisions were accepted on
2026-08-17. Stage 54E-4 itself remains incomplete: Stage 54E-4b must still
implement and verify the accepted contract, and no runtime work has been
performed.
