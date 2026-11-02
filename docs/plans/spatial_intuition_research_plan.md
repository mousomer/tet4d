# Spatial Intuition Research Plan

Role: spec
Status: active
Source of truth: this file for proposed spatial-learning study design and participant data requirements; programme priority and gates remain with `docs/plans/professional_godot_game_programme.md`
Supersedes: none
Last updated: 2026-11-01
Programme authority: `docs/plans/professional_godot_game_programme.md`
Active execution/debt: `docs/BACKLOG.md`

## 1. Objective and hypothesis

Develop a bounded, comprehensible Godot 4D practice environment and test
whether repeated interaction produces **transferable four-dimensional spatial
competence**, rather than only better use of Tet4D's controls or memorisation
of practiced puzzles.

A favourable result would be improvement on previously unseen, independently
scored 4D tasks relative to an appropriate comparison, with an interpretable
retention result. The project cannot claim that a participant has acquired
general 4D intuition solely from game score, completion time or self-report.
A negative or inconclusive result is an acceptable scientific outcome.

This plan is subordinate to the existing product, topology, packaging and
architecture owners. It does not authorise new accounts, server operations,
participant collection, RDS changes, topology activation, or code migration.

## 2. Repository baseline and scope

Already available or accepted:

- Professional bounded Godot 2D/3D/4D core; Stage 54G recorded
  `PROFESSIONAL_CORE_GAME_READY: YES`.
- Native deterministic gameplay, replay and presentation-authority separation.
- Python Explorer / Topology Playground with Editor, Sandbox and Play concepts,
  general topology semantics and an existing standalone explosion simulator.
- Godot Presentation Designer, comparative Design Laboratory, responsive
  cockpit and the accepted Stage 58B board-area/scale allocation.
- Current Stage 56H, Stage 58C/59 and cockpit follow-up issues in the backlog.

Not established by those features:

- A complete, beginner-accepted **Godot** free-practice Explorer.
- A validated measure of 4D spatial transfer and an approved study protocol.
- Participant identity/authentication, hosted progress storage and a reliable
  consent-aware research event pipeline.
- Research-grade evidence of acquired 4D competence.

Governance-agent telemetry (`tools/workspace_governance/telemetry.py`), local
Design Laboratory ratings and existing gameplay analytics have other owners
and do not become a participant-event backend by renaming them.

## 3. Priority slices and acceptance

### E1 — Bounded practice Explorer: immediate execution contract

**Owner priority decision: 2026-11-02.** Begin this work without waiting for
the outstanding Stage 59, Designer/replay toolbar or cosmetic cockpit issues.
Only an issue that demonstrably blocks an Explorer operation becomes an
Explorer blocker. The first slice is not a redesign of the Play cockpit.

**Goal:** one playable, gravity-free 4D learning workspace in Godot, with no
score, queue advance, lock, gravity timer, game-over or forced placement.
The exercise is to manipulate and understand a piece, not to win a game.

#### Stage E1-A — Semantic and adapter vertical slice

Existing reusable repository surfaces (verify actual method contracts before
implementation):

- `godot/Tet4D.Godot/scripts/native/tet4d_core_bridge.gd` delegates to
  native `geometry_translate_blocks`, `geometry_rotate_blocks`,
  `query_piece_pose_legal` and bounded/topology step queries. These are
  candidates for exact transforms/legality; do not port their algorithms
  to GDScript.
- Python `src/tet4d/engine/runtime/topology_playground_sandbox.py` owns
  reference Sandbox selection, translation, shape rotation and movement policy.
  `explorer_runtime_nd.py` and topology contracts own inherited transport
  behavior. For this phase, the profile is bounded only.
- `SliceBasis4D`, `ControlFrameMapping`, `SliceLocalOrientation`,
  `TraceCoordinateMapper`, the shared renderer and `CameraRig` already
  establish distinct presentation/input owners in Live 4D. Reuse or adapt
  their read-only consumption paths; do not invent a parallel 4D mapper.
- `LiveInputContract` owns action descriptions, effective bindings and
  rotation-plane inventory. Explorer may have a different no-pressure
  *interaction layout*, but must reference these action descriptors rather
  than hardcoding a second conflicting binding table.

Implement a small dedicated Explorer state/adapter owner, not an Explorer
branch inside the native live-game session's gravity loop. The adapter owns
the current practice-piece pose, immutable initial scenario and practice
reset; the native geometry/legality boundary evaluates every translation and
rotation. No inherited piece-transform, collision, adjacency or topology
rule is implemented independently in GDScript. If the existing pure API
cannot support a required atomic transition, introduce a bounded native
practice-query/session API with separate conformance evidence rather than
silently appropriating the live gameplay session.

**First acceptance fixture:** fixed bounded 4D board and one known nontrivial
4D polycube. Exact shape and extents come from an explicit fixture/test
contract, not an arbitrary hidden random game seed. All axes X/Y/Z/W permit
positive and negative deliberate moves. All six plane families XY/XZ/YZ/
XW/YW/ZW permit both quarter-turn directions. Out-of-bounds or overlapping
moves are rejected without changing the practice pose. There is no gravity
or lock on any number of frames.

