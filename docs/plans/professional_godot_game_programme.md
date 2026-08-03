# Professional Godot Game Programme

Role: authority  
Status: active  
Source of truth: this file for product-programme priorities, phase sequencing,
and completion gates  
Supersedes: none  
Last updated: 2026-08-03

## 1. Purpose

This document defines the active long-term product programme for Tet4D.

Its first and overriding goal is:

> Deliver a fully playable, professionally presented four-dimensional game in
> Godot, with a stable product architecture that supports later extension into
> topology, free spatial exploration, challenge campaigns, and physics
> simulation.

This document owns:

- the order of major product capabilities;
- the boundary between the professional core game and later extensions;
- phase-completion gates;
- dependencies between board configuration, four-dimensional view controls,
  Hold, topology, exploration, challenges, and simulation;
- the authority model used when new capabilities no longer have a Python
  predecessor.

This document does not own:

- detailed durable behaviour, which belongs in `docs/rds/*`;
- architecture law, which belongs in `docs/ARCHITECTURE_CONTRACT.md`;
- subsystem authority records, which belong in
  `docs/architecture/authority_map.md`;
- topology-playground invariants, which belong in
  `docs/plans/topology_playground_current_authority.md`;
- current restart context, which belongs in `CURRENT_STATE.md`;
- open execution work and deferrals, which belong in `docs/BACKLOG.md`;
- completed implementation evidence, which belongs in architecture records and
  history.

When a programme stage changes durable product behaviour, the owning RDS must
be updated in the same implementation slice.

## 2. Primary Product Goal

Tet4D must become a professional game before its surrounding research and
exploration capabilities are allowed to displace the core product.

The first major programme gate is:

```text
PROFESSIONAL_CORE_GAME_READY
```

Passing this gate means that the 4D game is not merely technically functional.
It is understandable, configurable, reliable, visually coherent, responsive,
and ready to support additional professional gaming features.

The core game must:

1. be enjoyable and coherent as a game;
2. present 2D, 3D, and especially 4D state clearly;
3. allow meaningful board configuration rather than only curated demos;
4. distinguish piece rotation, camera movement, slice movement, and
   four-dimensional view-basis changes;
5. provide a modern gameplay baseline, including a Hold mechanic;
6. have reliable controls, menus, persistence, rendering, performance, and
   packaging;
7. be architecturally ready for topology, exploration, challenges, and
   simulation without requiring those later modes for core completeness.

## 3. Product Structure

Tet4D is not one linear tutorial ladder.

The product varies along four substantially independent axes:

| Product axis | Meaning |
| --- | --- |
| Dimension | 2D, 3D, or 4D spatial structure |
| Board geometry | Size of each active coordinate axis |
| Topology | How boundaries and locations are connected |
| Activity | Play, Explore, Challenge, or Simulate |

The final product therefore supports several valid paths.

### Dimensional path

```text
2D bounded play
-> 3D bounded play
-> 4D bounded play
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
contextual guidance
-> free manipulation
-> target-pose challenges
-> placement and clearing puzzles
-> four-dimensional challenge campaign
```

### Simulation path

```text
game or constructed state
-> final board
-> explosion or physics simulation
-> inspect, replay, or continue experimenting
```

Engineering phases may be sequential. The final product must not force every
player through one mandatory conceptual progression.

## 4. Programme Principles

### 4.1 Product work before speculative migration

Implementation priority is driven by player value, product completeness, and
measured performance.

C++ migration is not itself a product milestone.

### 4.2 New capability before repeated proof

Do not create a new stage merely to repeat already established lifecycle,
governance, or parity checks.

Every stage must provide at least one of:

- a new user-facing capability;
- correction of an observed user-facing defect;
- removal of a demonstrated product blocker;
- an explicit subsystem authority change with measurable benefit.

Existing regression suites remain mandatory, but running them is not itself a
product stage.

### 4.3 Four-dimensional comprehension is core gameplay

