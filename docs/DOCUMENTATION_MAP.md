# Documentation Map

This file is the routing and ownership map for the repository documentation.

Use it to answer two questions first:

1. which document class owns the topic you are touching,
2. which specific file is the current authority for that topic.

## Documentation classes

### 1. Entry and routing

These files help readers enter the docs layer.

- `docs/README.md` (landing page only)
- `docs/DOCUMENTATION_MAP.md` (routing and ownership authority)

### 2. Architecture and structure

These files define the codebase shape and architectural rules.

- `docs/ARCHITECTURE_CONTRACT.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/architecture/authority_map.md`
- `docs/architecture/parity_protocol.md`
- `docs/architecture/authority_transfer_protocol.md`
- `docs/architecture/topology_contract_foundation.md`
- `docs/architecture/topology_aware_board_extent_contract.md`
- `docs/architecture/editable_board_setup_and_persistence.md`
- `docs/architecture/game_safe_4d_slice_basis.md`
- `docs/architecture/4d_presentation_interaction_architecture.md`
- `docs/architecture/camera_gui_preset_semantics.md`
- `docs/architecture/presentation_parameter_contract.md`
- `docs/architecture/built_in_style_catalog.md`
- `docs/architecture/canonical_local_board_presentation_geometry.md`
- `docs/architecture/ghost_piece.md`
- `docs/architecture/godot_shell_layout_stabilization.md`
- `docs/architecture/godot_shell_settings_source_of_truth.md`
- `docs/architecture/godot_shell_settings_persistence.md`
- `docs/architecture/configurable_plain_boards_and_4d_layout.md`
- `docs/architecture/plain_game_setup_completion.md`
- `docs/architecture/display_infrastructure.md`
- `docs/architecture/accessibility_infrastructure.md`
- `docs/architecture/godot_replay_shell_ux_acceptance.md`
- `docs/architecture/godot_visual_style_authority.md`
- `docs/architecture/godot_visual_style_foundation.md`
- `docs/architecture/godot_vector_arcade_cockpit_overhaul.md`
- `docs/architecture/godot_core_gameplay_completion.md`
- `docs/architecture/godot_guided_onboarding_navigation.md`

### 3. Active planning

These files define current planning authority, active specs, and active cleanup
or debt ledgers.

- `docs/plans/README.md`
- `docs/plans/plan_authority_map.md`
- `docs/plans/professional_godot_game_programme.md`
- `docs/plans/presentation_parameter_contract_acceptance.md`
- `docs/plans/canonical_local_board_presentation_geometry_acceptance.md`
- `docs/plans/cleanup_master_plan.md`
- domain-specific active plan files under `docs/plans/`
- recent planning-adjacent audits under `docs/plans/audits/`
- current repository quality-tool evidence:
  `docs/plans/audits/static_analysis_formatting_audit_2026-07-25.md`
- current Godot engine/toolchain migration evidence:
  `docs/plans/audits/godot_4_7_migration_2026-07-25.md`

### 4. Current execution state

These files track live restart context and open execution work.

- `CURRENT_STATE.md`
- `docs/BACKLOG.md`

### 5. Product/spec contracts

These files define durable behavior contracts and product requirements.

- `docs/rds/README.md`
- `docs/rds/*.md`
- `docs/design/godot_visual_system.md`

### 6. Contributor workflow and policy

These files define contributor process, policy, and verification workflow.

- `AGENTS.md`
- `docs/WORKFLOW_CODEX.md`
- `docs/governance/task_contract.md`
- `docs/governance/completion_report.md`
- `docs/KEYBINDINGS_EDITING.md`
- `docs/SHORT_KEYBINDINGS_GUIDE.md`
- `docs/MENU_STRUCTURE_EDITING.md`
- `docs/policies/*`
- machine-readable governance in `config/project/policy_pack.json`
- domain-specific contracts under `config/project/policy/manifests/`

### 7. Generated references

These files are generated inventories and references. They are not the first
place to define behavior policy.

- `docs/CONFIGURATION_REFERENCE.md`
- `docs/USER_SETTINGS_REFERENCE.md`

### 8. Help, release, and user-facing support docs

- `docs/help/*`
- `docs/RELEASE_INSTALLERS.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/CHANGELOG.md`

### 9. History and retired material

These files preserve useful background, completed pass notes, and retired plans.

