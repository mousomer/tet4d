"""Synthetic filesystem recovery and fake-clock E4 sync tests."""

import errno
import json
import signal
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

pytest.importorskip("psycopg")
pytest.importorskip("rfc8785")

from e4_harness import journal as storage
from e4_harness import sync as delivery
from e4_harness.edge import parse
from e4_harness.journal import Journal, JournalError
from e4_harness.sync import Reply, Sync


def _present(slot):
    return {
        "id": str(uuid4()),
        "kind": "present",
        "slot": str(slot),
        "observed_at": None,
    }


def _submit(slot):
    return {
        "id": str(uuid4()),
        "kind": "submit",
        "slot": str(slot),
        "attempt": str(uuid4()),
        "response": [1, -2, 0, 4],
        "latency_ms": 200,
        "observed_at": None,
    }


def _success(body):
    commands, digests = parse(body)
    return Reply(
        200,
        {
            "receipts": [
                {
                    "command": command["id"],
                    "digest": digest.hex(),
                    "received_at": "2026-11-20T15:00:00+00:00",
                }
                for command, digest in zip(commands, digests, strict=True)
            ]
        },
    )


class _Client:
    def __init__(self, root, slots):
        self.root = root
        self.account, self.enrollment = uuid4(), uuid4()
        self.milliseconds = 100_000
        self.calls = []
        self.slots = slots

    def open(self, respond=_success, *, cap=storage.HARD_BYTES):
        def send(enrollment, body):
            assert enrollment == self.enrollment
            self.calls.append(body)
            return respond(body)

        file = Journal(self.root, self.account, self.enrollment, cap=cap)
        client = Sync(
            file,
            lambda: self.milliseconds,
            send,
            slots=self.slots,
            jitter=lambda delay: delay,
        )
        client.bind(self.account)
        return client


def test_restart_ignores_unpublished_tail_and_reclaims_after_durable_ack(
    tmp_path, monkeypatch
):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    client = setup.open()
    present = _present(slot)
    client.capture(present)
    (client.journal.path / ".pending-crash").write_bytes(b"partial")
    client = setup.open()
    with monkeypatch.context() as patch:
        # Simulate interruption after advancing the durable checkpoint.
        patch.setattr(Journal, "_reclaim", lambda _journal: None)
        client.flush(early=True)
    assert len(list(client.journal.path.glob("*.record"))) == 1
    client = setup.open()
    assert client.status == "synced"
    assert not list(client.journal.path.glob("*.record"))
    client.capture(_submit(slot))
    setup.milliseconds += 5_000
    client.flush(early=True)
    assert len(setup.calls) == 2
    assert client.status == "synced"


def test_corrupt_committed_tail_blocks_delivery(tmp_path):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    client = setup.open()
    client.capture(_present(slot))
    client.capture(_submit(slot))
    last = max(client.journal.path.glob("*.record"))
    last.write_bytes(b"bad checksum")
    recovered = setup.open()
    recovered.flush(early=True)
    assert recovered.status == "blocked"
    assert last.read_bytes() == b"bad checksum"
    assert not setup.calls


def test_disk_full_or_capacity_does_not_report_saved(tmp_path, monkeypatch):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    client = setup.open(cap=1)
    with pytest.raises(JournalError, match="capacity"):
        client.capture(_present(slot))
    client = setup.open()

    def disk_full(*_args):
        raise OSError(errno.ENOSPC, "synthetic")

    with monkeypatch.context() as patch:
        patch.setattr(storage.os, "replace", disk_full)
        with pytest.raises(JournalError, match="did not complete"):
            client.capture(_present(slot))
    assert client.status == "blocked"
    assert setup.open().status == "synced"


def test_coalescing_limit_and_minimum_spacing(tmp_path):
    slots = [uuid4() for _ in range(65)]
    setup = _Client(tmp_path, slots)
    client = setup.open()
    client.capture(_present(slots[0]))
    client.flush()
    assert not setup.calls
    for slot in slots[1:]:
        client.capture(_present(slot))
    client.flush()
    client.flush(early=True)
    assert len(setup.calls) == 1
    assert len(parse(setup.calls[0])[0]) == 64
    setup.milliseconds += 5_000
    client.flush()
    assert len(parse(setup.calls[1])[0]) == 1
    assert client.status == "synced"


def test_retry_budget_and_retry_after_survive_restart(tmp_path):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    client = setup.open(lambda _body: Reply(429, {}, retry_after_ms=20_000))
    client.capture(_present(slot))
    client.flush(early=True)
    client = setup.open(lambda _body: Reply(503, {}))
    setup.milliseconds += 19_999
    client.flush(early=True)
    assert len(setup.calls) == 1
    setup.milliseconds += 1
    client.flush(early=True)
    for delay in (10_000, 20_000):
        setup.milliseconds += delay
        client.flush(early=True)
    assert len(setup.calls) == 4 and len(set(setup.calls)) == 1
    client = setup.open()
    client.flush(early=True)
    assert client.status == "paused"
    client.resume()
    client.flush(early=True)
    assert len(setup.calls) == 4
    setup.milliseconds += 40_000
    client.flush(early=True)
    assert client.status == "synced"


