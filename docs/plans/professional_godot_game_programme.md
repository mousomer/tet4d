# Professional Godot Game Programme

Role: authority  
Status: active  
Source of truth: this file for product priorities, phase sequencing, and
completion gates  
Supersedes: none  
Last updated: 2026-08-10

## 1. Purpose

This document defines the active long-term product programme for Tet4D.

Its first and overriding goal is:

> Deliver a fully playable, professionally presented four-dimensional game in
> Godot, with an architecture ready for professional gaming features and later
> extension into topology, spatial exploration, challenge campaigns, and
> physics simulation.

This document owns:

- programme priority and stage order;
- the boundary between the professional core game and later extensions;
- phase-completion gates;
- implementation-stage dependencies;
- the programme-level authority direction for inherited and genuinely new
  capabilities.

It does not own:

- durable feature behaviour, which belongs in `docs/rds/*`;
- architecture law, which belongs in `docs/ARCHITECTURE_CONTRACT.md`;
- current subsystem ownership, which belongs in
  `docs/architecture/authority_map.md`;
- authority transfer and establishment procedure, which belongs in
  `docs/architecture/authority_transfer_protocol.md`;
- topology-playground invariants, which belong in
  `docs/plans/topology_playground_current_authority.md`;
- current execution state, which belongs in `CURRENT_STATE.md` and
  `docs/BACKLOG.md`;
- completed implementation evidence, which belongs in architecture records and
  history.

When a programme stage changes durable product behaviour, the owning RDS and
relevant authority records must be updated in the same implementation slice.

## 2. First Product Gate

The first major gate is:

```text
PROFESSIONAL_CORE_GAME_READY
```

Tet4D must pass this gate before topology, the full Explorer, challenge
campaigns, or simulation become the dominant implementation focus.

Passing the gate means that the 4D game is not merely technically functional.
It is:

- understandable;
- configurable;
- reliable;
- visually coherent;
- responsive;
- enjoyable as a game;
- distributable;
- ready for further professional gameplay features.

The core product must:

1. provide polished 2D, 3D, and 4D play;
2. make 4D state legible rather than merely correct;
3. support direct per-axis board configuration;
4. distinguish piece rotation, camera movement, slice navigation, and 4D
   presentation-basis rotation;
5. provide a modern gameplay baseline including next-piece preview, ghost
   piece, and Hold;
6. have coherent setup, controls, menus, persistence, accessibility, display,
   performance, and packaging;
7. expose stable integration boundaries for later modes.

## 3. Product Structure

Tet4D does not have one mandatory linear progression.

It varies along four independent product axes:

| Axis | Options |
| --- | --- |
| Dimension | 2D, 3D, 4D |
| Board geometry | Validated size on every active axis |
| Topology | Bounded, strip, Möbius, and later richer spaces |
| Activity | Play, Explore, Challenge, Simulate |

This supports several player paths.

### Dimensional path

```text
2D bounded
-> 3D bounded
-> 4D bounded
```

### Topological path

```text
2D bounded
-> 2D strip
-> 2D Möbius strip
-> higher-dimensional topology
```

### Spatial-learning path

```text
contextual help
-> free manipulation
-> spatial challenges
-> placement and clearing puzzles
-> 4D challenge campaign
```

### Simulation path

```text
game or constructed state
-> final state
-> explosion or physics simulation
-> inspect, replay, or continue experimenting
```

Engineering phases may be sequential. The final product must not force every
player through one conceptual ladder.

## 4. Programme Principles

### 4.1 Product value before migration volume

Implementation priority is determined by player value, product completeness,
and measured performance.

C++ migration is not itself a product milestone.

### 4.2 New capability before repeated verification

Do not create a stage merely to re-prove lifecycle, governance, or parity
behaviour already covered by existing regression suites.

A stage must provide at least one of:

- a new user-facing capability;
- correction of an observed user-facing defect;
- removal of a demonstrated product blocker;
- an explicit bounded authority change with measurable benefit.

Regression verification remains mandatory, but is not itself a product stage.

### 4.3 Four-dimensional comprehension is gameplay

A mathematically correct state is insufficient when the player cannot read it.

The product must keep distinct:

- object position;
- object orientation;
- camera orientation;
- visible 3D basis;
- current slice axis;
- active slice;
- slice navigation;
- 4D presentation-basis rotation.

Landing preview, queue visibility, slice-aware previews, and readable basis
feedback are therefore gameplay requirements rather than optional decoration.

