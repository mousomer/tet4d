# Task Contract — Stage 54F-3R.1 Shared Replacement Review Corrections

Status: COMPLETE / LOCAL CORRECTION GREEN / INDEPENDENT RE-REVIEW PENDING

Starting branch: `codex/canonical-local-board-geometry`

Starting SHA: `31fef3718c967a20fcb6b9d14b83356f92ea40d2`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Close only the three findings from the independent Stage 54F-3R review: keep
unrelated sibling backups intact when exporting to a previously absent arbitrary
destination, guard the two newly introduced persistence-test load paths from the
repository runner's pre-existing false-green crash behavior, and directly cover
the three missing shared-replacement transitions. Preserve the accepted profile,
settings, Designer, cockpit, gameplay, and persistence architecture.

## Classification and Authority Comparison

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`, because the bounded filesystem-mechanics
  provider is consumed by the separate named-profile and ordinary-settings
  persistence owners.
- Affected layers: shared Godot persistent-file mechanics, profile artifact
  export/persistence results, ordinary shell-settings write regression tests,
  Godot persistence tests, and governing architecture/acceptance records.
- Claims: sibling backup cleanup is limited to an existing-destination
  replacement lifecycle; the three unexercised state-machine transitions are
  explicit and deterministic; failed profile loads append ordinary test failures
  instead of dereferencing null; existing profile/settings behavior remains
  intact.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `integration`, and `deterministic`.
- Full repository gate: required because this is an independent-review
  correction to shared product-shell persistence infrastructure.
- Authority effect: none. `PersistentFileReplacement` continues to own only
  filesystem mechanics; `PresentationProfileLibrary` retains named-artifact
  lifecycle and export semantics; `SettingsStore` retains ordinary-preference
  ownership; the registry and `PresentationProfile` retain parameter/schema
  authority.
- Visual-design status: this task uses the completed presentation-comparison
  apparatus but neither creates candidate styles nor performs comparative visual
  evaluation or default-presentation selection. Those remain separate future
  stages (54F-4, 54F-5, and 54F-6 respectively).

The existing profile-library contract makes export an explicit write to an
arbitrary user-selected path, while the settings contract owns a fixed app path.
The shared helper may use pre-operation destination existence as filesystem
state, but may not infer ownership from caller type or destination semantics.
Therefore a successful direct install may clean a sibling backup only when the
destination existed before this replacement operation. Existing-destination
backup/install/restore behavior remains unchanged.

## Scope Matrix

| Layer | Required change | Evidence |
| --- | --- | --- |
| Shared file mechanics | Capture whether the destination existed before direct install; preserve unrelated sibling backup state for a fresh destination; make stale-backup cleanup failure explicit. | Failure-injected absent-install, backup/install-success, and cleanup-failure transition tests. |
| Profile library | Preserve fresh-export sibling `.bak` byte-for-byte and surface actionable helper warnings through the existing result boundary. | Production-path `export_profile()` regression plus existing lifecycle/restore coverage. |
| SettingsStore | Preserve fixed app-path save, cleanup, restoration, counters, and warning diagnostics. | Focused existing-destination and failure-regression suite. |
| Test integrity | Guard the two Stage 54F-3R load assertions before profile dereference. | Scratch mutation produces an ordinary recorded test failure without a script crash. |
| Documentation | Record backup-ownership, warning, test-guard, and transition closure without downgrading Stage 54F-3 reviewed-green status or claiming visual comparison. | Governance, generated-document, semantic-boundary, sanitation, and diff checks. |

## Allowed and Required Changes

1. Track pre-operation destination existence inside
   `PersistentFileReplacement`; do not add caller-semantic knowledge.
2. Preserve a sibling `.bak` on successful installation to a destination that
   did not exist before the operation.
3. Preserve existing-destination direct replacement, backup/install, restoration,
   recoverability, and cleanup guarantees.
4. Add direct failure-injection coverage for absent-destination install failure,
   existing-destination backup/install success, and stale-backup cleanup failure.
5. Exercise actual `PresentationProfileLibrary.export_profile()` with a fresh
   destination and unrelated sibling backup whose bytes must remain unchanged.
6. Guard the two newly introduced Stage 54F-3R profile-load assertions and
   perform a non-committed mutation sanity check.
7. Propagate an actionable successful-write cleanup warning through existing
   profile-library results; do not create a diagnostics framework.
8. Update only the routed architecture, acceptance, backlog, and restart-handoff
   records, then run every task-requested gate.

## Forbidden Changes

- profile/artifact/settings schemas, IDs, names, import/export format, Save/Save
  As/load/A-B/dirty-state behavior, startup defaults, or ordinary settings policy;
- gameplay/setup/native/replay/hash, camera, basis/slice, NEXT/HOLD/Ghost,
  cockpit geometry, layout, input, or Designer persistence boundaries;
- the global Godot test runner, a new test framework, new backup naming, export
  UX, themes, style catalogs, candidate visual designs, comparative visual
  evaluation, or default-presentation selection;
- reset, rebase, merge, predecessor amendment, push, PR, or publication.

## Acceptance Criteria

1. A successful write to a previously absent destination preserves any
   pre-existing sibling `.bak` byte-for-byte.
2. Actual profile export to a fresh arbitrary destination proves that behavior.
3. Existing-destination profile and settings replacement semantics remain intact.
4. Destination-absent install failure reports failure, creates no destination or
   phantom artifact, cleans temp according to contract, leaves backup untouched,
   and increments no success counter.
5. Direct-replace failure followed by backup/install success installs the new
   destination, cleans owned backup state, reports success, and increments once.
6. Stale-backup cleanup failure has explicit deterministic non-destructive
   semantics and is not silently swallowed.
7. Actionable successful-write cleanup warnings reach the profile-library result
   boundary; settings retain their existing diagnostic propagation.
8. The two affected profile-load assertions append a failure and return rather
   than crashing when load fails; a scratch mutation proves ordinary failure
   reporting.
9. Partial-write, failed Save As, restore rename, restore copy fallback, total
   restoration failure, SettingsStore, deterministic diagnostics, corruption
   isolation, and viewport-allocation regressions remain green.
10. No semantic authority transfers and no visual-design comparison is claimed.
11. Focused, canonical Godot, pinned Godot 4.7.1, governance, generated-doc,
    settings-externalization, semantic-boundary, sanitation, diff, and full
    repository gates pass.
12. One coherent local commit is verified as the exact final tree and leaves a
    clean worktree without push or PR.

## Explicit Deferrals

The repository-wide Godot runner false-green architecture remains advisory-only.
All Stage 54F-3 non-goals remain deferred. Candidate style creation belongs to
Stage 54F-4, comparative visual evaluation to Stage 54F-5, and default visual
selection/polish to Stage 54F-6; the comparison apparatus being available is not
evidence that any of those visual-design stages is complete.

## Completion Evidence

- focused helper, profile-library, SettingsStore, settings-integration, and
  cockpit tests pass in Godot 4.7.1;
- a scratch-copy mutation forces the guarded restored-profile load to fail as an
  ordinary recorded assertion with process exit 1 and no script crash;
- the isolated canonical Godot suite prints `Godot replay tests passed.`;
- the pinned clean-copy gate passes engine/API checks, the canonical suite, 59
  topology transport cases, and Godot 4.7.1 verification;
- settings externalization, 117-path project-contract validation, generated
  maintenance/configuration checks, 120-script semantic-boundary validation,
  repository sanitation, and diff checks pass;
- the full repository gate reports `verify: OK`.

The existing host-user-data canonical invocation still reproduces the documented
unrelated onboarding-preference contamination; the isolated canonical and pinned
invocations are green. Intentional negative-path persistence diagnostics and
known non-failing Godot teardown advisories remain visible. No push or PR is
performed, and Stage 54F-3R remains pending independent re-review.

---

# Task Contract — Stage 54F-3R Profile Persistence Robustness

Status: COMPLETE / LOCAL AGENT-DRIVEN ROBUSTNESS GREEN

Starting branch: `codex/canonical-local-board-geometry`

Starting SHA: `47c90c67d5a13a84bd826f17f2838f0de3f38ec5`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Close the four P2 findings from the reviewed-green Stage 54F-3 implementation:
reject incomplete temporary writes before installation, give profile replacement
the existing settings-store rename/copy restoration guarantees, make library
scan diagnostics idempotent and deterministically ordered, and mechanically
protect the Live-4D gameplay viewport allocation from Profile Library expansion.
The accepted explicit-persistence architecture and all profile, Designer,
settings, gameplay, camera, basis, schema, and authority semantics remain
unchanged.

## Classification and Authority Comparison

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`, because one bounded persistent-file
  mechanics provider is shared by the existing named-profile store and ordinary
  settings store, while the cockpit assertion crosses library UI and production
  HUD layout.
- Affected layers: Godot persistent-file mechanics, named profile artifact
  storage, ordinary shell-settings write safety, current-scan diagnostics,
  Designer/HUD layout tests, and governing architecture/acceptance records.
- Claims: incomplete writes never install; failed replacement preserves or
  explicitly retains recoverable prior content; unchanged storage produces an
  unchanged snapshot; library disclosure consumes internal Designer space
  without changing the gameplay viewport; Stage 54F-3 semantics remain intact.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `integration`, `deterministic`, and bounded `human_visual` inspection.
- Full repository gate: required because this is a reviewer-requested correction
  that hardens mechanics shared by two persistent product-shell domains.
- Authority effect: none. `PresentationProfileLibrary` retains named-artifact
  lifecycle ownership, `SettingsStore` retains ordinary-preference ownership,
  and the registry plus `PresentationProfile` retain parameter/schema authority.

The owning Stage 54F-3 library contract already requires temporary replacement
consistent with shell-settings persistence and isolated deterministic listing.
The shell-settings persistence contract already requires rename restoration
with copy fallback. This slice corrects implementation/evidence drift against
those accepted contracts; it does not revise product semantics or establish a
new persistence domain.

## Scope Matrix

| Layer | Required change | Evidence |
| --- | --- | --- |
| Shared file mechanics | Check the Godot file error after writing/flushing a sibling temp; install only a confirmed write; preserve backup until install or restoration succeeds. | Injected write, rename, copy, and cleanup failure tests through both existing owners as applicable. |
| Profile library | Use the shared mechanics without changing artifact paths/schema/counters; report restored, backup-recoverable, and failed-restoration outcomes explicitly. | Persisted-state overwrite/Save-As tests and restore rename/copy/total-failure cases. |
| SettingsStore | Adopt only the shared write-completion check while preserving schema, save-on-change, diagnostics, injection ordering, and ordinary-preference ownership. | Existing focused settings-store suite plus incomplete-write regression. |
| Diagnostics | Rebuild one sorted current-scan diagnostic set per listing operation. | Three equal deterministic snapshots with healthy, corrupt, stale-temp, and stale-backup artifacts. |
| Cockpit layout | Assert full Live-4D Designer library collapse/expansion leaves the production gameplay viewport rect unchanged. | Structural production-scene test retaining NEXT, HOLD, piece controls, and basis/slice visibility. |
| Documentation | Record the bounded robustness closure without downgrading Stage 54F-3 reviewed-green status. | Governance/generated-doc validation and updated architecture, acceptance, backlog, and restart handoff. |

## Allowed and Required Changes

1. Add one small Godot helper for temp write, replacement, backup, and
   restoration mechanics; do not create a general filesystem abstraction.
2. Route only `PresentationProfileLibrary` and `SettingsStore` through it,
   preserving their separate paths, schemas, diagnostics, counters, and APIs.
3. Check `FileAccess.get_error()` after the write/flush and before installation;
   remove an invalid temporary artifact where safe and leave the destination
   untouched.
4. Restore by rename, then copy; retain a valid backup and report failure if all
   restoration paths fail. Never report success or delete the backup in that
   total-failure state.
5. Treat diagnostics exposed by listing/snapshot as deterministic current-scan
   state, with stable artifact order and no query-driven accumulation.
6. Add focused persisted-state, isolation, stale-artifact, Stage 54F-3 semantic,
   settings, and production cockpit-allocation regressions.
7. Update the library/settings architecture records, Stage 54F-3 acceptance,
   backlog, and `CURRENT_STATE.md`; run every task-requested gate.

## Forbidden Changes

- profile/artifact schema, migration, unknown/missing/future-version policy,
  profile identity/naming, startup/default-profile, or ordinary settings policy;
- Designer A/B, dirty-state, Save/Save As/load/import/delete behavior, automatic
  persistence, or application authority;
- themes, catalog/built-in profiles, Tron/Python-reference styles, palette or
  authoring infrastructure, cloud/sharing, telemetry, or new parameters;
- gameplay/setup/native/replay/hash, camera, basis/slice, NEXT/HOLD/Ghost,
  cockpit geometry, responsive redesign, or presentation semantics;
- reset, rebase, predecessor amendment, push, PR, or publication.

## Acceptance Criteria

1. Write/flush success is checked explicitly before any temp installation.
2. Injected incomplete overwrite preserves the exact old readable artifact,
   reports failure, installs no invalid artifact, and increments no success
   counter; failed Save As creates no listed phantom.
3. Install failure restores the old artifact by rename; failed restore rename
   falls back to copy; total restoration failure is explicit and retains a
   recoverable backup while unrelated healthy profiles remain listed.
4. Backups are deleted only after successful installation/restoration, and
   stale `.tmp`/`.bak` artifacts never appear as profiles.
5. Repeated deterministic snapshots over one healthy and one corrupt artifact
   are equal, diagnostics stay stable and ordered, and corruption isolation
   remains intact.
6. Full Live-4D Designer library collapse/expansion leaves the production
   gameplay viewport rect unchanged while NEXT, HOLD, piece controls, and
   basis/slice state remain visible.
7. Save B while A is displayed, detached load, delete-with-active-B, import
   persistence-only, ordinary settings separation, deterministic isolation,
   and all Stage 54F-3 schema/identity semantics remain unchanged.
8. Focused profile/settings/cockpit tests, canonical and pinned Godot gates,
   governance/generated-doc/settings/semantic-boundary/sanitation/diff checks,
   bounded production Live-4D inspection, and the full repository gate pass.
