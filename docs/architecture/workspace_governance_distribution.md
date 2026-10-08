# Workspace governance distribution

Status: local distribution implementation authorized by the workspace owner's
2026-10-04 all-repository rollout request. No remote/public publisher is selected.

## Decision and source identity

Retain the already canonical logical source `workspace/policy-kit`. Evolve it
into a versioned local distribution combining the workspace baseline, portable
workspace-governance machinery and two shared skills. Consumer authorities and
stronger local checks retain their owners. Tet4D's vendored runtime contributes
reviewed bytes; it does not become publisher authority.

Use the versioned distribution option in the canonical-upstream boundary.
The workspace owner controls release acceptance. Tooling prepares/validates the
export; mutable Git remotes and arbitrary local hashes do not confer authority.

## Immutable release contract

A release declares logical name/version, source provenance and a canonical JSON
manifest with SHA-256 identity. Every exported file has a source-relative path,
consumer-relative destination, mode and content hash. Retain complete exported
bytes and source commit/tree or uncommitted source bytes for reconstruction.
The manifest digest identifies the export. Do not rewrite an existing release
with different bytes; use a new identity/version. Consumer adoption records
bind this identity; runtime locks bind the declared pack file set. Installation
paths are machine details, not source authority. Validate bytes before writes.

Initial lines: distribution 1.2.x and portable runtime 0.5.x. Preserve legacy
1.1.x metadata/template interfaces until accepted per-consumer replacements.
A version label alone proves neither adopted bytes nor runner coverage.

## Runtime, skills and consumers

The pack declares its own Python floor. Machine selection belongs to permitted
local configuration. Python application/source certification applies only to
selected consumer profiles. Native/docs consumers need no fabricated Python
project metadata. Tool requirements and verification commands are bindings.

Universal manifests declare identity, authorities, routes/modes, verification,
sanitation and owners. Direct declarations coexist with legacy pointers.
No generated outputs is valid. Generic output checks delegate rendering to a
declared consumer command with bounded execution. Default `gov check` and
context resolution validate declarations without starting application renderers.
`gov check --generated` executes renderers in the selected consumer environment
and is mandatory in governed verification runners. Retain original obligations
and make no domain-semantic correctness claim.

Skills live once in the pack; Codex/Claude adapters resolve to that source and
are drift-checked. Skills guide selection/review while runners enforce checks.
Normative skills are treatment; validators/schemas are machinery. Classification
follows semantics and inherited policy, not directory placement.

## Adoption, evidence and rollback

Fleet tooling uses a private explicit registry. Plans retain exact preimages,
release identity and conflicts. Application is guarded/reversible; undo refuses
to overwrite subsequent changes. Keep dispatcher/verifier bodies with bounded
managed integration, stronger extensions and protected data intact.

Acceptance requires validated release bytes, real authorities, correct profile
checks, deliberate drift rejection, actual runner integration and declared
product evidence. Installation/structural success is separate from product
acceptance. Unavailable evidence does not pass. Archives/tool-managed stores
receive external governance instead of modified evidence/package internals.
The release-owned `policies/external_checkouts.md` defines this preservation
boundary; private records must pin its release and retain observed owners and
classification reasons. Read-only status does not certify installed files or
product/producer verification.

## Compatibility and review

Tet4D's six human owners, legacy machine families and routing facade retain
unmigrated scopes. Independent review and equivalent obligations precede family
handoffs. Deferred comparison/blocking logic and telemetry continuation retain
their evidence gates. Fleet audit reports missing coverage, orphaned checkouts
and failed checks with aggregate failure status.

## Accepted 1.3 contract: durable control and portable verification

The owner's logging/meta-testing repair authorization extends the distribution
with separately hashed runtime, verification and distribution-control components.
Only runtime payload files are installed into consumers. Verification tests,
fixtures, dependency ranges and the full gate remain kit-owned; selected module
origins and complete component bytes/modes are checked before execution. The
full kit gate defaults to the active immutable release. Editable candidates
require explicit selection. Context checks never start that suite.

Release identity depends on declared content, paths, modes, versions and
component contracts. Source commit and publication time are separate receipt
provenance. The public-safe editable kit has its own Git history; machine state,
raw outputs, keys and receipts stay excluded. Permanent private state and
verified backup copies replace session-local operational state. A persistent
writer lock, guarded activation journal and tested recovery protect the switch.
Owner-only copied permissions may tighten original modes, which remain recorded.
A backup on the same device does not cover device loss.

Execution uses approved absolute tools, a declared environment policy and bounded
process-group timeouts. Shell startup, foreign/repeated Makefiles, unsafe PATH
overrides and deterministic-Git escapes reject before dispatch. Unsupported
untracked child boundaries remain incomplete. A same-directory declared relative
CLAUDE-to-AGENTS alias is checked without following installer writes through it.

The v2 evidence envelope records completed run identity, selection, registry and
release identities, collector/execution-policy versions, actual argv, baseline
and product outcomes, stable inputs and timestamps. Matching passing records in
a finalized mixed-result batch may support only their stated scope. The trust
level is collector-reported execution: it does not authenticate execution against
a same-user actor able to rewrite the collector and evidence. Default audit is
structural/evidence-only; explicit baseline refresh and product collection remain
different actions. Existing holds, failed products and coverage gaps remain
nonzero. Mutable human authorities and backlog/current-state text are one-time
migration edits rather than permanently frozen installer postimages.

Global skill discovery points to immutable active release bodies. Repository
adapters declare the canonical name, relative link, body hash and fleet release
pin; ordinary context validation enforces the declaration. Generated checks share
execution only when their resolved command, cwd, interpreter, environment and
timeout agree. Every output remains guarded and validated. Native Tet4D gates
preserve named family coverage while executing each equivalent obligation once.
Tet4D dispatches ordinary named steps through its failure-log runner, retaining
checker diagnostics and exit codes. Matched-content sanitation and secret scans
retain bounded classifications in both logging modes. Repository discovery
adapters are Git-visible artifacts; private Claude workspace files stay ignored.

P1a logging gains read-only last-observed readiness and an explicit private
append/readback selftest. Probe observations are synthetic and never establish
product evidence. Recording failure preserves the observed command exit status.
No global automatic logging or deferred P1b/P1c/P6 continuation is activated.

The 1.3.1 publication patch keeps machine execution paths and values in the
private registry. Public fleet metadata carries the portable verifier declaration
and a versioned hash binding to that complete private policy. Execution uses
the original declaration; the hash preserves policy-drift detection. Project
tests are one-time owner migrations and never continuing installer postimages.
