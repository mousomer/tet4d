# Professional Godot Game Programme

Role: authority  
Status: active  
Source of truth: this file for product priorities, phase sequencing, and
completion gates  
Supersedes: none  
Last updated: 2026-08-03

## 1. Purpose

This document defines the active long-term product programme for Tet4D.

Its first and overriding goal is:

> Deliver a fully playable, professionally presented four-dimensional game in
> Godot, with an architecture ready for professional gaming features and later
> extension into topology, spatial exploration, challenge campaigns, and
> physics simulation.

This document owns:

- programme priority and stage order;
- the boundary between the core game and later extensions;
- phase-completion gates;
- dependencies among board configuration, 4D view controls, Hold, topology,
  Explorer, challenges, and simulation;
- the programme-level authority model for inherited and genuinely new
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

When a programme stage changes durable product behaviour, the owning RDS must
be updated in the same implementation slice.

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
5. provide a modern gameplay baseline, including Hold;
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

Examples:

- reach a coordinate;
- match a target orientation;
- select a useful slicing direction;
- fit a piece into a cavity;
- clear a line, plane, or hyperplane with a constrained sequence;
- use a topology seam deliberately.

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

### Stage 54A status

Stage 54A is complete, human accepted, and merged.

It established:

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

#### Reset and lifecycle semantics

Provide separate actions:

- `Reset Sizes`: restore canonical dimensions for the selected mode;
- `Reset Setup`: restore all setup fields for the selected mode.

An active game is never resized.

- `Restart Game` reconstructs the frozen current setup.
- `Change Setup` leaves the session before another setup is constructed.

#### Authority boundary

One board-extent contract owns product minima, maxima, setup validation,
persistence validation, native construction limits, and tests.

Godot must not invent independent limits.

Stage 49 and Stage 50 remain accurate records of their completed curated-preset
scope. Stage 54B extends the current product boundary rather than rewriting
those records.

### Stage 54C — Game-safe 4D slice-basis rotations

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

### Stage 54D — Hold-piece gameplay

Objective:

Add the modern one-slot Hold mechanic across 2D, 3D, and 4D.

#### Rule

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

#### Setup and presentation

Ordinary setup may expose:

```text
Hold: On / Off
```

The modern standard game defaults to `On`. Initial support is exactly one slot.

Godot provides:

- semantic `hold_piece` input through the shared input contract;
- a clear `HOLD` preview;
- empty, available, and unavailable states;
- readable previews in 2D, 3D, and 4D.

#### Deterministic identity and compatibility

Hold authority establishment must define snapshot, state-hash, replay, trace,
and compatibility behaviour before implementation is accepted.

Snapshots, hashes, replay/session identity, and restart behaviour represent:

- held piece or empty state;
- Hold availability;
- Hold enablement where it affects gameplay.

Existing replay formats created before Hold must remain readable through an
explicit compatibility rule, such as treating Hold as disabled with an empty
slot, or through a deliberate schema-version boundary. The implementation must
not silently reinterpret old replay identity.

The eventual Stage 54D authority-establishment record must identify:

- Hold state owner;
- queue-transition owner;
- snapshot fields;
- replay schema/version behaviour;
- old-replay compatibility;
- state-hash inclusion;
- restart semantics;
- fallback or safe-failure behaviour.

### Stage 54E — Visible-GUI professional playability review

Objective:

Conduct a real human playability review of integrated 2D, 3D, and 4D play,
with primary emphasis on 4D.

This is evidence-driven. It does not begin with a speculative rewrite list.

Review:

- visual regressions in the settled Stage 54A scope;
- custom setup usability;
- basis-rotation comprehension;
- Hold usability and preview clarity;
- active and locked-piece readability;
- axis and depth distinction;
- current-slice-axis comprehension;
- camera recovery;
- menu and button hierarchy;
- pause, restart, setup, and game-over usability;
- responsiveness and representative board-size performance;
- grid contrast and visibility across representative 3D/4D views, display
  settings, and accessibility combinations;
- minimum viewport and accessibility composition.

Implement only defects observed during review.

### Stage 54F — Professional gaming-experience and release hardening

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
- Movement, piece rotation, soft/hard drop, Hold, lock, clear, scoring, pause,
  restart, and game over are reliable.
- Custom dimensions work within supported limits.
- Presets remain convenient.
- deterministic restart and random-session behaviour remain coherent.

### 4D presentation

- visible axes and slice axis are explicit;
- slice navigation works;
- exact game-safe basis quarter-turns work;
- basis changes do not mutate gameplay state;
- camera and basis controls are distinct;
- cells, grid, labels, frames, and Hold previews are readable.

### Product shell

- setup, menus, settings, play, pause, restart, and return paths are coherent;
- controls and helper text share authority;
- interactive controls and passive help are visually distinct;
- essential controls do not clip at supported viewports;
- accessibility and display settings compose correctly.