9. Documentation accurately records this post-review closure; one coherent
   local commit leaves a clean worktree without push or PR.

## Explicit Deferrals

All Stage 54F-3 non-goals remain deferred, including themes/catalogs, built-in
profiles, new presentation parameters, schema migration, cloud/sharing,
gameplay persistence, shell-settings redesign, and Designer/cockpit redesign.

---

# Task Contract — Stage 54F-3 Presentation Profile Library

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Starting branch: `codex/canonical-local-board-geometry`

Starting SHA: `5a2e648124ed4ea0f62003fd95fb3d8dca1a57f6`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Add one bounded, explicit, portable library for named `PresentationProfile`
artifacts without changing ordinary shell preferences or the Stage 54F-2 rule
that Designer edits, A/B switching, resets, and hide actions are runtime-only.
The user crosses the persistence boundary only through an explicit library
save, save-as, duplicate, rename, delete, import, or export action.

## Classification and Authority Comparison

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`, because the new presentation-artifact
  storage provider is consumed by the existing Designer UI and bounded runtime
  application seam.
- Affected layers: versioned presentation-artifact storage, detached
  `PresentationProfile` composition, Designer library UI/state, HUD wiring,
  Godot integration tests, and governing architecture/programme records.
- Claims: explicit persistence only; safe named-artifact lifecycle; strict
  current-schema import; detached load into B; unchanged A, ordinary settings,
  gameplay identity, current camera pose, applicability, and cockpit hierarchy.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `integration`, `deterministic`, and bounded `human_visual` evidence.
- Full repository gate: required because this establishes a persistent user-
  artifact owner and integrates it with a shared live product surface.

The versioned shell-settings registry remains the only parameter inventory and
semantic authority. Schema-1 `PresentationProfile` remains the value schema:
it rejects unknown or invalid IDs/values and fills omitted current keys from
registry defaults. `SettingsStore` remains the only ordinary-preference writer.
The library establishes authority only for named artifact identity, naming,
storage, listing, and explicit lifecycle operations. It does not own parameter
meaning, applicability, renderer application, gameplay, camera pose, A/B
semantics, factory defaults, or shell startup preferences.

The exact predecessor commit was clean and verified before this stage with
`CODEX_MODE=1 ./scripts/verify.sh` -> `verify: OK`.

## Scope Matrix

| Layer | Required change | Evidence |
| --- | --- | --- |
| Artifact store | One validated file per generated stable ID under the repository-standard Godot user-data boundary; safe replacement, isolated corruption, and no index drift. | Focused lifecycle, corruption, write-failure, and path-safety tests. |
| Profile contract | Embed and deserialize the existing `PresentationProfile.snapshot()` without a second parameter schema. | Current/future version, unknown/missing, type, bound, enum, and finite-number tests. |
| Designer | Add a collapsed-by-default library surface; save working B explicitly, load a detached B, preserve A, and expose loaded/dirty state. | Component and scene integration tests plus bounded real-window review. |
| Runtime integration | Apply only loaded detached B through the existing preview signal. | 2D/3D/4D applicability, settings, gameplay, camera, NEXT/HOLD, Ghost, basis, and cockpit assertions. |
| Documentation | Establish artifact ownership and reconcile completed programme/backlog/handoff state. | Architecture, authority map, acceptance, programme, backlog, and governance validation. |

## Required Changes

1. Store user profiles as independently readable, versioned JSON artifacts
   whose filesystem names derive only from generated validated IDs.
2. Define artifact type/version, stable local identity, display name, and one
   embedded authoritative `PresentationProfile` snapshot.
3. Support list, Save As, explicit Save/overwrite, load, duplicate, rename,
   deliberate delete, import, and export without an index or database.
4. Reject invalid names, duplicate display names, unsafe IDs, malformed/root-
   shape-invalid JSON, unsupported artifact/profile versions, unknown IDs,
   invalid types/bounds/enums, and non-finite numbers before mutation.
5. Preserve the profile contract's current same-schema missing-key policy:
   fill from registry defaults; do not add implicit cross-version migration.
6. Load into a detached working B, display B, leave captured A unchanged, and
   apply through the existing bounded preview signal only.
7. Track dirty state by semantic B values against the loaded/saved baseline;
   A/B display, camera manipulation, collapse, scroll, and gameplay do not
   affect it.
8. Keep explicit library persistence separate from `SettingsStore`; imports do
   not auto-apply, loads do not rewrite preferences, and edits never auto-save.
9. Keep the library collapsed when not managed and preserve the accepted board,
   NEXT/HOLD, piece controls, basis/slice, Fit, full, and compact hierarchy.
10. Add focused tests and record bounded production-window save/load/A-B/
    delete/import/export evidence.

## Forbidden Changes

- New presentation parameters, themes or built-in style packs, palette-role
  editing, theme authoring, marketplace/sharing/cloud/account synchronization;
- gameplay/setup/replay/profile-preset semantics, current camera pose, exact
  basis, active slice, native state, queue/RNG, Ghost truth, NEXT/HOLD, score,
  collision, hash, or trace changes;
- using named profiles as shell-settings persistence or inventing Set as Default;
- storing Designer open/collapse/scroll/A-B state, gameplay/session fields,
  screenshots, hashes, absolute machine paths, or transient camera state;
- an index/database, display-name-derived paths, silent overwrite, partial
  import/application, automatic save prompts, or Designer auto-save;
- cockpit enlargement, right-inspector growth, board shrinkage, camera-fit,
  slice-set, geometry, controls/remapping, or unrelated review cleanup;
- reset, rebase, predecessor amendment, push, PR, or publication.

## Acceptance Criteria

1. All eight lifecycle operations work through one explicit library owner.
2. Artifacts are portable, deterministic enough to review, versioned, and
   contain every and only authoritative presentation values plus library
   identity/name metadata.
3. Display names are validated case-insensitively for uniqueness and never
   participate in storage paths; stable IDs survive rename and duplicates gain
   new IDs.
4. Corrupt artifacts are isolated; unsupported or invalid imports and failed
   writes leave library, B, A, runtime presentation, settings, and gameplay
   unchanged.
5. Designer edits, resets, A/B switching, Factory Defaults, Keep B & Hide,
   collapse, and hide perform zero library writes.
6. Save As persists working B; explicit Save updates only the selected stable
   profile; loading replaces/displays detached B and leaves A unchanged.
7. Editing loaded B or a duplicate does not mutate any stored source; rename
   preserves identity/values; delete preserves currently active detached B.
8. Dirty state depends only on semantic B-versus-baseline values.
9. Export/import round-trip preserves asymmetric representative values across
   board, piece, Ghost, slice-set, HUD/environment, and accessibility owners.
10. Current/future schema policy, unknown/missing policy, types, bounds, enums,
    finite values, name/path attacks, and storage failures have focused tests.
11. 2D/3D/4D application remains registry-driven, and settings, gameplay hash/
    snapshot, camera pose, basis/slice, Ghost semantics, NEXT/HOLD, geometry,
    and cockpit controls remain unchanged.
12. The library is collapsed by default and full/compact Designer remain usable
    without changing the accepted cockpit allocation.
13. Focused tests, canonical Godot suite, pinned Godot 4.7.1, settings/storage,
    governance/generated-doc, semantic-boundary, sanitation, diff, and one full
    repository gate pass.
14. Bounded agent-driven production-window evidence covers Save As, visible
    restoration on load, A/B, detached delete, and an actual export/import path.
15. Documentation names the new artifact owner without transferring parameter
    semantic authority; one coherent local commit leaves a clean worktree.

## Verification and Explicit Deferrals

Run focused library/Designer tests first, then the canonical Godot suite,
pinned Godot 4.7.1 gate, settings externalization, project-contract,
generated-maintenance/configuration, semantic-boundary, sanitation, and diff
checks, followed by one final full repository gate. A bounded visual campaign
is sufficient because the library is collapsible and does not alter board or
inspector geometry.

Predefined/built-in theme profiles, theme packs/authoring, procedural
backgrounds, sharing/cloud/telemetry/recommendations, startup/default profile
selection, gameplay presets, new parameters, remapping, and all camera/geometry/
slice/cockpit follow-ons remain deferred.

---

# Task Contract — Stage 54F-2R.1 Bounded Cockpit Review Cleanup

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Starting branch: `codex/canonical-local-board-geometry`

Starting SHA: `d77aca9a3a7556d6e4db71ba47af24894e75e5ad`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Close exactly two non-blocking P2 findings from the independent reviewed-green
Stage 54F-2R review: explicitly hide the live Reset View action after returning
to replay, and make the 4D W/slice translation row consume reachable semantic
compaction metadata instead of a dead display-string matcher. Do not reopen the
accepted cockpit, Designer, camera, input, or gameplay architecture.

## Classification and Authority Comparison

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer` because one existing Godot input-contract
  provider projection is consumed by the live HUD presentation and verified at
  the mode-transition integration boundary.
- Affected layers: live/replay HUD visibility lifecycle, authoritative input-
  contract presentation descriptors, passive compact-control rendering,
  focused Godot integration tests, and bounded acceptance/status documents.
- Claims: Reset View is deterministically live-only across replay -> live ->
  replay; X/Z/W compact presentation uses authoritative semantic descriptors;
  existing bindings, action applicability, hierarchy, Designer behavior, and
  deterministic gameplay remain unchanged.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `integration`, `deterministic`, and bounded `human_visual` inspection.
- Full repository gate: required by the supplied post-review correction brief.

Existing authorities already define the solution boundary. `ReplayHud` owns
shell visibility and mode lifecycle. `LiveInputContract` owns action identity,
bindings, mode applicability, and control-frame labels; its new metadata is
only a query/presentation projection of those same items. `LivePieceControlStrip`
remains a passive consumer with no gameplay callbacks. The Stage 54F-2R
cockpit hierarchy, Designer contract, camera semantics, native state, exact
basis, canonical geometry, NEXT/HOLD, persistence, and deterministic identity
are consumed unchanged. No authority transfers.

## Scope Matrix

| Layer | Required correction | Evidence |
| --- | --- | --- |
| HUD lifecycle | Set Reset View visibility explicitly at both replay and live boundaries. | Actual-button replay -> live -> replay assertions plus neighbouring live-only surfaces. |
| Input presentation contract | Attach minimal direction and signed-axis semantics to existing movement items. | Exact 2D/3D/4D descriptor and binding assertions. |
| Passive strip | Render compact X/Z/W labels from metadata; remove translation label parsing. | Compact-output snapshot, exactly-once W/slice assertion, and no action/key inventory check. |
| Documentation | Record closure without changing reviewed-green parent status. | Contract, acceptance, backlog, and restart handoff checks. |

## Required Changes

1. `LiveResetViewButton.visible` is false in fresh replay, true in each live
   mode, and false again after live -> replay, independent of parent visibility
   or reparenting.
2. Existing movement items expose only the minimal semantic direction and
   signed-axis values required for compact display, including current 4D
   control-frame/basis semantics.
3. The strip renders horizontal, depth, and slice rows through that metadata;
   no translation display-string matching, action table, binding table, or
   gameplay callback remains or is introduced in the presentation consumer.
4. Focused tests cover lifecycle, 2D/3D exclusion, one compact 4D slice row,
   signed axes, authoritative keycaps, and passive behavior.
5. Only the four review-closure documents routed by the brief are reconciled.

## Forbidden Changes

- Reset/Fit/named-view/camera behavior; gameplay actions, bindings, remapping,
  native state, basis, geometry, deterministic identity, or input routing;
- cockpit/NEXT/HOLD/Designer/layout redesign, more 4D enlargement, Drop strip,
  profile/theme/Stage 54F-3/release work, or review-adjacent advisories;
- reset, rebase, amendment of the reviewed parent, push, PR, or publication.

## Acceptance Criteria

1. The actual Reset View button is hidden in fresh replay, visible in live 2D,
   3D, and 4D, and hidden after each return to replay; other live-only surfaces
   retain their lifecycle.
2. Reset behavior and all camera semantics are byte-for-byte unchanged outside
   visibility assignments.
3. Translation compaction uses semantic metadata, not display-string parsing.
4. 2D exposes one horizontal compact row and no slice row; 3D exposes
   horizontal/depth and no slice row; 4D exposes horizontal/depth/slice exactly
   once with correct current signed axes and authoritative bindings.
5. The W/slice row is compact and understandable, and the strip remains passive
   with no duplicate action, keybinding, applicability, or rotation inventory.
6. Stage 54F-2R hierarchy, board allocation, NEXT/HOLD, Fit, helper, full/
   compact Designer, input isolation, and deterministic state remain unchanged.
7. Focused tests, canonical Godot suite, pinned Godot 4.7.1, required
   governance/semantic/sanitation checks, and one full repository gate pass.
8. A bounded production-window inspection confirms the W row and replay-after-
   live state; a new full visual campaign is not required.
9. One local commit is created, the worktree is clean, and nothing is published.

## Verification and Deferrals

Run the focused cockpit/layout tests first; then the canonical Godot suite,
pinned 4.7.1 gate, supplied governance/hygiene checks, and one full verifier.
Reuse the reviewed Stage 54F-2R campaign for unchanged layout/input claims and
perform only a bounded production inspection of the two corrected states.

All Stage 54F-3 work, horizontal-letterboxing and Hard Drop advisories, profile
or theme work, new controls, remapping/touch, layout/camera/NEXT/HOLD/Designer
changes, native/basis/geometry work, release hardening, and independent human
acceptance remain explicitly deferred.

---

# Task Contract — Stage 54F-2R Gameplay Cockpit Density and Control Hierarchy

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Starting branch: `codex/canonical-local-board-geometry`

