# Task Contract — Stage 54E-3a Setup Taxonomy and Classification

## Objective

Make the accepted `RDS_MENU_STRUCTURE.md` section 4.4 setup taxonomy
first-class declarative data for the Godot game-setup surface, classify every
field the setup panel renders, and enforce the taxonomy rules as testable
invariants. This slice changes no rendering, no field semantics, and no
persisted or canonical setup payload. Progressive-disclosure presentation is
Stage 54E-3b.

## Current Authority

- `docs/rds/RDS_MENU_STRUCTURE.md`: section 4.4 setup and presentation
  ownership taxonomy, its four categories, and the progressive-disclosure rule;
  section 5.1 shared shell layout and overflow behaviour.
- `docs/plans/professional_godot_game_programme.md`: Stage 54E-3 scope, the
  requirement to reuse existing menu machinery, and the prohibition on adding
  another menu validator for the taxonomy.
- `docs/architecture/editable_board_setup_and_persistence.md`: frozen game
  setup, last-valid setup, draft, and persistence ownership.
- `docs/ARCHITECTURE_CONTRACT.md` and `docs/architecture/authority_map.md`:
  Godot presentation ownership and the native deterministic-gameplay boundary.
- `config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`, `AGENTS.md`, and
  `godot/AGENTS.md`: routing and verification governance.

Godot owns the setup presentation surface and its field taxonomy. Native
gameplay remains authoritative for canonical session construction. This slice
performs no authority transfer and no authority establishment.

## Allowed Systems and Paths

- `godot/Tet4D.Godot/scripts/ui/game_setup/` field specification and
  classification registry.
- Focused Godot setup taxonomy, classification, and conformance tests.
- Task, RDS status, backlog, and restart-handoff documentation.

## Required Changes

- Add `setup_field_spec.gd` as a sibling of `setting_spec.gd`. It must reuse
  the established spec/validation mechanism without modifying the settings
  surface or relaxing its `FORBIDDEN_CATEGORY_TOKENS` guard, which exists
  because the settings panel is shell-only while setup is game definition.
- Declare the four `RDS_MENU_STRUCTURE.md` section 4.4 categories, their
  required disclosure level, and their required identity classification as
  data rather than as prose or panel control flow.
- Add a setup field registry declaring every field the setup panel renders,
  per mode: board preset shortcut, each board dimension axis, piece set,
  randomness mode, seed, starting speed, translation frame, and rotation
  frame.
- Express the two conditions currently hardcoded in
  `game_setup_panel.gd::_refresh_from_model()` as declared data: seed is
  visible only under fixed-seed randomness, and the control-frame fields do
  not apply to 2D. Mode applicability must be carried by each field's declared
  mode list, not by branching in the registry builder, so that changing where a
  field appears is a data edit the tests can contradict. Board dimension axes
  remain generated per mode because their count and ranges derive from the
  board-extent contract.
- Enforce, as validation failures rather than convention:
  - every declared field resolves to exactly one category;
  - contextual game definition declares a `visible_when` condition and no
    other category may declare one;
  - advanced gameplay/input and presentation preference must not be classified
    as session identity;
  - declared disclosure and identity match the category.
- Add a conformance test binding the taxonomy to actual data flow: the set of
  fields classified as session identity must correspond exactly to the fields
  `game_setup_model.gd::canonical_session_setup()` sends to native, and the
  control-frame fields must remain outside it.
- Validate declared numeric ranges and bind them to the sources that own them:
  axis ranges must equal `board_axis_ranges()` from the board-extent contract,
  and seed and starting-speed ranges must equal their `GameSetupSpec`
  constants. Enum fields must not declare ranges at all.
- Add a panel-introspection test binding the taxonomy to the rendered surface:
  enumerate the setup panel's visible value controls from the live scene tree
  and require exact correspondence with the registry's visible fields, so an
  undeclared control added to `_rebuild()` fails rather than passing silently.
  Assert declared visibility in both directions across representative mode and
  randomness combinations.
- Leave `game_setup_panel.gd` rendering, focus order, `game_setup_model.gd`
  semantics, and `game_setup_store.gd` persistence unchanged. The panel
  therefore keeps its own conditional visibility logic during this slice, and
  the declared conditions duplicate it. That duplication is intentional and
  bounded: Stage 54E-3b removes it by making the panel consume the registry.
  The introspection test is what keeps the two sides agreeing until then.

## Forbidden Changes

- Progressive-disclosure rendering, section restructuring, focus-order
  redesign, or any visible setup layout change; those are Stage 54E-3b.
- Modifying `setting_spec.gd`, `settings_registry.gd`, `settings_store.gd`, or
  the Godot settings panel, including its forbidden-token guard.
