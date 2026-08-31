# Tet4D Open Work

Updated: 2026-08-30
Scope: active work, explicit deferrals, and acceptance boundaries only.

Completed detail is preserved in `docs/history/backlog_archive_2026-07-30.md`,
`docs/history/current_state_archive_2026-07-30.md`, and
`docs/history/DONE_SUMMARIES.md`.

## Current Authority

- Professional product programme and phase gates:
  `docs/plans/professional_godot_game_programme.md`
- Product behaviour: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Topology architecture and invariants:
  `docs/plans/topology_playground_current_authority.md`
- Subsystem authority: `docs/architecture/authority_map.md`
- Authority transfer and establishment:
  `docs/architecture/authority_transfer_protocol.md`
- Documentation routing: `docs/DOCUMENTATION_MAP.md`
- Workflow and change classes: `docs/WORKFLOW_CODEX.md`
- Machine governance: `config/project/policy_pack.json`

## Tracking Boundaries

This backlog tracks the active implementation slice, immediate accepted
follow-ups, and deferrals whose resolution depends on product evidence or an
authority decision.

It does not duplicate the complete programme roadmap.

GitHub issues are for independently actionable, user-visible or reproducible
bugs and their collaboration lifecycle.

## Active Work

Primary gate:

```text
PROFESSIONAL_CORE_GAME_READY
```

The first priority is a fully playable and professionally presented 4D Godot
game ready for later topology, Explorer, challenge, and simulation extensions.
The programme is owned by
`docs/plans/professional_godot_game_programme.md`.

Status: `PROFESSIONAL_CORE_GAME_READY: YES`. Stage 54G passed final manual
release acceptance, closing the Stage 54 Professional Core Game programme.
Future implementation starts as a new programme or stage rather than extending
54G; topology, Explorer, challenge/campaign, simulation, broader distribution,
and post-release polish remain outside this completed gate.

Completed bounded regression repair (2026-08-30): live active/locked exterior
faces now retain style alpha on a depth-stable structural path; Live-4D
left-drag matches the apparent Live-3D screen-direction convention with
invert-Y limited to vertical input; normal-gameplay pitch expands
asymmetrically from `-40` to `+80` degrees; slice anchors use one stable
geometry-derived envelope over that full orientation range; and Fit consumes
the renderer's effective scaled bounds with one modest framing margin. Focused
screen-projection, material, envelope, spacing, pitch, fit, idempotence, and
deterministic-isolation tests plus the pinned Godot 4.7.2 aggregate gate are
green. This repair changes presentation providers only: exact basis, gameplay,
native hashes, trace/replay identity, 2D/3D geometry, Ghost hierarchy, and
persistence remain unchanged. The governing refinement is recorded in
`docs/architecture/4d_presentation_interaction_architecture.md`; final
repository and real-window evidence is recorded in the current task contract
and completion report.

Completed bounded follow-on: the Presentation Parameter Contract is locally
accepted on `codex/presentation-parameter-contract`. It reuses the existing
registry, store, palettes, renderer, and 54E presentation spaces; it does not
reopen Stage 54 or change deterministic/native authority. Focused, pinned,
full-repository, and agent-driven real-window checks pass. The durable contract
is `docs/architecture/presentation_parameter_contract.md`, and the acceptance
record is `docs/plans/presentation_parameter_contract_acceptance.md`.

Completed bounded follow-on: Stage 54F-2 adds the Live Presentation Designer
on `codex/canonical-local-board-geometry`. It generates 16/18/20 applicable
Live-2D/3D/4D controls from the established registry and semantic owners,
edits a detached working B profile, captures immutable A, supports exact
numeric editing plus parameter/group/opening/factory resets, and previews only
through the existing bounded app seam. Full/compact/hidden layout preserves
the board and the existing right cockpit; NEXT and authoritative HOLD
(`AE-0055`) remain simultaneously viewable, while 4D basis and helper/status
content remain visible or immediately inspector-scroll-reachable. Focused,
input/layout, deterministic/store isolation, non-headless visual, pinned
Godot 4.7.1, and full-repository evidence is recorded in
`docs/plans/live_presentation_designer_acceptance.md`. No persistence,
gameplay, profile, registry, geometry, basis, NEXT, HOLD, or camera-pose
authority changes.

Completed bounded review correction: Stage 54F-2R makes the gameplay board the
dominant visual surface, presents native NEXT and HOLD as one compact shared-
thumbnail row, and keeps a passive `LiveInputContract`-derived translation and
rotation vocabulary permanently visible above secondary camera guidance. It
first recovers vertical board allocation, then narrows only the bounds-derived
Live-4D fit clearance. Fit remains readily available. Full/compact Designer,
input and persistence isolation, deterministic state, canonical geometry,
exact basis, helper authority, and native NEXT/HOLD authority are unchanged.
Focused, pinned/full, governance, deterministic/input, responsive-layout, and
production-window evidence is recorded in
`docs/plans/live_presentation_designer_acceptance.md`; independent human
acceptance remains unclaimed.

Completed bounded post-review cleanup: Stage 54F-2R.1 closes the two P2
advisories from the independent reviewed-green cockpit review. Reset View now
has explicit live-only visibility across replay -> live -> replay rather than
depending on its shared camera parent. X/Z/W translation rows now compact from
minimal direction/signed-axis metadata supplied by `LiveInputContract`, with
no HUD display-string parsing or duplicate action/binding inventory. The
reviewed Stage 54F-2R hierarchy, layout, Designer, camera behavior, gameplay,
and authority boundaries remain unchanged. Evidence is appended to
`docs/plans/live_presentation_designer_acceptance.md`.

