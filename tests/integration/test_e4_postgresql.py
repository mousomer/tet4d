"""Synthetic integration against a disposable PostgreSQL database."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest

DSN = os.environ.get("TET4D_E4_TEST_DSN")
if not DSN:
    pytest.skip(
        "set TET4D_E4_TEST_DSN for disposable PostgreSQL", allow_module_level=True
    )

import psycopg

from tet4d.participant_data import lifecycle
from tet4d.participant_data.http import application
from tet4d.participant_data.ingestion import IngestError, ingest

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migration" / "participant_data" / "001_assessment.sql"
FIXTURE = ROOT / "tests" / "unit" / "research" / "fixtures" / "e4_storage_v1.json"


@pytest.fixture(scope="module", autouse=True)
def database():
    manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
    with psycopg.connect(DSN, autocommit=True) as connection:
        assert connection.execute(
            "SELECT to_regnamespace('assessment') IS NULL"
        ).fetchone()[0], "Use an empty disposable database"
        connection.execute(MIGRATION.read_text(encoding="utf-8"))
    with psycopg.connect(DSN) as connection:
        connection.execute("INSERT INTO assessment.protocol VALUES ('fixture@1', 60)")
        for item, scorer in manifest["items"].items():
            connection.execute(
                "INSERT INTO assessment.item VALUES (%s, %s, %s, sha256(%s::bytea), %s)",
                (item, scorer, "synthetic@1", item.encode(), item),
            )
        for form, items in manifest["forms"].items():
            connection.execute("INSERT INTO assessment.form VALUES (%s)", (form,))
            for ordinal, item in enumerate(items):
                connection.execute(
                    "INSERT INTO assessment.form_item VALUES (%s, %s, %s)",
                    (form, ordinal, item),
                )
        protocol = manifest["protocols"]["fixture@1"]
        for sequence, visits in protocol["sequences"].items():
            for phase, form in visits.items():
                connection.execute(
                    "INSERT INTO assessment.protocol_visit VALUES ('fixture@1', %s, %s, %s)",
                    (sequence, phase, form),
                )
        for arm in protocol["arms"]:
            connection.execute(
                "INSERT INTO assessment.protocol_arm VALUES ('fixture@1', %s)", (arm,)
            )


def _query(sql, *params):
    with psycopg.connect(DSN) as connection:
        return connection.execute(sql, params).fetchall()


def _slots(visit):
    return [
        slot
        for (slot,) in _query(
            "SELECT id FROM assessment.slot WHERE visit = %s ORDER BY ordinal", visit
        )
    ]


def _baseline(*, start=True):
    enrollment, principal = uuid4(), uuid4()
    now = datetime.now(UTC)
    window = (now - timedelta(hours=2), now - timedelta(hours=1))
    visit = lifecycle.assign_baseline(
        DSN, enrollment, principal, "fixture@1", "AB", window
    )
    if start:
        lifecycle.start_visit(DSN, enrollment, visit, "synthetic-build")
    return enrollment, principal, visit, _slots(visit)


def _submit(slot):
    return {
        "id": str(uuid4()),
        "kind": "submit",
        "slot": str(slot),
        "attempt": str(uuid4()),
        "response": [-3, 5, 1, 2],
        "latency_ms": 700,
        "observed_at": None,
    }


def _outcome(slot, status="invalid"):
    return {
        "id": str(uuid4()),
        "kind": "outcome",
        "slot": str(slot),
        "status": status,
        "observed_at": None,
    }


def _send(principal, enrollment, *commands):
    return ingest(
        DSN,
        principal,
        enrollment,
        json.dumps({"version": 1, "commands": commands}).encode(),
    )


def _windows():
    now = datetime.now(UTC)
    return {
        "posttest": (now - timedelta(minutes=15), now - timedelta(minutes=10)),
        "retention": (now - timedelta(seconds=30), now - timedelta(seconds=5)),
    }


def _complete_baseline(enrollment, principal, visit, slots):
    _send(principal, enrollment, _submit(slots[0]), _outcome(slots[1]))
    lifecycle.close_visit(DSN, enrollment, visit, "completed")


def test_replay_after_closure_and_revocation():
    enrollment, principal, visit, slots = _baseline()
    command = _submit(slots[0])
    receipt = _send(principal, enrollment, command)
    _send(principal, enrollment, _outcome(slots[1]))
    lifecycle.close_visit(DSN, enrollment, visit, "completed")
    assert (
        _send(principal, enrollment, dict(reversed(list(command.items())))) == receipt
    )
    with pytest.raises(IngestError, match="conflict"):
        _send(principal, enrollment, command | {"latency_ms": 900})
    lifecycle.revoke(DSN, enrollment)
    with pytest.raises(IngestError, match="authorization_failure"):
        _send(principal, enrollment, command)


def test_batch_rollback_including_attempt_written_before_outcome_failure():
    enrollment, principal, _, slots = _baseline()
    _send(principal, enrollment, _outcome(slots[1]))
    first, conflicts = map(_submit, slots)
    with pytest.raises(IngestError, match="conflict"):
        _send(principal, enrollment, first, conflicts)
    assert not _query("SELECT 1 FROM assessment.attempt WHERE slot = ANY(%s)", slots)
    assert not _query(
        "SELECT 1 FROM assessment.receipt WHERE enrollment = %s AND command = %s",
        enrollment,
        first["id"],
    )
    assert len(_send(principal, enrollment, first)) == 1


def test_enrollment_isolation_and_missing_dependency():
    enrollment, principal, _, slots = _baseline()
    foreign_enrollment, foreign_principal, _, foreign_slots = _baseline()
    with pytest.raises(IngestError, match="authorization_failure"):
        _send(foreign_principal, enrollment, _submit(slots[0]))
    with pytest.raises(IngestError, match="missing_dependency"):
        _send(principal, enrollment, _submit(foreign_slots[0]))
    exposure = {
        "id": str(uuid4()),
        "kind": "exposure",
        "activity": "none",
        "active_ms": 0,
        "examples": 0,
    }
    with pytest.raises(IngestError, match="missing_dependency"):
        _send(foreign_principal, foreign_enrollment, exposure)


def test_allocation_followups_expiry_and_reconciliation():
    enrollment, principal, visit, slots = _baseline()
    with pytest.raises(IngestError, match="ineligible_baseline"):
        lifecycle.allocate(
            DSN, enrollment, "rotation_4d", eligible=True, follow_up_windows=_windows()
        )
    _complete_baseline(enrollment, principal, visit, slots)
    windows = _windows()
    followups = lifecycle.allocate(
        DSN, enrollment, "rotation_4d", eligible=True, follow_up_windows=windows
    )
    retention = followups["retention"]
    with pytest.raises(IngestError, match="invalid_expiry"):
        lifecycle.close_visit(DSN, enrollment, retention, "expired")
    assert (
        _query("SELECT status FROM assessment.visit_close WHERE visit = %s", retention)
        == []
    )
    posttest = followups["posttest"]
    lifecycle.start_visit(DSN, enrollment, posttest, "synthetic-build")
    answered, abandoned = _slots(posttest)
    lifecycle.mark_slot_presented(DSN, enrollment, abandoned)
    during_window = windows["posttest"][0].isoformat().replace("+00:00", "Z")
    command = _submit(answered) | {"observed_at": during_window}
    receipt = _send(principal, enrollment, command)[0]
    assert receipt.received_at > windows["posttest"][1]
    lifecycle.close_visit(DSN, enrollment, posttest, "interrupted")
    assert _query(
        "SELECT status, timing FROM assessment.outcome WHERE slot = %s", answered
    ) == [("submitted", "in_window")]
    assert _query(
        "SELECT status FROM assessment.outcome WHERE slot = %s", abandoned
    ) == [("interrupted",)]
    assert (
        _query(
            "SELECT status FROM assessment.outcome WHERE slot = %s",
            _slots(retention)[0],
        )
        == []
    )


def test_expired_baseline_has_unpresented_slots_and_cannot_allocate():
    enrollment, _, visit, slots = _baseline(start=False)
    lifecycle.close_visit(DSN, enrollment, visit, "expired")
    assert _query(
        "SELECT status FROM assessment.outcome WHERE slot = ANY(%s)", slots
    ) == [("unpresented",), ("unpresented",)]
    with pytest.raises(IngestError, match="ineligible_baseline"):
        lifecycle.allocate(
            DSN, enrollment, "rotation_4d", eligible=True, follow_up_windows=_windows()
        )


def _race(first, second):
    barrier = Barrier(2)

    def run(operation):
        barrier.wait(timeout=10)
        try:
            return operation()
        except IngestError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, operation) for operation in (first, second)]
        return [future.result(timeout=15) for future in futures]


def test_duplicate_concurrent_submission_returns_one_durable_receipt():
    enrollment, principal, _, slots = _baseline()
    command = _submit(slots[0])

    def send():
        return _send(principal, enrollment, command)

    first, second = _race(send, send)
    assert first == second and isinstance(first, list)
    assert (
        len(_query("SELECT 1 FROM assessment.attempt WHERE slot = %s", slots[0])) == 1
    )


@pytest.mark.parametrize("race_with", ["close", "withdraw"])
def test_submit_races_with_finalization_under_same_lock(race_with):
    enrollment, principal, visit, slots = _baseline()
    command = _submit(slots[0])

    def finalize():
        if race_with == "close":
            lifecycle.close_visit(DSN, enrollment, visit, "interrupted")
        else:
            lifecycle.revoke(DSN, enrollment)

    submission, finalization = _race(
        lambda: _send(principal, enrollment, command), finalize
    )
    assert finalization is None
    written = _query("SELECT 1 FROM assessment.attempt WHERE slot = %s", slots[0])
    if isinstance(submission, list):
        assert written == [(1,)]
    else:
        assert submission == (
            "conflict" if race_with == "close" else "authorization_failure"
        )
        assert not written


def test_wire_rejects_duplicate_fields_and_unknown_version():
    enrollment, principal, _, _ = _baseline()
    with pytest.raises(IngestError, match="invalid_payload"):
        ingest(DSN, principal, enrollment, b'{"version":1,"version":1,"commands":[]}')
    with pytest.raises(IngestError, match="unsupported_version"):
        ingest(DSN, principal, enrollment, b'{"version":2,"commands":[]}')


def test_http_uses_only_middleware_identity_and_returns_committed_receipt():
    enrollment, principal, _, slots = _baseline()
    command = _submit(slots[0])
    payload = json.dumps({"version": 1, "commands": [command]}).encode()
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": f"/v1/assessment/enrollments/{enrollment}/commands",
        "CONTENT_LENGTH": str(len(payload)),
        "HTTP_TET4D_VERIFIED_PRINCIPAL": str(principal),
    }
    statuses = []
    app = application(DSN)

    def request():
        return json.loads(
            b"".join(
                app(
                    environ | {"wsgi.input": BytesIO(payload)},
                    lambda status, _headers: statuses.append(status),
                )
            )
        )

    assert request() == {"error": "authentication_required"}
    environ["tet4d.verified_principal"] = principal
    result = request()
    assert request() == result
    assert result["receipts"][0]["command"] == command["id"]
    assert statuses == ["401 Unauthorized", "200 OK", "200 OK"]


def test_read_only_role_cannot_write_assessment_tables():
    with psycopg.connect(DSN) as connection:
        connection.execute("SET LOCAL ROLE pg_read_all_data")
        with (
            pytest.raises(psycopg.errors.InsufficientPrivilege),
            connection.transaction(),
        ):
            connection.execute(
                "INSERT INTO assessment.protocol VALUES ('forbidden@1', 0)"
            )
