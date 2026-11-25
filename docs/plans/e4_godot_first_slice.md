# First Godot journal and offline sync slice

Role: implementation proposal

Status: synthetic implementation, interactive QA pending

Last updated: 2026-11-22

Parent contract: [E4 client journal and offline sync](e4_client_journal_and_sync.md)

## Proposed slice

Build an explicitly launched Godot QA scene that uses one synthetic account
and one pre-confirmed assessment visit. The scene presents a fixture slot,
accepts a four-coordinate answer, and shows whether the answer is pending,
synced, paused, or blocked. Use the same path in headless and interactive QA.
Start offline, save a response, kill and restart Godot, reconnect through an
injected fake transport that commits but loses its first response, and replay
to a verified receipt. The QA scene should be reachable from a test entry
point only. Keep the normal product entry point independent of it.

The slice exercises the actual Godot persistence and scheduling code. It
needs no real participant, account provider, remote endpoint, new native rule,
or assessment scoring. Preload the confirmed visit and slot manifest from a
synthetic fixture. The server's repeatable start or authenticated read-back
remains a prerequisite for a future live workflow.

## Implementation boundaries

| Area | First implementation |
| --- | --- |
| Storage | One serialized worker owns versioned immutable command segments and an acknowledgment checkpoint in an isolated test root under `user://participant_data/`. Validate internal fixture identifiers before path construction. Persist presentation before accepting an answer, and persist the answer before reporting it saved. Ignore unpublished temporary files, recover a valid segment published ahead of its checkpoint, block on a missing or corrupt committed segment, and reclaim only after a verified checkpoint is written. Apply the approved warning and hard caps to the synthetic enrollment. |
| Filesystem | Inspect and reuse `PersistentFileReplacement` only for operations whose failure semantics fit the journal. Its backup fallback can leave a recovery interval between renames, so journal startup must explicitly recover a valid generation or block. Keep storage operations injectable for testing. Establish process-kill recovery on the named development host. Packaged crash and power-loss claims require storage primitive and filesystem evidence before rollout. |
| Runtime | Use a single background worker for filesystem operations, with results handed back to the main thread. Keep the worker off the scene tree. Inject time and the fake transport into the coordinator. Keep current-process scheduling monotonic and persist reboot-aware retry checkpoints using UTC plus a conservative delay when wall time is uncertain. |
| Wire | Share golden command-body and receipt-digest vectors with the existing Python E4 adapter. Encode only the approved v1 field shapes and integer ranges. Freeze canonical UTF-8 bytes, UUIDs and observation times before sending. Validate the exact receipt ID set and sha256 digests before checkpointing. Plain JSON serialization alone does not establish RFC 8785 compatibility. |
| Delivery | Use one in-flight ordered batch per enrollment, 64 commands and 64 KiB max, the approved coalescing and spacing, and a persisted retry budget. Fence stale callbacks after account switch. Stop on authorization denial, retain the pending partition for approved disposition, and avoid empty or speculative requests. A missing dependency or bad receipt blocks for reconciliation. |

Godot owns local journal orchestration and the QA scene. E3 remains the
measurement and scoring authority. The E4 storage and wire contracts own
record identity, receipts and authorization. PostgreSQL owns server-side
state transitions, and #195/#196 own the audit and retention requirements.
Portable golden vectors prove interoperability with the merged harness.
They do not make the Python harness a runtime dependency or require
byte-compatible on-disk journals across implementations.

Godot documents file flushing and the scene-tree threading boundary. Use
those APIs within their documented scope and test the complete commit and
recovery sequence. [FileAccess](https://docs.godotengine.org/en/stable/classes/class_fileaccess.html)
· [Thread-safe APIs](https://docs.godotengine.org/en/stable/tutorials/performance/thread_safe_apis.html)

## Acceptance for this slice

1. Headless Godot tests, registered in the existing runner, validate canonical
   command bytes against shared vectors and reject malformed, wrong-digest
   and incomplete receipts. Verify causal ordering, batch limits, no empty
   requests, and fake-clock batching, retries, restart cooldown and denial.
2. On the named host, kill a Godot child process before publication, after a
   segment is published, and after the acknowledgment checkpoint but before
   reclamation. Reopen the same isolated test root and check that committed
   records survive, unknown gaps block, and acknowledged records are never
   resent. Inject a disk-write failure and check that the UI never reports
   an unsaved response as saved.
3. Exercise the QA flow through an interactive Godot test build and record
   owner acceptance using a short test sheet. Verify the ordinary Godot
   suite still passes and the QA route is absent from the normal game launch.
4. Run the scoped Godot verifier and the repository gate as applicable. The
   existing PostgreSQL audit-count evidence remains backend evidence. A later
   loopback adapter slice should count actual database reads from a Godot
   client before making an end-to-end audit-capacity claim.

After this slice, add a loopback adapter test with PostgreSQL and then make
the storage durability and trusted visit bootstrap decisions for named
release platforms. Defer live authentication, production deployment,
multi-device reconciliation and real data collection to their existing gates.

## Running the implemented QA slice

From the repository root, set `GODOT_BIN` to the pinned executable and
choose a fresh writable temporary folder as `TET4D_E4_QA_ROOT`. Reuse that
folder when relaunching the scene so it can recover the same visit.

```sh
TET4D_GODOT_TEST_GROUP=e4_journal "$GODOT_BIN" --headless --log-file "$TET4D_E4_QA_ROOT/godot.log" --path godot/Tet4D.Godot --script tests/run_tests.gd
python godot/Tet4D.Godot/tests/e4_qa/process_recovery.py --godot "$GODOT_BIN"
"$GODOT_BIN" --log-file "$TET4D_E4_QA_ROOT/scene.log" --path godot/Tet4D.Godot res://tests/e4_qa/scene.tscn
```

Select **Present synthetic item**, enter `-3, 5, 1, 2`, and select **Save
answer offline**. Relaunch and confirm **Pending**. Select **Reconnect and
flush**. The fixture drops the first response. Allow at least five seconds
and select it again. The status should be **Synced** and remain so on the
next launch. A new sandbox directory starts a fresh fixture.

The one-slot QA journal uses bounded, checksummed whole-outbox generations
instead of per-command files. This keeps a pending pair and its
acknowledgment in one snapshot. A high-water marker detects lost committed
generations. Publication uses direct rename with a flushed staging file,
and refuses a failed rename instead of taking the generic backup path.
The worker is invoked by the test scene's buttons. Its retry gate is
persisted in UTC milliseconds and the test injects the clock. Continuous
coalescing, account switching and release filesystem guarantees remain
outside this one-account, manually flushed implementation. The process
probe covers host process termination. It does not establish power-loss
durability or interactive owner acceptance.