Starting SHA: `4c2dc44c89865193bf2022ffab822741feac1bdb`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Correct the accepted Stage 54F-2 cockpit's three bounded visual defects: make
the default Live 4D slice collection materially larger, make native NEXT and
HOLD compact glanceable state, and keep mode-applicable piece translation and
rotation vocabulary permanently visible above secondary camera guidance. Keep
the registry-driven Designer, detached A/B semantics, input and persistence
isolation, canonical local-board geometry, exact basis, native NEXT/HOLD,
helper ownership, and deterministic gameplay unchanged.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`.
- Affected layers: Godot live cockpit allocation and hierarchy, shared
  NEXT/HOLD presentation geometry, authoritative live-input presentation,
  bounded fit policy, layout/input integration tests, focused real-window
  evidence, and governing documents.
- Claims: materially larger default Live 4D presentation; compact simultaneous
  NEXT/HOLD; always-visible authority-derived piece guidance; subordinate but
  available camera guidance; responsive Designer coexistence; and unchanged
  gameplay, input, persistence, geometry, basis, and native preview authority.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `deterministic`, `integration`, and `human_visual`.
- Full repository gate: required because this is a reviewer-requested
  correction to shared live HUD layout, input-facing guidance, and visible
  presentation framing.

## Current Authority and Design Comparison

- `godot_vector_arcade_cockpit_overhaul.md` makes the board primary and keeps
  the ordinary cockpit a filtered consumer of `LiveInputContract`; this stage
  strengthens that hierarchy without creating new commands or bindings.
- `next_piece_preview.md` and `authoritative_hold.md` retain native gameplay
  identity and the shared `PieceThumbnailModel` / `PieceThumbnail` rendering
  path. Compactness changes only panel geometry and HUD placement.
- `live_presentation_designer.md` retains registry generation, detached A/B,
  non-persistence, and bounded full/compact/hidden overlay semantics. Designer
  state does not become a gameplay-layout or camera authority.
- `camera_gui_preset_semantics.md` and
  `4d_presentation_interaction_architecture.md` retain the decomposition
  `local geometry -> slice layout -> collection bounds -> fit`. Any bounded
  framing refinement must continue to consume authoritative collection bounds
  and must not add a mode translation offset or merge layout with camera pose.
- Canonical local-board geometry, exact `BasisState`, native session/queue/Hold,
  Ghost truth, deterministic identity, and persistence owners are consumed
  unchanged. This task transfers no authority.

## Pre-change Production Allocation Record

The production scene was inspected in Live 2D, Live 3D, and Live 4D with the
Designer hidden, full, and compact. Requested 960x720, 1440x900, and 1600x960
windows all use the project's fixed 1600x960 logical canvas and scale that
canvas to the physical window, so the normalized allocation is invariant;
real-window captures remain required for physical-size readability.

At the 1600x960 logical canvas before correction:

| Surface | Baseline allocation |
| --- | --- |
| body | `(12,159) 1576x789` |
| game area | `(12,159) 1298x789`, 82.4% of body width |
| gameplay viewport | `(36,210) 1250x714`, 71.8% of body area |
| right inspector | `(1320,159) 268x789`, 17.0% of body width |
| top live action stack | 96 px high inside the 159 px top allocation |
| NEXT, Live 4D | 260x240 |
| HOLD, Live 4D | 260x212 |
| NEXT + HOLD | 452 px before gaps; separate full-width cards |
| basis panel | begins at y=635; 260x200 |
| detailed 4D helper | begins at y=877; 260x895, below the initial fold |
| standard camera detail | hidden; View Actions / Fit / Reset remain promoted in the top stack |
| Designer full | `(20,167) 420x773`, board overlay only |
| Designer compact | `(20,167) 493x63`, board overlay only |

The default fitted 4D authoritative collection envelope projects to about
342x541 inside the 1250x714 gameplay viewport: 27.3% of viewport width, 75.8%
of viewport height, and 20.7% of viewport area. The fit is height-limited by
the tall collection envelope; widening the already-dominant board region alone
cannot materially enlarge it. The root cause is therefore both allocation and
framing: a tall top stack removes useful vertical board space, while the
existing 1.32 Live-4D fit margin leaves excessive recovery clearance around an
already authoritative collection envelope. Layout allocation is corrected
first; any fit-policy refinement follows and remains bounds-derived.

## Scope Matrix

| Layer | Required change | Provider evidence | Consumer evidence |
| --- | --- | --- | --- |
| Cockpit allocation | Compress the top live action stack and prioritize permanent inspector content. | Ratio/rect layout contract and responsive tests. | Larger gameplay viewport and fold-safe primary guidance. |
| NEXT/HOLD | Apply one compact shared geometry convention and one side-by-side cockpit region while retaining the shared thumbnail path. | Model/renderer identity and panel geometry tests. | Simultaneous readable previews with reduced combined footprint. |
| Piece guidance | Select movement/rotation groups inside `LiveInputContract` via metadata on the existing groups; render compact symbols, authoritative labels, and bindings. | 2D/3D/4D group and binding tests. | One always-visible passive surface without input capture or duplicate action inventory. |
| Camera hierarchy | Keep Fit readily discoverable; place view actions/gestures/reset below piece and basis guidance with details progressive. | Semantic order/reachability tests. | Camera remains available but visibly secondary. |
| Framing | After allocation correction, refine only the existing bounds-derived Live-4D fit clearance if needed. | Camera projected-bounds containment tests. | Default cells/slices become materially larger without manual zoom. |
| Designer/input | Preserve overlay bounds and Stage 54F-2 pointer/keyboard isolation. | Full/compact layout and input regression tests. | Board, NEXT, HOLD, and piece guidance remain visible during tuning. |
| Documentation | Reconcile hierarchy, evidence, programme, backlog, and restart handoff. | Governance/document checks. | Durable authorities and deferrals remain unambiguous. |

## Required Changes

1. Reduce top live cockpit height before changing camera fit, and keep the
   gameplay viewport the dominant live surface at supported sizes.
2. Present NEXT and HOLD together using one compact geometry convention while
   retaining exact native identities and the existing shared thumbnail model
   and renderer.
3. Add one passive, always-visible piece-control surface generated from the
   existing `LiveInputContract` movement and rotation groups. Show actual
   bindings, directional category symbolism, and exact rotation-plane labels
   applicable to 2D, 3D, or 4D.
4. Keep Fit readily visible; move named view actions, reset, gestures, and
   optional numeric camera detail below piece guidance and 4D basis/slice
   state. Keep detailed prose in the existing helper.
5. Preserve the full and compact Designer overlays and all Stage 54F-2 input,
   persistence, deterministic, and presentation-authority isolation.
6. If allocation alone is insufficient, refine only the established Live-4D
   bounds-derived fit margin and prove the authoritative envelope remains
   inside the viewport across supported aspect ratios.

## Forbidden Changes

- named profiles, profile persistence/import/export, themes, new presentation
  parameters, telemetry, or a general cockpit redesign;
- new gameplay actions, bindings, remapping, clickable piece-command UI, or a
  parallel input/action inventory;
- native gameplay, queue/randomizer/Hold, Ghost truth, snapshots/hashes,
  deterministic state, replay/session identity, or settings writes;
- canonical board geometry, slice-set identity/layout ownership, exact basis,
  topology, or native/presentation authority transfer;
- mode-specific camera translation offsets or fit constants that bypass
  authoritative collection bounds;
- push, rebase, reset, prior-commit amendment, pull request, or publication.

## Acceptance Criteria

1. The default Live 4D collection is materially larger and immediately legible
   without manual zoom; authoritative bounds remain wholly framed.
2. Layout allocation is corrected before the bounded framing refinement, and
   the gameplay viewport retains the documented minimum body share.
3. NEXT and HOLD are simultaneous, non-overlapping, wholly inside the
   inspector, compact, labelled, and recognizable at supported viewport and
   accessibility scales.
4. NEXT/HOLD preserve native authority and one shared thumbnail model,
   renderer, palette, and compact geometry convention.
5. One passive surface permanently shows mode-applicable translation and
   rotation vocabulary, exact current bindings, and 4D plane labels without
   inspector scrolling.
6. The permanent surface consumes `LiveInputContract` groups and introduces no
   second action/binding/mode-applicability inventory or gameplay input path.
7. 2D omits 3D/4D planes; 3D shows XY/XZ/YZ; 4D shows
   XY/XZ/YZ/XW/YW/ZW and applicable X/Z/W translations.
8. Piece guidance appears before and is more prominent than camera guidance;
   Fit remains easy to locate and all existing camera functions remain
   reachable.
9. The contextual helper remains available for detailed semantics while
   primary piece vocabulary requires no helper scrolling.
10. At requested 960x720 and 1440x900 windows and the normal 1600x960 logical
    desktop, the board, NEXT, HOLD, and piece surface survive without clipping;
    wrapping stays inside the inspector at supported UI/accessibility scales.
11. Full Designer preserves judgeable board, NEXT, HOLD, and piece guidance;
    compact Designer preserves the near-normal cockpit.
12. Slider, SpinBox, scroll, orbit, pan, zoom, hard drop, Hold, translation,
    and rotation routing retain Stage 54F-2 isolation and deterministic state.
13. Focused tests, canonical Godot tests, pinned Godot 4.7.1, governance,
    semantic-boundary, sanitation, and full repository verification pass.
14. Agent-driven production-window 2D/3D/4D normal, 4D full/compact Designer,
    and constrained-window evidence explicitly answers all five visual
    questions Yes; independent human review is not claimed without a human.
15. One local correction commit is produced, no publication occurs, and the
    final worktree is clean.

## Verification Plan

- focused `LiveInputContract`, compact preview, cockpit layout, camera fit,
  Designer coexistence, and live input/deterministic integration tests;
- canonical Godot test runner plus pinned Godot 4.7.1 verification;
- governance, generated maintenance/config, semantic-boundary, sanitation,
  diff, and `CODEX_MODE=1 ./scripts/verify.sh` full gate;
- production Godot 4.7.1 real-window captures for Live 2D, 3D, 4D normal,
  Live 4D Designer full/compact, and approximately 960x720 constrained use.

## Explicit Deferrals

- named/persistent profiles, import/export, themes, new parameters/actions,
  control remapping, touch controls, topology/challenge work, release
  hardening, independent human acceptance, and all Stage 54G work.

---

# Task Contract — Stage 54F-2 Live Presentation Designer

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Starting branch: `codex/canonical-local-board-geometry`

Starting SHA: `32e9d2a9e8f431693761a25ba6cd9736419ab4bf`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Add a registry-driven, live Presentation Designer to the Godot product shell.
The Designer edits only a detached working `PresentationProfile`, previews it
through `TraceReplayApp.apply_presentation_profile()`, compares an immutable A
reference with working B, and supplies deterministic parameter/group/profile
resets. It must not persist values or alter gameplay, replay identity, camera
pose, board geometry, NEXT/HOLD state, or helper/status reachability.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`.
- Affected layers: presentation registry/profile consumption, Godot HUD and
  application preview seam, input/layout ownership, scene tests, focused
  real-window evidence, and governing documents.
- Claims: registry-complete live controls; detached and non-persistent B state;
  immutable A comparison; bounded live apply; deterministic reset semantics;
  responsive full/compact/hidden presentation; and gameplay/input isolation.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `deterministic`, `integration`, and `human_visual`.
- Full repository gate: required because a registry-wide visible product
  surface, shared HUD input boundary, and application presentation seam are in
  scope.

## Current Authority and Design Comparison

- `presentation_parameter_contract.md` keeps the registry as the sole owner of
  parameter identity, type, bounds/options, defaults, semantic owner,
  persistence class, and runtime applicability. The Designer generates rows
  from that metadata and declares no parallel parameter list.
- `PresentationProfile` remains the detached typed value carrier.
  `SettingsStore` remains the only persistence writer; the Designer receives
  neither a store nor a save callback.
- `TraceReplayApp.apply_presentation_profile()` remains the single bounded
  preview seam. Designer UI and rows do not write renderers, cameras, geometry,
  gameplay state, replay state, or settings directly.
- `visual_system_contract.md`, `live_hud_cockpit_architecture.md`, and
  `accessibility_contract.md` retain product-shell layout and input ownership.
  Full Designer mode owns interactive input; compact/hidden modes release
  gameplay keys while their own pointer hit area remains isolated.
- `next_piece_preview_contract.md` remains NEXT authority. HOLD is already
  established native authority under `AE-0055`; NEXT, HOLD, helper/status, and
  the board therefore remain simultaneous viewability constraints, not future
  placeholders.
- Canonical local-board geometry, exact 4D basis, slice layout, gameplay,
  session, and replay authorities are consumed unchanged. This task transfers
  no authority.

## Registry Inventory and Live Exposure Decision

The runtime-applicability metadata decides exposure. Every applicable entry is
generated and editable; every non-applicable entry is omitted from the live
surface. `ui_visible` is not an exclusion because this is the explicit
developer-facing presentation surface, while `applies_at_runtime` is the
authoritative safety boundary.

| Registry parameter | Type / owner | Live modes | Designer decision and refresh class |
| --- | --- | --- | --- |
| `display.window_mode` | enum / shell | none | Hidden; shell/window transition is inappropriate during live play. |
| `display.windowed_size` | size / shell | none | Hidden; shell/window transition is inappropriate during live play. |
| `display.ui_scale` | enum / shell | 2D/3D/4D | Editable; bounded shell/HUD relayout. |
| `display.hud_density` | enum / hud | 2D/3D/4D | Editable; bounded HUD relayout. |
| `display.board_detail` | enum / board | 2D/3D/4D | Editable; renderer refresh. |
| `ghost.enabled` | bool / ghost | 2D/3D/4D | Editable; renderer refresh. |
| `settled_cells.opacity` | float / board | 2D/3D/4D | Editable; renderer refresh. |
| `display.grid_visible` | bool / board | 2D/3D/4D | Editable; renderer refresh. |
| `board.grid_opacity` | float / board | 2D/3D/4D | Editable; renderer refresh. |
| `board.boundary_opacity` | float / board | 2D/3D/4D | Editable; renderer refresh. |
| `active_cells.opacity` | float / piece | 2D/3D/4D | Editable; renderer refresh. |
| `ghost.opacity` | float / ghost | 2D/3D/4D | Editable; renderer refresh. |
| `slice_set.spacing` | float / slice | 4D | Editable only in 4D; slice-layout refresh. |
| `environment.background_intensity` | float / environment | 2D/3D/4D | Editable; environment refresh. |
| `replay.playback_speed` | float / replay | none | Hidden; replay-only and inappropriate for live play. |
| `replay.loop_enabled` | bool / replay | none | Hidden; replay-only and inappropriate for live play. |
| `display.show_w_labels` | bool / slice | 4D | Editable only in 4D; renderer/HUD refresh. |
| `display.projection_strength` | float / camera | none | Hidden; replay-only and inappropriate for live play. |
| `theme.name` | enum / palette | 2D/3D/4D | Editable; theme and renderer refresh. |
| `accessibility.high_contrast` | bool / accessibility | 2D/3D/4D | Editable; theme and renderer refresh. |
| `accessibility.reduced_motion` | bool / accessibility | 2D/3D/4D | Editable; renderer motion-policy refresh. |
| `accessibility.show_help_hints` | bool / accessibility | 2D/3D/4D | Editable; HUD/helper relayout. |
| `camera.sensitivity` | enum / camera | 3D/4D | Editable only in 3D/4D; preference update without pose mutation. |
| `camera.invert_y` | bool / camera | 3D/4D | Editable only in 3D/4D; preference update without pose mutation. |
| `diagnostics.show_layout_bounds` | bool / diagnostics | none | Hidden; shell/replay diagnostics are not live-applicable. |
| `interface.show_onboarding` | bool / guidance | 2D/3D/4D | Editable; HUD/helper relayout. |