### 4.4 Presets are shortcuts, not restrictions

Presets should populate supported configuration values. They must not remain
the only permitted board shapes where the runtime supports a validated range.

### 4.5 Topology is independent of dimension

Topology is not simply an advanced feature after 4D. Two-dimensional bounded,
strip, and Möbius games are independently meaningful.

This does not change the immediate priority: complete the professional bounded
4D game before topology becomes the principal implementation programme.

### 4.6 Exploration is a learning mode

The Explorer is not only an editor or diagnostic surface. It is a free-practice
environment for movement, object rotation, camera rotation, re-slicing,
inspection, resetting, and repetition without game pressure.

### 4.7 Challenges are the main curriculum

Contextual prompts remain useful, but the principal tutorial system should ask
the player to solve spatial and gameplay problems.

Examples include:

- reaching a coordinate;
- matching a target orientation;
- selecting a useful slicing direction;
- fitting a piece into a cavity;
- clearing a line, plane, or hyperplane with a constrained sequence;
- using a topology seam deliberately.

## 5. Current Foundation

The project already has:

- bounded 2D, 3D, and 4D live play;
- deterministic state transitions;
- multiple piece sets;
- fixed-seed and random sessions;
- initial speed setup;
- restart and new-random-game behaviour;
- curated board presets;
- adaptive 4D slice layout;
- Godot settings, display, and accessibility infrastructure;
- strict topology contracts and native transport;
- a Python topology Editor/Sandbox/Play model;
- an existing explosion simulator and deterministic traces.

Stage 54A is complete, human accepted, and merged. It established:

- Ctrl-only soft drop;
- left-drag camera rotation;
- right-drag camera translation;
- ordinary wheel zoom;
- shared runtime/helper input authority;
- cockpit-panel ownership for interactive controls;
- clearer button/helper distinction;
- rear-face W labels;
- restrained active-slice framing.

Further visual defects are handled through later evidence-driven playability
review rather than reopening Stage 54A.

## 6. Phase I — Professional Core Game

Status: active  
Priority: highest

#### Programme-planning lenses

Use the following lenses to decompose programme work and identify the concern
that a stage addresses: deterministic gameplay, 4D representation, input
semantics, product information architecture, visual system, and product
acceptance. They are descriptive programme-planning vocabulary only; they do
not define Codex routing or task classification.

The current descriptive mapping is: 54D-3, deterministic gameplay; 54E-1/2,
4D representation and input semantics; 54E-3, product information
architecture; 54E-4/5, visual system and product information architecture;
and 54F, product acceptance.

### Stage 54A — Control and cockpit coherence

Status: complete and merged

Do not reopen the settled functional scope unless later visible-GUI review
identifies a concrete defect.

### Stage 54B — Complete custom board configuration

Objective:

Allow direct editing of every active board axis inside one validated product
envelope.

#### Fields

| Mode | Editable axes |
| --- | --- |
| 2D | X, Y |
| 3D | X, Y, Z |
| 4D | X, Y, Z, W |

Each active axis must provide:

- direct integer entry;
- increment/decrement controls;
- visible minimum and maximum;
- validation feedback;
- canonical default;
- persistence of the last valid setup;
- compatibility validation with the selected piece set;
- safe rejection of unsupported combinations.

Presets remain available:

```text
select preset
-> preset fills axis fields
-> edit any axis
-> launch validated custom game
```

#### Shared board-extent interface

One board-extent contract owns:

- product minima and maxima;
- topology input;
- piece-set compatibility;
- canonical spawn viability;
- setup and persistence validation;
- native construction limits;
- structured validation results;
- focused tests.

The selected topology is an explicit validation input. The contract must forbid
independent topology-blind hard-coded minima in Godot, native session builders,
or persistence adapters.

Phase I implements the complete bounded-board rule through this interface.
Strip and Möbius minimum-extent and seam-safety rules activate in Stage 55A
through the same interface. Later topology stages may add rules without
replacing the setup-validation architecture.

Unsupported configurations must be rejected before session construction. Do
not silently clamp an invalid request into a semantically different board.

#### Reset and lifecycle semantics

Provide separate actions:

- `Reset Sizes`: restore canonical dimensions for the selected mode;
- `Reset Setup`: restore all setup fields for the selected mode.

An active game is never resized.

- `Restart Game` reconstructs the frozen current setup.
- `Change Setup` leaves the session before another setup is constructed.

