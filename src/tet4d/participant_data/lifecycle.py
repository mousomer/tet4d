"""Trusted study operations for the local assessment service."""

from uuid import uuid4

import psycopg

from .ingestion import IngestError, lock_enrollment


def _require_enrollment(connection, enrollment):
    if lock_enrollment(connection, enrollment) is None:
        raise IngestError("missing_dependency")
    allowed = connection.execute(
        """SELECT 1 FROM assessment.enrollment_access
           WHERE enrollment = %s AND revoked_at IS NULL""",
        (enrollment,),
    ).fetchone()
    if not allowed:
        raise IngestError("authorization_failure")


def _create_visit(connection, enrollment, phase, window):
    visit = uuid4()
    row = connection.execute(
        """INSERT INTO assessment.visit
           (id, enrollment, protocol, sequence, phase, form, opens_at, closes_at)
           SELECT %s, e.id, e.protocol, e.sequence, p.phase, p.form, %s, %s
           FROM assessment.enrollment e JOIN assessment.protocol_visit p
             ON (p.protocol, p.sequence) = (e.protocol, e.sequence)
           WHERE e.id = %s AND p.phase = %s RETURNING form""",
        (visit, *window, enrollment, phase),
    ).fetchone()
    if row is None:
        raise IngestError("missing_dependency")
    form = row[0]
    items = connection.execute(
        """SELECT f.ordinal, f.item, i.scorer FROM assessment.form_item f
           JOIN assessment.item i ON i.ref = f.item WHERE f.form = %s ORDER BY f.ordinal""",
        (form,),
    ).fetchall()
    if not items or [item[0] for item in items] != list(range(len(items))):
        raise IngestError("invalid_manifest")
    with connection.cursor() as cursor:
        cursor.executemany(
            """INSERT INTO assessment.slot (id, visit, form, ordinal, item, scorer)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            [(uuid4(), visit, form, *item) for item in items],
        )
    return visit


def assign_baseline(conninfo, enrollment, principal, protocol, sequence, window):
    with psycopg.connect(conninfo) as connection:
        connection.execute(
            "INSERT INTO assessment.enrollment VALUES (%s, %s, %s)",
            (enrollment, protocol, sequence),
        )
        connection.execute(
            "INSERT INTO assessment.enrollment_access (enrollment, principal) VALUES (%s, %s)",
            (enrollment, principal),
        )
        return _create_visit(connection, enrollment, "baseline", window)


def allocate(conninfo, enrollment, arm, *, eligible, follow_up_windows):
    """Persist the trusted allocator's result and all planned follow-up slots."""
    with psycopg.connect(conninfo) as connection:
        _require_enrollment(connection, enrollment)
        baseline = connection.execute(
            """SELECT v.protocol FROM assessment.visit v
               JOIN assessment.visit_close c ON c.visit = v.id
               WHERE v.enrollment = %s AND v.phase = 'baseline' AND c.status = 'completed'""",
            (enrollment,),
        ).fetchone()
        if baseline is None or eligible is not True:
            raise IngestError("ineligible_baseline")
        phases = connection.execute(
            """SELECT p.phase FROM assessment.enrollment e JOIN assessment.protocol_visit p
                 ON (p.protocol, p.sequence) = (e.protocol, e.sequence)
               WHERE e.id = %s AND p.phase <> 'baseline' ORDER BY p.phase""",
            (enrollment,),
        ).fetchall()
        if {phase for (phase,) in phases} != follow_up_windows.keys():
            raise IngestError("invalid_windows")
        connection.execute(
            "INSERT INTO assessment.allocation VALUES (%s, %s, %s)",
            (enrollment, baseline[0], arm),
        )
        return {
            phase: _create_visit(
                connection, enrollment, phase, follow_up_windows[phase]
            )
            for (phase,) in phases
        }


def start_visit(conninfo, enrollment, visit, client_build):
    with psycopg.connect(conninfo) as connection:
        _require_enrollment(connection, enrollment)
        row = connection.execute(
            """UPDATE assessment.visit SET client_build = %s, started_at = clock_timestamp()
               WHERE id = %s AND enrollment = %s AND started_at IS NULL
                 AND NOT EXISTS (SELECT 1 FROM assessment.visit_close WHERE visit = %s)
               RETURNING id""",
            (client_build, visit, enrollment, visit),
        ).fetchone()
        if row is None:
            raise IngestError("conflict")


def mark_slot_presented(conninfo, enrollment, slot):
    """Record presentation independently of a terminal response."""
    with psycopg.connect(conninfo) as connection:
        _require_enrollment(connection, enrollment)
        row = connection.execute(
            """UPDATE assessment.slot s
               SET presented_at = COALESCE(s.presented_at, clock_timestamp())
               FROM assessment.visit v
               WHERE s.id = %s AND s.visit = v.id AND v.enrollment = %s
                 AND v.started_at IS NOT NULL
                 AND NOT EXISTS (SELECT 1 FROM assessment.visit_close WHERE visit = v.id)
               RETURNING s.id""",
            (slot, enrollment),
        ).fetchone()
        if row is None:
            raise IngestError("conflict")


def _final_outcomes(connection, visit, status, started, grace_elapsed):
    if status == "completed":
        invalid = connection.execute(
            """SELECT 1 FROM assessment.slot s LEFT JOIN assessment.outcome o ON o.slot = s.id
               WHERE s.visit = %s AND (o.status IS NULL OR o.status NOT IN ('submitted', 'invalid'))""",
            (visit,),
        ).fetchone()
        if not started or invalid:
            raise IngestError("incomplete_visit")
        return
    if status == "expired" and (started or not grace_elapsed):
        raise IngestError("invalid_expiry")
    if status == "interrupted" and not started:
        raise IngestError("visit_not_started")
    if status not in ("expired", "interrupted"):
        raise IngestError("invalid_status")
    connection.execute(
        """INSERT INTO assessment.outcome (slot, status, timing)
           SELECT s.id, CASE WHEN s.presented_at IS NULL THEN 'unpresented'
                             ELSE 'interrupted' END, 'unknown'
           FROM assessment.slot s WHERE s.visit = %s
             AND NOT EXISTS (SELECT 1 FROM assessment.outcome o WHERE o.slot = s.id)""",
        (visit,),
    )


def close_visit(conninfo, enrollment, visit, status):
    with psycopg.connect(conninfo) as connection:
        _require_enrollment(connection, enrollment)
        row = connection.execute(
            """SELECT v.started_at IS NOT NULL,
                      clock_timestamp() >= v.closes_at + make_interval(secs => p.offline_grace_seconds),
                      c.status
               FROM assessment.visit v JOIN assessment.protocol p ON p.ref = v.protocol
               LEFT JOIN assessment.visit_close c ON c.visit = v.id
               WHERE v.id = %s AND v.enrollment = %s""",
            (visit, enrollment),
        ).fetchone()
        if row is None:
            raise IngestError("missing_dependency")
        started, grace_elapsed, closed_status = row
        if closed_status is not None:
            if closed_status != status:
                raise IngestError("conflict")
            return
        _final_outcomes(connection, visit, status, started, grace_elapsed)
        connection.execute(
            "INSERT INTO assessment.visit_close (visit, status) VALUES (%s, %s)",
            (visit, status),
        )


def revoke(conninfo, enrollment):
    with psycopg.connect(conninfo) as connection:
        if lock_enrollment(connection, enrollment) is None:
            raise IngestError("missing_dependency")
        connection.execute(
            """UPDATE assessment.enrollment_access SET revoked_at = clock_timestamp()
               WHERE enrollment = %s AND revoked_at IS NULL""",
            (enrollment,),
        )