@pytest.mark.parametrize(
    "fault", ["wrong_digest", "wrong_id", "bad_time", "duplicate", "missing"]
)
def test_unverified_success_never_reclaims_batch(tmp_path, fault):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])

    def malformed(body):
        receipts = _success(body).body["receipts"]
        if fault == "wrong_digest":
            receipts[0]["digest"] = "0" * 64
        elif fault == "wrong_id":
            receipts[0]["command"] = str(uuid4())
        elif fault == "bad_time":
            receipts[0]["received_at"] = "2026-11-20T15:00:00"
        elif fault == "duplicate":
            receipts[1] = receipts[0]
        else:
            receipts.pop()
        return Reply(200, {"receipts": receipts})

    client = setup.open(malformed)
    client.capture(_present(slot))
    client.capture(_submit(slot))
    client.flush(early=True)
    client = setup.open()
    client.flush(early=True)
    assert client.status == "blocked"
    assert len(client.journal.records) == 2
    assert len(setup.calls) == 1


def test_account_switch_fences_inflight_ack_and_replays_original_batch(tmp_path):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    other = uuid4()

    def switch(body):
        client.bind(other)
        return _success(body)

    client = setup.open(switch)
    client.capture(_present(slot))
    client.flush(early=True)
    client.flush(early=True)
    assert client.status == "paused"
    assert len(client.journal.records) == 1 and len(setup.calls) == 1
    with pytest.raises(JournalError, match="account"):
        client.capture(_submit(slot))
    assert not Journal(tmp_path, other, setup.enrollment).records
    client = setup.open()
    client.capture(_submit(slot))
    setup.milliseconds += 5_000
    client.flush(early=True)
    assert setup.calls[0] == setup.calls[1]
    assert [
        json.loads(record.payload)["kind"] for record in client.journal.records
    ] == ["submit"]


def test_causal_validation_and_withdrawal(tmp_path):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    client = setup.open()
    with pytest.raises(JournalError, match="causal"):
        client.capture(_submit(slot))
    with pytest.raises(JournalError, match="manifest"):
        client.capture(_present(uuid4()))
    client.capture(_present(slot))
    client.confirm_withdrawal()
    client = setup.open()
    client.resume(access_verified=True)
    client.flush(early=True)
    with pytest.raises(JournalError, match="authorization"):
        client.capture(_submit(slot))
    assert client.status == "blocked"
    assert not setup.calls


def test_missing_committed_tail_blocks_delivery(tmp_path):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    client = setup.open()
    client.capture(_present(slot))
    next(client.journal.path.glob("*.record")).unlink()
    recovered = setup.open()
    recovered.flush(early=True)
    assert recovered.status == "blocked"
    assert not setup.calls


def test_recovers_segment_published_before_checkpoint(tmp_path, monkeypatch):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    client = setup.open()

    def interrupted(*_args):
        raise JournalError("synthetic checkpoint interruption")

    with monkeypatch.context() as patch:
        patch.setattr(client.journal, "save", interrupted)
        with pytest.raises(JournalError, match="interruption"):
            client.capture(_present(slot))
    recovered = setup.open()
    assert len(recovered.journal.records) == 1
    recovered.capture(_submit(slot))
    recovered.flush(early=True)
    assert recovered.status == "synced"


def test_unclean_process_exit_after_segment_before_checkpoint(tmp_path):
    slot = uuid4()
    setup = _Client(tmp_path, [slot])
    setup.open()
    command = _present(slot)
    script = """
import json
import os
import signal
import sys
from pathlib import Path
from uuid import UUID
from e4_harness.journal import Journal

root, account, enrollment, command = sys.argv[1:]
journal = Journal(Path(root), UUID(account), UUID(enrollment))
journal.save = lambda _: os.kill(os.getpid(), signal.SIGKILL)
journal.append(json.loads(command))
"""
    exited = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(tmp_path),
            str(setup.account),
            str(setup.enrollment),
            json.dumps(command),
        ],
        cwd=Path(__file__).parent,
        check=False,
        capture_output=True,
        timeout=10,
    )
    assert exited.returncode == -signal.SIGKILL, exited.stderr.decode()
    client = setup.open()
    client.capture(_submit(slot))
    client.flush(early=True)
    assert parse(setup.calls[0])[0][0]["id"] == command["id"]


def test_actual_request_byte_limit_splits_before_send(tmp_path, monkeypatch):
    slots = [uuid4(), uuid4()]
    setup = _Client(tmp_path, slots)
    client = setup.open()
    for slot in slots:
        client.capture(_present(slot))
    one_command = client.journal.records[0].payload
    limit = len(b'{"version":1,"commands":[' + one_command + b"]}")
    monkeypatch.setattr(delivery, "MAX_BYTES", limit)
    client.flush()
    setup.milliseconds += 5_000
    client.flush()
    assert len(setup.calls) == 2
    assert all(len(body) == limit for body in setup.calls)
