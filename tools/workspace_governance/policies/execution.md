# Completion-based execution without autonomous polling

Owner: the shared workspace governance policy owner. Applies to every work type,
project, agent role and execution mode (`LOCAL_FIX`, `FEATURE`,
`STRUCTURAL_CHANGE` alike) of every adopted consumer, independently of CI or
GitHub. Machine contract: `execution.json` (`synchronous-completion-v2`),
resolved as `execution.completion`. It supersedes `synchronous-completion-v1`,
whose blocking-watch allowance is withdrawn.

## Rule

Agents MUST NOT autonomously poll external or asynchronous state. Polling means
repeated state observations whose purpose is to discover whether an external or
asynchronous operation has finished or changed. The prohibition holds whether
the repetition is performed by the agent, a shell loop, a subprocess, a CLI
tool's internal watch or interval mode, or repeated independent requests.
Violations carry the code `NO_AUTONOMOUS_POLLING`.

1. **No tool-watch exemption.** `gh pr checks --watch`, `gh run watch`,
   `watch(1)`, CLI interval/refresh modes and equivalent internal polling are
   prohibited. A tool repeating the query does not make the wait synchronous.
2. **No synthetic waiting.** `sleep`, timed shell loops, repeated API queries,
   background monitors of remote state and agent-issued refresh cycles cannot
   substitute for an external completion event.
3. **No invented dependencies.** Wait for remote state only when the declared
   task gate, repository protection rules or applicable governance require it.
   Local verification and remote CI are separate evidence obligations: a gate
   requiring verification on clean `master` does not add remote CI to it.
4. **Synchronous observation.** When remote state is required, make one bounded
   status request (for example `gh pr checks N --json name,state,bucket` or
   `./gov ci-status N`) and interpret its result.
5. **Pending is terminal for the current observation.** If the dependency is
   unresolved, report `PENDING_EXTERNAL` and end or suspend the workflow. Do
   not query again in the same turn.
6. **Event-driven resumption.** A genuine host completion notification, a
   relevant state-changing event or a new user instruction authorizes one new
   observation.
7. **No false verification.** Pending, unknown, unavailable and failed results
   are never successful verification. A task requiring successful remote CI is
   not complete while that CI is pending.

## Permitted

Local process synchronization (awaiting the exit of a command the agent
started, resuming the same yielded local invocation, draining its pipes),
bounded transport retries inside a single request, application input and event
loops, and deterministic computational loops remain permitted. A transport
retry must not become a repeated asynchronous-status query. Run independent
operations concurrently only inside an invocation that awaits all children and
preserves every failure; do not launch a second full verifier when a pre-push
hook already runs it.

Timeout, cancellation, disconnect, unsupported completion and unknown outcome
are explicit states, never success. Reconnect to the same local execution
identity after a lost connection. A retry is a deliberate new attempt after
diagnosis, never an automatic replacement for an execution of unknown outcome.
If no completion mechanism exists, report that limitation; never fall back to
polling.

## Enforcement

The pack's shared command policy (`command_policy.py`) classifies a normalized
tool invocation as `ALLOW`, `DENY` or `UNDETERMINED`; an undetermined
invocation that may observe remote state is denied. The pack-managed
`PreToolUse` adapters for Claude Code and Codex (`hooks/no_polling.sh`, bound
by `gov check`) apply it before execution and convert guard failure into
denial. Execution review (`execution_policy.review_execution`) applies the same
classification after the fact and distinguishes blocked attempts, executed
violations, repeated observations, compliant one-shot observations and external
notifications. Runtime coverage limits stay explicit; a passing `gov check`
proves binding and integrity, not agent compliance. This policy enables no
transcript collection or telemetry.
