# Tet4d Topology Playground Restructuring Plan
## Canonical mode model, movement semantics, runtime authority, and staged migration

## 1. Purpose

This plan restructures the topology playground around a smaller, clearer, and more stable interaction model.

The current system has these failures:

- top-level modes mix **purpose**, **movement model**, and **rule set**
- 2D and ND diverge semantically where they should differ only in projection/picking
- Inspect and Edit are artificially separated, creating clutter and unclear workflows
- Sandbox bundles unrelated behaviors, especially hidden ND neighbor-search
- Play mode still leaks through non-canonical logic, causing runtime bugs such as incorrect drop/lock behavior
- helper panels are incomplete or inconsistent
- menu and button hierarchy is cluttered because submodes have been promoted to top-level modes

This plan fixes that by:

- reducing the top-level mode count
- separating **workspace**, **tool**, **movement target**, and **rule set**
- enforcing canonical runtime authority for gameplay
- making higher-dimensional behavior consistent at the semantic layer
- migrating in stages with regression coverage

---

## 2. Target user-facing structure

## Top-level workspaces

The playground should expose exactly **three** top-level workspaces:

1. **Editor**
2. **Sandbox**
3. **Play**

This replaces the current top-level split:

- Edit
- Inspect
- Sandbox
- Play

### Why this is correct

Inspect and Edit are part of one real workflow:
- move around
- inspect the current target
- preview change
- apply or cancel

They should not be separate top-level modes.

Sandbox is a separate purpose:
- free experimentation with piece motion and topology behavior

Play is a separate purpose:
- real gameplay rules

That is the correct top-level split.

---

## 3. Semantic model

## 3.1 Editor workspace

### Purpose
Inspect, select, analyze, and modify topology / board state.

### Core rule
The user always has a safe cursor/probe/selection substrate.  
Mutation happens only through explicit tools/actions.

### Internal structure
Editor contains three kinds of tools:

#### A. Selection / Probe tools
Non-destructive tools used for:
- moving the editor cursor
- selecting a cell / region / topology entity
- tracing movement
- showing coordinates / transport / adjacency

This is what current “Inspect” should become.

#### B. Edit tools
Mutating tools used for:
- toggling or placing cells
- erasing cells
- modifying topology attachments / glueings
- setting anchors / markers / edit targets
- applying structural changes deliberately

This is what current “Edit” should become.

#### C. Analysis overlays/tools
Tools used for:
- neighbor search
- adjacency highlight
- transport preview
- connectivity / reachability overlays

These are not top-level modes.

### Movement target
Editor movement always moves:
- the editor probe / cursor / selection

Editor movement must never move:
- the sandbox piece
- the gameplay piece

### Mutation rule
Cursor movement is always safe.  
Mutation requires:
- an explicit edit tool
- an explicit apply/placement action

This is mandatory. Without it, the unified Editor becomes dangerous and unclear.

---

## 3.2 Sandbox workspace

### Purpose
Free experimentation with a projected piece and topology behavior outside real gameplay constraints.

### Core rule
Sandbox is not gameplay and not board editing.  
It is controlled simulation / experimentation.

### Allowed capabilities
- spawn or reset projected piece
- move and rotate piece
- test topology transport
- optionally enable or disable gravity
- optionally enable or disable locking
- optionally enable or disable neighbor-search overlay
- show transport / adjacency / landing overlays

### Movement target
Sandbox movement always moves:
- the sandbox piece

Sandbox movement must never move:
- the editor probe
- the gameplay piece

### Important correction
Neighbor-search is **not** intrinsic to ND Sandbox.  
It must be an explicit Sandbox option or overlay.

### Required split
Sandbox must support:
- **Sandbox without neighbor search**
- **Sandbox with neighbor search**

The ND-only hidden bundled behavior must be removed.

---

## 3.3 Play workspace

### Purpose
Actual gameplay on the selected topology.

### Core rule
Play uses real game rules:
- real gravity
- real support
- real lock behavior
- real line/layer/drop semantics

### Movement target
Play movement always moves:
- the active gameplay piece

Play movement must never move:
- the editor probe
- the sandbox piece

### View options
The current “play mode / exploration mode” under Play should be treated as:
- view/presentation/control variants inside Play

