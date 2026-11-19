# E4 assessment storage contract v1

Role: spec
Status: active
Source of truth: this file for E4 logical assessment records, write and reconstruction rules (synthetic implementation only; physical schema in `docs/architecture/participant_data_platform.md`)
Supersedes: none
Last updated: 2026-11-19
Derived from: [approved E3 record boundaries](assessment_measurement_contract.md) and
[participant-platform implementation plan](participant_data_platform_implementation.md)

## Scope and ownership

This contract specifies the first storage slice, from study assignment to
reconstructible assessment outcomes. E3 owns stimulus meaning, expected
answers and scientific analysis. The immutable item registry owns published
stimulus, presentation and scorer references. Ingestion owns identity,
referential integrity, duplicate detection and server receipt provenance.
Analysis consumes pseudonymous records and independently derives scores.
The observer uses completed semantic actions from the existing runtime.
Gameplay and topology ownership stay with their existing authorities.

The conformance format represents a logical record stream after authorization.
The [local PostgreSQL slice](e4_local_postgresql.md) implements assessment
tables and ingestion behind a verified-principal boundary. Client journaling,
identity-provider integration, personal cloud progress, trace-object storage
and retention operations belong to later stages. This draft authorizes synthetic data only.

## Record shape and purpose

Each record has an integer `version` (1), a `kind`, and kind-specific fields.
Opaque IDs are nonempty strings in the logical format. Published references
include a version in their identity. A protocol manifest defines valid arm,
sequence and visit codes and links form versions. A form manifest lists
ordered item versions. These manifests are immutable and loaded before
dependent records. The item registry resolves each item version to a frozen
stimulus and presentation reference, its full content digest, exposure-check
identity and supported scorer version. Production serialization and hashing
must follow the registry contract. The fixture uses opaque registry references.

| Kind | Fields beyond envelope | Purpose and constraints |
| --- | --- | --- |
| `assignment` | `enrollment`, `protocol`, `sequence` | One immutable pseudonymous enrollment plan. Baseline can be assigned before allocation. No account, authentication or contact records. |
| `allocation` | `enrollment`, `arm` | One immutable randomized arm, committed after the baseline closes. Retain the assigned arm even if actual practice differs. |
| `visit` | `id`, `enrollment`, `phase`, `form` | Assign a form independently of responses. The protocol and sequence must authorize the phase/form pair. A phase has at most one visit per enrollment in this slice. |
| `slot` | `id`, `visit`, `ordinal`, `item`, `scorer` | Assign each zero-based form position once. Item must match the manifest and scorer must match the item registry. |
| `exposure` | `enrollment`, `activity`, `active_ms`, `examples` | One coarse practice summary after allocation, including explicit zero exposure when known. Missing summary means unknown. Activity may differ from assigned arm. |
| `presentation` | `slot` | One client-reported presentation per slot, with its own observation time, window classification and server receipt time. Required before any `attempt` and before every outcome except `unpresented`; never allowed after an outcome. |
| `attempt` | `id`, `slot`, `response`, `latency_ms` | One immutable valid submission per slot. Response is exactly four signed 32-bit integer coordinates in X, Y, Z, W order. Latency is nonnegative elapsed monotonic time from usable stimulus to submission. |
| `outcome` | `slot`, `status`, `attempt` | One terminal outcome per slot. `submitted` must link to its own attempt. `invalid`, `interrupted`, and `unpresented` carry a null attempt. Only `unpresented` may lack a presentation, and an `unpresented` slot can never have one, so presented, submitted and unpresented classifications cannot disagree. |
| `close_visit` | `visit`, `status` | One terminal visit status: `completed`, `interrupted`, `expired` or `withdrawn`. Require a complete assigned-slot manifest and explicit outcomes. An expired visit has only unpresented slots. A completed visit allows submitted or invalid slots. An interrupted or withdrawn visit may include any supported slot outcome. `withdrawn` requires the enrollment's withdrawal record. |
| `withdrawal` | `enrollment` | One immutable withdrawal. It carries no account identity. It stops collection immediately and closes every open visit as `withdrawn`, so attrition can be reconstructed from study records alone. |

Unknown record fields, versions and kinds are rejected. Ordinals, durations
and example counts are nonnegative integers. Booleans are not integers.
The 32-bit coordinate range is a transport bound. Item publication verifies
that stimuli and correct answers fit the configured board bounds. A typed
but incorrect answer remains a valid submission for scoring.

