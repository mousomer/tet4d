# Stage 54F-3 Presentation Profile Library Acceptance

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Branch: `codex/canonical-local-board-geometry`

Starting HEAD: `5a2e648124ed4ea0f62003fd95fb3d8dca1a57f6`

Evidence owner: local agent-driven acceptance; no independent human sign-off is
claimed.

## Predecessor boundary

The starting branch was clean at the expected correction commit, had no
configured upstream, and preserved the unpublished Stage 54E/54F stack. Before
production edits, the exact committed predecessor passed:

```text
CODEX_MODE=1 ./scripts/verify.sh
verify: OK
```

No reset, rebase, merge, push, PR, or publication occurred.

## Implemented architecture

- `PresentationProfileLibrary` is the sole named-artifact lifecycle owner.
- Storage is one JSON artifact per generated 32-lowercase-hex stable ID under
  `user://presentation_profiles/`; display names never select paths.
- Listing derives from independently validated files, so one corrupt artifact
  is diagnosed/skipped without an index that can drift.
- Artifact schema 1 contains type/version, stable identity, validated display
  name, and the existing schema-1 `PresentationProfile.snapshot()`.
- Unknown IDs, invalid values, unsafe identities/names, and unsupported outer
  or profile versions reject before mutation. Current-schema missing values
  follow the existing profile contract and receive registry defaults.
- Temporary-write plus backup/install/restore replacement follows the existing
  shell-settings safety convention without writing `SettingsStore`.
- Save As and duplicate allocate new identities. Rename preserves identity and
  values. Delete removes only storage. Export preserves portable identity;
  import validates first and allocates a fresh local identity.

## Designer semantics

- The library surface is inside full Designer, collapsed by default, and does
  not change compact/hidden geometry.
- Save As and Save explicitly persist working B. A being displayed never
  changes the save target.
- Load creates/replaces detached B, displays B, applies it through the existing
  preview signal, and never recaptures or mutates A.
- Loaded/saved source state is visible; `*` means semantic B values differ from
  the stored/saved baseline.
- A/B display, camera motion, game advancement, collapse, scroll, hide, resets,
  Factory Defaults, and Keep B & Hide do not write or alter dirty state except
  when they semantically change B.
- Overwrite and delete are confirmation-backed. Delete leaves active detached
  B unchanged. Import does not auto-apply.

## Focused automated evidence

The focused Stage 54F-3, existing Designer, cockpit-density, and replay-layout
tests pass in Godot 4.7.1. They exercise the storage boundary directly and
cover:

- edit/A-B/compact/Keep B & Hide/reopen -> zero writes; explicit Save -> write;
- Save As while A is displayed -> exact working B values are stored;
- Save/load detachment and stored-source immutability after B edits;
- immutable A across load/toggle/edit sequences;
- duplicate identity/value independence; rename identity/value preservation;
- delete with detached B still active;
- malformed/root-shape/future-version/type/bound/enum/non-finite/unknown/
  missing/name/path cases and atomic failure;
- injected storage-write failure without partial mutation;
- isolated corrupted file and healthy listing;
- asymmetric board, piece, Ghost, slice-set, HUD/environment, and accessibility
  export/import round-trip;
- complete payload plus registry-driven 16/18/20 Live-2D/3D/4D applicability;
- settings, gameplay snapshot/setup/hash, exact basis/local orientation, camera
  pose, NEXT/HOLD identity, and cockpit-surface isolation.

## Production-window acceptance

Production Godot 4.7.1 Metal was run at the existing 1600x960 logical canvas
with an isolated user-data library and paused Live 4D for exact state evidence.
The agent drove the real production scene and UI handlers through:

1. capture immutable A;
2. Save As `Stage 54F3 Visual` from working B;
3. visibly reduce background/Ghost presentation and observe the `*` dirty mark;
4. load the saved profile and observe exact visual restoration/clean state;
5. toggle A then B without mutation;
6. export and import through the production file-dialog signal path;
7. confirm deletion of the loaded stored source while detached B stayed active.