Completed bounded follow-on: Stage 54F-4 ships the built-in style catalog on
`codex/built-in-style-catalog`, starting from
`1cb6e8db474d57832c0b715fd9bc5d57716aa354`. `BuiltInStyleCatalog` reads one
repository-shipped versioned JSON catalog through `res://`, never touches
`user://`, and exposes no write API, so read-only is structural rather than a
runtime flag. Applying a style replaces detached working B, leaves captured A and
the shipped entry unchanged, and clears the loaded user-profile identity so
explicit Save cannot overwrite a built-in; `Save As` and `Copy to User Library`
produce ordinary mutable user profiles. Six curated styles ship, one of which,
Tron Grid Flow, is genuinely animated. Three new `ENVIRONMENT_PRESENTATION`
registry parameters drive one bounded `AnimatedBackground` component confined to
the environment layer: screen-space pattern, no depth write, palette-derived
colour, damped frame centre, and a resettable component-local phase excluded from
every deterministic snapshot. `accessibility.reduced_motion` freezes it. Focused
catalog/animation/Designer/cockpit tests, canonical and pinned Godot 4.7.2,
governance/generated-doc/settings/semantic-boundary, sanitation, full-repository,
and production real-window evidence are green. The durable contract and evidence
are `docs/architecture/built_in_style_catalog.md` and
`docs/plans/built_in_style_catalog_acceptance.md`. This stage creates candidates
only; 54F-5 compares them and 54F-6 selects the default.

Completed implementation follow-on: Stage 54F-5 supplies the standalone Design
Laboratory on `codex/built-in-style-catalog`, starting from
`1edd764abd3ab04d44546f97be317bec1c4be57e`. It reuses the six shipped styles,
the canonical registry and apply seam, and the existing user profile library.
Ten versioned scenarios reconstruct existing fixed-seed native/replay truth for
2D/3D/4D, sparse/dense, NEXT/HOLD/Ghost, and topology review. Frozen A/B
sessions enforce one non-style fingerprint, exact `A -> B -> A`, deterministic
blind labels, canonical reset, and fail-closed drift detection. Replacement-safe
evaluations, viewport PNG pairs, immutable hashes/snapshots, explicit nomination,
three-file proposal export, and a read-only repository validator provide the
evidence/promotion path without selecting a default or mutating authority.

Completed integration correction (2026-08-31): comparison assignment was made
explicit before merge. One catalogue selector exposes `Apply Live`,
`Set as A`, and `Set as B`; frozen A/B slots and `shown_arm` are independent.
Showing, toggling, reset, blind mode, candidate edit/save, evaluation, and
capture never infer an assignment target. Focused session and production-panel
runtime tests cover reassignment while B is shown, repeated display changes,
reset, blind entry/exit, candidate isolation, snapshot restoration, and exact
provenance. The fresh final matrix for PR #75 was green at rewritten head
`9dfabd44` and it was squash-merged to master as `eb112dc2`. Its agent-driven real-window
check is recorded without claiming independent human sign-off.

The current Godot Windows x86_64 portable ZIP builds with a release
GDExtension, application identity/icon, shipped resources, no Python/editor
dependency, and structural/PE/path validation. The Windows CI lane runs focused
laboratory coverage and packaged-runtime startup when published. Local macOS
evidence does not claim Windows execution; clean-machine Windows and human
comparative design acceptance remain the explicit follow-ups in
`docs/plans/design_evaluation_laboratory_acceptance.md`. Stage 54F-6 default
selection/polish remains planned and must consume reviewed human evidence.
The exact locally validated ZIP was removed from the unmerged integration
branch's history while its source metadata and validator tests were retained.
Its original path and blob are unreachable from the rewritten branch. Future
Windows candidates must use Actions, release, or canonical release-candidate
asset storage outside normal Git history.

Active packaging proof (2026-08-31): Python/PyInstaller is restored as an
active, separately named product family. The existing macOS builder produced a
versioned arm64 DMG from integrated master; its mounted app launched from
outside the checkout with isolated user state. Actions run 33390087916 also
proved the Linux DEB end to end. Windows built and installed its MSI and printed
`runtime smoke check: OK`, but its GUI-subsystem process returned control before
the harness could inspect a process exit code. That first-run harness defect was
corrected before the final proof. Remote branch review deleted 22 content-proven
obsolete refs and retained `codex/explosion-architecture-inventory` for manual
inspection because it contains unique implementation changes and conflicts.

The corrected follow-up run 33392862609 was green for all three Python platform jobs
at exact master `d542d682`: macOS arm64 DMG, Linux amd64 DEB, and Windows x64
MSI each built, reported 0.7.5, launched outside the checkout, and completed
their mount/removal or install/uninstall checks. The release-unification gate
is open. The seven-artifact Python-plus-Designer workflow,
tag/project-version agreement check, and source-SHA/checksum manifest with
truthful iPadOS status are implemented and awaiting integrated CI plus a real
manual workflow-dispatch proof.

Integrated diagnostic run 33397993043 found two release-orchestration defects
before manifest assembly: cache-free direct Godot tests could not self-construct
`PresentationProfile`, and Windows split the 7-Zip output switch. The three
Python package proofs remained green. Narrow corrections and a fresh integrated
seven-artifact dispatch are now the release-unification blocker.

PR #79 corrected those two defects, had a green full exact-head matrix, and
merged as `38551bb2`. Follow-up integrated dispatch 33401278911 cleared the
cache-free tablet semantic boundary and retained three green Python packages,
but exposed one narrower orchestration defect shared by Android and iPadOS:
YAML folding plus an explicit shell continuation made each indented build-script
path a leading-space command name. Replace both steps with unambiguous block
commands, enforce that shape in packaging contracts, and rerun the complete
integrated workflow before closing the seven-artifact item.

