# Production Governance Post-mortems

Status: operational analysis aid; non-authoritative and observational.

## Purpose

This is the thin production companion to Stage C1 trajectory measurement. It answers whether a governance encounter changed a decision and whether that decision has observable outcome evidence. It is not an experiment framework, manifest redesign, scoring model, or automatic governance-rewrite mechanism.

Edge-state files are evaluated by consumption and function, not raw length.
`docs/BACKLOG.md` is conditionally routed open-work authority; `CURRENT_STATE.md`
is restart/staged-handoff context rather than ordinary task authority. For each
observed edge file the postmortem separates surface registration, resolver
routing when captured, actual reads, bounded/whole-file/repeated reads, and
segment-local materialization. It reports navigability, staleness, authority
duplication, information retention, and size-related friction only when
evidence supports them. A large unconsumed file has no inferred context cost,
and a shorter file that loses unresolved rationale is not an improvement.

Production post-mortems are the primary source of evidence about governance usefulness. Controlled experiments are used selectively to resolve causal questions that observational task evidence cannot answer.

The evidence chain is intentionally explicit:

```text
manifest/rule encountered -> observed decision -> observed outcome evidence

manifest access != manifest usefulness
compliance      != causal contribution
task success    != governance success
```

Compliance, successful verification, and successful task completion are not causal evidence that governance contributed positively. An encounter without an evaluator-supplied decision and observable outcome evidence remains `unknown`, as does anything supported only by temporal proximity. The descriptive comparisons below (projected/read, route/work, artifact coverage) never create a contribution.

## Existing inputs and the remaining gap

| Existing source | Mechanically recoverable evidence | Post-mortem gap it leaves |
| --- | --- | --- |
| C1 normalized trajectory | Human-turn interaction segments, repository revision, model, recorded tokens/duration, ordered retrieval/mutation/execution events, paths, and content identities. | Decision, contribution category, outcome linkage, and exhaustive exposure (see below). |
| G1 work-segment observer | Declared task/session boundary, start/end commits, and changed artifacts with roles. It also records `work_type`, `final_outcome`, failures, retries, and a self-reported tool-call count, which are available but not yet integrated. | Model, manifest encounters, and product/meta judgement. |
| Git and verification events | Revisions, mutations, test-command failures, and final command observations when recorded. | Task completion, rework intent, review findings, and causal attribution. |

The record binds the interaction segment, model, revision, and manifest exposure where evidence exists, leaves unavailable values as `not_recorded` or `not_inferable`, and uses an optional evaluator overlay only for fields needing judgement. It does not reconstruct missing transcripts or infer a branch, model version, final outcome, or causal effect from surrounding activity.

A C1 rollout is not itself an engineering task, and neither is a human turn. C1 trajectory version 2 records one interaction segment per human turn, with an explicit `unit: human_turn`; harness-injected context that also uses the user role opens none (the C1 protocol defines the boundary evidence). A segment carries a stable identity, row bounds, the SHA-256 of the turn's text, and its boundary evidence, never the text. Every recovered event carries its segment identity, and a post-mortem slices all event groups to one segment, so every emitted record names an identified human turn under `interaction` without claiming that it is a task: a continuation such as "continue" or "pull" is its own segment of what may be one engineering task. The task a segment serves is reserved as `interaction.task_group_id`, which version 3 keeps at `{"value": null, "evidence_state": "not_inferable"}`; neither the producer nor an evaluator can assert a grouping, and a record that does is rejected. A trajectory without a segment (a version 1 record whose boundaries were never captured, or a thread with no human turn such as a sub-agent) yields an `interaction_boundary_unavailable` batch diagnostic with `postmortem_emitted: false` instead of a post-mortem, and never stops the rest of the batch; evidence outside every segment is reported as `evidence_outside_interaction_segments`. The description is never derived from the turn text and stays `not_recorded` unless an evaluator supplies it. A bound G1 segment's declared `task_id` is kept beside the structural identity as `g1_task_id` provenance, never as the task group, and an evaluator cannot rebind the identity, the provenance, or the task group. Trajectory-scoped v2 post-mortem records are not reinterpreted as segment-scoped records.

## Record and activity

`tools/experiments/governance_manifest_quality/postmortem.py` produces a version 3 JSON record: source trajectory and interaction-segment binding, outcome evidence, measured `activity_total`, the activity partition, manifest encounters/effects, edge-state assessment, missing guidance, limitations, `encounter_coverage`, resolver projection, projection/read comparison, advisory route/work alignment, and G1 artifact coverage.

