# Task Contract — Stage 54E-3b Setup Progressive Disclosure

## Objective

Render the accepted `RDS_MENU_STRUCTURE.md` section 4.4 setup taxonomy as
progressive disclosure across 2D, 3D, and 4D, so ordinary setup is concise while
complete board configuration, reproducibility controls, and advanced input
configuration remain fully reachable. This slice changes information
architecture only: no setup value, validation rule, canonical session payload,
persisted document, or deterministic behaviour changes.

## Current Authority

- `docs/rds/RDS_MENU_STRUCTURE.md`: section 4.4 setup and presentation ownership
  taxonomy and the progressive-disclosure rule; section 4.5 setup disclosure
  behaviour; section 5.1 shared shell layout and overflow behaviour.
- `docs/plans/professional_godot_game_programme.md`: Stage 54E-3 scope, the
  requirement to reuse existing menu machinery, and the prohibition on adding
  another menu validator for the taxonomy.
- `docs/architecture/editable_board_setup_and_persistence.md`: frozen game
  setup, last-valid setup, draft, and persistence ownership.
- `docs/ARCHITECTURE_CONTRACT.md` and `docs/architecture/authority_map.md`:
  Godot presentation ownership and the native deterministic-gameplay boundary.
- `config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`, `AGENTS.md`, and
  `godot/AGENTS.md`: routing and verification governance.

Godot owns the setup presentation surface. Native gameplay remains
authoritative for canonical session construction. This slice performs no
authority transfer and no authority establishment.

## Allowed Systems and Paths

- `godot/Tet4D.Godot/scripts/ui/game_setup/game_setup_panel.gd` rendering,
  disclosure, focus, and validation presentation.
- `godot/Tet4D.Godot/scripts/ui/game_setup/setup_field_registry.gd` declared
  mode applicability.
- Focused Godot setup disclosure, navigation, and taxonomy conformance tests.
- Task, RDS, programme, backlog, and restart-handoff documentation.

## Required Changes

- Group the ordinary surface as board preset shortcut, piece set where a choice
  exists, and starting speed, with `Customize Board`, `Advanced Game`, and
  `Controls` as secondary disclosures and `Start Game` as the primary action.
- Keep every Stage 54B board capability: preset shortcuts, per-axis
  decrement/direct entry/increment, structured validation, and `Reset Sizes`,
  now placed with board customization rather than in the primary action row.
- Auto-expose a board shape that matches no named preset, including after the
  surface is rebuilt, and make the derived `Custom` identity expose the
  dimension editors without mutating the shape.
- Stop presenting a one-option piece-set selector. Declare `piece_set` only for
  the modes that publish more than one production set, and bind that declaration
  to the piece-set catalogue in test rather than restating it.
- Remove the bounded duplication Stage 54E-3a recorded: piece-set and
  control-frame mode applicability and the conditional seed rule must resolve
  through `SetupFieldRegistry` and `SetupFieldSpec.is_visible_for()` instead of
  a second copy of those rules in the panel.
- Exclude undisclosed controls from focus navigation, move focus to the owning
  disclosure control when a section holding focus collapses, and keep the
  focused control visible in the scrolling viewport.
- Keep validation actionable under disclosure: fold seed text that never
  reached the model into the always-visible summary, and expose and focus the
  section owning the first failure when a launch is blocked.

## Forbidden Changes

- Adding disclosure, section, or presentation state to `GameSetupModel`
  canonical session setup, `game_setup_store.gd` persistence, settings
  persistence, snapshots, hashes, traces, replays, or native session state.
- Any setup or persistence schema version change.
- Changing queue or RNG semantics, effective-seed behaviour, seed bounds,
  deterministic identity, control-frame semantics, relative-command resolution,
  `SliceLocalOrientation`, `SliceBasis4D`, `CameraRig`, or native movement.
- Adding a new menu validator, governance subsystem, or general-purpose
  disclosure framework; editing `config/menu/structure.json`.
- Adding piece sets, redesigning the speed curve, or moving speed authority
  into Godot.
- Stage 54D-3 Hold; Stage 54E-4 camera/GUI presets; Stage 54E-5 cockpit; Stage
  54F visual work including Issues #69 and #70; Stage 54G release hardening.

## Acceptance Criteria

1. Ordinary 2D, 3D, and 4D setup exposes the primary controls with every
   secondary section collapsed, and `Start Game` is immediately available for
   valid defaults.
2. A preset-backed board does not permanently expose axis editors;
   `Customize Board` exposes exactly the active axes for the mode.
