"""Durable, single-writer file outbox for the synthetic E4 client."""

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from uuid import UUID

import rfc8785

WARNING_BYTES = 1024 * 1024
HARD_BYTES = 4 * WARNING_BYTES
INITIAL_STATE = "pending"


class JournalError(Exception):
    """The outbox cannot safely accept or deliver records."""


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _publish(path, data):
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=".pending-", delete=False
    ) as file:
        temporary = Path(file.name)
        try:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
            os.replace(temporary, path)
            _sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)


def _pack(value):
    body = rfc8785.dumps(value)
    return _digest(body).encode() + b"\n" + body


def _unpack(data):
    mark, separator, body = data.partition(b"\n")
    if not separator or mark != _digest(body).encode():
        raise JournalError("invalid journal checksum")
    return json.loads(body)


@dataclass(frozen=True)
class Checkpoint:
    acknowledged: int = 0
    last_sequence: int = 0
    batch_end: int = 0
    attempts: int = 0
    ready_at_ms: int = 0
    last_start_ms: int | None = None
    state: str = INITIAL_STATE
    reason: str | None = None
    slots: dict = field(default_factory=dict)
    exposure: bool = False


@dataclass(frozen=True)
class Record:
    sequence: int
    command_id: str
    payload: bytes
    size: int

    @property
    def digest(self):
        return _digest(b'{"command":' + self.payload + b',"version":1}')


class Journal:
    """Filesystem owner for one synthetic account and enrollment partition."""

    def __init__(self, root: Path, account: UUID, enrollment: UUID, *, cap=HARD_BYTES):
        self.account = account
        self.enrollment = enrollment
        self.path = root / str(account) / str(enrollment)
        self.path.mkdir(parents=True, exist_ok=True)
        for directory in (self.path.parent, root, root.parent):
            _sync_directory(directory)
        self.cap = cap
        self.checkpoint = Checkpoint()
        self.records = []
        self.fault = False
        self.obsolete = []
        try:
            self._recover()
        except (JournalError, OSError, ValueError, TypeError, KeyError, OverflowError):
            self.fault = True

    def _recover(self):
        checkpoint = self.path / "checkpoint"
        if checkpoint.exists():
            packet = _unpack(checkpoint.read_bytes())
            if packet.pop("version") != 1:
                raise JournalError("unsupported checkpoint")
            self.checkpoint = Checkpoint(**packet)
        for path in sorted(self.path.glob("*.record")):
            sequence = int(path.stem)
            if sequence <= self.checkpoint.acknowledged:
                self.obsolete.append(path)
                continue
            if sequence != self.checkpoint.acknowledged + len(self.records) + 1:
                raise JournalError("journal sequence gap")
            data = path.read_bytes()
            packet = _unpack(data)
            if packet["version"] != 1 or packet["sequence"] != sequence:
                raise JournalError("invalid record identity")
            payload = packet["payload"].encode()
            command_id = json.loads(payload)["id"]
            self.records.append(Record(sequence, command_id, payload, len(data)))
        recovered_end = self.checkpoint.acknowledged + len(self.records)
        if (
            max(self.checkpoint.batch_end, self.checkpoint.last_sequence)
            > recovered_end
        ):
            raise JournalError("committed journal tail is incomplete")
        if not checkpoint.exists() or self.checkpoint.last_sequence != recovered_end:
            self.save(replace(self.checkpoint, last_sequence=recovered_end))
        self.obsolete.extend(self.path.glob(".pending-*"))
        self._reclaim()

    @property
    def queued_bytes(self):
        return sum(record.size for record in self.records)

    @property
    def capacity_warning(self):
        return self.queued_bytes >= WARNING_BYTES

    def append(self, command):
        self._require_healthy()
        command_id = command["id"]
        if str(UUID(command_id)) != command_id:
            raise JournalError("invalid command identity")
        if any(record.command_id == command_id for record in self.records):
            raise JournalError("command already queued")
        payload = rfc8785.dumps(command)
        sequence = self.checkpoint.acknowledged + len(self.records) + 1
        data = _pack({"version": 1, "sequence": sequence, "payload": payload.decode()})
        if self.queued_bytes + len(data) > self.cap:
            raise JournalError("journal capacity reached")
        self._write(self.path / f"{sequence:020}.record", data)
        self.save(replace(self.checkpoint, last_sequence=sequence))
        self.records.append(Record(sequence, command_id, payload, len(data)))

    def _require_healthy(self):
        if self.fault:
            raise JournalError("journal requires recovery")

    def _write(self, path, data):
        try:
            _publish(path, data)
        except OSError as error:
            self.fault = True
            raise JournalError("journal write did not complete") from error

    def save(self, checkpoint):
        self._require_healthy()
        self._write(
            self.path / "checkpoint", _pack({"version": 1, **asdict(checkpoint)})
        )
        self.checkpoint = checkpoint

    def causal_state(self, records):
        slots = dict(self.checkpoint.slots)
        exposure = self.checkpoint.exposure
        for record in records:
            command = json.loads(record.payload)
            if command["kind"] == "exposure":
                exposure = True
            else:
                slots[command["slot"]] = (
                    "presented" if command["kind"] == "present" else "resolved"
                )
        return slots, exposure

    def acknowledge(self, sequence):
        slots, exposure = self.causal_state(
            record for record in self.records if record.sequence <= sequence
        )
        self.save(
            replace(
                self.checkpoint,
                acknowledged=sequence,
                slots=slots,
                exposure=exposure,
                batch_end=0,
                attempts=0,
                ready_at_ms=0,
                state=INITIAL_STATE,
                reason=None,
            )
        )
        self.obsolete.extend(
            self.path / f"{record.sequence:020}.record"
            for record in self.records
            if record.sequence <= sequence
        )
        self.records = [record for record in self.records if record.sequence > sequence]
        self._reclaim()

    def _reclaim(self):
        # A durable checkpoint makes leftovers safe to remove on the next open.
        for path in self.obsolete[:]:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                continue
            self.obsolete.remove(path)