A mathematically correct state is insufficient when the player cannot
understand it.

The game must explain and keep distinct:

- the current visible coordinate basis;
- the current slice axis;
- the active slice;
- movement through the slice axis;
- piece rotation;
- ordinary 3D camera movement;
- discrete 4D view-basis rotation.

### 4.4 Presets are shortcuts, not restrictions

Presets populate supported setup values. They must not remain the only
available board shapes when the engine already supports a validated range.

### 4.5 Topology is independent of dimension

Topology is not merely an advanced feature after 4D.

Two-dimensional bounded, strip, and Möbius games are legitimate first-class
games. They form an independent conceptual progression.

This does not change the first product priority: complete the professional
bounded 4D game before topology becomes the dominant implementation focus.

### 4.6 Exploration is part of learning

The Explorer is not only a diagnostic or editing tool. It is a free-practice
environment where a player can move, rotate, re-slice, inspect, reset, and
repeat without gravity or score pressure.

### 4.7 Challenges replace the conventional tutorial as the main curriculum

Contextual prompts remain useful, but mastery should be demonstrated through
spatial and gameplay problems:

- reach a target coordinate;
- match a target orientation;
- choose a useful slicing direction;
- place a piece into a cavity;
- clear a line, plane, or hyperplane with a constrained sequence;
- use a topology seam deliberately.

## 5. Current Foundation

The programme begins from an already substantial foundation.

### 5.1 Existing live game

The project has bounded 2D, 3D, and 4D live game paths with deterministic
state transitions, multiple piece sets, fixed and random seeds, speed setup,
restart behaviour, settings, display infrastructure, accessibility, and an
adaptive 4D slice layout.

### 5.2 Current board setup

Godot currently exposes curated board presets. The underlying setup and native
session boundaries already carry explicit board shapes.

The missing product capability is direct, validated editing of every active
axis.

### 5.3 Current 4D presentation

The 4D view presents a visible 3D volume as a stack or matrix of slices along a
selected axis.

The missing fundamental operation is an exact quarter-turn of the 4D
presentation basis that changes which coordinate axis defines the slice stack.

### 5.4 Current guidance

The existing Godot onboarding layer provides useful contextual control
information. It remains a help system, not the final learning model.

### 5.5 Current topology and exploration

The Python topology path already has an accepted Editor, Sandbox, and Play
architecture. Sandbox already represents free piece experimentation and
movement diagnostics.

Godot does not yet provide the complete player-facing equivalent.

### 5.6 Stage 54A

Stage 54A has been implemented and locally committed at `bfeb23dc`.

It establishes:

- Ctrl-only soft drop;
- left-drag camera rotation;
- right-drag camera translation;
- ordinary wheel zoom;
- no Shift-wheel translation;
- shared runtime/helper input authority;
- cockpit ownership for interactive buttons;
- clearer button/helper distinction;
- improved W labels and restrained active-slice framing.

Automated verification passed. Human visual acceptance remains pending because
the implementation environment could not capture a valid viewport.

## 6. Phase I — Professional Core Game

Status: active  
Priority: highest

Phase I exists to pass:

```text
PROFESSIONAL_CORE_GAME_READY
```

Later topology, Explorer, challenge, and simulation work must not replace this
gate.

### Stage 54A — Control and cockpit coherence

Status: implemented locally; automated verification passed; human visual
acceptance pending.

Remaining work:

- publish and integrate the implementation;
- complete visible-GUI acceptance during a later representative play session.

### Stage 54B — Complete custom board configuration

Objective:

Allow the player to configure every active board axis directly within one
validated product envelope.

#### Required fields

2D:

```text
X size
Y size
```

3D:

```text
X size
Y size
Z size
```

4D:

```text
X size
Y size
Z size
W size
```

Each active axis must provide:

- direct integer entry;
- increment and decrement controls;
- explicit minimum and maximum;
- validation feedback;
- canonical default value;
- persistence of the last valid setup;
- compatibility checks with the selected piece set;
- safe rejection of unsupported combinations.

