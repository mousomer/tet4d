# Workspace governance v0.1

Status: implemented architecture contract for the first bounded extraction,
including the v0.1 integrity repair. The final section records an accepted
extension that is partly implemented.

## Ownership model

The vendored pack at `tools/workspace_governance/` owns generic schema,
resolution, diagnostics, pack-integrity, and environment-inspection mechanisms.
It contains no Tet4D semantic values: required authority IDs, the
execution-mode variable and the project manifest location come from the
workspace and project manifests, and `test_project_independence.py` rejects any
pack file naming a value from them. Portable agent telemetry is an accepted, not
fully implemented, extension of the pack's scope (see "Planned: portable
agent telemetry"). `.governance/workspace.json` owns only
membership, relationships, workspace defaults, and the pack-lock reference.
`config/governance/project.json` owns Tet4D executable governance facts added by
this extraction and stable references to human authorities. Human RDS,
architecture, and governance documents remain semantic truth. Machine-specific
locations may appear only in the ignored `.governance/workspace.local.json`.
Copy `.governance/workspace.local.example.json` to that ignored path when a
machine needs an approved interpreter or route-tool override. Its checkout and
cache maps are explicitly reserved and must remain empty in v0.1.

`config/project/policy_pack.json` remains authoritative for facts not migrated
in v0.1. Routes are the one exception: `config/governance/project.json` is their
canonical owner and `policy_pack.json:codex_routing.routes` is a mechanically
parity-validated compatibility facade. No product authority transfer occurs.

## Resolution and contradiction behavior

`gov resolve` composes the pack, workspace index, project references, and only
the permitted local execution overlay into an ephemeral, provenance-bearing
view. `gov explain` returns one resolved value or stable authority identity.
Exclusive-scope collisions fail as `AMBIGUOUS_AUTHORITY`; no discovery-order or
generic layer precedence exists.

A provenance-bearing resolved stable fact is sufficient for task decisions and
must not be rediscovered by reopening its backing manifest. Read the backing
authority when the resolved projection omits semantic detail needed by the
task, ownership is ambiguous or conflicting, a diff crosses an authority
boundary or escalation trigger, a provenance audit is required, or the task
modifies that authority. The backing source remains canonical; sufficiency of
its resolved projection is not an ownership transfer or a replacement of the
source.

`gov check` loads the versioned JSON schemas as structural authority, then
extends them with stable-ID uniqueness, authority reachability, route
reachability, route-facade parity, generated relationships, path sanitation,
field-use classification, and pinned-pack checks.

Reachability is enforced in both directions. An authority that no route
references, and a route that no execution profile or representative scenario
can select, are both `BROKEN_REFERENCE`: a declared fact nothing can reach is
unowned rather than merely unused, and its `consumed` classification cannot be
demonstrated.

## Environment contract

The Python constraint and dependencies are owned by `pyproject.toml`. The one
semantic priority is `TET4D_PYTHON`, then the approved repository-overlay
interpreter, then the inherited workspace overlay, then repository `.venv`, else
`ENVIRONMENT_INVALID`. The inherited overlay lives at
`${XDG_CONFIG_HOME:-~/.config}/workspace-governance/<workspace_id>.local.json`;
being keyed by workspace identity rather than checkout path, one runtime
selection is available to every worktree wherever it sits, including those
outside any common parent directory. The same declaration also starts
governance: the bootstrap chain reads this overlay, so a fresh worktree with no
`.venv` and no bootstrap variables can run `gov`. A shared editable environment
is still not certified across multiple worktree origins. The two overlays merge per key, so
a repository overlay naming only `tool_paths` keeps the inherited interpreter.
`PYTHON_BIN` is output
compatibility state only. `GOVERNANCE_PYTHON` selects only the CLI bootstrap and
cannot affect certification. `resolve_python_env.sh` delegates to `gov doctor`.
An inherited interpreter may be shared with projects outside this workspace, so
its `site-packages` is not inert and is not governed from here. A third-party
distribution can ship a generic top-level package, and a regular package
anywhere on `sys.path` beats a namespace portion, so repository code and tests
must never import an ambiguous top-level name such as `tests`: sibling test
helpers are imported directly, which is the standard pytest prepend-mode form
and needs no package at all. The constraint is permanent while the interpreter
is shared, and it is invisible from inside the repository, because the same
import succeeds under a private `.venv` that lacks the offending distribution.

