"""Edge adapter: wire validation, digests and the error contract.

jsonb keeps only the last of duplicate keys and PostgreSQL has no RFC 8785
serializer, so both checks run here before `assessment_api.ingest`.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from uuid import UUID

import psycopg
import rfc8785
from psycopg.types.json import Jsonb

MAX_BYTES = 64 * 1024
MAX_COMMANDS = 64
INT_MIN = -(2**31)
INT_MAX = 2**31 - 1
OBSERVED_AT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")
ROUTE = re.compile(r"/v1/assessment/enrollments/([0-9a-f-]{36})/commands")

# Code -> HTTP status. The client action for each code is documented in
# docs/architecture/participant_data_platform.md.
ERROR_STATUS = {
    "invalid_payload": HTTPStatus.BAD_REQUEST,
    "unsupported_version": HTTPStatus.BAD_REQUEST,
    "authorization_failure": HTTPStatus.FORBIDDEN,
    "missing_dependency": HTTPStatus.UNPROCESSABLE_ENTITY,
    "conflict": HTTPStatus.CONFLICT,
    "visit_closed": HTTPStatus.CONFLICT,
    "transient_service_error": HTTPStatus.SERVICE_UNAVAILABLE,
}
# SQLSTATE classes that mean "retry the same command later".
TRANSIENT_CLASSES = ("08", "40", "53", "57")


class IngestError(Exception):
    """A stable error code from the E4 error contract."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Receipt:
    command: UUID
    digest: str
    received_at: datetime


def map_database_error(error):
    """Translate a psycopg error into the stable error contract."""
    state = error.sqlstate or ""
    if state.startswith("T4"):
        return IngestError(error.diag.message_primary)
    if isinstance(error, psycopg.OperationalError) or state[:2] in TRANSIENT_CLASSES:
        return IngestError("transient_service_error")
    return None


def connect(conninfo, role):
    connection = psycopg.connect(conninfo)
    connection.execute(f"SET ROLE {role}")
    return connection


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


def _integer(value, minimum=0):
    if type(value) is not int or not minimum <= value <= INT_MAX:
        raise IngestError("invalid_payload")


def _observed_at(value):
    if value is None:
        return
    if not isinstance(value, str) or not OBSERVED_AT.fullmatch(value):
        raise IngestError("invalid_payload")
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise IngestError("invalid_payload") from None


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
        _integer(value, INT_MIN)


def _other_outcome(record):
    _fields(record, {"id", "kind", "slot", "status", "observed_at"})
    if record["status"] not in ("invalid", "interrupted", "unpresented"):
        raise IngestError("invalid_payload")


def _exposure(record):
    _fields(record, {"id", "kind", "activity", "active_ms", "examples"})
    _integer(record["active_ms"])
    _integer(record["examples"])
    if not isinstance(record["activity"], str):
        raise IngestError("invalid_payload")


VALIDATORS = {"submit": _submission, "outcome": _other_outcome, "exposure": _exposure}


def parse(payload):
    """Validate the wire batch and return (commands, digests)."""
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
        kind = record.get("kind") if isinstance(record, dict) else None
        if not isinstance(kind, str) or kind not in VALIDATORS:
            raise IngestError("invalid_payload")
        VALIDATORS[kind](record)
        _uuid(record["id"])
        if kind != "exposure":
            _uuid(record["slot"])
            _observed_at(record["observed_at"])
    digests = [
        hashlib.sha256(rfc8785.dumps({"version": 1, "command": command})).digest()
        for command in commands
    ]
    return commands, digests


def ingest(conninfo, principal, enrollment, payload):
    """Apply one ordered batch as assessment_ingest; receipts follow commit."""
    commands, digests = parse(payload)
    try:
        with connect(conninfo, "assessment_ingest") as connection:
            rows = connection.execute(
                "SELECT command, digest, received_at FROM assessment_api.ingest(%s, %s, %s, %s)",
                (principal, enrollment, Jsonb(commands), digests),
            ).fetchall()
    except psycopg.Error as error:
        mapped = map_database_error(error)
        if mapped is None:
            raise
        raise mapped from None
    return [
        Receipt(command, digest.hex(), received_at)
        for command, digest, received_at in rows
    ]


def _read_payload(environ):
    length = environ.get("CONTENT_LENGTH", "")
    if not re.fullmatch(r"[0-9]{1,5}", length) or not 0 < int(length) <= MAX_BYTES:
        raise IngestError("invalid_payload")
    payload = environ["wsgi.input"].read(int(length))
    if len(payload) != int(length):
        raise IngestError("invalid_payload")
    return payload


def _handle(conninfo, environ):
    match = ROUTE.fullmatch(environ.get("PATH_INFO", ""))
    if match is None:
        return HTTPStatus.NOT_FOUND, {"error": "not_found"}
    try:
        enrollment = UUID(match[1])
    except ValueError:
        return HTTPStatus.NOT_FOUND, {"error": "not_found"}
    if environ.get("REQUEST_METHOD") != "POST":
        return HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method_not_allowed"}
    principal = environ.get("tet4d.verified_principal")
    if not isinstance(principal, UUID):
        return HTTPStatus.UNAUTHORIZED, {"error": "authentication_required"}
    try:
        receipts = ingest(conninfo, principal, enrollment, _read_payload(environ))
    except IngestError as error:
        return ERROR_STATUS[error.code], {"error": error.code}
    return HTTPStatus.OK, {
        "receipts": [
            {
                "command": str(receipt.command),
                "digest": receipt.digest,
                "received_at": receipt.received_at.isoformat(),
            }
            for receipt in receipts
        ]
    }


def application(conninfo):
    """WSGI app behind middleware that supplies a verified principal UUID."""

    def app(environ, start_response):
        status, data = _handle(conninfo, environ)
        body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ]
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            headers.append(("Allow", "POST"))
        start_response(f"{status.value} {status.phrase}", headers)
        return [body]

    return app