The Windows job in the same dispatch subsequently completed its native build
and export, then the existing strict validator rejected the runner checkout
marker. Its disposable project copy had inherited ignored `.godot` state
created by the preceding direct Godot test. Windows, Android, and iPadOS must
all remove copied editor cache state before their isolated import/export; keep
the host-path rejection intact, cover the builder boundary with a regression
contract, and include the result in the same fresh integrated proof.

PR #80 had a green complete exact-head matrix and merged as `979b91c2`.
Follow-up integrated dispatch 33416903976 reached Android native compilation:
configuration and staged signing passed, but pinned `godot-cpp` requested NDK
`28.1.13356709` while the workflow had selected the runner's newest installed
NDK. Install and assert the binding-owned exact NDK version, add a packaging
contract for the pin, and rerun the complete gates before closing the unified
release item.

The iPadOS lane in that dispatch compiled its arm64 device archive, then stopped
because the build script asserted the declared release XCFramework without
assembling it. Compile the universal simulator archive as a distinct second
target, create the XCFramework from exactly the device and simulator archives,
cover the topology in the packaging contracts, and include it in the same
complete-gate and integrated-proof cycle.

Windows in the dispatch completed native compilation and export before the
strict validator found the runner checkout marker in `.godot` cache regenerated
during disposable-project import. Retain copied-cache removal and strict path
rejection, add `.godot/*` to the canonical exclusion filter for all four
Designer presets, cover the four-preset boundary, and include it in the same
proof cycle.

PR #81 had a green exact-head matrix and merged as `f8e70ca2`. Integrated
dispatch 33421053972 derived the correct binding-owned NDK version, but the
hosted image does not place `sdkmanager` on PATH. Resolve and assert the exact
command-line-tools executable under `$ANDROID_HOME`, install the pinned NDK
without a `yes` pipeline, retain the Clang assertion, and rerun the complete
gates before closing the unified release item.

Windows in dispatch 33421053972 still failed strict host-path validation after
cache isolation and preset exclusions were active. The same current package
passes from local MinGW, isolating the remaining hosted-runner exposure to
MSVC's embedded absolute PDB reference. Add `/PDBALTPATH:%_PDB%` to MSVC native
links, retain the existing compiler path maps, improve the validator to name the
offending ZIP member, and prove the correction through full PR and fresh
integrated release gates.

Android in dispatch 33426937123 cleared exact `sdkmanager`, NDK installation,
and Clang validation, then failed while archiving pinned `godot-cpp`: the POSIX
`ar` invocation exceeded the hosted process argument limit. Extend the existing
Linux SCons response-file `ARCOM` boundary to Android, cover the platform split,
and prove the APK through full PR and fresh integrated release gates.

PR #84 merged the Android response-file transport as `61437bd6`. Integrated
dispatch 33429888428 proved the response file is created and removed the old
argument-limit error, then stopped because the wrapper omitted `TEMPFILE`'s
compact display-string argument and SCons expanded the full archive command
into the CI log. Pass `ARCOMSTR` as the second argument and repeat the full PR
and integrated APK gates.

PR #85 merged bounded response-file logging as `ea9be00d`. Integrated dispatch
33433033740 completed Android archive, ranlib, native compilation, and arm64
shared linking, then found the clean disposable project lacks the ignored
native `bin` directory. Create that staging directory before copying the `.so`,
cover the order, and repeat full PR and integrated APK gates.

PR #86 merged explicit Android native staging as `b4498c27`. Integrated
dispatch 33436190052 then compiled and linked the arm64 GDExtension, exported,
aligned, signed, and verified the APK through Godot before the repository
validator rejected the absence of a conventional `.pck` ZIP member. Godot
4.7.2 intentionally stores Android project files individually under `assets/`
with `assets/assets.sparsepck` metadata. Align the validator and normative
packaging documentation with that exact upstream layout, retain required-asset
and path-hygiene checks, and repeat focused, full, PR, and integrated APK gates.

The iPadOS failure in integrated dispatch 33436190052 is the analogous clean
staging-directory boundary. The disposable project is copied before native
output creates the source project's ignored add-on `bin` directory. Without an
explicit destination directory, `cp -R` creates `bin` from the XCFramework's
contents and loses the `.xcframework` directory name, so Godot resolves no
library and `_export_additional_assets` returns file-not-found. Create the
staging directory before copying, assert command order, and validate the exact
nested framework path Godot emits in the Xcode project.

Windows dispatch 33439410913 again completed native compilation and Godot
export before strict validation attributed `\\a\\tet4d\\tet4d` solely to the
release GDExtension DLL. `/pathmap` and `/PDBALTPATH:%_PDB%` remain present, but
pinned godot-cpp defaults `debug_symbols=true` and therefore adds `/Zi` plus
`/DEBUG:FULL` even for `template_release`. A published portable DLL has no PDB
payload; explicitly pass `debug_symbols=no` only for the Windows release package,
preserve other build defaults and strict path checks, and prove the DLL on the
hosted MSVC runner.

Cross-platform enlargement (2026-08-30): the same Design Laboratory now also
targets Android tablets and iPadOS, both for landscape use with a physical
keyboard. One catalogue, one scenario system, one A/B implementation, one
evaluation schema, one nomination schema, and one repository-side validator
serve all three; platform reaches an exported bundle only as provenance. A
platform adapter boundary owns export transport, handheld safe-area insets, and
system Back behaviour, and nothing else.