Interpreter and source selection are separate decisions. Tet4D's distribution
and import package both normalize to `tet4d`; no distinct-name abstraction is
claimed. An installed project makes one checkout authoritative for every other;
the invoking checkout decides instead through a binding derived from
`environment.editable_source`. `gov env` emits the
interpreter, resolved execution mode, and, in source mode, that binding as shell assignments, because shell
cannot import the resolver and `resolve_python_env.sh` prints one interpreter and
rejects arguments. Gates consume it rather than deriving their own, which could
verify a different environment than `doctor` certified.

Injection happens only in source mode: injected everywhere, import origin would
equal the expectation by construction and `editable_install` could never observe
a foreign install again. Source mode instead adds two assertions that check
cannot make -- the bound source is this checkout, and no project distribution is
installed. Importability cannot see the second, because the binding wins the
import while the distribution remains a silent second answer.

One environment serves only checkouts whose declared requirements are
certifiably compatible. Before source-mode bootstrap mutates the shared
interpreter, it compares the requesting checkout with the shared declaration
snapshot using `packaging` requirement/specifier semantics. Identical and
simple overlapping interval constraints are accepted; disjoint intervals are
rejected; direct references, exclusions, compatible-release clauses, and other
intersections outside this conservative proof subset are rejected as unknown.
Python-version metadata is not a proxy for dependency compatibility. The shared
snapshot merges accepted declarations, so later bootstrap validates the full
environment requirement set rather than the last checkout's fingerprint.

Execution mode is declared, never inferred. `environment.execution_mode` names
the variable that carries it and the default when that variable is unset, and
the machine-wide overlay may declare it beside the interpreter -- a shared
environment owning no distribution is in source mode for every checkout on it.
Precedence is override, then overlay, then project default;
`source` means the project is imported from a checkout, `installed` that it
comes from a distribution. Which one holds decides whether `pyproject.toml` or
distribution metadata is the truthful dependency record, so reading it back
from whichever source happens to answer would make the check agree with any
environment it runs in, including one holding another worktree's build
artifacts. The set of modes is implementation, not configuration: a project
says which variable carries the mode and what it defaults to, never what a
third mode would mean.

`gov doctor` verifies interpreter/version selection, import and editable-install
origin, dependency authority, and reports `ENVIRONMENT_INVALID` via
`ENVIRONMENT_MISMATCH` diagnostics. Godot inspection remains route-specific and
with existing Tet4D tooling; v0.1 does not duplicate its platform contract.

## Execution modes and verification

`LOCAL_FIX`, `FEATURE`, and `STRUCTURAL_CHANGE` bound discovery breadth. They do
not select or waive final evidence: the task, referenced authority, actual diff,
claims, and risk still determine verification. The representative scenarios in
the project manifest exercise this separation, including distinct Godot
presentation fixes and features plus structural CI/product-platform routing
repairs. Automatic general-purpose prompt classification is intentionally out
of scope.

Scenario resolution evaluates every scenario whose `match_all` tokens occur in
the task, then selects the unique match with the highest numeric `priority`.
Manifest declaration order has no semantic effect. If multiple applicable
scenarios share the highest priority, resolution fails as
`AMBIGUOUS_AUTHORITY`; the manifest must express an unambiguous precedence
instead of relying on serialization order. Priorities encode known overlap
intent, not a total ordering of every scenario. The project uses four broad
semantic tiers: cross-layer work; constrained defects and routing repairs;
subsystem features and release work; and broad generic feature or governance
wording. The constrained-repair and subsystem-feature tiers each have one
specificity level above their generic level. This preserves structural scope,
lets a named repair beat a generic defect, and lets a named subsystem feature
beat generic planning or presentation wording. Peers remain equal where neither
authority subsumes the other, so a task that genuinely combines them fails
closed. The resolved view reports both the matched scenario ID and its priority
with project provenance.

