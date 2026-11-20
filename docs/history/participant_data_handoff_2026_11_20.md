# Participant Data Platform — Handoff Snapshot (2026-11-20)

**Role:** historical/restart reference, not an active-task or planning authority
**Snapshot:** 20 November 2026, `master` at `912edfbb54402ef4f5fc4c6480db1a91d153cff2`
**Programme owner:** `docs/plans/professional_godot_game_programme.md`
**Live status owner:** `docs/BACKLOG.md` and root `CURRENT_STATE.md`
**Current domain design:** `docs/plans/participant_data_platform_implementation.md`; proposed security design: `docs/plans/participant_data_security_plan.md`

This is a dated handoff of the November 2026 research-platform planning/review session. It must not be interpreted as the latest runtime status or become a second authority for stage order. For subsequent work, read the current repository and governing owners.

## Objective and boundaries

Tet4D aims to investigate whether 2D/3D/4D gameplay and Explorer practice improve **transferable** spatial reasoning, rather than only familiarity with game controls. Keep player progress, behavioral observations and validated scientific inference distinct.

The proposed platform is offline-first, compact, pseudonymous for researchers, opt-in for detailed research capture, and independently reproducible. Native gameplay/transforms and Explorer topology remain authoritative; recording consumes semantic results without influencing movement, timing or replay.

Do not activate accounts, hosted collection or a human study merely because a database migration exists.

## Repository state at the handoff

| PR | Work | Verified status on 2026-11-20 |
| --- | --- | --- |
| [#189](https://github.com/mousomer/tet4d/pull/189) | Non-technical participant-data overview and full nine-PR implementation plan | Merged |
| [#194](https://github.com/mousomer/tet4d/pull/194) | E3 coordinate assessment, E4 logical schema and synthetic local PostgreSQL functions | Merged 2026-11-19, merge `6ac5ce17bcc72250b96f0d77d203eeaebd8c403e` |
| [#195](https://github.com/mousomer/tet4d/pull/195) | Before-production audit retention, indexing and volume contract | Merged 2026-11-20, master `912edfbb54402ef4f5fc4c6480db1a91d153cff2` |
| [#196](https://github.com/mousomer/tet4d/pull/196) | Correct retention wording from link "exists" to link "unrevoked" | Open; required CI gate passed at snapshot |

The final PR #194 head had 17 successful checks, including four Python jobs with PostgreSQL 16.6 service containers. These checks support the synthetic slice, **not** production identity security or research readiness.

## Implemented baseline

### Measurement (E3)

- First assessment: bounded 4D coordinate prediction after signed quarter-turn about a pivot.
- Engine-consistent rotation: positive `(a,b) → (b,-a)`; negative `(a,b) → (-b,a)`.
- Frozen versioned items/forms/scoring, exact-coordinate answer classification, latency and missingness handling.
- Scientific limitations: one task family; form equivalence, held-out transfer and later study protocol require calibration.

### Storage (E4)

- `migration/participant_data/001_assessment.sql` defines schema and restricted PL/pgSQL API for synthetic study records.
- Enrollment, protocol/arm allocation, visits, slots, presentation, attempts/outcomes, exposure, withdrawal and durable ingestion receipts are represented.
- Research-visible records use random enrollment IDs; account linkage is in restricted `assessment_private`.
- Presentation is a client event with independent observed and received times; answered/invalid/interrupted outcomes require presentation, while "unpresented" forbids it.
- All ingest commands are idempotent under stable identities and content digests; enrollment-level locks serialize write/close/withdraw.
- A rejected batch rolls back its research writes but retains the allowed authorization/conflict audit event using a PL/pgSQL exception block and an error-row response that the adapter commits before translating to a client error.
- A withdraw action blocks subsequent ingest and closes unresolved visits, preserving study attrition records.

### Coverage

At merge, PR #194 reported 22 PostgreSQL integration tests and 25 research/conformance tests; hosted Python-matrix checks succeeded. This is synthetic evidence and is not a penetration test, full-client test or pilot.

## Explicitly not implemented

- Godot local journal and post-action recorder.
- Optional real accounts, authenticated cloud sync or a deployed Supabase host.
- Production-ready KMS/encrypted identity boundary, OS token integration or independent security review.
- Server-calculated eligibility and concealed study allocation (the synthetic `eligible`/`arm` arguments are not authoritative).
- Calibrated full assessment forms and controlled study protocol.
- Secure trace storage, exports/deletion, complete retention jobs, object+database restore drill.
- Authorized research enrollment, human pilot or proof of improved 4D ability.

Backlog P3 and P4 remain unchecked; `EXPLORER_LEARNING_READY` and `RESEARCH_PLATFORM_READY` have not been established by these PRs.

## Immediate follow-on work

1. **Reconcile open PR #196** and do not duplicate or overwrite its document changes. Its core correction specifies active-link retention using `revoked_at IS NULL`, not link-row existence.
2. **Review proposed security plan** `docs/plans/participant_data_security_plan.md` before implementing user identity, account mapping or production data. Decide on provider, trust separation, lookup encryption/HMAC keys, KMS custody, RLS, role policy and negative tests. These are proposals, not previously implemented controls.
3. **Next proposed bounded technical PR:** offline-only Godot session recorder. Confirm its sequencing against programme and P3 contract before starting. Use thin post-action adapter modules rather than adding network/storage/scoring to `trace_replay_app.gd`.
4. **Scientific work in parallel:** task/form calibration, transfer and retention protocol, comparison-arm definitions and ethics/privacy/legal review.

### Godot recorder requirements

- Stable ID, versioned session envelope, dimension/topology/configuration provenance and L0 summary.
- Durable `user://participant_data/` journal with atomic writes, checksums, bounded volume, crash-tail recovery and local-only operation.
- Post-action observation of native and Explorer semantic outcomes; no duplicate gameplay authority.
- Disable collector without changing game hashes, movement or interaction timing.
- Deterministically stepped tests (avoid uncontrolled gravity ticks), isolated Godot `user://` test directories, disk-full/restart/truncation behavior and actual-platform durability tests.
- Keep client token and contact information outside the journal; no cloud upload or real-person data in first slice.

## Prior unresolved review notes

- Researcher-facing link reads are now audited within the PL/pgSQL ingress path, but privileged database owner reads fall outside that application audit boundary. The later deployment threat model must control those reads.
- Access audits generate one event per authorization check; retention, capacity, monitoring and indexes are covered by #195/#196 **planning**, not by a deployed retention job.
- Credential storage and encrypted local files need platform-specific evidence. Release programme ordering is Windows, Linux, Android tablets; macOS distribution is deferred.
- Research events are self-reported by the client and are not independent proof of scientific authenticity.
- Offline research withdrawal prevents new ingestion; deletion, retention and backups still need approved policy and implementation.

## Verification and closure

Before any change, follow root `AGENTS.md`, `docs/governance/CHANGE_GOVERNANCE.md`, `docs/governance/VERIFICATION.md` and actual diff-driven routes. Run focused tests and the required `CODEX_MODE=1 ./scripts/verify.sh` gate where triggered. Report local/hosted evidence separately, and do not poll CI.

**This handoff is a snapshot, not authorization to merge #196, deploy a provider, collect participant data, or declare an acceptance gate passed.**
