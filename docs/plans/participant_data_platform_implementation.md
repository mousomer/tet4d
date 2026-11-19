# Participant Data Platform — Full Implementation Plan

Role: spec
Status: active
Source of truth: this file for **proposed participant-platform implementation sequencing and acceptance**, not for scientific endpoints, existing gameplay authority, or approval to collect people’s data
Supersedes: none
Last updated: 2026-11-18
Programme authority: `professional_godot_game_programme.md`
Scientific authority: `spatial_intuition_research_plan.md`
Open work: `docs/BACKLOG.md`
Plain-language explanation: `participant_data_platform_overview.md`

## 0. Status, decision boundary, and non-goals

**Documentation and design only.** No production service, account enrollment, data collection, research protocol, approved legal basis, or semantic authority transfer is claimed. Each implementation PR requires its own contract review and evidence.

Target: optional personal cloud saves, meaningful compact session records, versioned assessment results, and opt-in reproducible research traces for Tet4D's 2D/3D/4D Play and Explorer.

Candidate choices for first implementation. Provider and stack are selected only by a separate design decision after the E3-derived storage contract is approved (`spatial_intuition_research_plan.md` E4); this table records the leading candidates, not that decision:

| Concern | V1 proposal |
| --- | --- |
| Managed host | Supabase project in Ireland (`eu-west-1`) — leading candidate, subject to the provider design decision and procurement/privacy approval |
| Relational records | PostgreSQL |
| Accounts | Supabase Auth; email OTP initially |
| API | Authenticated Supabase Edge Functions; TypeScript, modular handlers |
| Client | Godot 4, explicit HTTPS adapter and local journal; no engine rule changes |
| Detailed traces | Private Supabase object storage, content-addressed manifests |
| Analyses | Versioned, reproducible Python analysis and export; not a continuously running service |
| Environments | Local CLI stack, separate staging, production |
| Early research cohort | Adults only, after review |
| Initial recording defaults | Guest local-only (L0); registered player compact summary (L1), plus individual attempts (L2) only for assessments they choose to take; research traces (L3) only when separately authorized |

Alternatives deferred: custom VPS/FastAPI, streaming infrastructure, new player-ranking system, automatic adaptive teaching, online replication of the native game engine, a bespoke identity provider, and global recording of raw controller inputs. Revisit providers only with measured operational or compliance evidence; PostgreSQL/schema/exports must remain portable.

No changes to platform-support matrices, existing gameplay rules, native/topology authority, Python oracle, approved cockpit geometry, deterministic seeds or gameplay/replay hashes are authorized by this plan. The newer forward Explorer topology RDS remains independent; its unusual cellwise geometry must not be relabeled as a player error.

## 1. Ownership and contracts

1. `docs/plans/professional_godot_game_programme.md` owns priority and programme completion gates.
2. `docs/plans/spatial_intuition_research_plan.md` owns the proposed research hypotheses, measures, controlled comparison, transfer/retention analysis and participant obligations.
3. The first implementation PR creates `docs/rds/RDS_PARTICIPANT_DATA_PLATFORM.md` to own durable player-facing account, persistence, collection-level, synchronization and privacy behavior.
4. The assessment PR creates `docs/rds/RDS_SPATIAL_ABILITY_ASSESSMENT.md` to own user-visible task/scoring behavior. It must not assert a validated general-4D-ability scale.
5. Architecture, module boundaries and server protocol are specified under `docs/architecture/participant_data_platform.md` as they are implemented.
6. `docs/architecture/authority_map.md` must identify the new observer/client, ingestion and scoring ownership as **new domains**, not secretly transfer gameplay semantics.
7. `docs/BACKLOG.md` owns implementation status; history/PRs own completion evidence. This plan is not a running work log.
8. Existing `docs/rds/RDS_SCORE_ANALYZER.md` is Python gameplay-quality telemetry, not a ready participant backend or scientific ability measure.

