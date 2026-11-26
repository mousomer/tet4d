# Participant Data Security and Identity Protection Plan

Role: spec
Status: active
Source of truth: this file for **proposed** Tet4D participant-platform security design, threat model, and acceptance requirements; repository security governance remains with `docs/governance/SECURITY_AND_SANITATION.md`
Supersedes: none
Last updated: 2026-11-20
Programme: `participant_data_platform_implementation.md`
Study/consent: `spatial_intuition_research_plan.md`, `e4_assessment_storage_contract.md`
Implementation baseline: `docs/architecture/participant_data_platform.md`

## 1. Purpose and current status

Plan security controls for optional player accounts, offline progress, assessment outcomes and opt-in detailed research traces. A breach of the research store must not automatically disclose account identities or credentials. Minimize how much any compromised user, service, backup or administrative account can learn or alter.

**Design proposal only.** This document does not assert that encryption, KMS, managed authentication, new roles, RLS, key custody, operational monitoring or production hosting have been implemented. The existing E4 PostgreSQL slice and its synthetic-only tests remain the current implementation. Live participant collection, deployment and any new gate acceptance require separate review. Existing repository governance is not replaced.

Security should protect confidentiality, integrity, availability and reproducibility. It cannot eliminate the risk of compromise of a service that is legitimately authorized to decrypt or export data.

## 2. Information classification and cryptography

| Data | Design | Reason / constraint |
| --- | --- | --- |
| Account password | **Prefer no Tet4D-managed password.** Use a managed identity provider with email OTP or passkeys where feasible. If a custom password service becomes necessary, store only Argon2id salted password verifiers with appropriately tuned parameters; optional separate server-side pepper, never reversible encryption | Passwords must never be recoverable. Do not add a duplicate password table alongside managed Auth |
| Email address | Keep only in the identity provider/isolated identity service when possible. If Tet4D independently needs recoverable email, use randomized authenticated encryption with per-record nonce and key version | Login/recovery/contact require an address; a hash cannot be used to send an email |
| Email lookup | Where a **custom** encrypted email directory requires deterministic matching, compute HMAC-SHA-256 over a documented canonical representation with a distinct, guarded lookup key | Plain unsalted SHA-256 of common emails is vulnerable to dictionary matching. Normalization must not accidentally collapse distinct email addresses |
| Username | Decide whether intentionally public. Private identifiers are stored as encrypted text with a keyed lookup token when necessary; public display names require disclosure and moderation rules | A username is not necessarily a secret, but it can be personally identifying |
| Authentication token | Short-lived access credentials; refresh tokens protected by supported OS credential storage, rotated/revoked by provider | Never store refresh tokens in ordinary Godot settings or plaintext journals |
| Player progress | Minimize content, authorize every record by verified account, encrypt at rest where feasible and in transit | Progress contains detailed personal usage history |
| Research enrollment ID | Cryptographically random, independent from the auth user ID; do not derive from name/email or an unkeyed hash | Makes routine research queries pseudonymous |
| Account-to-enrollment link | Restrict to an identity-controlled boundary, independently encrypted/permissioned where warranted, with audited accesses | A separate schema alone is **not** a separate breach boundary if full backups or administrative credentials cover both |
| Assessment stimuli, answers and traces | No names/emails/contact fields; narrow research roles; private object storage; content digests and immutable versioned manifests | Indirect re-identification is still possible through timestamps, device data and unusual action sequences |
| Backups, audit records and exports | Encryption, explicit access/retention boundaries, separate backup access, integrity manifests | Audit logs and backups can contain identifiers even when the main research schema does not |

**Supabase Auth constraint:** if chosen, Supabase Auth itself manages email and password-verifier storage. Tet4D must not claim it can replace provider-owned email fields with HMAC values while preserving email sign-in. Avoid duplicating plaintext emails in application/research tables; isolate the provider's auth domain from research data. Do not assume Supabase's password-verifier algorithm is configurable or identical to a proposed Argon2id custom service.