A task that matches no scenario takes its mode's profile routes. `FEATURE` and
`LOCAL_FIX` default to `godot_product_shell`, because the Godot game is the
product. Python reference-engine work is reached through the `python` scenario,
in the broad-wording tier, and the `reference engine` scenario, in the
subsystem-feature tier.

## Pack updates and sanitation

`VERSION`, `MANIFEST.json`, and `config/governance/workspace.lock.json` identify
the vendored pack bytes. Hashing consumes the manifest-declared algorithm and
exclusions; sync copies manifest version/revision into the lock.
`gov sync` is the explicit local acceptance operation;
ordinary checks report `PACK_DRIFT`. Generic path checks complement, rather than
replace, Tet4D's existing bounded secret scanner and sanitation entrypoint.
While the pack is 0.x, every change to a pack schema raises the minor
`VERSION`, and its pull request states whether the change can invalidate an
existing manifest. The `MANIFEST.json` revision advances with every change to
pack bytes. Earlier v0.1 revisions predate this rule: `v0.1-integrity-1`, `-2`
and `-8` made breaking project-schema changes, the last requiring scenario
`priority`, while `VERSION` stayed `0.1.0`. They are not renumbered.

## Deferred

The compatibility policy pack, route semantics, product/platform matrix, exact
CI lanes, release rules, Godot/native parity, generalized orchestration,
automatic classification, and planner/runner redesign remain local to existing
Tet4D authorities and outside this extraction.

Workspace `relationships` and local `checkout_locations`/`cache_locations` are
reserved in v0.1. Workspace project membership/defaults and local interpreter/
tool paths are consumed. v0.1 selects the declared default project and its
repository/manifest path; it does not claim general task routing across several
projects. Schema annotations classify every declared field.

## Round 2 integrity contracts

`scripts/resolve_bootstrap_python.sh` owns bootstrap selection for the shell
launcher, `bootstrap_env.sh`, and `verify_local.sh`: `GOVERNANCE_PYTHON`, then
`$WORKSPACE_VENV/bin/python`, then the inherited workspace overlay interpreter,
then an executable local `.venv`, else a structured `ENVIRONMENT_MISMATCH`.
System Python discovered on `PATH` is not an approved bootstrap, and there is no
fallback past an unusable candidate. Explicit operator overrides stay strongest
and machine-wide authority precedes the repository-local fallback; the
repository overlay is deliberately absent from this chain, being per checkout
and therefore never present in the fresh worktree this tier exists to start.
Two-worktree operation is certified without a `.venv` symlink farm. A checkout
predating the inherited overlay still needs its four shared-environment
symlinks or `WORKSPACE_VENV`.
Bootstrap cannot ask the interpreter it is selecting to parse the overlay, so
the shell reads that one key itself with a depth-aware scan: an overlay may
carry a `tool_paths` entry keyed `interpreter`, and matching it would start
governance under a tool path.
Bootstrap only runs standard-library governance code; its early capability check
reads the lower bound from `[project].requires-python` before importing
`tomllib`. `bootstrap_env.sh` and `verify_local.sh` invoke the same early check
before creating or replacing an environment. Bootstrap never certifies its own
interpreter for project execution: `GOVERNANCE_PYTHON` can start governance and
nothing more. `check`, `resolve`, and `explain` need no third-party libraries.
`doctor` resolves the approved project interpreter independently of whichever
bootstrap started it, returning `ENVIRONMENT_INVALID` with
`ENVIRONMENT_MISMATCH` when that interpreter is unavailable.