- `docs/history/*`
- `docs/history/current_state_archive_2026-07-30.md`
- `docs/history/backlog_archive_2026-07-30.md`
- completed parity and migration evidence:
  `docs/architecture/first_subsystem_parity_pilot.md`,
  `docs/architecture/parity_pilot_audit_and_promotion_gates.md`,
  `docs/architecture/second_parity_slice_candidate_selection.md`,
  `docs/architecture/trace_metadata_identity_digest_parity.md`,
  `docs/architecture/parity_evidence_review_and_third_slice_selection.md`,
  `docs/architecture/topology_identifier_normalization_parity.md`,
  `docs/architecture/parity_evidence_package_review.md`,
  `docs/architecture/trace_schema_version_normalization_parity.md`,
  `docs/architecture/python_oracle_boundary_audit.md`,
  `docs/architecture/parity_tooling_package_review.md`,
  `docs/architecture/structural_parity_slice_selection.md`, and
  `docs/architecture/trace_envelope_validation_parity.md`

## Ownership map

| Topic | Primary owner |
| --- | --- |
| Documentation-layer routing and file-role boundaries | `docs/DOCUMENTATION_MAP.md` |
| Planning-layer routing and planning-doc ownership | `docs/plans/README.md`, `docs/plans/plan_authority_map.md` |
| Professional Godot product priorities, phase sequencing, and completion gates | `docs/plans/professional_godot_game_programme.md` |
| Codebase dependency rules and package ownership law | `docs/ARCHITECTURE_CONTRACT.md` |
| Canonical package layout, entrypoints, and generated ownership inventory | `docs/PROJECT_STRUCTURE.md` |
| Current topology-playground architecture and invariants | `docs/plans/topology_playground_current_authority.md` |
| Current topology-playground visible shell contract | `docs/plans/topology_playground_shell_redesign_spec.md` |
| Topology-playground deferred cleanup and transitional debt | `docs/plans/topology_playground_debt_register.md` |
| Canonical topology interchange, identity, and migration contract | `docs/architecture/canonical_topology_contract.md` |
| Shared topology scalar limits, generated bindings, and fingerprint | `contracts/topology_contract_v1.json`, `docs/architecture/topology_contract_foundation.md` |
| Professional live-board extent, bounded setup admissibility, and checked setup errors | `contracts/board_extent_contract_v1.json`, `docs/architecture/topology_aware_board_extent_contract.md` |
| Godot editable board drafts, last-valid setup persistence, and launch gating | `docs/architecture/editable_board_setup_and_persistence.md` |
| Strict native/Godot topology profile and resolver-query transport | `docs/architecture/native_topology_transport.md` |
| Strict internal Python topology constructor and source-adapter boundary | `docs/architecture/python_topology_domain_model.md` |
| Explorer topology persistence versions, strict loading, and legacy recovery | `docs/architecture/topology_persistence_recovery.md` |
| Subsystem authority, inherited reference ownership, and new authority establishment | `docs/architecture/authority_map.md`, `docs/architecture/authority_transfer_protocol.md` |
| Authoritative deterministic Hold transition, queue/RNG, state identity, and presentation boundary | `docs/architecture/authoritative_hold.md` |
| Repo-wide structural cleanup sequencing | `docs/plans/cleanup_master_plan.md` |
| Repository static-analysis, formatting, and CI coverage evidence | `docs/plans/audits/static_analysis_formatting_audit_2026-07-25.md` |
| Current Python semantic-boundary, coercion, retirement, and complexity audit | `docs/plans/audits/python_boundary_audit_2026-08-02.md` |
| Godot 4.7 engine, godot-cpp, native build, and CI migration evidence | `docs/plans/audits/godot_4_7_migration_2026-07-25.md` |
| Current Godot product-shell visual system | `docs/design/godot_visual_system.md` |
| Live 3D and future Live 4D gameboard visual language | `docs/plans/gameboard_visual_language_design.md` |
| Parity implementation and evidence process | `docs/architecture/parity_protocol.md`, `docs/governance/README.md` |
| Authority transfer and new-authority establishment | `docs/architecture/authority_transfer_protocol.md`, `docs/architecture/authority_map.md` |
| Completed parity/migration evidence | historical evidence index above and `docs/history/*` |
| Stage 45A Python 2D/ND duplication audit and first safe slice | `docs/architecture/python_2d_nd_dedup_audit.md` |
| Stage 28 Godot shell layout stabilization | `docs/architecture/godot_shell_layout_stabilization.md` |
| Stage 29 Godot shell settings registry foundation | `docs/architecture/godot_shell_settings_source_of_truth.md` |
| Stage 30 Godot replay shell UX acceptance | `docs/architecture/godot_replay_shell_ux_acceptance.md` |
| Stage 31 Godot visual style authority | `docs/architecture/godot_visual_style_authority.md` |
| Stage 32 Godot visual style foundation | `docs/architecture/godot_visual_style_foundation.md` |
| Stage 33 Godot Vector Arcade Cockpit UI overhaul | `docs/architecture/godot_vector_arcade_cockpit_overhaul.md` |
| Stage 46 Godot plain 2D/3D/4D gameplay completion boundary and audit | `docs/architecture/godot_core_gameplay_completion.md` |
| Stage 47 Godot guided onboarding and navigation contract | `docs/architecture/godot_guided_onboarding_navigation.md` |
| Stage 48 Godot shell settings persistence contract | `docs/architecture/godot_shell_settings_persistence.md` |
| Stage 49 configurable plain-board setup and adaptive 4D presentation | `docs/architecture/configurable_plain_boards_and_4d_layout.md` |
| Stage 54B-2 editable Godot board dimensions and persistence | `docs/architecture/editable_board_setup_and_persistence.md` |
| Stage 54C exact game-safe 4D presentation basis, coordinate mapping, and input routing | `docs/architecture/game_safe_4d_slice_basis.md` |
| Stage 54E-1 accepted 4D presentation-space separation, relative-control audit, and bounded 54E-2 plan | `docs/architecture/4d_presentation_interaction_architecture.md` |
| Stage 54E-4a camera/view/layout/GUI preset taxonomy, ownership, identity, reset, and persistence semantics | `docs/architecture/camera_gui_preset_semantics.md` |
| Post-Stage-54 typed presentation parameters, semantic ownership, profiles, live application, persistence isolation, and 3D/4D divergence audit | `docs/architecture/presentation_parameter_contract.md` |
| Stage 54F-1 canonical local board cells, extents, centring, grids, boundaries, dimensional adaptation, and slice-layout separation | `docs/architecture/canonical_local_board_presentation_geometry.md` |
| Post-Stage-54 presentation-parameter implementation and agent-driven acceptance evidence | `docs/plans/presentation_parameter_contract_acceptance.md` |
| Stage 54F-1 canonical local-board geometry implementation and agent-driven structural/real-window acceptance evidence | `docs/plans/canonical_local_board_presentation_geometry_acceptance.md` |
| Stage 54D-1 authoritative one-piece queue query and shared live thumbnail presentation | `docs/architecture/next_piece_preview.md` |
| Stage 54D-2 authoritative hard-drop destination query and live ghost presentation | `docs/architecture/ghost_piece.md` |
| Completed Stage 50 canonical bounded plain-game setup, RNG, piece-set, speed, restart, and acceptance contract | `docs/architecture/plain_game_setup_completion.md` |
| Stage 51 canonical Godot display settings, persistence, and runtime presentation policy | `docs/architecture/display_infrastructure.md` |
| Stage 52 Godot accessibility invariants, preferences, persistence, and runtime presentation policy | `docs/architecture/accessibility_infrastructure.md` |
| Stage 22f manual Live 3D acceptance run record | `docs/plans/godot_live_3d_manual_acceptance.md` |
| Current restart handoff | `CURRENT_STATE.md` |
| Open execution backlog and current work footprint | `docs/BACKLOG.md` |
| Durable product behavior contracts | `docs/rds/*.md` |
| Contributor workflow and verification sequence | `docs/WORKFLOW_CODEX.md` |
| Machine-readable governance and maintenance authority | `config/project/policy_pack.json` |
| Config-first keybinding editing workflow | `docs/KEYBINDINGS_EDITING.md` |
| Short practical keybinding editing checklist | `docs/SHORT_KEYBINDINGS_GUIDE.md` |
| Config-first menu editing workflow | `docs/MENU_STRUCTURE_EDITING.md` |
| Historical background and retired plans | `docs/history/*` |

