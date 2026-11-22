# E4 client journal and offline sync defaults

Role: implementation proposal
Status: approved defaults, synthetic slice implemented
Last updated: 2026-11-20
Sources: [E4 storage contract](e4_assessment_storage_contract.md),
[participant platform plan](participant_data_platform_implementation.md),
[merged PostgreSQL slice #194](https://github.com/mousomer/tet4d/pull/194),
[merged audit requirements in #195](https://github.com/mousomer/tet4d/pull/195),
and [retention clarification in #196](https://github.com/mousomer/tet4d/pull/196)

## Review of the server boundary

#194 tests the actual PostgreSQL functions through restricted roles. It
covers atomic rollback, replay after closure, denied replay after withdrawal,
concurrent submit versus close or withdrawal, and presentation before answer.
Its test adapter commits the result before returning a receipt or a rejection.
The client can rely on an authorized exact replay after a lost acknowledgment.
These tests do not exercise client persistence or scheduling.

Two boundaries need explicit treatment before client rollout:

- Trusted `start_visit` returns a generic conflict when a visit is already
  started. Its response can be lost after commit. The synthetic client should
  start with a server-confirmed, started visit and cached immutable slot
  manifest. An authenticated, repeatable start or read-back operation is needed
  before handling real start requests. Verify that a retry with the same build
  returns existing state and a different build cannot rebind the visit.
- A rejected atomic batch returns a code without a failing command ID or
  prerequisite identifier. `missing_dependency` can mean a missing presentation,
  visit start, or allocation. Keep the batch durable. Use known local causal
  dependencies and a trusted state refresh. When neither identifies the
  prerequisite, block the enrollment queue for reconciliation. Avoid automatic
  binary splitting or speculative replays to discover which command failed.
  Consider a bounded error detail or authenticated state read in the production
  adapter only if client tests show the current contract is insufficient.

## Proposed defaults

### 1. Journal ownership, durability and capacity

- Use versioned, bounded record segments under `user://participant_data/`,
  following the existing plan. One background writer owns each journal. Give
  every command a local sequence number, canonical command UUID and exact
  versioned payload plus checksum. Persist the enrollment and local account
  binding when recording. The account binding stays local and is never a
  credential or an ingest field. Keep guest and different-account partitions
  separate. Exclude these files from telemetry, support logs and automatic
  cloud backup where the platform permits.
- Freeze payload bytes before the first send, including nullable canonical UTC
  observation and elapsed monotonic latency. Generate a submit's attempt ID
  once. Persist the presentation boundary before accepting a response and the
  response before showing it as saved. Let the UI wait asynchronously at these
  boundaries. Test actual crash durability on each supported filesystem.
  Use durable flush and atomic replacement where supported. Keep SQLite as a
  fallback candidate if packaged platforms cannot meet that file contract.
  [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html)
- On restart, recover valid committed records and the last durable receipt
  checkpoint. Isolate unreadable segments and preserve the fault state without
  advancing across an unknown sequence gap. Reclaim acknowledged segments
  only after persisting the receipt checkpoint. Migrations must preserve the
  bytes and identity of already queued commands. Start with a provisional
  1 MiB warning and 4 MiB hard cap per active assessment enrollment, with a
  separate total cap per installation before release. At the cap, stop
  accepting new assessment records and show the failure. Existing pending
  records remain available to sync, and ordinary play stays available.

### 2. Admission and causal delivery

- An initial synthetic slice may finish a previously started, cached visit
  offline. Starting or allocating a new research visit requires confirmation
  from the trusted service. A missing, expired or stale manifest must not
  create a local substitute assignment. After a crash keep already saved
  responses and presentation evidence. Resolve a presented, unanswered slot
  through the interruption policy before proceeding.
- Use one in-flight batch per enrollment, from the oldest ready contiguous
  prefix. Send `present` before `submit` or `invalid`/`interrupted` for the same
  slot, ordinarily in the same batch. Send `unpresented` only if no presentation
  occurred. Final exposure depends on allocation. Delay operator closure until
  durable client receipts reconcile or the server's protocol grace permits
  adjudication. The device may display the grace deadline but cannot extend it.
- On HTTP success, require exactly one receipt for each submitted command ID,
  with a matching RFC 8785 SHA-256 digest and valid receipt timestamp. Compare
  IDs as a set and reject duplicates, missing or extra receipts. Record the
  verified batch atomically with the local acknowledgment checkpoint. An
  incomplete or mismatched success leaves the batch in reconciliation. A
  timeout after commit can replay the same command IDs and payloads safely.

### 3. Flush, backoff and audit capacity

- Flush one nonempty batch per wake-up, up to 64 commands and 64 KiB on the
  actual UTF-8 request body. Default to a 30-second coalescing window, with
  early flush on visit completion, reconnect with a backlog, or reaching a
  batch limit. Coalesce simultaneous triggers. Drain further batches through
  the rate gate with a provisional five-second minimum between starts per
  enrollment. Closing the app never depends on a successful final flush.
- Retry network failures and 503 with the same ordered payload, starting at
  five seconds with jitter and doubling up to a five-minute ceiling. Respect
  a longer `Retry-After` for throttling or service errors. Allow three
  automatic retries after the first request, then pause for a meaningful
  connectivity or service recovery signal, authorized manual retry, or a
  reviewed recovery action. Persist cooldowns and retry state across process
  restarts. Prevent repeated reconnects, resume events or button presses
  from bypassing the gate. There are no empty ingest probes.
- Propose an adapter limiter before PostgreSQL, keyed by authenticated
  principal and enrollment independently. Start capacity testing at 12
  calls/minute per enrollment and 24 calls/minute per principal, with
  `429` and `Retry-After`; tune using reconnect and audit measurements.
  Keep one audit event per authorized or denied database access as #195
  requires. Measure calls, attempts per command, stop reasons, and oldest
  queue age without recording payloads, tokens or principal identifiers in
  client telemetry. One clean 24-command visit fits in one request when
  flushed together. Measure real cadence rather than assuming one audit
  row per visit. Feed the observed distribution into #195's capacity alert.
  Production audit retention and pruning follow the approved schedule,
  with no proposed retention period here.

### 4. Reconciliation and visible status

| Event | Default client action |
| --- | --- |
| 401 | Wait for verification of the same signed-in account. Resume only that account's queue. |
| 403 / authorization failure | Stop uploads for the enrollment immediately, including receipt retries. Quarantine pending study records and apply the approved disposition once the service confirms what happened. A generic denial cannot prove withdrawal. |
| Confirmed withdrawal | Stop study capture and sync. Disposition of pending records follows the approved study policy. Ordinary player progress is independent. |
| Sign-out or account change | Stop sending and fence in-flight callbacks by account generation. Keep old commands in their original partition. Reconcile any uncertain send by exact replay after the same account returns and access is verified. |
| Missing dependency | Supply the known prerequisite in causal order, or reconcile via trusted service state. Leave all affected commands pending until receipts verify. |
| Conflict, visit closed, invalid command, unsupported version, or malformed success | Block the affected queue with a reason. Preserve records for explicit reconciliation. Keep compatible old queued wire versions, and avoid regenerating IDs or editing a command already sent. |

Expose local-only, pending, synced, paused, and blocked states without
showing an unverified delivery as synced. Display whether a pause needs
connectivity, sign-in, or operator reconciliation.

## Implementation acceptance

Prove journal recovery at every boundary from capture through durable
acknowledgment, including force kill, interrupted compaction, disk full,
malformed tail, and reopening an older journal. Run a fake-clock transport
suite for causal batching, byte limits, mismatched receipts, lost responses,
rate limits, rebooted retry timers, account switch and withdrawal. Exercise
the same workflow against PostgreSQL and assert one audit read per actual
ingest call, no calls after a denial, and correct outcomes when offline work
arrives on either side of grace. Require named-platform restart evidence
before release. Keep E3 calibration thresholds and server scheduling in the
versioned protocol.

## Synthetic implementation

The reference client runs in `tests/integration/e4_harness/`. The caller
supplies a previously confirmed manifest, verified local account binding,
transport and epoch-millisecond clock. Its serialized worker API uses one
file segment per command and a versioned atomic checkpoint. POSIX file and
directory flushes are exercised on the test host. Godot integration,
asynchronous platform workers, named-platform durability, a production
rate limiter and approved local deletion remain follow-up work. The
harness supports no real identities or network probing. Journal tests use
synthetic replies, and the PostgreSQL tests drive the same implementation
through the ingestion adapter to count actual audit reads.

Run with the optional local E4 dependencies from
`migration/participant_data/requirements.txt` and the PostgreSQL setup in
[e4_local_postgresql.md](e4_local_postgresql.md). Include
`tests/integration/test_e4_client_sync.py` and
`tests/integration/test_e4_postgresql.py` in the focused run.
