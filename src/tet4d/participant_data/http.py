"""WSGI endpoint for the local assessment service."""

import json
import re
from http import HTTPStatus
from uuid import UUID

from .ingestion import MAX_BYTES, IngestError, ingest

ROUTE = re.compile(r"/v1/assessment/enrollments/([0-9a-f-]{36})/commands")
ERROR_STATUS = {
    "authorization_failure": HTTPStatus.FORBIDDEN,
    "conflict": HTTPStatus.CONFLICT,
    "invalid_payload": HTTPStatus.BAD_REQUEST,
    "missing_dependency": HTTPStatus.CONFLICT,
    "transient_service_error": HTTPStatus.SERVICE_UNAVAILABLE,
    "unsupported_version": HTTPStatus.BAD_REQUEST,
}


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
    """Build a WSGI app behind middleware that supplies a verified UUID."""

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