**Boundary:** Native/gameplay modules produce authoritative outcomes. Godot's presentation/input owners provide view and command context. A detached collection adapter consumes these *after* the action. It cannot calculate legality, modify game state, create a second replay engine, block the input/render thread on I/O, or change player actions.

## 2. User journeys

### 2.1 Guest

- Can play/Explore without account or network.
- Local settings and gameplay remain unchanged.
- Proposed new progress summaries stay local (level L0).
- No research telemetry upload and no hidden anonymous cloud identity.
- Later account creation offers an **explicit** import of eligible local summaries with visible confirmation; no silent attribution of earlier anonymous research data.

### 2.2 Registered player

- Can sign in using an email one-time code, sign out, recover access and request export/deletion.
- Cloud progress (L1) is enabled only after clear disclosure.
- Saves personal activity/session summaries and eligible self-assessment attempts (L2) with transparent recording purpose.
- Can use another installation; server ownership is linked to verified auth subject, not client-supplied email.
- A record already uploaded under one account cannot be silently re-owned by another.

### 2.3 Research participant

- Joins a named approved study with a frozen protocol version and study-specific recording policy.
- Has a random `participant_id` held separately from `auth.users.id`.
- Has versioned information/permission records (or other justified legal-basis and ethical authorization).
- Research L3 traces are permitted only for an actively authorized study session.
- Can withdraw or request deletion under documented handling; the server stops new study collection immediately, including during offline-recovery reconciliation.
- Initial live pilot is adult-only; do not infer that login establishes eligibility, consent or research ethics clearance.

## 3. Measurement design before telemetry design

Precede a production event schema with the smallest versioned assessment contract. Item, form and scoring design is owned by research-plan E3 / backlog P3; the table below is illustrative input to that work, and this plan's PR 1 and PR 5 implement the result rather than define it:

| Domain | Example item | Primary observation |
| --- | --- | --- |
| Rotation | Predict resulting orientation after XW or YZ turn | Exact correctness/error class |
| Adjacency | Identify a 4D cell's neighbors | Correct neighbor set |
| Projection | Match structure under a new view | Correct choice |
| Coordinates | Predict coordinates after a transform | Exact/graded error |
| Navigation | Reach target via valid transformations | Success, relative effort |
| Transfer | Solve held-out novel tasks | Accuracy on unfamiliar calibrated forms |

Assessment item definition includes `item_id`, `item_version`, task family/domain, content digest, deterministic seed and generator version or frozen concrete stimulus, scoring rubric/version, allowed hints/controls, and applicable projection/basis state.

Required protocol decisions before collecting people: population/exclusions, comparison group or active control, assignment strategy and counterbalancing, pre/post/held-out/retention scheduling, primary endpoint, secondary endpoints, effect/uncertainty analysis, missing-data and attrition handling, exclusion criteria. Pilot calibration precedes protocol freeze. The experimental hypothesis can fail without being a platform failure.

Do not report an unvalidated scalar "4D intelligence" score. V1 exposes separately named accuracy, valid attempt counts, time distributions, baseline differences and uncertainty **only across comparable assessment forms**. Derived ability tables are recomputable from immutable attempts, scoring version, input IDs and code release. Future IRT or hierarchical modeling requires demonstrated item calibration and identifiability.

## 4. Collection policy and data budget

| Level | Collection | Intended case |
| --- | --- | --- |
| L0 | Local-only player summary; no upload | Guest |
| L1 | Small session summary (aggregate action/error counts, score, duration, setup) | Authenticated player |
| L2 | L1 plus individual versioned assessment attempts | Personal assessments; research use separately authorized |
| L3 | L2 plus semantic action sequence in compressed segments | Explicit study-specific recording |

A session begins when a Play, Explorer or Assessment activity starts; an application launch may contain several sessions. New Play/Explorer setup or restart creates a new session or linked attempt, not an undocumented rewind. A session records interrupted/complete/recovered status; crashes never become fabricated successful endings.