Current live-applicable registry types are boolean, float, and enum. The
control factory remains type-driven; no speculative colour control or setting
is introduced.

## Scope Matrix

| Layer | Required change | Provider evidence | Consumer evidence |
| --- | --- | --- | --- |
| Designer component | Generate owner groups and typed controls from registry metadata; hold opening/reference/working detached profiles. | Registry-count/type/range/option and reset unit tests. | HUD embeds one component without a parallel parameter table. |
| Preview seam | Relay A/B/edit/reset previews through the existing app apply method. | Signal and detached-profile tests. | HUD, renderer, environment, camera preferences, and shell consume one profile snapshot. |
| Persistence/gameplay | Never receive/write `SettingsStore`; preserve deterministic game/session/replay/camera-pose state. | Store snapshot/save-count and deterministic before/after assertions. | Live preview changes presentation only. |
| Layout/input | Full, compact, and hidden states with bounded panel/strip geometry and pointer/focus isolation. | Responsive layout and synthetic input tests. | Board, NEXT, HOLD, helper/status stay visible or immediately reachable; gameplay recovers in compact/hidden states. |
| Documentation | Record authority, reset/baseline semantics, evidence, and Stage 54G preservation. | Governance and generated-document checks. | Programme, backlog, architecture, and restart state agree. |

## Required Changes

1. Add a reusable registry-driven Designer component grouped by existing
   `semantic_owner`, with boolean, numeric slider-plus-exact-value, and enum
   controls, per-parameter reset, per-owner reset, and whole-profile reset.
2. Capture an immutable opening baseline and detached B profile. Capture A only
   by explicit user action; A/B selection and compact mode must expose an
   accessible textual state.
3. Define reset semantics exactly: parameter/group/`Reset B` restore opening
   values; `Factory defaults` constructs a detached registry-default profile;
   `Revert & Hide` restores the opening profile; hiding/collapsing otherwise
   preserves A, B, and the currently previewed slot.
4. Preview every edit/toggle/reset through
   `TraceReplayApp.apply_presentation_profile()` and retain one detached active
   profile in the HUD. Do not call `SettingsStore` or renderer/camera/gameplay
   consumers directly.
5. Provide responsive full, compact, and hidden states. Full mode owns keyboard
   input; compact/hidden release gameplay input; Designer pointer hits never
   leak to camera/gameplay handling.
6. Preserve board visibility and existing right-inspector reachability for
   NEXT, HOLD, helper, and status content across 2D/3D/4D and supported window
   and UI-scale conditions.

## Forbidden Changes

- setting persistence, profile naming/import/export, telemetry, undo history,
  speculative parameters, colour settings, or general-purpose editor scope;
- gameplay/session/native/replay state, snapshots, hashes, input semantics,
  queue/RNG, scoring, pieces, Ghost truth, NEXT/HOLD truth, or authority;
- canonical board geometry, exact 4D basis, slice semantics, camera pose, or
  renderer-local parameter ownership;
- weakening runtime applicability, deterministic identity, sanitation, tests,
  explicit deferrals, or the existing Stage 54G programme history;
- push, force operation, pull-request creation, or publication.

## Acceptance Criteria

1. Controls, groups, defaults, validation, options, and live visibility derive
   from registry metadata; a registry mutation is reflected without editing a
   Designer parameter list.
2. All and only live-applicable parameters are editable in each of 2D, 3D, and
   4D, with exact numeric input paired to sliders.
3. B is detached and non-persistent; edits leave store values/save count,
   gameplay snapshot/hash, replay identity, board basis/geometry, and camera
   pose unchanged unless the edited registry preference explicitly owns a
   presentation refresh.
4. A is immutable after capture. A/B buttons and toggle produce exact,
   repeatable profile snapshots and plainly announce the displayed slot.
5. Parameter/group/profile resets use the documented opening baseline;
   factory defaults and revert-and-hide have distinct deterministic semantics.
6. Full, compact, hide, reopen, and resize/UI-scale transitions preserve
   working/reference state. Compact and hidden modes restore ordinary gameplay
   controls; all Designer pointer input remains isolated.
7. The board plus NEXT and HOLD are simultaneously viewable, and helper/status
   content remains visible or immediately scroll-reachable, at supported 2D,
   3D, 4D, window-size, HUD-density, and UI-scale combinations.
8. Focused component/integration/deterministic/input/layout tests, governance
   checks, sanitation, pinned Godot 4.7.1, full repository verification, and
   real-window 2D/3D/4D full/compact/A/B evidence pass.
9. Governing documents agree, Stage 54G history is preserved, one local commit
   contains the stage, and the final worktree is clean.

## Verification Plan

- focused registry/control-generation, A/B, reset, persistence isolation,
  app-preview, deterministic invariance, input, and responsive-layout tests;
- project-contract, settings externalization, generated maintenance/config,
  semantic-boundary, sanitation, and diff checks;
- pinned Godot 4.7.1 and `CODEX_MODE=1 ./scripts/verify.sh`;
- agent-driven real-window screenshots in 2D, 3D, and 4D covering full,
  compact, and A/B states, with board/NEXT/HOLD/helper observations recorded.

## Explicit Deferrals

- named/saved profiles, persistence, import/export, undo/redo, telemetry,
  advanced colour authoring, and general-purpose scene/editor tooling;
- independent human acceptance and all Stage 54G work.

---

# Task Contract — Stage 54F-1R Geometry Review Corrections

Status: COMPLETE / REVIEWED GREEN

Starting branch: `codex/canonical-local-board-geometry`

Starting SHA: `d85605966ef9eb145f969a3d8e6550563c45b268`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Preserve the Stage 54F-1 canonical local-board architecture while correcting
the review regression caused by routing continuous endgame presentation points
through the strict lattice-cell API. Keep one geometry owner with separate
discrete-cell and continuous-affine domains, route the production particle and
event-marker path through the continuous domain, make slice layout consume the
canonical local extent, and replace tautological slice-isolation evidence.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`.
- Affected layers: canonical Godot presentation geometry, coordinate mapping,
  slice-set layout consumption, endgame renderer integration, Godot tests,
  focused real-window evidence, and governing documents.
- Claims: distinct strict-cell and finite continuous-point domains over one
  affine formula; restored 2D/3D fractional and out-of-board effects;
  non-degenerate interpolation/trails and marker following; canonical-extent
  layout ownership; meaningful slice isolation; strict cell preservation; and
  unchanged deterministic and 4D basis authority.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `deterministic`, `integration`, and `human_visual`.
- Full repository gate: required because this corrects a reviewer-reported P1
  in a shared presentation construction path and reconciles its acceptance.

## Current Authority and Design Comparison

- `docs/architecture/canonical_local_board_presentation_geometry.md` already
  assigns pitch, centering, Y inversion, local extent, cells, grids, and bounds
  to `LocalBoardPresentationGeometry`. The correction adds a second input
  domain to that owner; it does not restore mapper- or renderer-local math.
- `docs/architecture/game_safe_4d_slice_basis.md` continues to own exact signed
  4D coordinate conversion. Its integral validation is pre-existing and is not
  weakened or reinterpreted as a fractional basis contract here.
- `docs/architecture/4d_presentation_interaction_architecture.md` retains
  `B -> G_D -> L -> anchor -> view`. Canonical local extent remains an input to
  downstream adaptive layout; slice spacing remains outside local geometry.
- `docs/architecture/presentation_parameter_contract.md` continues to own the
  slice-spacing multiplier. No cell-pitch preference or profile parameter is
  introduced.
- `docs/architecture/authority_map.md` already assigns this new presentation
  geometry to Godot. The correction transfers and establishes no authority.

## Scope Matrix

| Layer | Required change | Provider evidence | Consumer evidence |
| --- | --- | --- | --- |
| Canonical geometry | Keep strict `cell_position()` and add a finite continuous affine point API using identical pitch/centering/orientation. | Exact integral equivalence, fractional/out-of-board, malformed, NaN, and infinity tests. | Mapper consumes the continuous API; locked/active/Ghost remain strict. |
| Mapper/layout | Route presentation points through canonical continuous geometry and pass canonical X/Y extent to adaptive layout. | Mapper/layout snapshots and structural source assertion. | Renderer positions and slice anchors use the corrected outputs. |
| Endgame renderer | Preserve extraction and rendering flow while restoring fractional particles, interpolation/trails, and event markers. | Committed 2D/3D fixture values and independently derived exact expectations. | Production `TraceSceneRenderer` nodes occupy distinct affine positions. |
| Isolation | Replace repeated access to one geometry object with independently configured same-local/different-slice states. | Structural snapshot equality across differing slice counts/layouts. | Exact 4D basis and deterministic suites remain unchanged and green. |
| Documentation | Record the correction history and evidence without recasting the canonical architecture as failed. | Governance/document checks. | Acceptance, backlog, authority, and restart status agree. |

## Required Changes

1. Preserve `cell_position()` as an integral, in-board lattice API with the
   existing above-board active-Y policy. Add a separate API for arbitrary
   finite three-axis presentation points; malformed or non-finite input must
   fail safely without contaminating transforms.
2. Share exactly one canonical affine implementation so every valid integral
   cell maps identically through both public domains.
3. Keep cells on the strict path and route `TraceCoordinateMapper` continuous
   presentation points through the new API. Fix the confirmed 2D/3D endgame
   regression without broadening Stage 54C fractional 4D semantics.
4. Configure `AdaptiveLayerLayout` from canonical `local_extent.x/y`, retaining
   its existing adaptive algorithm and the profile-owned spacing multiplier.
5. Add production-path exact-value regressions for real committed 2D and 3D
   fractional points, a finite out-of-board point, distinct particles,
   interpolation/trail movement, and event-marker offset composition.
6. Replace the slice-isolation self-comparison with independently configured
   states that share visible local dimensions but differ in slice count and
   layout state.

## Forbidden Changes

- gameplay coordinates/dimensions, native/session state, snapshots, hashes,
  replay identity, queue/RNG, collision, gravity, scoring, pieces, Hold,
  Ghost truth, or topology validity;
- exact Stage 54C basis laws or fractional signed-axis basis invention;
- separate 2D/3D/4D local geometry, mapper/renderer centering formulas,
  duplicated pitch, configurable cell size, or slice layout inside geometry;
- Stage 54E-4 profile ownership, camera/view lifecycle, Designer Lab, themes,
  unrelated cleanup, push, or pull-request creation.

## Acceptance Criteria

1. Canonical geometry remains the sole local-board mathematics owner with
   explicitly separate discrete-cell and continuous-point domains.
2. Both APIs share pitch, centering, and orientation, and agree for every valid
   integral coordinate covered by the focused suite.
3. Real fractional 2D and 3D fixture points plus finite out-of-board points map
   affinely rather than to the origin.
4. Production particles remain distinct; interpolation/trails move; event
   markers equal mapped particle positions plus the authorized local offset.
5. Locked, active, and Ghost cells retain strict lattice validation, including
   the existing above-board active-Y exception only.
6. Exact 4D basis authority, 2D semantic rank, deterministic identity, and
   presentation-profile ownership remain unchanged.
7. Independently configured slice states prove local-geometry isolation.
8. Adaptive layout consumes canonical local extent without changing its
   algorithm or absorbing slice spacing into geometry.
9. Focused Godot, governance, sanitation, pinned Godot 4.7.1, full repository,
   and agent-driven focused real-window 2D/3D checks pass.
10. Acceptance/status documents tell the correction history accurately and
    the final committed worktree is clean.

## Verification Plan

- focused canonical geometry, mapper, renderer, particle/trail, exact-basis,
  deterministic-isolation, and profile tests;
- project-contract, settings externalization, generated maintenance/config,
  semantic-boundary, sanitation, and diff checks;
- the pinned Godot 4.7.1 gate and `CODEX_MODE=1 ./scripts/verify.sh`;
- agent-driven real-window 2D and 3D endgame inspection with particle,
  interpolation/trail, marker, and ordinary-board observations recorded.

## Explicit Deferrals

- fractional 4D basis semantics beyond the existing exact Stage 54C contract;
- independent human acceptance, the full prior 13-image visual campaign, and
  unrelated Stage 54F-2 or later presentation work.

---

# Prior Contract — Canonical Local Board Presentation Geometry

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Starting branch: `codex/presentation-parameter-contract`

Starting SHA: `addd0d194f8fb53f57daf03e8b48ca4dd07ee6d4`

Implementation branch: `codex/canonical-local-board-geometry`

## Objective

Establish one canonical `LocalBoardPresentationGeometry` for the geometry of a
single displayed board volume. Adapt semantic 2D `[X,Y]` to presentation-only
`[X,Y,1]`, consume semantic 3D extents directly, and derive 4D slice-local
extents and signed coordinate orientation from the exact `SliceBasis4D`.
Migrate cells, centering, grid subdivisions, outer boundaries, and relevant
active/Ghost/locked placement without changing gameplay identity, exact-basis
laws, camera framing, presentation-profile ownership, or 4D slice-set layout.

This is Stage 54F-1, delivered as bounded internal slices 54F-1a contract,
54F-1b renderer migration, and 54F-1c cleanup/acceptance. They are one
architectural change and one local commit, not separate long-lived systems.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`.
- Affected layers: Godot presentation geometry, exact-basis dimensional
  adaptation, coordinate mapping, cell/grid/boundary rendering, Godot tests,
  real-window acceptance evidence, and governing documents.
