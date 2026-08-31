# CURRENT_STATE (Restart Handoff)

Last updated: 2026-08-31
Worktree expectation: active governed unified-release implementation on
`codex/android-validate-sparse-apk`; do not treat the worktree as a clean
handoff

## Purpose

This file is the compact restart handoff for staged, phase-dependent, or
multi-batch work. It is not workflow authority, a validation transcript, or a
history ledger. Detailed history is preserved in
`docs/history/current_state_archive_2026-07-30.md` and
`docs/history/DONE_SUMMARIES.md`.

## Active Focus

- The fresh final matrix for integration PR #75 was green at rewritten head
  `9dfabd44f8242e2c4d935e86f9eb40eeb39e0abf` and was squash-merged to
  `master` as `eb112dc26ef8c87aa86be94d6cfc026f134e8d94`. The earlier diagnostic
  Godot timing failure was corrected before the final run; Python 3.11-3.14,
  native, deterministic/parity, Godot, integration, packaging, platform,
  release-acceptance, and aggregate required gates all passed.

- The merge-blocking Design Laboratory A/B correction is implemented and
  committed on the rewritten integration branch.
  The catalogue exposes `Apply Live`, `Set as A`, and `Set as B`; the session
  stores frozen A/B slots separately from `shown_arm`; assignment never follows
  the visible arm; blind labels retain true provenance; candidate edit/save is
  unassigned; reassignment rotates the evidence identity so captures from
  different pairings cannot mix. Focused state and real production-panel
  runtime tests pass. An agent-driven real-window production-scene checklist
  also passed: assigning A while B was shown left B visible, blind entry/exit
  preserved the true arms, edit/save did not assign, and the edited candidate
  changed A only after the explicit action. This is not independent human
  sign-off.

- The 39 MB Windows ZIP path and original blob are unreachable from integrated
  master; all seven useful documentation, metadata, and validator-test files
  remain. Content-aware branch review deleted 22 obsolete remote refs and
  retained only `codex/explosion-architecture-inventory` for inspection because
  it contains unique implementation work and conflicts.

- Initial Actions proof run 33390087916 accepted macOS arm64 and Linux amd64
  end to end. Windows built and installed its MSI and the installed runtime
  printed success, but its GUI-subsystem process returned control before
  PowerShell populated `$LASTEXITCODE`. The proof harness was corrected to wait
  for the process and inspect its real exit code before uninstall verification.

- Final Actions proof run 33392862609 was green for all three Python jobs at exact
  integrated master `d542d682ab9f66a6e8ca95b888232b90524ef266`. macOS arm64,
  Linux amd64, and Windows x64 each built version 0.7.5, launched outside the
  checkout with isolated user state, and completed mount/removal or
  install/uninstall. The release-unification gate is open. The seven-artifact
  Python-plus-Designer workflow, tag/project-version invariant, and
  source-SHA/checksum manifest with truthful iPadOS status are implemented and
  awaiting integrated CI plus real workflow-dispatch evidence.

- PR #78 had a green complete fresh CI matrix and was squash-merged as
  `4fdb8bfa4e5730426789453df71ea198e70d475f`. Integrated manual release run
  33397993043 is diagnostic: all three Python jobs passed, while Android and
  iPadOS exposed a cache-free `PresentationProfile` self-construction defect
  and Windows exposed a split 7-Zip output option. A narrow correction and
  fresh seven-artifact run are active; no unified manifest claim is made yet.

- PR #79 corrected those dependencies, had green complete exact-head CI, and
  was squash-merged as `38551bb2f87d4f2866f33f99a7143cf156c75da6`.
  Integrated dispatch 33401278911 cleared the corrected cache-free tablet
  semantic test and retained green Python packaging, but Android and iPadOS
  then exposed a shared YAML/shell folding defect before either checked-in
  builder executed. Block-form tablet invocations, regression coverage, full
  gates, and a fresh integrated seven-artifact run are active; no unified
  manifest claim is made yet.

- The Windows job in dispatch 33401278911 then completed its native build and
  export, but the strict validator found the runner checkout marker in the
  package. The disposable project had copied ignored `.godot` state generated
  by the preceding direct Godot test; Android and iPadOS share that source-copy
  exposure. All three builders must remove copied editor cache state before
  export while retaining strict host-path rejection. This isolation correction
  is included in the active full-gate and integrated-proof cycle.

- PR #80 had a green fresh complete CI matrix and squash-merged as
  `979b91c23e63ab0489265c26bd43e84db06ccf2f`. Integrated dispatch
  33416903976 cleared the Android command, cache-isolation, configuration, and
  staged-signing boundaries, then native compilation found the runner lacked
  pinned `godot-cpp`'s exact NDK `28.1.13356709`. Exact NDK installation and
  assertion, its packaging contract, full gates, and a fresh integrated proof
  are active; no unified manifest claim is made yet.

- The iPadOS lane in dispatch 33416903976 compiled its arm64 device archive,
  then found the builder asserted the declared release XCFramework without
  creating it. The active correction adds a separate universal simulator
  archive and assembles the XCFramework explicitly from both native outputs;
  regression coverage, full gates, and fresh integrated proof remain required.

- Windows in dispatch 33416903976 completed native compilation and export, then
  strict validation found the runner path in `.godot` cache regenerated during
  disposable-project import. The active correction keeps pre-import cache
  removal and strict scanning while excluding `.godot/*` from every canonical
  Designer preset; full gates and fresh integrated proof remain required.