Recording mode is frozen for each session. A mode/permission change starts a new recording boundary. Research permission is checked at capture **and** at ingestion; withdrawal or lost authorization prevents future uploads even if local records remain queued. Define deletion/discard of now-ineligible queued research records.

**Record post-action semantic results**, not raw input repeat, polling or render frames. Classification: `session_start`/`session_end`, task/stimulus/answer/hint, object translation/rotation/rejection, view-basis turn, slice change, camera gesture boundary/final pose, reset/retry and relevant gameplay score/lock transitions. Reuse semantic action identifiers from the established input contract. For high-frequency camera drag, record bounded start/end summary with final presentation pose and duration rather than per-frame samples; if scientific reconstruction needs intermediate views, define explicit sampling in the approved task protocol, not global collection.

Suggested initial engineering targets, to be benchmarked rather than claimed as measured: L1 summary <=10 KiB, L2 session <=100 KiB, L3 trace soft target <=250 KiB per 30 minutes compressed, trace segment <=64 KiB compressed, max batch 256 semantic actions, normal network flush every 15–30 s. Transport and queue limits must be defined from measured build behavior. **Never silently truncate research evidence:** split segments, mark incomplete on unsustainable volume and alert. Routine mode must have bounded queues and storage pressure UI/recovery.

Capacity model: 1,000 sessions/day × 10 KiB ≈290 MiB summaries/month; if 10% produce 250 KiB traces, ≈730 MiB trace content/month. These are logical new bytes, excluding indexes, backups, auth, egress, and retention accumulation.

## 5. Identity, tables, and integrity

Use UUIDs, foreign keys, timestamps, schema/version fields, row-level security and migrations. Do not use GitHub as the data store.

**Important:** an ordinary player is not necessarily a research participant. Sessions are owned by `auth.users.id`; a research enrollment/participant reference is optional and never used as a public account identifier.

Target logical tables (create by stage, not all in PR 1):

| Table | Minimum columns / invariant |
| --- | --- |
| `public.player_profiles` | `user_id` FK to `auth.users` PK, created/updated; no custom password |
| `public.sessions` | `session_id` UUID PK, `user_id` FK, mode/activity, start/end, status, recording level, build/collector/config versions, validated setup JSON |
| `public.session_summaries` | (`session_id` FK, `revision`) PK, aggregate JSONB, content digest, received_at; every received revision is kept and none is overwritten |
| `public.session_summary_heads` | `session_id` PK FK, current `revision` FK, sealed flag; the only row that changes when a newer revision is accepted |
| `public.assessment_attempts` | immutable `attempt_id` UUID PK, session FK, `item_id`+`version`, stimulus digest, response, outcome, timing, scoring version |
| `public.assessment_items` | unique `item_id`+`version`, task/domain, frozen stimulus reference or generator/seed, rubric/digest |
| `public.ability_estimates` | player FK, domain, model version, input-set digest, estimate/uncertainty, computed_at |
| `research.studies` | study ID, approved protocol version/status, task-set refs |
| `research.participants` | random participant ID; no account identifier |
| `research_private.account_links` | participant ID ↔ `auth.users.id`; reachable only by the service role, every read logged in `research.access_audit`; never joined in researcher queries or exports |
| `research.enrollments` | participant, study, condition, eligibility, status, approval provenance |
| `research.permission_records` | purpose, notice/protocol version, decision/legal-basis record, effective_at, withdrawal |
| `research.trace_manifests` | session FK, enrollment, contiguous sequence range, hash, size, object path, verification state |
| `research.access_audit` | researcher/admin action, record scope and time, no secrets |

**Indexes:** sessions on (`user_id`, `started_at`); attempts on (`session_id`, `item_id`); ability history on (`user_id`, `domain`, `computed_at`); research manifests on (`session_id`, `first_seq`). Add query indexes only with measured evidence. Direct client writes to protected research/attempt records must be denied.

