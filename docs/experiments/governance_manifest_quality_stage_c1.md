# Governance-manifest quality: Stage C1 measurement protocol

Status: non-authoritative experiment protocol; baseline-gated implementation

This protocol defines the observational instrumentation for Stage C1. It does
not alter governance ownership, routing, scenarios, thresholds, resolver
semantics, or the active governance surface. Experiment code may inspect those
authorities but is not an authority itself.

## Objective and boundary

Stage C1 measures governance materialization in real agent trajectories and
keeps retrieval, mutation, execution, and independent engineering-outcome
evidence separate. It does not infer an optimal manifest size, invent a
governability score, perturb the treatment, or continue into Stage C2.

Tracked content is limited to the implementation, schemas, small synthetic
fixtures, tests, and this protocol. Raw trajectories and generated run outputs
remain outside Git.

## Frozen baseline gate

`tools/experiments/governance_manifest_quality/frozen_baseline.json` records the
declared PR118 treatment identity. The fingerprint and corpus commands measure
the checkout from source and remain strict reproduction commands: they fail
unless every declared identity matches. They never rewrite governance.

The declaration separates three identity domains: the PR118 repository commit,
the workspace-governance package identity under
`sha256-path-and-content-v1`, and the raw bytes of
`config/project/policy_pack.json`. The workspace package digest is
`6a3ca683...`; the machine-policy raw SHA-256 is `44c126b6...` and its exact
length is 74,150 bytes. Regression tests reject either digest in the other
domain. Strict C1 reproduction requires every frozen treatment path in the
checkout to remain byte-identical to PR118. That is not a permanent constraint
on later master checkouts: repository regression verification reads the named
Git snapshot directly and verifies the recorded PR118 treatment there. The
canonical Python CI checkout therefore retains full history so it can verify the
declared commit and ancestry instead of treating a shallow checkout as evidence
that the baseline is absent.

The edge-state correction moved this checkout past that treatment: declaring
file classes and edge-state profiles changed the machine policy, so the
fingerprint and corpus commands now fail closed here and strict reproduction
runs from the PR118 snapshot. The frozen declaration is not restated to match
current policy. Measurement still runs under the historical rules: a policy
that predates the declarations classifies every path as `unclassified` rather
than failing, so the recorded corpus stays reproducible on its own terms.

The generated fingerprint includes repository commit, pack revision and lock
digest, raw policy SHA-256, serialized policy bytes, structural policy metrics,
human-governance LOC, active governance files, and resolver/scenario schema
identity. Paths in the fingerprint are repository-relative.

`fingerprint_source` names what was measured. A `current_checkout` record
carries the surface validator's verdict in `governance_surface_issues`. A
`historical_git_snapshot` record sets that field to `null`: the contemporary
validator is deliberately not replayed against an old treatment, because
current validation semantics need not stay meaningful for it, and an empty list
would claim a clean result that was never measured. Both sources share one
implementation of every structural measurement, so their metrics are comparable.

## Normalized records

Each trajectory record has four independent evidence groups:

1. `retrieval_events`: repository-relative path, governance classification and
   policy-declared file class, active-surface registration, and edge operational
   role/limit rationale where applicable,
   access mode (`bounded`, `whole_file`, or `unknown`), materialized bytes,
   optional half-open byte range, content identity, and observable
   route/authority identity.
2. `mutation_events`: path, governance classification, operation, line/byte
   delta when recorded, intent when recorded, and generated-file status.
3. `execution_events`: tool, command category, search/test flags, exit status,
   duration, and failure/repetition evidence actually present in the source.
4. `outcome_evidence`: nullable external observations only. Measurement code
   stores but does not judge tests, gates, regressions, scope/authority findings,
   unnecessary changes, technical debt, acceptance, or review findings.

Unavailable evidence is represented as `null` plus a completeness reason. No
adapter estimates token counts, elapsed time, byte ranges, revisions, or
outcomes that the source did not record.