- PR #81 had a green complete exact-head matrix and squash-merged as
  `f8e70ca27c111410861ec7572f4ef9771fafb634`. Integrated dispatch 33421053972
  derived the correct Android NDK pin but found `sdkmanager` absent from PATH.
  The active correction resolves the exact command-line-tools executable under
  `$ANDROID_HOME`, removes the unbounded `yes` pipeline, and retains exact NDK
  Clang validation; full gates and fresh integrated proof remain required.

- PR #82 resolved the exact Android command-line-tools executable, passed its
  complete exact-head matrix (Actions run 33421707698), and squash-merged as
  `5c3cc3ead8dcb67d10f3e1a627b88210c4f1312e`. The active Windows follow-up
  addresses the remaining hosted MSVC-only checkout marker by embedding the
  PDB basename through `/PDBALTPATH:%_PDB%`; it retains existing compiler path
  maps and adds member-level strict-validator diagnostics. Focused, full, PR,
  and fresh integrated release evidence remain required.

- PR #83 had a green complete exact-head matrix (Actions run 33424857253) and
  squash-merged as `9058e93ede45efe79ef841209c1f6fbe96af2401`.
  Integrated dispatch 33426937123 proved all three Python packages and Godot
  macOS again. Android cleared the exact SDK/NDK setup and reached native
  archiving, where pinned `godot-cpp` exceeded the POSIX `ar` argument limit.
  The active correction extends Linux's existing SCons response-file archive
  command to Android; focused, full, PR, and fresh integrated evidence remain
  required. Windows remains isolated to the native DLL despite the PDB-path
  correction, and iPadOS remains isolated to Godot additional-asset export;
  neither is silently included in this Android objective.

- PR #84 had a green selected exact-head matrix and squash-merged as
  `61437bd682c09adfc73482ca291073343e5541e3`. Integrated dispatch
  33429888428 proved SCons creates the Android archive response file and the
  old `Argument list too long` failure is gone. It then terminated before
  `ar` returned because the wrapper omitted `TEMPFILE`'s compact display-string
  argument, causing SCons to expand the enormous command into the CI log. The
  active follow-up passes `ARCOMSTR` as that second argument; focused, full,
  PR, and fresh integrated APK evidence remain required. Windows and iPadOS
  retained their prior isolated failures and remain outside this correction.

- PR #85 had a green selected exact-head matrix and squash-merged as
  `ea9be00d709d14fd55e70dab81f814ba07ecfe7c`. Integrated dispatch
  33433033740 completed Android's binding archive, ranlib, project-native
  compilation, and arm64 shared-library link. It stopped only because the
  disposable project's ignored native `bin` directory was absent before the
  `.so` copy. The active correction creates that staging directory explicitly;
  focused, full, PR, and fresh integrated APK evidence remain required.

- PR #86 had a green selected exact-head matrix and squash-merged as
  `b4498c2742bcb4b4309816f2c9ff405e9cf1f5c8`. Integrated dispatch
  33436190052 compiled and linked the Android arm64 GDExtension, exported the
  APK, and completed Godot alignment, signing, and verification. The repository
  validator then rejected the lack of a `.pck` ZIP member, although Godot 4.7.2
  intentionally stores Android project resources individually under `assets/`
  and emits `assets/assets.sparsepck` metadata. The active correction aligns
  validation and packaging documentation to that upstream layout while keeping
  required-resource and path-hygiene enforcement; focused, full, PR, and fresh
  integrated evidence remain required.

- Completed bounded live-presentation regression repair on
  `codex/built-in-style-catalog`, starting from
  `47df7cef84db32a2aa7dff383a84cdb968b53223`. Translucent active/locked
  exterior faces now retain requested alpha on a depth-writing structural path;
  Ghost and environment transparency remain distinct. Live-4D left-drag now
  accounts for passive `L` so its apparent screen convention matches Live 3D,
  with invert-Y affecting only vertical input. Normal-gameplay pitch is
  `-40..+80` degrees inside the proven all-yaw safe interval. Stable
  shape-derived slice envelopes reserve full supported `L` clearance, spacing
  remains a multiplier, renderer bounds include root stabilization, and Fit
  uses one `1.05` framing margin. Focused regression, pinned Godot 4.7.2,
  keybinding, governance/generated-doc, full repository, and plain/Tron real-
  window evidence pass. Manual mouse drag was unavailable through the local UI
  automation bridge; an actual production `Camera3D` projection test covers the
  four drag directions and invert-Y. No basis/gameplay/native hash/trace/schema,
  2D/3D geometry, or authority change occurred. Nothing was pushed and no PR
  was opened. Detailed evidence is in `docs/governance/task_contract.md` and
  `docs/governance/completion_report.md`.