Password salting and a password pepper are different: use an independent random salt **per password**; a pepper is a secret held separately from the password database. Use an adaptive password hashing function, not SHA-256 or general-purpose HMAC as the password verifier.

## 3. Separation and threat boundaries

Proposed trust domains:

1. **Godot client:** untrusted, works offline; no service-role credentials or KMS decryption keys.
2. **Authentication service:** verifies identities and controls login, recovery, MFA and session revocation.
3. **Participant API:** verifies token claims, recording policy, ownership, payload integrity and rate limits; has only the permissions its endpoints require.
4. **Identity-link service or vault:** handles account-to-research linkage for narrowly authorized participant rights and administration; research queries cannot call it freely.
5. **Research storage:** pseudonymous enrollment/visit/outcome/trace records without email, username, or password data.
6. **Analysis/export service:** accesses approved minimized datasets, not the general account-identity directory.
7. **External KMS and protected backups:** their access policies are independent of ordinary research-reader credentials.

Separate database schemas + SQL grants are useful against ordinary database roles, as demonstrated by E4. They are **insufficient** against a stolen full database backup, privileged database credentials or a compromised host. Before deployment, decide whether identity mapping needs a separate database/project/service and distinct backup boundary. The security decision must name the attacker capabilities that separation is intended to withstand.

No user-supplied `principal`, `user_id`, `enrollment` or study code can override verified auth ownership. All elevated `SECURITY DEFINER` and service-role operations require reviewed parameter checks, function grants, pinned search paths and least privilege. Research-readers must never receive the link key or identity-join capability.

## 4. Key custody, lifecycle and encryption limits

Use a managed KMS/key vault, not keys in code, GitHub, client binaries, database tables, general environment dumps or logs. Separate purposes and permissions:

- field-encryption key for recoverable identity attributes, if applicable;
- HMAC lookup key, if a keyed directory is required;
- optional password pepper **only** for a custom password service;
- backup encryption keys;
- research trace/object encryption keys where client/provider envelope encryption is required;
- token-signing/provider keys administered by the authentication system.

For any app-managed encryption, use a reviewed AEAD scheme (e.g. AES-256-GCM) with unique nonces, authenticated associated data binding record identity, and explicit algorithm/key version. Support key rotation and re-encryption, recovery from lost access, revocation after compromise, and tests for tampering or wrong-key use. HMAC lookup rotation needs a controlled dual-index/reindex procedure. Never reuse keys across purposes.

A KMS does not guarantee secrecy after an authorized API server is compromised: that server may request decryptions. Bind KMS rights to narrow service identities, limit decryption rates, log calls, and separate administrative controls. A breached administrator may defeat field encryption; defend the control plane separately.

## 5. Required controls by boundary

### 5.1 Accounts and authentication (P0 before account launch)

- Prefer managed Auth rather than custom password handling.
- MFA or phishing-resistant passkeys for administrators, researchers and deployment identities; step-up authentication for account export/deletion or sensitive identity recovery.
- Short access-token validity, refresh-token rotation/revocation and logout behavior; protect against account enumeration, brute force and OTP abuse with rate limits and generic failure messages.
- Document recovery/ownership transfer, email changes, account compromise and device loss.
- For supported Godot platforms, confirm a reviewed secure-token-storage adapter. If unavailable, do not persist long-lived refresh tokens; require new login.
- Explicitly test a signed-out account A's pending records cannot sync under account B and can resume only as A.

### 5.2 APIs, databases and object storage (P0)

- Verified user identity and permission checks at **every** endpoint and object boundary; RLS as defense-in-depth, not a substitute for endpoint ownership checks.
- Restricted database roles; no direct public client writes to research tables or unrestricted user-controlled `SECURITY DEFINER` operations.
- Parameterized SQL, schema allowlists, bounded payloads, length and quota limits, content digests, immutable IDs, idempotent retries and conflict audit.
- Private object buckets and short-lived scoped upload/download permissions; check authorization again at finalization and download.
- Per-account, per-enrollment, per-IP/abuse-signal rate controls where permitted; controls must not expose researcher identity mappings.
- Separate local, staging and production deployments, least-privileged deploy identities, migration review and staged rollback; no production participant fixtures in CI.
- Assess supply-chain changes and dependencies before adding encryption/storage plugins.