- Claims: exactly-one local-board geometry owner; presentation-only degenerate
  2D depth; exact signed-basis 4D adaptation; unified centering, cells, grids,
  and boundaries; deterministic isolation; and retained presentation-profile
  compatibility.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `deterministic`, `integration`, and `human_visual`.
- Full repository gate: required because a shared presentation construction
  path, exact-basis consumer, visible product behavior, and architecture
  contract are all in scope.

## Current Authority and Design Comparison

- `docs/architecture/topology_aware_board_extent_contract.md` remains the sole
  owner of valid semantic board extents. Presentation consumes validated
  extents and does not establish gameplay minima, maxima, or topology rules.
- `docs/architecture/game_safe_4d_slice_basis.md` owns the exact signed 4D
  basis, coordinate reversal, and gravity-preserving `+Y` slot. The geometry
  receives its visible axis mapping from that owner and never invents or
  persists basis semantics.
- `docs/architecture/4d_presentation_interaction_architecture.md` owns the
  `B -> G_D -> L -> anchor -> view` composition. This task makes `G_D` an
  explicit canonical geometry and leaves `L`, slice anchors, adaptive slice-set
  layout, and camera framing as separate downstream transforms.
- `docs/architecture/presentation_parameter_contract.md` owns tweakable style
  values. Geometry supplies mathematical structure; it is not another profile
  registry and does not absorb opacity, materials, camera, or accessibility.
- `docs/architecture/authority_map.md` already assigns board rendering and new
  presentation semantics to Godot. This task formalizes an owner within that
  existing authority and performs no gameplay authority transfer or separate
  authority-establishment event.

## Audited Divergence Table

| Concern | Current 2D owner/path | Current 3D owner/path | Current 4D owner/path | Shared? | Legitimate mode difference? | Migration action |
| --- | --- | --- | --- | --- | --- | --- |
| Dimensional adaptation | `TraceCoordinateMapper` implicitly supplies missing Z as size 1 | mapper copies XYZ | `SliceBasis4D.visible_dimensions()` supplies three visible extents | Yes | Basis decomposition is 4D-only | Make adapters explicit and construct one canonical geometry with authoritative axis mapping. |
| Coordinate-to-local position | mapper `centered_local_point()` with absent Z fallback | same mapper formula | exact basis coordinate then same mapper formula | Yes | Signed basis remap occurs before geometry | Delegate the sole affine conversion to canonical geometry. |
| Origin/centering/bounds | mapper `_axis_size()` and `local_slice_bounds()` | same implicit code | same implicit code per slice | Yes | None | Canonical geometry owns center, extent, cell bounds, and board bounds. |
| Cell physical envelope | flat `CellRenderer.setup()` plus `LIVE_CELL_DEPTH = 0.08` | full exterior cubic block | full exterior cubic block per slice | Yes | Material/facing treatment may differ | Use the canonical one-cell physical depth and shared cell pitch; retain mode-specific surface/material treatment only. |
| Locked/active/Ghost placement | `BoardPresentationModel -> ProjectionLayout -> mapper` | same | exact basis -> projection -> mapper -> slice anchor | Yes | Slice anchor and local orientation are 4D-only | Retain one placement chain and expose/test its canonical geometry input. |
| Grid subdivisions | `_add_flat_grid()` recomputes X/Y lines | `_add_boundary_face_grid()` recomputes six faces | same volumetric helper per slice | Yes | 2D may display one planar face; 3D/4D choose camera-relative rear faces | Canonical geometry returns face-grid segments; renderer only chooses visibility/material/offset. |
| Gravity floor lattice | absent | `_add_floor_lattice()` recomputes X/Z lines | same per slice | Underlying face geometry yes | Floor visibility/emphasis is 3D/4D presentation | Reuse canonical negative-Y face-grid segments with floor styling. |
| Outer boundary/active frame | `_add_outline_box()` manually derives 12 edges | same | same per slice | Yes | Active-slice frame is 4D-only styling | Canonical geometry returns the 12 boundary segments; renderer applies role/material/thickness. |
| Local orientation | identity | identity | `SliceLocalOrientation` applies `L` after local mapping | No | Yes, accepted 4D physical rotation | Keep downstream of canonical geometry. |
| Slice placement | none | none | `AdaptiveLayerLayout` anchors every slice | No | Yes, essential 4D slice-set composition | Keep separate; canonical geometry owns one slice only. |
| Camera/framing | planar product defaults | volumetric defaults | complete slice-set fit/envelope | No | Yes | Consume geometry bounds but retain existing camera owners. |

## Scope Matrix

| Layer | Required change | Provider evidence | Consumer evidence |
| --- | --- | --- | --- |
| Canonical geometry | Add a pure bounded value object for dimensions, axis mapping, pitch, extent, center, cell transforms/bounds, face-grid segments, and boundary segments. | Focused geometry tests over asymmetric and degenerate extents. | Mapper and grid renderer consume it without recomputing formulas. |
| Dimensional adapters | Adapt 2D to `[X,Y,1]`, 3D directly, and 4D through exact visible signed basis slots. | Adapter, permutation, and sign assertions. | Projection/cell placement and each 4D slice expose the same geometry snapshot. |
| Renderer | Replace flat/volumetric/floor/boundary construction formulas with canonical segment descriptors and use one-cell physical depth for 2D. | Structural node metadata/count tests. | Live 2D/3D/4D locked, active, Ghost, grid, frame, and boundary paths. |
| Isolation | Preserve gameplay setup/state/hash/replay/Ghost landing and Stage 54E-4 profile ownership. | Existing deterministic/profile suites plus targeted snapshots. | Same native session and canonical snapshot before/after presentation changes. |
| Documentation | Record the durable semantic/presentation dimensional split and owner boundaries. | Governance/document checks. | Programme, backlog, RDS/architecture, authority map, and handoff agree. |

## Required Changes

1. Add one canonical local-board presentation geometry with a unit cell pitch,
   one-cell non-zero degenerate extents, zero-centered board extent, canonical
   cell centers/bounds, face-grid segments, and twelve outer-boundary segments.
2. Make `TraceCoordinateMapper` the dimensional-adaptation seam only: it
   selects semantic extents/axis mapping, delegates local geometry, then composes
   4D slice anchors. Preserve exact-basis coordinate mapping ahead of geometry.
3. Make `GridRenderer` consume canonical grid/boundary descriptors for flat,
   volumetric, floor, ordinary-frame, and active-frame construction; retain
   mode-specific visibility, materials, camera-relative face selection, labels,
   and z-fighting offsets outside the geometry contract.
4. Remove the 2D thin-depth geometry distinction. Keep 2D visually planar
   through its existing camera/projection and material treatment, not a second
   local board geometry.
5. Prove structural equivalence for 2D `[X,Y]`, direct local `[X,Y,1]`, 3D
   `[X,Y,1]`, and a one-slice 4D basis-visible `[X,Y,1]`, without weakening
   gameplay validity rules.
6. Cover asymmetric odd/even/single-axis extents, every supported live basis
   exchange, negative signed axes, and slice-index isolation.

## Forbidden Changes

- gameplay coordinates, semantic dimension, board validity/topology, native
  schemas, deterministic identity, snapshots/hashes/replays, collision,
  clearing, gravity, scoring, RNG/queue, pieces, Hold, or Ghost landing truth;
- exact `SliceBasis4D` laws, slice-set layout/spacing/centering, current local
  orientation `L`, camera pose/projection/framing, Fit/Reset lifecycle, labels,
  HUD, or presentation-profile persistence/ownership;
- mode-specific compensating board offsets or retained parallel local-geometry
  paths hidden behind wrappers;
- Designer Lab, profiles/themes, telemetry, topology expansion, gameplay
  features, unrelated visual redesign, push, or PR creation.

## Acceptance Criteria

1. One geometry object owns dimensions, axis mapping, unit cell convention,
   extent, center, local cell mapping/bounds, grid segments, and boundary edges.
2. 2D `[X,Y]` becomes presentation-only `[X,Y,1]`; semantic setup remains 2D.
3. 3D consumes the same geometry directly; 4D uses exact visible basis axes and
   the same geometry per slice before orientation/anchor/layout.
4. Odd, even, asymmetric, and single-cell axes center without drift.
5. 2D/3D/4D degenerate local geometry snapshots are structurally equivalent;
   negative axes preserve extent and reverse authoritative coordinates.
6. Grid, floor lattice, boundary, and active frame derive from canonical
   segment descriptors; obsolete duplicate formulas are removed.
7. Locked, active, and Ghost presentation use the shared mapping and one-cell
   depth convention while retaining legitimate material differences.
8. Deterministic gameplay identity and Stage 54E-4 live parameters are
   unchanged and their existing suites remain green.
9. Agent-driven real-window acceptance covers requested default, asymmetric,
   narrow, W=1, multi-slice, permuted-basis, and signed-basis states and records
   controlled convergence evidence; independent human sign-off is not claimed.
10. Focused Godot, governance, sanitation, pinned Godot 4.7.1, and full
    repository checks pass; documentation is reconciled and the committed
    tracked worktree is clean.

## Verification Plan

- focused canonical geometry, coordinate mapper, renderer, exact basis,
  deterministic-isolation, and presentation-profile Godot tests;
- governance/documentation, settings externalization, semantic-boundary, and
  sanitation checks derived by policy;
- `GODOT_BIN=... ./scripts/verify_godot_4_7.sh`;
- agent-driven real-window scenarios and controlled dimensional comparison,
  with Godot/platform/setup/profile/screenshots/observations recorded; and
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Explicit Deferrals

- camera/framing redesign, material/theme redesign, Designer Lab, named
  profiles, procedural environments, topology/gameplay work, thumbnails that
  do not consume live board geometry, and unrelated release hardening;
- independent human visual review, which may follow the recorded agent-driven
  acceptance; and
- Stage 54F-2, limited to any separately contracted post-convergence visual
  polish identified by real-window acceptance rather than another geometry
  abstraction.

---

# Prior Contract — Presentation Parameter Contract Follow-on

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Starting branch: `codex/54g-release-hardening`

Starting SHA: `7d9d3872180905e67874329f8046f336744a348e`

Implementation branch: `codex/presentation-parameter-contract`

## Objective

Establish one explicit, typed, authoritative contract for tweakable Godot
presentation parameters on top of the locally accepted Stage 54E-4, Stage 54F,
Hold, and Stage 54G stack. Reuse the existing shell settings registry, guarded
settings store, semantic palette roles, presentation-space decomposition, and
renderer consumers. Make validated presentation profiles independently
applicable to a frozen game state without changing deterministic gameplay,
reopening accepted view semantics, or introducing a second settings/theme
architecture.

This task is a post-Stage-54 follow-on. It does not retroactively replace the
completed Stage 54E-4 camera/GUI preset contract and does not create Stage 54H.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`.
- Affected layers: declarative Godot settings metadata, presentation-profile
  composition, shell preference persistence, HUD/application propagation,
  renderer/material/layout consumers, Godot tests, and governing documents.
- Claims: typed and uniquely owned presentation parameters; default visual
  parity; bounded live profile application; settings-only persistence;
  deterministic/session/replay/hash isolation; palette-role reuse; and
  documented 3D/4D presentation divergence.
- Required evidence: `documentation`, `governance_structure`, `godot`,
  `deterministic`, `integration`, and `human_visual`.
- Full repository gate: required because the canonical settings declaration,
  persistence schema interpretation, shared rendering, and architecture
  authority are all in scope.

## Current Authority and Design Comparison

- `docs/design/godot_visual_system.md` already owns the semantic colour roles,
  accepted visual hierarchy, and accessibility composition. Palette roles stay
  in `config/shell_theme_palettes.json`; the parameter contract selects or
  modulates them and never creates renderer-local replacement colours.
- `docs/architecture/display_infrastructure.md` and
  `docs/architecture/godot_shell_settings_persistence.md` already make
  `config/shell_settings_registry.json` the declaration/default authority and
  `user://shell_settings.json` the sole preference store. This task extends
  that path rather than adding a profile document.
- `docs/architecture/accessibility_infrastructure.md` owns invariant versus
  preference behavior. Accessibility overrides compose with aesthetic values
  and retain final say over minimum legibility.
- `docs/architecture/4d_presentation_interaction_architecture.md` and
  `docs/architecture/camera_gui_preset_semantics.md` own `B`, shared `L`,
  anchor/layout, outer view/framing, Fit, Reset, and lifecycle. A presentation
  profile may tune safe layout spacing and camera preferences, but never stores
  or replaces current basis, pose, projection, focus, zoom, or preset-action
  state.
- `docs/architecture/authority_map.md` assigns rendering, camera, HUD,
  accessibility, and new presentation semantics to Godot. This task formalizes
  data and application ownership inside that existing authority; it performs
  no authority transfer or new-authority establishment.

## Scope Matrix

| Layer | Required change | Provider evidence | Consumer evidence |
| --- | --- | --- | --- |
| Registry/config | Add exactly-one semantic owner, accessibility classification, and runtime applicability to every presentation parameter; add the bounded initial envelope. | Registry/spec validation and policy-backed externalization check. | Profile and Settings tests consume the declared type/default/range/options only. |
| Profile/runtime | Add a detached, versioned `PresentationProfile` built from validated registry/store values with copy-on-override profile switching. | Profile integrity/default/override tests. | HUD/app expose one bounded live application entry point. |
| Persistence | Reuse schema-3 `user://shell_settings.json`; new keys default when absent and remain excluded from setup/session persistence. | Store round-trip/migration/whitelist tests. | Reopened settings reconstruct the same profile without gameplay fields. |
| Renderer/layout | Consume profile values for representative board, piece, Ghost, slice-set, palette, and environment properties. | Structural material/layout/property assertions. | 2D, 3D, 4D Standard, custom 4D, and W=1 render/app isolation tests. |
| Documentation | Define inventory, terminology, lifecycle, isolation, and 3D/4D investigation. | Documentation/governance checks. | Programme, backlog, authority map, visual system, persistence, and handoff agree. |