#### Implementation slices

##### Stage 54B-1 — Shared board-extent contract

Status: complete — established by `AE-0054` and integrated on `master` through
PR #63 at `c93dcc8cfa93857d514a14b925002efc4404b007`.

The topology-aware validation interface and complete bounded rule are now
implemented through `contracts/board_extent_contract_v1.json`, including:

- minima and maxima;
- piece-set compatibility;
- spawn viability;
- native construction limits;
- structured errors;
- persistence validation;
- focused native and contract tests.

It preserves the existing persistence versions and deterministic gameplay
identity. It does not implement direct size-entry UI or topology seam rules.

##### Stage 54B-2 — Godot setup and persistence

Status: complete and integrated on `master` through PR #63 at
`c93dcc8cfa93857d514a14b925002efc4404b007`.

Implement:

- editable X/Y/Z/W fields;
- increment/decrement controls;
- presets that populate editable fields;
- validation feedback;
- `Reset Sizes` and `Reset Setup`;
- last-valid-setup persistence;
- frozen-session restart semantics;
- visible-GUI acceptance.

Stage 49 and Stage 50 remain accurate records of their curated-preset scope.
Stage 54B extends the current product boundary rather than rewriting those
records.

### Stage 54C — Game-safe 4D slice-basis rotations

Status: complete and integrated on `master` through PR #63 at
`c93dcc8cfa93857d514a14b925002efc4404b007`.

Objective:

Allow the player to change the 3D slicing through which the 4D game board is
displayed while preserving the visible meaning of gravity.

#### Distinct operations

The live 4D game distinguishes:

1. **Piece rotation** — changes active-piece orientation.
2. **3D camera movement** — changes the viewpoint within the visible volume.
3. **Slice navigation** — moves along the current slice axis.
4. **Slice-basis rotation** — exchanges the slice axis with a visible
   non-gravity axis and reconstructs the slice stack.

These require separate actions, labels, helpers, and feedback.

#### Gravity invariant

```text
Y = gravity axis
```

Y remains visible and retains a stable downward presentation during live play.
The game does not exchange Y with the current slice axis.

#### Canonical basis and actions

Initial basis:

```text
Visible: X Y Z
Slices: W
```

Initial exact quarter-turns:

```text
XW +90°
XW -90°
ZW +90°
ZW -90°
```

After a basis change, the current slice axis may exchange with either visible
non-gravity axis. Both directions are supported.

#### Required update

A basis turn updates:

- visible-axis basis;
- slice axis;
- slice membership and ordering;
- labels and active-slice identity;
- basis indicator;
- grid and cell presentation;
- active and locked-piece presentation;
- framing and helper presentation.

It does not alter:

- semantic board coordinates;
- active-piece coordinates;
- gravity;
- movement or piece-rotation legality;
- scoring;
- topology;
- deterministic gameplay state.

The transition may animate between two exact states. Animation is presentation,
not semantic interpolation.

#### Focused instruction

Stage 54C includes a small instructional sequence without prematurely building
the complete challenge framework:

1. rotate the basis and observe that the object does not change;
2. choose a slicing direction that makes a piece easier to understand;
3. find a marked coordinate by re-slicing and navigating;
4. match a target visible/slice basis;
5. re-slice to inspect a difficult placement.

The lesson data should be reusable by the later challenge runner.

#### Implementation slices

1. exact basis-state and transform contract;
2. Godot controls and basis indicators;
3. slice reconstruction and presentation;
4. focused instructional sequence;
5. manual 4D comprehension review.

The exact contract is
`docs/architecture/game_safe_4d_slice_basis.md`. Godot owns this presentation
capability under the existing authority-map grant; native gameplay, topology,
snapshot/hash/replay identity, configuration, and persistence authority are
unchanged. Completion evidence covers exact group laws, exhaustive coordinate
bijection, asymmetric and W=1 layouts, basis-aware input and HUD behavior,
replay isolation, deterministic invariance, and visible GUI review.

### Stage 54D — Modern gameplay baseline

Objective:

Complete the minimum modern gameplay baseline across 2D, 3D, and 4D through
three ordered sub-slices:

```text
54D-1 Next-piece preview
-> 54D-2 Ghost piece
-> 54D-3 Hold
```

This order is load-bearing. Queue visibility and a shared piece-preview
component make Hold an informed strategic choice rather than a blind swap.

#### Stage 54D-1 — Next-piece preview

