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

### E1 — Bounded practice Explorer

One Godot practice workspace with:

- independent object pose, camera pose, exact 4D view/slice basis and slice
  selection;
- X/Y/Z/W translation, relevant 4D object-rotation planes, and no automatic
  gravity during ordinary free practice;
- clear active orientation, neighboring cells, coordinates, visible slice
  identity and feedback explaining what each action changed;
- reset, deterministic restart or retry, and safe transitions into bounded
  normal Play;
- reference/conformance checks at the Python/native/Godot boundaries and
  regression tests for both 3D and 4D camera-relative motion.

Do not build a second topology transport engine or a full topology editor.
Non-bounded topology is supported at the model/contract boundary but not
selectable in the initial Godot experiment UX. The established Python modes
are not removed or globally disabled.

Gate `EXPLORER_LEARNING_READY`: real novice sessions demonstrate task
discovery, deliberate rotation, recovery from disorientation, and the ability
to identify whether the object, camera, slice or basis changed. Test
projection-versus-adjacency misunderstandings explicitly.

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