**Idempotency:** `session_id` identifies a session; `attempt_id` an immutable answer; summary pair (`session_id`, `revision`) identifies a revision; trace segment is (`session_id`, `first_seq`, `last_seq`, content hash). Identical replays acknowledge; same identity with different payload rejects and audits; overlapping conflicting trace ranges reject. Old received revisions stay in `session_summaries`; accepting a newer revision only moves the pointer in `session_summary_heads`, and a revision lower than the current head is rejected. Once a head is sealed, no further revision is accepted.

Versioned session envelope MUST contain: activity/dimension, canonical board extents, topology space/construction/profile IDs (where applicable), build/commit + gameplay contract, collector + input-control version, seed, camera/basis/slice/presentation state needed for assessment, recording level, task/study ID when applicable, client monotonic timing and UTC timestamp provenance. The server assigns its own receipt times. Never infer topology IDs from display labels; camera is not a native gameplay hash.

## 6. Client implementation

Proposed new folder: `godot/Tet4D.Godot/scripts/participant_data/`. Make small, single-owner modules:

- `participant_identity.gd` — local guest ID, sign-in state and restricted account binding.
- `session_coordinator.gd` — session IDs and state machine (`created` → `active` → `interrupted|closed` → `synced`).
- `recording_policy.gd` — L0–L3 permissions, sampling rules, collector versions, volume budgets.
- `event_collector.gd` — immutable semantic result input; non-blocking enqueue.
- `session_aggregator.gd` — counts, active/idle duration, outcome rollup.
- `assessment_recorder.gd` — frozen item identity, response, hint and timing; **not** its own scoring oracle.
- `local_journal.gd` — durable pending records and acknowledgment tracking.
- `api_transport.gd` — HTTP requests, schema/wire serialization and error decoding only.
- `sync_coordinator.gd` — bounded batches, retries with jitter, dedupe, network recovery.
- `progress_repository.gd` — load local/cloud history with explicit sync state.

Integration ownership to inspect before coding:
`scripts/app/trace_replay_app.gd` (session routing; must remain thin);
`scripts/input/live_input_contract.gd` (semantic commands);
`scripts/ui/practice_explorer_panel.gd` (Explorer intent and results);
`scripts/native/tet4d_core_bridge.gd` (observe authoritative outcomes, never patch semantics);
`scripts/persistence/persistent_file_replacement.gd` (existing atomic-file pattern);
`scripts/ui/settings/settings_store.gd` (existing settings separation).

Do not add HTTP, scoring, or filesystem writes directly to the large app controller. Provide narrow signals/callbacks at existing authoritative post-action seams. New UI should reuse cockpit style/navigation, not invent a separate menu framework.

Use `user://participant_data/` with versioned record files and checksums. Design atomic append/segment replacement, crash-tail recovery, bounded memory, journal compaction after verified ACK, migration of old local schema, protection against duplicate session imports, and disk-full behavior. Confirm durability guarantees on actual builds for each release platform, in the programme's order (currently Windows → Linux → Android tablets; macOS once its packaging is scheduled). Android needs its own evidence: the OS may stop the app at any moment without a clean shutdown, so recovery must never depend on an orderly exit. Godot file closure alone must not be claimed as crash-proof without tests.

**Authentication token safety:** do not put privileged keys in clients. The public Supabase project URL and publishable key are not service credentials, but tokens still require protection. Persist a long-lived refresh token only if the target platform has an approved secure-storage adapter (OS credential store on desktop; an Android Keystore-backed adapter, which Godot does not provide natively and needs a plugin); otherwise require login again across launches. Server never trusts a local flag for identity or study authorization.

## 7. Hosted API and authorization

One authenticated Edge Function, `participant-api`, with modular handlers. Version all request/response schemas. Example logical routes (HTTP routing implemented inside the function):