Status: complete and integrated on `master` through PR #63 at
`c93dcc8cfa93857d514a14b925002efc4404b007`.

Display exactly one authoritative next piece in live 2D, 3D, and 4D play.

The slice must:

- consume the existing next-piece value without changing queue semantics;
- provide a shared piece-thumbnail presentation used later by `HOLD`;
- support readable 2D and 3D previews;
- provide a compact slice-decomposed 4D preview;
- compose with supported viewport and accessibility settings.

Initial scope excludes:

- multiple visible queue entries;
- configurable preview depth;
- randomizer-history presentation.

Authority boundary:

- queue state remains owned by the current deterministic gameplay authority;
- Godot owns the live preview presentation;
- no snapshot, hash, replay, trace, or randomizer semantics change.

#### Stage 54D-2 — Ghost piece

Implementation status: complete and integrated on `master` through PR #63 at
`c93dcc8cfa93857d514a14b925002efc4404b007`, with native/Godot conformance
and a corrective presentation pass for grid/ghost readability, locked-cell
opacity, and exact XW/ZW/ZX view rotations.
Developer/user visual review accepted the Stage 54D-2 Ghost/board presentation;
integrated professional playability acceptance remains part of Stage 54F.

The accepted fixed dense-4D calibration artifact,
`tet4d-wireframe-grid-canonical-after.png` (SHA-256
`76c0d8ae3eaf25b047516768044b66e3599c140969739838c222a8c55fae49e1`),
confirms that the bright frame identifies only the active slice, ordinary
wireframes preserve every board volume, and the continuously visible internal
grid remains subordinate. This is Stage 54D-2 visual evidence, not Stage 54F
integrated playability acceptance.

Display the exact destination produced by the authoritative hard-drop
semantics.

The ghost must:

- use the same legality and landing result as hard drop;
- appear at every destination cell;
- appear in every affected 4D slice;
- remain distinct from active and locked cells;
- remain readable against the grid and accessibility composition;
- support `Ghost: On / Off`, default `On`.

Godot must not calculate collision, drop distance, topology traversal, or
landing legality independently. If no suitable query exists, add a bounded
read-only landing query over inherited hard-drop semantics.

The landing query does not transfer authority and must not create a second drop
algorithm.

Ghost state is presentation-only and must not enter:

- gameplay snapshots;
- state hashes;
- replay identity;
- scoring;
- collision;
- lock state.

Use the existing `ghost.enabled` capability vocabulary unless the owning RDS
explicitly replaces it.

#### Stage 54D-3 — Hold

Status: unblocked deterministic-core work after the accepted Stage 54E-1
record is merged. Hold does not require Stage 54E-2.

Add one-slot Hold after next-piece and ghost presentation are accepted. Its
only presentation dependency is the shared piece thumbnail already delivered
by Stage 54D-1. Hold changes deterministic gameplay state and must not be
absorbed into the presentation-architecture refactor.

A successful Hold action:

- stores the active piece when the slot is empty and activates the next queued
  piece;
- swaps active and held pieces when the slot is occupied;
- becomes unavailable until the resulting active piece locks;
- respawns the incoming piece at canonical spawn position and orientation;
- does not preserve the outgoing piece pose;
- does not rewind or reshuffle the queue;
- does not consume a queue entry during an occupied-slot swap.

Failure to spawn the incoming piece uses normal game-over policy.

Hold stores piece identity, not:

- position;
- active slice;
- orientation;
- camera state;
- view basis;
- presentation layout.

Ordinary setup may expose:

```text
Hold: On / Off
```

The modern standard game defaults to `On`. Initial support is exactly one slot.
The `HOLD` preview reuses the Stage 54D-1 thumbnail presentation.

Hold changes deterministic state. Its implementation slice must define:

- Hold state owner;
- queue-transition owner;
- held-piece and availability snapshot fields;
- state-hash inclusion;
- replay and trace schema behaviour;
- old-replay compatibility;
- restart semantics;
- failed-spawn policy;
- safe failure or fallback;
- conformance evidence;
- authority-map update.

Keep Hold as refined deferred-candidate prose in
`docs/architecture/authority_transfer_protocol.md` until implementation
provides concrete contracts, code, compatibility decisions, and evidence.
Stage 54D-3 then creates and completes an `AE-####` authority-establishment
record. Do not create an incomplete placeholder row in advance.

### Stage 54E — 4D Presentation & Interaction Architecture

