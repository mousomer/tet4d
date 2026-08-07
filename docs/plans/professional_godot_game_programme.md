# Professional Godot Game Programme

Role: authority  
Status: active  
Source of truth: this file for product priorities, phase sequencing, and
completion gates  
Supersedes: none  
Last updated: 2026-08-05

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

Status: complete — established by `AE-0054`.

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

Status: complete and verified.

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

Status: complete and verified on the Stage 54C implementation branch.

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

Add one-slot Hold after next-piece and ghost presentation are accepted.

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

### Stage 54E — Visible-GUI professional playability review

Objective:

Conduct a real human playability review of integrated 2D, 3D, and 4D play,
with primary emphasis on 4D.

This is evidence-driven. It does not begin with a speculative rewrite list.

Review:

- visual regressions in the settled Stage 54A scope;
- custom setup usability;
- basis-rotation comprehension;
- next-piece preview clarity;
- 4D next-piece and Hold thumbnail readability;
- ghost usefulness and contrast;
- cross-slice ghost comprehension;
- distinction among ghost, active, and locked cells;
- Hold decision quality with visible queue information;
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

Stage 54E completes only when:

1. representative human-visible review evidence is recorded;
2. findings are classified by severity and gate impact;
3. every defect classified as blocking `PROFESSIONAL_CORE_GAME_READY` is
   corrected and re-reviewed, or remains an explicit blocker preventing the
   gate from passing;
4. non-blocking defects have an owner or deliberate deferral.

Grid strengthening is required only if review evidence classifies current grid
visibility as blocking comprehension or accessibility.

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
- Stage 54E review evidence and any focused correction batches.

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

1. Stage 54B-1 — shared topology-aware board-extent contract, bounded rule.
2. Stage 54B-2 — Godot custom-size setup, validation, and persistence.
3. Stage 54C — game-safe 4D slice-basis rotations and focused instruction.
4. Stage 54D-1 — one-piece next preview and shared thumbnail presentation.
5. Stage 54D-2 — authoritative ghost-piece landing preview.
6. Stage 54D-3 — one-slot Hold with completed authority establishment.
7. Stage 54E — visible-GUI review and blocking-defect correction.
8. Stage 54F — remaining professional release hardening.
9. Stage 55A — first-class 2D bounded, Strip, and Möbius games.
10. Later Explorer, challenge, topology, and simulation phases.

Weak live-grid visibility remains non-blocking visual debt for Stage 54E unless
review evidence classifies it as a professional-core-game blocker.

Compaction or splitting of `docs/history/DONE_SUMMARIES.md` belongs to a
separate documentation-hygiene batch. Historical archive size is not active
product work and must not be mixed into Phase I implementation PRs.
