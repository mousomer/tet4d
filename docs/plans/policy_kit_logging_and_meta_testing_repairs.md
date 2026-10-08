# Policy kit logging and manifest meta testing repairs

Status: implementation authorized by the owner on 2026-10-04. This document
combines the logging and meta-test packaging gaps with the supplied review of
the all-repository rollout. The authorization covers the successor kit, safe
state migration and guarded adoption described below. Model downloads, unrelated
product repairs and deferred telemetry continuation retain their existing gates.

The objective is a durable, reproducible policy-kit with its own meaningful
verification suite, bounded and actionable diagnostics, release-pinned skills,
and honest evidence of execution. Fix the existing P1a logging and publication
contracts without claiming that all agent activity is already captured.

## Current contract and verified findings

The active distribution is `workspace/policy-kit` 1.2.0, with portable runtime
0.5.0. Its release manifest digest is
`adb3e15dcb733f491c493de424750d056cb3b3485042d4b9662118e36a1536df`.
Keep this immutable release and its original receipts unchanged.

Design sources are `docs/architecture/workspace_governance_distribution.md`,
`docs/architecture/workspace_governance_v0_1.md`,
`docs/governance/CHANGE_GOVERNANCE.md`, `docs/governance/VERIFICATION.md`,
`docs/plans/all_repository_governance_rollout.md`, and the kit README.
The six Tet4D human owners retain their existing authority. The supplied
review's measurements are historical observations, not checks rerun for this
plan. Source inspection and safe parser probes confirmed the following issues.

| ID | Verified issue | Required correction |
| --- | --- | --- |
| R1 | Private registry, evidence and undo preimages live under a Codex visualization session; editable kit sources have no Git history. | Permanent private state, verified backup/restore and independent source history. |
| R2 | The full helper precedes quiet mode and lock setup; failures reduce policy output to hashes, warnings lose context, and overlapping checks/renderers execute repeatedly. | Native gate integration, safe structured diagnostics and exact-contract execution grouping. |
| R3 | Audit does not validate the evidence envelope's kind, registry digest or collector provenance; matching record fields can be fabricated. | Strict envelope and run validation, plus an explicit execution-evidence trust boundary. |
| R4 | Explicit/inherited shell startup injection and repeated Makefiles are admitted; executable basenames also admit foreign shell/Make paths and PATH overrides. | Declared executable/environment policy and rejection before any dispatch. |
| R5 | Global skill links point at editable bodies; ordinary `gov check` does not semantically validate adapter target/hash/release. | Immutable discovery targets and an explicit adapter contract. |
| R6 | A local `CLAUDE.md` alias to `AGENTS.md` is rejected. | Bounded alias support preserving the link and no-follow installer writes. |
| R7 | Audit runs structural `gov check`, while the collector uses the declared baseline; execution timeout/environment handling differs. | Distinct structural/baseline states and one bounded execution implementation. |
| R8 | Incidental Git HEAD is inside the release identity. | Deterministic content identity with source history in separate publication provenance. |
| R9 | External/text-conversion Git helpers can affect identity; untracked nested directories lack descendant identity. | Deterministic Git invocation and explicit child boundaries or a non-accepted unsupported state. |
| R10 | Reversed adjacent managed markers pass the ordering check; a tools-profile prerelease Python string fails integer parsing; the Tet4D binding duplicates an authority path. | Strict marker grammar, consistent numeric runtime-floor semantics and deterministic authority deduplication. |
| R11 | The primary registry freezes BACKLOG.md as a managed installer postimage; adding this requested plan correctly blocks its stale replacement. | Separate one-time migration edits from continuing installer ownership of mutable human documents. |
| M1 | Meta-test names and contradiction fixtures ship, but executable contracts remain in Tet4D. | A kit-owned portable verification component and full kit gate. |
| L1 | P1a logging ships and is opt-in; an enabled but unwritable private store only produces a warning. | Observable recording readiness, explicit private write probes and logging failure tests. |

Two corrections to the supplied review matter. Fleet identity checks already
detect changes to registered repository adapters; the missing guarantee is
ordinary context validation and global release pinning. Also, a mode-600 key
does not protect evidence from an agent or verifier running as the same user.

## Acceptance and evidence boundary