Open follow-ups, in order of what unblocks the most:

1. Produce the Android APK on an equipped runner. The release-signing defect is
   corrected: the canonical preset stays credential-free while an ephemeral
   test key is injected into the staged release fields. The implementation host
   still lacks the Java SDK, Android SDK, and NDK that Godot 4.7.2 requires, so
   configuration proof is not reported as APK success.
2. Compile the iPadOS application. The build script and `macos-latest` CI job
   are complete; the implementation host has Command Line Tools but no Xcode
   and therefore no iPhoneOS SDK. The local configuration export is a distinct
   reduced-descriptor artifact class and has no release checksum.
3. Device acceptance on all three platforms, including real physical keyboard
   testing, background/resume, and on-device share/export. No emulator,
   simulator, device, or physical-keyboard evidence exists yet, and none is
   claimed.

Completed bounded regression repair (2026-08-29): direct game startup could retain an
ignored Godot `global_script_class_cache.cfg` from the preceding revision. The
new application-controller annotations then failed to resolve
`AnimatedBackground`, leaving a visible but unwired main menu whose options and
`Start Game` did nothing. The repair removes that generated-cache dependency,
adds cache-independent startup/menu regression evidence, and changes no style,
gameplay, persistence, or authority behavior. A direct stale-cache real-window
launch and the isolated pinned Godot 4.7.2 gate are green.

Completed bounded follow-on: Stage 54F-3 implements the explicit Presentation
Profile Library on `codex/canonical-local-board-geometry`. Named user profiles
use generated stable IDs and independently validated versioned files under
Godot user data. The lifecycle includes list, Save As, explicit Save, detached
load into B, duplicate, rename, confirmed delete, import, and export. The
existing registry/profile schema remains authoritative, ordinary settings are
not rewritten, and normal Designer edits remain runtime-only. Focused storage,
validation, Designer, 2D/3D/4D, cockpit, deterministic-isolation, canonical/
pinned Godot 4.7.1, settings/governance/semantic-boundary, sanitation, full-
repository, and bounded production-window evidence is green. The durable
contract and evidence are
`docs/architecture/presentation_profile_library.md` and
`docs/plans/presentation_profile_library_acceptance.md`.

Completed toolchain baseline upgrade: Stage 54F-3R.2 starts from
`e2e1ef9254f12c528ce7a67599b43510abfc0902` on the same unpublished branch. It
moves the pinned engine from `4.7.1-stable` to `4.7.2-stable`
(`4.7.2.stable.official.ed1daf0bf`), the newest published stable 4.7 patch,
under the existing selection rule with no governance amendment. The `godot-cpp`
binding is retained on proven extension-API equivalence. Only the project
target-version declaration and three version literals moved. Gameplay and
presentation are provably unchanged across engines by identical state hashes,
identical layout rects, and byte-identical rendered frames. Pinned Godot, native
build/tests, governance, generated-doc, settings, semantic-boundary, sanitation,
full-repository, and bounded macOS window evidence are green. Linux re-proof is
deferred to CI on publication and Windows packaging remains unverified. The
durable record is `docs/plans/audits/godot_4_7_2_upgrade_2026-08-28.md`.

Completed bounded independent-review correction: Stage 54F-3R.1 starts from
`31fef3718c967a20fcb6b9d14b83356f92ea40d2` on the same unpublished branch.
It closes only the fresh-destination sibling-backup ownership regression, two
unsafe Stage 54F-3R test dereferences, and three missing shared-replacement
state-machine transitions. A previously absent export destination does not
claim an unrelated sibling `.bak`; existing managed profile/settings paths
retain the accepted replacement and recovery sequence. Cleanup warnings reach
the existing profile result/Designer status and settings diagnostic boundaries
without changing deterministic scan diagnostics. No schema, identity, A/B,
dirty-state, settings, gameplay, camera, basis, cockpit, or authority behavior
changes. Focused/canonical/pinned Godot 4.7.1, mutation, governance/generated-
doc/settings/semantic-boundary, sanitation, diff, and full-repository evidence
is green. Stage 54F-3 remains reviewed green; Stage 54F-3R remains pending
independent re-review.

The presentation comparison apparatus and its candidate styles now both exist,
but the visual-design comparison does not. Stage 54F-4 created the candidates;
the next distinct stages are 54F-5 systematic comparative visual evaluation and
54F-6 default presentation selection/polish. Stage 54F-3R also remains pending
independent re-review.

Completed bounded post-review hardening: Stage 54F-3R starts from reviewed-green
Stage 54F-3 HEAD `47c90c67d5a13a84bd826f17f2838f0de3f38ec5`
on the same unpublished branch. It closes only four P2 findings: shared profile/
settings file mechanics now check the flushed temporary write before install;
profile replacement restores by rename then copy and retains an explicit
recoverable backup on total failure; library diagnostics are deterministic
current-scan state; and a production Live-4D regression protects exact gameplay
viewport allocation across collapsed/expanded library disclosure. Focused
profile, settings, and cockpit suites; canonical and pinned Godot 4.7.1;
governance/generated-doc/settings/semantic-boundary and sanitation checks; the
full repository gate; and bounded production-window inspection are green.
Stage 54F-3 semantics and reviewed-green status, separate persistence ownership,
schemas, Designer A/B behavior, gameplay/deterministic state, camera/basis, and
cockpit design are unchanged.

