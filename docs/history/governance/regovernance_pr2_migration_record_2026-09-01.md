# Re-Governance PR 2 Migration Record

Status: historical, non-authoritative migration evidence

This record captures the pre-deletion coverage review for the canonical-owner
cut. It is not a governance router. Current governance starts at `AGENTS.md`.

## Baseline

The baseline is merged PR 1 commit
`bfea3bdb650fcec273ec98647eda810d6cef194f`. The defined human-facing active
governance boundary was 3,089 lines; `config/project/policy_pack.json` was
2,725 lines. The boundary counted root and local dispatch files,
`CURRENT_STATE.md`, the pull-request template, the authority-transfer protocol,
and the superseded workflow, documentation-map, governance, policy, and
workspace-bundle Markdown files.

## Source disposition and obligation coverage

The machine-reference column records the pre-cut coupling that was reconciled
atomically. “None direct” means the source was reached only through another
human router or documentation link.

| Source | Canonical destination | Machine-policy references | Route/reference consumers | Final disposition |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | Root constitution/router | `authority_model`, `maintenance_contract`, route dispatch | All contributors; local dispatch | RETAIN AS DISPATCH |
| `CLAUDE.md` | `AGENTS.md` | `maintenance_contract.required_paths` | Model compatibility entry | RETAIN AS DISPATCH |
| `godot/AGENTS.md` | Root plus native/platform and verification owners | Route dispatch, required paths | Godot subtree | RETAIN AS DISPATCH |
| `native/AGENTS.md` | Root plus native/platform and verification owners | Route dispatch, required paths | Native subtree | RETAIN AS DISPATCH |
| `docs/WORKFLOW_CODEX.md` | `CHANGE_GOVERNANCE.md`, `VERIFICATION.md` | Former workflow pointer, content rules, sources of truth | Root/docs/PR workflow links | MERGE INTO CANONICAL OWNER |
| `docs/DOCUMENTATION_MAP.md` | Six owners plus existing RDS/architecture indexes | Former required path and deprecated-reference checks | Documentation navigation | MERGE INTO CANONICAL OWNER |
| `docs/governance/README.md` | Direct root-to-owner routing | Former governance route and content rules | Root/local governance links | DELETE |
| `docs/governance/codex_policy.md` | `ENGINEERING.md`, `CHANGE_GOVERNANCE.md` | Former content/directive sources | Governance router and review checklist | MERGE INTO CANONICAL OWNER |
| `docs/governance/config_policy.md` | `CONFIG_AND_GENERATED_DATA.md` | Required paths/content rules | Policy index, router, validators | MERGE INTO CANONICAL OWNER |
| `docs/governance/cpp_safety_policy.md` | `NATIVE_AND_PLATFORM.md` | Required paths | Native dispatch, router, validator | MERGE INTO CANONICAL OWNER |
| `docs/governance/drift_protection_map.md` | `CHANGE_GOVERNANCE.md` plus machine contracts | Required paths/content rules | Router, architecture evidence, validators | MERGE INTO CANONICAL OWNER |
| `docs/governance/godot_cpp_policy.md` | `NATIVE_AND_PLATFORM.md`; semantic ownership remains architecture-owned | Required paths | Local dispatch and migration plans | MERGE INTO CANONICAL OWNER |
| `docs/governance/native_tooling_ci_policy.md` | `NATIVE_AND_PLATFORM.md`, `VERIFICATION.md` | Required paths/content rules | Native dispatch, review, validator | MERGE INTO CANONICAL OWNER |
| `docs/governance/review_checklist.md` | `CHANGE_GOVERNANCE.md`, `VERIFICATION.md`, PR template | Required paths/content rules | Governance router and validators | MERGE INTO CANONICAL OWNER |
| `docs/governance/secrets_policy.md` | `SECURITY_AND_SANITATION.md` | Required paths/content rules | Governance router and scanner guidance | MERGE INTO CANONICAL OWNER |
| `docs/governance/technical_debt_register.md` | Process to `ENGINEERING.md`; open items to `docs/BACKLOG.md` | Required paths/content rules | Router, review, debt validator | MERGE INTO CANONICAL OWNER |
| `docs/governance/testing_policy.md` | `VERIFICATION.md` | Required paths/content rules | Router and review checklist | MERGE INTO CANONICAL OWNER |
| `docs/policies/INDEX.md` | Direct root-to-owner routing | Required paths/content rules | Contributor docs and policy links | DELETE |
| `docs/policies/CI_COMPLIANCE_RUNBOOK.md` | `VERIFICATION.md`; commands remain script-owned | Required paths/content rules | Policy index and workflow | MERGE INTO CANONICAL OWNER |
| `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md` | `CONFIG_AND_GENERATED_DATA.md` | Former index route | Config validator and docs | MERGE INTO CANONICAL OWNER |
| `docs/policies/POLICY_FORMATTING.md` | `ENGINEERING.md`, `VERIFICATION.md` | Former index route | Workflow and CI guidance | MERGE INTO CANONICAL OWNER |
| `docs/policies/POLICY_NO_MAGIC_NUMBERS.md` | `CONFIG_AND_GENERATED_DATA.md` | Former content/directive source | Config validator and review | MERGE INTO CANONICAL OWNER |
| `docs/policies/POLICY_NO_REINVENTING_WHEEL.md` | `ENGINEERING.md`, `SECURITY_AND_SANITATION.md` | Former content/directive source | Utility validator and review | MERGE INTO CANONICAL OWNER |
| `docs/policies/POLICY_STRING_SANITATION.md` | `SECURITY_AND_SANITATION.md` | Former content/directive source | Runtime rules and review | MERGE INTO CANONICAL OWNER |
| `docs/governance/workspace_bundle/AGENTS.template.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/MANIFEST.md` | Generic template manifest | Former bundle required path | Bundle validator/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/README.md` | Generic template instructions | Former bundle required path | Bundle validator/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/codex_workflow_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/config_constants_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/dependency_reuse_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/drift_protection_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/programming_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/review_checklist_template.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/secrets_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/technical_debt_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/testing_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |
| `docs/governance/workspace_bundle/validator_design_policy.md` | Generic bootstrap template | Former bundle required path | Bundle manifest/exporter | MOVE TO NON-AUTHORITATIVE TEMPLATE |

The reusable templates now live at `tools/templates/governance/`, clearly state
`NON-AUTHORITATIVE TEMPLATE`, do not route tet4d work, and are excluded from the
active governance boundary.

## Debt-record disposition

- `TD-0001`, `TD-0002`, and `TD-0004` remain explicit deferrals in
  `docs/BACKLOG.md` with their triggers and owners.
- `TD-0003` is closed: PR 1 made the full Ruff formatting gate green. The
  historical identifier remains here for traceability and is not an active
  debt record.

## Semantic result

No product, runtime, schema, replay, trace, topology, packaging, or subsystem
authority changes. The change replaces overlapping contributor-process owners
and makes route selection compositional. Existing RDS, architecture,
authority-map, parity, and transfer/establishment contracts remain untouched as
semantic owners.

## Measured result

Using the same boundary defined above, human-facing active governance changes
from 3,089 to 1,055 lines, a reduction of 2,034. The machine policy changes
from 2,725 to 2,662 lines, a reduction of 63. The combined active read surface
therefore changes from 5,814 to 3,717 lines, a reduction of 2,097 and below the
PR 2 preferred range.

The machine policy remains above the deferred PR 3 target because it still
contains historical toolchain/audit result payloads and unrelated verbose
contracts. Removing those payloads, adding permanent total-size and provenance
budgets, and reducing backlog repetition are deliberately not part of this cut.