Recorded results were all true: save succeeded; dirty-before-load; clean-after-
load; A unchanged; export file created; import produced a fresh stable ID and
`Stage 54F3 Visual Imported`; detached B survived delete; native state hash and
ordinary settings were unchanged; and NEXT, HOLD, piece controls, and basis
remained visible. Visual inspection confirmed the expanded library stayed
inside the existing 420px full Designer pane, the large 4D board remained
judgeable, and the established right-inspector hierarchy did not change.

The captures and machine-local export were temporary agent evidence and were
removed after inspection; no machine-local path or user artifact was committed.

## Verification findings and final gates

One bare canonical invocation inherited the host's existing ordinary shell
preference that hides onboarding, so later default-onboarding tests failed.
The repository-standard clean HOME/XDG user-data invocation passed. No user
preference was modified. This distinguishes environmental contamination from a
product or test failure.

The first pinned clean-copy run then found that `DirAccess.open("user://…")`
did not enumerate the created profile directory in that copied-project
environment even though file writes succeeded. Production and test cleanup now
enumerate the globalized absolute user-data directory, matching the existing
absolute create/remove boundary. Focused tests and the pinned gate passed after
that portability correction.

Final results:

- focused profile-library plus adjacent Designer/cockpit/replay regressions:
  PASS;
- canonical Godot suite in isolated user data: `Godot replay tests passed`;
- pinned Godot 4.7.1 engine/API/clean-copy gate: PASS;
- topology transport parity: 59 shared cases PASS;
- settings externalization: PASS;
- project-contract validation: 117 required paths PASS;
- generated maintenance/configuration checks: PASS;
- Godot semantic-boundary validation: 118 scripts PASS;
- repository sanitation and `git diff --check`: PASS;
- final `CODEX_MODE=1 ./scripts/verify.sh`: `verify: OK`.

The canonical/pinned logs retain established negative-path settings/setup
diagnostics and existing non-failing Godot teardown advisories. No new runtime
failure was accepted or bypassed.

## Stage 54F-3R post-review robustness closure

Status: COMPLETE / LOCAL AGENT-DRIVEN ROBUSTNESS GREEN

The reviewed-green Stage 54F-3 architecture remains accepted. Its bounded
54F-3R follow-up corrects four P2 implementation/evidence gaps without changing
profile semantics or authority:

- a shared Godot file-mechanics helper writes and flushes the sibling temp,
  checks `FileAccess.get_error()` before install, and lets an incomplete write
  cleanly fail without moving the current destination;
- profile and settings persistence remain separate owners, paths, schemas,
  counters, and diagnostics while reusing the same direct-replace, backup,
  retry, restore-rename, and restore-copy sequence;
- total profile restoration failure reports failure and retains the exact prior
  artifact at its explicit backup path; it never deletes the last valid copy or
  reports success;
- profile diagnostics are sorted current-scan state. Repeated snapshots over
  unchanged healthy/corrupt/stale storage are identical and do not accumulate
  duplicate corrupt-artifact messages;
- the production cockpit test compares the actual Live-4D gameplay viewport and
  full Designer rect with the library collapsed and expanded. Both remain equal,
  while NEXT, HOLD, piece controls, and basis/slice state remain visible.

Focused Godot 4.7.1 evidence passes for profile persistence, `SettingsStore`,
and cockpit hierarchy. It inspects persisted bytes/values and covers incomplete
overwrite, failed Save As and Designer state, rename restoration, copy fallback,
total restoration failure with retained backup, unrelated healthy listing,
three equal corrupt-storage snapshots, stable diagnostic count/content, stale
`.tmp`/`.bak` invisibility, and exact viewport allocation. Existing lifecycle
coverage continues to prove Save B while A is displayed, detached load, delete
with runtime B active, import without auto-apply, ordinary settings separation,
and gameplay/camera/basis/NEXT/HOLD isolation.

