# Tet4d Manifest — Spherical Play False-Lock Fix

Archived note: the broader Play drop-policy fix has already been generalized
beyond this original spherical repro. Current topology-playground architecture
authority lives in `docs/plans/topology_playground_current_authority.md`. Newer
task instructions and the current-authority manifest take precedence over this
archive.

## Manifest ID
`tet4d-topology-play-spherical-false-lock-fix`

## Purpose
Historical task framing for the original spherical repro that exposed a broader Play-mode drop/lock defect on non-trivial `Y` seams.

This manifest exists because the earlier Stage 1 pass added useful structure and partial regression coverage, but did **not** capture the broader runtime contract. The later follow-up fix kept the useful Stage 1 scaffolding while generalizing the fix from the spherical repro to explicit Play drop legality across non-trivial `Y`-seam topology families.

---

## Historical status at task creation

### Confirmed
- Stage 1 workspace scaffolding around `editor / sandbox / play` is valid and should remain in place.
- Stage 1 added bottom-boundary continuation tests on traced live paths.
- Those tests were partial coverage, not the full Play drop/lock contract.

### Therefore
- The existing automated tests from that pass were incomplete.
- The current branch must not claim that Stage 1 fully fixed Play drop/lock semantics.
- The spherical repro should be treated as the motivating case for a broader non-trivial `Y`-seam runtime fix, not as a one-topology-only patch target.

---

## Original problem statement

At the time of this archived task, in topology playground **Play** mode on
**spherical topology**, the piece could still lock incorrectly in a live
user-visible session.

At the time of this archived task, this was not yet considered solved.

The task originally required answering:
1. what exact movement/topology sequence reproduces the bug,
2. what runtime path actually decides grounded/support/lock there,
3. whether stale or non-canonical state is being used after transport,
4. what minimal runtime fix makes the real spherical case correct.

---

## Scope

### In scope
- exact spherical bug reproduction
- failing regression from that repro
- live-path trace of support / grounded / lock decision
- minimal runtime fix
- correction of any overclaiming status/docs from Stage 1
- preservation of Stage 1 workspace work

### Out of scope
- Stage 2 Editor movement unification
- large menu cleanup
- broad topology redesign
- replacing Play topology semantics with a new gameplay rule
- fall-axis seam suppression as a production fix

---

## Hard constraints

### 1. Do not mask the bug with a rules change
Do **not** fix this by changing Play to remove Y seams or suppress fall-axis seam traversal globally.

That idea is a possible future gameplay rule, but it is **not** the bug fix for this task.

### 2. Preserve topology semantics during diagnosis
Assume current Play is intended to preserve the chosen topology unless and until an explicit design decision says otherwise.

### 3. Preserve Stage 1 structure
Do not revert:
- `editor / sandbox / play` internal workspace model
- explicit Sandbox neighbor-search state
- workspace-keyed helper scaffolding

### 4. Use the real runtime path
Do not rely only on helper-level geometry tests.
The failing regression must exercise the real Play/runtime path as directly as practical.

---

## Likely failure classes to investigate

1. **Wrong seam family covered by prior tests**
   - Stage 1 may have covered only a bottom-boundary continuation case that is not the actual spherical failure.

2. **Topology-specific transport branch**
   - spherical topology may route through transport/support logic not hit by existing regressions.

3. **Stale grounded/contact cache**
   - a pre-transport contact state may survive into the next step and cause false locking.

4. **Split movement vs lock coordinates**
   - movement acceptance may use canonical transported state while support/lock uses stale, raw, or topology-mismatched state.

5. **Live shell/runtime path divergence**
   - the shell path may still feed stale state into lock evaluation in a way helper tests do not reproduce.

---

## Required implementation sequence

### Step 1 — Correct status language
Update any code comments/docs/status that overclaim the Stage 1 bug status.

Required wording principle:
- traced continuation cases were covered,
- the actual spherical false-lock case remained open,
- this batch addresses that exact live bug.

### Step 2 — Reproduce the exact spherical bug
Identify the exact spherical topology configuration and movement sequence that reproduces the false lock in Play.

Requirements:
- use spherical topology specifically,
- use the live play/runtime path as directly as practical,
- prefer an end-to-end or close-to-end-to-end regression.

### Step 3 — Add the failing regression first
Before changing runtime logic, add a focused automated test derived from the exact or near-exact spherical repro.

This test must fail on the current buggy state.

### Step 4 — Trace the actual lock/support path
Trace the failing case far enough to answer:
- what the canonical post-transport state is,
- what state grounded/support reads,
- what state lock reads,
- exactly where they diverge.

### Step 5 — Apply the minimal runtime fix
Fix only what is needed to make the spherical failing regression pass.

Possible valid fixes include:
- invalidating stale grounded/contact cache after transport,
- recomputing support from canonical post-transport state,
- removing a topology-specific fallback bypass,
- aligning lock decision input with movement-acceptance state.

### Step 6 — Expand adjacent coverage only if justified
After the exact spherical bug is fixed, add small additional tests only if they follow directly from the diagnosed cause.

---

## Acceptance criteria

The task is complete only if all of the following are true:

1. the spherical false-lock bug is reproduced by an automated regression,
2. that regression fails before the fix,
3. that regression passes after the fix,
4. previously added Stage 1 play-path regressions still pass,
5. docs/status no longer overclaim the Stage 1 bug state,
6. the final report names the exact technical cause of the bug,
7. no topology rules change was used to hide the bug.

---

## Non-goals

Do not:
- start Editor movement unification here,
- redesign Play topology semantics here,
- implement fall-axis seam suppression as part of this fix,
- do broad menu/panel cleanup,
- perform large speculative refactors.

---

## Deferred design note — fall-axis seam suppression

This remains a **candidate future Play ruleset**, not part of the current fix.

Possible future design:
- keep full topology for lateral motion and rotation,
- forbid fall-axis seam traversal only for gravity / soft drop / hard drop.

This is a valid gameplay idea but must be evaluated **after** the real spherical false-lock bug is fixed under current intended topology semantics.

It must not be used as the present bug fix.

---

## Suggested files/areas to inspect first

- `src/tet4d/engine/gameplay/game_nd.py`
- `src/tet4d/engine/runtime/topology_playground_state.py`
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- `tests/unit/engine/test_topology_playground_launch.py`

Also inspect any helpers or branches specific to:
- spherical topology transport
- grounded/contact cache
- lock-delay / immediate-lock
- topology-specific support evaluation

---

## Required final report format

### Summary
One paragraph describing the actual cause and fix.

### Root cause
State exactly where the wrong lock/support decision came from.

### Files changed
List each modified/added file with one sentence per file.

### Tests
List:
- the new failing-then-passing spherical regression,
- all updated tests,
- commands run,
- pass/fail status.

### Deferred items
List only items intentionally left for later.

### Risks
List remaining seam/topology families still not covered, if any.
