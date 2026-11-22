"""Clock-driven synthetic E4 delivery against the existing ingest wire contract."""

import json
import random
from dataclasses import dataclass, replace
from datetime import datetime

from .edge import parse
from .journal import JournalError

MAX_BYTES = 64 * 1024
MAX_COMMANDS = 64
COALESCE_MS = 30_000
GATE_MS = 5_000
RETRY_LIMIT = 4
RETRY_CEILING_MS = 300_000
PREFIX = b'{"version":1,"commands":['
SUFFIX = b"]}"


@dataclass(frozen=True)
class Reply:
    status: int
    body: dict
    retry_after_ms: int = 0


def _batch(records):
    return PREFIX + b",".join(record.payload for record in records) + SUFFIX


def _receipt_time(value):
    try:
        return datetime.fromisoformat(value).utcoffset() is not None
    except (TypeError, ValueError):
        return False


def _receipts_match(reply, records):
    receipts = reply.body.get("receipts") if isinstance(reply.body, dict) else None
    if not isinstance(receipts, list) or len(receipts) != len(records):
        return False
    expected = {record.command_id: record.digest for record in records}
    for receipt in receipts:
        if not isinstance(receipt, dict):
            return False
        command = receipt.get("command")
        if not isinstance(command, str) or command not in expected:
            return False
        if receipt.get("digest") != expected.pop(command):
            return False
        if not _receipt_time(receipt.get("received_at")):
            return False
    return not expected


def _jitter(delay):
    return random.randint(delay * 3 // 4, min(RETRY_CEILING_MS, delay * 5 // 4))


class Sync:
    """One synchronous tick at a time, driven by a caller on its worker."""

    def __init__(self, journal, now, send, *, slots, allocated=False, jitter=_jitter):
        self.journal = journal
        self.now = now
        self.send = send
        self.jitter = jitter
        self.slots = frozenset(map(str, slots))
        self.allocated = allocated
        self.account = None
        self.generation = 0
        self.sending = False
        self.flush_at = now() + COALESCE_MS

    @property
    def status(self):
        if self.journal.fault:
            return "blocked"
        state = self.journal.checkpoint.state
        if state != "pending":
            return state
        if not self.journal.records:
            return "synced"
        return "pending" if self.account == self.journal.account else "paused"

    def bind(self, account):
        self.generation += 1
        self.account = account

    def capture(self, command):
        # Exercise exactly the server's version-one wire constraints.
        parse(json.dumps({"version": 1, "commands": [command]}).encode())
        if self.account != self.journal.account:
            raise JournalError("capture account mismatch")
        if self.journal.checkpoint.reason in {"authorization_failure", "withdrawn"}:
            raise JournalError("capture authorization is unresolved")
        self._require_causal(command)
        if not self.journal.records:
            self.flush_at = self.now() + COALESCE_MS
        self.journal.append(command)

    def _require_causal(self, command):
        slots, exposure = self.journal.causal_state(self.journal.records)
        if command["kind"] == "exposure":
            if not self.allocated or exposure:
                raise JournalError("exposure requires allocation and no prior summary")
            return
        slot = command["slot"]
        if slot not in self.slots:
            raise JournalError("slot is absent from the confirmed manifest")
        unpresented = command.get("status") == "unpresented"
        required = None if command["kind"] == "present" or unpresented else "presented"
        if slots.get(slot) != required:
            raise JournalError("slot command is out of causal order")

    def confirm_withdrawal(self):
        self.generation += 1
        self.journal.save(
            replace(self.journal.checkpoint, state="blocked", reason="withdrawn")
        )

    def resume(self, *, access_verified=False):
        if self.account != self.journal.account or self.journal.fault:
            return
        state = self.journal.checkpoint
        allowed = {"retry_budget"}
        if access_verified:
            allowed.update(("authentication_required", "authorization_failure"))
        if state.reason in allowed:
            self.journal.save(replace(state, state="pending", reason=None, attempts=0))

    def _select(self, state):
        records = []
        size = len(PREFIX) + len(SUFFIX)
        for record in self.journal.records:
            size += len(record.payload) + bool(records)
            if size > MAX_BYTES or len(records) == MAX_COMMANDS:
                return records, True
            records.append(record)
            if record.sequence == state.batch_end:
                return records, True
        return records, len(records) == MAX_COMMANDS or size == MAX_BYTES

    def flush(self, *, early=False):
        if self.sending or self.status != "pending":
            return
        now = self.now()
        state = self.journal.checkpoint
        if now < state.ready_at_ms:
            return
        if state.last_start_ms is not None and now < state.last_start_ms + GATE_MS:
            return
        if state.attempts >= RETRY_LIMIT:
            self.journal.save(replace(state, state="paused", reason="retry_budget"))
            return
        records, full = self._select(state)
        if not records or (not early and not full and now < self.flush_at):
            return
        state = replace(
            state,
            batch_end=records[-1].sequence,
            attempts=state.attempts + 1,
            last_start_ms=now,
            ready_at_ms=now + self._retry_delay(state.attempts + 1),
        )
        self.journal.save(state)
        generation = self.generation
        self.sending = True
        try:
            try:
                reply = self.send(self.journal.enrollment, _batch(records))
            except OSError:
                reply = Reply(503, {})
            if generation == self.generation:
                self._apply(reply, records, state)
        finally:
            self.sending = False

    def _apply(self, reply, records, state):
        if reply.status == 200 and _receipts_match(reply, records):
            self.journal.acknowledge(records[-1].sequence)
            self.flush_at = self.now()
            return
        if reply.status in {429, 503}:
            self._defer(reply, state)
            return
        reason = {
            200: "malformed_receipts",
            401: "authentication_required",
            403: "authorization_failure",
        }.get(reply.status)
        if reason is None and isinstance(reply.body, dict):
            reason = reply.body.get("error")
        paused = reply.status in {401, 403}
        self.journal.save(
            replace(
                state,
                state="paused" if paused else "blocked",
                reason=reason if isinstance(reason, str) else "unrecognized_response",
            )
        )

    def _retry_delay(self, attempts):
        delay = min(RETRY_CEILING_MS, GATE_MS * 2 ** (attempts - 1))
        return max(GATE_MS, min(RETRY_CEILING_MS, self.jitter(delay)))

    def _defer(self, reply, state):
        delay = max(state.ready_at_ms - state.last_start_ms, reply.retry_after_ms)
        exhausted = state.attempts >= RETRY_LIMIT
        self.journal.save(
            replace(
                state,
                ready_at_ms=self.now() + delay,
                state="paused" if exhausted else "pending",
                reason="retry_budget" if exhausted else None,
            )
        )