Objective:

Establish a deliberate presentation and interaction architecture for live 4D
play before changing the existing runtime. The current presentation conflates
three concepts that must become explicit and separately owned:

1. exact 4D `BasisState` rotation;
2. slice-local 3D camera orientation: how the volume inside every individual
   slice is viewed;
3. slice-set/layout transformation: how the collection of slice volumes is
   arranged and viewed as a collection.

The slice sequence is a presentation-layout coordinate. It is not the local X
axis of each 3D slice.

#### Stage 54E-1 — Presentation-space architecture/design

Status: complete — human accepted.

The accepted contract is
`docs/architecture/4d_presentation_interaction_architecture.md`. It adopts
Option A, records the `DEFECTIVE` combined-camera-yaw verdict, accepts normal
gameplay roll removal while preserving Explorer/free-inspection roll, and
accepts the constrained pitch-depth-preservation policy. No runtime
implementation is part of the acceptance record.

54E-1 completes only when its accepted design provides all of the following:

1. precise definitions of exact 4D `BasisState` space, slice-local 3D
   camera/view space, and slice-set/layout space, including the coordinate
   frame each acts in and what it may change;
2. one explicit transform-composition model/order that distinguishes canonical
   gameplay coordinates, exact 4D basis mapping, per-slice local 3D
   presentation, slice anchor/layout placement, and final camera/view
   transformation;
3. an owner for every resulting presentation state, explicitly distinct from
   deterministic gameplay state, topology state, snapshots, hashes, and replay
   identity, with any new authority boundary following the established protocol;
4. persistence and lifecycle decisions for every presentation-space state:
   ephemeral interaction, reset-view, game/session-local, persisted
   presentation preference, setup state, or deliberately non-persistent, with
   behaviour defined for new game, restart game, change setup, reset view, and
   application restart;
5. scene-graph consequences that state where per-slice local orientation,
   slice layout/anchors, and outer viewing-camera transforms belong and must
   not belong;
6. an audit of `ControlFrameMapping`, `CameraRig.control_frame_yaw()`, exact
   `SliceBasis4D` state, slice anchor/layout generation, and the live input
   resolver construction. The audit must issue a definite `CONFORMING` or
   `DEFECTIVE` verdict, with architectural reasoning that decides whether the
   yaw used by the resolver is the required slice-local 3D orientation or
   incorrectly includes slice-set/layout viewing transformation;
7. these architecture invariants:
   - a slice-local 3D Y rotation changes the internal X/Z view identically in
     every slice while leaving slice anchors and slice ordering unchanged;
   - a slice-layout transformation changes slice anchors/layout without
     changing the local 3D coordinate frame inside each slice;
8. a verification design explaining how those invariants become executable
   regression coverage in 54E-2, without deliberately committing failing
   current tests; and
9. a bounded 54E-2 implementation plan: affected Godot components, proposed
   state owners, scene-graph changes, migration sequence, compatibility/reset
   implications, focused regression coverage, human-visible verification, and
   forbidden scope.

The accepted architecture decides the transform order and ownership for 54E-2;
runtime authority records remain contingent on concrete implementation evidence.

#### Stage 54E-2 — Camera-space separation implementation

Status: COMPLETE — REVIEWED GREEN. Stages 54E-2a, 54E-2b, 54E-2c, and
54E-2d are all complete and reviewed green.

Implement the architecture accepted in 54E-1. Separate the relevant
presentation transforms without changing canonical gameplay coordinates,
collision, scoring, RNG, topology semantics, deterministic snapshots/hashes,
or replay identity, unless the accepted design identifies a presentation-only
replay concern.

The mandatory reviewed-green sequence is 54E-2a (presentation state and
coordinate decomposition), then 54E-2b (renderer composition), then 54E-2c
(interaction and camera-rig separation), then 54E-2d (lifecycle, authority,
and contract reconciliation). All four slices are complete and reviewed green.
No later slice may repair a prior slice, and a monolithic 54E-2 implementation
is forbidden.

Stage 54E-2c established that interactive yaw/pitch changes to shared `L`
refresh renderer-derived orientation state and recompute oriented fit bounds,
so geometry and the fitting envelope cannot diverge.

Stage 54E-2d implements and closes the accepted lifecycle: fresh
entry/new/random/restart defaults; presentation-only Reset View; internal
basis-only reset; synchronous setup/menu/mode teardown and coherent re-entry;
public roll removal with generic low-level capability retained; and
settings/setup/native/replay exclusion evidence. External technical review
accepted the implementation. No authority transfer or establishment occurs.