`bootstrap_env.sh` consumes `gov env --allow-missing-interpreter`, so it mutates
exactly the interpreter and mode selected by the resolver. The missing-interpreter
exception is resolver-owned and limited to the declared installed-mode local
environment, which bootstrap may create. What it builds follows the declared mode:
installed mode an environment belonging to
this checkout, source mode declared dependencies in the shared toolchain and no
project. Its fingerprint and mutation lock sit beside that environment, since a
shared one is reachable from every worktree while a worktree's verify lock
guards only its own tree. `verify_local.sh` owns nothing and creates nothing.
The fingerprint is only an optimization: source bootstrap validates installed
versions against applicable base and optional dependency requirements on every
cache hit and after installation before recording success. An installation that
leaves a declaration unsatisfied records no fingerprint and names each
unsatisfied requirement on stderr. Its source-mode atomic directory lock stores
PID, hostname, and process-start identity when available. A live or ambiguous
owner is never stolen; only a proven-dead local owner (or detected PID reuse
when the platform exposes identity) is recovered. Foreign or malformed locks
remain diagnostic failures for an operator to inspect.
The selected project interpreter evaluates the full Python specifier using
`packaging`, explicitly declared in `pyproject.toml`. Missing packages and broken
metadata produce diagnostics, not forwarded subprocess tracebacks.

`resolve_python_env.sh` prints only the approved interpreter and rejects all
arguments. Shell entry points that may import project code consume `gov env`
instead, so they receive its source binding as well as `PYTHON_BIN`; neither
value is an independent selection input.

`canonical_owner_set` references the existing compatibility authority's
`authority_model.canonical_human_owners`. Graph validation requires exactly one
exclusive human file authority flagged `canonical_governance` for each owner,
with existing route reachability still required. Tet4D's existing surface
validator protects the six-domain owner set. ENGINEERING and VERIFICATION cover
Python engineering and verification; NATIVE_AND_PLATFORM and VERIFICATION cover
Godot, native, and parity. CONFIG_AND_GENERATED_DATA and SECURITY_AND_SANITATION
retain their respective owners; CHANGE_GOVERNANCE covers change discipline.
No separate Python, Godot, or parity governance documents are invented.

Authority sources explicitly distinguish files, directories, aliases, and JSON
pointers. An alias must reference a non-alias with the same source and cannot
claim exclusive or canonical ownership. Two exclusive identities cannot share
one source. Route `authority_refs` have set semantics; facade comparison sorts
both sides. Serialization order does not establish authority precedence.

Schema field-use annotations reference `field-usage.json` behavior families.
Each family identifies an implementation path and an executable mutation test.
Validation-only families use schema or sanitation validators; reserved arrays
and objects must be constrained empty. Tests execute the registry and the
contradiction catalog, including actual emissions for every advertised code.
The registry is a coverage index, not proof by declaration.

Generic generated surfaces in v0.1 support compatibility facades only. Drift
emits `CONFLICTING_VALUE`; `STALE_GENERATED_SURFACE` is not a public capability.
CONFIGURATION_REFERENCE and USER_SETTINGS_REFERENCE remain solely checked by
`generate_configuration_reference.py --check`. PROJECT_STRUCTURE and
CURRENT_STATE generated blocks remain solely checked by
`generate_maintenance_docs.py --check`. Broader generated-artifact migration is
deferred. The configuration reference covers `config/**`; workspace membership
at `.governance/workspace.json` is explicitly outside its scope and checked by
`gov check`.

`verification.canonical` is the unqualified repository gate (`verify.sh`), whose
normal mode uses the standard stability repeats. `verification.full` is the
existing agent invocation (`CODEX_MODE=1 ./scripts/verify.sh`), retaining all
verification families while reducing stability repeats. `targeted` is the
bounded focus gate, not a completion substitute. The `godot_toolchain` pointer
for the full repository invocation remains legacy compatibility debt; that
namespace does not describe the gate's ownership. No further policy family is
extracted here. Pack hashing ignores platform `.DS_Store` files through the
manifest exclusion mechanism, alongside bytecode caches.

## Canonical upstream boundary

The vendored pack lock proves the identity of bytes consumed inside Tet4D; it
does not identify an external canonical source. No current workspace or project
manifest declares the external package/repository, its immutable release
identity, or the trust owner allowed to publish it. The local Git remote named
`origin` and the policy pack's GitHub publication target are mutable publication
mechanisms, not governance-source authority, and cannot derive this contract
across forks, worktrees, CI checkouts, or alternate local checkouts.