Presets remain available and populate the editable fields:

```text
select preset
-> receive preset dimensions
-> edit any axis
-> start a validated custom game
```

#### Reset semantics

Provide two distinct actions:

- `Reset Sizes`: restore canonical dimensions for the current mode;
- `Reset Setup`: restore all setup fields for the current mode.

Do not resize an active session.

`Restart Game` reconstructs the frozen current setup. `Change Setup` returns to
setup before constructing another session.

#### Authority boundary

One board-extent contract must define product minima, product maxima, setup
validation, persistence validation, native construction limits, and tests.

Godot must not invent a second set of board limits.

Stage 49 and Stage 50 remain accurate records of their completed curated-preset
scope. Stage 54B extends the active product boundary rather than rewriting
those completed records.

### Stage 54C — Game-safe four-dimensional slice-basis rotations

Objective:

Allow the player to change the 3D slicing through which the 4D game board is
displayed while preserving the visible meaning of the gravity axis.

#### Distinct operations

The live 4D game distinguishes:

1. **Piece rotation** — changes the active piece orientation.
2. **Three-dimensional camera movement** — changes the viewpoint inside the
   current visible 3D volume.
3. **Slice navigation** — changes the active index along the current slice
   axis.
4. **Slice-basis rotation** — exchanges the current slice axis with a visible
   non-gravity axis and reconstructs the slice stack.

These operations require separate actions, labels, helper descriptions, and
feedback.

#### Gravity-axis invariant

In live gameplay:

```text
Y = gravity axis
```

Y remains visible and retains a stable downward presentation.

The game must not exchange Y with the current slice axis because that would
conflate presentation transformation with gameplay gravity.

#### Canonical initial basis

```text
Visible axes: X Y Z
Slice axis: W
```

#### Required game-safe quarter-turns

From the canonical basis:

```text
XW +90°
XW -90°
ZW +90°
ZW -90°
```

After a basis change, the general rule is:

> The current slice axis may be exchanged with either visible non-gravity axis.

Both directions must be supported.

#### Coherent update

A basis rotation updates:

- visible-axis basis;
- current slice axis;
- slice membership and order;
- labels and active-slice identity;
- axis/basis indicator;
- grid, cell, piece, and locked-state presentation;
- camera framing;
- helper presentation.

It does not alter:

- board cells;
- active-piece semantic coordinates;
- gravity;
- movement or piece-rotation legality;
- scoring;
- topology;
- deterministic gameplay state.

The transition may be animated between two exact basis states. Animation must
not become semantic interpolation.

#### Focused instruction

Stage 54C includes a small dedicated instructional sequence, without building
the complete future challenge framework.

Minimum exercises:

1. **The object does not change** — rotate the basis and observe that semantic
   coordinates remain fixed.
2. **Choose the useful slicing** — select the slice direction that makes a
   supplied piece easiest to understand.
3. **Find the marked coordinate** — re-slice and navigate until a marked 4D
   cell is visible.
4. **Match the target decomposition** — match a target visible/slice basis.
5. **Inspect before placement** — use re-slicing to verify a difficult
   gameplay placement.

The lesson data should be structured for later migration into the general
challenge runner.

### Stage 54D — Hold-piece gameplay

Objective:

Add the modern Hold mechanic as first-class deterministic gameplay across 2D,
3D, and 4D.

#### Product rule

Each live session has one optional held-piece slot.

A successful Hold action:

- stores the active piece when the slot is empty and activates the next queued
  piece;
- swaps the active and held pieces when the slot is occupied;
- becomes unavailable until the resulting active piece locks;
- respawns the incoming piece at its canonical spawn position and orientation;
- does not preserve the previous active-piece pose;
- does not rewind or reshuffle the queue;
- does not consume the next queue entry during an occupied-slot swap.

Failure to spawn the incoming piece follows the normal game-over policy.