## Precedence

`docs/WORKFLOW_CODEX.md` owns source-of-truth precedence. This map owns
documentation roles and routing only; it does not outrank the product or
architecture authority it helps readers locate. When a routed document is
stale, follow the workflow precedence and update or archive the stale text in
the same change.

## Scope boundaries

### `docs/ARCHITECTURE_CONTRACT.md`
Owns dependency direction, package ownership rules, and enforcement.
It does not own current execution state or active migration-phase detail.

### `docs/PROJECT_STRUCTURE.md`
Owns package layout, entrypoint inventory, and generated ownership snapshots.
It does not own architecture law.

### `docs/plans/*`
Own current active planning authority/spec/debt.
They do not replace durable RDS behavior contracts outside active in-flight
migration exceptions.

### `docs/plans/professional_godot_game_programme.md`
Owns programme order, phase gates, and cross-phase product priorities.
It does not own detailed feature behaviour, implementation history, or current
batch status.

### `docs/rds/*`
Own durable product requirements and behavior contracts.
They must not accumulate active batch logs, migration diaries, or completed-pass
history.

### `CURRENT_STATE.md`
Owns restart handoff only.
It is not the historical ledger.

### `docs/BACKLOG.md`
Owns open work and current change footprint.
It is not the product contract or complete roadmap.