Completion requires all repair cases to have accepting and rejecting tests,
the kit's full gate to run from an extracted standalone release with Tet4D
unavailable, unchanged release bytes to yield unchanged identity, and actual
pilot verification followed by guarded fleet adoption. Installation, bounded
validation, baseline success and product acceptance stay separate states.

Use the existing governed interpreter and declared dependencies. Checks must
not install packages, create a venv, access a model or require network access.
Ordinary `gov check`, `resolve` and `explain` must remain bounded and must not
start pytest, application renderers or product verifiers.

For the current same-user machine model, describe execution records as
**collector-reported execution attestations**. Strict validation supplies
scope, consistency and freshness; it does not prove execution against an actor
who can rewrite the evidence and collector. Do not replace that distinction
with a locally readable signing key. A stronger claim requires a separately
protected signer/collector identity and issuance interface outside the agent
and consumer processes' access boundary. That is a separate infrastructure
decision, not a prerequisite invented for this local repair.

## Implementation sequence

### 1 Preserve state and establish source history

Move the complete private bundle to
`${XDG_STATE_HOME:-~/.local/state}/workspace-governance/distribution/`.
Use owner-only directory and file permissions. Retain exact bytes, modes,
historical plans, receipts, failed evidence and source captures; do not retag
old proof or casually rewrite embedded historical paths.

Copy into staging, validate a complete file manifest, test recovery, and only
then switch machine configuration atomically. Keep the original session copy.
Use a cooperative distribution lock to quiesce collectors, planners, receipt
writers and audit output for the final snapshot and switch; an in-flight writer
must not update the old bundle after activation. Do not interrupt an authorized
product gate to force migration. Flush retained data and the activation boundary
durably, and test concurrent writers, interruption and restart recovery.
Record any historical path mapping explicitly; produce fresh plans rather than
reusing a plan tied to its old registry path. Interrupted migration must leave
the previous configuration usable. Create an independent non-session backup
and test restoration with the source session unavailable; state clearly that
two directories on one disk do not protect against device loss.

Put the public-safe editable kit, publication tooling, tests and release
contract in a dedicated source repository. Exclude `_machine/`, private state,
receipts, raw transcripts, telemetry and keys before recording any history.
Use the existing isolated governance worktree where appropriate for Tet4D
integration. Preserve the primary fast-session-flow branch and unrelated edits;
governance and product changes must have separate reviewable scopes.

Update the owning distribution design and correct its durability/review claims
before implementing the remaining phases.

### 2 Repair execution, identity and evidence contracts

In `fleet_support.py` and `fleet_execution.py`, resolve the approved shell/Make
executable and declared runner before dispatch. Reject foreign paths, startup
assignments such as `BASH_ENV`, prohibited PATH changes, all foreign/repeated
Makefile combinations and existing dry-run/skip escapes. Scrub prohibited
ambient startup and Make overrides. Retain approved consumer variables through
an explicit environment policy; do not discard application requirements
indiscriminately or print variable values. Bind that policy's version to proof.

Make Git identity independent of external diff/text-conversion configuration.
Use deterministic arguments including `--no-ext-diff --no-textconv`. Handle
Git-visible nested directories by an explicit child-checkout contract or fail
with an unsupported/incomplete identity; directory metadata alone is not proof
that child contents stayed unchanged. Never turn this into recursive installer
writes or silently hash protected/ignored trees as if coverage were complete.

Validate evidence against a versioned envelope before examining records:
kind, registry and release digests, collector and execution-policy versions,
completed run identity, IDs, timestamps, actual argv, baseline/product outcomes,
timeout state and stable pre/post identities. Reject duplicate/unknown IDs,
invalid types, contradictory statuses, missing baselines, incomplete runs and
wrong bindings. Failed records remain historical evidence and cannot establish
acceptance. A registered handler or test name is not execution authentication.
Validate the declared selection and aggregate consistency without requiring a
completed mixed-result batch's top-level `ok` to be true. Its matching finalized
passing records can establish the stated local acceptance for those consumers;
genuine failing records remain failures. Incomplete or malformed records cannot
borrow another consumer's successful result.

Keep default audit structural/evidence-only. Label structural observation
separately from the declared governance baseline. Use the same bounded
process-group timeout and environment implementation as the collector. Add an
explicit bounded baseline-refresh mode resolving the same `governance_runner`
as the collector; keep product verification a distinct requested action.
No default audit may silently execute renderers/products or bypass holds.