### 5.3 Local/offline Godot records (P0 for the local recorder)

- Files under `user://participant_data/` must not contain passwords, service tokens, plaintext contact details or unneeded identity data.
- Encrypt *sensitive* offline records when a viable platform-protected key is available; avoid pretending an encryption key bundled in Godot protects local data. A local guest with no OS secure-storage capability needs explicit documented threat limits.
- Atomic journal updates, checksums/integrity, bounded queue, crash-tail recovery, account binding and no upload after research withdrawal.
- Independent account-bound local queues; distinguish local-only/pending/synced/error. A user action must never block on network or cryptography work.
- Confirm storage and credential behavior on release platforms in actual programme order (Windows, Linux, Android tablets; macOS later). Android needs OS-kill recovery and a vetted Keystore-compatible integration.
- Test deterministic playback with collector on/off, controlled gravity ticks and isolated `user://` test directories.

### 5.4 Researchers and administrators (P0 before studies)

- Roles: player (own progress), researcher (approved pseudonymous study scope), identity custodian (restricted identity operations), deployment operator (environment operations), privacy/retention operator (data-subject lifecycle). Keep them independent by default.
- Minimized exports only; explicit permissions by study/purpose, expiring export access and an access approval trail.
- Protect against linkage through fine timestamps, rare topology usage, device fingerprint attributes, IP addresses, repeated behavior patterns and unrestricted longitudinal traces.
- Audit privileged reads, account linking, permission changes, withdrawals, conflicts, exports and deletions. Do not write decrypted identities, tokens or raw payloads into general logs.
- Audit retention and indexing follow `e4_assessment_storage_contract.md`; a later correction to the "unrevoked link" wording is under PR #196 at the time of this document. Retention remains subject to approved schedule/legal review; withdrawal is not automatically deletion.
- Deploy safeguards for direct database administrator reads, which the local E4 `access_audit` does **not** capture.

### 5.5 Operations and recovery (P1 before production)

- Encrypted independent database **and** object-store backups. Database backups alone do not guarantee recovery of private trace-object bytes.
- Restrict backup decrypt/read and deletion capabilities separately; run isolated restore drills, check integrity and reconciled object manifests.
- Retention schedules for identity, progress, research, trace, audit, export, local queue and backups; implement right of access/erasure and applicable research exceptions through legal review.
- Monitor abnormal authorization failures, large exports, decryption rates, data-volume spikes, unexpected administrative privileges, failed restores, incomplete traces and provider alerts.
- Document breach response: containment, credential/token revocation, key rotation, access suspension, forensic evidence, participant impact assessment, legal notification obligations and recovery ownership. Any GDPR deadlines must be assessed against the incident and applicable law, not assumed from code.
- Maintain vulnerability/dependency scanning, change review, incident drills and periodic privilege review.

## 6. Breach scenarios and expected resistance

| Scenario | Primary defense | Residual risk / proof |
| --- | --- | --- |
| Public research database backup stolen | No direct identities; isolated mapping; field/backup encryption | Indirect reidentification and any privileged identity copies still matter; test full-backup exposure model |
| Ordinary researcher credential stolen | Scope-specific read permissions; no identity lookup; MFA | Access to assigned pseudonymous records; test unrelated-study denial and bulk export limits |
| User JWT stolen | Short-lived/revocable sessions; ownership checks; step-up for sensitive actions | Attacker may see that user's permitted progress until revocation |
| Participant API compromised | Least-privileged services, per-purpose KMS permissions, egress/decryption limits | The service may legitimately decrypt what it can access |
| KMS or administrative account compromised | Separate roles, MFA, alerts, limited grants, emergency rotation | A sufficiently privileged control-plane breach may defeat encryption |
| Godot device stolen | OS-protected tokens, encrypted local sensitive records where supported | Guest local-only data may not have strong at-rest protection |
| Malicious client forges research answers | Never trust the client as scientific truth; validate ownership, IDs, contract and timing provenance | Valid-looking events can still be fabricated; study anti-cheat and exclusions remain necessary |
| Deleted records remain in backup | Documented expiry and deletion/restore reconciliation | Restore must not silently reintroduce erased records outside an approved exception |