Canonical extraction is blocked until governance decides the external
package/repository identity and release/version model. The smallest missing
authority is an immutable canonical-upstream identity with a publisher/trust
owner and deterministic export procedure; Tet4D's current lock is only a
consumer byte identity. The available choices are: (1) declare a governed
upstream repository plus immutable revision and export algorithm, then pin that
identity here; or (2) establish a versioned distribution/release identity with
equivalent publisher and reconstruction rules. Choosing either publication and
trust model requires owner/architecture review. Only after that decision can
extraction, deterministic pinning, drift protection, and offline consumption
proceed without inventing policy in resolver logic.

## Planned: portable agent telemetry

Status: accepted planning decision (2026-09-25). This section is the authority
for backlog items P1a–P1c; P1a is implemented and P1b–P1c are not.

**Implemented in P1a.** `tools/workspace_governance/telemetry.py` records each
`gov` execution as one first-hand immutable observation, validated against
`schemas/telemetry-event.v1.schema.json`. The envelope has an
`observation_id`, never an activity identifier: an observation is evidence
about an activity, not the activity itself. It is a `command_execution`
observation with a generic payload: a safe logical program identity, one
structurally classified argument token per argument, a `completion` phase, and
process and parent-process identities as correlation evidence. The current
`gov` completion producer also records exit status and duration, but those
result fields remain optional for future command observations. Its `source` is
`self_instrumented` and its attribution basis is `first_hand`. A `governance`
enrichment block adds what only `gov` knows about itself: the subcommand,
diagnostic identities, and, for `resolve` and `explain`, which routes, scenario
and authorities were handed out.
Recording is off unless the machine's local overlay sets
`"telemetry": {"enabled": true}`. Every observation records `observed_at`
(when its underlying fact occurred) separately from `recorded_at` (when the
pack persisted or imported it); daily files are selected by `recorded_at`. For
a `completion`, `observed_at` is when the command finished; it started
`duration_ms` earlier. Observations are appended to
`${XDG_STATE_HOME:-~/.local/state}/workspace-governance/<workspace_id>/telemetry/`,
one file per persistence day, readable only by their owner. A private,
owner-readable telemetry key sits beside that directory, in
`<workspace_id>/`, never inside it, so copying or pruning the events never
carries the key. It is generated as needed, published whole or not at all, and
never committed or printed. `gov` preserves only safe grammar
literals (subcommands, option names, fixed execution modes and boolean
switches); free-form values and machine paths, including an `explain` positional
query, are keyed HMAC-SHA-256 identities with a key identifier and a
normalization identifier (`gov-argv-1` for arguments). Length is retained only
where useful. HMAC correlation is scoped to observations produced or imported
with the same telemetry key: a transcript imported on another machine/key is
not expected to produce matching private identities. The recorded key
identifier makes key rotation or deletion detectable instead of silently
looking like a different command. Per-run context comes from the
`GOVERNANCE_TELEMETRY_CONTEXT` variable, a JSON object with optional
`session_id`, `task_id`, `agent`, `model` and string `labels`;
malformed
context is recorded as `invalid`, never guessed. A failure to record prints one
warning and never changes the command's outcome.

The pack records generic agent activity; projects and experiments interpret it.
Activity flows from agent execution through capture sources to the pack logger,
into a versioned raw event stream, through generic pack reconstruction, and
only then to project- or experiment-specific analysis. A repository that
installs the pack gets the same instrumentation without copying Tet4D scripts,
and an experiment can be replaced while the historical record stays usable.

**What is recorded.** Low-level facts, not answers to current questions: task,
trajectory and session identity; agent and model identity when available;
timestamps; file reads, with their range or whether they were bounded or full;
mutations; command executions with status and duration; verification
invocations and results; governance resolution and materialization; declared
segment boundaries; and the provenance needed to reconstruct what happened. The
logger is not designed around the C1 or G1 questions. A future experiment must
be able to ask questions nobody has formulated yet.

**Schema.** The event schema is versioned and project-independent. It declares
no project paths, authority names, experiment identifiers, treatment or control
concepts, or project classifications; project values appear only as recorded
data. Per-run context, such as an experiment arm, is supplied at invocation as
opaque labels that the schema carries and never interprets. It never comes from
`config/governance/project.json`, which is a governance-treatment root: context
stored there would put the instrument inside the treatment and make switching
arms a Manifest change.