- Stage 54F-5 was enlarged on 2026-08-30 from one distribution target to three:
  Windows, Android tablet, and iPadOS, both tablets for landscape use with a
  physical keyboard rather than as touch-first games. There is still exactly one
  Design Laboratory. The catalogue, scenario system, A/B implementation,
  evaluation schema, capture semantics, nomination bundle, semantic-owner
  registry, and repository-side validator are unchanged and platform
  independent; `tests/test_cross_platform_design_boundary.gd` asserts that a
  candidate exported under Windows, Android, and iPadOS provenance yields
  identical preset identity, properties, semantic owners, and snapshot hash. A
  platform adapter boundary owns export transport, handheld safe-area insets,
  and system Back behaviour, and owns nothing else.

  Implementation is complete on all three targets. Two artifacts are not:

  - The Android APK does not build on this host. Godot 4.7.2 requires a Java SDK
    and an Android SDK with `platform-tools` and `build-tools` unconditionally
    in `can_export()` (verified directly; `package/signed=false` does not bypass
    it), and the arm64 GDExtension needs the NDK. Installing them was declined.
    The Android resource pack does export and validate locally.
  - The iPadOS application does not compile on this host, which has Command Line
    Tools but no Xcode and therefore no iPhoneOS SDK. The Xcode project itself
    exports and validates locally.

  Both build scripts and both CI jobs are complete: `package-android` on
  `ubuntu-latest` and `package-ipados` on `macos-latest` carry the toolchains
  this host lacks. No emulator, simulator, device, or physical-keyboard evidence
  exists on any platform, and none is claimed. The Windows artifact was rebuilt
  and revalidated after the shared changes. The exact evidence matrix is
  `docs/plans/design_evaluation_laboratory_acceptance.md`.

- Stage 54F-5 Design Laboratory implementation and local automated acceptance are
  complete from starting SHA `1edd764abd3ab04d44546f97be317bec1c4be57e` on
  `codex/built-in-style-catalog`. The new main-menu route combines the existing
  immutable built-in catalog and mutable replacement-safe profile library with
  ten deterministic live/replay scenarios, frozen A/B and deterministic blind
  comparison, canonical reset, preference/eight-rating/notes persistence, A/B
  PNG capture, and explicit nomination. Exported `preset.json`,
  `comparison_summary.json`, and `DESIGN_PROPOSAL.md` are review evidence only;
  the read-only repository validator resolves all 29 properties and owners and
  never promotes them. The runtime matrix reloads every scenario and
  applies/renders every shipped preset without non-style drift.

  A current-Godot Windows x86_64 portable ZIP is now an explicit build artifact
  with its release DLL, PCK/resources, product metadata/icon, structural
  validator, and Windows CI/focused-smoke lane. It requires no Python, editor, or
  checkout. Local macOS evidence validates the PE/package but does not execute
  it. The only platform gap is direct clean-machine Windows acceptance; the
  human design comparison itself is also intentionally pending and does not
  block implementation acceptance. Durable ownership and the exact checklist
  are `docs/architecture/design_evaluation_laboratory.md` and
  `docs/plans/design_evaluation_laboratory_acceptance.md`. Stage 54F-6 remains a
  separate human-reviewed default-selection change.

- Completed candidate-style creation: Stage 54F-4 starts from
  `1cb6e8db474d57832c0b715fd9bc5d57716aa354` on the new branch
  `codex/built-in-style-catalog`. It adds `BuiltInStyleCatalog`, a third
  presentation artifact kind beside runtime working state and mutable user
  profiles. The catalog reads one repository-shipped versioned JSON document
  through `res://config/built_in_style_catalog.json`, never touches `user://`,
  and exposes no save/rename/delete/overwrite API, so read-only is structural.
  Applying a style replaces detached working B, leaves captured A and the shipped
  entry unchanged, and clears the loaded user-profile identity so explicit Save
  cannot target a built-in; `Save As` and `Copy to User Library` create ordinary
  mutable user profiles. Six curated styles ship: Tet4D Balanced, Python
  Reference, Arcade Neon, Tron Grid Flow, Blueprint Technical, and High Contrast.
  Three new `ENVIRONMENT_PRESENTATION` registry parameters
  (`environment.background_animation_mode`, `..._intensity`, `..._speed`) drive
  one bounded `AnimatedBackground` component. It renders a screen-space luminous
  grid flow on a camera-anchored quad far behind the play volume, never writes
  depth, derives colour only from existing palette roles, damps the frame centre
  where the board sits, and owns a resettable component-local phase that is
  deliberately excluded from every deterministic snapshot.
  `accessibility.reduced_motion` freezes it and the accessibility style ships
  with motion off. `mode = none` is byte-equivalent to the previous static
  background. The registry grows from 26 to 29 parameters, so the documented
  live-applicable Designer counts move to 19/21/23; those count assertions were
  updated, not weakened. The durable records are
  `docs/architecture/built_in_style_catalog.md` and
  `docs/plans/built_in_style_catalog_acceptance.md`. This stage creates
  candidates only: Stage 54F-5 compares them and Stage 54F-6 selects and polishes
  the default.

- Completed toolchain baseline upgrade: Stage 54F-3R.2 starts from
  `e2e1ef9254f12c528ce7a67599b43510abfc0902` on
  `codex/canonical-local-board-geometry`. The pinned engine moves from
  `4.7.1-stable` to `4.7.2-stable` (`4.7.2.stable.official.ed1daf0bf`, published
  2026-08-18), the newest published stable 4.7 patch and newest Godot 4.x stable
  overall, under the policy pack's existing selection rule. Archive hashes were
  verified against upstream `SHA512-SUMS.txt` before use. The `godot-cpp` binding
  is deliberately retained: the dumped 4.7.2 extension API is identical to the
  pinned 4.7-stable baseline once the header is excluded, and upstream has
  published no newer API sync. Only the project target-version declaration and
  three version literals moved; `config/features`, `compatibility_minimum`, and
  the native `api_version` stay minor-scoped at `4.7`. Gameplay and presentation
  are provably unchanged: `live_4d_state_hash` and every layout contract rect are
  identical across engines, and four rendered frames including the full Designer
  with the Profile Library expanded are byte-identical to their 4.7.1 captures.
  Pinned Godot, native build/tests, governance, generated-doc, settings,
  semantic-boundary, sanitation, full-repository, and bounded macOS Metal window
  evidence are green. This slice changes no gameplay, presentation,
  profile-library, schema, or authority behavior. The durable record is
  `docs/plans/audits/godot_4_7_2_upgrade_2026-08-28.md`.

