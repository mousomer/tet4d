# Supervised completion without agent polling

Owner: the shared workspace governance policy owner. Applies to every work type,
project, agent role and execution mode (`LOCAL_FIX`, `FEATURE`,
`STRUCTURAL_CHANGE` alike) of every adopted consumer. Machine contract:
`execution.json` (`supervised-completion-v3`), resolved as
`execution.completion`; operation profiles: `operation_profiles.json`. It
supersedes `synchronous-completion-v2`.

**Primary acceptance criterion:** covered operations cannot generate
uncontrolled agent polling. A ten-minute job requires one submission and one
supervised wait, not hundreds of agent turns checking status. When a blocking
wait returns `pending` because its response window expired, the supervisor
continues waiting on the same operation within budget. When the waiting
mechanism fails, it reports an error; it never silently switches to status
polling.

## Rule

Agents MUST NOT repeatedly query status, logs, files or process state to wait
for an operation's completion. Use synchronous execution or the designated
supervised completion mechanism. Where a service requires polling, an approved
adapter performs it under enforced timing and request budgets, without repeated
agent involvement.

Repeatedly reading a log, checking whether an output file exists or inspecting a
process counts as polling when it is used to detect completion. So does
repeating the supervisor's own status report (`gov op list`, `gov op result`)
for a pending operation. Ordinary repository inspection (`git status`,
`git diff`, reading source files, running tests) remains permitted. Violations
carry `NO_AUTONOMOUS_POLLING`; probes of a managed operation carry
`OPERATION_PENDING`.

## Ownership

| Part | Owns |
| --- | --- |
| Policy pack (`execution.json`, this document) | Permitted behaviour and the transition rules |
| Service profile (`operation_profiles.json`) | Identity, ordered completion preference, whether adapter polling is authorized, polling limits, the operation budget |
| Supervisor (`operation_supervisor.py`, `./gov op`) | Mechanism selection, cadence, budgets and durable operation state |
| Service adapter | Executes the selected mechanism: one blocking call, continuation or status request at a time |
| Pack hook (`hooks/no_polling.sh`) | Rejects prohibited agent actions before dispatch, using supervisor state |

The agent chooses none of these: the command line accepts no mechanism,
interval, backoff, window or budget.

## Deterministic completion path

Every managed operation starts under a profile that declares:

1. **Identity**: the operation id plus, for example, argv and process id, a run
   id and head commit, or a continuation handle.
2. **Ordered preference** among the mechanisms the service supports:
   `synchronous_return`, `notification`, `blocking_wait`,
   `controlled_continuation`, each with its response window.
3. **Adapter polling**: eligible only when the profile sets
   `adapter_polling.authorized` and no preferred mechanism is available. Its
   minimum interval, backoff factor and maximum interval are fixed there.
4. **Budget**: the operation's waiting deadline, request limit, wait limit and
   the number of renewals a user instruction may grant.

The supervisor selects the first mechanism in preference order that the bound
adapter can perform for this operation, otherwise authorized adapter polling.
Each selection is recorded with the mechanisms found unavailable. If nothing is
eligible, the result is `mechanism_error` with reason `no_supported_mechanism`:
report that limitation and never fall back to an agent-written loop.

Profiles are validated before any operation starts, at pack load (`gov check`)
and again when the supervisor loads them. A profile is rejected when it is
incomplete or contradictory: no identity or budget; unknown keys; a mechanism
without its parameters; parameters for a mechanism outside the preference;
polling listed as a preference; a window longer than the deadline; a minimum
interval above the maximum or below one second; a backoff factor below one; an
immediate-response fraction outside (0, 1]; or fixed transition rules changed.
The profile is frozen into the operation record at submission and checked
against its digest, so it cannot be weakened while the operation is pending.

Run managed operations through `./gov op`: `run` submits and awaits in one call;
`submit` registers, `wait` awaits, `result` returns a completed outcome. In
Claude Code, start a wait that may outlast the tool-call limit with
`run_in_background`, so completion arrives as a harness notification.

## Transition contract

| Event | Transition | Status | Reason |
| --- | --- | --- | --- |
| Terminal outcome | Return it with evidence (exit status, conclusion, log tail) | `succeeded`, `failed`, `cancelled`, `unknown` | `completed` |
| Response window expires | Continue the same handle within the remaining budget | stays `pending` | `response_window_expired` |
| Calling tool stopped mid-wait | The next wait continues the same handle and budget | stays `pending` | `waiter_interrupted` |
| Deadline spent | Preserve the handle; never restart or cancel | `deadline_expired` | `deadline_expired` |
| Request or wait budget spent | Preserve the handle; never restart or cancel | `budget_exhausted` | `request_budget_exhausted`, `wait_budget_exhausted` |
| Mechanism fails | Report an explicit error; no fallback | `mechanism_error` | `mechanism_failure` |
| Repeated immediate `pending` | Stop automatic retries | `adapter_fault` | `repeated_immediate_pending` |
| Preferred mechanism unavailable | Next preference, or authorized polling, keeping identity and consumed budget | unchanged | `selected`, `preferred_unavailable_authorized_polling` |
| New user instruction after a stall | Resume the same handle; renew an exhausted budget, at most `max_renewals` times | unchanged | `user_instruction_resume`, `user_instruction_renewed_budget` |

An eligible renewal records the newer instruction identity with the wait.
A replay cannot create a newer identity. An exhausted request or wait budget
returns the durable operation result even if no waiter survived to report it.

The budget belongs to the operation, not to a wait. Waiting time, requests,
waits and polling cadence persist in the operation record across waits,
mechanism changes, interfaces and sessions. Every result reports the status,
reason, selected mechanism, profile id and digest, budget, consumed and
remaining amounts, recent transitions and enforcement errors. Only `succeeded`
is verification; pending, unknown, cancelled, abandoned and error results
never satisfy a verification requirement.