Fix managed-marker ordering and line grammar, including duplicate and adjacent
reversed markers. Support only declared same-directory relative
`CLAUDE.md -> AGENTS.md` aliases to a regular file. Write the dispatch once to
AGENTS, preserve exact link text/type, and recheck it before apply, audit and
undo. External, absolute, chained, cyclic, dangling or changed aliases reject.
Preserve no-follow semantics for every installer write.

Classify each private managed-file entry by ongoing ownership. Remove mutable
human backlog/current-state and authority bodies from static desired installer
content after an accepted one-time migration; retain their historical receipts
and authority/evidence references. Future installation owns declared machinery,
bindings and bounded dispatch sections, not an old copy of ordinary open work.
Test that adding a backlog item leaves it intact through plan/reapply and does
not trigger a request to restore stale text. Authority changes still require
their semantic review and fresh evidence; this is not an audit bypass.

Use a shared stdlib numeric Python-floor comparison for the dependency-light
tools profile, covering prerelease version strings. Keep application-profile
compound requirements and their declared prerelease policy separate. Remove
duplicate authority paths while retaining first occurrence and owner order.

### 3 Restore gate diagnostics and demonstrate P1a logging

Integrate Tet4D through its native named governance graph after environment,
quiet-mode and lock setup, rather than prepending the complete standalone helper.
Map every existing obligation to its accepting invocation; preserve provenance
families and stronger duties. Each equivalent check runs once within a full
gate. The standalone declared baseline remains available. Do not introduce an
environment flag or reusable "already checked" result that skips real checks.
The collector may deliberately execute a standalone baseline before a distinct
full product invocation; do not confuse those two runs with internal duplication.

Validate every generated declaration, then group only identical resolved argv,
cwd, interpreter/binding, environment and timeout contracts. Execute such a
group once, retain mutation guards and verify all declared outputs. Attribute
failure to every affected surface. Different contracts stay separate. Preserve
equivalent named gate/provenance coverage when sharing a renderer execution.

Emit bounded diagnostics with check/rule ID, severity, safely escaped relative
location and remediation. Preserve warnings and their existing exit semantics.
Summarize passing files and scanner exclusions by counts/reasons. Avoid matched
secret content from sanitation and secret scanners, including in verbose mode.
Ordinary native checker failures retain actionable diagnostics and their exit
status; their successful output remains quiet unless verbose mode is selected.
A quiet failure must identify the cause rather than only a digest; quiet success
must fit a documented bound tested with large skipped-file fixtures.

Add a proposed telemetry status/readiness interface and an explicit private
write selftest. Report disabled, enabled/recording, enabled/unwritable and unknown
states accurately; filesystem permission bits alone do not prove a sandboxed
process can write. A write probe uses owner-only persistent state, clearly
distinguished synthetic observations and no secrets. Disabled telemetry writes
nothing. Recording failure continues to preserve the observed command's exit
status, while the explicit recording selftest reports failure.
Read-only status may report configuration and the last observed successful
append; a recording claim must carry observation time and store identity rather
than infer present writability. Probe observations must never supply ordinary
command or product acceptance evidence.

Verify event schema, safe argument handling, attribution, observation/persistence
times, private key separation, isolation and interrupted/concurrent key creation.
Make no switch to global automatic logging. P1b/P1c importers/reconstruction and
P6 interpretation remain behind the existing 56H postmortem continuation gate;
C1/G1/postmortem analyses remain outside consumers of generic instrumentation.

### 4 Package portable meta-tests and deterministic releases

Create kit-owned `tests/workspace_governance/` using synthetic consumer builders.
Fixtures must not clone Tet4D manifests/docs/scripts, symlink its product trees,
import Tet4D, or consult its host execution mode. Provide a Python application,
a tools/native consumer without fabricated `pyproject.toml`, and multiple
checkouts sharing one workspace. Construct authorities, pointer forms, routes,
renderers and targets locally; isolate both XDG configuration and state.

Extract consumed-field, contradiction, diagnostic, authority/role/route,
membership, environment, overlay, source-binding, project-independence,
telemetry, fleet, sanitation, export and repair-safety contracts. Preserve
Tet4D-specific six-owner, Godot route, application packaging and actual gate
integration tests in Tet4D. Establish one canonical shared suite with a declared
invocation; do not maintain divergent generic copies.