## Initial Parameter Envelope

Preserve every existing shell preference and classify it. Add only these
currently useful, presentation-only controls:

- board grid opacity and boundary opacity;
- active-piece fill opacity, retaining the existing locked-cell opacity;
- Ghost fill opacity, retaining the existing Ghost visibility preference;
- 4D slice-set spacing as a multiplier over accepted responsive layout;
- world-background intensity as a multiplier over the selected palette role.

Existing theme selection is the palette/profile identity seam. Existing UI
scale, HUD density, board/cell-outline emphasis, camera sensitivity/inversion,
high contrast, reduced motion, labels, replay presentation, diagnostics, and
guidance preferences are reconciled into the same ownership inventory. Direct
per-role colour editing, procedural environment motion, named profile-library
management, Designer Lab UI, and A/B assignment remain deferred.

## Required Changes

1. Extend the existing setting specification with required, validated
   `semantic_owner`, `accessibility_classification`, and
   `runtime_applicability` fields. Each parameter has one owner, one type, one
   default, one persistence policy, and valid bounds/options.
2. Add a versioned detached `PresentationProfile` value object. It accepts only
   known validated IDs, fills omitted values from the registry, returns safe
   copies, and produces new profiles for overrides rather than mutating a
   process-global theme.
3. Route live profile application through one explicit app entry point. It may
   refresh presentation geometry/materials and derived fit bounds; it may not
   construct, reset, command, or otherwise mutate a native session.
4. Make migrated renderer/layout values consume profile values. Registered
   defaults and ranges must not be duplicated in renderer code.
5. Keep the existing palette contract authoritative for semantic colours and
   keep High Contrast as a compositional accessibility override.
6. Retain the shell settings store as the sole disk owner. No presentation
   value may enter `canonical_session_setup()`, native state, snapshots, trace
   or replay identity, state hashes, queue/RNG, score, Hold, or Ghost landing
   truth.
7. Record whether observed 3D/4D divergence comes from shared local geometry,
   mode-specific materials, slice-set composition, and/or camera framing. Do
   not repair structural divergence with mode-specific profile constants.

## Forbidden Changes

- deterministic gameplay, native rules, board extent/topology, pieces,
  coordinates, legality, gravity, scoring, RNG/queue, Hold, clearing, replay,
  trace, hash, or snapshot semantics;
- current camera pose, `B`, `L`, outer view/framing, Fit/Reset lifecycle, or
  named view-action persistence;
- profile-specific board offsets, scales, camera hacks, or mode-specific
  geometry compensation for 3D/4D divergence;
- a second settings file, theme/palette framework, persistence writer, or
  presentation-global singleton;
- the full Designer Lab, named theme library, A/B assignment/telemetry,
  procedural Tron environment, or Stage 54 cockpit/view redesign;
- push, PR creation, or unrelated release/topology work.

## Acceptance Criteria

1. Every registry entry has a unique ID and exactly one known semantic owner,
   valid type/default/bounds/options, known persistence policy, accessibility
   classification, and non-empty valid runtime applicability.
2. A canonical default profile reproduces representative pre-change material,
   layout, palette, HUD, and camera-preference values structurally.
3. Representative board, piece, Ghost, slice-set, palette, and environment
   values update through one live profile application entry without restarting
   or replacing the native session.
4. Applying profile A and profile B to the same frozen snapshot leaves
   canonical setup, native snapshot/hash, board, active/next/Hold state,
   queue/RNG-observable state, score, basis semantics, and current camera pose
   unchanged; only presentation outputs differ.
5. Schema-1/2/3 preference files remain readable; new values default when
   absent; a round trip persists only registry-approved shell preferences; no
   presentation field appears in game setup or deterministic persistence.
6. Renderer consumers use the authoritative profile value for every migrated
   property and retain no independent range/default.
7. Focused mode coverage includes 2D, 3D, 4D Standard, custom 4D, and W=1.
8. The 3D/4D divergence investigation records common geometry and deliberate
   differences without adding compensating style hacks.
9. Focused Godot, settings-externalization, governance/documentation,
   sanitation, pinned Godot 4.7.1, full repository, and real-window checks pass
   or any environmental limitation is reported explicitly.
10. Programme, backlog, current-state, visual-system, persistence, authority,
    and documentation routing are reconciled; the tracked worktree is clean.

## Verification Plan

- focused profile/registry/store/renderer/layout/application Godot tests;
- `python tools/governance/check_godot_settings_externalization.py`;
- policy resolver and project/governance document checks;
- `git diff --check` and repository sanitation;
- `GODOT_BIN=... ./scripts/verify_godot_4_7.sh`;
- agent-driven real-window 2D/3D/4D/custom/W=1/default/live-modification
  inspection, explicitly not independent human sign-off; and
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Explicit Deferrals

- direct colour editors and arbitrary palette authoring;
- named presentation-profile save/load/library UI beyond the versioned runtime
  value object and existing settings persistence;
- Designer Lab, controlled experiment assignment, telemetry, and statistics;
- animated/procedural backgrounds and complete theme packs;
- canonical 3D/4D board-presentation geometry redesign if the recorded
  divergence proves structural; and
- all post-release backlog items unrelated to presentation parameters.

---

# Prior Contract — Stage 54G and Professional Core Game Closure

Status: COMPLETE / FINAL DOCUMENTATION AND GOVERNANCE CLOSURE

## Objective

Record the independent final blocker re-acceptance, close Stage 54G and the
Professional Core Game gate, preserve non-blocking findings, and identify the
accepted release candidate without changing runtime implementation or
established authority.

## Classification

- Primary task type: `product_planning`.
- Workflow modifiers: none.
- Affected layers: documentation and recorded release acceptance.
- Required evidence: `documentation` and `release_acceptance`.
- Full repository gate: required because this records the final release claim.

## Authority and Scope

- `docs/plans/professional_godot_game_programme.md` owns the gate.
- `docs/plans/stage_54g_release_acceptance.md` owns candidate evidence.
- `CURRENT_STATE.md`, `docs/BACKLOG.md`, and this contract own current handoff,
  deferrals, and task scope.
- Allowed changes are limited to authoritative status and release-history
  documentation. Runtime, packaging, tests, CI, and authority records are
  forbidden.

Authority effect: none. This task records acceptance of already-established
deterministic gameplay, `AE-0055` Hold authority, product-shell semantics, and
the frozen release candidate.

## Acceptance and Verification

1. Re-read the gate and confirm every formal prerequisite is complete.
2. Record `Stage 54G: COMPLETE / FINAL MANUAL RELEASE ACCEPTANCE PASSED`,
   `PROFESSIONAL_CORE_GAME_READY: YES`, and
   `FINAL HUMAN BLOCKER RE-ACCEPTANCE: PASS`.
3. Record the exact accepted candidate, signature limitations, and separation
   between product readiness and public macOS distribution readiness.
4. Preserve non-blocking post-release findings and close Stage 54 without
   creating Stage 54H or absorbing later product work.
5. Run the policy-routed documentation/governance checks, sanitation, and full
   repository gate; commit only documentation and leave a clean worktree.

## Explicit Deferrals

Topology gameplay, Explorer, challenge/campaign, simulation, broader
distribution, signing/notarization, and post-release UI polish begin under a
new contract and programme or stage.

---

# Prior Contract — Stage 54G Live Presentation Restoration Blocker

Status: COMPLETE / FINAL MANUAL RELEASE ACCEPTANCE PASSED

## Objective