## Write and reconstruction rules

1. Authorize each write for the pseudonymous enrollment before commit.
   All dependent records inherit enrollment through validated foreign keys.
   A batch may resolve its own dependencies in order. Persist an attempt
   and its submitted outcome atomically in production. The conformance
   stream exposes both records to test their relationship.
2. A record identity is kind plus primary key. The keys are enrollment
   for assignment, allocation and exposure, record ID for visit, slot
   and attempt, slot for outcome, and visit for close. Identical retries
   acknowledge without changing state, even after visit closure. Conflicting
   reuse rejects. Also enforce unique visit phase, slot ordinal and attempt
   per slot independently of identifier reuse.
3. Close only once all expected slots and their outcomes reconcile. A visit
   without a closure record stays unresolved. An absent visit assignment is
   an absent record, not proof that the participant skipped it. Record an
   expired visit and explicit unpresented slots when expiry is established.
4. Reconstruct eligibility for analysis from protocol and phase, counts of
   submitted, invalid, interrupted and unpresented slots, and immutable
   response and scorer references. Compute correct answers independently.
   Preserve raw counts across protocol versions. The proposed valid-answer
   threshold, timing windows and calibration targets are protocol parameters
   and are deliberately absent from storage validation.
5. Retain only typed responses and coarse exposure in this slice. Discard
   malformed payloads while preserving invalid status. Assign server receipt
   time at durable ingestion separately from monotonic response latency.
   Access policy, retention, deletion and any link to account identity
   require separate authorization and deployment evidence.

## Synthetic conformance

The `tests/unit/research/fixtures/e4_storage_v1.json` and
`tests/unit/research/test_e4_storage_contract.py`
exercise baseline-before-allocation, duplicate delivery, actual exposure,
responses and missing visits. The verifier checks logical record shape and
links. Authentication, durable transactions and deployment checks require
their own implementation evidence.

## Persistence and ingestion review

The fixtures cover a single enrollment with baseline, interrupted posttest,
and expired retention. They check key conflicts, form and scorer references,
terminal status, and response shape. The ledger accepts an attempt before its
outcome, so it cannot establish atomic persistence. It also treats any closed
baseline as sufficient for allocation, including an expired one. It has no
cases for authorization, simultaneous writers, device clocks, manifest
digests, a never-assigned visit, or an assigned visit that stays unresolved.
These are implementation acceptance gaps. The existing fixtures remain useful
as examples of logical records.

### Proposed defaults for implementation

1. **Typed storage and immutable references.** Start with a versioned
   migration against local PostgreSQL and synthetic data. Use UUIDs for
   enrollment, visit, slot and attempt identities, typed relational columns
   for the logical records, and immutable versioned manifests for protocol,
   form, item and scorer. Enforce unique enrollment/phase and visit/ordinal
   pairs, plus one attempt and one outcome per slot. Use a composite foreign
   key for the submitted outcome's slot and attempt ID. Keep study storage
   and account linkage separately permissioned. Retain stimulus, presentation
   and scorer provenance in the registry, and link visit execution to its
   client build provenance. Keep host selection and live retention policy
   in their separate decisions.

2. **Server-owned assignment and finalization.** A study service creates the
   baseline assignment and its full slot set atomically. It allocates once,
   after a completed baseline has passed the versioned protocol's eligibility
   check. The protocol can apply a data-completeness rule without embedding a
   numeric calibration threshold in the schema. At allocation, materialize
   planned follow-up visits and slots so missed visits remain enumerable.
   Store scheduled windows and their protocol version, server receipt times,
   and timing provenance separately from monotonic latency. Keep visit
   closure explicit. The server may expire a never-started visit after the
   versioned window and an explicit offline-reconciliation grace period.
   Once evidence shows any slot was presented, use interrupted closure for an
   abandoned visit. Late delivery during reconciliation preserves the
   observed outcome and records its timing classification. After closure,
   accept authorized exact replays and reject new outcomes. Treat arrival
   time alone as insufficient to infer presentation time or classify an
   assessment as late.