The same rule applies in 2D, 3D, and 4D.

Hold stores piece identity, not:

- board position;
- active slice;
- piece orientation;
- camera orientation;
- view basis;
- presentation layout.

#### Setup and presentation

Ordinary setup may expose:

```text
Hold: On / Off
```

The modern standard game defaults to `On`. The initial implementation supports
one slot only.

Godot provides:

- a semantic `hold_piece` action through the shared input authority;
- a clear `HOLD` preview area;
- empty, available, and unavailable states;
- readable previews for 2D, 3D, and 4D pieces.

#### Deterministic identity

Snapshots, hashes, replay/session identity, and restart behaviour must include:

- held-piece identity or empty state;
- Hold availability;
- Hold enablement where it affects gameplay.

### Stage 54E — Professional visible-GUI playability review

Objective:

Perform a real playability review of integrated 2D, 3D, and 4D gameplay, with
primary emphasis on 4D.

This stage is evidence-driven. It must not begin with a speculative rewrite
list.

Review areas:

- Stage 54A visual acceptance;
- custom board setup usability;
- slice-basis rotation discoverability and comprehension;
- Hold usability and preview clarity;
- active and locked-piece readability;
- axis and depth distinction;
- current-slice-axis comprehension;
- camera recovery;
- menus and button hierarchy;
- pause, restart, change-setup, and game-over usability;
- startup and transition responsiveness;
- representative board-size performance;
- minimum viewport and accessibility composition.

Implement only defects observed during review.

### Stage 54F — Professional gaming-experience and release hardening

Objective:

Close the gap between a verified prototype and a professional game build.

Candidate focused slices include:

- complete keybinding/remapping workflow;
- gamepad support if adopted;
- audio, volume, and mute controls;
- polished pause and game-over presentation;
- scoring and progression presentation;
- settings recovery;
- user-visible performance correction;
- installer, export, and launch reliability;
- release help and documentation;
- final manual acceptance matrix.

These may be separate implementation slices. All remain part of Phase I.

## 7. Professional Core Game Gate

Phase I completes only when all of the following hold.

### Gameplay

- 2D, 3D, and 4D are fully playable.
- 4D is understandable rather than merely operational.
- Movement, piece rotation, soft/hard drop, lock, clearing, scoring, pause,
  restart, Hold, and game over are reliable.
- Custom dimensions work within supported limits.
- Presets remain convenient shortcuts.
- Fixed-seed restart and random-session behaviour remain coherent.

### Four-dimensional presentation

- visible axes and slice axis are explicit;
- slice navigation works;
- exact game-safe basis quarter-turns work;
- basis changes do not mutate gameplay state;
- camera and basis controls are distinct;
- cells, grid, labels, active frames, and Hold previews are readable.

### Product shell

- setup, menus, settings, live play, pause, restart, and return paths are
  coherent;
- controls and helper text share authority;
- interactive and passive UI elements remain visually distinct;
- supported viewports do not clip essential controls;
- accessibility and display settings compose correctly.

### Reliability and performance

- automated verification is green;
- representative manual play has passed;
- invalid settings and failed construction recover safely;
- supported packaging/startup paths work;
- no known high-severity gameplay or data-loss defect remains;
- normal setup, start, and basis transitions are responsive on representative
  hardware;
- supported board maxima remain usable.

### Extension readiness

- subsystem authority is explicit;
- no semantic rule is duplicated in GDScript presentation code;
- board dimensions, view basis, topology profile, challenge state, and
  simulator input have stable integration boundaries;
- later modes can reuse shared semantics rather than fork them.

Passing this gate does not require complete topology, Explorer, challenge, or
physics features.

## 8. Phase II — First-Class Topological Games

Status: planned  
Dependency: professional core game gate, except for isolated architecture work

Topology begins in 2D, where it can be understood without simultaneous
higher-dimensional visual complexity.

### Stage 55A — 2D topology games

Expose three first-class 2D games:

1. `Bounded`
2. `Strip`
3. `Möbius Strip`

#### Bounded

All board boundaries are walls.

#### Strip

One non-gravity axis wraps with orientation preserved.

#### Möbius strip

Crossing the seam applies the accepted reflection/orientation transform.

#### Requirements

- available from ordinary setup;
- concise visual explanation;
- visible seam behaviour;
- exact canonical topology transport;
- deterministic identity;
- no silent fallback to bounded play;
- product labels separated from stable internal IDs;
- inherited topology semantics reused rather than rewritten.

The mapping between current generic presets and these product concepts must be
verified and documented.

### Stage 55B — Higher-dimensional topology play

After 2D topology acceptance:

- expose selected canonical 3D and 4D topology presets;
- preserve exact topology transport;
- provide visible seam and transformation feedback;
- distinguish topology effects from projection, slice movement, and basis
  rotation;
- retain bounded gameplay as the default reference case.

Do not expose every advanced topology-editor possibility as an ordinary game
preset.

## 9. Phase III — Explorer as Spatial Practice

Status: planned  
Dependency: stable view-basis rotations; topology support may be incremental

The Godot Explorer is a player-facing practice environment, not only a
developer diagnostic tool.

It should preserve the accepted conceptual separation of Editor, Sandbox, and
Play. The player-facing Sandbox/practice experience may arrive before the full
editor migration.

### 9.1 Explorer movement

The Explorer permits deliberate movement in both directions along every active
axis:

```text
X ±
Y ±
Z ±
W ±
```

Y is not privileged by gravity unless an explicit experiment enables gravity.

### 9.2 Explorer camera controls

The Explorer exposes both continuous and exact camera controls for the current
visible 3D volume:

- continuous mouse orbit;
- explicit yaw around the visible Y axis;
- explicit pitch around the visible X axis;
- explicit roll around the visible Z axis;
- exact positive and negative 90-degree camera turns;
- reset to canonical camera orientation.

These change camera orientation only. They do not reconstruct the slice stack.

### 9.3 Explorer basis controls

The Explorer may exchange the current slice axis with any visible axis.

From `XYZ | W` this includes:

```text
XW ±90°
YW ±90°
ZW ±90°
```

After a basis change, the same rule applies relative to the current visible and
slice axes.

Unlike the live game, the Explorer permits Y/slice exchange.

### 9.4 Independent state concepts

The Explorer must keep independently observable:

```text
camera orientation
view basis
slice axis
active slice
object position
object orientation
```

Changing one must not silently mutate the others.

### 9.5 Core practice capabilities

- choose a piece or object;
- move freely;
- rotate the object freely;
- rotate the camera freely or by exact quarter-turns;
- rotate the 4D view basis;
- navigate the current slice axis;
- reset position, orientation, camera, and basis independently;
- inspect coordinates and orientation;
- show occupied slices;
- choose a bounded or supported topology;
- cross seams deliberately;
- inspect neighbours and movement effects;
- transition from exploration into play.

### 9.6 Product transitions

```text
Explore This Space
-> Play in This Space
```

```text
Game State
-> Explore Current Board
```

```text
Challenge
-> Practise in Explorer
-> Retry Challenge
```

The Explorer must not become a second implementation of movement, rotation, or
topology semantics.

## 10. Phase IV — Challenge and Learning System

Status: planned  
Dependency: stable gameplay, basis controls, and a reusable Explorer path

The main tutorial becomes a challenge system.

### 10.1 Challenge families

- target-pose challenges;
- piece-rotation challenges;
- camera-orientation challenges;
- view-basis challenges;
- navigation challenges;
- placement challenges;
- line/plane/hyperplane-clearing puzzles;
- topology challenges;
- later scored or constrained puzzle campaigns.

### 10.2 Data-driven challenge definitions

A challenge may define:

- stable ID and title;
- concise instructions;
- dimension and board shape;
- topology profile;
- starting board;
- piece or fixed piece sequence;
- initial piece pose;
- initial camera orientation;
- initial 4D view basis;
- target pose, cells, board pattern, camera, basis, or clear condition;
- allowed actions;
- move/time limits;
- required or forbidden seam crossings;
- Hold policy;
- success/failure conditions;
- hints;
- scoring thresholds;
- unlock relationships.

### 10.3 Initial vertical slice

Begin with a small representative set:

- one 2D placement challenge;
- one 2D strip or Möbius navigation challenge;
- one 3D orientation challenge;
- one 4D W-navigation challenge;
- one 4D view-basis challenge.

The objective is to validate the runner and shared semantics, not to create the
full campaign immediately.

### 10.4 Four-dimensional campaign

A later campaign can progress through:

1. locating cells across slices;
2. W-axis movement;
3. occupied-slice sets;
4. XW basis quarter-turns;
5. ZW basis quarter-turns;
6. Explorer YW basis quarter-turns;
7. inverse and repeated basis turns;
8. camera-versus-basis distinction;
9. 4D piece rotations;
10. target-pose matching;
11. placement across several slices;
12. constrained hyperlayer clearing;
13. topology-aware 4D navigation;
14. advanced packing and transformation puzzles.

This is both a tutorial and an independent puzzle mode.

## 11. Phase V — Unified Game, Explorer, Topology, and Simulation

Status: long-term

The mature product connects its activities without collapsing their ownership.

```text
Play
-> Game Over
-> Replay / Explore Final Board / Simulate
```

```text
Topology Editor
-> Sandbox
-> Play This Topology
```

```text
Challenge
-> Practise in Explorer
-> Retry
```

```text
Constructed State
-> Run Physics Simulation
```

The simulator may consume a game board, Explorer state, challenge state,
topology profile, or constructed scenario through an explicit versioned
conversion boundary.

Gameplay state must not be silently reinterpreted as physics state.

## 12. Cross-Cutting Authority Model

### 12.1 Authority is subsystem-specific

Tet4D no longer treats one language as the universal semantic authority.

Authority is assigned per subsystem according to:

- where the behaviour originated;
- whether the behaviour already exists;
- whether it is deterministic core behaviour or product presentation;
- the implementation intended to own it long term;
- the available contract and verification evidence.

The project distinguishes:

1. inherited Python semantics;
2. transferred inherited semantics;
3. new deterministic core semantics;
4. new Godot product/presentation semantics;
5. declarative content authority.

### 12.2 Python as a bounded reference authority

Python remains reference authority only for existing behaviour that:

- originated in Python;
- remains intended product behaviour;
- has not received a completed authority transfer;
- has not been retired.

This currently includes relevant portions of existing gameplay, piece
transformations, gravity/drop/lock, scoring, topology, replay compatibility,
configuration, and locked-cell explosion behaviour.

This does not mean:

- every new feature must first be implemented in Python;
- every Godot feature requires Python parity;
- Python owns new presentation semantics;
- the future Explorer or challenge campaign must exist in Python;
- new native systems require an artificial Python predecessor.

### 12.3 Existing-behaviour transfer

When another implementation replaces inherited Python behaviour, the existing
authority-transfer protocol applies.

Parity alone does not move authority.

### 12.4 New-behaviour authority establishment

A capability with no Python predecessor receives authority directly when it is
designed.

Authority establishment requires:

- an owning RDS, specification, or versioned contract;
- a named implementation owner;
- explicit semantic and presentation boundaries;
- deterministic conformance tests where applicable;
- persistence and compatibility rules where applicable;
- an authority-map entry;
- no competing duplicate implementation.

New behaviour must not be implemented in Python solely to manufacture an
oracle.

### 12.5 Godot-authoritative behaviour

Godot owns new product and presentation semantics, including:

- menus and setup interaction;
- live HUD and guidance;
- camera orientation;
- 4D presentation basis;
- slice layout and labels;
- animation;
- Explorer interaction;
- challenge screens and hints;
- campaign navigation and progress presentation;
- accessibility and visual feedback.

