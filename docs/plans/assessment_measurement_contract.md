# E3 assessment measurement contract

Role: spec
Status: active
Source of truth: this file for the E3 coordinate-prediction instrument, its scoring and its record boundaries (draft for research review; not study endpoints or approval to collect data)
Supersedes: none
Last updated: 2026-11-19
Parent authority: [Spatial Intuition Research Plan, E3](spatial_intuition_research_plan.md#e3--assessment-instrument-and-study-protocol)

## First instrument slice

Use a fixed coordinate-prediction task in bounded 4D space. Present a marked
cell, a pivot and a signed quarter-turn. The respondent enters the cell's new
coordinates in X, Y, Z, W order. The frame stays fixed during the item. Show
the same axis legend and response controls across conditions. The item does
not require executing Tet4D movement commands.

The draft covers one task family. Adjacency, unfamiliar projection
recognition and view-basis transformation remain in the parent E3 scope.
Results from this slice describe coordinate prediction under the specified
conditions. Broader transfer across task families requires separate evidence.

## Stimulus and scoring

An item is identified by its ID and version. Its frozen stimulus contains
the frame ID, pivot and marked point as ordered four-integer coordinates,
the ordered plane axes and the signed turn. A change to the stimulus or
response semantics requires a new item version. A form version fixes the
ordered list of item versions and its use in the protocol. Scoring has its
own version so an independent analysis can reproduce the original result.

For axes A and B, subtract the pivot to get the input offset. A positive
quarter-turn maps offsets (a, b) to (b, -a). A negative quarter-turn maps them
to (-b, a). Preserve the two other offsets and add the pivot back. This is the
gameplay engine's sign (`rotate_point_nd` and the native core), so a turn
shown in an item means the same as that turn in Explorer practice. Items show
turns with the same glyphs and labels as the Explorer rotation controls. The scorer
compares the submitted four coordinates exactly. A valid answer receives 1
when correct and 0 otherwise. Tag an incorrect answer as unchanged if it
equals the marked point, opposite turn if it equals the inverse result, or
other coordinate error otherwise. Exclude points on the rotation plane's
pivot in both rotated axes because the turn would leave them unchanged.

A submitted response must contain exactly four integers. The proposed UI
keeps malformed drafts editable. If a malformed submission reaches analysis,
flag it as invalid with a null score. An interrupted or unpresented item also
has a null score and retains its status. Each scored form slot contributes at
most one terminal outcome. Training retries are separate practice attempts.

Use frozen, disjoint training, baseline and held-out items. Keep both item IDs
and equivalent stimuli out of training feedback and hints. In operational
forms, vary stimuli and turn direction while matching difficulty using pilot
evidence. The synthetic forms demonstrate separation and scoring. Form
comparability and a stimulus digest representation are review items before
the production storage contract freezes.

## Outcomes and proposed comparison

- **Primary candidate.** Immediate held-out coordinate-prediction accuracy
  per participant, compared between randomized 4D training and an active
  comparison matched on interaction time and feedback. Use baseline accuracy
  and assigned form in the prespecified comparison. Report the estimated
  difference with uncertainty. Treat a zero-valid-answer form as missing.
- **Secondary observations.** Report error categories, valid answers,
  assigned and presented counts, completion, hint use during practice,
  training exposure and response latency. Measure latency from usable
  stimulus to terminal submission on a monotonic clock. Flag interruptions
  separately. Scored forms use no hints or retries.
- **Missingness.** Report valid, invalid, interrupted and unpresented slots
  against the assigned count. Compute descriptive accuracy as correct divided
  by valid submissions. Report missingness and attrition by condition and
  use an assigned-slot sensitivity analysis to show how missing outcomes
  could affect the conclusion. Freeze the main missing-data method before
  inspecting study outcomes.
- **Timing and assignment.** Use pretest, training, immediate posttest with
  held-out items, and delayed retention where feasible. Counterbalance
  comparable forms independently of condition and record form assignment.
  Pilot calibration determines durations, form matching and delay.

The proposed initial pilot population is adults with limited formal exposure
to 4D visualization. Record prior practice under an approved protocol.
Recruitment criteria, active comparison tasks, sample size, form calibration,
missing-data analysis and the primary comparison require review before
protocol freeze. No collection is authorized by this draft.

## Handoff and evidence

E4 derives its minimal data needs from immutable item and form versions,
scoring version, slot status, submitted coordinates, exposure and timing,
condition assignment and the frozen stimulus reference. A future
display-dependent task must also freeze relevant presentation state. The
contract adds no runtime event schema, account identity or gameplay rules.

The `tests/unit/research/fixtures/e3_coordinate_prediction_v2.json`
and `tests/unit/research/test_e3_coordinate_prediction.py`
exercise positive and negative turns, a non-origin pivot, correct and
incorrect answers, invalid input, interruption, an unpresented slot and a
form with no valid submissions. Review acceptance requires independently
reproducing those scores, confirming that training and scored stimuli stay
separate, and resolving the protocol decisions that affect E4's fields.

## Review findings and proposed defaults

The fixtures verify arithmetic, error labels and denominator handling. The
baseline has one item and the posttest has five, so they cannot establish
parallel-form difficulty. The separation test catches shared IDs and identical
serialized stimuli. It does not catch equivalent axis-order and sign encodings,
or problems that differ only by translating the pivot and marked point together.
It also does not cover configured board bounds, response widgets, exposure
control or assignment balance. Treat these as acceptance gaps for operational
forms. Keep the scored fixtures as arithmetic examples.

### 1. Form construction and calibration

- Draft parallel forms A and B, initially 12 items each. Use one positive and
  one negative turn in each of the six axis planes. Match the two forms on
  pivot type, offset magnitude, zero offsets and orientation of the frame.
  Keep practice and retention bank C separate. Give each participant only
  unseen items at each scored visit. Confirm both the stimulus and answer fit
  the configured coordinate bounds.
- Canonicalize axis order and invert the sign when swapping axes. For
  exposure checks, compare the normalized plane, turn and point-minus-pivot
  offset. Reject exact structural matches across banks and audit obvious
  variants before release. For provenance, separately hash the full frozen
  stimulus and presentation version with SHA-256 over a specified canonical
  serialization. A digest identifies content. Exposure checks establish the
  separation rules.
- Before randomized feasibility testing, use a calibration review with
  order-balanced A/B exposure and no answer feedback. Examine accuracy by
  item, axis plane, form and order, completion time, and signs of floor or
  ceiling effects. Use a 10 percentage point adjusted A/B accuracy gap as a
  provisional revision trigger, with uncertainty shown. A small observed gap
  alone cannot establish equivalence. Revise confusing or redundant items,
  version the revised form, and repeat calibration before treating A and B
  as interchangeable.

### 2. Eligibility, comparison and assignment

- Start with adults who can use the designated test build and have had no
  formal 4D rotation training. Record prior 3D/4D practice in coarse bands,
  including prior Tet4D exposure. Apply eligibility rules before allocation.
- Randomize 1:1 after the baseline. Use guided 4D Explorer rotation practice
  for the training arm and guided 3D rotation practice for the active
  comparison. Match allotted time, controls where possible, example count
  and feedback frequency. This estimates the added value of 4D-specific
  practice over 3D rotation practice.
- Assign the A-to-B or B-to-A sequence independently of condition at baseline
  and balance arm allocation within form sequence. Use a concealed schedule
  with variable block sizes. Keep the scoring calculation independent of
  condition and retain both the assigned arm and actual exposure.

### 3. Visits and pilot progression

- Run baseline, practice and immediate posttest in one visit. Start pilot
  scheduling with up to 10 minutes per scored form and 15 minutes of
  practice. Offer retention on form C at day 7 with a two-day window on
  either side. Treat out-of-window results as flagged observations and
  retention as secondary. Tune the timing after usability evidence.
- Budget for about 24 randomized feasibility participants, targeting six
  per arm-by-sequence combination. Review form completion, slot validity,
  adherence, visit duration and retention return with counts and uncertainty.
  Use provisional review triggers of fewer than 80% completing the immediate
  posttest, fewer than 90% valid slots among completers, or any scoring or
  assignment-integrity defect. Report defects and decide whether to revise
  and rerun. These are proposed feasibility targets. Size the later main
  study from a meaningful effect and credible variance and attrition
  estimates. See [CONSORT pilot and feasibility guidance](https://www.bmj.com/content/355/bmj.i5239).

### 4. Primary analysis and incomplete data

- For the main study, estimate the effect of randomized assignment on
  immediate posttest accuracy in percentage points. Use baseline accuracy
  and assigned sequence as prespecified covariates and report a 95%
  confidence interval. Retain participants in their assigned arm regardless
  of training adherence. Treat coordinate prediction on novel items as
  within-family transfer.
- Use correct divided by valid submissions where at least 9 of 12 slots
  have valid responses. Keep lower-coverage forms missing for the endpoint
  and report their descriptive results and slot counts. Plan a
  missing-at-random analysis with multiple imputation of missing
  participant-level outcomes using arm, baseline and sequence, subject to
  analysis review and adequate main-study sample size. Report the observed
  outcome analysis and assigned-slot bounds that count unresolved slots as
  all incorrect or all correct. Report attrition and missing status by arm
  and visit. Keep the pilot analysis descriptive.

### 5. E4 handoff and freeze points

The owner approved these defaults and logical record boundaries. Calibration
thresholds remain provisional. The [E4 contract](e4_assessment_storage_contract.md)
uses those boundaries without encoding thresholds in storage.

Approve the logical record boundaries before E4 schema work. Preserve the
protocol version, pseudonymous study enrollment, assigned arm and form
sequence, visit and assigned slot IDs, versioned item/form/scorer and
presentation references, normalized exposure-check identity, approved
response representation, slot status, monotonic latency, and coarse
actual training exposure. Store form and slot assignment independently of
attempts so skipped visits and unpresented items can be reconstructed.
Distinguish expired or interrupted visits from missing imports. Keep
malformed payloads out of the research export and retain the invalid status.
The form/item registry can own immutable fingerprints and manifests.
Keep raw keystrokes, repeated render events and contact details outside
these measurement records.

Before schema freeze, review which assignment, exposure, version and
missingness facts must be independently reconstructible. Freeze exact form
content, visit windows, progression thresholds, confirmatory analysis and
power assumptions after calibration and before the main study. Real-person
pilot collection remains subject to the programme gates and applicable
review and authorization.