| Method | Path | Contract |
| --- | --- | --- |
| POST | `/v1/sessions` | Create/bind session to verified owner; idempotent |
| PUT | `/v1/sessions/{id}/summaries/{revision}` | Digest-checked aggregate revision |
| POST | `/v1/sessions/{id}/attempts` | Immutable, idempotent batch of attempts |
| POST | `/v1/sessions/{id}/trace-segments/init` | Authorize L3, allocate short-lived private upload |
| POST | `/v1/sessions/{id}/trace-segments/finalize` | Verify checksum/size/order, commit manifest |
| POST | `/v1/sessions/{id}/close` | Seal session, completeness status |
| GET | `/v1/me/progress` | Paginated own history/derived measures |
| POST | `/v1/studies/{id}/enroll` | Controlled participant enrollment; no client-selected condition |
| POST | `/v1/studies/{id}/withdraw` | Record withdrawal as a new `research.permission_records` row, effective before the next upload check; idempotent; response states the retention rule that applies to already-received data. Withdrawal is not deletion |
| POST | `/v1/me/export-requests` | Personal export job with authenticated delivery |
| POST | `/v1/me/deletion-requests` | Account/research deletion request workflow |

For server handlers:
- Authenticate each request using the supported Supabase user JWT verification pattern; derive account from verified claims. Reject missing/expired tokens and cross-user IDs.
- Require active, purpose-appropriate research authorization for every L3 initiation and finalization. Never let a client choose its own study condition.
- Validate bounded request sizes, enums, lengths, schemas, chronology, item references, digests, session ownership and allowed recording levels. Preserve exact canonical values, not arbitrary coercion.
- Use database transactions/constraints for idempotent inserts and conflict responses; document retryable vs permanent errors.
- Apply per-user/session rate controls and operation quotas; prevent replay/flooding abuse.
- Direct account read access is constrained by reviewed RLS. Protected research tables and object paths are inaccessible to public clients; administrative routes perform explicit ownership checks before using elevated privileges.
- Stage uncommitted object uploads and clean orphans; object-store upload and relational manifest insert are not one atomic transaction.

Session creation/closure and attempts are server-authoritative receipts of client observations, **not** proof that the client could not be modified. Record client build/integrity hints but treat untrusted clients as untrusted. The experimental protocol must define anti-cheat/exclusion policy separately.

## 8. Synchronization algorithm and failure behavior

1. Generate stable UUID locally; write session envelope before recording associated events.
2. Write records to durable local journal, append sequence and checksum.
3. Aggregate L1 locally, keep assessment attempts individually, build L3 trace segments.
4. Once signed in and authorized, send compact batches asynchronously; no synchronous network work in gameplay.
5. Server validates owner/schema/permission; performs idempotent transaction and responds with per-record ACK and server receipt.
6. Client verifies ACK identity/hash, records acknowledgment durably, then reclaims sent journal segments.
7. Retry transient errors with bounded exponential backoff+jitter and connectivity recovery; surface persistent failures.
8. On restart, recover journal and retry exactly the same IDs/content. A crash between server commit and local ACK is expected and must not duplicate data.
9. Out-of-order arrival may be buffered/manifested, but finalized research traces must have verified contiguous sequence coverage or an explicit incomplete status.
10. Every journal record carries the account (or guest) it belongs to, fixed when it is written. Records are uploaded only while that same account is signed in and never under another account.
11. On sign-out, stop uploading and keep the account's queued records; resume when the same account signs in again. Discard queued L0–L2 records only when the player explicitly chooses to.
12. On withdrawal or lost research authorization, stop L3 uploads immediately and apply the study's discard/retention rule to queued research records. Ordinary L1/L2 progress for the account is unaffected.

No fake "offline synchronization succeeded" state; show local-only, pending, synced or error. Causal order inside a single task must be preserved. Timestamps alone do not determine sequence order.

## 9. Research reconstruction and scoring