**One observation model.** Every capture source emits observations in this one
versioned schema, layered as activity semantics, then the observation, then its
provenance and attribution, then optional domain enrichment. The event type
and payload say what happened; the `source` block and attribution basis say how
it was observed. An event type names the fact a source actually observed, never
an inference about it. A structured read found in a Codex transcript and the
same read found in a Claude Code transcript are the same kind of event, and a
`gov` execution is a `command_execution` like any other command. A filesystem
snapshot observes only that a path's state differed across an interval: it
never yields a read or a write, and it names no actor. No source defines
its own event type, top-level format or parallel telemetry stream, and domain
detail only one observer can see goes in an enrichment block.

`source_ref`, when present, identifies a source-native item or pairing such as
a future Codex call ID. `evidence_ref`, when present, identifies underlying
source evidence independently of the parser that derived the observation.
Neither is required for self-instrumented `gov`. Generic run context carries
opaque invocation labels only; it does not carry source-native call IDs.
Process and parent-process IDs are local, ephemeral supplementary evidence,
not generally reliable cross-source invocation identities. They do not replace
an observation ID, `source_ref`, or `evidence_ref`.

**Observations are never merged by resemblance.** Each record is one observation
with its own stable `observation_id`, and a stored observation is never rewritten or
combined. Two observations may describe the same activity, such as a
first-hand `gov` event and a transcript's record of the same call. Matching
program, arguments and approximate time is not enough to treat them as one.
Reconstruction records a correlation only on explicit evidence, such as a
shared source-native call identity in `source_ref`, together with that
evidence and a confidence, and keeps both observations until the correlation is
strong enough.
The observed fact, its source/provenance, any attribution, and a later
correlation conclusion remain distinct claims throughout that process.

**v1 compatibility.** Telemetry schema v1 freezes the observation envelope and
compatibility semantics, not an exhaustive set of activity payloads. Within v1,
later work may compatibly add event-type values, attribution or provenance basis
values, optional fields, and event-specific payload definitions. Readers must
tolerate unknown optional fields and tolerate or skip event types they do not
understand where appropriate; they must not treat the initial enums as
exhaustive. A reader refuses a `schema_version` it does not support rather than
reading it as v1, as `iter_events` does. No later payload type is implemented by
this P1a work.

**Capture is passive.** Sources are the pack's own commands, which observe
their own executions first-hand; importers for agent transcripts; filesystem
snapshots; and live agent hooks, only where a consumer needs evidence that
transcripts lack. Importers and hooks are specific to an agent
runtime, not to a project, so they belong in the pack. An agent declares only
segment boundaries, which remain telemetry rather than ground truth; it does
not call a logging command for ordinary activity.

**Snapshots are evidence, not attribution.** A before/after filesystem delta
establishes that state changed during an observation interval. It does not
establish which agent or process caused the change. Every event records its
source and the basis of any attribution, such as a tool call that names the
write as opposed to a change seen only within the interval. Later analysis must
not turn that correlation into attribution.

**Retention is separable.** An event record carries the identity of the
transcript it came from, its hash, the parser and parser version, and the source
location. Keeping the raw transcript, which may hold prompts, file contents or
secrets, is a configurable storage and retention policy, not a condition for
keeping telemetry. Where the raw source is kept, a newer parser may re-derive
earlier events; where it is not, the recorded events stand as parsed.

**Storage.** Logs live outside the repository, keyed by workspace identity like
the inherited overlay. Privacy-sensitive correlatable paths and free-form values
use the local keyed identities described above rather than unkeyed hashes;
anything retained passes secret scanning. There is no committed log corpus.

**Reconstruction and analysis.** The pack reconstructs only what is semantically
universal: segments from boundary events, read and write timelines, and
invocation results. Calibration, treatment-versus-control comparison,
governance-effectiveness metrics, the G1 compatibility outcome and postmortem
aggregation stay outside the pack and consume its interface. They never decide
what is logged.