Strengthen consumed-field proof: every consumed schema leaf, including optional
fields and direct/reference forms, needs a representative fixture and a
field-specific semantic change or expected controlled diagnostic. An arbitrary
exception, unrelated output change or schema-only type rejection does not prove
consumption. Unexpected failures fail the test. Execute each contradiction
fixture and every advertised diagnostic class, with positive controls.

Declare the test interpreter floor, pytest/packaging ranges and Git/Bash needs.
Add proposed `scripts/verify_policy_kit.sh` as the full kit gate. Keep the
existing selftest a quick integrity command, and keep context commands free of
test startup. The full gate verifies and tests the exact selected candidate or
immutable runtime and records both runtime and verification identities.
Default to the active immutable verification component; require explicit
candidate selection for editable work. Assert imported runtime module origins
and all schema/registry/catalog roots are inside the selected components. Test
poisoned `PYTHONPATH` and different editable-kit bytes so the developer checkout
cannot silently satisfy an immutable-release check.

Package tests, fixtures, dependency declarations and the runner as a separately
hashed verification component. The current exporter installs every runtime
artifact through the fleet; placing tests inside that file set would distribute
test tooling to every consumer. Keep installed runtime files distinct from the
verification component in the next release contract. Validate verification bytes
before executing them, and retain them for standalone reconstruction.

Define release identity from deterministic payload paths/hashes/modes, declared
version/revision/schema and the verification component. Put incidental Git HEAD,
source location and publication time in a separate publication receipt. Identical
declared content from another HEAD, checkout or non-Git source has the same
identity. Changed relevant bytes/modes/contracts require a new release.

Global Codex/Claude discovery links must target the active immutable release's
skill directories. Activation updates them through guarded preimages and rollback.
Declare adapter name/target/hash/release relationships and validate them in
ordinary `gov check`, kit verification and fleet checks. An ignored Claude
materialization is acceptable only when its expected contract is versioned and
its actual bytes are checked and a checkout can reproduce the materialization
before checking it. Tet4D's declared repository adapters must be Git-visible.
Editing candidate skills must not alter active
discovery.

### 5 Review, pilot and adopt the successor

Use distribution 1.3.0 / runtime 0.6.0 for the reviewed successor, followed by
the additive 1.3.1 / 0.6.1 publication patch described below;
schema versions change explicitly where contracts require them. Do not modify
1.2.0 or retroactively make its historical evidence meet new guarantees.

Independent review must reproduce the supplied probes and the new rejecting
cases against the candidate. Verify source/adapters/provenance documentation
and generated relationships through their owning generators before release.
Pilot Tet4D, a native/tools consumer and an outside-workspace Python consumer.
Run the exact full kit gate, Tet4D's `CODEX_MODE=1 ./scripts/verify.sh`, and each
pilot's declared verifier against the checked bytes. Observe command counts and
safe quiet failure/warning output, rather than estimating them from code.

Then plan/apply in explicit registry waves, preserving preimages and owner
changes, and collect fresh baseline/product attestations under the new release
and execution policy. Test zero-write reapplication and guarded undo refusal.
Keep old evidence intact; do not copy, retag or sign it into fresh acceptance.

The two existing scientific/product failures, sanitation/template conflicts,
governance-only consumers, IQA execution hold, nine blocked locations and census
gaps remain separate owner work. These repairs must not weaken their checks,
rewrite fixtures or download models to produce a passing fleet report.

## Required proof matrix