3. **Atomic write commands.** Expose a single-enrollment ingest endpoint
   with commands for valid submission, other slot outcome, and final
   exposure. Derive a submitted outcome from its validated attempt in the
   same transaction. Assignment, allocation, expiry and visit closure
   remain trusted operations. Start with one transaction per ordered batch,
   initially at most 64 commands and 64 KiB uncompressed, subject to
   measurement. A failing command rolls back new writes in that batch.
   Serialize assessment writers and finalization on the enrollment row
   in the first slice. Permission revocation must take that same lock,
   and writes must recheck authorization after acquiring it. Database
   constraints still enforce uniqueness and foreign keys. Return durable
   receipts only after commit. [PostgreSQL row locking](https://www.postgresql.org/docs/current/explicit-locking.html)

4. **Retry, versioning and authorization.** Compare a stable command ID
   and a server-computed SHA-256 digest of the validated versioned payload.
   Scope receipts to the enrollment and retain the original receipt on an
   authorized exact replay. Disallow duplicate JSON keys and define
   safe numeric ranges before canonicalization. Use RFC 8785 for digest
   bytes, with cross-client test vectors. Keep receipt timestamps and
   transport metadata outside the digest. Reject reused IDs with different
   payloads and conflicting logical keys. Return stable error codes for
   invalid payload, unsupported version, missing dependency, conflict,
   authorization failure and transient service error. Retry the same ID and
   payload after transient failures or lost acknowledgments. For a missing
   dependency, submit the prerequisite or reconcile first. Bind enrollment
   access to the authenticated caller and current study permission,
   including on receipt lookup. Deny direct client writes. Keep raw
   responses, invalid payloads and credentials out of error logs.
   [RFC 8785 canonical JSON](https://www.rfc-editor.org/rfc/rfc8785.html)

### Integration acceptance

Run synthetic database and service tests for rollback between attempt and
outcome, commit-before-ack replay, changed-payload conflicts, simultaneous
duplicate submissions, and submit-versus-close or submit-versus-withdraw
races. Test enrollment isolation, denied receipt lookup after withdrawal,
out-of-order delivery, expiry and reconciliation, and version/digest
interoperability. Reconstruct never-assigned, unresolved, expired, and
interrupted visits distinctly. Require a migration test against the
supported prior schema when one exists. These checks are required for
implementation evidence. The ledger tests continue to cover logical shape.

## Local implementation (review fixes, 2026-11-19)

The local slice implements these rules as PostgreSQL functions, specified in
the participant data platform architecture
(`docs/architecture/participant_data_platform.md`).
Review fixes changed four details of the defaults above:

- The account link lives in a private schema that study readers cannot
  reach. Study records carry no principal.
- Interrupted closure waits for the offline grace period unless every slot
  already has an outcome. New outcomes after closure return `visit_closed`,
  distinct from `conflict`.
- Expiry is allowed while no slot has been presented, even if the visit
  started. A presented slot makes `interrupted` the only abandonment closure.
- Client observation times use one canonical form,
  `YYYY-MM-DDTHH:MM:SS.sssZ`, so equal instants produce equal digests.
  Exposure activities are protocol data, not a fixed list.
- Presentation is a client event with its own time provenance, delivered
  through the same idempotent ingest path as answers. A foreign key ties
  every non-`unpresented` outcome to its slot's presentation record.
- Every read of the account link is audited (`read_allow`, `read_deny`),
  as are grants, revocations and rejected conflicting commands. Audit rows
  survive a rejected batch.

## Before real enrollment: assignment integrity

The local slice accepts the arm and the eligibility decision from a trusted
caller (`allocate(enrollment, arm, eligible, windows)`). That is acceptable for
synthetic data only. A caller-supplied `eligible = true` is not a research
eligibility authority, and a caller-chosen arm is not concealed randomization.
Before any real enrollment, the trusted study service must:

1. **Compute eligibility server-side** from the stored, completed baseline
   records under the frozen protocol version's rule (for example the E3
   valid-response threshold), and record the rule version and inputs with the
   decision. No caller argument may override it.
2. **Draw the arm from a concealed allocation sequence** generated before
   enrollment opens: variable block sizes, balanced within form sequence as E3
   requires, stored where neither callers nor study readers can see unused
   entries, and consumed strictly in order. The arm is revealed only by
   committing the allocation.
3. **Audit every assignment**: sequence position, protocol version,
   eligibility inputs and decision, and time, in a record study readers can
   verify without seeing future allocations.
4. **Prove it with tests**: callers cannot choose or preview an arm,
   ineligible baselines cannot be allocated, concurrent allocations cannot
   consume the same position, and the realised allocation matches the
   sequence.

Until those exist, this slice must not be used for real participants. Hosting,
authentication provider and deployment decisions remain separate.