## Cadence belongs to the adapter

The supervisor controls blocking durations, continuation eligibility, polling
intervals, backoff and request limits, and holds an exclusive waiter lock, so
concurrent or redundant waits on one operation are refused. Cadence persists
between waits: a new or restarted wait first waits until the next permitted
request time, so wrapping an immediate status check in `gov op wait` and
interrupting it does not produce a faster cadence. A request reserves its
budget before dispatch. For polling, the next interval starts at the
adapter response or, after an interruption without a response, at recovery.

For blocking calls and continuations, an immediate return caused by completion
is valid. An immediate `pending` return makes the adapter keep the rest of the
window before the next call; repeated immediate `pending` returns are an
adapter fault, and the supervisor stops instead of retrying. Moving an
aggressive loop into a wrapper does not satisfy this policy. Tool watch modes
(`gh run watch`, `gh pr checks --watch`, `watch(1)`) are not approved adapters:
their cadence is agent-controlled.

## Operation-specific, stateful enforcement

The pack hook consults the durable per-checkout operation registry before
dispatch, independent of agent session, turn, interface and context
compaction. While an operation is pending it refuses status queries, log and
output-file reads, process probes, `sleep` substitutes for waiting, duplicate
submissions, redundant waits and a repeated supervisor status report under the
same user instruction. A `gov op` call composed with other shell commands gets
every probe check. The command a `gov op run` or `submit` would start gets the
same checks, in the hook and again in the supervisor before it starts, so a
probe wrapped in a new operation is still a probe of the pending one.
Local duplicate detection compares argv and resolved working directory across
profiles at submission and in the child probe. Quoted argument whitespace is
significant. Relative artifact paths and Glob bases resolve from the invocation's
working directory. A single `*` matches within a directory entry and `**/`
can also match zero directories. Supported unquoted shell wildcard patterns
are checked against protected outputs, and Grep's explicit or default base
is checked for overlap with those paths. Prefix-sharing files in a sibling
path retain their own identity.

For supported GitHub queries, a pending run reserves its run ID and bound commit
within its repository. Direct reads of either are refused and a query for an
independent commit or run uses ordinary observation policy keyed by repository
and the observed commit or run. Managed runs are found across checkouts sharing the same state base.
Hook and supervisor use the same remote reservation for an instruction. A broad workflow-run
listing that may include the pending run has one dispatch per repository per
user instruction, shared by the hook and supervisor across supported CLI, REST
and MCP requests. Output fields, session changes and agent state changes do not
renew that allowance. Only a distinct user-prompt event in the issuing runtime and session
renews that instruction's allowance. Replaying that event, delivering a prompt
to a different session, or sending a callback without a stable event identity
does not renew the issuing instruction. The broad allowance
does not grant a wait, adapter request or operation budget renewal.
One shell admission must not fan out into repeated remote observations
through a recognized repeater. Local repeaters remain available. A shell
wrapper that submits a remote observation must be a standalone supervised
call so its instruction can follow the child to the dispatching entry point.
The allowance is reserved before dispatch, including when an admitted request
subsequently fails. An unreadable allowance blocks the affected broad query
and reports guard degradation. Independent work and the supervisor's own
completion mechanism remain available.

A remote run's success is verification only when
its head commit matches the full commit SHA bound at submission; without that
binding the outcome is `unknown`. Its successful result records the repository,
run ID, verified head SHA and service conclusion. Submission persists the operation identity and an uncertain start intent
before the service is called. Only an accepted receipt or adapter-owned
reconciliation can transition that intent to pending. A start with a missing
receipt remains guarded and reports `start_uncertain` under its original ID.
Submitting the same operation again never retries an uncertain start.
Wait ownership is registered under the registry and waiter locks.

A denial names the operation and the permitted next action and blocks only the
offending call. It must not start a retry cycle: continue independent work, use
the designated completion mechanism or yield.

A guard failure (missing interpreter, crash, deadline, unreadable state) blocks
only calls that plainly wait for or probe an operation and lets every other call
proceed with a `GUARD_DEGRADED` warning, which is also recorded with the
checkout's operations when the registry is reachable. No waiting-policy failure
may become a blanket prohibition of shell use.

An optional classifier failure leaves independently identifiable operation
checks active. An unreadable operation record reports record_unreadable
for its identity and keeps its saved guard scope active. Where scope cannot
be reconstructed, requests that could probe or duplicate the damaged
operation require repair of the record before dispatch.

Shell pattern detection catches common probes and loops but cannot establish
complete enforcement and does not justify a universal compliance claim.
`operation_profiles.json` declares the interfaces and services the adapter
actually covers and what remains uncovered.

## Unmanaged remote state

For remote state without a managed profile, make one bounded status request,
report `PENDING_EXTERNAL` if unresolved, and resume only on a notification,
relevant event or new user instruction. Wait for remote state only when the
declared gate requires it. Local verification and remote CI are separate evidence
obligations: a gate requiring local verification does not add remote CI to it.
Reconnect to the same execution identity after a lost connection; a retry is a
deliberate new attempt after diagnosis, never an automatic replacement.
Independent operations may run concurrently inside an invocation that awaits
all children and preserves every failure.

## Conformance and rollout

Release-blocking behavioural tests drive action sequences through the hook and
supervisor with a simulated clock and service, and assert downstream calls and
timing, not only warning text. Publishing this contract and its conformance
fixtures is separate from harness acceptance: a policy-pack version change does
not show that a consuming harness enforces this policy, and each harness is
compliant only after the behavioural suite passes against its own dispatch
path. `gov check` proves binding, integrity and profile validity, not agent
compliance; this policy enables no transcript collection or telemetry.