| Area | Acceptance proof |
| --- | --- |
| Durability | Copied bundle hashes/modes match; incomplete migration never activates; historical undo works in a disposable consumer with the session source absent; backup restores. |
| Environment | Startup/PATH/foreign executable and every repeated/foreign Makefile escape rejects before dispatch; approved actual runners retain required environment. |
| Evidence | Wrong kind/registry/release/policy, duplicate IDs, inconsistent results, malformed timestamps, timeouts and changed inputs cannot establish acceptance; same-user trust limits are explicit. |
| Audit | Default starts no renderer/product; structural and baseline states differ; explicit baseline uses the declared runner; timeout terminates the process group. |
| Checkout identity | Configured Git diff helpers never run; unsupported nested state stays incomplete and child mutations cannot retain accepted identity. |
| Instruction aliases | Safe alias remains identical through apply/reapply/undo; changed/external/chained/cyclic/dangling aliases and malformed markers reject before writes. |
| Human document ownership | An authorized backlog/current-state edit is preserved through future sync; historical migration backups stay available; changed authorities still invalidate stale evidence. |
| Native gate | Trace shows each equivalent obligation once per full invocation; grouping rejects drift/mutation in only the second target and diagnoses every affected surface; argv, timeout, binding and environment variations stay separate. |
| Diagnostics | Quiet failure gives safe actionable cause; warnings remain visible; many exclusions summarize within a bound; synthetic sensitive output is absent from console and events. |
| Logging | Explicit writable probe records a valid observation; disabled and unwritable cases have truthful status; recording errors preserve command exit; host state/key is untouched in tests. |
| Meta-tests | Standalone extracted kit passes with Tet4D unavailable and poisoned ambient overlays; every consumed optional field and diagnostic has meaningful proof; unimplemented declarations fail. |
| Separation | Installer plan contains no verification bundle or pytest writes; ordinary context commands never launch the meta-suite. |
| Release and skills | HEAD-only/source-location changes are reproducible; altered payload/test bytes reject; candidate skill edits cannot alter active discovery; stale adapter/link contracts reject; activation rollback restores links. |
| Rollout | Actual pilot/full gates, fresh attestations, zero-write reapply and owner-edit undo refusal are recorded; outstanding product/coverage limits remain nonzero. |

## File ownership and planning checkpoint

General changes belong to policy-kit's `fleet.py`, `fleet_support.py`,
`fleet_execution.py`, `validators/core.py`, resolver/CLI/telemetry modules,
`release.py`, schemas, skill contracts, portable tests and publication tooling.
Machine configuration/migration and evidence remain private. Tet4D changes are
its verifier integration, consumer manifests/adapters, specific tests, owning
design documents and generated references. Skills explain the verified command
contract and trust limits; they do not replace executable checks.

Next implementation step: phase 1 preservation and the explicit contract
updates, followed by phase 2 rejecting tests before execution changes. This is
a planning checkpoint only. The active release remains unchanged; full kit,
product and successor acceptance have not been rerun or claimed by this plan.
Documentation edits make earlier checkout-specific proof historical until the
actual changed tree receives its required verification.

Planning checks passed: `gov check`, the pinned inventory check, handoff
lifecycle validation and `git diff --check`. Read-only calls through the
canonical distribution configuration ran its guarded planner and structural
fleet audit without saving over historical artifacts or starting products.
After the planning edits, the planner reports 33 unchanged, 104 external and
10 blocked locations: the original nine plus the protected stale backlog
postimage. Audit reports four accepted, 104 read-only and 39 incomplete, with
41 failures including scope gaps. These are current planning observations,
not regression claims about the product or a successor release.

## Implementation checkpoint: durable state and released contracts

The public-safe kit now has an independent source repository. Private registry,
receipts and failed evidence remain excluded. The complete session bundle was
copied under the persistent distribution writer lock into permanent private
state and a separate private backup. All 440 files were verified before the
configuration pointers switched atomically; restoration of all 440 files from
the backup also passed. The original session copy remains unchanged. Original
modes are recorded as provenance; destination permissions were tightened to
owner-only where the source had group/other access. Both copies use the same
device and provide no device-loss protection.

Distribution 1.3.0 / runtime 0.6.0 passed 544 cases in both its frozen export
and the actual canonical kit. Its independent Tet4D implementation worktree
passed the full source verifier and 114 retained project integration cases.
Before any fleet installer writes, review found that public fleet metadata
would copy machine execution paths from the private registry. The additive
1.3.1 / 0.6.1 patch publishes a fingerprint of that entire private policy while
execution continues to consume the complete declaration. Its frozen portable
gate passed 552 cases. Both releases and the earlier 1.2.0 archive remain
immutable; source commit provenance is retained separately from release identity.

The final registry preserves 148 locations: 34 direct, 105 external/read-only
and nine orphaned blockers. The planner can update 33 direct consumers; one
unsupported nested boundary remains blocked. All project tests and mutable
human documents are retired from continuing installer ownership. The private
rebase records retain the original metadata preimages and the separately
reviewed authority-preservation exception, without inventing receipt provenance.