Metric additions stay backward compatible: `edge_state_file_activity` was added
to the version 1 metric contract, is empty for a trajectory with no edge-state
read, and changes no earlier metric, so the historical result remains
comparable. Version 2 drops the source `task_identity`, which hashed the first
user-role message and, in Codex Desktop rollouts, that message is injected
context rather than a request; interaction segments now carry the structural
identity. A stored version 1 record carrying the field still normalizes, and
the historical result's availability count for it remains valid for version 1.

Normalized trajectories are versioned separately from C1 metrics. Version 2,
added after the frozen result for production post-mortems, records structural
`interaction_segments`: one per human turn, each with a stable
`<source SHA-256>:user-<row>` identity, an explicit `unit: human_turn`, the
half-open raw-row interval up to the next human turn, the `turn_text_sha256` of
the turn's text, and the `boundary_evidence` that established it. A human turn
is an interaction, not necessarily an engineering task: a continuation such as
"continue" opens its own segment, and C1 never groups segments into tasks.
Harness-injected context such as `<environment_context>` or `AGENTS.md`
instructions also arrives with the user role and opens no segment. A boundary is
established, in order, by the message's own content kinds (`user.*`), by an
exact match with a harness `UserMessage` item (whole text or one text part,
since image inputs split text), and only in rollouts recording neither, by a
closed list of known injected forms. Every event and limitation carries its
`interaction_segment_id`, or `null` outside any human turn. A version 1 input
normalizes to version 2 with `interaction_segments: null`, meaning boundaries
were not captured. Segment capture changes no measured quantity: over the 567
local rollouts it accepts and rejects exactly the same rollouts, and C1 metrics
remain version 1.

## Materialization accounting

The trajectory metric contract preserves:

- total materialization: the sum of every evidenced read, including repeats;
- unique materialization: the union of evidenced half-open ranges per stable
  `(path, content_identity)`;
- repeated materialization: total minus unique when both are complete.

If any applicable read lacks materialized-byte evidence, the total is `null`.
If any applicable read lacks stable content identity or a range sufficient for
overlap accounting, unique and repeated values are `null`. Known-byte subtotals
and explicit incompleteness reasons remain available for diagnostics.

Mutation events never contribute retrieval bytes. Reading and later editing a
governance file yields one retrieval event and one mutation event. Editing it
without prior retrieval yields only a mutation event.

## Corpus handling and outputs

The Codex rollout adapter reads local JSONL files in place, accepts the legacy
direct-function-call and current custom-tool-call envelopes, and never mutates
the source. Sanitized source identity is the source file's SHA-256; output does
not include the source path, raw prompt, raw command output, or conversation
text. Interaction segments carry only the SHA-256 of a turn's text, never the
text. Repository paths are relative; out-of-repository paths are redacted.

A successful baseline-gated run writes to a caller-selected untracked directory:

- `baseline_fingerprint.json`;
- `trajectories.jsonl`;
- `aggregate.csv` and `aggregate.json`;
- `run_metadata.json`.

The aggregate reports counts, rejection reasons, median, quartiles, range,
unique/repeated bytes, bounded/whole-file access, governance/non-governance
retrieval, mutations, and conspicuous outliers. These are observations, not
threshold recommendations. The compact, sanitized historical result is retained
in `governance_manifest_quality_stage_c1_results.json`; detailed normalized
trajectory files remain untracked.

### Edge-state interpretation

`CURRENT_STATE.md` and `docs/BACKLOG.md` are policy-declared `edge_state`
files. Their raw size is descriptive telemetry, never a direct quality penalty.
For each post-mortem segment, the relevant cost is observed consumption after
routing, not active surface membership or file length. The postmortem records
independently whether an edge file was registered on the surface, routed for
the segment when resolver evidence exists, actually read,
bounded/whole-file/repeated, and how much the segment materialized.

