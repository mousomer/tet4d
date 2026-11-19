"""Synthetic integration against a disposable PostgreSQL database.

Every call goes through the `assessment_api` functions as the role a real
caller would hold (assessment_ingest or assessment_operator), so the grants
are exercised, not bypassed by the owner.

CI sets TET4D_E4_REQUIRE_POSTGRES=1 next to the DSN, so a missing database
fails the run instead of silently skipping it.
"""

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
    if os.environ.get("TET4D_E4_REQUIRE_POSTGRES") == "1":
        pytest.fail(
            "TET4D_E4_REQUIRE_POSTGRES=1 but TET4D_E4_TEST_DSN is not set",
            pytrace=False,
        )
    pytest.skip(
        "set TET4D_E4_TEST_DSN for disposable PostgreSQL", allow_module_level=True
    )

import psycopg
from e4_harness import operations
from e4_harness.edge import IngestError, application, connect, ingest
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migration" / "participant_data" / "001_assessment.sql"
FIXTURE = ROOT / "tests" / "unit" / "research" / "fixtures" / "e4_storage_v1.json"
PROTOCOL = "fixture@2"
GRACE_SECONDS = 60


@pytest.fixture(scope="module", autouse=True)
def database():
    manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
    with psycopg.connect(DSN, autocommit=True) as connection:
        assert connection.execute(
            "SELECT to_regnamespace('assessment') IS NULL"
        ).fetchone()[0], "Use an empty disposable database"
        connection.execute(MIGRATION.read_text(encoding="utf-8"))
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "INSERT INTO assessment.protocol VALUES (%s, %s)", (PROTOCOL, GRACE_SECONDS)
        )
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
        protocol = manifest["protocols"][PROTOCOL]
        for sequence, visits in protocol["sequences"].items():
            for phase, form in visits.items():
                connection.execute(
                    "INSERT INTO assessment.protocol_visit VALUES (%s, %s, %s, %s)",
                    (PROTOCOL, sequence, phase, form),
                )
        for arm in protocol["arms"]:
            connection.execute(
                "INSERT INTO assessment.protocol_arm VALUES (%s, %s)", (PROTOCOL, arm)
            )
        for activity in protocol["activities"]:
            connection.execute(
                "INSERT INTO assessment.protocol_activity VALUES (%s, %s)",
                (PROTOCOL, activity),
            )


def _query(sql, *params, role=None):
    with psycopg.connect(DSN) as connection:
        if role:
            connection.execute(f"SET ROLE {role}")
        return connection.execute(sql, params).fetchall()


def _slots(visit):
    return [
        slot
        for (slot,) in _query(
            "SELECT id FROM assessment.slot WHERE visit = %s ORDER BY ordinal", visit
        )
    ]


