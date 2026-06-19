# Governance Router

This repository is Python-centered. Godot/C++ migration governance is an
overlay, not a replacement for existing Python/repo governance.

## Applies everywhere

- machine-readable governance authority: `config/project/policy_pack.json`
- Codex workflow policy: `docs/governance/codex_policy.md`
- repo workflow explainer: `docs/WORKFLOW_CODEX.md`
- existing repo policies under `docs/policies/`
- secrets/security policy: `docs/governance/secrets_policy.md`
- config/constants policy: `docs/governance/config_policy.md`
- config authority validator:
  `tools/governance/validate_config_authority.py`
- native C++ safety policy: `docs/governance/cpp_safety_policy.md`
- testing policy: `docs/governance/testing_policy.md`
- review checklist: `docs/governance/review_checklist.md`

## Applies to current Python implementation

- `docs/ARCHITECTURE_CONTRACT.md`
- relevant `docs/rds/*`
- current tests and trace behavior
- current semantic implementation under `src/tet4d/`

## Applies to Godot/C++ migration

- Godot/C++ migration policy: `docs/governance/godot_cpp_policy.md`
- native C++ safety policy: `docs/governance/cpp_safety_policy.md`
- native C++ tooling validator:
  `tools/governance/validate_native_cpp_tooling.py`
- architecture authority map: `docs/architecture/authority_map.md`
- parity protocol: `docs/architecture/parity_protocol.md`
- migration plan: `docs/plans/godot_core_port_plan.md`
- topology migration plan: `docs/plans/topology_godot_core_port_plan.md`
- utility index: `docs/architecture/utility_index.md`
- relevant local `AGENTS.md` files

## Work-type routing

| Work type | Read first |
|---|---|
| Python gameplay/topology/trace behavior | `AGENTS.md`, `docs/WORKFLOW_CODEX.md`, `docs/ARCHITECTURE_CONTRACT.md`, relevant `docs/rds/*` |
| Godot UI/product shell | `AGENTS.md`, `godot/AGENTS.md`, `docs/governance/godot_cpp_policy.md`, `docs/architecture/authority_map.md` |
| C++/GDExtension/native | `AGENTS.md`, `native/AGENTS.md`, `docs/governance/godot_cpp_policy.md`, `docs/governance/cpp_safety_policy.md`, `docs/architecture/parity_protocol.md`, `docs/architecture/authority_map.md` |
| Testing/parity | `docs/architecture/parity_protocol.md`, `docs/governance/testing_policy.md`, relevant test docs and trace plans |
| Config/constants | `docs/governance/config_policy.md`, `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`, `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`, `tools/governance/validate_config_authority.py` |
| Secrets/security | `docs/governance/secrets_policy.md`, `config/project/policy/manifests/secret_scan.json` |
| Mixed migration | all relevant Python, Godot, native, testing, config, and authority docs above |

## Authority rule

The existing Python implementation is the semantic oracle. Godot and C++ code
are ports/adapters until explicitly promoted by documented parity evidence.

## Conflict rule

When documents conflict:

1. Safety/security rules win over convenience.
2. Existing Python semantics win over migration convenience.
3. The authority map decides ownership.
4. Folder-local `AGENTS.md` may add narrower constraints but must not weaken
   root constraints.
5. New Godot/C++ governance may clarify migration work but must not silently
   supersede existing Python governance.
