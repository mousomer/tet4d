# Task Contract — Canonical Local Board Presentation Geometry

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