The profiles are intentionally different. `docs/BACKLOG.md` is a conditional
open-work authority, so retrieval locality, ambiguity, staleness, and authority
duplication matter when routed work uses it. `CURRENT_STATE.md` is
restart/staged-handoff context, assessed for restart completeness and handoff
clarity only when that path is exercised. Existing LOC guards remain separately
classified as human-reviewability, structural-discipline, or handoff-usability
controls; they are not agent-context-size scores. Edge-file reduction is not a
project goal, and unrecoverable loss of rationale, dependencies, or deferred
state is information loss rather than simplification.

## Commands

Use the repository-selected Python from `./gov env`:

```bash
python -m tools.experiments.governance_manifest_quality.cli fingerprint \
  --output /tmp/tet4d-c1/baseline_fingerprint.json
python -m tools.experiments.governance_manifest_quality.cli corpus \
  --source-root /path/to/local/codex/sessions \
  --output-dir /tmp/tet4d-c1
```

Both commands fail closed if any declared identity or frozen treatment path
differs. Focused verification is:

```bash
./scripts/verify_focus.sh \
  tools/experiments/governance_manifest_quality \
  --pytest tests/unit/experiments
```

Stage C1 completion additionally requires `./gov check`, the canonical full
gate, `git diff --check`, repository sanitation, and a clean worktree.

## Acceptance and deferrals

The instrumentation is accepted when deterministic fixtures cover bounded,
whole-file, repeated, overlapping, read/edit, edit-only, non-governance,
missing-evidence, malformed, and source-format-equivalence cases; negative
controls prove the fixture oracle rejects naive accounting.

The completed historical pass discovered 556 rollout files. It measured 302,
excluded 250 from other repositories, and excluded four after normalization;
all statuses reconcile. Of the measured trajectories, 163 have complete byte
evidence and 139 retain explicit limitations. The complete subset contains no
governance retrieval, so its exact total, unique, and repeated distributions are
all zero. Across all measured trajectories, the evidenced governance-byte lower
bound is 16,888,308 bytes (median 0, Q3 45,684.25, maximum 1,229,474). This lower
bound is not an exact total for incomplete trajectories.

There are 4,283 governance read events: 4,214 bounded and 69 whole-file. The
corpus records 1,714 governance mutation events in 103 trajectories, so
retrieval and intentional governance implementation remain separate dimensions.
`docs/BACKLOG.md` and `CURRENT_STATE.md` account for 68.5% of known governance
bytes and also have 896 mutation events, consistent with long, bookkeeping-heavy
or governance-active work rather than a simple waste interpretation. Forty
lower-bound outliers were reviewed from normalized metadata: 31 mutate
governance, 11 exceed 1,000 tool calls, and only six contain any whole-file
governance read. Nine have no governance mutation and are useful repeated-read
candidates, but unresolved search/command output prevents exact repeat analysis.

The earlier policy-pack observation holds: all 244 policy-pack reads were
bounded and none were whole-file; 23 trajectories also mutated the file. Source
revision, model, recorded token, and duration metadata are often available, but
independent outcome evidence is absent. The history is therefore useful for C2
task selection and telemetry design, but not for causal threshold calibration or
exact total/unique/repeated comparisons without richer retrieval evidence.

The PR118-baseline migration-bundle check reproduced outcome B. Canonical regeneration
would replace the stale `da6e2dd6...` policy digest with `44c126b6...`, add the
new governance config inputs, and refresh several authority-document digests.
This is classified as a pre-existing generated-artifact defect. Because the
ordinary full gate does not require regeneration and the delta is broader than
the C1 semantic objective, the generated bundle is left unchanged and its repair
is deferred.

Deferred work includes treatment perturbation, causal inference, threshold
changes, classifier optimization, route/scenario changes, VERSION compatibility,
the migration-bundle regeneration, Stage 28 extraction, and Stage 56 product
behaviour. Stage C1 does not continue automatically into any of those items.