### 12.6 New native deterministic behaviour

New deterministic semantics should normally be established in native C++ when
they:

- operate on gameplay or geometric state;
- must be shared by Play, Explore, and Challenge;
- affect legality, success, or reproducible results;
- are intended to remain in the professional product core.

Likely examples include:

- Hold state transitions;
- target-pose comparison;
- target-cell occupancy predicates;
- constrained-move accounting;
- deterministic challenge evaluation;
- shared geometric transform utilities;
- later simulation stepping beyond inherited Python behaviour.

No Python parity is required where no Python predecessor exists.

### 12.7 Declarative content authority

Versioned data owns challenge content, campaign structure, and topology/profile
selection data. Runtime implementations validate and execute that content but
do not silently redefine it.

### 12.8 Long-term Python role

Python remains valuable as:

- the historical reference implementation;
- a source of inherited semantic evidence;
- a fixture/trace generator for untransferred behaviour;
- a research and rapid-experiment environment;
- an offline analysis tool;
- an independent verifier for selected high-value deterministic subsystems.

It is not required to remain the production runtime, universal semantic owner,
or complete mirror of future Godot interaction.

## 13. Documentation Integration

This document is the planning authority for the professional Godot game
programme.

### Routing maps

`docs/plans/plan_authority_map.md` and `docs/DOCUMENTATION_MAP.md` must route
programme sequencing and phase gates here.

### Current state and backlog

`CURRENT_STATE.md` should point to the active programme and current stage only.

`docs/BACKLOG.md` should track the active slice, immediate accepted follow-ups,
and explicit deferrals rather than duplicate this roadmap.

### RDS

Durable requirements are added to the relevant RDS when their stage begins.
Near-term reconciliation includes:

- direct per-axis board dimensions;
- complete game-safe slice-basis rotation requirements;
- distinction between camera, piece, slice, and basis actions;
- Hold behaviour;
- challenge-based tutorial direction;
- product-facing 2D topology names.

### Completed architecture records

Completed stage records remain accurate historical evidence of the boundary
accepted at that time. Do not rewrite Stage 49 or Stage 50 to imply that they
delivered unrestricted custom dimensions.

### Topology authority

Do not duplicate topology-playground invariants here. Topology and Explorer
work must route through
`docs/plans/topology_playground_current_authority.md` and its associated spec
and debt register.

## 14. Immediate Execution Order

The intended order is:

1. Publish and integrate Stage 54A.
2. Stage 54B: complete custom per-axis board configuration.
3. Stage 54C: game-safe 4D slice-basis rotations and focused instruction.
4. Stage 54D: Hold-piece gameplay.
5. Stage 54E: visible-GUI professional playability review and
   evidence-driven correction.
6. Stage 54F: remaining professional gaming-experience and release hardening.
7. Pass `PROFESSIONAL_CORE_GAME_READY`.
8. Stage 55A: first-class 2D bounded, strip, and Möbius games.
9. Extend selected topology play to higher dimensions.
10. Build the Godot Explorer as a complete spatial practice environment.
11. Build the general challenge runner and 4D challenge campaign.
12. Connect game, Explorer, challenges, topology, endgame, and simulation.
13. Transfer inherited semantics or establish new native authority only at
    explicit subsystem boundaries.

A later stage must not be pulled forward merely because its infrastructure is
technically mature.

## 15. Current Decision

The next product capability after Stage 54A is:

```text
Stage 54B — Complete Custom Board Configuration
```

The next specifically four-dimensional capability is:

```text
Stage 54C — Game-Safe Four-Dimensional Slice-Basis Rotations
```

The next modern gameplay capability is:

```text
Stage 54D — Hold-Piece Gameplay
```

Progress is measured by whether Tet4D is becoming a clearer, deeper, more
enjoyable, more professional, and more extensible game—not by the number of
migration stages completed.