- Completed independent-review correction: Stage 54F-3R.1 starts from
  `31fef3718c967a20fcb6b9d14b83356f92ea40d2` on
  `codex/canonical-local-board-geometry`. The bounded fix limits sibling backup
  cleanup to destinations that existed before replacement, so fresh arbitrary
  profile exports preserve unrelated `.bak` files while existing managed
  profile/settings paths retain their accepted recovery mechanics. Direct tests
  cover absent install failure, backup/install success, and cleanup warning;
  the two new persistence load assertions fail normally rather than crashing.
  Focused helper/profile/settings/cockpit, scratch mutation, isolated canonical,
  pinned Godot 4.7.1, governance/generated-doc/settings/semantic-boundary,
  sanitation, diff, and full-repository evidence is green. Stage 54F-3 remains
  reviewed green; Stage 54F-3R remains pending independent re-review. No
  semantic authority transfers.

- Programme clarification: the parameter contract, canonical geometry,
  Designer A/B machinery, compact cockpit, profile library, and persistence
  isolation form the comparison apparatus, and Stage 54F-4 has now supplied the
  candidate styles. Neither constitutes candidate visual-design comparison.
  Stage 54F-5 compares candidates systematically and Stage 54F-6
  selects/polishes the default presentation.

- Completed bounded post-review hardening: Stage 54F-3R starts from reviewed-green
  Stage 54F-3 HEAD `47c90c67d5a13a84bd826f17f2838f0de3f38ec5`
  on `codex/canonical-local-board-geometry`. One small Godot helper now owns only
  temp-write/replace/backup/restore mechanics for the still-separate
  `PresentationProfileLibrary` and `SettingsStore`: flushed write errors abort
  before installation, restoration uses rename then copy, and total restore
  failure retains an explicit recoverable backup. Profile listing rebuilds
  sorted current-scan diagnostics, so repeated deterministic snapshots no
  longer accumulate corrupt-artifact messages. A production Live-4D test proves
  collapsed/expanded Profile Library disclosure leaves the gameplay viewport
  and full Designer rect unchanged while NEXT, HOLD, piece controls, and basis/
  slice state remain visible. Focused profile/settings/cockpit, canonical and
  pinned Godot 4.7.1, governance/generated-doc/settings/semantic-boundary,
  sanitation, full-repository, and bounded production-window evidence is green.
  This slice changes no schema, identity, Designer A/B/dirty semantics,
  ordinary settings ownership, gameplay/deterministic state, camera/basis, or
  authority.

- Completed bounded follow-on: Stage 54F-3 starts from verified local HEAD
  `5a2e648124ed4ea0f62003fd95fb3d8dca1a57f6` on
  `codex/canonical-local-board-geometry`. It adds an explicit one-file-per-
  profile `PresentationProfileLibrary` under Godot user data, with generated
  stable IDs, validated display names, the existing schema-1 profile payload,
  safe replacement, corruption isolation, and list/save/load/duplicate/rename/
  delete/import/export lifecycle. The Designer integrates a collapsed-by-
  default library surface; Save targets working B, load replaces/displays a
  detached B without changing A, and semantic dirty state is separate from
  runtime-only edits. Ordinary settings, gameplay, native hash, camera pose,
  basis/slice, Ghost truth, NEXT/HOLD, controls, and cockpit allocation remain
  unchanged. Focused, canonical/pinned Godot 4.7.1, settings/persistence,
  semantic-boundary, governance, sanitation, full-repository, and bounded real-
  window evidence is green. Authority and acceptance are recorded in
  `docs/architecture/presentation_profile_library.md` and
  `docs/plans/presentation_profile_library_acceptance.md`.

- Completed bounded post-review cleanup: Stage 54F-2R.1 starts from reviewed-
  green cockpit HEAD `d77aca9a3a7556d6e4db71ba47af24894e75e5ad` on
  `codex/canonical-local-board-geometry`. It makes Reset View visibility
  explicitly live-only across replay -> Live 2D/3D/4D -> replay, and replaces
  the dead W/slice display-string matcher with direction/signed-axis metadata
  supplied by `LiveInputContract`. The passive strip retains authoritative
  bindings and exact mode applicability. No layout, camera behavior, Designer,
  gameplay, deterministic state, geometry, basis, NEXT/HOLD, input, or
  authority change is included. Closure evidence is appended to
  `docs/plans/live_presentation_designer_acceptance.md`; the parent stages
  remain REVIEWED GREEN.