A reconstruction record binds:
`game_build_id`, native/Explorer topology contract, scenario configuration, deterministic seed, task stimulus/generator digest, input semantics, presentation basis/slice/view commands as required, ordered semantic transitions and any expected state hashes.

Do **not** equate a gameplay hash with a presentation snapshot. If an image/projection question depends on camera or UI state, that state is part of the frozen assessment stimulus.

An independent Python analysis package must:
- validate and export minimized participant datasets (Parquet/CSV + manifest);
- reconstruct task assignments and item-level responses;
- recompute primary/secondary measures using versioned code;
- flag missing segments, altered stimuli, incompatible forms and protocol deviations;
- report uncertainty, attrition, exclusions and study condition metadata;
- work without direct access to email/account tables;
- reproduce saved derived estimates from their input digest/model version.

Before study deployment, freeze study protocol, item set, scoring rules, relevant UI/build version, randomization scheme and primary analysis. Calibration/novice usability and ethics/privacy acceptance are independent gates.

## 10. Hosted setup, operations and cost

### 10.1 Environments and migration

- Local: Supabase CLI + test fixtures; no real identities.
- Staging: separate Supabase project; only synthetic or explicitly approved test records.
- Production: separate project in Ireland region on a plan with suitable operational guarantees, proposed Pro.
- Schema, RLS, function configs, object-bucket policies and indexes are versioned through migrations. No manual-only production schema changes.
- GitHub CI runs unit/schema/migration/security tests. Staging deploy is automatic only after checks; production requires a human-controlled deployment approval and reviewed migration/rollback.
- Edge API and client advertise supported schema-version ranges; new deployments must handle supported older packaged games or reject clearly without corrupting local queues.
- Verify pricing, current provider limits, processing/subprocessors and contract before provisioning. $25/month is a **starting subscription estimate**, not a guaranteed all-in operating cost (separate projects, egress, compute, backups and overages matter).

### 10.2 Security/privacy checklist

Before any real user collection:
- data map, purposes, legal basis and separate research authorization;
- privacy/participant notices and retention schedule;
- provider processing agreement, subprocessor/transfer review, regional choice;
- ethics/guardian requirements for intended recruitment (first pilot adults only);
- RLS tests with two users, unauthenticated user, researcher role and service role;
- least privilege, TLS, rate limits, secrets outside repository, token safety;
- withdrawal, account export and deletion lifecycle including backup expiry;
- restricted researcher exports and access audit;
- incident response owner and contact procedure.

Pseudonymized data is still potentially personal data. Scientific retention and withdrawal exceptions require legal review; do not infer automatic deletion or indefinite retention.

### 10.3 Backup and monitoring

Database backups **do not include actual Supabase Storage object bytes**. Design separate encrypted off-project backups for PostgreSQL and L3 objects, record backup manifests/digests, restore into an isolated project and verify referential integrity and sample reconstruction. Define retention, restore point/recovery-time objectives and deletion in backups before launch.

Operational telemetry (not participant research events) monitors: upload failure/retry rates; pending and incomplete sessions; idempotency conflicts; database size and object growth; abnormal client output; storage quota; orphan objects; unauthorized attempts; backup age and restore test outcomes. Trigger investigation at >1% sustained upload errors, any conflicting reused ID, unexpected research gaps, >2x volume forecast, and storage warnings around 60%/80%. Calibrate thresholds with the pilot.

Do not silently discard failed records when storage pressure occurs; for research freeze new capture/mark incomplete under protocol, and allow ordinary gameplay to continue.

## 11. PR-by-PR execution plan

**PR 1 — Contract and architecture.** New product-data RDS, assessment RDS outline recording the P3 assessment design as a contract, versioned schemas (`session`, `summary`, `attempt`, `trace`), ownership map, storage/retention rationale and focused schema validators. Declare field purposes, accepted dimensions/topologies, recording levels, and research exclusions. No data collection or hosting. **Gate:** reviewable conformance examples and explicit privacy/scoring open decisions.

