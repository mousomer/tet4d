# Task Contract — Stage 54E-2d Lifecycle, Authority, and Contract Reconciliation

## Objective

Complete Stage 54E-2 implementation by enforcing the accepted Live-4D
presentation lifecycle and reconciling the public control, persistence, RDS,
architecture, authority, programme, backlog, and restart-handoff contracts with
the reviewed-green `B -> G_D -> L -> anchor -> V/P` implementation.

## Current Authority

- `docs/architecture/4d_presentation_interaction_architecture.md`: accepted
  transform, ownership, lifecycle, pitch-depth, preset, and staged-delivery
  contract.
- `docs/architecture/game_safe_4d_slice_basis.md`: exact signed `B`, reset,
  input-routing, and deterministic-exclusion contract.
- `docs/rds/RDS_4D_TETRIS.md` and `docs/rds/RDS_KEYBINDINGS.md`: durable
  product and binding requirements, interpreted with explicit runtime scope
  where inherited Python behavior differs from the Godot product shell.
- `docs/ARCHITECTURE_CONTRACT.md` and
  `docs/architecture/authority_map.md`: Godot presentation ownership and
  native deterministic-gameplay boundary.
- `docs/architecture/editable_board_setup_and_persistence.md` and
  `docs/architecture/godot_shell_settings_persistence.md`: frozen game setup,
  last-valid setup, shell preference, recovery, and persistence ownership.
- `docs/plans/professional_godot_game_programme.md`, `CURRENT_STATE.md`, and
  `docs/BACKLOG.md`: Stage 54E sequencing, current handoff, and explicit
  deferrals.
- `config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`, `AGENTS.md`,
  and `godot/AGENTS.md`: routing and verification governance.

Godot owns `B`, shared continuous `L`, layout, renderer composition, `V/P`,
input adaptation, help, and presentation lifecycle. Native gameplay remains
authoritative for canonical state and session transitions. This slice performs
no authority transfer or establishment.

## Allowed Systems and Paths

- Godot Live-4D app/session lifecycle orchestration.
- Godot renderer presentation teardown and semantic state snapshots.
- Godot `CameraRig` default framing/projection/reflection reset seam.
- Godot normal Live-4D action registration, routing, helper, and help copy.
- Focused Godot lifecycle, input, camera, renderer, settings, setup,
  persistence, deterministic-isolation, and integration tests.
- Necessary task, RDS, architecture, authority, programme, backlog, design,
  README/control, and restart-handoff documentation.

## Required Changes

- Establish app-owned seams for fresh Live-4D defaults, session teardown, and
  basis-only reset without redesigning transform ownership.
- Reset ephemeral `B/L/V/P`, anchors/bounds/fit reference, reflection, helper,
  and resolver state on the lifecycle events that own a full reset.
- Keep Restart Game bound to native reconstruction of the frozen current setup
  and preserve existing deterministic seed/RNG/session behavior.
- Make Reset View presentation-only and basis reset `B`-only, with explicit
  deterministic-isolation evidence.
- Clear stale Live-4D state and renderer children on setup/menu exit and mode
  transition; re-entry must start from coherent defaults on its first frame.
- Keep presets decomposed into `L` plus `V/P`, non-persistent, and independent
  of `B` and canonical gameplay.
- Remove normal-gameplay roll action registration/routing/help exposure while
  retaining generic low-level `CameraRig` roll primitives.
- Reconcile Live-4D terminology and the Reset View / Restart Game / Fit View
  distinction across runtime helpers and durable documentation.
- Make inherited Python keybinding scope explicit rather than changing Python
  behavior or shared keybinding configuration to match Godot.
- Prove ephemeral presentation fields are absent from settings/setup/native
  identity while established frame and camera preferences continue to persist.
- Close Stage 54E-2 authority records only to implemented/review-pending state.

## Forbidden Changes

- Native C++, Python gameplay, deterministic rules, topology, collision,
  gravity, scoring, hard drop, RNG, queue/NEXT, Ghost landing, replay/trace
  schema, or board-extent semantics.
- Quantized-yaw mathematics, ties-to-even, the `[-40°, +60°]` pitch policy,
  transform ordering, fitted mount, reflection mechanism, or projection proof.
- Stage 54D-3 Hold; Stages 54E-3/4/5; Stage 54F visual work; Stage 54G release
  hardening; Issues #69/#70.
- Preset taxonomy/names/categories/UI/persistence redesign; Explorer UI;
  topology UI; gamepad support; a keybinding editor/profile/schema redesign.
- A new persistent `B/L/V/P` schema or authority-establishment record.

## Acceptance Criteria

1. Fresh/configured/random Live-4D sessions start with identity `B`, default
   yaw/pitch `L`, recomputed layout/bounds, and fitted reflected default `V/P`.