- Completed bounded review correction: Stage 54F-2R starts from local Designer
  HEAD `4c2dc44c89865193bf2022ffab822741feac1bdb` on
  `codex/canonical-local-board-geometry`. It recovers vertical board space with
  a single live action row, puts NEXT/HOLD in one compact shared-thumbnail row,
  and permanently displays mode-applicable piece translation/rotation guidance
  derived from `LiveInputContract` before secondary camera controls. The
  Live-4D fit margin changes only after allocation, from 1.32 to 1.20, while
  consuming authoritative collection bounds. Production Godot 4.7.1 Metal
  captures cover 2D/3D/4D, full/compact Designer, and a requested 960x720
  constrained window. Designer A/B/input/persistence isolation, deterministic
  gameplay, canonical geometry, exact basis, helper authority, and native
  NEXT/HOLD remain unchanged. This is local agent-driven acceptance, not
  independent human sign-off; evidence is in
  `docs/plans/live_presentation_designer_acceptance.md`.

- Completed bounded follow-on: Stage 54F-2 Live Presentation Designer starts
  from reviewed Stage 54F-1R HEAD
  `32e9d2a9e8f431693761a25ba6cd9736419ab4bf` on
  `codex/canonical-local-board-geometry`. It generates its live parameter rows
  and semantic-owner groups from the existing registry, edits only detached B,
  captures immutable A, supports opening-baseline and factory resets, and
  previews through `TraceReplayApp.apply_presentation_profile()`. Full mode
  owns input; compact/hidden restore gameplay keys; the remaining panel hit
  area blocks pointer pass-through. Store/save count, deterministic live
  state, canonical geometry/bounds, exact basis/slice orientation, camera pose,
  NEXT, and authoritative HOLD (`AE-0055`) remain unchanged. Non-headless Godot
  4.7.1 Metal captures cover full 2D/3D/4D, compact 4D, and frozen-state A/B;
  focused, pinned, full-repository, governance, and sanitation checks pass.
  This is local agent-driven acceptance, not independent human sign-off. The
  contract and evidence are `docs/architecture/live_presentation_designer.md`
  and `docs/plans/live_presentation_designer_acceptance.md`. Named-profile
  persistence/import/export, formal experiments/telemetry, broader theme work,
  and Stage 54G changes remain out of scope.

- Completed bounded review correction: `codex/canonical-local-board-geometry` starts
  from presentation-parameter HEAD
  `addd0d194f8fb53f57daf03e8b48ca4dd07ee6d4`. It establishes one canonical
  local-board geometry for Live 2D, Live 3D, and every local Live-4D slice;
  adapts 2D to presentation-only `[X,Y,1]`; consumes exact signed 4D basis
  axes; unifies cell mapping, centring, grids, floors, and boundaries; and
  removes the thin 2D depth exception. Review of implementation HEAD
  `d85605966ef9eb145f969a3d8e6550563c45b268` found one P1 domain regression:
  continuous fractional/out-of-board 2D/3D endgame points were entering the
  strict lattice-cell API and collapsing to the origin. Stage 54F-1R now
  separates strict-cell and finite continuous affine domains under the same
  geometry owner, keeps cells strict, routes particle/marker presentation
  points continuously, feeds canonical local extent to adaptive layout, and
  replaces tautological slice-isolation evidence. Focused Godot, governance,
  sanitation, pinned Godot 4.7.1, full-repository, deterministic-isolation, and
  focused agent-driven 2D/3D endgame visual evidence pass. Independent human
  visual acceptance is not claimed. The acceptance record is
  `docs/plans/canonical_local_board_presentation_geometry_acceptance.md`.
  Gameplay extents, native/session/replay/hash state, exact-basis laws, 4D
  slice-set layout, camera framing, and profile ownership are unchanged.

- Completed bounded follow-on: `codex/presentation-parameter-contract` starts
  from the locally accepted release-hardening stack at
  `7d9d3872180905e67874329f8046f336744a348e`. It implements a typed,
  uniquely-owned presentation-parameter registry, detached schema-1
  `PresentationProfile`, schema-3 settings reuse, and one bounded live app
  apply path over unchanged deterministic state. Focused, governance,
  sanitation, pinned Godot 4.7.1, full-repository, and agent-driven real-window
  checks pass. The acceptance record is
  `docs/plans/presentation_parameter_contract_acceptance.md`. This work does
  not reopen historical Stage 54E-4 or alter native/gameplay, replay/hash,
  basis, Hold, NEXT, Ghost-truth, or camera-pose authority.

- The accepted Godot foundation is merged on `master` at `eb584e4f`. It
  includes configurable bounded setup, display/accessibility infrastructure,
  settings hardening, Godot 4.7.1, pinned native dependencies, blocking
  Godot/native/parity CI, and Ruff 0.16 migration.
- Governance trajectory simplification is merged on `master` at `f7e519b0`.
  Active routing now uses the stable constitution, task contract, change
  classes, and completion report; completed stage detail remains historical.
- Godot visual consolidation was human accepted and merged at `6e06e00a`.
  Its viewport-control and persistence recovery was manually accepted and
  merged at `6bedb75a`.
- Canonical topology contract version 1 is merged on `master` at `86906eb8`.
  Shared topology-contract foundations are merged at `af01bbd6`, and Stage 53B
  native topology transport is merged at `fe867627` with strict profile/query
  transport and 59 shared Python/Godot-native acceptance fixtures.
- Stage 53C strict Python topology constructors are merged at `36972384`.
  Stage 53D topology persistence and legacy recovery is merged at `c7243828`.
  Stage 53E is merged at `22938485`. Stage 53F is merged and verified on
  `master` at `91b901f3`. The short-term Python boundary-governance programme
  is closed.