Activity categories are a partition of measured burden. For every proxy with a measured total, `activity_total = product + meta_required + meta_induced + waste + unknown`, and validation rejects any record that breaks it. `action_count` counts C1 execution events inside the selected interaction segment. C1 currently records elapsed milliseconds and total tokens only at rollout scope, so a single-segment rollout keeps them while a multi-segment rollout, even one whose later turns merely continue the work, leaves them unavailable rather than copying them into every segment. A G1 segment adds boundaries and artifacts but never overrides C1 totals, because G1 reports 0 tool calls whenever the count was not supplied.

All measured activity starts as `unknown`. An evaluator reclassifies it into `product`, `meta_required`, `meta_induced`, or `waste`; `unknown` is always the unattributed remainder and cannot be set directly. Attribution may not exceed a measured total, and a proxy without a measured total cannot be attributed. No path-based rule classifies an edit by itself. Burden ratios are per proxy, never mixing units, and remain null until product and at least one meta category have been attributed:

```text
(meta_required + meta_induced) / product
```

Each observed governance read becomes a manifest encounter with `effect: unknown`. The evaluator may only update an observed `(source, encountered_at)` pair, at most once, and any non-`unknown` contribution requires both a decision and outcome evidence. Supported categories are `decisive`, `useful`, `confirmatory`, `neutral`, `distracting`, `harmful`, and `unknown`.

Missing guidance is separate from a harmful manifest: it records an observed failure the current material did not address and a candidate scope, without automatically changing governance.

## Encounters are partial exposure evidence

An encounter is a file read recognized by the trajectory producer, so governance encounter telemetry is partial, and every record and aggregate declares that in `encounter_coverage`. Governance CLI output (`./gov explain`, `./gov check`, `./gov env`) and harness-injected instructions such as `AGENTS.md` context are `not_observed`. File reads are observed only through C1's bounded read grammar (`partial`). `execution_events_without_recovered_command` counts tool calls from which C1 recovered no shell command; any reads they made are invisible. The current Codex Desktop `exec` form quotes its `"cmd"` key, which the C1 adapter does not recover, so recent Codex sessions report every tool call in that count and no encounters.

A low encounter count is therefore not evidence of low governance exposure, and `projected_not_observed_read` is not evidence that a source was unused.

Real C1 reads record neither `authority` nor `route`, so `rule_or_section` stays null and aggregation is per source file path. A resolver authority is not a finer identity than the path, and the path-to-authority mapping can be ambiguous: `docs/architecture/authority_map.md` is the source of both `subsystem-ownership` and `godot-runtime`. The projected/read comparison carries the resolver's authority IDs instead. A `#rule_or_section` key suffix appears only when a trajectory producer or evaluator records one.

## Resolver, reads, and changed surfaces

Resolver evidence is a captured `gov explain --task "exact task text"` JSON result paired with the exact task string; routing is phrase-sensitive, so the string is mandatory. The raw resolver output is retained so its `entries` structure provides scenario, route, authority, verification, owner, and source provenance without a parallel semantic schema. A recorded result distinguishes a matched scenario, no matching scenario with a fallback/default route, and no projected route. Without captured resolver evidence the projection, comparison, and route lists are null, never an empty projection. A reconstructed probe is not historical resolver evidence unless the original task string is known.

Projected governance and actual governance reads are different evidence surfaces. The comparator matches projected authority and dispatch sources against all observed reads, whatever their C1 source class, because C1 classes some projected authorities, such as `docs/ARCHITECTURE_CONTRACT.md` and `docs/rds/`, as non-governance. `read_not_projected` uses only governance-classified reads, since it describes governance consumed outside the projection. Read limitations remain attached, and none of `projected_and_read`, `projected_not_observed_read`, or `read_not_projected` establishes relevance, waste, a projection defect, contribution, or benefit.

G1 artifact paths, or C1 `apply_patch` mutations when no segment is bound, give the modified top-level surfaces. For the three surfaces with dedicated routes (`godot/`, `native/`, `packaging/`) the route/work comparison runs both ways: a modified dedicated surface whose route was not projected, and a projected dedicated route whose surface was not modified. Other surfaces are not compared. `mismatch_observed` is advisory, keeps `causal_interpretation: unknown`, and prescribes no route. A bound G1 artifact must contain a non-empty path and an explicit role from the existing G1 role vocabulary (or explicit `unclassified`); malformed or role-less artifacts reject the post-mortem. Coverage records observed, classified, and unclassified artifacts with a `migration_limited`, non-normative interpretation; it is not a threshold, score, or gate.