Completed bounded geometry review correction: Stage 54F-1 established the correct
canonical local-board architecture on `codex/canonical-local-board-geometry`,
but review found that continuous 2D/3D endgame points were routed through its
strict cell domain. Stage 54F-1R preserves one geometry owner while separating
strict lattice-cell and finite continuous affine APIs, adds production
particle/interpolation/trail/event-marker regressions, replaces tautological
slice-isolation evidence, and makes adaptive slice layout consume canonical
local extent. One canonical local-board geometry continues to own unit cells,
centred extent, coordinate conversion, face-grid segments,
and boundary segments for Live 2D, Live 3D, and every local Live-4D slice.
Semantic 2D embeds as presentation `[X,Y,1]`; exact `SliceBasis4D` supplies 4D
visible signed axes; slice-set layout, camera/framing, and profile styling stay
separate. Focused, governance, sanitation, pinned/full, deterministic-isolation,
and agent-driven 2D/3D endgame evidence pass; evidence is recorded in
`docs/plans/canonical_local_board_presentation_geometry_acceptance.md`.

Explicit deferrals from these follow-ons are formal A/B assignment/telemetry,
free-form palette-role editing, procedural style authoring, style thumbnail
generation, additional background-animation modes, broader theme work, and
independent human review of the Designer workflow, the built-in style catalog,
and the intentional full-depth 2D mesh under unusual debug camera views. Stage
54F-2 added the editing instrument only; Stage 54F-4 has since delivered the
read-only built-in style catalog and its bounded animated background, so those
two items are no longer deferred.

## Next Work

### Stage 54E-1 — Presentation-space architecture/design

Status: COMPLETE — HUMAN ACCEPTED.

The accepted architecture contract is
`docs/architecture/4d_presentation_interaction_architecture.md`. It defines
the three spaces, composition, ownership, lifecycle, scene implications,
`DEFECTIVE` current resolver verdict, anchor-only layout, shared slice-local
orientation, active/passive yaw and displayed-depth contract, verification
strategy, and mandatory green 54E-2 slices. Decisions A/B/C are accepted:
Option A; normal-gameplay roll removal while preserving Explorer/free-inspection
roll; and constrained pitch-depth preservation. No runtime implementation is
part of this acceptance record.

### Stage 54E-2a — Presentation state and coordinate decomposition

Status: COMPLETE — REVIEWED GREEN.

The implementation introduces the first-class shared Godot
`SliceLocalOrientation`, separates exact `B` mapping, centred `G_D` point
mapping, anchor lookup, and compatibility world composition, and executes the
accepted active/passive yaw, point-difference, signed-basis, asymmetric-board,
anchor-only, and `W=1` contracts. At the reviewed-green 54E-2a boundary the
renderer remained on the compatibility `G_D(p) + anchor_i` path; the separate
54E-2b implementation below now migrates that path.

### Stage 54E-2b — Renderer composition

Status: COMPLETE — REVIEWED GREEN.

The implementation migrates Live-4D cells, Ghost, geometry-attached markers,
grid/floor/lattice, ordinary and active frames, slice-label placement, and
camera-fit bounds to `B -> G_D -> L -> anchor`. It uses one shared continuous
orientation across all slice-local content, leaves anchors/layout/exact basis
unchanged, derives world AABBs from transformed local corners, and retains
2D/3D identity behavior. Focused Godot evidence covers asymmetric dimensions,
quarter/non-quarter yaw, pitch, signed basis, W=1 re-slicing, multiple slices,
Ghost alignment, grid/frame orientation, label identity, and bounds
containment. Technical review accepted this evidence; Stage 54E-2c has since
completed and been reviewed green.

### Stage 54E-2c — Interaction and camera-rig separation

Status: COMPLETE — REVIEWED GREEN.

Normal Live-4D left-drag and keyboard yaw/pitch mutate the one shared
`SliceLocalOrientation`; the app-owned mutation seam rerenders presentation,
recomputes oriented bounds, and refreshes the renderer fit reference. Relative
commands use exact `B + Q(L.local_yaw)` and ignore outer framing. Right-drag,
wheel/zoom, and Fit remain framing operations; gameplay roll is detached while
generic roll remains reusable. Legacy presets are temporarily decomposed into
`L` orientation and `V/P` framing. The fixed fitted mount applies one
renderer-only outer `V` reflection across the active camera's vertical/depth
plane, with Camera3D and HUD outside it. Actual Camera3D projection proves
resolver-selected Right screen-right, and effective camera-space depth proves
resolver-selected Forward receding across continuous yaw. Review-correction
evidence gives the strict all-yaw pitch interval as approximately
`(-42.480 degrees, +86.240 degrees)` and selects the asymmetric product range
`[-40 degrees, +60 degrees]`, retaining a `2.480-degree` lower margin. Final
visual review corrects Live-4D active spawn cells with negative canonical `Y`:
they retain their basis-derived slice and above-board position instead of
collapsing to a shared renderer origin. The same final visual pass corrects
shared NEXT-thumbnail cell adjacency so connected cells share projected cube
faces within each intentional `W` group.

### Stage 54E-2d — Lifecycle, authority, and contract reconciliation

Status: COMPLETE — REVIEWED GREEN.

The implementation restores fresh `B/L/V/P` defaults on Live-4D entry,
configured/random launch, Restart Game, and Reset View; keeps Reset View
presentation-only; provides an internal basis-only reset; synchronously clears
renderer, fit, reflection, focus/zoom/projection, and interpolation state on
setup/menu/mode exit; and rebuilds coherent defaults on re-entry. Normal
gameplay no longer registers/routes/advertises roll, while generic `CameraRig`
roll remains reusable. Persistence and deterministic-isolation tests exclude
ephemeral presentation state while retaining established preferences. No
authority transfer or establishment occurs. External technical review accepted
the implementation and its evidence. Aggregate Stage 54E-2 is COMPLETE /
REVIEWED GREEN.
The fresh-restart statement above is historical implementation evidence. The
accepted Stage 54E-4 forward contract intentionally changes same-context
Restart/new-game behaviour to preserve current view; it does not rewrite the
Stage 54E-2d review outcome.