Unless they differ in actual rules, they are not separate conceptual modes.

### Runtime authority
Gameplay decisions must use canonical runtime state only.  
No gameplay-critical logic may depend on:
- retained shell snapshot state
- scene-derived projection state
- panel-owned inspection state
- legacy normal-mode helpers that assume non-topological semantics

This directly addresses the current drop-layer / lock bug.

---

## 4. Movement model

The system is currently inconsistent because different modes move different hidden objects under different hidden rules.

That must end.

## 4.1 One movement contract per workspace

### Editor
Movement moves the editor probe / selection.

### Sandbox
Movement moves the sandbox piece.

### Play
Movement moves the gameplay piece.

This must be explicit in code and UI help.

## 4.2 Shared semantic stepping model

The semantic stepping model should be shared across dimensions:

- step intent is defined canonically
- topology transport is resolved canonically
- 2D / 3D / 4D differ only in:
  - projection
  - picking
  - view overlay

They must not differ in semantic meaning of movement.

## 4.3 Editor movement specifics

Editor movement should support:
- canonical cell stepping
- optional trace recording
- optional transport annotation

It should not inherit piece movement semantics.

## 4.4 Sandbox movement specifics

Sandbox movement should support:
- piece translation
- piece rotation
- transport across topological boundaries
- optional simulation overlays

Neighbor-search, if enabled, is derived from the sandbox piece state. It is not itself the moved object.

## 4.5 Play movement specifics

Play movement should support:
- gameplay translation/rotation/drop consistent with actual rules
- canonical topology transport
- canonical support/grounded/lock evaluation

This must be runtime-authoritative and dimension-consistent.

---

## 5. Canonical state architecture

## 5.1 Rule

All semantically important state must live in canonical playground/runtime state.

Retained shell, scene, panel, and snapshot state may visualize or cache. They may not adjudicate gameplay or semantic truth.

## 5.2 Gameplay-critical canonical sources

For Play, the same canonical post-transport state must drive:

- move acceptance
- continued fall eligibility
- grounded/support detection
- lock decision
- active piece rendering

Any split here is a bug.

## 5.3 Editor canonical sources

For Editor, the canonical source must drive:
- selected entity / canonical target
- trace
- analysis overlays
- edit preview anchor
- apply target

Projection state may help pick. It may not become the semantic source of truth.

## 5.4 Sandbox canonical sources

For Sandbox, the canonical source must drive:
- sandbox piece state
- neighbor-search seed/source when enabled
- gravity / lock toggles and their effects
- transport overlays

---

## 6. UI restructuring

## 6.1 Primary controls

The primary mode toolbar should contain only:

- Editor
- Sandbox
- Play

Nothing else belongs at that hierarchy level.

## 6.2 Contextual secondary panel

Each workspace gets its own contextual panel.

### Editor panel
Contains:
- selection/probe tools
- edit tools
- analysis overlays
- coordinate/trace/transport toggles

### Sandbox panel
Contains:
- piece controls
- spawn/reset
- gravity toggle
- lock toggle
- neighbor-search toggle
- sandbox overlays

### Play panel
Contains:
- gameplay controls
- play/exploration view option
- topology-specific play information
- gameplay helper info

## 6.3 Advanced/debug drawer

Move non-core clutter into an advanced/debug drawer:
- projection/debug settings
- migration shims
- legacy compatibility toggles while migration is incomplete
- developer-only inspection options

## 6.4 Helper panels

Each workspace must have a clear helper panel.

### Editor helper
Explains:
- cursor movement
- selection meaning
- active tool
- edit apply/cancel semantics
- analysis overlay meanings

### Sandbox helper
Explains:
- piece movement/rotation
- reset/spawn actions
- gravity/locking toggles
- neighbor-search toggle and meaning

### Play helper
Explains:
- controls
- view option
- topology-specific gameplay effects
- layer/drop semantics if relevant

This is required to reduce ambiguity and button clutter.

---

## 7. Current bugs mapped to the new structure

## Bug 1 — Inspect movement is wrong and inconsistent
Under the new structure, this becomes:

- Editor probe/cursor movement is wrong and inconsistent

Fix:
- define one canonical Editor probe movement contract
- keep 2D/3D/4D differences only in projection/picking
- add tests ensuring consistent semantic target resolution