- Stage 54A is human accepted and merged on `master` at `bcf41519`.
- The active product authority is
  `docs/plans/professional_godot_game_programme.md`. Its first gate is a fully
  playable, professionally presented 4D Godot game that is ready for later
  topology, Explorer, challenge, and simulation extensions.
- PR #63 is merged on `master` at
  `c93dcc8cfa93857d514a14b925002efc4404b007`. Stages 54B-1 through 54D-2 are
  integrated: the topology-aware board-extent contract; editable validated
  setup; exact signed 4D basis; authoritative NEXT; and Ghost plus accepted
  presentation/control corrections.
- Stage 54E-1 is HUMAN ACCEPTED. Its accepted architecture contract is
  `docs/architecture/4d_presentation_interaction_architecture.md`: the
  combined-camera-yaw resolver is `DEFECTIVE`; Option A assigns shared
  slice-local orientation, anchor-only layout, and non-orienting normal
  Live-4D `V/P`; the F/R/Q and displayed-Forward/depth contracts are accepted.
  Normal-gameplay roll is removed in 54E-2 while reusable Explorer/free-
  inspection roll remains intended. Constrained pitch is accepted only where
  Pitch-depth preservation keeps Forward away from the viewer.
- Stage 54D-3 Hold is independently eligible. Stage 54E-2a is COMPLETE /
  REVIEWED GREEN: it established the first-class shared
  `SliceLocalOrientation`, explicit `B`, affine centred `G_D`, anchor-only
  layout decomposition, continuous `F(theta)`/`R(theta)`, and discrete `Q(q)`
  control projection distinction. Stage 54E-2b is COMPLETE / REVIEWED GREEN:
  it establishes `B -> G_D -> L -> anchor` renderer composition; one shared
  continuous `L`; aligned cells, active piece, Ghost, grids, and frames;
  anchor-only layout; oriented corner-derived fit bounds; and slice identity
  labels outside local physical rotation. Stage 54E-2c — interaction and
  camera-rig separation — is COMPLETE / REVIEWED GREEN: left-drag and keyboard
  yaw/pitch mutate the one shared `L`; relative controls consume exact
  `B + Q(L.local_yaw)`; outer pan/zoom/Fit remain framing-only; gameplay roll
  is detached while generic roll remains; preset yaw/pitch and framing are
  decomposed; and every `L` mutation rerenders oriented geometry, bounds, and
  the fit reference. The fixed far-side mount uses one renderer-only outer `V`
  reflection across the active camera's vertical/depth plane; the camera and
  HUD remain outside it. Actual `Camera3D.unproject_position()` evidence proves
  resolver-selected Right is screen-right, while effective camera-space depth
  proves resolver-selected Forward recedes. Review correction accounts for
  residual continuous yaw between `L.local_yaw` and `Q(L.local_yaw)`: the
  strict all-yaw pitch interval is approximately
  `(-42.480 degrees, +86.240 degrees)`, and normal gameplay uses
  `[-40 degrees, +60 degrees]` with a `2.480-degree` lower margin. Final visual
  review identified and fixed an above-board active-spawn projection collapse
  that had initially looked like a stale Ghost cell; the investigation also
  hardened presentation-node teardown by synchronously detaching obsolete
  children before deferred destruction, but that hardening was not the root
  cause of the reported cube. It also restores face-connected cell adjacency
  inside each shared NEXT-thumbnail `W` group. Board spacing and grid/wireframe
  styling remain deferred visual-quality work tracked in `docs/BACKLOG.md` and
  GitHub Issues. Stage 54E-2d — lifecycle, authority, and contract
  reconciliation — is COMPLETE / REVIEWED GREEN on PR #72: it establishes
  fresh entry/restart/reset defaults, presentation-only Reset View, an internal
  basis-only reset, synchronous setup/menu/mode teardown, coherent re-entry,
  public roll removal with generic roll retained, and persistence/deterministic
  exclusion evidence. It performs no authority transfer or establishment.
  Aggregate Stage 54E-2 is COMPLETE / REVIEWED GREEN. Stage 54E-3 — setup/menu
  information architecture — is COMPLETE / REVIEWED GREEN. Stage 54E-3a
  declared the taxonomy as data; Stage 54E-3b renders it as progressive
  disclosure, removes the panel's duplicate visibility rules, and keeps
  disclosure out of canonical session setup, setup persistence, and native
  session state. Its distinct human product review is outstanding and belongs
  to integrated Stage 54F unless performed sooner; E3 remains COMPLETE /
  REVIEWED GREEN. A post-acceptance registry validation defect is FIXED:
  declarations are validated before mode expansion, so an empty mode set
  cannot disappear without a validation failure. Stage 54E-4a human view
  semantics and final technical findings are REVIEWED GREEN. Stage 54E-4b
  implements that contract and is COMPLETE / FOCUSED VISIBLE REVIEW ACCEPTED.
  The active contract in
  `docs/architecture/camera_gui_preset_semantics.md` treats current view as
  transient presentation-context state; exposes one composite Reset View and a
  framing-only Fit View; preserves view across same-context Restart/new game;
  establishes fresh canonical view after setup/menu/mode exit and re-entry;
  defines flat 2D plus mode-owned 3D/4D/replay semantics; assigns UI scale to
  accessibility reset ownership; resolves camera projection as transient; and
  treats named presets as actions with no continuous `Custom`/state-equality
  identity. This deliberately refines the then-accepted Stage 54E-2d restart
  lifecycle without rewriting its historical reviewed-green evidence. The
  implementation splits outer orientation from framing, removes continuous
  preset identity and dead `frame_board()`, preserves view across Restart/new
  same-context games, rebuilds canonical views on context re-entry, and routes
  UI-scale reset ownership to Accessibility without changing persistence ID or
  schema. The focused real-window review found and closed two player-facing
  affordance blockers: Reset View had no invocation path in Live 2D or Live 3D,
  and Live 3D help advertised `F` as Fit View while `F` is Rotate XZ. Live 2D
  and Live 3D now route the existing `reset` action (key `0`) to the same
  composite Reset View that Live 4D already used, and the Live 3D Camera help
  states its real double-click Fit affordance. Aggregate Stage 54E-4 is
  COMPLETE / REVIEWED GREEN.