Completion evidence:

- focused profile, `SettingsStore`, and production cockpit suites: PASS;
- canonical Godot 4.7.1 suite in an isolated temporary project/user-data copy:
  `Godot replay tests passed.`;
- pinned Godot 4.7.1 gate: 59 topology transport cases and
  `Godot 4.7.1 verification passed.`;
- settings externalization, project-contract, generated maintenance/
  configuration, semantic-boundary (119 scripts), sanitation, and
  `git diff --check`: PASS;
- full `CODEX_MODE=1 ./scripts/verify.sh`: `verify: OK`;
- one production Live-4D real-window session: collapsed and expanded Profile
  Library states retained the same visible gameplay frame and full Designer
  allocation, with NEXT, HOLD, piece controls, 4D actions, and basis/slice
  labels visible.

Intentional negative-path persistence diagnostics and the repository's known
non-failing Godot teardown advisories remain visible in automated output; no
failure was bypassed. The production-window inspection is agent-driven, so no
independent human sign-off is claimed.

## Stage 54F-3R.1 independent-review corrections

Status: COMPLETE / LOCAL CORRECTION GREEN / INDEPENDENT RE-REVIEW PENDING

The independent Stage 54F-3R review confirmed the original four P2 findings
closed and identified three bounded follow-ups. The shared helper now captures
whether the destination existed before replacement and cleans a sibling backup
only for an existing-destination lifecycle. Actual profile export to a fresh
path preserves a pre-existing unrelated sibling `.bak` byte-for-byte, while
existing profile and settings replacement retains direct, backup/install,
restore-rename, restore-copy, and retained-recovery behavior.

Direct injected transition coverage now exercises absent-destination install
failure, existing-destination backup/install success, and stale-backup cleanup
failure. Cleanup failure after a successful install returns an explicit warning;
`PresentationProfileLibrary` preserves it, Designer status surfaces it, and
`SettingsStore` retains its existing warning diagnostic. Profile scan
diagnostics remain deterministic current-scan state rather than an operation
log.

The two Stage 54F-3R assertions that read a restored profile now validate the
load result and detached profile before calling `values()`. A scratch-copy
mutation that removed the expected restored artifact produced an ordinary
recorded failure and Godot exit 1, without a script error or false-green pass.
Focused helper, profile-library, settings, settings-integration, and cockpit
tests pass in Godot 4.7.1. The isolated canonical suite passes; the pinned clean-
copy gate passes engine/API checks, the canonical suite, 59 topology transport
cases, and Godot 4.7.1 verification. Settings externalization, 117-path project-
contract validation, generated maintenance/configuration checks, 120-script
semantic-boundary validation, sanitation, diff checks, and the full repository
gate pass. The bare host-user-data canonical invocation retains the documented
unrelated onboarding-preference contamination; intentional negative-path and
known non-failing teardown diagnostics remain visible.

This correction completes no visual-design comparison. Stages 54E-4 and
54F-1/2/3 provide the parameter, geometry, A/B, cockpit, and profile apparatus;
candidate creation, comparative evaluation, and default selection remain
separate future Stages 54F-4, 54F-5, and 54F-6.

Stage 54F-3 remains reviewed green. Stage 54F-3R is locally correction-green and
remains pending independent re-review; no human acceptance, push, or PR is
claimed.

## Explicit deferrals

No themes, built-in style pack, new parameters, palette editor, procedural
background, marketplace/sharing/cloud, default/startup profile, gameplay preset,
telemetry, remapping, camera/geometry/slice/cockpit change, or independent human
acceptance is included.

The recommended next bounded style stage is a read-only built-in-profile
catalog using this exact `PresentationProfile` payload and a small declarative
name/description/category layer. It should curate and review actual visual
styles without changing user-profile lifecycle, ordinary settings, parameter
semantics, or adding procedural/theme-authoring infrastructure.
