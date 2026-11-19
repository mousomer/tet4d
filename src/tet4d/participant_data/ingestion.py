"""Synchronous assessment ingestion for an already authenticated local caller."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import psycopg
import rfc8785
from psycopg.errors import IntegrityError, OperationalError

MAX_BYTES = 64 * 1024
MAX_COMMANDS = 64
INT_MAX = 2**31 - 1


class IngestError(Exception):
    """A stable error code suitable for the caller's retry policy."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Receipt:
    command: UUID
    digest: str
    received_at: datetime


def _object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise IngestError("invalid_payload")
    return result


def _uuid(value):
    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError):
        raise IngestError("invalid_payload") from None
    if str(parsed) != value:
        raise IngestError("invalid_payload")
    return parsed


def _integer(value, minimum=0):
    if type(value) is not int or not minimum <= value <= INT_MAX:
        raise IngestError("invalid_payload")


def _observed_at(value):
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise IngestError("invalid_payload") from None
    if not isinstance(value, str) or not value.endswith("Z") or parsed.tzinfo is None:
        raise IngestError("invalid_payload")
    return parsed


def _fields(record, expected):
    if not isinstance(record, dict) or record.keys() != expected:
        raise IngestError("invalid_payload")


def _submission(record):
    _fields(
        record,
        {"id", "kind", "slot", "attempt", "response", "latency_ms", "observed_at"},
    )
    _uuid(record["attempt"])
    _integer(record["latency_ms"])
    response = record["response"]
    if not isinstance(response, list) or len(response) != 4:
        raise IngestError("invalid_payload")
    for value in response:
        _integer(value, -(2**31))


def _other_outcome(record):
    _fields(record, {"id", "kind", "slot", "status", "observed_at"})
    if record["status"] not in ("invalid", "interrupted", "unpresented"):
        raise IngestError("invalid_payload")
    if record["status"] == "unpresented" and record["observed_at"] is not None:
        raise IngestError("invalid_payload")


def _exposure(record):
    _fields(record, {"id", "kind", "activity", "active_ms", "examples"})
    _integer(record["active_ms"])
    _integer(record["examples"])
    if record["activity"] not in ("rotation_3d", "rotation_4d", "none"):
        raise IngestError("invalid_payload")
    if record["activity"] == "none" and (record["active_ms"] or record["examples"]):
        raise IngestError("invalid_payload")


VALIDATORS = {
    "submit": _submission,
    "outcome": _other_outcome,
    "exposure": _exposure,
}


def _commands(payload):
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise IngestError("invalid_payload")
    try:
        batch = json.loads(payload.decode("utf-8"), object_pairs_hook=_object)
    except (UnicodeError, ValueError, RecursionError):
        raise IngestError("invalid_payload") from None
    _fields(batch, {"version", "commands"})
    if type(batch["version"]) is not int or batch["version"] != 1:
        raise IngestError("unsupported_version")
    commands = batch["commands"]
    if not isinstance(commands, list) or not 1 <= len(commands) <= MAX_COMMANDS:
        raise IngestError("invalid_payload")
    for record in commands:
        if not isinstance(record, dict):
            raise IngestError("invalid_payload")
        kind = record.get("kind")
        if not isinstance(kind, str) or kind not in VALIDATORS:
            raise IngestError("invalid_payload")
        VALIDATORS[kind](record)
        _uuid(record["id"])
        if kind != "exposure":
            _uuid(record["slot"])
            _observed_at(record["observed_at"])
    return commands


def lock_enrollment(connection, enrollment):
    return connection.execute(
        "SELECT id FROM assessment.enrollment WHERE id = %s FOR UPDATE",
        (enrollment,),
    ).fetchone()


def _authorize(connection, enrollment, principal):
    if lock_enrollment(connection, enrollment) is None:
        raise IngestError("authorization_failure")
    allowed = connection.execute(
        """SELECT 1 FROM assessment.enrollment_access
           WHERE enrollment = %s AND principal = %s AND revoked_at IS NULL""",
        (enrollment, principal),
    ).fetchone()
    if not allowed:
        raise IngestError("authorization_failure")