**PR 2 — Local Godot recorder.** Implement session coordinator, recording policy, aggregator and journal. Integrate post-action observations for ordinary 2D/3D/4D Play and current Explorer without modifying native execution. Synthetic fixtures and restart tests. **Gate:** no altered game/replay hashes, bounded memory/storage, crash recovery, silent network absence.

**PR 3 — Local hosted contract.** Add Supabase CLI migrations, RLS, Edge Function auth/ingest routes, synthetic users and contractual database tests. No production deployment. **Gate:** cross-user denials, identical-retry ACK, conflict rejection, schema migration and transaction integrity.

**PR 4 — Account and sync.** Add account UI, transport/sync coordinator, supported token handling, explicit guest import, pending/receipt UX, staged deployment on synthetic data. **Gate:** login/logout, fresh-device progress, outage, crash-between-commit-and-ACK and account-switch behavior.

**PR 5 — Assessment V1.** Implement P3's smallest assessment task slice: a small versioned assessment runner reusing Explorer, fixed items plus generator contract, immutable attempts and simple domain-level progress with comparable-form flags. **Gate:** novice task usability, independent rescoring, version mismatch and stimulus-reconstruction tests.

**PR 6 — Authorized detailed traces.** Implement study enrollment/permissions, L3 compact events and private object segments, reconstruction and consent/withdrawal enforcement, storage cleanup. **Gate:** full session reconstruction; integrity/volume and authorization negative tests.

**PR 7 — Research export and progress.** Versioned, minimized datasets; independent Python recalculation; longitudinal charts; access audit and derived estimate provenance. **Gate:** reproducible output on frozen fixtures, no account identifiers in research datasets.

**PR 8 — Production hardening.** Dedicated staging/production configuration, DPA/privacy/ethics gates, retention/export/deletion, restore drill including objects, monitoring, rate control and deploy/revert playbook. **Gate:** documented operational evidence and review, not simply a live URL.

**PR 9 — Authorized pilot and protocol freeze.** Adult usability/data-quality pilot. Evaluate item calibration, missingness, recording overhead, retention, completeness, cost and comprehension. Revise tasks then freeze protocol for the controlled main study. **Gate:** `RESEARCH_PLATFORM_READY` evidence as governed by the existing research plan. The pilot is not evidence of improved spatial competence by itself.

When PR 1/2 may start relative to other work is set by `professional_godot_game_programme.md`, not by this plan. Do not deploy studies until beginner acceptance, experimental UI stability and required approvals. Each PR contains its relevant source/tests/docs and scoped authority changes; avoid a single all-subsystems PR.

## 12. Test matrix and objective gates

| Test family | Required evidence |
| --- | --- |
| Gameplay isolation | Same seed + actions yield identical gameplay snapshots and hashes with recording on/off in 2D/3D/4D |
| Explorer isolation | Object/camera/basis/slice operations retain existing semantics including non-bounded cases; reject taxonomy errors |
| Local durability | Disk failure, truncation, process interruption and restart; accepted committed records recovered or explicitly incomplete |
| Sync | Offline 24h equivalent, reconnect, unordered uploads, duplicate ACK, mismatched digest, account switch (queued records never upload under the new account), sign-out then same-account sign-in resumes the queue |
| Security | Guest/owner/foreign user, expired auth, role escalation, injection/oversized payload, private object URL denial, researcher role cannot read `research_private.account_links` or join a participant to an account |
| Research permission | No L3 without authorization; withdrawal through `/v1/studies/{id}/withdraw` before queued upload; repeated withdrawal is idempotent; withdrawal leaves L1/L2 progress intact; consent/protocol version mismatch |
| Contract evolution | Older supported build/version; unknown fields; invalid topology IDs; explicit incompatible version handling |
| Task scoring | Frozen stimuli, scored answers, expected error classes, replay, attempts immutable; holdout separation |
| Volume/performance | Representative 30-min activity, bursty input, memory cap, bytes/session, no frame/input-loop blocking |
| Research reproducibility | Export+recompute from identical fixtures independent of original client/server |
| Operations | Backup/restore both database and objects, orphan reconciliation, retention/deletion, cost alert |
| Platform | Human review on each release platform in programme order (Windows → Linux → Android tablets), including journal recovery after the OS stops the app on Android; no release readiness inferred from headless CI |