### Reliability, performance, and release

- automated verification is green;
- representative manual play has passed;
- invalid setup and failed construction recover safely;
- supported package/startup paths work;
- no known high-severity gameplay or data-loss defect remains;
- start, setup, and basis transitions are responsive;
- supported board maxima remain usable.

### Extension readiness

- subsystem authority is explicit;
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

#### Product meanings

- **Bounded:** all boundaries are walls.
- **Strip:** one non-gravity axis wraps with orientation preserved.
- **Möbius Strip:** seam crossing applies the accepted
  reflection/orientation transformation.

Requirements:

- normal setup access;
- concise visual explanation;
- visible seam behaviour;
- exact canonical topology transport;
- deterministic identity;
- no silent fallback to bounded play;
- product labels separate from stable internal IDs;
- inherited topology semantics reused rather than rewritten.

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

### 9.1 Movement

The Explorer permits deliberate movement in both directions along every axis:

```text
X ±
Y ±
Z ±
W ±
```

Y is not privileged by gravity unless an experiment explicitly enables
gravity.

### 9.2 Camera orientation

The Explorer exposes:

- continuous mouse orbit;
- explicit yaw around visible Y;
- explicit pitch around visible X;
- explicit roll around visible Z;
- exact positive and negative 90-degree camera turns;
- reset to canonical camera orientation.

Camera changes do not rebuild the slice stack.

### 9.3 Complete 4D basis control

Unlike live play, the Explorer may exchange the slice axis with any visible
axis.

From `XYZ | W`:

```text
XW ±90°
YW ±90°
ZW ±90°
```

After a basis change, the same rule applies relative to the current basis.
Y/slice exchange is therefore available in Explorer even though it is excluded
from ordinary gravity-driven play.

### 9.4 Independent state

The Explorer keeps independently observable:

- camera orientation;
- 4D view basis;
- slice axis;
- active slice;
- object position;
- object orientation.

Changing one must not silently modify another.

### 9.5 Practice capabilities

- choose a piece or object;
- move freely;
- rotate the object freely;
- rotate the camera continuously or discretely;
- rotate the 4D basis;
- navigate slices;
- reset position, object orientation, camera, and basis independently;
- inspect coordinates, orientation, and occupied slices;
- choose a supported topology;
- cross seams deliberately;
- inspect neighbours and movement effects;
- transition into Play.

Intended transitions:

```text
Explore This Space -> Play in This Space
Game State -> Explore Current Board
Challenge -> Practise in Explorer -> Retry
```

Explorer must not create a second movement, rotation, or topology rule system.

## 10. Phase IV — Challenge and Learning System

Status: planned  
Dependency: stable gameplay, basis controls, and a reusable Explorer path

The primary tutorial becomes a data-driven challenge system.

### Challenge families

- target-pose challenges;
- piece-rotation challenges;
- camera-orientation challenges;
- view-basis challenges;
- navigation challenges;
- placement challenges;
- line/plane/hyperplane-clearing puzzles;
- topology challenges;
- scored and constrained puzzle campaigns.

### Challenge definition

A challenge may define:

- stable ID, title, and instructions;
- dimension and board shape;
- topology profile;
- starting board;
- piece or fixed sequence;
- initial piece pose;
- initial camera orientation;
- initial 4D view basis;
- target pose, cells, board pattern, camera, basis, or clear condition;
- allowed actions;
- move/time limits;
- required or forbidden seam crossings;
- Hold policy;
- success and failure conditions;
- hints;
- scoring thresholds;
- unlock relationships.

### Initial vertical slice

Begin with a small representative set:

- one 2D placement challenge;
- one 2D strip or Möbius navigation challenge;
- one 3D orientation challenge;
- one 4D W-navigation challenge;
- one 4D basis challenge.

The objective is to validate the runner and shared semantics, not immediately
produce the full campaign.

### 4D campaign direction

The later campaign may progress through:

1. finding cells across slices;
2. W movement;
3. occupied-slice sets;
4. XW and ZW game-safe basis turns;
5. Explorer YW basis turns;
6. inverse and repeated basis turns;
7. camera-versus-basis distinction;
8. 4D piece rotations;
9. target-pose matching;
10. placement across several slices;
11. constrained hyperlayer clearing;
12. topology-aware 4D navigation;
13. advanced packing and transformation puzzles.

This campaign is both tutorial and independent puzzle mode.

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

### 12.1 Inherited Python behaviour

Python remains reference authority only for inherited behaviour that:

- originated in Python;
- remains intended product behaviour;
- has not received a completed transfer;
- has not been retired.

Relevant inherited areas currently include portions of gameplay, piece
transformations, gravity/drop/lock, scoring, topology, replay, configuration,
and locked-cell explosion behaviour.