Fix the single Stage 54G manual-acceptance blocker in which returning to the
Viewer through Main Menu, Advanced / Diagnostics, and Replay Demos leaves an
existing Live-4D session with no rendered board geometry. Restore a valid live
presentation through the app-owned lifecycle seam without changing native
gameplay, replay semantics, Fit/Reset semantics, or accepted presentation
architecture.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer`.
- Affected layers: Godot shell, replay/live navigation integration, visible
  product, and release acceptance.
- Required evidence: `godot`, `integration`, `human_visual`, `platform`, and
  `release_acceptance`.
- Full repository gate: required because this corrects a reproduced packaged
  release blocker on a shared live/replay navigation path.

## Current Authority

- `docs/architecture/camera_gui_preset_semantics.md` owns presentation-context
  teardown and canonical re-entry, composite Reset View, and framing-only Fit.
- `docs/architecture/4d_presentation_interaction_architecture.md` owns the
  separate Live-4D `B`, `L`, layout, and outer camera presentation state.
- `docs/architecture/authority_map.md` assigns live/replay presentation and
  camera ownership to Godot while native sessions retain gameplay authority.
- Native Hold, NEXT, Ghost, board, queue/RNG, and state hashes remain frozen.

Authority effect: none. This fix restores an accepted Godot lifecycle seam and
does not establish or transfer deterministic authority.

## Allowed Systems and Paths

- the app-owned live/replay navigation and presentation re-entry seam;
- the HUD Viewer request boundary needed to route navigation to that owner;
- executable Godot integration coverage for 2D, 3D, 4D, replay, native-state
  preservation, view lifecycle, and input/focus restoration;
- the owning lifecycle contract and bounded release/backlog evidence; and
- rebuilt current-platform release evidence.

## Forbidden Changes

- gameplay/session recreation as a way to hide the blank board;
- changes to native gameplay, Hold, NEXT, Ghost, RNG, queue, score, replay
  schema/content, relative controls, projection, or camera ownership;
- broadening Fit View into a repair/reset operation;
- calling composite Reset View as a hidden return-navigation workaround;
- preserving a noncanonical pose across Main Menu when E4 defines that exit as
  presentation-context destruction;
- pause-status UI work or any other non-blocking Stage 54G finding; and
- push, PR creation, or final acceptance declaration before independent human
  re-review.

## Acceptance Criteria

1. The original packaged-app Live-4D navigation failure is reproduced before
   implementation and classified against Live 2D and Live 3D.
2. Viewer navigation routes through the app lifecycle owner rather than
   exposing a stale live mode through a raw HUD screen switch.
3. Returning to retained live gameplay after Main Menu establishes the
   canonical mode presentation required by E4, with visible renderer bounds
   and geometry in 2D, 3D, and 4D.
4. Native bridge identity and state hash, active piece, Hold state and
   availability, NEXT, Ghost, score, and game-over state remain unchanged.
5. Fit remains framing-only; Reset remains the explicit composite canonical
   action and is not required for recovery.
6. Replay Viewer behavior, camera ownership, diagnostics, navigation, and
   input/focus behavior remain correct.
7. Focused lifecycle regression, pinned Godot 4.7.1, sanitation, keybinding,
   full repository, rebuilt package, and outside-tree real-app checks pass.
8. Stage 54G remains incomplete until the independent narrow human re-review
   passes; the recorded final verdict now satisfies this criterion.

## Explicit Deferrals

- the live pause badge continuing to display `[ RUNNING ]` is post-release
  polish and a separate task;
- minimum-window enforcement, HiDPI point-size behavior, small-width SPAWN
  ENTRY clipping, replay-list keyboard accessibility, window-position
  persistence, notarization, and mouse-only 3D camera coverage; and
- all unrelated Stage 54G polish and future features.

## Verification Evidence

- The pre-fix executable Godot 4.7.1 diagnostic reproduced cleared camera
  presentation in 2D and 3D and the blank-board failure only in 4D. In all
  modes the native bridge, native state hash, renderer owner, viewport, and
  camera node remained live; 4D alone had zero grid/cell instances and invalid
  bounds after the presentation teardown.
- The focused integration test was mutation-checked against the original
  implementation: it failed for the missing 2D/3D canonical re-entry and 4D
  session/bounds/geometry/canonical re-entry, then passed after the correction.
- Focused lifecycle, sanitation, keybinding/native, pinned Godot 4.7.1, and
  full repository gates pass.
- A rebuilt macOS Universal 2 app passed its integrated two-user outside-tree
  smoke. The exact packaged Live-4D path returned to visible board geometry
  without Fit, Reset, or Restart; post-return Hold input and actual 4D replay
  viewing also worked.
- Independent narrow human re-acceptance passed. Running and paused Live 4D,
  shared Live 2D/3D return, replay, immediate board visibility, retained native
  gameplay/HOLD/NEXT/Ghost coherence, restored input ownership, and clean
  runtime logs were accepted. Stage 54G is complete and
  `PROFESSIONAL_CORE_GAME_READY` is `YES`.

---

# Prior Contract — Stage 54G Release Hardening and Final Manual Acceptance

Status: IMPLEMENTED / READY FOR FINAL MANUAL RELEASE ACCEPTANCE

## Objective

Prove that the accepted Godot professional core game can be built, exported,
launched outside the source tree, recovered from clean and malformed user
state, and exercised through its supported release path without a known
professional-quality blocker. Preserve accepted gameplay and presentation
semantics, introduce no features, and close only concrete release defects.

## Classification

- Primary task type: `packaging_and_release`.
- Workflow modifier: `cross_layer`.
- Affected layers: documentation, governance, Godot, native,
  deterministic-state and conformance evidence, integration boundary, visible
  product, packaging, current platform, and release acceptance.
- Required evidence: `documentation`, `godot`, `native`, `deterministic`,
  `parity_or_conformance`, `integration`, `human_visual`, `packaging`,
  `platform`, `release_acceptance`, and `governance_structure`.
- Full repository gate: required because this stage makes a release claim
  across the Godot/native boundary and closes the Phase I product gate.

## Current Authority

- `docs/plans/professional_godot_game_programme.md` owns the Professional Core
  Game Gate and Stage 54G outcome.
- `docs/rds/RDS_PACKAGING.md` and `docs/RELEASE_CHECKLIST.md` own supported
  release-path requirements and must be reconciled with the accepted Godot
  product direction before completion.
- `docs/ARCHITECTURE_CONTRACT.md` and
  `docs/architecture/authority_map.md` own subsystem boundaries.
- `docs/architecture/authoritative_hold.md` and `AE-0055` own deterministic
  Hold; this stage performs release regression only.
- Existing view, controls, NEXT, Ghost, cockpit, and Stage 54F presentation
  authorities remain frozen unless a reproducible release regression is found.

Authority effect: none. Stage 54G establishes or transfers no deterministic
authority.

## Allowed Systems and Paths

- Godot export presets and narrowly required release/export scripts;
- native GDExtension build configuration and artifact-selection metadata;
- current release CI, packaging RDS/checklists, launch/build documentation,
  version metadata, and release evidence;
- focused automated seams for clean, persisted, malformed, and transient-state
  startup; export contents; outside-tree launch; and release regressions;
- programme, backlog, task contract, and restart handoff status; and
- a tiny presentation-only 4D polish correction only if direct comparison
  proves an obvious low-risk improvement.

## Required Changes

1. Establish the factual current versus development-only versus legacy release
   inventory, including supported targets, metadata, native artifacts, and CI.
2. Reconcile the supported Godot release path with any stale Python packaging
   claims without repairing obsolete packaging solely for historical parity.
3. Build the native extension, export the supported current-platform artifact,
   inspect its contents, and launch it outside the repository with isolated
   user data and no current-working-directory dependency.
4. Verify clean, persisted, and malformed settings/setup startup, including
   correct preference ownership and exclusion of transient view/gameplay/Hold
   state.
5. Run final 2D/3D/4D, Hold/NEXT/Ghost, replay, setup, Settings,
   accessibility, focus/modal, warning/error, resize, and performance sanity.
6. Run policy-routed focused, release-specific, sanitation, pinned Godot, and
   full repository gates.
7. Record release evidence and present the exported candidate for independent
   human acceptance before declaring Stage 54G or the programme gate complete.

## Forbidden Changes

- new gameplay, topology, Explorer, challenge, campaign, simulation,
  controller, audio, localisation, or migration features;
- deterministic gameplay semantics, queue/RNG, collision, scoring, piece
  definitions, projection, control-frame, replay schema, or persistence
  architecture changes absent a reproduced release blocker;
- accepted Reset/Fit/Restart lifecycle, relative controls, NEXT, Ghost, Hold,
  cockpit, #69/#70, setup, Settings, or Stage 54F visual redesign;
- speculative optimization or structural 4D rendering experimentation;
- treating agent-driven inspection as independent human acceptance; and
- push, pull-request creation, or unsupported-platform runtime claims.

## Acceptance Criteria

1. Every formal pre-54G programme prerequisite, including Stage 54F and
   `AE-0055`, remains complete.
2. Supported release targets and legacy paths are documented truthfully.
3. Two isolated clean-user launches and persisted/corrupt-state launches
   succeed with correct recovery and ownership.
4. Transient view and live gameplay state, including Hold, never persist as
   preferences; new sessions reconstruct canonical empty/available Hold.
5. Final 2D, 3D, 4D, Hold, NEXT/Ghost, replay, setup, Settings,
   accessibility, modal/input, resize, warning/error, and performance checks
   have no release blocker.
6. The current supported release path reproducibly builds and exports the
   correct native artifact and runtime resources.
7. The exported artifact launches and plays outside the source tree with
   isolated user data and no repository-relative dependency.
8. Cross-platform evidence is explicitly limited to static/configuration or CI
   evidence where the platform cannot run locally.
9. Sanitation, keybinding, native/conformance, pinned Godot 4.7.1, release
   checks, and `CODEX_MODE=1 ./scripts/verify.sh` pass.
10. An independent human accepts the exported release candidate matrix.
11. No known release blocker remains; unresolved observations are classified
    as non-blocking polish or future work.

## Automated Verification

- focused Godot startup, persistence, input, UI, replay, Hold/NEXT/Ghost,
  setup, accessibility, and release/export tests selected by the actual diff;
- clean native build and native/conformance/parity checks required by the
  packaged GDExtension boundary;
- `git diff --check`;
- `./scripts/check_git_sanitation_repo.sh`;
- `./scripts/check_keybinding_contract.sh`;
- project/governance and release-package validators;
- `GODOT_BIN=/path/to/Godot ./scripts/verify_godot_4_7.sh`; and
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

- Prefer the exported macOS artifact with isolated user data, launched outside
  the source tree.
- Exercise fresh startup; persisted preferences and transient-state reset;
  representative 2D, 3D, and 4D play; Hold lifecycle; NEXT/Ghost
  synchronization; Standard and High Contrast; constrained/normal/large
  windows; Settings and resets; replay; navigation and modal recovery; quit;
  and relaunch.
- Agent-driven real-window inspection may prepare evidence and diagnose
  defects but does not satisfy final independent human acceptance.

## Documentation Updates

- reconcile the packaging RDS, release checklist, installer/export guide,
  README, and platform/version claims with the factual supported path;
- record 54G evidence and cross-platform limitations;
- update the programme, backlog, this contract, and `CURRENT_STATE.md` with the
  final verified versus human-accepted state; and
- preserve completed Stage 54F, Hold, and architecture evidence.

## Explicit Deferrals

- signing/notarization and store distribution unless current policy already
  claims them as required for this gate;
- unsupported-platform runtime evidence unavailable on this machine;
- legacy Python installer repairs when that path is formally classified as
  retained legacy rather than the Godot professional-core release path;
- non-blocking standard-mode Live-4D legibility polish if no obvious local,
  low-risk improvement is demonstrably better; and
- all new features listed under Forbidden Changes.

---

# Prior Contract — Stage 54F Integrated Professional Playability and Visual Acceptance

Status: COMPLETE / HUMAN INTEGRATED PLAYABILITY ACCEPTED (2026-08-23)

## Objective

Make the accepted Godot 2D, 3D, and Live-4D product shell visually legible,
coherent, usable, and professionally presentable in actual play. Close the
known Stage 54F presentation and responsive-shell blockers without reopening
accepted gameplay, view, movement, NEXT, Ghost, cockpit, or persistence
semantics and without absorbing new features.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifiers: none.
- Affected layers: Godot presentation shell and governing documentation.
- Required evidence: `documentation`, `godot`, `integration`, and
  `human_visual`.
- Full repository gate: required because shared rendering, setup, Settings,
  accessibility, and integrated product-acceptance claims are in scope.

## Current Authority

- The relevant product RDS documents own durable behavior.
- `docs/architecture/4d_presentation_interaction_architecture.md` owns the
  accepted `B -> G_D -> L -> anchor/layout -> V/P` composition. Adaptive
  layout owns anchors, arrangement, gaps, and layout bounds.
- `docs/architecture/camera_gui_preset_semantics.md` owns Reset View, Fit View,
  lifecycle, flat 2D, and stateless named view actions.
- `docs/architecture/godot_vector_arcade_cockpit_overhaul.md` owns the accepted
  board-first cockpit hierarchy and progressive disclosure.
- The NEXT, Ghost, display, and accessibility architecture documents own their
  existing presentation/data boundaries, semantic roles, responsive
  scrolling/focus, contrast, motion, and non-colour cues.
- `docs/architecture/authority_map.md` assigns these presentation concerns to
  Godot/GDScript.

Authority effect: existing Godot presentation owners are refined. No
deterministic gameplay authority is transferred or established. Native rules,
topology, queue/RNG, collision, scoring, piece definitions, snapshots, hashes,
replay identity, and persistence schemas remain unchanged.

## Known Findings to Reproduce and Classify

1. Live-4D inter-slice spacing may visually fuse adjacent 3D volumes (#69).
2. Grid, inactive wireframe, active frame, Ghost, and piece strength may not
   express the required hierarchy (#70).
3. Each 4D W slice must perceptually read as a 3D board volume.
4. Invalid setup must be unmistakable in standard and High Contrast themes,
   including when the responsible section is collapsed.
5. Settings controls and both reset actions must remain reachable after
   Display Reset and at every supported constrained size.
6. 4D slice labels must communicate semantic slice membership without
   colliding with pieces, frames, neighbouring slices, or viewport edges.
7. View Actions must still look interactive while remaining stateless.
8. Above-board 2D spawn presentation must clarify the playable boundary
   without changing spawn rules or fabricating hidden cells.
9. Player-facing display setting names and applicability must match their
   actual runtime effects.

Every observed issue is classified as a 54F blocker, a 54G hardening item, a
new feature, or a correctness regression in an accepted subsystem. Correctness
regressions are diagnosed separately and are not masked by visual changes.

## Allowed Systems and Paths

- adaptive 4D slice-layout policy and structural tests;
- shared Godot board-rendering roles, depth cues, labels, theme palettes,
  accessibility derivatives, and focused tests;
- setup validation presentation and progressive-disclosure tests, without
  changing validation rules;
- Settings registry presentation metadata, generated panel scrolling/focus,
  applicability filtering, and responsive-layout tests;
- bounded HUD/control affordance corrections proven by current review;
- existing architecture/programme/backlog/handoff docs and before/after
  screenshots; and
- test-only seams needed to inspect layout/style state without pixel-diff
  acceptance.

## Required Changes

1. Capture and inspect a real-window baseline for 2D, 3D, 4D, setup,
   Settings, accessibility, HUD densities, and representative window sizes.
2. Route confirmed spacing through `AdaptiveLayerLayout`, preserving stable
   assignment, anchor-only composition, non-overlap, Fit bounds, resize, and
   deterministic output.
3. Express the required board hierarchy through shared semantic roles and
   render-state selection so active piece/Ghost dominate grid and frames while
   active board identity remains clear in standard and High Contrast modes.
4. Preserve volumetric depth cues for 3D and every 4D slice.
5. Place slice labels by a stable, camera-aware rule outside gameplay
   geometry, with a subtle readability treatment if required.
6. Make validation failure unmistakable with error text, theme role, field
   treatment, and collapsed-section indication; reapply runtime style changes.
7. Make Settings genuinely scrollable and focus-reachable at the supported
   minimum and after reset/resizing, including focus reveal for off-screen
   controls.
8. Correct only concrete setting applicability/naming defects, preserving IDs,
   persistence compatibility, and settings taxonomy.
9. Add executable structural evidence and record the final real-window review,
   accessibility result, performance sanity, and any 54G deferrals.

## Forbidden Changes

- deterministic gameplay, native sessions, queue/RNG, collision, scoring,
  topology, piece definitions, spawn rules, snapshots, hashes, or replay/trace
  schemas;
- movement/control-frame resolution or accepted relative-control semantics;
- camera projection policy, Reset/Fit/Restart lifecycle, view ownership, or
  named-preset identity;
- NEXT geometry/data construction or Ghost landing authority;
- E5 cockpit information-architecture redesign;
- Hold, campaign, topology gameplay, Explorer, a new renderer, a new control
  system, or other new features;
- viewport-coordinate rendering hacks, persisted transient layout pose,
  screenshot pixel diffs as the primary oracle, or per-frame node churn; and
- push or pull-request creation.

## Acceptance Criteria

1. Live 2D is intentional, simple, and clear about its board/spawn boundary.
2. Live 3D depth is readable without grid/wireframe noise dominating.
3. Every Live-4D W slice reads as a 3D volume and adjacent slices remain
   visibly separate but related.
4. Active piece and Ghost are the strongest gameplay content; active frame,
   inactive wireframe, and internal grid follow in that order.
5. Slice labels remain legible, semantically assigned, and unobtrusive.
6. NEXT remains visible, faithful, and prominent without competing with play.
7. The accepted cockpit, view actions, Fit/Reset, relative controls, and
   session actions retain their semantics and reachability.
8. Invalid setup is unmistakable locally and globally, including a hidden
   error in a collapsed section and High Contrast mode.
9. Settings scrolling reaches every control and both reset actions at the
   supported minimum; keyboard focus does not become stranded off-screen.
10. Exposed display setting names and applicability are truthful.
11. Compact, Standard, and Detailed HUD remain coherent across modes.
12. Larger UI scale, High Contrast, and Reduced Motion retain semantic
    hierarchy and label reachability.
13. No essential clipping, overlap, or obvious performance regression blocks
    play at the declared minimum, constrained, normal, and larger windows.
14. Focused checks, pinned Godot 4.7.1 verification, and the full gate pass.
15. Real DisplayServer review accepts integrated 2D, 3D, and 4D playability;
    otherwise the stage stops at ready-for-human-review status.

## Automated Verification

- focused layout, rendering-role, label, setup-validation, settings,
  accessibility, HUD, NEXT, Ghost, input, and view-lifecycle tests selected by
  the actual diff;
- `git diff --check`;
- `./scripts/check_git_sanitation_repo.sh`;
- `./scripts/check_keybinding_contract.sh`;
- routed documentation/governance checks;
- pinned Godot 4.7.1 verification; and
- `CODEX_MODE=1 ./scripts/verify.sh`.

Native, packaging, and platform checks are omitted unless their files become
legitimately in scope. No deterministic semantics change.

## Manual Verification

- Real Godot 4.7.1 window with fresh throwaway user state, not headless.
- 2D: play, spawn boundary, NEXT, Ghost, setup, invalid setup, constrained
  window, larger UI scale.
- 3D: canonical and rotated camera, depth, pieces/Ghost/NEXT, relative movement,
  cockpit, constrained window.
- 4D: simple and occupied boards, multi-W piece/Ghost, labels, HUD densities,
  constrained/normal/large windows, Fit/Reset, and representative board sizes.
- Settings: default, Display Reset, supported minimum, keyboard traversal,
  focus reveal, and both reset actions.
- Accessibility: High Contrast, larger UI scale, Reduced Motion sanity, and
  non-colour semantic cues.
- Capture representative before/after screenshots and inspect interaction, not
  screenshots alone.

## Documentation Updates

- extend existing presentation/cockpit architecture rather than creating a
  parallel visual authority;
- update the programme and backlog with closed 54F findings and bounded 54G
  deferrals;
- update this contract and `CURRENT_STATE.md` with final status; and
- preserve historical E3/E4/E5 evidence.

## Explicit Deferrals

- Stage 54D-3 Hold;
- non-blocking cosmetic/release polish classified for Stage 54G, including a
  modest standard-mode Live-4D volume-legibility pass that must preserve
  accepted slice/layout, projection, grid/wireframe hierarchy, control, and
  gameplay semantics;
- packaging, platform, controller, audio, localisation, and broader
  accessibility work; and
- every new gameplay, topology, Explorer, challenge, campaign, or simulation
  feature.

## Verification and Handoff Result

The Stage 54F candidate closes the reproduced implementation blockers and has
green focused Godot, sanitation, keybinding, project-contract, generated-doc,
pinned Godot 4.7.1, and full `CODEX_MODE=1 ./scripts/verify.sh` evidence.
Agent-driven real-DisplayServer review is green at the supported minimum,
constrained, normal, and larger window requests across the required 2D, 3D,
4D, setup, Settings, HUD-density, camera, and accessibility scenarios. The
durable evidence is
`docs/plans/stage_54f_integrated_visual_acceptance.md`.

The automated and agent-driven evidence was not independent human product
sign-off. Human integrated review subsequently accepted 2D, 3D, and 4D on
2026-08-23, so no Stage 54F gate remains. That review recorded slightly weaker
standard-mode Live-4D gamebox legibility than the equivalent 2D/3D boards as
non-blocking Stage 54G polish; the usable current presentation and strong High
Contrast alternative keep it outside the Stage 54F correctness and
architecture gates.

---

## Prior Contract — Stage 54E-5 Gameplay Cockpit Consolidation

Status: COMPLETE / HUMAN PRODUCT REVIEW ACCEPTED (2026-08-21)

## Objective

Make ordinary Live 2D, Live 3D, and Live 4D present a coherent gameplay
cockpit in which the board is primary and the player can immediately identify
game state, NEXT, mode-appropriate gameplay guidance, view actions, and
session actions. This is information-architecture and player-affordance work,
not a gameplay, camera, movement, NEXT, Ghost, or broad visual redesign.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifiers: none.
- Affected layers: Godot product shell and documentation.
- Required evidence: `documentation`, `godot`, `integration`, and
  `human_visual`.
- Full repository gate: required because the shared live/replay HUD and its
  product authorities change.

## Current Authority

- Godot owns live HUD layout, control presentation, input adaptation,
  guidance, accessibility, diagnostics, and camera/view presentation.
- `docs/architecture/camera_gui_preset_semantics.md` owns stateless named view
  actions, one composite Reset View, framing-only Fit View, mode canonical
  views, and view-preserving same-context Restart Game.
- `godot/Tet4D.Godot/scripts/input/live_input_contract.gd` owns public live
  action bindings and derives movement guidance from the app-supplied effective
  control-frame snapshot.
- `docs/architecture/next_piece_preview.md` owns the authoritative NEXT query,
  shared thumbnail, live-only placement, and replay exclusion.
- `docs/architecture/ghost_piece.md` owns authoritative Ghost presentation over
  the read-only landing query.
- `docs/architecture/godot_vector_arcade_cockpit_overhaul.md` owns the existing
  live/replay cockpit structure and is extended by the E5 decision record.

Authority effect: existing presentation owners are reused. No authority is
transferred or established.

## Cockpit Inventory Before Change

| Surface | Owner | Default live visibility | Interaction | Source / role | E5 finding |
| --- | --- | --- | --- | --- | --- |
| Replay/live/mode navigation buttons | `ReplayHud._build_layout()` | 2D/3D/4D | buttons | shell navigation | replay and alternate-mode chrome dominates ordinary play |
| `Show Quick Settings`, `Grid: On` | `ReplayHud._live_view_actions` | 2D/3D/4D | buttons | persisted HUD density and board-detail presentation | useful but visually promoted above gameplay/view recovery |
| `Bundle` / `TET4D` panel | `ReplayHud._top_status_panel` | 2D/3D/4D | passive | replay bundle status reused as product branding | redundant non-game information |
| `Live Session` summary | `ReplayHud.live_gameplay_summary_text()` | 2D/3D/4D | passive | native snapshot plus setup labels | truthful but overloaded with board, seed, piece set, score, queue, and feedback until it clips |
| running/paused/game-over badge | `ReplayHud._top_state_badge_label` | 2D/3D/4D | passive | live snapshot/state | essential and correctly prominent |
| `Restart Game` | `ReplayHud._restart_game_button` | game over only | button | existing reset signal / native session restart | semantic is correct but ordinary-play reachability is weak |
| `New Random Game` | `ReplayHud._new_random_game_button` | true-random setup only | button | session lifecycle | legitimate conditional session action |
| `Change Setup` | `ReplayHud._change_setup_button` | 2D/3D/4D | button | setup lifecycle | legitimate session action |
| `Authority` panel | `ReplayHud._authority_panel` | 2D/3D/4D | passive | implementation/ownership diagnostic | developer information promoted above gameplay |
| board and active/Ghost/locked cells | renderer plus `ReplayHud._game_area` | mode-owned | gameplay/camera pointer input | native snapshots and accepted Godot presentation owners | primary surface; unchanged |
| NEXT | `NextPiecePanel` in `_right_column` | 2D/3D/4D | passive | authoritative observational query | correct, readable, and retained before secondary guidance |
| `4D VIEW ROTATION` basis/axis panel | `ReplayHud._build_basis_panel()` | 4D only | exact view-action buttons | accepted signed-basis presentation and live input contract | legitimate 4D comprehension/action surface; action family wording needs clarification |
| grouped controls | `LiveInputContract.control_hint_groups()` rendered by `ReplayHud` | 2D/3D/4D | passive help | actual action contract plus effective control-frame snapshot | truthful; 2D is too dense and 4D repeats exact view actions already exposed as buttons |
| `INSPECTOR` session/status/view text | `ReplayHud._integrity_panel` | 2D/3D/4D | passive | native snapshot plus HUD formatting | duplicates top state and exposes engine/shell/topology/last-input diagnostics |
| bundle detail | `ReplayHud._bundle_detail_panel` | Detailed only | passive | replay bundle diagnostics | not ordinary live-game information |
| `VIEW` / `Camera` / `View Actions` | `ReplayHud._camera_panel` | 2D/3D/4D except Compact; menu hidden in 2D | stateless `MenuButton` plus passive status | camera preset action catalogue and numeric camera status | unreachable below long controls, empty/diagnostic in 2D, and menu needs explicit input ownership |
| diagnostics/events | `DiagnosticsPanel` / `EventListPanel` | replay only | passive | development diagnostics | already correctly hidden in live mode |
| Quick Settings panel | generated `SettingsPanel` | Detailed only | controls | persisted shell settings | valid progressive disclosure; remains secondary |
| hidden replay footer Reset/Fit/Reset Replay | `_bottom_panel` | replay only | buttons | replay/view/session signals | correct for replay, not a live affordance |
| onboarding | `LiveOnboardingPanel` | preference-controlled | dismiss button | accepted onboarding model | retained as optional guidance |

Ghost has no separate ordinary-play cockpit label. Its visibility preference is
already owned by Quick Settings/Settings and its rendered cells remain the
player-facing surface; E5 does not add a duplicate status.

## Allowed Systems and Paths

- shared Godot live/replay HUD composition and its layout snapshot;
- existing live control-contract presentation helpers, without changing
  bindings or command semantics;
- app-level input suppression while a cockpit popup owns interaction;
- focused Godot HUD/layout/input tests; and
- existing cockpit architecture, programme, backlog, and restart handoff.

## Required Changes

1. Replace live replay/developer chrome with clear `View` and `Session` action
   families while preserving replay layout when replay is active.
2. Keep Running/Paused/Game Over, score, clears, active piece, and speed in a
   concise live summary; leave NEXT to the authoritative thumbnail panel.
3. Hide live bundle/authority/session-diagnostic panels and preserve detailed
   observability through existing replay/Advanced Diagnostics surfaces.
4. Keep 2D minimal, show legitimate 3D camera guidance and stateless View
   Actions, and retain 4D movement/view distinction plus useful axis/slice cues.
5. Present Fit View, Reset View, and Restart Game as distinct reachable actions
   backed by their existing signals; do not invent universal key labels.
6. Remove conceptual duplicates from the ordinary cockpit by deriving a
   cockpit subset from the full shared input contract rather than creating a
   new binding table.
7. Make the View Actions popup explicitly own keyboard interaction while open
   so unhandled input cannot dispatch gameplay, then restore live capture when
   it closes.
8. Preserve the supported minimum, scrollable inspector, board dominance,
   NEXT placement, and replay behavior.

## Forbidden Changes

- deterministic gameplay, native sessions, queue/RNG, scoring, topology,
  movement/rotation/drop legality, replay/trace schemas, or persistence;
- control-frame resolution or any HUD-local yaw/quadrant resolver;
- camera/view/Reset/Fit/Restart semantics or persistent preset identity;
- NEXT geometry, queue data path, W grouping/placement, or normalization;
- Ghost landing/collision semantics or renderer authority;
- Hold, #69, #70, 4D volume redesign, board art, Settings-screen overflow,
  setup error colour, or other Stage 54F work; and
- push or pull-request creation.

## Acceptance Criteria

1. The board remains the dominant live surface and NEXT remains visible,
   readable, authoritative, and before secondary inspector content.
2. 2D exposes no named View Actions, camera diagnostics, 3D/4D orientation, or
   slice concepts.
3. 3D exposes truthful relative movement, piece rotation, camera gestures,
   stateless View Actions, and distinct recovery/session actions.
4. 4D exposes ordinary/W movement, piece rotation, exact re-slice actions,
   slice orientation/framing, and meaningful axis/slice cues without raw `B/L`
   or implementation terminology.
5. Reset View, Fit View, and Restart Game are distinct, visible, reachable, and
   retain their accepted semantics.
6. View Actions visibly read as actions and never expose selected/`Custom`
   identity after manual manipulation.
7. Cockpit movement labels continue to consume the effective translation
   snapshot and displayed bindings resolve through `LiveInputContract`.
8. Ordinary live mode hides bundle, authority, raw engine/shell/topology,
   numeric camera, and last-input diagnostics; existing diagnostic routes
   remain available.
9. Opening View Actions suppresses gameplay dispatch until the popup closes.
10. Compact/Standard/Detailed density retains critical state, gives Standard
    the intended ordinary cockpit, and keeps detailed settings secondary.
11. Supported default, smaller, and larger layouts keep essential actions and
    NEXT reachable without structural overlap; replay shared infrastructure is
    not regressed.
12. Focused Godot checks, pinned Godot verification, sanitation,
    documentation/governance checks, and the full gate pass.
13. Real-window 2D/3D/4D review accepts first-five-seconds hierarchy,
    dimensional progression, semantic distinctions, truthfulness, and
    supported-size composition.

## Automated Verification

- focused cockpit mode-visibility, grouping, action, responsive-layout, and
  popup-input-ownership tests;
- existing live input, control-frame, NEXT, Ghost, replay-layout, and menu
  routing tests affected by the shared HUD;
- `./scripts/check_keybinding_contract.sh`;
- `git diff --check`;
- `./scripts/check_git_sanitation_repo.sh`;
- routed governance/documentation checks;
- `GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot
  ./scripts/verify_godot_4_7.sh`;
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

- Capture before/after real-window evidence at the supported normal desktop
  size for Live 2D, Live 3D, and Live 4D.
- Exercise View Actions then manual view manipulation, Fit View, Reset View,
  Restart Game, pause, Change Setup, Main Menu, Quick Settings, and popup input
  ownership.
- Resize to the supported smaller window and a larger desktop window; sanity
  check replay when shared HUD structure changes.
- Do not infer human-visible acceptance from headless tests.

Acceptance record (2026-08-21): pinned Godot 4.7.1 real-window review accepted
Live 2D, Live 3D, and Live 4D at the normal desktop size, plus 960 x 640 and
1728 x 1000 window requests. The review exercised stateless named View Actions
followed by manual camera manipulation, Fit View, Reset View, Restart Game,
Change Setup, Main Menu, Quick Settings, and the View Actions popup. It
confirmed board-first hierarchy; prominent authoritative NEXT; intentionally
increasing 2D/3D/4D complexity; distinct View, Display, and Session families;
truthful relative guidance; and the absence of replay/developer diagnostics in
ordinary play. The popup was visibly inspected and executable dispatch tests
proved that gameplay input remains suppressed until it closes. Replay's
shared layout, diagnostics, NEXT/status, and view controls were regression-
checked by the focused executable suite. No E5 blocker remained.

## Documentation Updates

- extend the existing cockpit architecture with the E5 hierarchy and
  progressive-disclosure decisions;
- expand the E5 programme section and update `docs/BACKLOG.md`;
- update this task contract before implementation; and
- update `CURRENT_STATE.md` with final verified/reviewed status.

## Explicit Deferrals

- Stage 54D-3 Hold;
- Stage 54F #69 spacing, #70 grid/wireframe/active hierarchy, 4D volume
  readability, broad polish, Settings overflow, and setup-error colour;
- display-setting applicability/name findings carried from E4a unless a direct
  cockpit regression makes a minimal shared correction unavoidable; and
- replay-specific redesign beyond regression safety for shared components.

## Stage 54D-3 Authoritative Hold Completion

Stage 54D-3 is COMPLETE / DETERMINISTIC AUTHORITY ESTABLISHED / HUMAN VISIBLE
ACCEPTED under `AE-0055`. Its normative transition and boundary contract is
`docs/architecture/authoritative_hold.md`. Native live sessions own held-piece
identity, lifecycle legality, queue/RNG and canonical-spawn consequences,
snapshot fields, and deterministic hash participation. Godot owns one
edge-triggered `C` input affordance and HOLD presentation through the existing
thumbnail model/renderer. The fixed replay schema is unchanged; historical
fixtures remain compatible. This completion does not rewrite the historical
E5 deferral record above and does not authorize Stage 54G work in this batch.