#### Stage 54E-3 — Setup/menu information architecture

Status: COMPLETE / REVIEW PENDING. Stage 54E-3a taxonomy and classification and
Stage 54E-3b progressive-disclosure rendering are both implemented with
automated and real-window evidence recorded.

The 4D setup surface had exceeded an acceptable flat complexity level and now
uses progressive disclosure. The durable taxonomy and its rules are owned by
`docs/rds/RDS_MENU_STRUCTURE.md`. This stage implements that approved
information architecture and reuses the existing
`menu_structure_single_source`, `menu_control_typing_contract`, and menu-graph
machinery wherever enforcement is required; it introduces no menu validator for
the taxonomy and no general-purpose disclosure framework.

Stage 54E-3a records direct seed input as the semantic setup control type
`numeric_entry`; Godot maps that type to its existing `LineEdit`. This is a
typing-contract clarification, not a setup behavior or identity change. Stage
54E-3b keeps board-axis controls as `stepper`, because their ranges are small
enough for stepping to be the primary interaction.

Stage 54E-3b makes ordinary setup the board preset shortcut, the piece-set
choice where a mode publishes more than one set, and the starting speed, with
board customization, reproducibility, and control frames behind secondary
disclosure. The panel no longer keeps a second copy of the declared visibility
rules; mode applicability and the conditional seed rule resolve through
`SetupFieldRegistry`. Disclosure is ephemeral presentation state that never
reaches canonical session setup, the persisted setup document, or native
session state, so no schema version changes. Undisclosed controls leave the
focus ring, a collapsing section that holds focus hands focus to its own
disclosure control, and a validation failure inside a collapsed section stays
explained and reachable.

#### Stage 54E-4 — Camera/GUI presets

Current camera/GUI presets are provisional pending the corrected camera-space
model. After 54E-2, decide what camera and GUI/layout presets transform,
whether combined presets are permitted, the affected presentation spaces,
reset behaviour, and persistence ownership. This programme does not make those
decisions or redesign existing presets now.

54E-4 may begin only after 54E-2 is complete.

#### Stage 54E-5 — Cockpit consolidation

After the preceding semantics are stable, rationalize the cockpit, helper
surfaces, indicators, buttons, camera/layout controls, and presentation
affordances. This is a bounded consolidation pass, not authorization for an
unbounded visual rewrite.

Stage 54E-5 completes when the cockpit surfaces identified by the accepted
54E architecture are consolidated onto their intended state owners,
contradictory or redundant presentation/control displays are removed, and the
resulting cockpit passes focused consistency and visible-GUI review. It does
not authorize unrelated visual redesign.

### Stage 54F — Integrated professional playability/visual acceptance

Objective:

Conduct a real, evidence-driven human playability review of integrated 2D, 3D,
and 4D play, with primary emphasis on 4D and the corrected Stage 54E
architecture. It does not begin with a speculative rewrite list.

Review basis-rotation comprehension; slice-local camera and slice-layout
manipulation; viewer-relative controls; setup progressive disclosure;
camera/GUI presets; cockpit consolidation; NEXT; Ghost; Hold; board/grid/cell
hierarchy; accessibility; viewport composition; responsiveness; pause,
restart, setup, and game-over usability.

Stage 54F completes only when representative human-visible review evidence is
recorded, findings are classified by severity and gate impact, each
`PROFESSIONAL_CORE_GAME_READY` blocker is corrected and re-reviewed or remains
an explicit blocker, and non-blocking defects have an owner or deliberate
deferral. Grid strengthening is required only if evidence classifies grid
visibility as blocking comprehension or accessibility.

### Stage 54G — Professional gaming-experience and release hardening

Objective:

Close the gap between a verified prototype and a professional game release.

Use focused slices for demonstrated needs such as:

- full keybinding/remapping workflow;
- gamepad support if adopted;
- audio, mute, and volume controls;
- polished pause and game-over presentation;
- scoring and progression presentation;
- persistence and recovery;
- performance correction;
- installer, export, and launch reliability;
- user help and release documentation;
- final manual acceptance.

## 7. Professional Core Game Gate

Phase I is complete only when the following hold.

### Gameplay

- 2D, 3D, and 4D are fully playable.
- 4D is understandable rather than merely operational.
- Movement, piece rotation, soft/hard drop, lock, clear, scoring, pause,
  restart, and game over are reliable.