#### Stage E1-B — First visible Godot practice workspace

- Provide a clearly named `Explore 4D` entry in the existing LEARN
  navigation and a dedicated Explorer/practice mode. Preserve existing
  Play 2D/3D/4D entry and the Python Topology Playground.
- Render the practice piece with the existing 4D slice projection and board
  visual grammar. Show the active canonical coordinate, object orientation,
  current signed view basis, slice axis/index and camera orientation as
  distinct, readable concepts.
- Keep piece rotation, camera orbit/pan/zoom, exact view-basis quarter turns,
  local slice yaw/pitch and slice navigation independent. A camera or basis
  change must not alter native piece coordinates or its geometry hash.
- Show the *effective* keys alongside their actions at the point of use.
  Never require memorising undocumented keys. Explain rejected moves and
  allow `Reset Piece`, `Reset View`, `Reset All` and repeat of the initial
  fixture. Give a direct path to bounded ordinary Play that creates a new
  validated game session; no implicit conversion of practice pose to game
  state.
- Make the workspace usable at 1280×720 and 1440×900 logical viewport sizes,
  with fit-before-scroll controls and legible piece cells. Do not change
  accepted Live board allocation or Designer geometry to accomplish this.

**E1-B gate:** a user can reach Explore 4D, move in W and Y as freely as X/Z,
rotate in an XW/YW/ZW plane, rotate the view without moving the object,
recover their orientation and return to Play without disturbing gameplay
identity. Required tests assert the observable result, not merely a method
call or scene load.

#### Stage E1-C — Adjacency and 3D comparison

- Provide an explicit `Neighbors`/adjacency overlay. Select a cell and
  distinguish its face-adjacent canonical neighbors from other nearby or
  overlapping projected boxes. The overlay must disclose which canonical
  coordinate differs and by one step on which axis; W neighbors must be
  traceable across slices.
- Use canonical bounded neighbor-query truth, not projected pixel distance,
  ray overlap or a new GDScript graph rule. Neighbor markers are subordinate
  to actual full-cell piece geometry and may be switched off.
- Add a 3D practice configuration for comparison; keep analogous object
  motion, camera-relative input, labeling, reset and adjacency behavior.
  Neither mode silently adopts normal Play gravity or lock policy.

#### Verification and acceptance

1. **Geometry:** every supported rotation followed by its inverse returns
   exactly to the prior pose; four same-direction quarter turns return to the
   initial pose; translation and inverse agree except at a blocked boundary.
2. **Semantic safety:** invalid moves are atomic failures; empty/bounded
   topology behaves as specified by the reference fixtures; no Python
   semantic authority is transferred by adding a Godot UI.
3. **Presentation:** view/camera/slice transforms preserve practice piece
   canonical identity; 3D/4D camera-relative movement matches the established
   `test` family added by PR #158. Explorer navigation must not advance or
   mutate an existing live game session.
4. **Interaction:** test all six 4D rotation planes, negative/positive W and Y,
   reset and rejected-move feedback, changing view basis then moving, and
   neighbor behavior under a reversed signed slice axis.
5. **Human evidence:** real Godot captures and hands-on novice tasks at
   1280×720 and 1440×900, checking discoverability, label comprehension,
   disorientation recovery and whether apparent proximity is mistaken for
   topological adjacency.
6. **Governance:** one semantic objective per PR (E1-A, E1-B, E1-C).
   Select `product_planning`, `godot_product_shell`, `topology_and_explorer`
   and `native_deterministic_core` only where the actual diff invokes them.
   Apply the cross-layer scope matrix and parity/conformance requirements
   when native and Godot change together; run the canonical full gate for
   authority or broad shared changes.

`EXPLORER_LEARNING_READY` is passed only after E1-A/B/C and representative
human acceptance. E1-B is the first *visible* delivery and must not wait for
the completed learning system, user accounts, research event schema or a
comprehensive UI redesign. Non-bounded topology remains available in Python
and supported by the model/architecture contract but is hidden or disabled
in the initial Godot study UX. No full editor, custom gluing, seams, campaigns,
new input devices, physics simulator or server backend in E1.

### E2 — Professional UI and comprehension review

Review the production Godot game and Explorer together. Include:

- contrast and information hierarchy: piece / settled / ghost / grid / helper;
- depth cues, occlusion, near-axis appearance, 4D active/inactive slices,
  W-label anchoring, and projected-neighbor cues;
- control discoverability and readable dynamic bindings while playing;
- distinction between object rotation, camera motion, 4D basis rotation and
  slice movement;
- cockpit density, menus, responsive text scaling and fit-before-scroll.

Use Stage 58C evidence and existing Design Laboratory A/B comparisons. Preserve
accepted locked shell allocations and Stage 58B geometry unless a separate
product decision explicitly reopens them. Professional review plus observed
novice performance are both needed; aesthetic preference alone is not a
comprehension test. The study interface should be version-frozen once pilot
tasks are calibrated.

### E3 — Assessment instrument and study protocol

Before designing the production event schema, define:

1. **Population and recruitment:** eligibility, experience with 3D/4D
   visualisations, exclusions and relevant prior practice.
2. **Conditions:** randomized training vs a justified active control or
   comparison when feasible, with counterbalancing for test-order effects.
3. **Timeline:** pretest, training/practice, immediate posttest, held-out
   transfer and a delayed retention assessment when feasible. Specify
   durations after pilot calibration, not as unsupported defaults.
4. **Items:** reproducible, graded examples of coordinate/neighbor inference,
   object-orientation prediction, view-basis transformation and recognition of
   the same structure under unfamiliar projection. Include unfamiliar objects
   and never reuse scored transfer items as training hints.
5. **Endpoints:** prespecified accuracy and error-type outcomes, with
   latency, hint use, exposure and task completion as secondary measures.
6. **Analysis:** handle baseline differences, missing events, repeated
   measures, attrition, uncertainty and prior experience. Predefine primary
   comparisons before inspecting outcomes.

The minimum assessment/challenge runner belongs here. A full tutorial or
campaign is not required for the first experiment and follows afterwards.

### E4 — Participant records, local recovery and server ingestion

Derive the storage contract from E3 rather than guessing what future analysis
might need.

Separate domains:

| Domain | Proposed responsibility |
| --- | --- |
| Gameplay authority | Native gameplay state, deterministic transitions and replay identity remain unchanged |
| Presentation | Godot controls, displayed views and local research-task UX |
| Study definition | Versioned protocol, cohort/condition, task IDs, scoring rules and frozen item seeds |
| Participant identity | Pseudonymous participant ID, consent version and optional account authentication |
| Client session | Persist pending events locally, including network outage/restart recovery |
| Server ingestion | Validate/authenticate, deduplicate, acknowledge and retain event order, with auditable schema versions |
| Analysis export | Reconstruct task/attempt history and produce minimised datasets with documented provenance |

Candidate event categories: session start/end; task assignment and stimulus;
input/action; object/camera/basis/slice state transition; hint/error;
completion/answer; network recovery; and consent-related state. Every record
should identify build, study/task schema, source session, monotonic event
sequence and deterministic scenario seed where applicable. Avoid collecting
continuous raw input or personally identifying detail unless the protocol
demonstrates that it is necessary.

Define explicitly before implementation:

- stable pseudonymous IDs separate from login/email identifiers;
- purpose-limited data collection, participant-facing consent, privacy notice,
  access controls, retention, withdrawal, deletion and export;
- age/guardian consent and applicable ethics/privacy review if minors are
  recruited; do not assume an ordinary account login supplies research consent;
- offline-first buffering, acknowledged idempotent writes, duplicate prevention,
  version migration and failure/recovery tests;
- replay/sample reconstruction from stored scenarios and transitions without
  conflating participant events with canonical gameplay hash/state;
- event-volume and performance budgets so logging does not change input
  timing or experimental conditions.

No hosting vendor, authentication provider, database or cloud architecture is
selected by this planning change. Select them in a separate design decision
based on the approved schema, operations and compliance requirements.

Gate `RESEARCH_PLATFORM_READY`: scenario and scoring contracts are frozen,
consent/withdrawal and storage recovery have evidence, auth separation and
server access rules are reviewed, event loss/duplication are tested, and a
dataset can be exported and independently reconstructed.

### E5 — Pilot and first human experiment

Start with a bounded pilot to verify onboarding, task difficulty,
comprehension, recording completeness and reproducibility. Fix issues before
freezing the protocol for the main study. Then run the controlled comparison,
report primary and secondary endpoints, uncertainty, confounds, limitations,
data exclusions and negative findings.

Gate `FIRST_EXPERIMENT_COMPLETE`: controlled data and a documented analysis
exist. There is no success requirement on the hypothesis itself.

## 4. Parallelism and stopping rules

- Experimental design E3 can begin during Explorer E1 and visual review E2;
  **final assessment version** waits for a sufficiently stable user interface.
- Storage contracts E4 follow E3's measurement requirements; backend scaffolding
  can run in parallel only after that interface is specified.
- No study recruits participants before consent, privacy, data-integrity and
  task-scoring requirements have been reviewed.
- No major topology, campaign, simulation or platform expansion blocks the
  first experiment. A reproducible Windows/Linux research build may move up
  if recruitment genuinely needs it; this alone changes no support matrix.
- A falsified or unsupported intuition hypothesis redirects the learning
  curriculum and measurement approach, not the correctness of the bounded game.

## 5. Future programme preserved

After the initial study: expand data-driven learning challenges and optional
curricula; release first-class bounded/Strip/Möbius games and selected 3D/4D
topologies; complete the Godot Editor/Sandbox/Play topology laboratory; connect
game and constructed states to the existing explosion simulator and later
physics; then add advanced game features, consumer platforms and possible
commercial distribution. The canonical platform priority remains
Windows, Linux, Android tablets, with public macOS and iPadOS deferred.

Each implementation slice must use the repository's routing, authority,
verification, backlog and PR process. Human study results and genuine
user-facing feature behavior must not be asserted by documentation alone.