- Stage 54E-5 gameplay cockpit consolidation is COMPLETE / HUMAN PRODUCT
  REVIEW ACCEPTED on `codex/54e-5-cockpit-consolidation`. Ordinary live play
  is board-first, keeps NEXT prominent, separates View, Display, and Session
  actions, derives progressively richer 2D/3D/4D guidance from the shared live
  input contract, and hides replay/developer diagnostics without removing
  their existing routes. View Actions remain stateless and own input while
  open. Focused, keybinding, sanitation, pinned Godot 4.7.1, and full
  repository gates pass; normal, smaller, and larger real-window review is
  accepted. No gameplay, view lifecycle, control-frame, NEXT, Ghost,
  deterministic, native, topology, or persistence authority changed.
- Pre-54F issue #74 is COMPLETE / REVIEWED GREEN, and the 3D/4D NEXT
  correction is COMPLETE / HUMAN VISIBLE REVIEW ACCEPTED.
- Stage 54F integrated professional playability/visual acceptance is
  COMPLETE / HUMAN INTEGRATED PLAYABILITY ACCEPTED on
  `codex/54f-integrated-playability-visual-acceptance`. The candidate closes
  #69 responsive slice spacing, #70 board hierarchy, 4D label collisions,
  setup-error presentation, small-window Settings reachability, 2D spawn-entry
  grammar, and concrete setting naming/applicability defects. Focused tests and
  agent-driven Godot 4.7.1 real-window evidence cover 2D, 3D, occupied/rotated/
  wide-W 4D, High Contrast, and 1600x960, 1180x760, and OS-clamped 960x660
  windows; the pinned Godot 4.7.1 and full repository gates pass. No
  deterministic gameplay, view, movement, NEXT, Ghost, native, topology, or
  persistence authority changed. Human integrated review accepted 2D, 3D, and
  4D on 2026-08-23. It recorded slightly weaker standard-mode Live-4D gamebox
  legibility than equivalent 2D/3D boards as non-blocking Stage 54G polish;
  the usable current presentation and strong High Contrast alternative keep it
  outside the 54F correctness and architecture gates.
- Stage 54D-3 Hold is COMPLETE / DETERMINISTIC AUTHORITY ESTABLISHED / HUMAN
  VISIBLE ACCEPTED under `AE-0055` on
  `codex/54d-3-authoritative-hold`. Native live sessions own the one-slot
  identity, lifecycle legality, queue/RNG and canonical-spawn consequences,
  snapshots, and hashes. Godot dispatches one non-repeat `C` action and renders
  empty, populated, and unavailable HOLD state through the accepted NEXT
  thumbnail model/renderer. Transition-table, production-registry,
  deterministic replay/value-restore, GDExtension conformance, input/modal,
  responsive cockpit, pinned Godot 4.7.1, and full repository evidence are
  green. The fixed trace/replay schema and historical fixture results are
  unchanged. No Stage 54G polish was absorbed.
- Stage 54G is COMPLETE / FINAL MANUAL RELEASE ACCEPTANCE PASSED on
  `codex/54g-release-hardening`. The current candidate is the Godot 4.7.1
  macOS 13+ Universal 2 app/ZIP at runtime HEAD
  `fcaa450a57a43f6e1c931ceb35b98cdf2b0ccfbc`. Exact export-template pinning,
  release native build, metadata/signature/artifact inspection, two-user
  outside-tree smoke, persisted/invalid-state launches, and agent real-window
  2D/3D/4D/Hold/Settings/replay-browser evidence are recorded in
  `docs/plans/stage_54g_release_acceptance.md`. Linux and Windows are
  development-configured only, and Python/PyInstaller packaging is retained
  legacy. The first independent matrix found one Live-4D blocker after Main
  Menu / Advanced / Replay Demos / Viewer navigation. Viewer now returns
  through the app lifecycle owner and rebuilds canonical live presentation
  without resetting native gameplay. All-mode/replay regression, pinned Godot,
  full verification, rebuilt packaging, outside-tree smoke, and actual-app
  reproduction pass. No deterministic authority or accepted Fit/Reset,
  gameplay, Hold, NEXT, Ghost, replay, controls, or camera semantics changed.
  The independent final blocker re-acceptance passed for running and paused
  Live 4D, shared Live 2D/3D return, replay, immediate board visibility,
  retained gameplay/HOLD/NEXT/Ghost state, restored input ownership, and clean
  runtime logs. The bounded 4D polish decision remains disposition B.
  `PROFESSIONAL_CORE_GAME_READY` is `YES`, and the Stage 54 Professional Core
  Game programme is complete. No further Stage 54 implementation slice is
  required; later product and distribution work begins under a new programme
  or stage. The accepted package is ad-hoc signed and not notarized, so this
  product gate does not claim frictionless public macOS distribution.