2. Restart Game reconstructs the frozen current setup and resets presentation
   defaults without changing its established deterministic semantics.
3. Change Setup, menu return, and mode transitions clear Live-4D ephemeral
   state, presentation children, fit state, and reflection authority.
4. Re-entering Live 4D after another mode uses fresh presentation defaults;
   Live 3D retains its existing camera behavior and inherits no 4D state.
5. Reset View resets `B + L + V/P` and renderer/resolver/HUD state without
   changing native snapshot, hash, RNG, score, queue, cells, Ghost, or setup.
6. The internal basis-only reset restores identity `B` and dependent
   layout/bounds while preserving `L`, pan/focus, zoom, projection, and frame
   preferences.
7. Presets preserve `B`, anchors, canonical gameplay, and preferences while
   updating shared `L`, oriented bounds/fit inputs, and framing coherently.
8. No stale cells, Ghost, active nodes, grids, frames, labels, markers, gizmo
   authority, fit envelope, reflection pivot, focus, or interpolation state
   survives presentation teardown/re-entry.
9. Ephemeral presentation state is not serialized in shell settings, game
   setup, native snapshot/hash, or replay identity; accepted presentation and
   frame preferences retain their established persistence.
10. Normal Live-4D gameplay registers and advertises no roll action; reusable
    low-level camera roll remains available outside normal gameplay.
11. Public Live-4D help distinguishes piece movement/rotation, exact 90° view
    rotation/re-slicing, slice orientation, framing, Drop, Session, and
    Navigation, and accurately distinguishes Restart, Reset View, and Fit.
12. RDS/architecture/authority documents describe exact `B`, continuous
    yaw/pitch `L`, yaw-only `Q`, framing-only `V/P`, lifecycle reset semantics,
    deterministic exclusion, and runtime-specific binding scope.
13. Existing screen-right/Forward-depth, active-spawn, NEXT, Ghost,
    asymmetric-board, `W=1`, and signed-basis guarantees remain green.
14. Resolver-required focused, governance, sanitation, full-repository, and
    real-window verification pass; the worktree is clean and the draft PR is
    unmerged with review pending.

## Automated Verification

- Policy resolver: `godot_product_shell` with `staged_handoff` and
  `cross_layer`.
- Requirements: `documentation`, `governance_structure`, `godot`,
  `deterministic`, `integration`, and `human_visual`; full repository gate
  required; no typical requirement omitted.
- Focused LiveInputContract, Live-4D lifecycle/reset/session/mode tests,
  SliceLocalOrientation, ProjectionLayout, CameraRig, renderer cleanup,
  control-frame mapping, preset, setup/settings persistence, and deterministic
  isolation.
- `./scripts/check_keybinding_contract.sh` if shared keybinding/configuration
  sources change.
- `GODOT_BIN=... ./scripts/verify_godot_4_7.sh`.
- Governance validators and generated-document checks.
- Git sanitation, `git diff --check`, and `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

Run Godot 4.7.1 in a real non-headless window. Cover asymmetric
`5 x 10 x 4 x 4`, `W=1`, and representative Live 3D sessions. Verify Restart,
Reset View after visible gameplay change, basis-only reset via the semantic
seam, representative preset with non-identity `B`, `4D -> 3D -> 4D`, Change
Setup/relaunch, coherent first frames/Fit/reflection/helpers, and absence of
normal-gameplay roll advertising or response.

## Documentation Updates

Update only concrete stale statements or required evidence in:

- `docs/architecture/4d_presentation_interaction_architecture.md`
- `docs/architecture/game_safe_4d_slice_basis.md`
- `docs/ARCHITECTURE_CONTRACT.md`
- `docs/architecture/authority_map.md`
- `docs/rds/RDS_4D_TETRIS.md`
- `docs/rds/RDS_KEYBINDINGS.md`
- `docs/design/godot_visual_system.md` or the current Godot README/control
  reference where runtime help terminology is stale
- `docs/plans/professional_godot_game_programme.md`
- `docs/BACKLOG.md`
- `CURRENT_STATE.md`

## Explicit Deferrals

- Stage 54D-3 Hold.
- Stage 54E-3 setup/menu information architecture.
- Stage 54E-4 preset taxonomy, naming, categories, UI, and persistence.
- Stage 54E-5 cockpit consolidation.
- Stage 54F integrated visual acceptance, including Issues #69 and #70.
- Stage 54G release hardening and full keybinding/remapping/gamepad work.
- Explorer, topology, challenge, campaign, and simulation later phases.

Implementation handoff status may become `STAGE 54E-2d IMPLEMENTED — REVIEW
PENDING`; neither Stage 54E-2d nor Stage 54E-2 may be called reviewed green or
programme-complete before external review.