## Bug 2 — Sandbox should allow with/without neighbor search
Fix:
- make neighbor-search a Sandbox option/overlay
- remove hidden ND-only bundling
- add explicit mode state and UI toggle

## Bug 3 — Play → Play this topology has a drop-layer issue
Fix:
- decouple from UI restructure
- repair canonical Play runtime path
- ensure support/grounded/lock uses transported canonical coordinates
- add live-path regression tests in 3D/4D

## Bug 4 — Sandbox mode needs helper panel
Fix:
- add dedicated Sandbox helper panel from shared helper schema

## Bug 5 — Edit mode is very unclear
Fix:
- remove Edit as a top-level mode
- make it a tool family inside Editor
- define safe probe/selection vs explicit mutating tools

## Bug 6 — Button and menu clutter
Fix:
- reduce top-level modes to three
- move tool/options into contextual secondary panel
- move advanced/debug options into drawer

---

## 8. Migration phases

## Phase 1 — Semantic freeze and naming cleanup

### Goal
Stop further drift by locking the target model.

### Tasks
- define Editor / Sandbox / Play as the only user-facing top-level workspaces
- demote Inspect into Editor selection/probe tools
- demote Edit into Editor edit tools
- define neighbor-search as an explicit tool/overlay, not a hidden ND behavior
- define movement target per workspace in code comments, internal types, and docs

### Outputs
- shared vocabulary
- stable target architecture
- explicit internal identifiers for workspace/tool states

### Acceptance
- no ambiguous top-level “Inspect” or “Edit” mode remains in the target model
- no code/documentation treats Sandbox as implicitly including neighbor-search

---

## Phase 2 — Play runtime stabilization

### Goal
Fix gameplay-critical correctness before broader UI restructuring.

### Tasks
- trace live Play path through topology transport, support, grounded, and lock logic
- remove/bypass any gameplay-critical dependency on:
  - retained shell state
  - scene refresh results
  - panel/inspection state
  - legacy normal-mode helpers with non-topological assumptions
- enforce one canonical post-transport active-piece state for:
  - movement acceptance
  - fall continuation
  - support detection
  - lock decision
  - rendering

### Outputs
- 3D/4D drop/lock bug fixed
- canonical gameplay authority restored

### Acceptance
- seam traversal in 3D/4D no longer causes false immediate lock when continuation exists
- tests cover live play/runtime path

---

## Phase 3 — Editor unification

### Goal
Replace separate Inspect/Edit mode behavior with one Editor workspace.

### Tasks
- create or formalize shared Editor selection/probe state
- move inspect functionality into non-destructive Editor tools
- move edit actions into explicit Editor edit tools
- ensure movement always acts on the Editor probe, not world state
- add edit apply/cancel clarity
- unify helper panel

### Outputs
- single Editor workspace
- reduced top-level clutter
- clearer workflow

### Acceptance
- user can inspect and preview edits without leaving Editor
- edits only occur via explicit tool/application action
- helper panel explains the difference

---

## Phase 4 — Sandbox cleanup

### Goal
Make Sandbox a clear free-simulation workspace.

### Tasks
- separate Sandbox from hidden neighbor-search behavior
- add explicit Sandbox toggles:
  - neighbor-search on/off
  - gravity on/off
  - locking on/off
- unify sandbox piece control semantics
- add Sandbox helper panel
- ensure 2D and ND differ only where projection requires it

### Outputs
- clean Sandbox behavior
- explicit options
- helper support

### Acceptance
- Sandbox behavior is understandable in both 2D and ND
- neighbor-search is optional and explicit
- movement target is clearly the sandbox piece

---

## Phase 5 — Projection and semantic consistency

### Goal
Make 2D/3D/4D consistent semantically.

### Tasks
- define canonical target/result type for Editor selection
- define canonical piece/result type for Sandbox and Play
- move dimension-specific logic into:
  - picking adapters
  - projection adapters
  - overlay renderers
- remove semantic divergence where 2D/3D/4D currently behave differently without justification

### Outputs
- shared semantics
- dimension-specific adapters only

### Acceptance
- 2D/3D/4D resolve to the same semantic output types
- behavior differs only due to projection/picking, not because of arbitrary mode forks

