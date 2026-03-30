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

- `docs/RDS_AND_CODEX.md`
- `docs/KEYBINDINGS_EDITING.md`
- `docs/SHORT_KEYBINDINGS_GUIDE.md`
- `docs/MENU_STRUCTURE_EDITING.md`
- `docs/policies/*`
- top-level governance in `config/project/policy/governance.json` and
  `config/project/policy/code_rules.json`
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
| Current restart handoff | `CURRENT_STATE.md` |
| Open execution backlog and current work footprint | `docs/BACKLOG.md` |
| Durable product behavior contracts | `docs/rds/*.md` |
| Contributor workflow and verification sequence | `docs/RDS_AND_CODEX.md` |
| Config-first keybinding editing workflow | `docs/KEYBINDINGS_EDITING.md` |
| Short practical keybinding editing checklist | `docs/SHORT_KEYBINDINGS_GUIDE.md` |
| Config-first menu editing workflow | `docs/MENU_STRUCTURE_EDITING.md` |
| Historical background and retired plans | `docs/history/*` |

## Precedence

When documents disagree, precedence is:

1. newer task instruction
2. owning active plan `authority` document for the domain
3. owning active or frozen plan `spec` document for the domain
4. this file for documentation routing and file ownership
5. durable RDS contract for the topic
6. architecture and structure docs
7. current-state/backlog/generated references
8. historical docs

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
- If you need durable menu or gameplay product rules: use `docs/rds/*`.
- If you need to edit keybinding structure or shipped defaults: use
  `docs/KEYBINDINGS_EDITING.md`.
- If you need a short practical keybinding edit checklist: use
  `docs/SHORT_KEYBINDINGS_GUIDE.md`.
- If you need to edit the menu graph or filtered settings structure: use
  `docs/MENU_STRUCTURE_EDITING.md`.
- If you need the live work handoff: use `CURRENT_STATE.md` and
  `docs/BACKLOG.md`.
- If you need historical context only: use `docs/history/*`.