- Next-piece preview reflects the authoritative queue.
- Ghost projection matches authoritative hard drop.
- Hold follows its established deterministic contract.
- Custom dimensions work within supported limits.
- Presets remain convenient.
- deterministic restart and random-session behaviour remain coherent.

### 4D presentation

- visible axes and slice axis are explicit;
- slice navigation works;
- exact game-safe basis quarter-turns work;
- basis changes do not mutate gameplay state;
- camera and basis controls are distinct;
- next-piece and Hold previews are readable;
- ghost cells appear in every affected slice;
- ghost, active, and locked cells are distinguishable;
- cells, grid, labels, and frames remain readable.

### Product shell

- setup, menus, settings, play, pause, restart, and return paths are coherent;
- controls and helper text share authority;
- interactive controls and passive help are visually distinct;
- essential controls do not clip at supported viewports;
- accessibility and display settings compose correctly.

### Semantic boundaries

- Godot does not independently calculate queue order or landing legality;
- ghost remains presentation-only;
- Hold state participates in deterministic identity;
- old replay formats follow an explicit compatibility rule;
- subsystem authority is explicit.

### Reliability, performance, and release

- automated verification is green;
- representative manual play has passed;
- invalid setup and failed construction recover safely;
- supported package/startup paths work;
- no known high-severity gameplay or data-loss defect remains;
- start, setup, and basis transitions are responsive;
- supported board maxima remain usable.

### Extension readiness

- GDScript does not duplicate inherited deterministic rules;
- board setup, view basis, topology profile, challenge state, and simulation
  input have stable boundaries;
- later modes can reuse shared semantics instead of forking them.

Passing this gate does not require complete topology, Explorer, challenge, or
physics features.

## 8. Phase II — First-Class Topological Games

Status: planned  
Dependency: professional core-game gate, except for isolated architecture work

### Stage 55A — 2D topology games

Expose three first-class 2D games:

1. `Bounded`
2. `Strip`
3. `Möbius Strip`

Requirements:

- normal setup access;
- concise visual explanation;
- visible seam behaviour;
- exact canonical topology transport;
- deterministic identity;
- no silent fallback to bounded play;
- product labels separate from stable internal IDs;
- inherited topology semantics reused rather than rewritten;
- Strip and Möbius extent/seam-safety rules activated through the Stage 54B
  board-extent interface.

The mapping from current generic topology presets to these product concepts
must be verified rather than assumed.

### Stage 55B — Higher-dimensional topology play

After 2D topology acceptance:

- expose selected canonical 3D and 4D topology presets;
- preserve exact topology transport;
- show seam and transformation feedback;
- distinguish topology effects from projection, slice navigation, and basis
  rotation;
- retain bounded play as the default reference case.

Do not expose every editor possibility as an ordinary game preset.

## 9. Phase III — Explorer as Spatial Practice

Status: planned  
Dependency: stable view-basis controls; topology support may be incremental

The Godot Explorer is a player-facing practice environment. It should preserve
the accepted conceptual distinction among Editor, Sandbox, and Play. The
Sandbox/practice path may arrive before the complete editor migration.

The Explorer permits deliberate movement in both directions along every axis:

```text
X ±
Y ±
Z ±
W ±
```

Y is not privileged by gravity unless an experiment explicitly enables
gravity.

The Explorer exposes continuous and exact camera controls, complete 4D basis
control including Y/slice exchange, independent camera/basis/slice/object
state, reset operations, coordinate inspection, topology selection, deliberate
seam traversal, and transition into Play.

Explorer must not create a second movement, rotation, or topology rule system.

## 10. Phase IV — Challenge and Learning System

Status: planned  
Dependency: stable gameplay, basis controls, and a reusable Explorer path

The primary tutorial becomes a data-driven challenge system.

Challenge families include:

- target-pose challenges;
- piece-rotation challenges;
- camera-orientation challenges;
- view-basis challenges;
- navigation challenges;
- placement challenges;
- line/plane/hyperplane-clearing puzzles;
- topology challenges;
- scored and constrained puzzle campaigns.

Begin with a small representative vertical slice rather than the complete
campaign.

## 11. Phase V — Unified Product

Status: long-term

The mature product connects activities without collapsing their ownership.