---

## Phase 6 — Menu and panel decomposition

### Goal
Reduce structural clutter after semantics are stabilized.

### Tasks
- decompose large menu/controller files such as `topology_lab_menu.py`
- migrate retained panel responsibilities into canonical playground state
- consolidate helper-panel definitions into shared schema/config
- delete obsolete legacy bridges after behavior is covered by tests

### Outputs
- smaller modules
- less retained-state debt
- cleaner ownership boundaries

### Acceptance
- menu files become orchestration layers rather than semantic owners
- canonical state holds semantic truth
- legacy bridges can be removed safely

---

## 9. Testing strategy

## 9.1 Play regression tests
Add live-path tests for:
- 3D topology seam traversal does not cause false lock
- 4D topology seam traversal does not cause false lock
- grounded/support/lock uses transported canonical coordinates

## 9.2 Editor tests
Add tests for:
- probe movement semantics are consistent across dimensions at the semantic layer
- selection resolves to canonical targets
- edit tools mutate only through explicit apply actions
- trace and transport overlays do not mutate state

## 9.3 Sandbox tests
Add tests for:
- Sandbox with neighbor-search off
- Sandbox with neighbor-search on
- gravity on/off
- locking on/off
- sandbox piece movement independent of Editor/Play state

## 9.4 Mode/workspace tests
Add tests for:
- top-level workspace switching preserves correct state boundaries
- Editor, Sandbox, and Play do not share movement targets improperly
- menu/runtime state round-trips correctly

## 9.5 UI/helper tests
Add tests or snapshots for:
- contextual helper panel contents by workspace
- top-level toolbar reduction
- contextual options visibility

---

## 10. Internal implementation rules

These rules must be treated as hard constraints.

### Rule 1
Top-level workspaces are:
- Editor
- Sandbox
- Play

### Rule 2
Inspect is not a top-level mode.  
It is a non-destructive toolset inside Editor.

### Rule 3
Edit is not a top-level mode.  
It is a mutating toolset inside Editor.

### Rule 4
Sandbox does not implicitly include neighbor-search.  
Neighbor-search must be explicit.

### Rule 5
Gameplay-critical logic must not depend on scene/panel/snapshot state.

### Rule 6
Dimension-specific code may adapt projection/picking only.  
Semantic truth must remain shared.

### Rule 7
Movement target must be explicit and workspace-specific.

### Rule 8
Helper content must be contextual and workspace-specific.

---

## 11. Expected benefits

If implemented correctly, this restructuring will:

- eliminate top-level mode clutter
- make Edit understandable by folding it into a clear Editor workflow
- make Inspect consistent by redefining it as Editor probe movement
- stop ND Sandbox from hiding unrelated behaviors
- support a proper Sandbox helper panel
- isolate and fix Play runtime bugs without conflating them with UI work
- reduce semantic divergence between 2D, 3D, and 4D
- create a clean basis for later decomposition and legacy deletion

---

## 12. Risks and failure modes

## Risk 1 — Collapsing Inspect and Edit too aggressively
Failure mode:
- edits happen accidentally during inspection

Mitigation:
- explicit tool arming
- explicit apply action
- safe cursor movement always

## Risk 2 — Treating Sandbox as Edit again
Failure mode:
- Sandbox semantics become muddled and unclear

Mitigation:
- keep Sandbox strictly piece-simulation oriented
- keep world mutation in Editor only

## Risk 3 — Fixing UI before runtime correctness
Failure mode:
- Play remains broken under a cleaner menu

Mitigation:
- repair canonical Play runtime in Phase 2 before major UI cleanup

## Risk 4 — Letting 3D/4D keep separate semantic logic
Failure mode:
- inconsistency persists under renamed modes

Mitigation:
- enforce shared semantic target/result types
- isolate dimension-specific logic to adapters only

---

## 13. Immediate next implementation target

The first implementation pass should do the following:

1. freeze the new workspace model in code/docs
2. pin the Play drop/lock bug with live-path tests
3. separate Sandbox neighbor-search into an explicit option/state
4. begin the Editor unification by defining safe probe/selection semantics
5. add helper-panel scaffolding per workspace

That is the correct first stage.