## Reader shortcuts

- If you need the docs entrypoint only: use `docs/README.md`.
- If you need routing or precedence: use `docs/DOCUMENTATION_MAP.md`.
- If you need the active professional Godot product programme and phase order:
  use `docs/plans/professional_godot_game_programme.md`.
- If you need the current repo architecture: start with
  `docs/ARCHITECTURE_CONTRACT.md`.
- If you need current subsystem authority, inherited Python-reference limits,
  or new-authority establishment: use `docs/architecture/authority_map.md` and
  `docs/architecture/authority_transfer_protocol.md`.
- If you need the current topology-playground direction: start with
  `docs/plans/topology_playground_current_authority.md`.
- If you need the current topology-playground shell behavior: use
  `docs/plans/topology_playground_shell_redesign_spec.md`.
- If you need Live 3D or future Live 4D gameboard visual-language rules: use
  `docs/plans/gameboard_visual_language_design.md`.
- If you need current Godot visual direction, theme purposes, semantic roles,
  typography, spacing, component states, accessibility composition, or
  board/shell hierarchy: use `docs/design/godot_visual_system.md`.
- If you need earlier palette-token implementation context or the historical
  Vector Arcade overhaul record: use
  `docs/architecture/godot_visual_style_foundation.md` and
  `docs/architecture/godot_vector_arcade_cockpit_overhaul.md`.
- If you need the Stage 46 plain live gameplay completion scope, audit, or
  later-stage deferrals: use
  `docs/architecture/godot_core_gameplay_completion.md`.
- If you need the Stage 47 contextual onboarding, navigation, or session-local
  guidance contract: use
  `docs/architecture/godot_guided_onboarding_navigation.md`.
- If you need the Stage 48 Godot shell persistence, recovery, reset, or
  persistent-setting inventory: use
  `docs/architecture/godot_shell_settings_persistence.md`.
- If you need configurable Godot plain-board presets, parameterized native live
  sessions, or adaptive 4D layer layout: use
  `docs/architecture/configurable_plain_boards_and_4d_layout.md`.
- If you need editable Godot board dimensions, draft/last-valid behavior, or
  `game_setup.json` schema 3 migration: use
  `docs/architecture/editable_board_setup_and_persistence.md`.
- If you need exact 4D presentation-basis composition, basis-aware coordinate
  mapping, or view-relative input routing: use
  `docs/architecture/game_safe_4d_slice_basis.md`.
- If you need the accepted separation of exact basis, slice-local orientation,
  slice layout, final view, or the Stage 54E-1 resolver verdict: use
  `docs/architecture/4d_presentation_interaction_architecture.md`.
- If you need presentation-parameter identity, ownership, bounds, profile
  composition, persistence isolation, live application, or the documented
  3D/4D divergence: use
  `docs/architecture/presentation_parameter_contract.md`.
- If you need durable menu or gameplay product rules: use `docs/rds/*`.
- If you need repo workflow or verification order: use `docs/WORKFLOW_CODEX.md`.
- If you need to constrain a repository-changing task: use
  `docs/governance/task_contract.md`.
- If you need the required handoff fields: use
  `docs/governance/completion_report.md`.
- If you need task-specific context loading: use the context-switch profiles in
  `docs/WORKFLOW_CODEX.md`.
- If you need to edit keybinding structure or shipped defaults: use
  `docs/KEYBINDINGS_EDITING.md`.
- If you need a short practical keybinding edit checklist: use
  `docs/SHORT_KEYBINDINGS_GUIDE.md`.
- If you need to edit the menu graph or filtered settings structure: use
  `docs/MENU_STRUCTURE_EDITING.md`.
- If you need the live work handoff: use `CURRENT_STATE.md` and
  `docs/BACKLOG.md`.
- If you need completed parity or migration evidence: use the historical
  evidence index above, `docs/governance/README.md`, and Git history.
- If you need other historical context only: use `docs/history/*`.
