# Participant Data Platform Architecture

Status: local synthetic slice (E4 assessment storage). No real-person collection.

## Purpose and source of truth

This document records how the participant data platform is built, as
`docs/plans/participant_data_platform_implementation.md` requires. The first
implemented slice is E4 assessment storage. Its logical rules are owned by
`docs/plans/e4_assessment_storage_contract.md`; measurement and scoring are
owned by `docs/plans/assessment_measurement_contract.md` (E3).

The source of truth for behaviour is `migration/participant_data/001_assessment.sql`.
All write logic lives there as PL/pgSQL functions, so it moves unchanged to any
PostgreSQL host, including the leading Supabase candidate. The future Edge
Function, like today's test harness, is a thin adapter. Gameplay, topology,
the native core and the Python oracle are not involved.

## Schemas and roles

| Schema | Holds | Who can reach it |
| --- | --- | --- |
| `assessment` | Study records: manifests, enrollment, allocation, visits, slots, attempts, outcomes, closures, exposure, receipts, withdrawal. No principal or account identifier. | `research_reader`: SELECT only |
| `assessment_private` | `enrollment_access` (enrollment to principal link), `access_audit` (grant and revoke events), private helper functions | `assessment_owner` and its definer functions only |
| `assessment_api` | The seven entry points below | `assessment_ingest`, `assessment_operator`: EXECUTE as granted |

`assessment_owner` is a NOLOGIN, non-superuser role that owns every object.
The entry points are `SECURITY DEFINER` with `search_path` pinned to
`pg_catalog` and schema-qualified references. Callers hold EXECUTE and never
table privileges, so the functions are the only write path.

| Entry point | Granted to | Lock and access check |
| --- | --- | --- |
| `ingest(principal, enrollment, commands jsonb, digests bytea[])` | `assessment_ingest` | Enrollment row lock; caller's live access and no withdrawal |
| `assign_baseline(enrollment, principal, protocol, sequence, opens, closes)` | `assessment_operator` | Creates the enrollment, the private access link and the baseline visit with its full slot set |
| `allocate(enrollment, arm, eligible, windows jsonb)` | `assessment_operator` | Lock; collection open; completed baseline; materializes every follow-up visit and slot |
| `start_visit(enrollment, visit, client_build)` | `assessment_operator` | Lock; collection open |
| `mark_slot_presented(enrollment, slot)` | `assessment_operator` | Lock; collection open; slot has no outcome yet |
| `close_visit(enrollment, visit, status)` | `assessment_operator` | Lock; enrollment exists (bookkeeping, allowed after withdrawal) |
| `withdraw(enrollment)` | `assessment_operator` | Lock; idempotent |

Every entry point takes the enrollment row lock first, so writes,
finalization and withdrawal are serialized for each enrollment. A raised
error aborts the whole statement, which makes each ingest batch atomic.

## Edge adapter responsibilities

`jsonb` keeps only the last of duplicate keys, and PostgreSQL has no RFC 8785
serializer. The adapter therefore:

1. reads at most 64 KiB, rejects duplicate keys and unknown fields, and checks
   the batch version and shape (at most 64 commands);
2. computes each command's digest as SHA-256 over RFC 8785
   `{"version": 1, "command": <command>}`;
3. supplies the principal only from verified authentication middleware;
4. commits, then returns receipts.

The SQL functions still re-check every type and range they rely on, so a
faulty adapter cannot store malformed records.

## Wire rules

- Command IDs, slots and attempts are lowercase canonical UUID strings.
- `observed_at` is JSON null or exactly `YYYY-MM-DDTHH:MM:SS.sssZ`. One form
  means one digest for each instant.
- Responses are four signed 32-bit integers; latency, durations and counts are
  non-negative 32-bit integers.
- Exposure activities must be listed for the protocol in
  `assessment.protocol_activity`.

## Visit lifecycle

| Closure | Allowed when | Unresolved slots become |
| --- | --- | --- |
| `completed` | Visit started; every slot submitted or invalid | (none remain) |
| `expired` | No slot presented, no answered outcome, and window plus offline grace has passed | `unpresented` |
| `interrupted` | Visit started, and either every slot has an outcome or the grace period has passed | `interrupted` if presented, else `unpresented` |
| `withdrawn` | Only through `withdraw`, which closes every open visit at once | `interrupted` if presented, else `unpresented` |

Until the grace period ends, an interrupted closure returns
`reconciliation_pending` so queued offline outcomes can still arrive. They keep
their client timing classification (`before_window`, `in_window`,
`after_window`), separate from the server receipt time.

## Error contract

Functions raise SQLSTATE class `T4`, which PostgreSQL does not use. The
message text is the stable code. The adapter maps unknown connection,
serialization or resource failures to `transient_service_error`.

| SQLSTATE | Code | HTTP | Client action |
| --- | --- | --- | --- |
| `T4001` | `invalid_payload` | 400 | Fix the client; drop the command |
| `T4002` | `unsupported_version` | 400 | Upgrade the client |
| `T4003` | `authorization_failure` | 403 | Stop uploading for this enrollment |
| `T4004` | `missing_dependency` | 422 | Send the prerequisite, then retry |
| `T4005` | `conflict` | 409 | Keep the record locally, flag it, do not retry |
| `T4006` | `visit_closed` | 409 | Keep the record locally, flag it, do not retry |
| `T4007` | `reconciliation_pending` | operator | Retry the closure after the grace period |
| `T4008` | `ineligible_baseline` | operator | Allocation refused |
| `T4009` | `incomplete_visit` | operator | Completed closure refused |
| `T4010` | `invalid_expiry` | operator | Expiry refused |
| `T4011` | `invalid_status` | operator | Unknown or reserved closure status |
| `T4012` | `invalid_manifest` | operator | Form ordinals are not contiguous from zero |
| `T4013` | `invalid_windows` | operator | Follow-up windows missing or malformed |
| `T4014` | `visit_not_started` | operator | Interrupted closure of a never-started visit |
| — | `transient_service_error` | 503 | Retry the same ID and payload |

## Verification

`tests/integration/test_e4_postgresql.py` runs against an empty, disposable
database named by `TET4D_E4_TEST_DSN`, connecting as the caller roles rather
than the owner. `tests/integration/e4_harness/` is the test-only adapter.
Setup is described in `docs/plans/e4_local_postgresql.md`.