def _slot_window(connection, enrollment, slot):
    row = connection.execute(
        """SELECT v.opens_at, v.closes_at, v.started_at, c.visit, s.presented_at
           FROM assessment.slot s JOIN assessment.visit v ON v.id = s.visit
           LEFT JOIN assessment.visit_close c ON c.visit = v.id
           WHERE s.id = %s AND v.enrollment = %s""",
        (slot, enrollment),
    ).fetchone()
    if row is None:
        raise IngestError("missing_dependency")
    if row[3] is not None:
        raise IngestError("conflict")
    if row[2] is None:
        raise IngestError("missing_dependency")
    return row[0], row[1], row[4]


def _timing(observed, opens, closes):
    if observed is None:
        return "unknown"
    if observed < opens:
        return "before_window"
    if observed >= closes:
        return "after_window"
    return "in_window"


def _write_slot(connection, enrollment, command):
    slot = _uuid(command["slot"])
    opens, closes, presented = _slot_window(connection, enrollment, slot)
    attempt = None
    if command["kind"] == "submit":
        status = "submitted"
        attempt = _uuid(command["attempt"])
        connection.execute(
            """INSERT INTO assessment.attempt (id, slot, x, y, z, w, latency_ms)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (attempt, slot, *command["response"], command["latency_ms"]),
        )
    else:
        status = command["status"]
        if status == "unpresented" and presented is not None:
            raise IngestError("conflict")
    observed = _observed_at(command["observed_at"])
    connection.execute(
        """INSERT INTO assessment.outcome (slot, status, attempt, observed_at, timing)
           VALUES (%s, %s, %s, %s, %s)""",
        (slot, status, attempt, observed, _timing(observed, opens, closes)),
    )


def _write_exposure(connection, enrollment, command):
    allocated = connection.execute(
        "SELECT 1 FROM assessment.allocation WHERE enrollment = %s", (enrollment,)
    ).fetchone()
    if not allocated:
        raise IngestError("missing_dependency")
    connection.execute(
        """INSERT INTO assessment.exposure (enrollment, activity, active_ms, examples)
           VALUES (%s, %s, %s, %s)""",
        (enrollment, command["activity"], command["active_ms"], command["examples"]),
    )


def _ingest_command(connection, enrollment, command):
    command_id = _uuid(command["id"])
    digest = hashlib.sha256(rfc8785.dumps({"version": 1, "command": command})).digest()
    row = connection.execute(
        """SELECT digest, received_at FROM assessment.receipt
           WHERE enrollment = %s AND command = %s""",
        (enrollment, command_id),
    ).fetchone()
    if row is not None:
        if row[0] != digest:
            raise IngestError("conflict")
        return Receipt(command_id, digest.hex(), row[1])

    if command["kind"] == "exposure":
        _write_exposure(connection, enrollment, command)
    else:
        _write_slot(connection, enrollment, command)
    received_at = connection.execute(
        """INSERT INTO assessment.receipt (enrollment, command, digest)
           VALUES (%s, %s, %s) RETURNING received_at""",
        (enrollment, command_id, digest),
    ).fetchone()[0]
    return Receipt(command_id, digest.hex(), received_at)


def ingest(
    conninfo: str, principal: UUID, enrollment: UUID, payload: bytes
) -> list[Receipt]:
    """Apply one ordered batch, returning receipts after the database commit."""
    commands = _commands(payload)
    try:
        with psycopg.connect(conninfo) as connection:
            _authorize(connection, enrollment, principal)
            receipts = [
                _ingest_command(connection, enrollment, command) for command in commands
            ]
    except IntegrityError:
        raise IngestError("conflict") from None
    except OperationalError:
        raise IngestError("transient_service_error") from None
    return receipts