def _utc(moment):
    """Canonical wire form: millisecond precision, Z suffix."""
    moment = moment.astimezone(UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def _past_window():
    now = datetime.now(UTC)
    return now - timedelta(hours=2), now - timedelta(hours=1)


def _baseline(*, start=True, window=None):
    enrollment, principal = uuid4(), uuid4()
    visit = operations.assign_baseline(
        DSN, enrollment, principal, PROTOCOL, "AB", window or _past_window()
    )
    if start:
        operations.start_visit(DSN, enrollment, visit, "synthetic-build")
    return enrollment, principal, visit, _slots(visit)


def _present(slot, observed_at=None):
    return {
        "id": str(uuid4()),
        "kind": "present",
        "slot": str(slot),
        "observed_at": observed_at,
    }


def _submit(slot, observed_at=None):
    return {
        "id": str(uuid4()),
        "kind": "submit",
        "slot": str(slot),
        "attempt": str(uuid4()),
        "response": [-3, 5, 1, 2],
        "latency_ms": 700,
        "observed_at": observed_at,
    }


def _outcome(slot, status="invalid"):
    return {
        "id": str(uuid4()),
        "kind": "outcome",
        "slot": str(slot),
        "status": status,
        "observed_at": None,
    }


def _exposure(activity="none", active_ms=0, examples=0):
    return {
        "id": str(uuid4()),
        "kind": "exposure",
        "activity": activity,
        "active_ms": active_ms,
        "examples": examples,
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
    first, second = slots
    _send(
        principal,
        enrollment,
        _present(first),
        _submit(first),
        _present(second),
        _outcome(second),
    )
    operations.close_visit(DSN, enrollment, visit, "completed")


def _allocated():
    enrollment, principal, visit, slots = _baseline()
    _complete_baseline(enrollment, principal, visit, slots)
    followups = operations.allocate(
        DSN, enrollment, "rotation_4d", eligible=True, follow_up_windows=_windows()
    )
    return enrollment, principal, followups


def _outcomes(slots):
    return [
        status
        for (status,) in _query(
            "SELECT o.status FROM assessment.outcome o JOIN assessment.slot s ON s.id = o.slot"
            " WHERE o.slot = ANY(%s) ORDER BY s.ordinal",
            slots,
        )
    ]


def _closure(visit):
    return _query("SELECT status FROM assessment.visit_close WHERE visit = %s", visit)


def _audit(enrollment):
    return _query(
        "SELECT action, command FROM assessment_private.access_audit"
        " WHERE enrollment = %s ORDER BY id",
        enrollment,
    )


# Behaviour carried over from the original slice -------------------------------


def test_replay_after_closure_and_withdrawal():
    enrollment, principal, visit, slots = _baseline()
    _send(principal, enrollment, _present(slots[0]), _present(slots[1]))
    command = _submit(slots[0])
    receipt = _send(principal, enrollment, command)
    _send(principal, enrollment, _outcome(slots[1]))
    operations.close_visit(DSN, enrollment, visit, "completed")
    assert (
        _send(principal, enrollment, dict(reversed(list(command.items())))) == receipt
    )
    with pytest.raises(IngestError, match="conflict"):
        _send(principal, enrollment, command | {"latency_ms": 900})
    operations.withdraw(DSN, enrollment)
    with pytest.raises(IngestError, match="authorization_failure"):
        _send(principal, enrollment, command)


def test_batch_rollback_including_attempt_written_before_outcome_failure():
    enrollment, principal, _, slots = _baseline()
    _send(principal, enrollment, _present(slots[1]), _outcome(slots[1]))
    shown = _present(slots[0])
    first, conflicts = map(_submit, slots)
    with pytest.raises(IngestError, match="conflict"):
        _send(principal, enrollment, shown, first, conflicts)
    assert not _query("SELECT 1 FROM assessment.attempt WHERE slot = ANY(%s)", slots)
    assert not _query("SELECT 1 FROM assessment.presentation WHERE slot = %s", slots[0])
    assert not _query(
        "SELECT 1 FROM assessment.receipt WHERE enrollment = %s AND command = ANY(%s)",
        enrollment,
        [shown["id"], first["id"]],
    )
    assert len(_send(principal, enrollment, shown, first)) == 2


def test_enrollment_isolation_and_missing_dependency():
    enrollment, principal, _, slots = _baseline()
    foreign_enrollment, foreign_principal, _, foreign_slots = _baseline()
    with pytest.raises(IngestError, match="authorization_failure"):
        _send(foreign_principal, enrollment, _present(slots[0]))
    with pytest.raises(IngestError, match="missing_dependency"):
        _send(principal, enrollment, _present(foreign_slots[0]))
    with pytest.raises(IngestError, match="missing_dependency"):
        _send(foreign_principal, foreign_enrollment, _exposure())


def test_allocation_followups_expiry_and_reconciliation():
    enrollment, principal, visit, slots = _baseline()
    with pytest.raises(IngestError, match="ineligible_baseline"):
        operations.allocate(
            DSN, enrollment, "rotation_4d", eligible=True, follow_up_windows=_windows()
        )
    _complete_baseline(enrollment, principal, visit, slots)
    windows = _windows()
    followups = operations.allocate(
        DSN, enrollment, "rotation_4d", eligible=True, follow_up_windows=windows
    )
    retention = followups["retention"]
    with pytest.raises(IngestError, match="invalid_expiry"):
        operations.close_visit(DSN, enrollment, retention, "expired")
    assert _closure(retention) == []
    posttest = followups["posttest"]
    operations.start_visit(DSN, enrollment, posttest, "synthetic-build")
    answered, abandoned = _slots(posttest)
    opens, closes = windows["posttest"]
    during = _utc(opens + (closes - opens) / 2)
    receipts = _send(
        principal,
        enrollment,
        _present(abandoned, during),
        _present(answered, during),
        _submit(answered, during),
    )
    assert all(receipt.received_at > closes for receipt in receipts)
    operations.close_visit(DSN, enrollment, posttest, "interrupted")
    assert _query(
        "SELECT status, timing FROM assessment.outcome WHERE slot = %s", answered
    ) == [("submitted", "in_window")]
    assert _query(
        "SELECT timing FROM assessment.presentation WHERE slot = %s", answered
    ) == [("in_window",)]
    assert _outcomes([abandoned]) == ["interrupted"]
    assert _outcomes(_slots(retention)) == []


def test_expired_baseline_has_unpresented_slots_and_cannot_allocate():
    enrollment, _, visit, slots = _baseline(start=False)
    operations.close_visit(DSN, enrollment, visit, "expired")
    assert _outcomes(slots) == ["unpresented", "unpresented"]
    with pytest.raises(IngestError, match="ineligible_baseline"):
        operations.allocate(
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
    _send(principal, enrollment, _present(slots[0]))
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
    _send(principal, enrollment, _present(slots[0]))
    command = _submit(slots[0])

    def finalize():
        if race_with == "close":
            operations.close_visit(DSN, enrollment, visit, "interrupted")
        else:
            operations.withdraw(DSN, enrollment)

    submission, finalization = _race(
        lambda: _send(principal, enrollment, command), finalize
    )
    assert finalization is None
    written = _query("SELECT 1 FROM assessment.attempt WHERE slot = %s", slots[0])
    if isinstance(submission, list):
        assert written == [(1,)]
    else:
        assert submission == (
            "visit_closed" if race_with == "close" else "authorization_failure"
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
    command = _present(slots[0])
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


# Roles and grants -----------------------------------------------------------------


def test_callers_can_only_use_their_granted_functions():
    with psycopg.connect(DSN) as connection:
        for role, statement in [
            (
                "research_reader",
                "INSERT INTO assessment.protocol VALUES ('forbidden@1', 0)",
            ),
            ("assessment_ingest", "SELECT 1 FROM assessment.enrollment"),
            ("assessment_operator", "SELECT 1 FROM assessment.enrollment"),
            ("assessment_ingest", "SELECT assessment_api.withdraw(gen_random_uuid())"),
            ("research_reader", "SELECT assessment_api.withdraw(gen_random_uuid())"),
        ]:
            with (
                pytest.raises(psycopg.errors.InsufficientPrivilege),
                connection.transaction(),
            ):
                connection.execute(f"SET LOCAL ROLE {role}")
                connection.execute(statement)


def test_sql_functions_validate_commands_without_the_adapter():
    enrollment, principal, _, slots = _baseline()
    _send(principal, enrollment, _present(slots[0]))
    command = _submit(slots[0]) | {"response": [1, 2, 3, 4.5]}
    with connect(DSN, "assessment_ingest") as connection:
        rows = connection.execute(
            "SELECT error FROM assessment_api.ingest(%s, %s, %s, %s)",
            (principal, enrollment, Jsonb([command]), [bytes(32)]),
        ).fetchall()
    assert rows == [("invalid_payload",)]
    assert not _query("SELECT 1 FROM assessment.attempt WHERE slot = %s", slots[0])


# Presentation provenance (review of #194, P1) ------------------------------------


def test_answers_require_a_presentation_record():
    enrollment, principal, _, (first, second) = _baseline()
    for command in (_submit(first), _outcome(first), _outcome(first, "interrupted")):
        with pytest.raises(IngestError, match="missing_dependency"):
            _send(principal, enrollment, command)
    observed = _utc(datetime.now(UTC) - timedelta(minutes=90))
    _send(principal, enrollment, _present(first, observed), _submit(first))
    assert _query(
        "SELECT p.timing, o.status, o.presentation = p.slot"
        " FROM assessment.presentation p JOIN assessment.outcome o ON o.slot = p.slot"
        " WHERE p.slot = %s",
        first,
    ) == [("in_window", "submitted", True)]
    with (
        psycopg.connect(DSN) as connection,
        pytest.raises(psycopg.errors.CheckViolation),
    ):
        connection.execute(
            "INSERT INTO assessment.outcome (slot, status, timing)"
            " VALUES (%s, 'invalid', 'unknown')",
            (second,),
        )


def test_presentation_and_unpresented_outcome_are_exclusive():
    enrollment, principal, _, (first, second) = _baseline()
    _send(principal, enrollment, _outcome(first, "unpresented"))
    with pytest.raises(IngestError, match="conflict"):
        _send(principal, enrollment, _present(first))
    _send(principal, enrollment, _present(second))
    with pytest.raises(IngestError, match="conflict"):
        _send(principal, enrollment, _outcome(second, "unpresented"))
    with pytest.raises(IngestError, match="conflict"):
        _send(principal, enrollment, _present(second))
    assert _query(
        "SELECT count(*) FROM assessment.presentation p"
        " JOIN assessment.outcome o ON o.slot = p.slot WHERE o.status = 'unpresented'"
    ) == [(0,)]


# Account link stays out of the research schema; its reads are audited -----------


def test_research_reader_cannot_reach_the_account_link():
    assert (
        _query(
            "SELECT table_name FROM information_schema.columns"
            " WHERE table_schema = 'assessment' AND column_name = 'principal'"
        )
        == []
    )
    for table in ("enrollment_access", "access_audit"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            _query(f"SELECT 1 FROM assessment_private.{table}", role="research_reader")
    enrollment, *_ = _baseline(start=False)
    assert _query(
        "SELECT count(*) FROM assessment.enrollment WHERE id = %s",
        enrollment,
        role="research_reader",
    ) == [(1,)]


def test_account_link_reads_and_conflicts_are_audited():
    enrollment, principal, _, slots = _baseline()
    command = _present(slots[0])
    _send(principal, enrollment, command)
    with pytest.raises(IngestError, match="authorization_failure"):
        _send(uuid4(), enrollment, _present(slots[1]))
    with pytest.raises(IngestError, match="conflict"):
        _send(
            principal, enrollment, command | {"observed_at": "2026-11-19T10:00:00.000Z"}
        )
    actions = _audit(enrollment)
    assert [action for action, _ in actions] == [
        "grant",
        "read_allow",
        "read_deny",
        "read_allow",
        "conflict",
    ]
    assert str(actions[-1][1]) == command["id"]


# Withdrawal -------------------------------------------------------------------------


def test_withdrawal_closes_open_visits_and_keeps_attrition_reconstructible():
    enrollment, principal, followups = _allocated()
    posttest = followups["posttest"]
    operations.start_visit(DSN, enrollment, posttest, "synthetic-build")
    shown, unseen = _slots(posttest)
    _send(principal, enrollment, _present(shown))
    operations.withdraw(DSN, enrollment)
    operations.withdraw(DSN, enrollment)

    assert _outcomes([shown, unseen]) == ["interrupted", "unpresented"]
    assert _outcomes(_slots(followups["retention"])) == ["unpresented"]
    attrition = _query(
        "SELECT a.arm, v.phase, c.status, w.enrollment IS NOT NULL"
        " FROM assessment.allocation a"
        " JOIN assessment.visit v ON v.enrollment = a.enrollment"
        " JOIN assessment.visit_close c ON c.visit = v.id"
        " LEFT JOIN assessment.withdrawal w ON w.enrollment = a.enrollment"
        " WHERE a.enrollment = %s ORDER BY v.opens_at",
        enrollment,
        role="research_reader",
    )
    assert attrition == [
        ("rotation_4d", "baseline", "completed", True),
        ("rotation_4d", "posttest", "withdrawn", True),
        ("rotation_4d", "retention", "withdrawn", True),
    ]
    with pytest.raises(IngestError, match="authorization_failure"):
        _send(principal, enrollment, _exposure())
    with pytest.raises(IngestError, match="authorization_failure"):
        operations.start_visit(DSN, enrollment, posttest, "synthetic-build")
    with pytest.raises(IngestError, match="invalid_status"):
        operations.close_visit(DSN, enrollment, posttest, "withdrawn")
    assert [action for action, _ in _audit(enrollment)] == [
        "grant",
        "read_allow",
        "read_allow",
        "revoke",
        "read_deny",
    ]


# Offline grace and late delivery ------------------------------------------------------


def test_interrupted_close_waits_for_grace_and_keeps_late_deliveries():
    now = datetime.now(UTC)
    enrollment, principal, visit, slots = _baseline(
        window=(now - timedelta(minutes=10), now - timedelta(seconds=1))
    )
    first, second = slots
    _send(principal, enrollment, _present(first), _submit(first))
    with pytest.raises(IngestError, match="reconciliation_pending"):
        operations.close_visit(DSN, enrollment, visit, "interrupted")

    late = _utc(datetime.now(UTC))
    _send(principal, enrollment, _present(second, late), _submit(second, late))
    assert _query("SELECT timing FROM assessment.outcome WHERE slot = %s", second) == [
        ("after_window",)
    ]
    operations.close_visit(DSN, enrollment, visit, "interrupted")
    assert _outcomes(slots) == ["submitted", "submitted"]
    with pytest.raises(IngestError, match="visit_closed"):
        _send(principal, enrollment, _outcome(second))


# Stable error codes from trusted operations -----------------------------------------


def test_double_allocation_is_a_stable_conflict():
    enrollment, _, _ = _allocated()
    with pytest.raises(IngestError, match="conflict"):
        operations.allocate(
            DSN, enrollment, "rotation_4d", eligible=True, follow_up_windows=_windows()
        )


# Minor items -----------------------------------------------------------------------


def test_started_visit_with_nothing_presented_can_expire():
    enrollment, _, visit, slots = _baseline()
    operations.close_visit(DSN, enrollment, visit, "expired")
    assert _closure(visit) == [("expired",)]
    assert _outcomes(slots) == ["unpresented", "unpresented"]


def test_observed_at_must_use_the_canonical_form():
    enrollment, principal, _, (first, _) = _baseline()
    for variant in (
        "2026-11-19T10:00:00Z",
        "2026-11-19T10:00:00.0Z",
        "2026-11-19T10:00:00.000+00:00",
    ):
        with pytest.raises(IngestError, match="invalid_payload"):
            _send(principal, enrollment, _present(first, variant))
    command = _present(first, "2026-11-19T10:00:00.000Z")
    assert _send(principal, enrollment, command) == _send(
        principal, enrollment, command
    )


def test_exposure_activity_must_belong_to_the_protocol():
    enrollment, principal, _ = _allocated()
    with pytest.raises(IngestError, match="invalid_payload"):
        _send(principal, enrollment, _exposure("rotation_5d", 10, 1))
    with pytest.raises(IngestError, match="invalid_payload"):
        _send(principal, enrollment, _exposure("none", 10, 0))
    assert len(_send(principal, enrollment, _exposure("rotation_3d", 9000, 2))) == 1