Stage 54E-3 is COMPLETE / REVIEWED GREEN: Stage 54E-3a
taxonomy and classification and Stage 54E-3b progressive-disclosure rendering
are implemented and accepted by external technical review. Ordinary setup is
the board preset shortcut, the piece-set choice where a mode publishes more
than one set, and the starting speed; board customization, reproducibility, and
control frames sit behind secondary disclosure. Disclosure is ephemeral
presentation state excluded from canonical session setup, setup persistence,
and native session state, so no schema version changes. Its distinct human
product review remains outstanding and is owned by integrated Stage 54F unless
performed sooner. Stage 54E-4a is REVIEWED GREEN. Stage 54E-4b implements the
accepted contract and is COMPLETE / FOCUSED VISIBLE REVIEW ACCEPTED; aggregate
Stage 54E-4 is COMPLETE / REVIEWED GREEN.

## Hold

### Stage 54D-3 — Hold

Status: COMPLETE / DETERMINISTIC AUTHORITY ESTABLISHED / HUMAN VISIBLE
ACCEPTED (`AE-0055`).

Native live sessions own the one-slot transition, lifecycle legality,
queue/RNG and canonical-spawn consequences, state hash, and snapshot fields.
Godot dispatches one edge-triggered `C` action and renders authoritative HOLD
state through the shared NEXT thumbnail pipeline. Fixed replay/trace schema and
historical fixtures remain unchanged. Multiple slots, buffering, and a setup
toggle remain outside this stage.

## Forward Work

- Stage 54E-2b — renderer composition (COMPLETE / REVIEWED GREEN).
- Stage 54E-2c — interaction and camera-rig separation (COMPLETE / REVIEWED
  GREEN).
- Stage 54E-2d — lifecycle, authority, and contract reconciliation (COMPLETE /
  REVIEWED GREEN).
- Stage 54E-3 — setup/menu information architecture (COMPLETE / REVIEWED
  GREEN): direct seed input is the semantic control type `numeric_entry`,
  and board-axis controls remain `stepper` because their ranges make stepping
  the primary interaction. No control factory was introduced. A
  post-acceptance registry validation defect is FIXED: declarations are now
  validated before mode expansion, so empty mode sets cannot disappear.
- Stage 54E-4 — camera/GUI presets (COMPLETE / REVIEWED GREEN): Stage 54E-4a is
  REVIEWED GREEN and Stage 54E-4b is COMPLETE / FOCUSED VISIBLE REVIEW
  ACCEPTED, with no remaining human design decisions. It defines transient
  presentation-context view state, one composite Reset View, framing-only Fit
  View, restart/new-game preservation,
  context re-entry defaults, mode-specific 2D/3D/4D/replay ownership,
  accessibility-owned UI scale, and action-based presets with no continuous
  `Custom`/state-equality identity. The focused real-window review required two
  live view-affordance corrections before acceptance: Live 2D and Live 3D now
  route the existing `reset` action (key `0`) to the one composite Reset View,
  and Live 3D help states its real double-click Fit affordance instead of
  advertising `F`, which remains Rotate XZ.
- Stage 54E-5 — gameplay cockpit consolidation — COMPLETE / HUMAN PRODUCT
  REVIEW ACCEPTED. The accepted
  bounded design removes replay/developer chrome from ordinary live play,
  simplifies the live status summary, exposes distinct View and Session action
  families, derives mode-specific cockpit guidance from the existing live
  input contract, suppresses gameplay input while View Actions owns its popup,
  keeps NEXT prominent, and preserves replay diagnostics through their existing
  routes. It changes no gameplay, view lifecycle, movement/control-frame,
  NEXT, Ghost, or deterministic authority. Focused Godot, keybinding,
  sanitation, pinned Godot 4.7.1, and full repository verification passed.
  Real-window 2D/3D/4D review accepted the default, smaller, and larger cockpit
  composition, stateless View Actions, recovery/session actions, and
  progressive disclosure.

  E5 also carries two findings from Stage 54E-4a
  section 12.1: `display.show_w_labels` is presented in 2D and 3D where the
  renderer gates it on `dimension >= 4`, which needs a declared applicability
  mechanism in the settings registry; and `display.projection_strength` is
  misleadingly named, since it scales cell, particle, and event size in every
  mode rather than expressing a 4D projection.
- Stage 54F — COMPLETE / HUMAN INTEGRATED PLAYABILITY ACCEPTED. The bounded
  implementation, agent-driven real-DisplayServer evidence, and 2026-08-23
  human verdict are recorded in
  `docs/plans/stage_54f_integrated_visual_acceptance.md`.
- Stage 54G — COMPLETE / FINAL MANUAL RELEASE ACCEPTANCE PASSED. The
  independent matrix found one release blocker: after Live 4D exited through
  Main Menu and navigated through Advanced / Diagnostics, Replay Demos, and
  Viewer, the retained native session was exposed with cleared live board
  presentation. Viewer navigation now returns through the app lifecycle owner,
  rebuilds the canonical live presentation, and preserves native gameplay and
  the retained pause state. Focused all-mode/replay coverage, pinned Godot,
  full verification, rebuilt packaging, outside-tree smoke, and an actual-app
  Live-4D reproduction pass. Independent final blocker re-acceptance passed
  running and paused Live 4D, shared Live 2D/3D return, replay, immediate board
  visibility, retained gameplay/HOLD/NEXT/Ghost coherence, restored input
  ownership, and clean runtime logs. `PROFESSIONAL_CORE_GAME_READY` is `YES`.