3. A non-preset board reads as `Custom` and exposes its dimensions on a rebuilt
   surface without another step.
4. Malformed dimension text stays visible, structured, and non-launchable, and
   increment recovers from it using the last-valid dimension.
5. `Reset Sizes` restores canonical dimensions without resetting piece set,
   speed, or control frames.
6. 2D presents no piece-set selector while still carrying `classic` in its
   session payload; 3D and 4D keep every audited piece set with its identity,
   label, and compatibility validation.
7. Fixed Seed exposes Seed and True Random hides it; a hidden Seed is not a
   focus target; seed validation is unchanged.
8. The control-frame disclosure is absent in 2D, present and collapsed by
   default in 3D and 4D, and toggling it does not change the frame values.
9. Toggling every disclosure leaves `canonical_session_setup()` and
   `last_valid_entries()` unchanged, and the persisted document records no
   disclosure state.
10. Undisclosed controls are not focus targets, focus order traverses only
    revealed controls and returns to its origin, collapsing a section holding
    focus lands focus on its disclosure control, and collapsing an unfocused
    section does not steal focus.
11. Expanding every section reveals every applicable field, so collapse is the
    only remaining reason an applicable field is off screen.
12. Resolver-required focused, documentation, human-visual, sanitation, and
    full-repository verification pass, and the tracked worktree is clean.

## Automated Verification

- Policy resolver: `godot_product_shell` with `staged_handoff`.
- Requirements: `documentation`, `godot`, and `human_visual`. Unlike Stage
  54E-3a, `human_visual` is claimed because this slice changes what the player
  sees.
- `tests/test_setup_progressive_disclosure.gd` for the disclosure, board,
  piece-set, advanced, controls, deterministic-isolation, and navigation
  evidence.
- `tests/test_setup_field_taxonomy.gd` for taxonomy conformance, now asserting
  semantic and presentational hiding independently.
- `tests/test_plain_setup_navigation.gd` and `tests/test_game_setup_model.gd`
  for the Stage 54B and session regressions.
- `GODOT_BIN=... ./scripts/verify_godot_4_7.sh`.
- Git sanitation, `git diff --check`, and `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

Drive the real windowed Godot 4.7.1 shell and confirm: 2D setup is concise with
no one-choice selector and discoverable X/Y; 3D piece-set choice, exact
dimensions, and a secondary `Controls`; 4D Standard reading as an
understandable game rather than an engineering form; a 4D custom shape staying
obvious after leaving and re-entering setup; W=1 with True 4D pieces remaining
understandable and actionable; conditional Seed presentation under Fixed Seed
and True Random; a complete keyboard-only traversal; and every disclosure and
principal action driven by pointer.

## Documentation Updates

- `docs/rds/RDS_MENU_STRUCTURE.md`: section 4.4 stepper/`numeric_entry`
  boundary and new section 4.5 recording durable setup disclosure behaviour —
  the two hiding reasons, the ordinary path, custom-board legibility,
  disclosure-state exclusion, the keyboard contract, and visible validation.
- `docs/plans/professional_godot_game_programme.md`: Stage 54E-3 status and
  scope outcome; Stage 54E-4 becomes next.
- `docs/BACKLOG.md` and `CURRENT_STATE.md`: Stage 54E-3 status and next steps.

## Resolved Decisions

- Board-axis controls remain `stepper`. Their ranges are small enough for
  stepping to be the primary interaction, so direct typed entry is a
  convenience affordance rather than the required input mode; `numeric_entry`
  stays reserved for ranges that make stepping impractical, such as the seed.
  No control factory was introduced, so no factory-level typing decision was
  forced.
- Disclosure state is owned by the panel, cleared and recomputed on every
  `configure()`. It is therefore structurally unable to reach the model, the
  persisted document, or the native session payload.
- The all-clear validation confirmation is feedback for dimension editing and
  is presented with board customization rather than in the ordinary path. A
  failure is always visible.

## Explicit Deferrals

- Stage 54E-3c final aggregate RDS, programme, backlog, and handoff
  reconciliation after external technical review accepts this implementation.
- Stage 54D-3 Hold and any Hold setup or keybinding field.
- Stage 54E-4 preset taxonomy, naming, categories, UI, and persistence,
  including all camera/GUI presentation-preference setup fields.
- Stage 54E-5 cockpit consolidation.
- Stage 54F integrated visual acceptance, including Issues #69 and #70.
- Stage 54G release hardening.

## Review Outcome

Pending. Stage 54E-3 is implemented with automated and real-window evidence
recorded; it is not reviewed green until external technical review accepts the
implementation and its evidence.