- Godot topology gameplay, the Godot Topology Lab, the full Explorer, the
  challenge campaign, and unified gameplay/endgame/topology/explosion
  integration remain later programme phases.

## Current Authority

- Professional product programme and phase gates:
  `docs/plans/professional_godot_game_programme.md`
- Contributor workflow and change-class routing: `docs/WORKFLOW_CODEX.md`
- Governance router and reusable contracts: `docs/governance/README.md`
- Machine-readable policy: `config/project/policy_pack.json`
- Product behaviour: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Subsystem authority and migration ownership:
  `docs/architecture/authority_map.md`
- Authority transfer and new-authority establishment:
  `docs/architecture/authority_transfer_protocol.md`
- Documentation routing: `docs/DOCUMENTATION_MAP.md`
- Open work and deferrals: `docs/BACKLOG.md`
- Generated structure inventory: `docs/PROJECT_STRUCTURE.md`

## Known Watchouts

- Python is reference authority only for inherited, untransferred behaviour.
  It is not the mandatory origin or universal oracle for new Godot/native
  product capabilities.
- Existing inherited behaviour moves through the authority-transfer protocol.
  New behaviour without a predecessor uses authority establishment with an
  owning contract, named owner, conformance evidence, and authority-map entry.
- Stage 54B-2 must consume the established board-extent contract; Strip and
  Möbius constraints activate later through the same interface. Do not
  introduce topology-blind duplicate minima in Godot or adapters.
- Stage 54D-1 presents inherited next-piece state. Stage 54D-2 presents an
  authoritative landing query. Stage 54D-3 introduces new Hold state and must
  complete an `AE-####` establishment record during implementation, not before
  concrete contract and evidence exist.
- Native topology transport accepts only values that satisfy the shared
  topology contract and runtime query contract. It does not coerce malformed
  scalar values into valid topology data.
- Stage 53B transports and validates topology data but does not transfer
  inherited topology semantics from Python/reference contracts to C++.
- Lenient persistence or human-input recovery must stay in named source
  adapters rather than topology domain constructors.
- Invalid topology movement caches are derived-data misses: discard and
  rebuild them from the authoritative profile and dimensions; never repair
  them into semantic state. Its separate C++-dependent setup-latency deferral
  remains in `docs/BACKLOG.md`.
- Live 4D basis state is Godot presentation state only. Do not persist it,
  include it in snapshots/hashes, apply it to replay rendering, exchange Y,
  or duplicate native movement legality in GDScript.
- `state/topology/profiles.json` is a distinct version-1 edge-rule workspace
  format. Invalid existing storage may provide read-only defaults but must
  block ordinary save; destructive replacement requires an explicit recovery
  operation.
- Do not create a Python mirror solely to satisfy an obsolete universal-oracle
  claim.
- Do not let completed stage narratives return to universal agent prompts,
  review checklists, or active drift rules.
- Keep `CURRENT_STATE.md` restart-only and `docs/BACKLOG.md` open-work-only.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
## Current Metric Snapshot

From `python scripts/arch_metrics.py`:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 290` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 28` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 5.96` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.94`
2. `code_balance = 2.03`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tools/governance/validate_project_contracts.py`: `4083` real LOC
2. `tests/unit/engine/test_topology_lab_menu.py`: `3804` real LOC
3. `tests/unit/render/test_locked_cell_explosion.py`: `3782` real LOC
4. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3194` real LOC
5. `tests/unit/governance/test_governance_validate_project_contracts.py`: `2457` real LOC
6. `src/tet4d/ui/pygame/front4d_render.py`: `2153` real LOC
7. `scripts/arch_metrics.py`: `1899` real LOC
8. `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`: `1883` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 804/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 140/160 real LOC (small engine compatibility facade)`
6. `src/tet4d/ui/pygame/front2d_game.py: 116/180 real LOC (2D orchestration entrypoint)`

Tutorial wording drift guard:

1. Lesson copy must not start with `Goal:` or `Action:`.
2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.
<!-- END GENERATED:current_state_drift_watch -->

## Restart Checklist

1. Run `git branch --show-current` and `git status --short`.
2. Read `AGENTS.md`, this handoff, `docs/BACKLOG.md`, and the authorities
   routed for the active task.
3. Confirm the task contract, branch, acceptance criteria, and forbidden scope.
4. Run focused checks while iterating.
5. Before completion, run:

```bash
git diff --check
./scripts/check_git_sanitation_repo.sh
CODEX_MODE=1 ./scripts/verify.sh
```

## Next Steps

1. Execute the Stage 54F-5 human checklist over the six shipped built-in styles,
   including a clean Windows launch, and preserve real preference/capture/export
   evidence. Then contract Stage 54F-6 default presentation selection and polish;
   do not infer a winner from automated or agent-driven evidence.
2. Stop Stage 54 implementation otherwise. Future product work begins as a
   separately contracted programme or stage; do not extend 54G or create Stage
   54H.
3. Keep the Standard Live-4D legibility and live pause-badge findings as
   non-blocking post-release polish; do not reopen the already-passed matrix.
4. Keep piece/config-bundle import readers and unrelated settings recovery as
   bounded, format-specific deferrals rather than reopening generic governance
   work.