### Stage 54F integrated visual findings

- [x] [Increase Live-4D inter-slice board spacing (#69)](https://github.com/mousomer/tet4d/issues/69):
  closed in the Stage 54F candidate through deterministic board-size-derived
  horizontal/vertical gutters, label-aware row clearance, stable slice
  assignment, non-overlap tests, and whole-collection Fit evidence for
  representative `2x2`, `W=8`, asymmetric, and constrained-window layouts.
- [x] [Refine Live-4D grid and board-wireframe visual hierarchy (#70)](https://github.com/mousomer/tet4d/issues/70):
  closed in the Stage 54F candidate. Internal-grid alpha is now operational
  and subordinate; wireframe and active-frame roles remain distinct; the
  active-frame multipliers are reduced; High Contrast preserves the ordering;
  and occupied real-window evidence keeps pieces and Ghost dominant.
- [x] Every displayed 4D W-slice reads as a 3D board volume in the agent-driven
  real-window matrix: front/back face grids, floor lattice, wireframe cage,
  piece/Ghost depth, responsive separation, and rotated-view evidence remain
  legible. Human integrated acceptance and final release acceptance passed.
- [x] The Stage 54E-3 setup-colour advisory is closed. Invalid setup now
  carries error-coloured summary and disclosure treatment plus literal
  `ERROR` text when the responsible section is collapsed, in standard and
  High Contrast modes.
- [x] The E5 display-setting findings are closed without changing setting IDs
  or persistence schema: runtime UI contexts now filter inapplicable quick
  settings, and player-facing labels describe cell-outline strength, 4D slice
  labels, and replay-object scale truthfully. The same audit also corrected
  runtime UI scale so it visibly reflows the shell instead of changing only a
  stored factor.
- [x] Supported-small-window Settings reachability is repaired: content and
  both reset actions scroll into range, and keyboard focus reveals an
  off-screen target instead of remaining stranded.

No new Stage 54F blockers remain in automated or agent-driven real-window
review.

- **Stage 54G polish — modest standard-mode Live-4D volume legibility.**
  Human review found that Live-4D gameboxes remain slightly less legible than
  equivalent 2D/3D boards in the standard presentation. The current
  presentation remains usable and comprehensible, and High Contrast provides
  a strong alternative, so this does not block Stage 54F acceptance. During
  The 54G comparison selected disposition B: no sufficiently clear low-risk
  improvement justified reopening the human-accepted rendering candidate.
  Retain this as non-blocking post-release polish, not a correctness or
  architecture defect.
- **Post-release polish — live pause status badge.** Pausing correctly stops
  live gameplay, but the cockpit badge can continue to display `[ RUNNING ]`.
  Track this separately from the Viewer-return release blocker; do not expand
  the bounded restoration fix into status-presentation work.
- **Post-release shell/accessibility follow-ups.** Preserve the non-blocking
  small-width `SPAWN ENTRY` clipping, replay case-list keyboard limitation,
  very-small-window/minimum-size behavior, HiDPI default physical-point
  sizing, and window size/position persistence observations for later bounded
  product work. Developer ID signing and notarization remain a separate macOS
  distribution prerequisite, not part of Professional Core Game readiness.

### Pre-54F correctness findings

- **Cross-dimensional relative-control truthfulness — COMPLETE / REVIEWED GREEN
  / issue #74.** Live 2D now resolves
  signed canonical X from presented outer yaw. Live 3D now resolves
  screen-relative Left/Right and viewer-away/viewer-toward Forward/Back from
  the outer-camera convention. Initial/repeated input, HUD, and the 3D gizmo
  consume one effective mapping; Absolute and accepted Live-4D
  `B + Q(L.local_yaw)` behaviour are protected by regression tests. Focused
  Godot verification and the full repository gate are green. Human-visible
  review accepted 2D Relative Left/Right, 3D Relative Left/Right and
  Forward/Back, and preservation of accepted 4D behaviour. E4 lifecycle and
  view architecture remain closed.
- **3D/4D NEXT geometry fidelity — COMPLETE / HUMAN VISIBLE REVIEW
  ACCEPTED.** The queue payload and thumbnail model were exact;
  independent renderer fitting per W pane erased shared XYZ placement. One
  complete-piece projection frame now preserves cross-W offsets. Registry-led
  conformance covers all 14 production Live-3D and 21 production Live-4D
  definitions, embedded lower-dimensional paths, FORK4, renderer completeness,
  and queued identity/update without changing queue or RNG semantics. Focused
  Godot 4.7.1 real-window review accepted representative native and embedded
  3D/4D pieces, FORK4's shared cross-W placement, renderer completeness, and
  queue progression. This closes only the bounded correctness item; do not
  absorb it into E4a or integrated 54F acceptance.

## Authority Transition Work

The repository no longer treats Python as the universal semantic oracle.

Python remains reference authority for inherited, untransferred behaviour.

New behaviour without a predecessor may establish authority directly in:

- Godot for product/presentation semantics;
- native C++ for deterministic shared semantics;
- versioned declarative data for challenge/campaign content.

Stage 54D exercises three distinct lanes:

- next preview: Godot presentation of inherited queue state;
- ghost: Godot presentation over an inherited read-only landing query;
- Hold: new deterministic state requiring authority establishment.

Immediate governance requirements:

- keep `docs/architecture/authority_map.md` aligned with actual subsystem
  owners;
- use transfer records for inherited behaviour;
- use establishment records for genuinely new behaviour;
- do not create Python mirrors solely to manufacture parity;
- do not add placeholder authority-record rows without the required concrete
  evidence.

Potential future bounded reviews include explicit native transfer of existing
bounded gameplay and topology subsystems. Do not transfer the full gameplay
loop or topology system as one undifferentiated unit.

## Later Programme Phases

The following are accepted later phases, not current implementation scope.

### First-class topology games

- ordinary 2D setup choices for Bounded, Strip, and Möbius Strip;
- Strip/Möbius board-extent rules through the Stage 54B validation interface;
- later selected 3D/4D topology presets;
- exact canonical topology transport;
- visible seam/transformation feedback;
- no silent fallback to bounded play.

### Godot Explorer as spatial practice

- free movement on all axes, including Y;
- independent object rotation, 3D camera orientation, 4D view basis, slice
  axis, and active-slice state;
- exact camera quarter-turns;
- complete X/slice, Y/slice, and Z/slice basis exchange;
- topology inspection and transitions into Play;
- no duplicate movement or topology rule system.

### Challenge and learning system

- data-driven target-pose, camera, basis, navigation, placement, clearing, and
  topology challenges;
- declarative challenge/campaign authority;
- native deterministic predicates where required;
- Godot instructions, hints, progress, and campaign navigation;
- a four-dimensional challenge campaign that replaces the conventional
  tutorial as the primary curriculum.

### Unified simulation flow

- explicit transitions from game, Explorer, or challenge state into the
  existing explosion simulator and future physics systems;
- versioned conversion boundaries;
- no silent reinterpretation of gameplay state as physics state.

## Explicit Deferrals

- topology-aware Godot gameplay until the professional core-game gate is
  substantially complete;
- full Godot Topology Lab/editor migration;
- complete Explorer implementation;
- general challenge runner and campaign;
- unified gameplay/endgame/explosion launch integration;
- multi-piece next-queue display and configurable preview depth;
- ghost style/opacity menus;
- multiple Hold slots, Hold buffering, or competitive Hold variants;
- gamepad support, audio, and broad control-remapping work until their focused
  Phase I hardening slices;
- piece-record and migration/config-bundle import readers identified by the
  Stage 53E audit, pending owning-format evidence and focused acceptance tests;
- unrelated settings recovery identified by Stage 53E, pending individual
  stored-schema review and named migration-adapter evidence;
- Stage 53E retirement candidates that retain active callers, product/policy
  roles, benchmark roles, or released compatibility obligations;
- compaction or splitting of `docs/history/DONE_SUMMARIES.md`, which belongs to
  a separate documentation-hygiene batch and is not active product work.

## Python Movement-Graph Persistent-Cache Performance

Status: deferred pending a native movement-graph authority/representation
decision or user-facing latency evidence.

Stage 53F correctness is complete: malformed or incompatible cache data is a
derived-data miss, and valid cache acceptance remains bounded without full
graph construction.

The diagnostic 20³ benchmark measured direct construction at approximately
`.054` seconds and a cold strict JSON cache read at approximately `.318`
seconds. The cache therefore makes no cold-start performance claim.

This affects setup and topology transitions only; it has no steady-state
movement, rendering, collision, determinism, or frame-rate impact.

Revisit when:

- a native movement-graph representation is designed; or
- representative normal start/topology-switch latency exceeds the accepted
  product budget.

## Codex Routing Follow-Ups

The machine-readable authority pointers, task taxonomy, workflow modifiers,
and composable verification-requirement schema are implemented in Slice A.

Slice B is now implemented: the policy-backed resolver consumes the routing model,
enforces read-only and repository-change invariants, composes requirements by
union, emits scope matrices, and renders stable JSON or Markdown reports.

Accepted follow-up:

- **Slice C — path-sensitive CI lanes:** map resolved requirements to explicit
  baseline, governance, Python, Godot, native, deterministic/parity, packaging,
  platform, and release lanes with conservative full-gate fallback.

Measure Slice C only against the CI baseline after duplicate push/PR execution
has been removed. Do not combine either follow-up with Stage 54B-1 runtime work.

Re-governance PR 1 retires the accumulated task and completion ledgers from
active governance and compacts the restart handoff without changing routing or
verification semantics. PR 2 remains separately scoped to canonical governance
consolidation, compositional route semantics, `docs/WORKFLOW_CODEX.md`
retirement, workspace-bundle and `docs/policies/` consolidation,
`docs/DOCUMENTATION_MAP.md` disposition, and a single-owner governance model.

## Governance Watchlist

- Keep one semantic objective per PR.
- Use the implementation-stage boundaries in the professional programme.
- Require a scope matrix for deliberately cross-layer integration PRs.
- Never weaken tests to fit an implementation.
- Keep subsystem authority and transfer/establishment records aligned with
  actual ownership.
- Do not create Python implementations solely to preserve a universal-oracle
  claim.
- Keep invalid topology-profile storage non-saveable through ordinary update
  paths; read-only fallback is not mutation authority.
- Keep generated outputs tied to their source authority and generator.
- Record new warnings separately from known advisories.
- Keep all Tet4D GitHub writes on the verified owner identity for canonical
  `origin`, without publishing unrelated account or local identity details.

## Completion Boundary

Work is complete only when the stated acceptance criteria pass, authoritative
documentation is current, required checks are green, publication state is
reported, and the tracked worktree is clean.

Opening a branch or draft PR is not completion.