This does not mean:

- every new feature must first exist in Python;
- every Godot feature requires Python parity;
- future Explorer or challenge features must be mirrored in Python;
- new native systems require an artificial Python predecessor.

### 12.2 Inherited transfer

When another implementation replaces inherited behaviour, it uses the
transfer procedure:

- exact subsystem scope;
- identified reference behaviour;
- parity or equivalent conformance evidence;
- documented exclusions and fallback;
- terminal transfer record;
- authority-map update.

Parity alone does not transfer authority.

### 12.3 New authority establishment

A capability without a predecessor receives authority directly through the
establishment procedure:

- normative RDS, specification, or schema;
- named implementation and data owners;
- explicit semantic/presentation boundaries;
- deterministic conformance tests where applicable;
- persistence and compatibility rules;
- establishment record;
- authority-map update;
- no competing truth implementation.

Do not implement new behaviour in Python solely to manufacture an oracle.

### 12.4 Godot authority

Godot owns new product and presentation semantics, including:

- setup interaction and menus;
- HUD and guidance;
- camera orientation;
- 4D presentation basis;
- slice layout, labels, and transition animation;
- Explorer interaction;
- challenge instructions, hints, progress, and campaign navigation;
- accessibility and visual feedback.

Godot may consume deterministic core state but must not duplicate inherited
gameplay or topology rules.

### 12.5 New native deterministic authority

New deterministic behaviour should normally be established in native C++ when
it:

- operates on gameplay or geometric state;
- must be shared by Play, Explorer, and Challenge;
- affects legality, success, or reproducible results;
- belongs in the long-term professional core.

Likely examples:

- Hold transitions;
- target-pose comparison;
- target-cell predicates;
- constrained-move accounting;
- deterministic challenge evaluation;
- shared exact geometric transforms;
- later simulation stepping beyond inherited Python behaviour.

No Python parity is required when no Python predecessor exists.

### 12.6 Declarative authority

Versioned data owns challenge content, campaign structure, and other named
product content. Runtime code validates and executes that content without
silently redefining it.

### 12.7 Long-term Python role

Python remains useful as:

- historical reference implementation;
- source of inherited semantic evidence;
- trace and fixture generator for untransferred behaviour;
- research and rapid-experiment environment;
- offline analysis tool;
- independent verifier for selected high-value subsystems.

It is not required to remain the production runtime, universal semantic owner,
or complete mirror of future Godot interaction.

## 13. Documentation Integration

This document is the active planning authority for the professional Godot game
programme.

Routing requirements:

- `docs/plans/plan_authority_map.md` and `docs/DOCUMENTATION_MAP.md` route
  programme sequence and phase gates here;
- `CURRENT_STATE.md` points to the current programme and immediate stage only;
- `docs/BACKLOG.md` tracks active work, immediate follow-ups, and deferrals
  rather than duplicating this roadmap;
- relevant RDS documents gain durable requirements when a stage begins;
- completed architecture records remain accurate evidence of their original
  scope;
- topology work continues to route through
  `docs/plans/topology_playground_current_authority.md`.

Near-term RDS reconciliation includes:

- direct per-axis board dimensions;
- game-safe slice-basis rotations;
- distinction among piece, camera, slice, and basis actions;
- Hold behaviour;
- challenge-based tutorial direction;
- product-facing 2D topology names.

## 14. Immediate Execution Order

1. Stage 54B — custom per-axis board configuration.
2. Stage 54C — game-safe 4D slice-basis rotations.
3. Stage 54D — Hold-piece gameplay.
4. Stage 54E — visible-GUI review and evidence-driven correction.
5. Stage 54F — release and professional gaming-experience hardening.
6. Pass `PROFESSIONAL_CORE_GAME_READY`.
7. Stage 55A — first-class 2D Bounded, Strip, and Möbius games.
8. Extend selected topology play to 3D and 4D.
9. Build the Godot Explorer as a complete spatial-practice mode.
10. Build the challenge runner and 4D challenge campaign.
11. Connect Play, Explorer, Challenge, topology, endgame, and simulation.
12. Transfer inherited semantics or establish new authority only at explicit
    subsystem boundaries.

A later stage must not be pulled forward merely because its infrastructure is
technically mature.

## 15. Current Decision

Next product capability:

```text
Stage 54B — Complete Custom Board Configuration
```

Next specifically 4D capability:

```text
Stage 54C — Game-Safe Four-Dimensional Slice-Basis Rotations
```

Next modern gameplay capability:

```text
Stage 54D — Hold-Piece Gameplay
```

Progress is measured by whether Tet4D is becoming a clearer, deeper, more
enjoyable, more professional, and more extensible game—not by the number of
migration stages completed.