Actual successor verification, guarded consumer application, zero-write
reapplication, fresh v2 collection and telemetry readiness are recorded in the
durable private bundle and final acceptance checkpoint. Baseline collection
covers all 34 direct declarations; product collection is limited to six approved
runners. IQA remains held because its runner may download model weights. RMBG
is also held because a canonical test writes/unlinks a fixed repository fixture
instead of an owner-approved temporary directory. These holds and the existing
scientific failures, sanitation conflicts, nine orphaned markers, unsupported
nested boundary and 155 census errors remain separate owner work. Coverage is
incomplete and the aggregate audit must remain nonzero.

## Applied repair and final proof handoff

The actual canonical kit is active at distribution 1.3.1 / runtime 0.6.1.
Its selfcheck validates 33 editable runtime files, 11 distribution files,
19 compatibility archive files and four immutable discovery links. The guarded
fleet receipt records 33 installed consumers, 863 writes and zero failed
installer rows; all ten blocked and 105 external/read-only locations were
preserved. A fresh saved plan and actual reapplication record zero consumer
writes, including after the authorized human-document and project-test edits.

Tet4D's native verifier retains all named families while factoring shared
contract validation, generated checks and the extension policy checker.
Eight portable test files were retired only after their immutable successors
passed; 114 retained project cases remain in the owning repository. The
independent source worktree has separate manual migration receipts and keeps
its fleet external/read-only classification. Its product evidence never
substitutes for the primary checkout's declared full verifier.

The primary P1a selftest passed append/readback and the subsequent status reports
the last observed recording time and store identity. It explicitly marks the
observation synthetic and product evidence false; present writability remains
unknown. No global logging activation or deferred observer/comparator is added.

Final canonical kit, implementation-worktree and primary/fleet results are
retained as distinct proofs in the durable private bundle. Failed and successful
collection sources stay finalized and separate, bound to the actual release,
registry and stable inputs. The structural audit reads those records and never
starts products. Historical failures and the first failed actual successor
gate remain available for diagnosis; reruns cannot erase them. The current
private audit is the authority for changing product outcomes and incomplete
coverage, rather than a static passing count in this document.

The actual gate's two diagnostic failures came from propagating an owner-only
report umask into synthetic public-source construction: four export fixtures
and the quick-selfcheck fixture acquired unsupported 600 modes. The retained
rerun uses the ordinary 022 public-source creation mode while report/log files
receive explicit 600 permissions inside private directories. It executes the
same immutable tests and validation; no source-mode check or case is bypassed.

## Integration review repair (2026-10-05)

The bounded follow-up repairs Tet4D's Git-visible adapter export and ordinary
full-gate diagnostics. The named invocation graph and checker obligations remain
intact; scanner classifications still suppress matched source. Quiet failures
preserve checker exit codes. The legacy-import guard now reports file/line
locations without copying its source matches.

Regression proof covers real Ruff file/line and rule output in quiet and verbose
modes, all four scanner failure classes, ignored private Claude settings and a
Git-visible checkout export. The first canonical full-gate run exposed an old
interpreter-selection test that expected inventory diagnostics to be hidden;
its assertion now requires the checker cause while retaining interpreter and
exit-status proof. `CODEX_MODE=1 ./scripts/verify_focus.sh
tests/unit/workspace_governance --pytest tests/unit/workspace_governance` and
the rerun of `CODEX_MODE=1 ./scripts/verify.sh` pass. Generated-document,
shell-syntax and whitespace checks also pass. The sanitation baseline retains
three bounded warnings; no check is bypassed.

The review also reproduced ambient `TERM` changing evidence contracts and Make
running product prerequisites before governance. These require shared-kit
repairs and a successor release; runtime 1.3.1 remains byte-identical here.
Whole-script native pinning remains a reviewed-integration guard, so the edited
Tet4D verifier needs guarded re-review before fresh fleet acceptance. Bootstrap
policy and default tool portability remain separate kit follow-up. No installer
application, release publication, evidence retagging or deferred-policy
activation is part of this bounded repair.
The refreshed guarded planner classifies 32 unchanged, 105 external/read-only
and 11 blocked locations. The evidence-only audit has 105 read-only and 43
incomplete locations with 46 failures and no accepted consumers. Tet4D's edited
native verifier is explicitly blocked by its reviewed-body drift guard. These
dated observations are not fleet acceptance; the private audit remains the
authority for later changing outcomes.
