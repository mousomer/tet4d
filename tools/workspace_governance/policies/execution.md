# Completion-based execution

Owner: the shared workspace governance policy owner. Applies to local tests,
scripts, builds, remote CI, packaging and publication for every adopted consumer.
Machine contract: `execution.json`, resolved as `execution.completion`.

Run each operation through one completion-waiting invocation. Local commands must
return their final exit status. Remote work uses a blocking watch or completion
notification bound to the exact run and source commit. If the tool yields, resume
waiting on the same invocation; yielding is not a reason to redispatch work.

Agent-driven polling is prohibited: do not repeatedly query status, inspect log
tails to discover completion, or launch duplicate watchers. In particular, do not
run `gh run view` alongside `gh run watch RUN --exit-status`. A blocking watch's
internal service queries and a runner's internal process checks are permitted.

Independent operations may execute concurrently inside an invocation that awaits
all children and preserves every failure. Do not launch a second full verifier
when a pre-push hook already runs it. Report useful progress from existing output
or completion events; progress-message expectations do not justify status polling.

Timeout, cancellation, disconnect, unsupported completion and unknown outcome are
explicit states, never success. Reconnect to the same execution identity after a
lost connection. A bounded identity lookup for recovery or initial run discovery
is permitted; repeated discovery queries used as a completion loop are not.
Retrieve final results, artifacts and failure logs after the waiting invocation
returns. A retry is a deliberate new attempt after diagnosis, not an automatic
replacement for an execution with unknown outcome.

The selected tool may require bounded continuation waits. Those waits resume the
same handle and satisfy this policy. If no completion mechanism is available,
report that limitation instead of silently falling back to polling.

`gov check` establishes policy binding and integrity, not agent compliance.
Synthetic or explicitly supplied execution observations may be reviewed with
`execution_policy.review_execution`; missing observations remain unknown. This
policy enables no transcript collection, telemetry or global interception.