```text
Play -> Game Over -> Replay / Explore Final Board / Simulate
Topology Editor -> Sandbox -> Play This Topology
Challenge -> Practise in Explorer -> Retry
Constructed State -> Run Physics Simulation
```

Simulation may consume a game board, Explorer state, challenge state, topology
profile, or constructed scenario through an explicit versioned conversion
boundary.

Gameplay state must not be silently reinterpreted as physics state.

## 12. Authority Model

Authority is subsystem-specific.

The governing documents are:

- `docs/architecture/authority_map.md` for current ownership;
- `docs/architecture/authority_transfer_protocol.md` for inherited authority
  transfer and new authority establishment;
- `docs/architecture/parity_protocol.md` for inherited parity evidence.

Python remains reference authority only for inherited behaviour that has not
been transferred or retired.

Godot owns product and presentation semantics, including menus, setup
interaction, input routing, HUD, camera, layout, animation, guidance,
accessibility, and diagnostics. It must not duplicate inherited deterministic
rules.

New deterministic behaviour without a predecessor may establish native
authority directly through a normative contract, implementation, conformance
evidence, compatibility rules, an establishment record, and authority-map
update. Do not create a Python mirror solely to manufacture an oracle.

A product stage may combine several authority lanes. Stage 54D is the immediate
example:

- next preview: Godot presentation of inherited queue state;
- ghost: Godot presentation over an inherited read-only landing query;
- Hold: genuinely new deterministic state requiring authority establishment.

## 13. Implementation and PR Discipline

Each implementation PR must have one bounded semantic objective.

Use separate PRs for:

- Stage 54B-1 board-extent contract;
- Stage 54B-2 Godot setup and persistence;
- Stage 54C bounded implementation slices;
- Stage 54D-1 next-piece preview;
- Stage 54D-2 ghost piece;
- Stage 54D-3 Hold;
- Stage 54E-1 presentation-space architecture/design;
- Stage 54E-2 camera-space separation implementation;
- Stage 54E-3 setup/menu information architecture;
- Stage 54E-4 camera/GUI presets;
- Stage 54E-5 cockpit consolidation;
- Stage 54F integrated playability/visual acceptance;
- Stage 54G release hardening.

Do not combine all of Phase I into one branch.

Every implementation PR must identify:

- owning product/RDS contract;
- current or newly established semantic authority;
- presentation owner;
- persistence, replay, and compatibility impact;
- focused tests;
- visible-GUI acceptance where relevant;
- remaining risks and deferrals.

## 14. Immediate Execution Order

The active order is:

1. Stages 54B-1, 54B-2, 54C, 54D-1, and 54D-2 are integrated on `master`
   through PR #63 at `c93dcc8cfa93857d514a14b925002efc4404b007`.
2. Stage 54E-1 — presentation-space architecture/design is complete, human
   accepted, and merged at `7e3558f823dd496b8896eabe6da9c18951bdb005`.
3. Stage 54D-3 — Hold is eligible and does not wait for 54E-2.
4. Stage 54E-2a — presentation state and coordinate decomposition is complete
   and reviewed green.
5. Stage 54E-2b — renderer composition — is complete and reviewed green;
   Stage 54E-2c — interaction and camera-rig separation — is complete and
   reviewed green; Stage 54E-2d — lifecycle, authority, and contract
   reconciliation — is complete and reviewed green. Aggregate Stage 54E-2 is
   complete and reviewed green.
6. Stage 54E-3 — setup/menu information architecture — is COMPLETE / REVIEW
   PENDING: Stage 54E-3a taxonomy and classification and Stage 54E-3b
   progressive-disclosure rendering are both implemented, with automated and
   real-window evidence recorded.
7. Stage 54E-4 — camera/GUI presets — is NEXT / ELIGIBLE.
8. Stage 54E-5 — cockpit consolidation.
9. Stage 54F — integrated professional playability/visual acceptance.
10. Stage 54G — remaining professional release hardening.
11. Stage 55A — first-class 2D bounded, Strip, and Möbius games.
12. Later Explorer, challenge, topology, and simulation phases.

Stage numbers do not imply that 54D-3 must run before 54E-1. Stage 54D-2
corrected the reviewed live-grid readability weakness and has developer/user
Ghost/board visual acceptance; this is not Stage 54F integrated acceptance.

Compaction or splitting of `docs/history/DONE_SUMMARIES.md` belongs to a
separate documentation-hygiene batch. Historical archive size is not active
product work and must not be mixed into Phase I implementation PRs.