## Aggregation

Repeated reads do not create repeated segments. Each aggregate group counts unique `(source_trajectory_id, interaction_segment_id)` pairs as `interaction_segment_count` and sums segment-level activity once per segment, while `encounter_count` keeps every read. Segments are not tasks, so the aggregate reports `task_group_count: null` instead of any engineering-task count; `by_task_class` groups segments by the evaluator's task class. Decision Yield `(decisive + useful) / judged` and Confirmatory Fraction `confirmatory / judged` use only judged, non-`unknown` encounters: null means not evaluated, and `0.0` means evaluated with no positive contribution. `judged_encounter_count` and the per-category counts expose all three states. The aggregate rejects a repeated interaction segment and is labelled descriptive evidence, not a causal estimate or a single manifest-quality score.

## Use

The `postmortem` command accepts C1 trajectories as JSON or JSONL, in the raw event form or C1's own normalized output such as a corpus `trajectories.jsonl`. One trajectory can yield multiple post-mortems when it has several interaction segments, and the output lists `diagnostics` for trajectories that yielded none. Every optional overlay record is `{"source_trajectory_id": ..., "interaction_segment_id": ..., "<payload>": {...}}` with payload `evaluation` (its identity block is `interaction`), `resolver_evidence` (`task_text`, the exact string passed to `gov explain`, which need not match the user's request, plus `resolver_output`), or `work_segment` (a G1 record), and binds to exactly one supplied interaction segment. Unmatched, repeated, or malformed overlay records fail the command and name the segment identity, so supplied evidence is never silently dropped.

```bash
"$(./scripts/resolve_python_env.sh)" -m tools.experiments.governance_manifest_quality.cli postmortem \
  --trajectory /path/to/trajectories.jsonl \
  --evaluator /path/to/evaluator-overlays.jsonl \
  --resolver-evidence /path/to/resolver-evidence.jsonl \
  --segment /path/to/work-segments.jsonl \
  --output /tmp/tet4d-postmortem.json
```

The output contains machine-readable records, compact per-segment summaries, and descriptive aggregates by source, model, and evaluator-supplied task class. Historical trajectories are valid inputs; partial history produces a partial record rather than an invented value. The operational target is a small evaluator pass over exceptions that need judgement, not mandatory prose for every segment; record a decision/outcome link only when it can be defended.

## Calibration specimens

On 2026-09-21 three real Codex rollouts were adapted by C1. Their historical normalized records predate interaction-segment capture, so they remain trajectory diagnostics rather than segment post-mortems unless the raw rollout is re-adapted with its human-turn boundaries:

- `01a0c556`, the post-mortem implementation itself, holds two tasks in one rollout: 99 tool calls, none with a recovered command, so no encounters. Its second task's instructions were truncated at the source, the turn ended at the model usage limit without a final report, and its last `verify.sh` exited 0 afterwards, visible only in the raw rollout.
- `01a0c497`, the Stage 56G repair (PR #127): 32 tool calls, none recovered, and Godot-only mutations, so route/work reports `mismatch_observed` against the fallback route.
- `01a0bdcc`, a long-run session containing the original Stage 56G work (PR #126) among other tasks: 792 tool calls, 71 with recovered commands, and 125 reads, all in one trajectory.

Candidate routing defect, observed and not repaired here: 7 of the 8 captured resolver calls in these sessions matched no scenario and fell back to `python_reference_engine`, including `Stage 56G real Godot window responsive cockpit reflow camera fitting and production integration tests` and governance-tooling tasks. Only `Add a bounded Godot presentation feature for the live cockpit responsive layout and 4D orientation display; do not change gameplay semantics.` matched `godot-presentation-feature`. Reproduce with `./gov --json explain --task "<string>"`.

## Known limitations

- Governance CLI output and injected instructions are not encounters, and C1 does not recover commands from the quoted Codex Desktop `exec` form; interaction segmentation does not change either.
- An interaction segment is one human turn, not an engineering task: follow-ups such as "continue" or "pull" are separate segments, and an auto-review thread's review requests are that thread's segments (separable by model). Grouping segments into tasks is reserved (`task_group_id`) and not inferred.
- C1 mutations cover `apply_patch` edits only; generator or shell writes appear only through G1.
- G1 `work_type`, `final_outcome`, failures, retries, and tool-call counts are available but not integrated.

Deferred work is tracked in `docs/BACKLOG.md`.