## 7. Test and implementation evidence

For each security-sensitive PR, specify actual test boundary and failure case. Minimum matrix:

| Test | Required assertion |
| --- | --- |
| Identity separation | Research-role dump cannot recover email/account mapping or call privileged join |
| Cross-account isolation | A cannot read, upload to, or claim B's session, queued record, trace, or assessment |
| Token security | Expired/revoked/forged token denied; secrets absent from normal logs/client assets |
| Key separation | Read-only database credentials cannot decrypt fields or compute keyed lookup tokens |
| Encryption | Wrong key, nonce misuse, modified ciphertext and changed associated data fail closed |
| Role and `SECURITY DEFINER` grants | Privilege escalation attempts fail; roles cannot read private schema outside reviewed operations |
| Withdraw/delete | Queued L3 stops on withdrawal; L1/L2 progress policy remains distinct; backup expiry is documented |
| Replay/idempotence | Duplicated requests acknowledge once; conflicts preserve audit without committing corrupted assessment records |
| Local integrity | Crash, disk-full, truncation, OS termination, account switching; no credentials in journals |
| Audit | Authorized/denied link reads, exports and administration tracked; denied batches retain audit records |
| Research exports | No direct identifiers; coarse data minimizes indirect identity clues |
| Restore | Database and object backups reconstruct authorized records without resurrecting prohibited deletions |
| Threat review | Simulated full database leak, API compromise, malicious client and privileged account misuse |

The E4 PostgreSQL synthetic implementation has partial evidence for roles, receipts and audit. It does **not** establish any identity-vault isolation, application field encryption, managed KMS, hosted RLS, secure Godot tokens or production deployment.

## 8. Implementation order and gates

The following are **proposed** subordinate design gates, not existing approved programme gate identifiers. Approval/registration belongs to the owning programme and governance contracts.

1. `SECURITY_DESIGN_READY`: field classification, provider choice constraints, threat model, mapping/backup separation, key inventory and per-role privilege matrix reviewed. No runtime code required.
2. `IDENTITY_SECURITY_READY`: managed Auth decision, token security, RLS, cross-account denial, cryptographic key custody/rotation and staged negative tests accepted.
3. `RESEARCH_PRIVACY_READY`: approved study authorization, minimization, controlled exports, audit/retention, withdrawal, deletion, restores and incident response accepted.

**Suggested slice order:** first define security and identity ownership before the account/backend PR; then implement offline journaling without user credentials; then managed authentication and identity separation; then private research linkage, traces, exports and operational proof. Independent assessment and novice-Explorer gates remain necessary. Do not treat local synthetic SQL completion as research readiness.

## 9. Decisions required before implementation

- Managed auth provider and whether email OTP or passkeys are the launch method.
- Whether user display names are public and whether any custom email directory is needed.
- Threat boundary for account-to-enrollment mapping: private schema, separate database or separate project/service.
- Key manager, authorized service identities, ownership, rotation and encrypted-backup separation.
- Offline key storage options on each release platform; guest-device threat model.
- Real research eligibility, concealed randomization, protocol freeze and adult-only pilot authorization.
- Legal basis, approved retention schedule, identity deletion/export and research-study withdrawal handling.
- Security owner, breach response and privileged audit review.

**Principle:** protect identity by minimizing and separating it, protect passwords with managed authentication, protect recoverable data with encryption, protect lookups with guarded keyed operations, and verify that a compromised component cannot automatically reach every other domain.