- Adding a new menu validator, a new governance subsystem, a versioned
  cross-language contract, or a generated GDScript contract for the taxonomy.
- Editing `config/menu/structure.json` or the Python menu surfaces it owns.
- Adding fields to, removing fields from, or reordering
  `canonical_session_setup()`; changing the persisted setup schema or
  `SCHEMA_VERSION`.
- Native C++, Python gameplay, deterministic rules, topology, RNG, queue,
  Ghost, replay/trace schema, or board-extent semantics.
- Stage 54D-3 Hold; Stage 54E-4 presets; Stage 54E-5 cockpit; Stage 54F visual
  work including Issues #69 and #70; Stage 54G release hardening.

## Acceptance Criteria

1. Every field the setup panel renders is declared with exactly one category,
   and no rendered field is unclassified. This is verified by enumerating the
   panel's visible value controls from the live scene tree, not by comparing
   the registry against a restatement of itself.
2. Declaring a field with a category/disclosure or category/identity mismatch
   fails validation with a named failure.
3. Declaring `visible_when` on a non-contextual category fails validation, and
   omitting it on contextual game definition fails validation.
4. Classifying an advanced gameplay/input or presentation-preference field as
   session identity fails validation.
5. The session-identity field set corresponds exactly to the payload
   `canonical_session_setup()` sends to native; `translation_frame` and
   `rotation_frame` remain outside it. Declared numeric ranges likewise
   correspond to their owning sources rather than to repeated literals, and an
   inverted, non-numeric, or missing range fails validation.
6. Seed is declared contextual on fixed-seed randomness, and the control-frame
   fields are declared as not applying to 2D. Declared visibility is checked
   against the panel in both directions: a field declared visible that the
   panel hides, and a field declared hidden that the panel shows, both fail.
7. The setup screens for 2D, 3D, and 4D render identically to `master`: same
   controls, same order, same visibility, same focus order.
8. `test_game_setup_model.gd` and `test_plain_setup_navigation.gd` pass
   unmodified.
9. The settings surface, its spec type, and its forbidden-token guard are
   unchanged.
10. No new validator, generated contract, or governance subsystem is
    introduced, and `config/menu/structure.json` is unchanged.
11. Resolver-required focused, governance, sanitation, and full-repository
    verification pass, and the tracked worktree is clean.

## Automated Verification

- Policy resolver: `godot_product_shell` with `staged_handoff`.
- Requirements: `documentation`, `governance_structure`, and `godot`. The
  `human_visual` requirement is not claimed for this slice because rendering is
  unchanged by construction; it is required for Stage 54E-3b.
- Focused Godot setup taxonomy validation tests, the classification totality
  test, the `canonical_session_setup()` conformance test, and the panel
  introspection test. The introspection test drives the real panel and awaits
  frames, so it registers in the `SceneTree` lane of `tests/run_tests.gd`
  alongside `test_plain_setup_navigation.gd`.
- Existing `test_game_setup_model.gd` and `test_plain_setup_navigation.gd`
  unmodified.
- `GODOT_BIN=... ./scripts/verify_godot_4_7.sh`.
- Governance validators and generated-document checks.
- Git sanitation, `git diff --check`, and `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

Open the setup screen for 2D, 3D, and 4D and confirm no visible difference
from `master`: identical control set and order, seed row still appearing only
under fixed-seed randomness, control-frame section still absent in 2D, and
unchanged keyboard focus traversal. This slice's manual check is a
no-visual-change confirmation, not a progressive-disclosure review.

## Documentation Updates

Update only concrete stale statements or required evidence in:

- `docs/rds/RDS_MENU_STRUCTURE.md` implementation-status section
- `docs/BACKLOG.md`
- `CURRENT_STATE.md`

## Open Questions For Review

- `config/project/policy_pack.json` declares
  `menu_control_typing_contract.setup_control_types` as `toggle`, `selector`,
  `slider`, and `stepper`. The seed field renders as a `LineEdit`, which has no
  entry in that list. This slice declares the field's actual control type and
  does not silently resolve the divergence. Review must decide whether to
  extend the policy list or migrate seed to a stepper in Stage 54E-3b.

## Explicit Deferrals

- Stage 54E-3b progressive-disclosure rendering, section layout, secondary
  advanced disclosure, and focus behaviour.
- Stage 54E-3c RDS, programme, backlog, and handoff reconciliation.
- Stage 54D-3 Hold and any Hold setup or keybinding field.
- Stage 54E-4 preset taxonomy, naming, categories, UI, and persistence.
- Stage 54E-5 cockpit consolidation.
- Stage 54F integrated visual acceptance, including Issues #69 and #70.
- Stage 54G release hardening.

## Review Outcome

Pending. Stage 54E-3a is not complete until external technical review accepts
the implementation and evidence.
