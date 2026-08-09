# Task Contract — Stage 54E-2c Interaction and Camera-Rig Separation

## Objective

Separate normal Live-4D slice-local interaction from outer framing and route
relative controls through exact `B` plus quantized shared `L.local_yaw`.

## Current Authority

- `docs/architecture/4d_presentation_interaction_architecture.md`: accepted
  Stage 54E transform, ownership, pitch-depth, and staged-delivery contract.
- Reviewed-green Stage 54E-2a/2b evidence on `master` at
  `51a17ae6291295ca1d00780a5dc98bf7336139d4`.
- `docs/architecture/game_safe_4d_slice_basis.md`: exact signed `B` contract.
- `docs/ARCHITECTURE_CONTRACT.md` and
  `docs/architecture/authority_map.md`: Godot presentation ownership and
  deterministic exclusion.
- `docs/rds/RDS_4D_TETRIS.md`, `docs/rds/RDS_KEYBINDINGS.md`, and the live
  input contract: current product/input surfaces, subordinate to the accepted
  54E architecture where transitional wording remains.
- `docs/plans/professional_godot_game_programme.md`, `CURRENT_STATE.md`, and
  `docs/BACKLOG.md`: Stage 54E sequencing and explicit deferrals.
- `config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`, and
  `godot/AGENTS.md`: routing and verification governance.

Godot owns this presentation behavior. Native gameplay remains authoritative
for canonical state and commands; no Python, native, or authority-transfer
work is permitted.

## Allowed Systems and Paths

- Godot Live-4D input and presentation orchestration.
- Godot camera/framing and temporary preset compatibility integration.
- Shared slice-local orientation and control-frame mapping consumers.
- Focused Godot camera, renderer, input, and live-integration tests.
- Necessary status, architecture, programme, backlog, task, and evidence docs.

## Required Changes

- Route Live-4D left drag and keyboard yaw/pitch to the one shared `L`.
- Keep right drag on outer pan and wheel/zoom actions on outer framing.
- Resolve relative Live-4D controls from exact `B + Q(L.local_yaw)` without
  consulting `CameraRig.control_frame_yaw()`.
- Remove ordinary Live-4D interactive outer yaw/pitch/roll while preserving
  reusable low-level free-inspection roll.
- Establish and enforce a fitted-view-derived normal-gameplay pitch domain.
- Prove fitted-view post-`R` `+X` is screen-right and `+Z` is receding.
- Decompose current preset yaw/pitch into `L` and framing/zoom/pan into `V/P`.
- Make every interactive or preset-driven `L` mutation explicitly rerender,
  recompute oriented bounds, and refresh fit inputs without native gameplay.
- Replace provisional combined-camera characterization tests with requirement
  and regression evidence while preserving non-Live camera behavior.

## Forbidden Changes

- Deterministic gameplay, canonical commands, snapshots/hashes, RNG, scoring,
  queue/NEXT, Ghost landing, collision, hard drop, or topology semantics.
- Native C++ or Python implementation changes.
- Camera-preset taxonomy, names, UI categories, persistence, or Stage 54E-4
  redesign.
- Broad lifecycle, Reset View, new-game/restart, setup-change, mode-switch,
  persistence, keybinding/RDS, or final authority closure from Stage 54E-2d.
- Explorer UI, Hold, or Stages 54E-3/4/5 implementation.

## Acceptance Criteria

1. One shared `L` owns normal Live-4D yaw/pitch for renderer, input, resolver,
   and preset compatibility.
2. Live-4D relative commands use exact `B + Q(L.local_yaw)`; pitch and outer
   framing never enter discrete mapping.
3. Left drag and keyboard yaw/pitch mutate `L`; right drag pans; wheel and
   zoom actions change framing; gameplay roll has no effect.
4. Normal Live-4D outer interactive rotation is absent, while generic rig
   orbit/yaw/pitch/roll remains valid for non-Live/free-inspection consumers.
5. Every `L` mutation rerenders continuous orientation, recomputes oriented
   bounds, and refreshes the renderer/camera-fit input seam without native
   transitions or automatic recentering on every drag.
6. `B`, `L`, pan, zoom, Fit, and presets satisfy their independence and
   deterministic-isolation contracts.
7. The declared normal-game pitch range is mathematically inside the actual
   fitted-view Forward inversion boundary and passes default, extrema,
   intermediate, and clamp coverage.
8. Actual fitted-view evidence proves board-frame `+X` projects screen-right
   and board-frame `+Z` recedes for identity and signed `B`, all four yaw
   quarters, and representative admitted pitch.
9. Preset yaw/pitch reaches `L`, framing reaches `V/P`, final bounds remain
   coherent, and no preset leaves normal Live-4D outer rotation.
10. Focused, resolver-required, sanitation, full-repository, and real-window
    verification are green; Stage 54E-2d remains the next gated slice.

## Automated Verification

- Policy resolver classification: `godot_product_shell` with
  `staged_handoff`.
- Requirements: `documentation`, `governance_structure`, `godot`,
  `deterministic`, `integration`, and `human_visual`; full repository gate
  required.
- Focused camera, orientation, mapping, renderer, input, and live-shell tests.
- `GODOT_BIN=... ./scripts/verify_godot_4_7.sh`.
- Governance validators and generated-document checks.
- Git sanitation and `git diff --check`.
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

Use a real window with an asymmetric multi-slice Live-4D board. Verify shared
slice-local left-drag/keyboard yaw and pitch, fixed anchors, right-drag pan,
wheel zoom, clamp behavior, Right/Forward correspondence, framing
independence, preset decomposition, roll detachment, visual alignment,
refreshed Fit bounds/no clipping, and a representative 3D/non-Live camera
path.

## Documentation Updates

Update concrete 54E-2c implementation/status evidence in `CURRENT_STATE.md`,
`docs/BACKLOG.md`,
`docs/architecture/4d_presentation_interaction_architecture.md`,
`docs/architecture/game_safe_4d_slice_basis.md`,
`docs/plans/professional_godot_game_programme.md`,
`docs/ARCHITECTURE_CONTRACT.md`, and
`docs/architecture/authority_map.md` as warranted by the final diff.

## Explicit Deferrals

- Stage 54E-2d: complete reset/new-game/restart/setup/mode-switch lifecycle,
  persistence semantics, final keybinding/RDS/help reconciliation, and final
  authority closure.
- Stage 54E-4: preset semantics, categories, naming, UI, and persistence.
- Explorer/free-inspection UI and later Stage 54E/54F work.
