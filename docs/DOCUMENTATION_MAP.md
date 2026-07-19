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
- `docs/architecture/first_subsystem_parity_pilot.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/architecture/second_parity_slice_candidate_selection.md`
- `docs/architecture/trace_metadata_identity_digest_parity.md`
- `docs/architecture/parity_evidence_review_and_third_slice_selection.md`
- `docs/architecture/topology_identifier_normalization_parity.md`
- `docs/architecture/parity_evidence_package_review.md`
- `docs/architecture/python_oracle_boundary_audit.md`
- `docs/architecture/python_2d_nd_dedup_audit.md`
- `docs/architecture/parity_tooling_package_review.md`
- `docs/architecture/structural_parity_slice_selection.md`
- `docs/architecture/trace_envelope_validation_parity.md`
- `docs/architecture/godot_shell_layout_stabilization.md`
- `docs/architecture/godot_shell_settings_source_of_truth.md`
- `docs/architecture/godot_shell_settings_persistence.md`
- `docs/architecture/configurable_plain_boards_and_4d_layout.md`
- `docs/architecture/plain_game_setup_completion.md`
- `docs/architecture/display_accessibility_completion.md`
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
- `docs/plans/cleanup_master_plan.md`
- domain-specific active plan files under `docs/plans/`
- recent planning-adjacent audits under `docs/plans/audits/`

### 4. Current execution state

These files track live restart context and open execution work.

- `CURRENT_STATE.md`
- `docs/BACKLOG.md`

### 5. Product/spec contracts

These files define durable behavior contracts and product requirements.

- `docs/rds/README.md`
- `docs/rds/*.md`

### 6. Contributor workflow and policy

These files define contributor process, policy, and verification workflow.

- `AGENTS.md`
- `docs/WORKFLOW_CODEX.md`
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

## Ownership map

| Topic | Primary owner |
| --- | --- |
| Documentation-layer routing and file-role boundaries | `docs/DOCUMENTATION_MAP.md` |
| Planning-layer routing and planning-doc ownership | `docs/plans/README.md`, `docs/plans/plan_authority_map.md` |
| Codebase dependency rules and package ownership law | `docs/ARCHITECTURE_CONTRACT.md` |
| Canonical package layout, entrypoints, and generated ownership inventory | `docs/PROJECT_STRUCTURE.md` |
| Current topology-playground architecture and invariants | `docs/plans/topology_playground_current_authority.md` |
| Current topology-playground visible shell contract | `docs/plans/topology_playground_shell_redesign_spec.md` |
| Topology-playground deferred cleanup and transitional debt | `docs/plans/topology_playground_debt_register.md` |
| Repo-wide structural cleanup sequencing | `docs/plans/cleanup_master_plan.md` |
| Live 3D and future Live 4D gameboard visual language | `docs/plans/gameboard_visual_language_design.md` |
| First subsystem parity pilot | `docs/architecture/first_subsystem_parity_pilot.md` |
| Future parity-slice promotion gate | `docs/architecture/parity_pilot_audit_and_promotion_gates.md` |
| Stage 18 selected parity candidate and boundary | `docs/architecture/second_parity_slice_candidate_selection.md` |
| Stage 18 trace metadata identity/digest parity implementation | `docs/architecture/trace_metadata_identity_digest_parity.md` |
| Stage 19 parity evidence review and third-slice selection | `docs/architecture/parity_evidence_review_and_third_slice_selection.md` |
| Stage 21 parity evidence package review of Stages 15, 18, and 20 and further expansion boundary | `docs/architecture/parity_evidence_package_review.md` |
| Stage 22 trace schema/version normalization parity implementation | `docs/architecture/trace_schema_version_normalization_parity.md` |
| Stage 23 Python oracle boundary audit | `docs/architecture/python_oracle_boundary_audit.md` |
| Stage 45A Python 2D/ND duplication audit and first safe slice | `docs/architecture/python_2d_nd_dedup_audit.md` |
| Stage 24 parity tooling package review and `tools/parity/` decision | `docs/architecture/parity_tooling_package_review.md` |
| Stage 26 structural parity slice selection | `docs/architecture/structural_parity_slice_selection.md` |
| Stage 27 trace envelope validation parity implementation | `docs/architecture/trace_envelope_validation_parity.md` |
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
| Completed Stage 50 canonical bounded plain-game setup, RNG, piece-set, speed, restart, and acceptance contract | `docs/architecture/plain_game_setup_completion.md` |
| Stage 51 Godot display, accessibility, camera, help, and schema-v2 shell-settings completion | `docs/architecture/display_accessibility_completion.md` |
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

When documents disagree, precedence is:

1. newer task instruction
2. `config/project/policy_pack.json` for repo governance, validation, and generated maintenance automation
3. owning active plan `authority` document for the domain
4. owning active or frozen plan `spec` document for the domain
5. this file for documentation routing and file ownership
6. durable RDS contract for the topic
7. architecture and structure docs
8. current-state/backlog/generated references
9. historical docs

If a lower-precedence file conflicts with a higher-precedence file, update or
move the lower-precedence file in the same batch.

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

### `docs/rds/*`
Own durable product requirements and behavior contracts.
They must not accumulate active batch logs, migration diaries, or completed-pass
history.

### `CURRENT_STATE.md`
Owns restart handoff only.
It is not the historical ledger.

### `docs/BACKLOG.md`
Owns open work and current change footprint.
It is not the product contract.

## Reader shortcuts

- If you need the docs entrypoint only: use `docs/README.md`.
- If you need routing or precedence: use `docs/DOCUMENTATION_MAP.md`.

- If you need the current repo architecture: start with
  `docs/ARCHITECTURE_CONTRACT.md`.
- If you need the current topology-playground direction: start with
  `docs/plans/topology_playground_current_authority.md`.
- If you need the current topology-playground shell behavior: use
  `docs/plans/topology_playground_shell_redesign_spec.md`.
- If you need Live 3D or future Live 4D gameboard visual-language rules: use
  `docs/plans/gameboard_visual_language_design.md`.
- If you need the current Stage 22f manual Live 3D gate status: use
  `docs/plans/godot_live_3d_manual_acceptance.md`.
- If you need Godot visual style, theme roles, typography, spacing, component
  styling, board/replay visual language, or the Godot shell MVP visual
  baseline: use `docs/architecture/godot_visual_style_authority.md`.
- If you need the current Godot implementation route for shell palette tokens
  and style application: use
  `docs/architecture/godot_visual_style_foundation.md`.
- If you need the current Godot Vector Arcade Cockpit UI overhaul status,
  acceptance criteria, or boundary: use
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
- If you need durable menu or gameplay product rules: use `docs/rds/*`.
- If you need repo workflow or verification order: use `docs/WORKFLOW_CODEX.md`.
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
- If you need historical context only: use `docs/history/*`.