Required gates:

- `PARTICIPANT_STORAGE_READY` — identity, local recovery, auth/RLS, idempotent server receipt and restore proven.
- `ASSESSMENT_PIPELINE_READY` — comparable versioned tasks, scoring, outcome persistence and export reconstruction proven.
- `RESEARCH_PLATFORM_READY` — inherited programme gate: approved study/permissions, usability, integrity and independently reproducible data; no claim until real reviewed pilot evidence.

These do not replace `EXPLORER_LEARNING_READY` or the programme's existing `FIRST_EXPERIMENT_COMPLETE`.

## 13. Verification, docs and release constraints

Follow root `AGENTS.md`, `docs/governance/CHANGE_GOVERNANCE.md` and `docs/governance/VERIFICATION.md`. Each implementation PR resolves and composes actual affected routes. Documentation-only changes still require documentation/governance validation; code/schema/identity changes additionally require their native/Godot/integration/security/regression evidence. Full `CODEX_MODE=1 ./scripts/verify.sh` is the canonical full gate when triggered. Do not claim any check passed unless run on that exact tree. Remote CI is observed once, not polled.

No real participant data, credentials, private URLs, research exports or production tokens in Git, PR text, fixtures, logs or CI artifacts. Synthetic fixtures only.

Documentation updates with implementation: add RDSs, architecture ownership, schema migration guide, tests/protocol references, research plan dependencies and focused backlog items. Keep completed batch evidence in PR/history, not appended into the active authority.

## 14. Explicit unresolved decisions and blockers

The following must be resolved at their stated gates rather than guessed:

1. Which exact assessment items/forms and primary endpoints will be valid for novice 4D participants? **Before PR 1 closes / before PR 5 implementation.**
2. Which research permission/legal-basis model and retention/deletion schedules apply, especially to minors? **Before live recruitment.**
3. Whether approved credential stores are available on each release platform (desktop OS stores; an Android Keystore plugin for Godot); otherwise reauthenticate rather than insecurely persist tokens. **Before PR 4 release.**
4. Detailed L3 traces required to reconstruct presentation-dependent tasks, including camera continuous motion representation. **Before PR 6 freeze.**
5. Concrete Supabase project, region, payer, service owners, DPA/subprocessor and operational costs. **Before staging/production provisioning.**
6. Disaster recovery objectives, external backup destination and scheduled restore owner. **Before production data.**
7. Pilot cohort size, assessment difficulty calibration, control condition and analysis plan. **Before PR 9.**

## 15. Completion definition

This implementation programme is complete only when a packaged Tet4D client can (a) record compact sessions locally without changing gameplay, (b) synchronize safely to an authorized user's central history, (c) score and display comparable domain assessments with provenance, (d) capture/reconstruct limited authorized research traces, (e) export a minimized independently reproducible dataset, and (f) pass privacy/security/backup/novice/operational acceptance.

A provider dashboard showing uploaded rows, a higher gameplay score, or a generated progress chart alone satisfies none of the scientific completion criteria.

### Provider references checked during planning

- Supabase regions: https://supabase.com/docs/guides/platform/regions
- Edge Function auth guidance: https://supabase.com/docs/guides/functions/auth
- PostgreSQL/RLS guidance: https://supabase.com/docs/guides/database/postgres/row-level-security
- Database backup limitation: https://supabase.com/docs/guides/platform/backups
- Pricing (recheck before procurement): https://supabase.com/pricing
