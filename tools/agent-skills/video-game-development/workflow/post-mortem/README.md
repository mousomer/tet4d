# The post mortem

At the end of a project (after release readiness, before any tribute or launch page: its conclusions go into the
page), Claude looks back over the whole project with the owner: what worked, what didn't, what it cost, and what
changes next time. The point is the rule changes. A conclusion that changes nothing in the skill, the working rules
or a project's CLAUDE.md is a story, not a lesson.

## 1. Gather the record (no memory, only sources)

Read what the project left behind. Never reconstruct it from recollection:

| Source | What it tells |
|---|---|
| The discrepancy register | every departure from the original, who decided it, and which ones were reversed later |
| The board's db (`items`) | every artifact, its type and topic, how many rounds it went through (versions), what is still not Done |
| Every QA sheet's `results` | Fails and Skips with the owner's comments: what broke, what was tested wrongly, what no longer applied |
| Every worksheet's answers | the decisions, the comments, the options the owner rejected and why |
| The editors' dbs | what the owner had to tune by hand (each item there is something the first build got wrong) |
| The project's CLAUDE.md, PLAN.md and git log | the timeline: slices, dates, rewrites, reverts |
| The owner's own words | quotes from sheets and notes, the corrections ("don't do stuff like that"), the praise |

Write the numbers down with their source: rounds per slice, tests per sheet and the share that failed, days per
slice, the times work stalled (and why), the slices reopened after sign-off.

## 2. Write the findings

In the project, `POST_MORTEM.md`, in this order:

1. **The project in a paragraph**: what was made, from what, how long it took, how many slices and sheets.
2. **What worked**: each with its evidence (a number, a sheet, a quote) and why it worked.
3. **What didn't**: each with its evidence, its cost (rounds, days, tokens, the owner's patience) and its cause.
   Name the cause precisely ("four tabs as one phase: 26 questions a round"), never "communication".
4. **The surprises**: what the original, the platform or the tools did that nobody expected.
5. **Proposed changes**: one per finding that should change how work is done, each written as the rule itself
   (the wording that would go into the skill or the working rules) and where it goes.

Quote the owner's real words where they exist (the working rules: text in the owner's name is written as them).

## 3. The owner decides

The proposed changes are decisions: put them on a worksheet (`worksheet/`), one question per change, with
Keep / Change / Drop and a comment box, the evidence on the card. More than eight changes: split by topic. Nothing
becomes a rule until the owner keeps it. Add the worksheet and `POST_MORTEM.md` to the board.

## 4. Apply

1. Write each kept change where it belongs: this skill (SKILL.md or a workflow guide), the workspace CLAUDE.md, the
   project's CLAUDE.md, or a memory. Date it and quote the owner, like every rule here.
2. Copy the skill into every repository that carries it (`.claude/skills/`), commit and push each.
3. Mark in `POST_MORTEM.md` what became of each proposal (kept and where, changed, dropped), and close the slice
   card on the board.

## Smaller ones

A slice that went badly (reopened twice, a stall, a sheet the owner gave up on) gets a short post mortem of its own
right away, the same four steps in a few lines, so the lesson reaches the next slice instead of waiting for the end.
